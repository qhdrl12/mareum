"""
Agent lifecycle management.

This module provides centralized agent instance management,
replacing global variables with proper dependency injection pattern.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..agents.react_agent import ReActAgent
from ..agents.tools import Calculator, WebSearch, KnowledgeBaseSearch, FileManager
from .exceptions import ConfigError


class AgentManager:
    """
    Centralized agent lifecycle management.
    
    Replaces global agent variables with proper singleton pattern
    and dependency injection for better testability and maintainability.
    """
    
    _instance: Optional['AgentManager'] = None
    _agent: Optional[ReActAgent] = None
    _config_path: Optional[str] = None
    
    def __new__(cls) -> 'AgentManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger(__name__)
        return cls._instance
    
    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._agent is not None
    
    def initialize_agent(
        self, 
        config_path: str, 
        tools: Optional[List] = None,
        force_reload: bool = False
    ) -> ReActAgent:
        """
        Initialize agent with configuration.
        
        Args:
            config_path: Path to agent configuration file
            tools: Optional list of tools to use (defaults to standard tools)
            force_reload: Force reload even if agent already exists
            
        Returns:
            Initialized ReActAgent instance
            
        Raises:
            ConfigError: If initialization fails
        """
        # Check if already initialized
        if self._agent is not None and not force_reload:
            if self._config_path == config_path:
                self.logger.info(f"Agent already initialized with config: {config_path}")
                return self._agent
            else:
                self.logger.info(f"Reloading agent with new config: {config_path}")
        
        # Convert to absolute path
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
        
        # Use default tools if none provided
        if tools is None:
            tools = [] # self._get_default_tools()
        
        try:
            # Create new agent instance
            self._agent = ReActAgent(config_path=config_path, tools=tools)
            self._config_path = config_path
            
            self.logger.info(
                f"Agent initialized successfully: {self._agent.config.metadata.name} "
                f"with {len(tools)} tools from {config_path}"
            )
            return self._agent
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            raise ConfigError(
                f"Failed to initialize agent: {str(e)}",
                config_path=config_path,
                cause=e
            )
    
    def get_agent(self) -> ReActAgent:
        """
        Get current agent instance.
        
        Returns:
            Current ReActAgent instance
            
        Raises:
            ConfigError: If agent is not initialized
        """
        if self._agent is None:
            raise ConfigError(
                "Agent not initialized. Call initialize_agent() first.",
                config_path=self._config_path
            )
        return self._agent
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get current agent information.
        
        Returns:
            Dictionary with agent configuration and status
        """
        if self._agent is None:
            return {
                "initialized": False,
                "config_path": self._config_path,
                "error": "Agent not initialized"
            }
        
        config = self._agent.config
        return {
            "initialized": True,
            "config_path": self._config_path,
            "agent_name": config.metadata.name,
            "agent_version": config.metadata.version,
            "model_provider": config.model.provider.value,
            "model_name": config.model.name,
            "tools_count": len(self._agent.tools),
            "memory_enabled": self._agent.memory_enabled,
        }
    
    def reload_agent(self, config_path: Optional[str] = None) -> ReActAgent:
        """
        Reload agent with same or new configuration.
        
        Args:
            config_path: Optional new config path (uses current if None)
            
        Returns:
            Reloaded ReActAgent instance
        """
        config_path = config_path or self._config_path
        if config_path is None:
            raise ConfigError("No config path available for reload")
        
        return self.initialize_agent(config_path, force_reload=True)
    
    def shutdown(self):
        """Shutdown and cleanup agent."""
        if self._agent is not None:
            self.logger.info("Shutting down agent")
            # Add any cleanup logic here if needed
            self._agent = None
            self._config_path = None
    
    def _get_default_tools(self) -> List:
        """Get default tool instances."""
        return [
            Calculator(),
            WebSearch(), 
            KnowledgeBaseSearch(),
            FileManager()
        ]
    
    @classmethod
    def create_from_env(cls, env_var: str = "AGENT_CONFIG_PATH", default_path: str = "examples/configs/openai_compatible.yaml") -> 'AgentManager':
        """
        Create and initialize agent manager from environment variable.
        
        Args:
            env_var: Environment variable name for config path
            default_path: Default config path if env var not set
            
        Returns:
            Initialized AgentManager instance
        """
        config_path = os.getenv(env_var, default_path)
        manager = cls()
        manager.initialize_agent(config_path)
        return manager 