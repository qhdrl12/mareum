"""
Agent management and lifecycle handling.

This module manages agent creation, lifecycle, and interactions.
Handles both direct agent instantiation and RESTful API interactions.

이 모듈은 에이전트 생성, 생명주기, 상호작용을 관리합니다.
직접 에이전트 인스턴스화와 RESTful API 상호작용을 모두 처리합니다.
"""

import logging
import os

from typing import Optional, Dict, Any

from ..agents.react_agent import ReActAgent
from .exceptions import ConfigError


class AgentManager:
    """
    Manages ReAct agent instances and their lifecycle.
    
    ReAct 에이전트 인스턴스와 생명주기를 관리합니다.
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
    
    async def initialize_agent(
        self, 
        config_path: str, 
        force_reload: bool = False
    ) -> ReActAgent:
        """
        Initialize agent with configuration.
        
        Args:
            config_path: Path to agent configuration file
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
        
        try:
            # Create new agent instance
            self._agent = ReActAgent(config_path=config_path)
            # Initialize the agent with tools and model
            await self._agent.initialize()
            self._config_path = config_path
            
            self.logger.info(
                f"Agent initialized successfully: {self._agent.config.metadata.name} "
                f"from {config_path}"
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
        }
    
    async def reload_agent(self, config_path: Optional[str] = None) -> ReActAgent:
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
        
        return await self.initialize_agent(config_path, force_reload=True)
    
    def shutdown(self):
        """Shutdown and cleanup agent."""
        if self._agent is not None:
            self.logger.info("Shutting down agent")
            # Add any cleanup logic here if needed
            self._agent = None
            self._config_path = None
    
    @classmethod
    async def create_from_env(cls, env_var: str = "AGENT_CONFIG_PATH", default_path: str = "examples/configs/openai_compatible.yaml") -> 'AgentManager':
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
        await manager.initialize_agent(config_path)
        return manager


# Global agent manager instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """
    Get the global agent manager instance.
    
    Returns:
        AgentManager: Global agent manager
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager 