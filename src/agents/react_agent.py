"""
ReAct Agent implementation with simplified tool integration.

This module implements ReAct (Reasoning and Acting) agents using LangGraph
with support for built-in LangChain BaseTool implementations and MCP tools
via streamable_http.

이 모듈은 내장된 LangChain BaseTool 구현과 streamable_http를 통한 MCP 도구를
지원하는 LangGraph를 사용하여 ReAct(추론 및 행동) 에이전트를 구현합니다.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from ..schemas.agent_config import AgentConfig

# Remove circular import - import inside functions instead


class ReActAgent:
    """
    ReAct Agent with simplified tool integration.
    
    간소화된 도구 통합을 지원하는 ReAct 에이전트입니다.
    """

    def __init__(self, config_path: Optional[str] = None, config: Optional[AgentConfig] = None):
        """
        Initialize ReAct agent.
        
        Args:
            config_path: Path to YAML configuration file
            config: Pre-loaded AgentConfig object
        """
        if config:
            self.config = config
        elif config_path:
            self.config = AgentConfig.from_yaml_file(config_path)
        else:
            raise ValueError("Either config_path or config must be provided")
            
        self.logger = logging.getLogger(__name__)
        self.agent = None
        self.tools: List[BaseTool] = []
        self.tool_registry = None

    async def initialize(self):
        """Initialize the agent with tools and model."""
        try:
            # Import here to avoid circular import
            from ..core.tool_registry import create_tool_registry
            
            self.logger.info(f"Initializing ReAct agent: {self.config.metadata.name}")
            
            # Debug: Check if tools are defined in config
            if hasattr(self.config, 'tools') and self.config.tools:
                self.logger.info(f"Config has {len(self.config.tools)} tools defined")
                for tool in self.config.tools:
                    self.logger.info(f"  - Tool: {tool.name} (type: {tool.type})")
            else:
                self.logger.info("No tools defined in config - agent will run without tools")
            
            # Initialize tools using ToolRegistry
            self.tool_registry = create_tool_registry(self.config)
            self.tools = await self.tool_registry.initialize()
            
            self.logger.info(f"ToolRegistry initialized with {len(self.tools)} tools")
            for tool in self.tools:
                self.logger.info(f"  - Loaded tool: {tool.name}")
            
            # Get LLM based on config
            llm = self._create_llm()
            self.logger.info(f"Created LLM: {type(llm).__name__}")
            
            # Create the ReAct agent
            self.agent = create_react_agent(
                llm, 
                self.tools,
                prompt=self._get_system_prompt()
            )
            
            self.logger.info("ReAct agent initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ReAct agent: {e}")
            raise
    
    def get_agent(self):
        """
        Get the underlying LangGraph agent for direct access.
        
        Returns:
            The LangGraph ReAct agent instance
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        return self.agent


    def _create_llm(self):
        """Create LLM instance based on configuration."""
        model_config = self.config.model
        
        # Get API key from environment variable
        api_key = os.getenv(model_config.api_key)
        if not api_key:
            raise ValueError(f"Environment variable '{model_config.api_key}' not found or empty")
        
        if model_config.provider.value == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_config.name,
                api_key=api_key,
                **model_config.parameters
            )
        elif model_config.provider.value == "openai_compatible":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_config.name,
                base_url=model_config.base_url,
                api_key=api_key,
                **model_config.parameters
            )
        elif model_config.provider.value == "aws_bedrock":
            from langchain_aws import ChatBedrock
            return ChatBedrock(
                model_id=model_config.name,
                region_name=model_config.region,
                **model_config.parameters
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_config.provider}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt from configuration."""
        if self.config.prompt:
            return self.config.prompt.system_prompt
        return "You are a helpful AI assistant with access to various tools."

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Run the agent with a message.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments
            
        Returns:
            Dict containing response and metadata
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Run the agent
            result = await self.agent.ainvoke({"messages": [("user", message)]})
            
            # Extract the final response
            final_message = result["messages"][-1]
            
            # Extract detailed tool call information
            tool_calls = []
            
            for msg in result["messages"]:
                msg.pretty_print()

                # Handle AI messages with tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        # Extract tool name and arguments
                        tool_name = None
                        tool_args = {}
                        
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get('name')
                            tool_args = tool_call.get('args', {})
                        elif hasattr(tool_call, 'name'):
                            tool_name = tool_call.name
                            tool_args = getattr(tool_call, 'args', {})
                        
                        if tool_name:
                            # Create detailed tool call info
                            tool_call_info = {
                                "name": tool_name,
                                "args": tool_args,
                                "result": None,
                                "error": None
                            }
                            tool_calls.append(tool_call_info)
                
                # Handle tool result messages
                elif hasattr(msg, 'content') and hasattr(msg, 'name'):
                    # This is a tool result message
                    tool_name = getattr(msg, 'name', None)
                    if tool_name:
                        # Find the corresponding tool call and update its result
                        for tool_call_info in reversed(tool_calls):
                            if tool_call_info["name"] == tool_name and tool_call_info["result"] is None:
                                tool_call_info["result"] = msg.content
                                break
            
            return {
                "response": final_message.content,
                "tool_calls": tool_calls
            }
            
        except Exception as e:
            self.logger.error(f"Error running agent: {e}")
            raise



    async def astream(self, message: str, **kwargs):
        """
        Stream the agent execution with a message.
        
        This is the primary streaming method that returns LangGraph's native format:
        each chunk is a tuple of (message, metadata) where:
        - message: AIMessage, ToolMessage, or other LangChain message types
        - metadata: dict with langgraph_step, langgraph_node, etc.
        
        Example usage:
            async for chunk in agent.astream("1 + 15를 계산해줘"):
                message, metadata = chunk
                
                # Content streaming
                if hasattr(message, 'content') and message.content:
                    print(f"Content: {message.content}")
                
                # Tool call detection
                elif hasattr(message, 'tool_calls') and message.tool_calls:
                    for tc in message.tool_calls:
                        print(f"Tool: {tc['name']}({tc['args']})")
                
                # Tool result
                elif hasattr(message, 'name') and hasattr(message, 'content'):
                    print(f"Tool result: {message.name} -> {message.content}")
        
        Client helper example:
            def parse_chunk(chunk):
                message, metadata = chunk
                return {
                    "type": "tool_result" if hasattr(message, 'name') and hasattr(message, 'content')
                           else "tool_call" if hasattr(message, 'tool_calls') and message.tool_calls
                           else "content" if hasattr(message, 'content') and message.content
                           else "metadata",
                    "content": getattr(message, 'content', ''),
                    "message": message,
                    "metadata": metadata
                }
        
        For maximum performance, consider using get_agent().astream() directly.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments (passed to LangGraph)
            
        Yields:
            (message, metadata) tuples from LangGraph agent execution
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Direct passthrough to LangGraph agent streaming
            async for chunk in self.agent.astream({"messages": [("user", message)]}, **kwargs):
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Error streaming agent: {e}")
            raise

    async def astream_events(self, message: str, **kwargs):
        """
        Stream fine-grained events from the agent execution.
        
        This provides the most detailed streaming information including
        token-level streaming and internal agent events.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments
            
        Yields:
            Event dictionaries from LangGraph's astream_events
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            async for event in self.agent.astream_events(
                {"messages": [("user", message)]}, 
                version="v2",
                **kwargs
            ):
                yield event
                
        except Exception as e:
            self.logger.error(f"Error streaming events: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        if self.tool_registry:
            await self.tool_registry.cleanup()
        self.logger.info("ReAct agent cleanup complete")

    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about loaded tools."""
        if self.tool_registry:
            return self.tool_registry.get_tool_info()
        return {"total_count": 0, "tools": []}

    async def astream_sse(self, message: str, **kwargs):
        """
        Stream the agent execution in Server-Sent Events format.
        
        클라이언트에서 EventSource로 직접 사용할 수 있는 SSE 형태로 스트리밍합니다.
        웹 애플리케이션에서 실시간 AI 응답을 구현할 때 최적화된 형태입니다.
        
        Example usage (FastAPI):
            @app.get("/stream")
            async def stream_chat(message: str):
                return StreamingResponse(
                    agent.astream_sse(message),
                    media_type="text/plain",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
        
        Example usage (Client - JavaScript):
            const eventSource = new EventSource('/stream?message=hello');
            eventSource.onmessage = (event) => {
                const chunk = JSON.parse(event.data);
                if (chunk.type === 'content') {
                    console.log(chunk.content);
                } else if (chunk.type === 'tool_call') {
                    console.log('Tool:', chunk.tool.name, chunk.tool.args);
                } else if (chunk.type === 'tool_result') {
                    console.log('Result:', chunk.result);
                }
            };
        
        Args:
            message: User message to process
            **kwargs: Additional arguments
            
        Yields:
            str: SSE formatted strings ready for StreamingResponse
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            from ..schemas.streaming import langraph_to_sse_stream
            
            # LangGraph 스트림을 SSE로 변환
            async for sse_chunk in langraph_to_sse_stream(
                self.agent.astream({"messages": [("user", message)]}, **kwargs)
            ):
                yield sse_chunk
                
        except Exception as e:
            self.logger.error(f"Error streaming SSE: {e}")
            # 에러도 SSE 형태로 전송
            error_chunk = f'data: {{"type": "error", "content": "{str(e)}"}}\n\n'
            yield error_chunk

    async def astream_json_lines(self, message: str, **kwargs):
        """
        Stream the agent execution in JSON Lines format.
        
        각 줄이 JSON 객체인 NDJSON 형태로 스트리밍합니다.
        SSE를 지원하지 않는 환경이나 배치 처리에 적합합니다.
        
        Example usage (FastAPI):
            @app.get("/stream-json")
            async def stream_json(message: str):
                return StreamingResponse(
                    agent.astream_json_lines(message),
                    media_type="application/x-ndjson"
                )
        
        Example usage (Client - Python):
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    print(f"{chunk['type']}: {chunk.get('content', '')}")
        
        Args:
            message: User message to process
            **kwargs: Additional arguments
            
        Yields:
            str: JSON Lines formatted strings
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            from ..schemas.streaming import langraph_to_json_lines_stream
            
            # LangGraph 스트림을 JSON Lines로 변환
            async for json_line in langraph_to_json_lines_stream(
                self.agent.astream({"messages": [("user", message)]}, **kwargs)
            ):
                yield json_line
                
        except Exception as e:
            self.logger.error(f"Error streaming JSON Lines: {e}")
            import json
            error_line = f'{json.dumps({"type": "error", "content": str(e)})}\n'
            yield error_line


async def create_react_agent_from_config(config_path: str) -> ReActAgent:
    """
    Factory function to create and initialize a ReAct agent from configuration.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Initialized ReActAgent instance
    """
    agent = ReActAgent(config_path=config_path)
    await agent.initialize()
    return agent
