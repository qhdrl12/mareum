"""
Simplified Tool Integration Framework for ReAct Agents.

This module provides a streamlined framework for integrating tools with ReAct agents:
- Built-in LangChain BaseTool implementations
- MCP (Model Context Protocol) tools via streamable_http

이 모듈은 ReAct 에이전트와 도구를 통합하기 위한 간소화된 프레임워크를 제공합니다:
- 내장된 LangChain BaseTool 구현
- streamable_http를 통한 MCP(Model Context Protocol) 도구
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool

# langchain-mcp-adapters imports
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from ..schemas.agent_config import AgentConfig, ToolConfig, ToolType
from ..tools import get_default_tools  # Clean import - no circular dependency


class MCPToolError(Exception):
    """Exception raised when MCP tool operations fail."""
    pass


class ToolRegistry:
    """
    Simplified registry for managing BaseTool and MCP tools.
    
    BaseTool과 MCP 도구를 관리하기 위한 간소화된 레지스트리입니다.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._tools: List[BaseTool] = []
        self._mcp_clients: Dict[str, MultiServerMCPClient] = {}
        
    async def initialize(self) -> List[BaseTool]:
        """
        Initialize and return all available tools.
        
        모든 사용 가능한 도구를 초기화하고 반환합니다.
        """
        try:
            # Process each tool configuration
            for tool_config in self.config.tools:
                if tool_config.type == ToolType.BUILTIN:
                    await self._add_builtin_tool(tool_config)
                elif tool_config.type == ToolType.MCP:
                    await self._add_mcp_tool(tool_config)
                else:
                    self.logger.warning(f"Unknown tool type: {tool_config.type}")
            
            self.logger.info(f"Tool registry initialized with {len(self._tools)} tools")
            return self._tools
            
        except Exception as e:
            self.logger.error(f"Failed to initialize tool registry: {e}")
            # Return at least default tools if available
            if not self._tools:
                self._add_default_tools()
            return self._tools
    
    def _add_default_tools(self):
        """Add all default built-in tools."""
        try:
            default_tools = get_default_tools()
            self._tools.extend(default_tools)
            self.logger.info(f"Added {len(default_tools)} default tools")
        except Exception as e:
            self.logger.error(f"Failed to add default tools: {e}")
    
    async def _add_builtin_tool(self, tool_config: ToolConfig):
        """Add a single built-in tool by name."""
        try:
            # Get available tools and find the one with matching name
            available_tools = get_default_tools()
            
            for tool in available_tools:
                if tool.name == tool_config.name:
                    self._tools.append(tool)
                    self.logger.info(f"Added builtin tool: {tool_config.name}")
                    return
            
            self.logger.warning(f"Builtin tool '{tool_config.name}' not found. Available: {[t.name for t in available_tools]}")
            
        except Exception as e:
            self.logger.error(f"Failed to add builtin tool {tool_config.name}: {e}")
    
    async def _add_mcp_tool(self, tool_config: ToolConfig):
        """Add MCP tools from a single server."""
        if not MCP_AVAILABLE:
            self.logger.warning("langchain-mcp-adapters not available, skipping MCP tools")
            return
            
        try:
            # Create MCP client configuration for this server
            mcp_config = {
                tool_config.name: {
                    "transport": "streamable_http",
                    "url": tool_config.url
                }
            }
            
            self.logger.info(f"Connecting to MCP server '{tool_config.name}' at {tool_config.url}")
            
            # Create client for this server
            client = MultiServerMCPClient(mcp_config)
            self._mcp_clients[tool_config.name] = client
            
            # Get all tools from this server
            server_tools = await client.get_tools()
            
            # Add all tools without filtering
            self._tools.extend(server_tools)
            self.logger.info(f"Added {len(server_tools)} MCP tools from server '{tool_config.name}'")
                    
        except Exception as e:
            self.logger.error(f"Failed to add MCP tools from {tool_config.name}: {e}")
            raise MCPToolError(f"MCP tool initialization failed for {tool_config.name}: {e}")
    
    def get_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about all registered tools."""
        tool_info = {
            "total_count": len(self._tools),
            "tools": []
        }
        
        for tool in self._tools:
            tool_data = {
                "name": tool.name,
                "description": tool.description,
                "type": "mcp" if hasattr(tool, '_mcp_tool') else "builtin"
            }
            tool_info["tools"].append(tool_data)
            
        return tool_info
    
    async def cleanup(self):
        """Cleanup resources, disconnect from MCP servers."""
        for server_name, client in self._mcp_clients.items():
            try:
                # MultiServerMCPClient handles cleanup automatically
                self.logger.info(f"Cleaned up MCP client for server '{server_name}'")
            except Exception as e:
                self.logger.error(f"Error during MCP client cleanup for {server_name}: {e}")
        
        self._mcp_clients.clear()
        self._tools.clear()
        self.logger.info("Tool registry cleaned up")


def create_tool_registry(config: AgentConfig) -> ToolRegistry:
    """
    Factory function to create a ToolRegistry instance.
    
    ToolRegistry 인스턴스를 생성하는 팩토리 함수입니다.
    """
    return ToolRegistry(config)


# Utility functions
def check_mcp_availability() -> bool:
    """Check if langchain-mcp-adapters is available."""
    return MCP_AVAILABLE


def get_available_builtin_tools() -> List[str]:
    """Get list of available built-in tool names."""
    try:
        tools = get_default_tools()
        return [tool.name for tool in tools]
    except Exception:
        return [] 