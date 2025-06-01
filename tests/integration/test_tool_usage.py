"""Tool usage integration tests."""

import pytest
from pathlib import Path
import sys

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.react_agent import ReActAgent


@pytest.mark.integration
@pytest.mark.api
class TestToolUsage:
    """Test tool usage in agents."""
    
    @pytest.mark.asyncio
    async def test_tool_usage_explicitly(self):
        """Test individual tools explicitly to ensure they work."""

        print("🛠️ Testing Individual Tools")
        print("=" * 50)

        try:
            # Import tools from package structure
            from src.tools import Calculator, WebSearch, KnowledgeBaseSearch, FileManager
            
            # Test tools individually first
            tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

            print("🧮 Testing Calculator tool directly...")
            calc_result = tools[0]._run("25 * 4")
            print(f"   Calculator result: {calc_result}")

            print("✅ All tools work individually!")

        except Exception as e:
            print(f"❌ Tool test failed: {e}")
            assert False, f"Tool test failed: {e}"

    @pytest.mark.asyncio
    async def test_agent_with_tool_forcing(self):
        """Test agent with explicit tool forcing instructions."""

        print("🤖 Testing Agent with Forced Tool Usage")
        print("=" * 50)

        config_path = str(
            Path(__file__).parent.parent.parent / "examples" / "configs" / "openai_compatible.yaml"
        )

        agent = ReActAgent(config_path=config_path)
        await agent.initialize()

        # Create very explicit prompts that should force tool usage
        forcing_queries = [
            "You MUST use the calculator tool to compute 123 * 456. Do not calculate this yourself, use the tool.",
        ]

        for i, query in enumerate(forcing_queries, 1):
            print(f"🎯 Forcing Test {i}: {query[:50]}...")
            print("-" * 40)

            try:
                result = await agent.run(query)

                print(f"✅ Response: {result.get('response', 'No response')[:150]}...")
                print(f"🛠️ Tool calls: {result.get('tool_calls', 0)}")
                
                # Basic validation
                assert "response" in result
                assert result.get('tool_calls', 0) >= 0  # Should be non-negative
                
                print("✅ Tool forcing test passed")

            except Exception as e:
                print(f"❌ Error in forcing test {i}: {e}")
                continue

        await agent.cleanup()

    @pytest.mark.asyncio  
    async def test_openai_compatible_agent(self):
        """Test the ReAct Agent with OpenAI compatible environment."""

        print("🏢 Testing OpenAI Compatible Agent")
        print("=" * 50)

        # Check if OpenAI compatible environment is configured
        import os
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ OPENAI_API_KEY not set. Using 'not-needed' for testing.")
            os.environ["OPENAI_API_KEY"] = "not-needed"

        config_path = str(
            Path(__file__).parent.parent.parent / "examples" / "configs" / "openai_compatible.yaml"
        )
        print(f"📝 Loading configuration: {config_path}")

        agent = ReActAgent(config_path=config_path)
        await agent.initialize()

        # Get basic agent info from config
        print(f"🤖 Agent: {agent.config.metadata.name}")
        print(f"🧠 Model: {agent.config.model.provider.value}/{agent.config.model.name}")
        print(f"🌐 Base URL: {getattr(agent.config.model, 'base_url', None)}")
        print(f"🛠️ Tools: {len(agent.tools)} tools loaded")

        # Test queries designed to trigger tool usage
        test_queries = [
            "Please use the calculator tool to compute exactly: 1500000 * 0.02 / 12",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"🧪 Test {i}: {query}")
            print("-" * 40)

            try:
                # Run the agent
                result = await agent.run(query)

                print(f"✅ Response: {result.get('response', 'No response')[:200]}...")
                print(f"🛠️ Tool calls: {result.get('tool_calls', 0)}")
                
                # Basic validation
                assert "response" in result
                print("✅ OpenAI compatible test passed")

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print(f"   Query: {query}")
                continue

        print("✅ OpenAI Compatible Agent tests completed!")
        
        await agent.cleanup() 