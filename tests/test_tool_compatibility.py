"""
Test individual tool integration with different approaches.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.tools import Calculator, WebSearch, KnowledgeBaseSearch, FileManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_langchain_tool_integration():
    """Test how LangChain tools work with different LLM providers."""

    print("🧪 Testing LangChain Tool Integration")
    print("=" * 50)

    # Initialize tools
    tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

    print("📋 Tool Information:")
    for tool in tools:
        print(f"   {tool.name}: {tool.description}")
        print(f"   Args schema: {tool.args_schema}")
        print(f"   Return direct: {getattr(tool, 'return_direct', False)}")
        print()

    # Test tool calls directly
    print("🔧 Testing Direct Tool Calls:")

    try:
        print("Calculator test:")
        result = tools[0]._run("25 * 4 + 10")
        print(f"   Result: {result}")
        assert result is not None, "Calculator should return a result"

        print("WebSearch test:")
        result = tools[1]._run("python programming")
        print(f"   Result: {result[:100]}...")
        assert result is not None, "WebSearch should return a result"

        print("KnowledgeBase test:")
        result = tools[2]._run("pricing")
        print(f"   Result: {result[:100]}...")
        assert result is not None, "KnowledgeBase should return a result"

        print("FileManager test:")
        result = tools[3]._run("list", ".")
        print(f"   Result: {result[:100]}...")
        assert result is not None, "FileManager should return a result"

        print("✅ All tool integration tests passed!")

    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        assert False, f"Tool integration test failed: {e}"


def test_tool_compatibility():
    """Test tool format compatibility with different LLM formats."""

    print("🔍 Testing Tool Format Compatibility")
    print("=" * 50)

    tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]

    for tool in tools:
        print(f"🛠️  Tool: {tool.name}")

        # Check if tool has proper LangChain structure
        has_name = hasattr(tool, "name")
        has_description = hasattr(tool, "description")
        has_args_schema = hasattr(tool, "args_schema")
        has_run = hasattr(tool, "_run")

        print(f"   ✅ Name: {has_name}")
        print(f"   ✅ Description: {has_description}")
        print(f"   ✅ Args Schema: {has_args_schema}")
        print(f"   ✅ Run Method: {has_run}")

        # Assert that all required attributes exist
        assert has_name, f"Tool {tool.__class__.__name__} should have a name attribute"
        assert has_description, f"Tool {tool.__class__.__name__} should have a description attribute"
        assert has_args_schema, f"Tool {tool.__class__.__name__} should have an args_schema attribute"
        assert has_run, f"Tool {tool.__class__.__name__} should have a _run method"

        # Test tool schema
        if has_args_schema:
            try:
                schema = tool.args_schema.model_json_schema()
                print(f"   📋 Schema Keys: {list(schema.keys())}")
                print(f"   📋 Properties: {list(schema.get('properties', {}).keys())}")
                assert isinstance(schema, dict), "Schema should be a dictionary"
                assert 'properties' in schema, "Schema should have properties"
            except Exception as e:
                print(f"   ❌ Schema Error: {e}")
                assert False, f"Schema validation failed for {tool.name}: {e}"

        print()

    print("✅ All tool compatibility tests passed!")


if __name__ == "__main__":
    print("🔬 Tool Compatibility Test Suite")
    print("=" * 50)
    print()

    # Test basic tool functionality
    integration_success = True
    try:
        test_langchain_tool_integration()
        print("Integration success: True")
    except Exception as e:
        integration_success = False
        print(f"Integration success: False - {e}")
    print()

    # Test tool compatibility
    compatibility_success = True
    try:
        test_tool_compatibility()
        print("Compatibility success: True")
    except Exception as e:
        compatibility_success = False
        print(f"Compatibility success: False - {e}")
    print()

    if integration_success and compatibility_success:
        print("✅ All tool tests passed!")
    else:
        print("❌ Some tool tests failed!")
