"""
pytest configuration and shared fixtures for all tests.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.react_agent import ReActAgent
from src.core.config_parser import ConfigParser
from src.core.agent_manager import AgentManager
from src.api.app import app


# Test configuration
pytest_plugins = ("pytest_asyncio",)


# Common path helpers to avoid hardcoding
def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_config_path(config_name: str) -> str:
    """Get path to a config file."""
    return str(get_project_root() / "examples" / "configs" / f"{config_name}.yaml")


def get_test_config_path(config_name: str) -> str:
    """Get path to a test config file."""
    return str(get_project_root() / "tests" / "examples" / "configs" / f"{config_name}.yaml")


@pytest.fixture
def sample_valid_config():
    """Sample valid configuration for testing."""
    from tests.test_data import VALID_CONFIGS
    return VALID_CONFIGS["openai_compatible"]


@pytest.fixture
def sample_invalid_config():
    """Sample invalid configuration for testing."""
    from tests.test_data import INVALID_CONFIGS
    return INVALID_CONFIGS["missing_metadata"]


@pytest.fixture
def mock_openai_api_key():
    """Mock OpenAI API key for testing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"}):
        yield "test-key-123"


@pytest_asyncio.fixture
async def react_agent():
    """Common ReActAgent fixture with proper cleanup."""
    from tests.test_data import VALID_CONFIGS
    from src.schemas.agent_config import AgentConfig
    
    # Use test configuration instead of file to avoid file dependency issues
    config_data = VALID_CONFIGS["openai_compatible"]
    config = AgentConfig(**config_data)
    
    agent = ReActAgent(config=config)
    
    try:
        await agent.initialize()
        yield agent
    finally:
        await agent.cleanup()


@pytest_asyncio.fixture
async def agent_manager():
    """Common AgentManager fixture."""
    from tests.test_data import VALID_CONFIGS
    from src.schemas.agent_config import AgentConfig
    
    manager = AgentManager()
    
    # Use test configuration instead of file
    config_data = VALID_CONFIGS["openai_compatible"]
    config = AgentConfig(**config_data)
    
    try:
        # Check if initialize_agent_with_config method exists, fallback to initialize_agent
        if hasattr(manager, 'initialize_agent_with_config'):
            await manager.initialize_agent_with_config(config)
        else:
            # Create a temporary config file for manager
            import tempfile
            import yaml
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f)
                temp_config_path = f.name
            
            try:
                await manager.initialize_agent(temp_config_path)
            finally:
                # Clean up temp file
                os.unlink(temp_config_path)
        
        yield manager
    finally:
        manager.shutdown()


@pytest.fixture
def api_client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def config_parser():
    """ConfigParser fixture."""
    return ConfigParser()


@pytest.fixture
def mock_file_system():
    """Mock file system for testing."""
    with patch('builtins.open'), patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


class TestUtils:
    """Utility class for common test operations."""
    
    @staticmethod
    def validate_agent_response(result):
        """Validate standard agent response structure."""
        from tests.test_data import VALIDATION_HELPERS
        
        # Check required fields
        for field in VALIDATION_HELPERS["required_response_fields"]:
            assert field in result, f"Result should contain '{field}' field"
        
        # Validate response content
        response = result["response"]
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"
        
        return True
    
    @staticmethod
    def validate_response_quality(result, min_length=10):
        """Validate response quality with basic checks."""
        response = result.get("response", "")
        
        # Basic quality checks
        assert len(response) >= min_length, f"Response too short: {len(response)} chars"
        assert not response.isspace(), "Response should not be only whitespace"
        
        # Check for basic structure (not just random characters)
        has_letters = any(c.isalpha() for c in response)
        assert has_letters, "Response should contain alphabetic characters"
        
        return True
    
    @staticmethod
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
    
    @staticmethod
    def validate_config_structure(config_data):
        """Validate configuration structure."""
        required_fields = ["metadata", "model", "prompt"]
        for field in required_fields:
            assert field in config_data, f"Missing required field: {field}"
        
        # Validate metadata
        metadata = config_data["metadata"]
        assert "name" in metadata, "Metadata missing 'name' field"
        assert "version" in metadata, "Metadata missing 'version' field"
        
        return True
    
    @staticmethod
    def create_mock_agent_response(text: str = "Mock response", tool_calls: int = 0):
        """Create a mock agent response for testing."""
        return {
            "response": text,
            "tool_calls": tool_calls,
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "model": "mock-model"
            }
        }
    
    @staticmethod
    def validate_concurrent_results(results, min_success_rate=0.5):
        """Validate results from concurrent operations."""
        from tests.test_data import TEST_CONSTANTS
        
        total_count = len(results)
        successful_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                continue
            try:
                TestUtils.validate_agent_response(result)
                successful_count += 1
            except AssertionError:
                continue
        
        success_rate = successful_count / total_count if total_count > 0 else 0
        min_rate = min_success_rate or TEST_CONSTANTS["min_success_rate"]
        
        assert success_rate >= min_rate, f"Success rate {success_rate:.1%} below minimum {min_rate:.1%}"
        
        return successful_count, success_rate


@pytest.fixture
def test_utils():
    """Test utilities fixture."""
    return TestUtils 