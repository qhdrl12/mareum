"""
FastAPI application for ReAct Agent API.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.api.models import (
    AgentRequest,
    AgentResponse,
    AgentStreamChunk,
    HealthResponse,
)
from src.core.agent_manager import AgentManager
from src.core.exceptions import ConfigError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent manager instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        raise HTTPException(
            status_code=500,
            detail="Agent manager not initialized. Please check server configuration.",
        )
    return _agent_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup and cleanup on shutdown."""
    global _agent_manager
    
    # Initialize agent manager
    try:
        _agent_manager = AgentManager.create_from_env(
            env_var="AGENT_CONFIG_PATH",
            default_path="examples/configs/openai_compatible.yaml"  # Fixed typo
        )
        logger.info("Server started with agent manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize agent manager on startup: {str(e)}")
        # Continue startup but agent will be unavailable

    yield

    # Cleanup on shutdown
    if _agent_manager is not None:
        _agent_manager.shutdown()
    logger.info("Server shutting down")


# FastAPI app instance with lifespan handler
app = FastAPI(
    title="ReAct Agent API",
    description="A REST API for ReAct Agent interactions",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic info."""
    return HealthResponse(
        status="running", version="1.0.0", timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.now().isoformat()
    )


@app.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Chat with the ReAct agent."""
    try:
        agent_manager = get_agent_manager()
        agent = agent_manager.get_agent()

        # Process the request using the correct method
        result = await agent.run(request.message)

        return AgentResponse(
            response=result["response"],
            tools_used=result.get("tools_used", []),
            metadata={
                "config_path": agent_manager._config_path,
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent.config.metadata.name,
                "model": f"{agent.config.model.provider.value}/{agent.config.model.name}",
                "memory_enabled": agent.memory_enabled,
            },
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@app.post("/chat/stream")
async def stream_chat_with_agent(request: AgentRequest):
    """Stream chat with the ReAct agent."""
    try:
        agent_manager = get_agent_manager()
        agent = agent_manager.get_agent()

        async def generate_stream():
            """Generate streaming response."""
            tools_used = []
            try:
                # Process the request with streaming using astream
                async for chunk in agent.astream(request.message):
                    # Track tools used in the chunk
                    if isinstance(chunk, dict) and "messages" in chunk:
                        for msg in chunk["messages"]:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    if hasattr(tool_call, "name"):
                                        tools_used.append(tool_call.name)
                                    elif (
                                        isinstance(tool_call, dict)
                                        and "name" in tool_call
                                    ):
                                        tools_used.append(tool_call["name"])

                    # Handle different types of chunks
                    content = ""
                    if isinstance(chunk, dict):
                        if "messages" in chunk and chunk["messages"]:
                            last_message = chunk["messages"][-1]
                            if hasattr(last_message, "content"):
                                content = last_message.content
                            else:
                                content = str(last_message)
                        else:
                            content = str(chunk)
                    else:
                        content = str(chunk)

                    chunk_data = AgentStreamChunk(
                        chunk=content,
                        is_final=False,
                        tools_used=[],
                        metadata={},
                    )
                    yield f"data: {chunk_data.model_dump_json()}\n\n"

                # Remove duplicates while preserving order
                tools_used = list(dict.fromkeys(tools_used))

                # Send final chunk with tools used
                final_chunk = AgentStreamChunk(
                    chunk="", is_final=True, tools_used=tools_used, metadata={}
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"

            except Exception as e:
                error_chunk = AgentStreamChunk(
                    chunk="",
                    is_final=True,
                    tools_used=tools_used,
                    metadata={"error": str(e)},
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception as e:
        logger.error(f"Stream processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process stream: {str(e)}")


@app.get("/agent/info")
async def get_agent_info():
    """Get information about the current agent configuration."""
    try:
        agent_manager = get_agent_manager()
        return agent_manager.get_agent_info()

    except Exception as e:
        logger.error(f"Failed to get agent info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": str(exc.status_code),
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    from fastapi.responses import JSONResponse

    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "500",
            "timestamp": datetime.now().isoformat(),
        },
    )


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    # For development
    run_server(reload=True)
