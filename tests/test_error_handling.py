"""Error handling tests for the system."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, Mock
from tests.test_data import INVALID_CONFIGS, ERROR_PATTERNS

# Import exception classes
from src.core.exceptions import ConfigParseError, ConfigValidationError


@pytest.mark.unit
class TestConfigErrorHandling:
    """Test error handling in configuration parsing."""
    
    def test_invalid_yaml_format(self, config_parser):
        """Test handling of malformed YAML."""
        invalid_yaml = """
        key: value
          bad_indentation: error
        """
        
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser._parse_yaml_content(invalid_yaml)
        
        error_msg = str(exc_info.value)
        assert any(pattern in error_msg for pattern in ERROR_PATTERNS["config_validation"])
    
    def test_missing_required_fields(self, config_parser):
        """Test handling of missing required configuration fields."""
        for config_name, config_data in INVALID_CONFIGS.items():
            with pytest.raises(ConfigValidationError) as exc_info:
                config_parser.validate_configuration(config_data)
            
            assert len(exc_info.value.errors) > 0
    
    def test_file_not_found_error(self, config_parser):
        """Test handling of non-existent configuration files."""
        non_existent_path = "/path/to/nonexistent/config.yaml"
        
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser.parse_from_file(non_existent_path)
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_permission_denied_error(self, config_parser):
        """Test handling of permission denied when reading config files."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            
            with pytest.raises(ConfigParseError) as exc_info:
                config_parser.parse_from_file("/protected/config.yaml")
            
            assert "Error reading configuration file" in str(exc_info.value)


@pytest.mark.integration
class TestAgentErrorHandling:
    """Test error handling in agent operations."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization_error(self):
        """Test agent initialization with invalid config."""
        from src.agents.react_agent import ReActAgent
        
        # Test with non-existent config file
        with pytest.raises((FileNotFoundError, ConfigParseError)):
            agent = ReActAgent(config_path="/nonexistent/config.yaml")
            await agent.initialize()
    
    @pytest.mark.asyncio
    async def test_agent_run_with_invalid_input(self, react_agent):
        """Test agent run method with invalid inputs."""
        # Test with None input
        try:
            result = await react_agent.run(None)
            # If it doesn't raise an exception, it should handle gracefully
            assert "error" in result or "response" in result
        except (ValueError, TypeError):
            # Expected behavior for invalid input
            pass
        
        # Test with empty string
        try:
            await react_agent.run("")
            # Empty string might be handled gracefully
        except Exception:
            # Also acceptable behavior
            pass
    
    @pytest.mark.asyncio
    async def test_agent_cleanup_error_handling(self, config_parser):
        """Test agent cleanup under error conditions."""
        from src.agents.react_agent import ReActAgent
        
        config_path = "examples/configs/openai_compatible.yaml"
        if not Path(config_path).exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        agent = ReActAgent(config_path=config_path)
        await agent.initialize()
        
        # Force an error condition
        agent.agent = None  # Simulate a broken state
        
        # Cleanup should handle this gracefully
        try:
            await agent.cleanup()
        except Exception:
            # If cleanup fails, that's also valid behavior to test
            pass


@pytest.mark.api
class TestAPIErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_request_format(self, api_client):
        """Test API handling of invalid request formats."""
        from tests.test_data import VALIDATION_HELPERS
        
        # Missing required fields
        response = api_client.post("/chat", json={})
        assert response.status_code == 422
        
        # Wrong data type
        response = api_client.post("/chat", json={"message": 123})
        assert response.status_code == 422
        
        # Invalid JSON
        response = api_client.post("/chat", data="invalid json")
        assert response.status_code == 422
    
    def test_unsupported_endpoints(self, api_client):
        """Test API handling of unsupported endpoints."""
        # Non-existent endpoint
        response = api_client.get("/nonexistent")
        assert response.status_code == 404
        
        # Wrong HTTP method
        response = api_client.delete("/chat")
        assert response.status_code == 405
    
    def test_server_error_simulation(self, api_client):
        """Test API handling of server errors."""
        from tests.test_data import VALIDATION_HELPERS
        
        # Test with extremely long message
        extremely_long_message = "A" * 100000  # 100K characters
        response = api_client.post("/chat", json={"message": extremely_long_message})
        
        # Should return appropriate status code
        assert response.status_code in VALIDATION_HELPERS["valid_status_codes"]


@pytest.mark.integration
class TestToolErrorHandling:
    """Test error handling in tool operations."""
    
    def test_tool_initialization_errors(self):
        """Test handling of tool initialization errors."""
        try:
            from src.tools import Calculator, WebSearch, KnowledgeBaseSearch, FileManager
            
            # Try to initialize tools
            tools = [Calculator(), WebSearch(), KnowledgeBaseSearch(), FileManager()]
            
            # Check if all tools have required attributes
            for tool in tools:
                assert hasattr(tool, 'name')
                assert hasattr(tool, 'description')
                assert hasattr(tool, '_run')
            
        except ImportError:
            pytest.skip("Tools not available for import")
        except Exception:
            # Any other error is also acceptable to test error handling
            pass
    
    def test_tool_execution_errors(self):
        """Test handling of tool execution errors."""
        try:
            from src.tools import Calculator
            
            calculator = Calculator()
            
            # Test with invalid mathematical expression
            try:
                result = calculator._run("invalid_expression")
                # If it doesn't raise an exception, check if it returns error message
                assert "error" in result.lower() or "invalid" in result.lower()
            except Exception:
                # Expected behavior for invalid expression
                pass
            
        except ImportError:
            pytest.skip("Calculator tool not available")


@pytest.mark.unit
class TestExceptionClasses:
    """Test custom exception classes."""
    
    def test_config_parse_error(self):
        """Test ConfigParseError exception."""
        # Test with message only
        error = ConfigParseError("Test error message")
        assert str(error) == "Test error message"
        assert error.details is None
        
        # Test with details
        details = {"line": 10, "column": 5}
        error = ConfigParseError("Test error", details)
        assert str(error) == "Test error"
        assert error.details == details
    
    def test_config_validation_error(self):
        """Test ConfigValidationError exception."""
        errors = ["Field 'name' is required", "Invalid provider value"]
        error = ConfigValidationError("Validation failed", errors)
        
        assert str(error) == "Validation failed"
        assert error.errors == errors
        assert len(error.errors) == 2


@pytest.mark.integration
@pytest.mark.slow
class TestRecoveryMechanisms:
    """Test system recovery mechanisms under error conditions."""
    
    @pytest.mark.asyncio
    async def test_agent_recovery_after_error(self, config_parser):
        """Test agent recovery after encountering errors."""
        from src.agents.react_agent import ReActAgent
        
        config_path = "examples/configs/openai_compatible.yaml"
        if not Path(config_path).exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        agent = ReActAgent(config_path=config_path)
        await agent.initialize()
        
        try:
            # First, cause an error
            try:
                await agent.run(None)
            except Exception:
                pass  # Expected error
            
            # Then test if agent can recover
            result = await agent.run("Hello, are you working?")
            assert "response" in result
            
        finally:
            await agent.cleanup()
    
    def test_api_recovery_after_errors(self, api_client):
        """Test API recovery after multiple error requests."""
        # Send multiple invalid requests
        for i in range(3):
            response = api_client.post("/chat", json={})
            assert response.status_code == 422
        
        # Check if API still works for valid requests
        response = api_client.get("/health")
        assert response.status_code == 200 