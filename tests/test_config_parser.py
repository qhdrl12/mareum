"""Tests for the ConfigParser class."""

import json
import pytest
import yaml
from pathlib import Path
from unittest.mock import mock_open, patch
from src.core.config_parser import ConfigParser, ConfigParseError, ConfigValidationError


class TestConfigParser:
    """Test cases for ConfigParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a ConfigParser instance for testing."""
        return ConfigParser()
    
    @pytest.fixture
    def sample_valid_config(self):
        """Sample valid configuration for testing."""
        return {
            "metadata": {
                "name": "test-agent",
                "version": "1.0.0",
                "description": "Test agent"
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4",
                "credentials_key": "OPENAI_API_KEY"
            },
            "prompt": {
                "system": "You are a helpful assistant."
            }
        }
    
    @pytest.fixture
    def sample_invalid_config(self):
        """Sample invalid configuration for testing."""
        return {
            "metadata": {
                # Missing required 'name' field
                "version": "1.0.0"
            },
            "model": {
                "provider": "invalid_provider",  # Invalid provider
                "name": "gpt-4"
                # Missing required 'credentials_key' field
            }
        }
    
    def test_init_default_schema_path(self, parser):
        """Test ConfigParser initialization with default schema path."""
        assert parser.schema_path is None
        assert parser._schema is None
    
    def test_init_custom_schema_path(self):
        """Test ConfigParser initialization with custom schema path."""
        custom_path = "/path/to/schema.json"
        parser = ConfigParser(schema_path=custom_path)
        assert parser.schema_path == custom_path
    
    def test_parse_yaml_content_valid(self, parser, sample_valid_config):
        """Test parsing valid YAML content."""
        yaml_content = yaml.dump(sample_valid_config)
        result = parser._parse_yaml_content(yaml_content)
        assert result == sample_valid_config
    
    def test_parse_yaml_content_with_comments(self, parser):
        """Test parsing YAML with comments."""
        yaml_content = '''
        # Configuration for test agent
        metadata:
          name: "test-agent"  # Agent name
        model:
          provider: "openai"  # Use OpenAI
        '''
        result = parser._parse_yaml_content(yaml_content)
        assert result['metadata']['name'] == "test-agent"
        assert result['model']['provider'] == "openai"
    
    def test_parse_yaml_content_multiline_strings(self, parser):
        """Test parsing YAML with multiline strings."""
        yaml_content = '''
        prompt:
          system: |
            You are a helpful assistant.
            Always be polite and professional.
          description: >
            This is a folded multiline string
            that will be joined with spaces.
        '''
        result = parser._parse_yaml_content(yaml_content)
        assert "Always be polite" in result['prompt']['system']
        assert "folded multiline" in result['prompt']['description']
    
    def test_parse_yaml_content_invalid(self, parser):
        """Test parsing invalid YAML content."""
        invalid_yaml = '''
        key: value
          invalid_indentation: test
        '''
        with pytest.raises(ConfigParseError) as exc_info:
            parser._parse_yaml_content(invalid_yaml)
        assert "Invalid YAML format" in str(exc_info.value)
    
    def test_parse_yaml_content_empty(self, parser):
        """Test parsing empty content."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser._parse_yaml_content('')
        assert "Configuration content is empty" in str(exc_info.value)
    
    def test_parse_yaml_content_whitespace_only(self, parser):
        """Test parsing whitespace-only content."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser._parse_yaml_content('   \n  \t  ')
        assert "Configuration content is empty" in str(exc_info.value)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_success(self, mock_exists, mock_file, parser):
        """Test successful schema loading."""
        schema = parser._load_schema()
        assert schema == {"key": "value"}
        assert parser._schema == {"key": "value"}  # Should be cached
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_schema_file_not_found(self, mock_exists, parser):
        """Test schema loading when file doesn't exist."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser._load_schema()
        assert "Schema file not found" in str(exc_info.value)
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_invalid_json(self, mock_exists, mock_file, parser):
        """Test schema loading with invalid JSON."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser._load_schema()
        assert "Invalid JSON in schema file" in str(exc_info.value)
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_load_schema_permission_error(self, mock_open, mock_exists, parser):
        """Test schema loading with permission error."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser._load_schema()
        assert "Error loading schema file" in str(exc_info.value)
    
    def test_format_validation_errors_simple(self, parser):
        """Test formatting of simple validation errors."""
        from jsonschema import ValidationError as JsonSchemaValidationError, validate
        
        # Create a real validation error by validating against a schema
        try:
            validate({"key": "value"}, {"required": ["name"]})
        except JsonSchemaValidationError as error:
            errors = parser._format_validation_errors(error)
            assert len(errors) == 1
            assert "'name' is a required property" in errors[0]
    
    def test_format_validation_errors_with_context(self, parser):
        """Test formatting of validation errors with context."""
        from jsonschema import ValidationError as JsonSchemaValidationError, validate
        
        # Create a schema with nested validation that might produce context errors
        schema = {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "required": ["name"]
                }
            }
        }
        
        # Test with data that should fail validation
        try:
            validate({"metadata": {}}, schema)
        except JsonSchemaValidationError as error:
            errors = parser._format_validation_errors(error)
            assert len(errors) >= 1
            assert "'name' is a required property" in errors[0]
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='metadata:\n  name: "test"')
    def test_parse_from_file_success_yaml(self, mock_file, mock_exists, parser):
        """Test successful YAML file parsing."""
        # Mock the schema loading
        with patch.object(parser, '_load_schema', return_value={}):
            with patch.object(parser, 'validate_configuration', return_value={"metadata": {"name": "test"}}):
                with patch.object(parser, 'normalize_configuration', return_value={"metadata": {"name": "test"}}):
                    result = parser.parse_from_file("/path/to/config.yaml")
                    assert result["metadata"]["name"] == "test"
    
    @patch('pathlib.Path.exists', return_value=True)
    def test_parse_from_file_invalid_extension(self, mock_exists, parser):
        """Test file parsing with invalid extension."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_from_file("/path/to/config.json")
        assert "Only YAML files (.yaml, .yml) are supported" in str(exc_info.value)
    
    @patch('pathlib.Path.exists', return_value=True)
    def test_parse_from_file_valid_extensions(self, mock_exists, parser):
        """Test file parsing with valid YAML extensions."""
        valid_files = ["/path/to/config.yaml", "/path/to/config.yml"]
        
        for file_path in valid_files:
            with patch('builtins.open', new_callable=mock_open, read_data='metadata:\n  name: "test"'):
                with patch.object(parser, '_load_schema', return_value={}):
                    with patch.object(parser, 'validate_configuration', return_value={"metadata": {"name": "test"}}):
                        with patch.object(parser, 'normalize_configuration', return_value={"metadata": {"name": "test"}}):
                            result = parser.parse_from_file(file_path)
                            assert result["metadata"]["name"] == "test"
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_parse_from_file_not_found(self, mock_exists, parser):
        """Test file parsing when file doesn't exist."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_from_file("/path/to/nonexistent.yaml")
        assert "Configuration file not found" in str(exc_info.value)
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_parse_from_file_permission_error(self, mock_open, mock_exists, parser):
        """Test file parsing with permission error."""
        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_from_file("/path/to/config.yaml")
        assert "Error reading configuration file" in str(exc_info.value)
    
    def test_apply_defaults_simple(self, parser):
        """Test applying simple default values."""
        data = {"key": "value"}
        schema = {
            "properties": {
                "key": {"type": "string"},
                "default_key": {"type": "string", "default": "default_value"}
            }
        }
        parser._apply_defaults(data, schema)
        assert data["default_key"] == "default_value"
        assert data["key"] == "value"  # Existing value unchanged
    
    def test_apply_defaults_nested(self, parser):
        """Test applying defaults to nested objects."""
        data = {
            "metadata": {
                "name": "test"
            }
        }
        schema = {
            "properties": {
                "metadata": {
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string", "default": "1.0.0"}
                    }
                }
            }
        }
        parser._apply_defaults(data, schema)
        assert data["metadata"]["version"] == "1.0.0"
        assert data["metadata"]["name"] == "test"
    
    def test_apply_defaults_array(self, parser):
        """Test applying defaults to array items."""
        data = [{"name": "item1"}, {"name": "item2"}]
        schema = {
            "items": {
                "properties": {
                    "name": {"type": "string"},
                    "enabled": {"type": "boolean", "default": True}
                }
            }
        }
        parser._apply_defaults(data, schema)
        assert data[0]["enabled"] is True
        assert data[1]["enabled"] is True
        assert data[0]["name"] == "item1"
    
    def test_normalize_configuration(self, parser):
        """Test configuration normalization."""
        config_data = {"key": "value"}
        schema = {
            "properties": {
                "key": {"type": "string"},
                "default_key": {"type": "string", "default": "default_value"}
            }
        }
        
        with patch.object(parser, '_load_schema', return_value=schema):
            result = parser.normalize_configuration(config_data)
            
        assert result["key"] == "value"
        assert result["default_key"] == "default_value"
        # Original data should remain unchanged
        assert "default_key" not in config_data
    
    def test_yaml_with_different_indentation(self, parser):
        """Test YAML parsing with different indentation styles."""
        yaml_content = '''
metadata:
    name: "test-agent"
    config:
        nested_value: "test"
model:
  provider: "openai"
  settings:
    temperature: 0.7
'''
        result = parser._parse_yaml_content(yaml_content)
        assert result['metadata']['name'] == "test-agent"
        assert result['metadata']['config']['nested_value'] == "test"
        assert result['model']['settings']['temperature'] == 0.7
    
    def test_yaml_with_multiline_strings(self, parser):
        """Test YAML parsing with various multiline string styles."""
        yaml_content = '''
literal_string: |
  This is a literal string.
  Line breaks are preserved.
  
folded_string: >
  This is a folded string.
  Line breaks become spaces.
  
plain_string: This is a plain string
'''
        result = parser._parse_yaml_content(yaml_content)
        assert "Line breaks are preserved" in result['literal_string']
        assert "Line breaks become spaces" in result['folded_string']
        assert result['plain_string'] == "This is a plain string"


class TestConfigParseError:
    """Test cases for ConfigParseError exception."""
    
    def test_init_message_only(self):
        """Test ConfigParseError initialization with message only."""
        error = ConfigParseError("Test error message")
        assert str(error) == "Test error message"
        assert error.details is None
    
    def test_init_with_details(self):
        """Test ConfigParseError initialization with details."""
        details = {"file": "config.yaml", "line": 10}
        error = ConfigParseError("Test error message", details)
        assert str(error) == "Test error message"
        assert error.details == details


class TestConfigValidationError:
    """Test cases for ConfigValidationError exception."""
    
    def test_init(self):
        """Test ConfigValidationError initialization."""
        errors = ["Error 1", "Error 2"]
        error = ConfigValidationError("Validation failed", errors)
        assert str(error) == "Validation failed"
        assert error.errors == errors 