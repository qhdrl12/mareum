"""
Pydantic models for the ReAct Agent API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message in the conversation history."""

    role: str = Field(description="The role of the message sender (human or assistant)")
    content: str = Field(description="The content of the message")


class ToolCall(BaseModel):
    """Detailed information about a tool call."""

    name: str = Field(description="Name of the tool that was called")
    args: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments/parameters passed to the tool"
    )
    result: Any = Field(default=None, description="Result returned by the tool")
    error: Optional[str] = Field(default=None, description="Error message if tool call failed")


class AgentRequest(BaseModel):
    """Request model for agent interaction."""

    message: str = Field(description="The user's message to the agent")


class AgentResponse(BaseModel):
    """Response model for agent interaction."""

    response: str = Field(description="The agent's response message")
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Detailed information about tool calls made during the interaction"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the response"
    )


class AgentStreamChunk(BaseModel):
    """A chunk of streaming response from the agent."""

    chunk: str = Field(description="The content chunk")
    is_final: bool = Field(description="Whether this is the final chunk")
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Detailed information about tool calls (populated in final chunk)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the chunk"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Current status of the service")
    version: str = Field(description="Version of the API")
    timestamp: str = Field(description="Current timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error message")
    error_code: str = Field(description="Error code")
    timestamp: str = Field(description="Error timestamp")
    detail: Optional[str] = Field(default=None, description="Additional error details")


class ConfigInfo(BaseModel):
    """Information about an agent configuration."""

    name: str = Field(description="Name of the configuration")
    path: str = Field(description="Path to the configuration file")
    description: str = Field(description="Description of the configuration")


class ConfigListResponse(BaseModel):
    """Response model for listing available configurations."""

    configs: List[ConfigInfo] = Field(description="List of available configurations")


class AgentInfoResponse(BaseModel):
    """Response model for agent information."""

    config_path: str = Field(description="Path to the agent configuration")
    agent_info: Dict[str, Any] = Field(description="Agent configuration details")
    tools_available: List[str] = Field(description="List of available tools")
    status: str = Field(description="Agent status")
