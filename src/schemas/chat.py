"""
Chat API schemas for request/response models.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="The role of the message sender (user, assistant, system)")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[datetime] = Field(default=None, description="When the message was created")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="The user's message")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the request")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Hello, how can you help me?",
                "session_id": "user123_session1",
                "context": {"user_preference": "detailed"}
            }
        }
    }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="The agent's response message")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the response was generated")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the response")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Hello! I'm here to help you with customer support questions.",
                "session_id": "user123_session1",
                "timestamp": "2024-01-01T12:00:00Z",
                "metadata": {"model_used": "gpt-4", "tokens_used": 25}
            }
        }
    }


class ChatStreamResponse(BaseModel):
    """Response model for streaming chat endpoint."""
    delta: str = Field(..., description="The incremental part of the response")
    session_id: str = Field(..., description="Session ID for this conversation")
    is_complete: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SessionInfo(BaseModel):
    """Information about a chat session."""
    session_id: str = Field(..., description="The session identifier")
    created_at: datetime = Field(..., description="When the session was created")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(default=0, description="Number of messages in the session")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Session metadata")


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    session_id: Optional[str] = Field(default=None, description="Optional custom session ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Initial session metadata")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred") 