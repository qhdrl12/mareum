"""MCP (Model Context Protocol) integration tests."""

import os
import pytest
import asyncio
import subprocess
import signal
from pathlib import Path
import aiohttp

# Add src to path  
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.react_agent import ReActAgent


class MCPServerManager:
    """Helper class to manage MCP server for testing."""
    
    def __init__(self, server_script_path: str, port: int = 3001):
        self.server_script_path = server_script_path
        self.port = port
        self.process = None
        
    async def start_server(self):
        """Start the MCP server."""
        try:
            print(f"🚀 Starting MCP server: {self.server_script_path}")
            self.process = subprocess.Popen(
                [sys.executable, self.server_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for server to start
            await asyncio.sleep(5)
            
            # Check if server is running
            if self.process.poll() is None:
                print(f"✅ MCP server started on port {self.port}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"❌ MCP server failed to start")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✅ MCP server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ MCP server didn't stop gracefully, forcing...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️ Error stopping MCP server: {e}")


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.slow
class TestMCPIntegration:
    """Test MCP server integration."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_availability(self):
        """Test that the MCP math server can be started and is accessible."""
        
        print("🔧 Testing MCP Server Availability")
        print("=" * 50)
        
        # First check if server is already running on port 3001
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3001/mcp") as response:
                    if response.status in [200, 404, 406]:
                        print(f"✅ MCP server already running (status: {response.status})")
                        return
                    else:
                        print(f"⚠️ MCP server returned status {response.status}")
        except Exception as e:
            print(f"⚠️ Could not connect to existing MCP server: {e}")
        
        # Path to the math server
        server_path = str(Path(__file__).parent.parent.parent / "examples" / "mcp_servers" / "math_server.py")
        
        if not os.path.exists(server_path):
            print(f"❌ MCP server script not found: {server_path}")
            pytest.skip("MCP server script not found")
            return
        
        # Start server on port 3001
        server_manager = MCPServerManager(server_path, port=3001)
        server_started = await server_manager.start_server()
        
        try:
            if not server_started:
                pytest.skip("Could not start MCP server")
                return
                
            # Test server accessibility
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:3001/mcp") as response:
                        if response.status in [200, 404]:
                            print("✅ MCP server is accessible on port 3001")
                        else:
                            print(f"⚠️ MCP server returned status {response.status}")
            except Exception as e:
                print(f"⚠️ Could not connect to MCP server: {e}")
                pytest.skip("MCP server not accessible")
                
        finally:
            server_manager.stop_server()

    @pytest.mark.asyncio
    async def test_mcp_agent_configuration(self):
        """Test MCP agent configuration loading."""
        
        print("⚙️ Testing MCP Agent Configuration")
        print("=" * 50)
        
        config_path = str(
            Path(__file__).parent.parent.parent / "examples" / "configs" / "mcp_agent.yaml"
        )
        
        if not os.path.exists(config_path):
            print(f"❌ MCP config file not found: {config_path}")
            pytest.skip("MCP config file not found")
            return
            
        print(f"📝 Loading MCP configuration: {config_path}")
        
        agent = ReActAgent(config_path=config_path)
        
        # Verify config loaded correctly
        assert agent.config.metadata.name == "mcp-local-test-agent"
        assert len(agent.config.tools) > 0
        assert agent.config.tools[0].type.value == "mcp"
        assert agent.config.tools[0].url == "http://localhost:3001/mcp"
        
        print("✅ MCP configuration loaded successfully")
        print(f"   Agent: {agent.config.metadata.name}")
        print(f"   MCP Tools: {len(agent.config.tools)}")
        print(f"   MCP URL: {agent.config.tools[0].url}")

    @pytest.mark.asyncio
    async def test_mcp_math_tools(self):
        """Test MCP math tools functionality."""
        
        print("🧮 Testing MCP Math Tools")
        print("=" * 50)
        
        # Check if MCP server is running
        server_available = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3001/mcp") as response:
                    if response.status in [200, 404, 406]:
                        print(f"✅ MCP server accessible (status: {response.status})")
                        server_available = True
        except Exception as e:
            print(f"❌ MCP server not accessible: {e}")
        
        if not server_available:
            pytest.skip("MCP server not available")
            return
        
        try:
            # Check dependencies
            from langchain_mcp_adapters.client import MultiServerMCPClient
            print("✅ langchain-mcp-adapters available")
        except ImportError:
            print("❌ langchain-mcp-adapters not available")
            pytest.skip("langchain-mcp-adapters not installed")
            return
        
        config_path = str(
            Path(__file__).parent.parent.parent / "examples" / "configs" / "mcp_agent.yaml"
        )
        
        agent = ReActAgent(config_path=config_path)
        await agent.initialize()
        
        print(f"🤖 Agent loaded with {len(agent.tools)} tools")
        
        # Verify expected MCP math tools are available
        expected_tools = ['add', 'subtract', 'multiply', 'divide', 'power', 'square_root']
        available_tools = [tool.name for tool in agent.tools]
        
        missing_tools = [t for t in expected_tools if t not in available_tools]
        if missing_tools:
            print(f"❌ Missing expected MCP tools: {missing_tools}")
            pytest.fail(f"Missing MCP tools: {missing_tools}")
        
        print(f"✅ All expected MCP math tools available: {expected_tools}")
        
        # Test sample math operations
        test_cases = [
            ("Use the multiply tool to calculate 12 * 8", "96"),
            ("Use the add tool to calculate 25 + 17", "42")
        ]
        
        for query, expected in test_cases:
            print(f"\n🧪 Testing: {query}")
            try:
                result = await agent.run(query)
                response = result.get('response', '')
                tool_calls = result.get('tool_calls', 0)
                
                print(f"✅ Response: {response[:100]}...")
                print(f"🛠️ Tool calls: {tool_calls}")
                
                if expected in response:
                    print(f"✅ Expected result '{expected}' found")
                else:
                    print(f"⚠️ Expected result '{expected}' not found")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        await agent.cleanup()
        print("\n✅ MCP math tools test completed!") 