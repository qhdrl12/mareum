from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import uvicorn
import logging
from pathlib import Path

from ..core.config_parser import load_config
from ..models.agent import Agent
from ..schemas.chat import ChatRequest, ChatResponse
from .routers import chat

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Load configuration if provided
    config_path = getattr(app.state, 'config_path', None)
    if config_path:
        try:
            config_data = load_config(config_path)
            agent_instance = Agent(config_data)
            
            # Store both agent and config in app state
            app.state.agent = agent_instance
            app.state.config_data = config_data
            
            logger.info(f"Agent initialized with config: {config_data['metadata']['name']}")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    else:
        logger.warning("No configuration provided, agent will be initialized per request")
        app.state.agent = None
        app.state.config_data = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if hasattr(app.state, 'agent') and app.state.agent:
        # Cleanup agent resources if needed
        pass


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="LangGraph Agent Server",
        description="AI Agent server powered by LangGraph",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Store config path in app state
    if config_path:
        app.state.config_path = config_path
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(chat.router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "LangGraph Agent Server",
            "version": "1.0.0",
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "agent_initialized": hasattr(app.state, 'agent') and app.state.agent is not None,
            "config_loaded": hasattr(app.state, 'config_data') and app.state.config_data is not None
        }
    
    @app.get("/config")
    async def get_config():
        """Get current configuration"""
        if not hasattr(app.state, 'config_data') or not app.state.config_data:
            raise HTTPException(status_code=404, detail="No configuration loaded")
        
        config_data = app.state.config_data
        
        # Return safe config data (without sensitive info)
        safe_config = {
            "metadata": config_data.get("metadata", {}),
            "model": {
                k: v for k, v in config_data.get("model", {}).items() 
                if k != "credentials_key"
            },
            "tools": config_data.get("tools", []),
            "memory": config_data.get("memory", {}),
            "knowledge": config_data.get("knowledge", {})
        }
        return safe_config
    
    return app


# def get_agent() -> Agent:
#     """Get the global agent instance (deprecated - use request.app.state.agent instead)"""
#     # This function is kept for backward compatibility
#     # New code should use dependency injection via request.app.state.agent
#     raise HTTPException(
#         status_code=500, 
#         detail="Direct agent access deprecated. Use dependency injection."
#     )


# def get_config() -> Dict[str, Any]:
#     """Get the global config data (deprecated - use request.app.state.config_data instead)"""
#     # This function is kept for backward compatibility
#     # New code should use dependency injection via request.app.state.config_data
#     raise HTTPException(
#         status_code=500,
#         detail="Direct config access deprecated. Use dependency injection."
#     ) 