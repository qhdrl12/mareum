"""Unit tests for ConfigParser class."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import mock_open, patch

from src.core.config_parser import (
    ConfigParser, 
    ConfigParseError, 
    ConfigValidationError
)
from src.schemas.agent_config import AgentConfig
from tests.test_data import VALID_CONFIGS, INVALID_CONFIGS


@pytest.mark.unit
class TestConfigParser:
    """Test cases for ConfigParser class."""
    
    def test_init(self, config_parser):
        """Test ConfigParser initialization."""
        assert isinstance(config_parser, ConfigParser)
    
    def test_parse_yaml_content_valid(self, config_parser):
        """Test parsing valid YAML content."""
        config_data = VALID_CONFIGS["basic"]
        yaml_content = yaml.dump(config_data)
        result = config_parser._parse_yaml_content(yaml_content)
        assert result == config_data
    
    def test_parse_yaml_content_with_comments(self, config_parser):
        """Test parsing YAML with comments."""
        yaml_content = '''
        # Configuration for test agent
        metadata:
          name: "test-agent"  # Agent name
        model:
          provider: "openai"  # Use OpenAI
          name: "gpt-4o-mini"
          api_key: "OPENAI_API_KEY"
        prompt:
          system_prompt: "You are helpful"
        '''
        result = config_parser._parse_yaml_content(yaml_content)
        assert result['metadata']['name'] == "test-agent"
        assert result['model']['provider'] == "openai"
    
    def test_parse_yaml_content_invalid(self, config_parser):
        """Test parsing invalid YAML content."""
        invalid_yaml = '''
        key: value
          invalid_indentation: test
        '''
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser._parse_yaml_content(invalid_yaml)
        assert "Invalid YAML format" in str(exc_info.value)
    
    def test_parse_yaml_content_empty(self, config_parser):
        """Test parsing empty content."""
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser._parse_yaml_content('')
        assert "Configuration content is empty" in str(exc_info.value)
    
    @pytest.mark.parametrize("config_key", ["basic", "openai_compatible", "with_tools"])
    def test_validate_configuration_valid(self, config_parser, config_key):
        """Test validation of valid configurations."""
        config_data = VALID_CONFIGS[config_key]
        result = config_parser.validate_configuration(config_data)
        assert isinstance(result, AgentConfig)
        assert result.metadata.name == config_data["metadata"]["name"]
    
    @pytest.mark.parametrize("config_key", ["missing_name", "missing_model", "invalid_provider"])
    def test_validate_configuration_invalid(self, config_parser, config_key):
        """Test validation of invalid configurations."""
        config_data = INVALID_CONFIGS[config_key]
        with pytest.raises(ConfigValidationError) as exc_info:
            config_parser.validate_configuration(config_data)
        assert "Configuration validation failed" in str(exc_info.value)
        assert len(exc_info.value.errors) > 0
    
    def test_parse_from_string_valid(self, config_parser):
        """Test parsing from valid YAML string."""
        config_data = VALID_CONFIGS["basic"]
        yaml_content = yaml.dump(config_data)
        result = config_parser.parse_from_string(yaml_content)
        assert isinstance(result, AgentConfig)
        assert result.metadata.name == "test-agent"
    
    def test_parse_from_string_invalid(self, config_parser):
        """Test parsing from invalid YAML string."""
        config_data = INVALID_CONFIGS["missing_model"]
        yaml_content = yaml.dump(config_data)
        with pytest.raises(ConfigValidationError):
            config_parser.parse_from_string(yaml_content)
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_parse_from_file_success(self, mock_file, mock_exists, config_parser):
        """Test successful file parsing."""
        config_data = VALID_CONFIGS["basic"]
        yaml_content = yaml.dump(config_data)
        mock_file.return_value.read.return_value = yaml_content
        
        result = config_parser.parse_from_file("/path/to/config.yaml")
        assert isinstance(result, AgentConfig)
        assert result.metadata.name == "test-agent"
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_parse_from_file_not_found(self, mock_exists, config_parser):
        """Test file parsing when file doesn't exist."""
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser.parse_from_file("/nonexistent/config.yaml")
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_parse_from_file_invalid_extension(self, config_parser):
        """Test file parsing with invalid extension."""
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser.parse_from_file("/path/to/config.json")
        assert "Only YAML files (.yaml, .yml) are supported" in str(exc_info.value)
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_parse_from_file_permission_error(self, mock_open, mock_exists, config_parser):
        """Test file parsing with permission error."""
        with pytest.raises(ConfigParseError) as exc_info:
            config_parser.parse_from_file("/path/to/config.yaml")
        assert "Error reading configuration file" in str(exc_info.value)
    
    def test_to_dict(self, config_parser):
        """Test converting AgentConfig to dictionary."""
        config_data = VALID_CONFIGS["basic"]
        config = config_parser.validate_configuration(config_data)
        result = config_parser.to_dict(config)
        
        assert isinstance(result, dict)
        assert result['metadata']['name'] == "test-agent"
        assert result['model']['provider'] == "openai"
    
    def test_to_yaml(self, config_parser):
        """Test converting AgentConfig to YAML string."""
        config_data = VALID_CONFIGS["basic"]
        config = config_parser.validate_configuration(config_data)
        yaml_str = config_parser.to_yaml(config)
        
        assert isinstance(yaml_str, str)
        assert "name: test-agent" in yaml_str
        assert "provider: openai" in yaml_str
    
    @patch('builtins.open', new_callable=mock_open)
    def test_to_yaml_save_file(self, mock_file, config_parser):
        """Test saving AgentConfig to YAML file."""
        config_data = VALID_CONFIGS["basic"]
        config = config_parser.validate_configuration(config_data)
        yaml_str = config_parser.to_yaml(config, "/path/to/output.yaml")
        
        mock_file.assert_called_once_with("/path/to/output.yaml", 'w', encoding='utf-8')
        mock_file().write.assert_called_once()


@pytest.mark.unit
class TestConfigParseError:
    """Test ConfigParseError exception class."""
    
    def test_init_message_only(self):
        """Test ConfigParseError initialization with message only."""
        error = ConfigParseError("Test error")
        assert str(error) == "Test error"
        assert error.details is None
    
    def test_init_with_details(self):
        """Test ConfigParseError initialization with details."""
        details = {"line": 5, "column": 10}
        error = ConfigParseError("Test error", details)
        assert str(error) == "Test error"
        assert error.details == details


@pytest.mark.unit
class TestConfigValidationError:
    """Test ConfigValidationError exception class."""
    
    def test_init(self):
        """Test ConfigValidationError initialization."""
        errors = ["Error 1", "Error 2"]
        error = ConfigValidationError("Validation failed", errors)
        assert str(error) == "Validation failed"
        assert error.errors == errors 