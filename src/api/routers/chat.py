from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
import logging

from ...schemas.chat import ChatRequest, ChatResponse
from ...models.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


async def get_agent_from_request(request: Request) -> Agent:
    """Dependency function to get agent from app state."""
    if not hasattr(request.app.state, 'agent') or request.app.state.agent is None:
        raise HTTPException(
            status_code=500, 
            detail="Agent not initialized. Please check server configuration."
        )
    return request.app.state.agent


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    agent: Agent = Depends(get_agent_from_request)
) -> ChatResponse:
    """
    Chat with the AI agent
    """
    try:
        logger.info(f"Received chat request: {request.message[:100]}...")
        
        # Process message through agent
        response = await agent.process_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        logger.info("Successfully processed message")
        return ChatResponse(
            message=response["message"],
            session_id=response["session_id"],
            metadata=response.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/chat/stream")
async def stream_chat_with_agent(
    request: ChatRequest,
    agent: Agent = Depends(get_agent_from_request)
):
    """
    Stream chat with the AI agent (for real-time responses)
    """
    try:
        logger.info(f"Received streaming chat request: {request.message[:100]}...")
        
        # This would implement streaming response
        # For now, return regular response
        response = await agent.process_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process streaming message: {str(e)}"
        )


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    agent: Agent = Depends(get_agent_from_request)
):
    """
    Get chat session information
    """
    try:
        session_info = await agent.get_session_info(session_id)
        return session_info
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}"
        )


@router.delete("/chat/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    agent: Agent = Depends(get_agent_from_request)
):
    """
    Clear chat session
    """
    try:
        await agent.clear_session(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session: {str(e)}"
        ) 