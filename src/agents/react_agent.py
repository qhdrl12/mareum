"""
ReAct Agent implementation using LangGraph's prebuilt create_react_agent.

This module implements a ReAct (Reasoning and Acting) agent that can:
1. Process user input
2. Reason about the required actions
3. Execute tools/actions
4. Provide responses based on results
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..core.config_parser import ConfigParser


class ReActAgent:
    """
    LangGraph-based ReAct Agent implementation using prebuilt create_react_agent.

    This agent follows the ReAct pattern:
    1. Reasoning about the current situation
    2. Acting by calling appropriate tools
    3. Observing the results
    4. Continuing until task completion
    """

    def __init__(self, config_path: str, tools: Optional[List] = None):
        """
        Initialize the ReAct Agent.
        
        Args:
            config_path: Path to the agent configuration file
            tools: Optional list of tools to use with the agent
        """
        self.logger = logging.getLogger(__name__)

        # Load configuration
        parser = ConfigParser()
        self.config = parser.parse_from_file(config_path)

        # Initialize LLM based on provider
        self._initialize_llm()

        # Initialize tools
        self.tools = tools or []

        # Initialize memory
        self.conversation_history = []
        memory_config = self.config.memory
        self.memory_enabled = memory_config is not None

        # Create the ReAct agent using LangGraph's prebuilt function
        self.agent = create_react_agent(model=self.llm, tools=self.tools)

        self.logger.info(f"ReAct Agent initialized with {len(self.tools)} tools")

    def _add_to_memory(self, role: str, content: str):
        """Add a message to the conversation memory."""
        if not self.memory_enabled:
            self.logger.debug("Memory disabled - skipping memory update")
            return

        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Keep only the last max_messages (default 10)
        max_messages = 10
        if self.config.memory and hasattr(self.config.memory, 'config') and self.config.memory.config:
            max_messages = self.config.memory.config.get('k', 10)

        if len(self.conversation_history) > max_messages:
            old_count = len(self.conversation_history)
            self.conversation_history = self.conversation_history[-max_messages:]
            self.logger.info(
                f"Memory buffer trimmed: {old_count} -> {len(self.conversation_history)} messages"
            )

        self.logger.info(
            f"Memory updated: {role} message added (total: {len(self.conversation_history)}/{max_messages} messages)"
        )

    def _get_conversation_context(self) -> str:
        """Get conversation context for the current request."""
        if not self.memory_enabled:
            self.logger.debug("Memory disabled - no conversation context available")
            return ""

        if not self.conversation_history:
            self.logger.debug("Memory enabled but conversation history is empty")
            return ""

        context_parts = []
        for msg in self.conversation_history:
            role_prefix = "User" if msg["role"] == "human" else "Assistant"
            context_parts.append(f"{role_prefix}: {msg['content']}")

        context = "\n".join(context_parts) + "\n" if context_parts else ""
        self.logger.info(
            f"Using conversation context with {len(self.conversation_history)} messages"
        )

        return context

    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory status."""
        return {
            "enabled": self.memory_enabled,
            "history_count": (
                len(self.conversation_history) if self.memory_enabled else 0
            ),
        }

    def _initialize_llm(self):
        """Initialize the LLM based on configuration."""
        model_config = self.config.model
        provider = model_config.provider.value

        # Helper function to get API key
        def get_api_key(key_name):
            """Get API key from environment or config."""
            if not key_name:
                return "not-needed"  # For testing or when key is not required
                
            # Check environment variable first
            env_value = os.getenv(key_name)
            if env_value and env_value != "test_key_for_docker_test":
                self.logger.debug(f"Using API key from environment: {key_name}")
                return env_value
            
            # Check if it's a literal key (starts with sk-, etc.)
            if isinstance(key_name, str) and (key_name.startswith('sk-') or key_name.startswith('gsk_')):
                self.logger.debug(f"Using literal API key")
                return key_name
                
            # Fallback to config value if it exists
            if hasattr(model_config, 'api_key') and model_config.api_key:
                self.logger.debug(f"Using API key from config")
                return model_config.api_key
                
            self.logger.warning(f"No API key found for {key_name}")
            return "not-needed"

        if provider == "openai":
            api_key = get_api_key(model_config.api_key)
            self.llm = ChatOpenAI(
                model=model_config.name,
                api_key=api_key,
                **model_config.parameters if model_config.parameters else {}
            )
            self.logger.info(f"Initialized OpenAI LLM: {model_config.name}")
        elif provider == "openai_compatible":
            # For OpenAI Compatible APIs that might not support function calling
            api_key = get_api_key(model_config.api_key)
            self.llm = ChatOpenAI(
                model=model_config.name,
                base_url=model_config.base_url,
                api_key=api_key,
                **model_config.parameters if model_config.parameters else {}
            )
            self.logger.info(
                f"Initialized OpenAI Compatible LLM: {model_config.name} at {model_config.base_url}"
            )
        elif provider == "aws_bedrock":
            api_key = get_api_key(model_config.api_key)
            self.llm = ChatAnthropic(
                model=model_config.name,
                api_key=api_key,
                **model_config.parameters if model_config.parameters else {}
            )
            self.logger.info(f"Initialized AWS Bedrock LLM: {model_config.name}")
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    def _create_system_message(self):
        """Create system message from configuration."""
        # Get system prompt from config or use default
        system_prompt = self.config.prompt.system_prompt or (
            f"You are {self.config.metadata.name}, {self.config.metadata.description}. "
            "Use the available tools to help answer questions and complete tasks. "
            "Always reason step by step and explain your actions."
        )

        return SystemMessage(content=system_prompt)

    def _create_llm_with_tools(self):
        """Create LLM instance with bound tools for tool calling."""
        return self.llm.bind_tools(self.tools)

    async def run(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """
        Run the agent with user input and return structured response.
        
        Args:
            user_input: User's message/question
            **kwargs: Additional arguments (chat_history, etc.)
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Add to memory if enabled
            self._add_to_memory("human", user_input)

            # Get conversation context if memory is enabled
            context = self._get_conversation_context()

            # Prepare input for the agent
            if context:
                # Include conversation context in the input
                enhanced_input = f"{context}\nCurrent request: {user_input}"
            else:
                enhanced_input = user_input

            # Handle chat history from request if provided
            chat_history = kwargs.get("chat_history", [])
            messages = []

            # Add chat history if provided
            for msg in chat_history:
                if msg["role"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            # Add current user input
            messages.append(HumanMessage(content=enhanced_input))

            # Run the agent
            agent_response = await self.agent.ainvoke({"messages": messages})

            # Extract the final response
            final_response = agent_response["messages"][-1].content if agent_response["messages"] else "No response generated."

            # Extract tool usage information
            tools_used = []
            for msg in agent_response.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = getattr(tool_call, "name", "unknown")
                        tools_used.append(tool_name)

            # Remove duplicates while preserving order
            tools_used = list(dict.fromkeys(tools_used))

            # Add to memory if enabled
            self._add_to_memory("assistant", final_response)

            return {
                "response": final_response,
                "tools_used": tools_used,
                "agent_response": agent_response,
            }

        except Exception as e:
            self.logger.error(f"Error in agent run: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "tools_used": [],
                "agent_response": None,
            }

    def run_sync(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """
        Synchronous version of run method.
        
        Args:
            user_input: User's message/question
            **kwargs: Additional arguments
            
        Returns:
            Dict containing response and metadata
        """
        import asyncio
        return asyncio.run(self.run(user_input, **kwargs))

    def stream(self, user_input: str, **kwargs):
        """
        Stream responses from the agent (synchronous).
        
        Args:
            user_input: User's message/question
            **kwargs: Additional arguments
            
        Yields:
            Streaming chunks from the agent
        """
        import asyncio
        
        async def _async_stream():
            async for chunk in self.astream(user_input, **kwargs):
                yield chunk
                
        # Run the async generator in the current event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        async def _collect_chunks():
            chunks = []
            async for chunk in self.astream(user_input, **kwargs):
                chunks.append(chunk)
            return chunks
            
        chunks = loop.run_until_complete(_collect_chunks())
        for chunk in chunks:
            yield chunk

    async def astream(self, user_input: str, **kwargs):
        """
        Stream responses from the agent asynchronously.
        
        Args:
            user_input: User's message/question
            **kwargs: Additional arguments
            
        Yields:
            Streaming chunks from the agent
        """
        try:
            # Add to memory if enabled  
            self._add_to_memory("human", user_input)

            # Get conversation context if memory is enabled
            context = self._get_conversation_context()

            # Prepare input
            if context:
                enhanced_input = f"{context}\nCurrent request: {user_input}"
            else:
                enhanced_input = user_input

            # Prepare messages
            messages = [HumanMessage(content=enhanced_input)]

            # Stream from agent
            async for chunk in self.agent.astream({"messages": messages}):
                yield chunk

        except Exception as e:
            self.logger.error(f"Error in agent stream: {str(e)}")
            yield {"error": str(e)}

    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the agent configuration."""
        return {
            "metadata": {
                "name": self.config.metadata.name,
                "description": self.config.metadata.description,
                "version": self.config.metadata.version,
            },
            "model": {
                "provider": self.config.model.provider.value,
                "name": self.config.model.name,
                "base_url": getattr(self.config.model, "base_url", None),
                "parameters": self.config.model.parameters or {},
            },
            "tools": [{"name": tool.name, "description": tool.description} for tool in self.tools],
            "memory": {
                "enabled": self.memory_enabled,
                "type": self.config.memory.type if self.config.memory else None,
                "config": self.config.memory.config if self.config.memory else None,
            },
        }
