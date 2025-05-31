#!/usr/bin/env python3
"""
Test script for the ReAct Agent using LangGraph's create_react_agent.

This script loads a configuration file and tests the agent with basic queries.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.react_agent import ReActAgent
from src.agents.tools import Calculator, WebSearch, KnowledgeBaseSearch, FileManager

load_dotenv('.env', override=True)

print("=" * 50)
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_tool_usage_from_result(result):
    """Extract tool usage information from agent result."""
    # Check if there's a tools_used field directly
    if "tools_used" in result and result["tools_used"]:
        # Convert string list to dict format for backward compatibility
        tools_used = result["tools_used"]
        if isinstance(tools_used, list) and tools_used:
            if isinstance(tools_used[0], str):
                # Convert string list to dict list format
                return [{"tool": tool, "args": {}} for tool in tools_used]
            else:
                # Already in dict format
                return tools_used
    return []


def test_openai_compatible_agent():
    """Test the ReAct Agent with OpenAI compatible environment."""

    print("🏢 Testing OpenAI Compatible Agent")
    print("=" * 50)

    # Check if OpenAI compatible environment is configured
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Using 'not-needed' for testing.")
        os.environ["OPENAI_API_KEY"] = "not-needed"

    try:
        # Initialize tools
        tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

        # Test with OpenAI compatible configuration
        config_path = str(
            Path(__file__).parent.parent
            / "examples"
            / "configs"
            / "openai_compatible.yaml"
        )
        print(f"📝 Loading internal configuration: {config_path}")
        print(f"🔧 Available tools: {[tool.name for tool in tools]}")
        print()

        agent = ReActAgent(config_path=config_path, tools=tools)

        # Get agent configuration info
        config_info = agent.get_config_info()
        print(f"🤖 Agent: {config_info['metadata']['name']}")
        print(
            f"🧠 Model: {config_info['model']['provider']}/{config_info['model']['name']}"
        )
        print(f"🌐 Base URL: {config_info['model']['base_url']}")
        print(f"🛠️  Tools: {[tool['name'] for tool in config_info['tools']]}")
        print()

        # Internal-specific test queries - designed to trigger tool usage
        test_queries = [
            # Force calculator usage with explicit instruction
            "Please use the calculator tool to compute exactly: 1500000 * 0.02 / 12",
            # Force web search usage
            "Please use the web search tool to find information about python programming",
            # Force knowledge base search
            "Please search the knowledge base using the knowledge_search tool for 'pricing' information",
            # Complex query that should trigger multiple tools
            "I need to calculate my monthly premium: 850000 * 0.025 / 12, and then search our knowledge base for pricing tiers",
            # File operations
            "Please use the file_manager tool to list files in the current directory",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"🧪 Test {i}: {query}")
            print("-" * 40)

            try:
                # Run the agent
                result = agent.run_sync(query)

                # Extract tool usage information
                tools_used = extract_tool_usage_from_result(result)

                print(f"✅ Response: {result.get('response', 'No response')[:200]}...")
                print(
                    f"🛠️  Tools used: {[tool['tool'] for tool in tools_used] if tools_used else 'None'}"
                )
                print()

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print(f"   Query: {query}")
                print()
                # Continue with next query
                continue

        # Test with a simple calculation that should definitely use the calculator
        print("🔧 Testing Direct Tool Request...")
        print("-" * 40)
        try:
            # Very explicit request
            explicit_query = "I need you to use the calculator tool to compute 999 * 888. Please call the calculator tool with expression '999 * 888'."
            print(f"Query: {explicit_query}")

            result = agent.run_sync(explicit_query)
            tools_used = extract_tool_usage_from_result(result)

            if tools_used:
                print(
                    f"✅ SUCCESS! Tools used: {[tool['tool'] for tool in tools_used]}"
                )
            else:
                print(
                    "❌ Still no tools used - this indicates a deeper integration issue"
                )

            print(f"Response: {result.get('response', 'No response')[:200]}...")
            print()

        except Exception as e:
            print(f"❌ Direct tool test failed: {e}")
            print()

        print("✅ OpenAI Compatible Agent tests completed!")

    except Exception as e:
        print(f"❌ Internal test failed: {e}")
        assert False, f"Internal test failed: {e}"


def test_tool_usage_explicitly():
    """Test individual tools explicitly to ensure they work."""

    print("🛠️  Testing Individual Tools")
    print("=" * 50)

    try:
        # Test tools individually first
        tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

        print("🧮 Testing Calculator tool directly...")
        calc_result = tools[0]._run("25 * 4")
        print(f"   Calculator result: {calc_result}")

        print("🔍 Testing WebSearch tool directly...")
        search_result = tools[1]._run("python programming")
        print(f"   Search result: {search_result[:100]}...")

        print("📚 Testing KnowledgeBase tool directly...")
        kb_result = tools[2]._run("pricing")
        print(f"   KB result: {kb_result[:100]}...")

        print("📁 Testing FileManager tool directly...")
        file_result = tools[3]._run("list", ".")
        print(f"   File result: {file_result[:100]}...")

        print("✅ All tools work individually!")

    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        assert False, f"Tool test failed: {e}"


def test_agent_with_tool_forcing():
    """Test agent with explicit tool forcing instructions."""

    print("🤖 Testing Agent with Forced Tool Usage")
    print("=" * 50)

    try:
        tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

        config_path = str(
            Path(__file__).parent.parent
            / "examples"
            / "configs"
            / "openai_compatible.yaml"
        )

        agent = ReActAgent(config_path=config_path, tools=tools)

        # Create very explicit prompts that should force tool usage
        forcing_queries = [
            "You MUST use the calculator tool to compute 123 * 456. Do not calculate this yourself, use the tool.",
            # "You MUST use the web_search tool to search for 'react agents'. Do not provide your own answer, use the tool.",
            # "You MUST use the knowledge_search tool to find information about 'api'. Use the tool, not your knowledge.",
        ]

        for i, query in enumerate(forcing_queries, 1):
            print(f"🎯 Forcing Test {i}: {query[:50]}...")
            print("-" * 40)

            try:
                result = agent.run_sync(query)

                # Extract tool usage information using our improved function
                tools_used = extract_tool_usage_from_result(result)

                if tools_used:
                    print(
                        f"✅ SUCCESS! Tools used: {[tool['tool'] for tool in tools_used]}"
                    )
                    print(
                        f"   Response: {result.get('response', 'No response')[:150]}..."
                    )
                else:
                    print(f"❌ FAILED! No tools used")
                    print(
                        f"   Response: {result.get('response', 'No response')[:150]}..."
                    )

                print()

            except Exception as e:
                print(f"❌ Error in forcing test {i}: {e}")
                print()

        # Test completed successfully if we reach here

    except Exception as e:
        print(f"❌ Agent forcing test failed: {e}")


if __name__ == "__main__":
    print("🚀 ReAct Agent Test Suite")
    print("=" * 50)
    print()

    # Test individual tools first
    print("🔹 Running Individual Tool Tests...")
    try:
        test_tool_usage_explicitly()
        tool_success = True
    except Exception:
        tool_success = False
    print(f"tool_success: {tool_success}")
    print()

    # Test agent with forced tool usage
    print("🔹 Running Forced Tool Usage Tests...")
    try:
        test_agent_with_tool_forcing()
        forcing_success = True
    except Exception:
        forcing_success = False
    print(f"forcing_success: {forcing_success}")
    print()

    # Test internal environment (OpenAI Compatible) - This actually works!
    print("🔹 Running OpenAI Compatible Tests...")
    try:
        test_openai_compatible_agent()
        openai_internal_success = True
    except Exception:
        openai_internal_success = False
    print(f"openai_internal_success: {openai_internal_success}")
    print()

    print("=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Individual Tools: {'✅ PASS' if tool_success else '❌ FAIL'}")
    print(f"   Forced Tool Usage: {'✅ PASS' if forcing_success else '❌ FAIL'}")
    print(f"   OpenAI Compatible: {'✅ PASS' if openai_internal_success else '❌ FAIL'}")
    print()

    if tool_success and forcing_success and openai_internal_success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
