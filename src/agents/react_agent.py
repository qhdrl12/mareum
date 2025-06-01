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
            
            # Extract tool names used during the conversation
            tools_used = []
            for msg in result["messages"]:
                msg.pretty_print()

                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        # Tool calls can be dicts with 'name' key or objects with 'name' attribute
                        tool_name = None
                        if isinstance(tool_call, dict) and 'name' in tool_call:
                            tool_name = tool_call['name']
                        elif hasattr(tool_call, 'name'):
                            tool_name = tool_call.name
                        
                        if tool_name and tool_name not in tools_used:
                            tools_used.append(tool_name)
            
            return {
                "response": final_message.content,
                "tools_used": tools_used
            }
            
        except Exception as e:
            self.logger.error(f"Error running agent: {e}")
            raise

    async def astream(self, message: str, **kwargs):
        """
        Stream the agent execution with a message.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments
            
        Yields:
            Streaming chunks from the agent execution
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Stream the agent execution
            async for chunk in self.agent.astream({"messages": [("user", message)]}):
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Error streaming agent: {e}")
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
