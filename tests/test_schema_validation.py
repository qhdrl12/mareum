"""
Tests for schema validation system.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

from src.utils.schema_validator import SchemaValidator, ValidationResult
from src.utils.config_loader import ConfigLoader


class TestSchemaValidator:
    """Test cases for SchemaValidator."""
    
    def test_valid_config_dict(self):
        """Test validation of a valid configuration dictionary."""
        config_data = {
            "metadata": {
                "name": "test-agent",
                "description": "Test agent",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "gpt-4"
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        result = SchemaValidator.validate_dict(config_data)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_config_dict(self):
        """Test validation of an invalid configuration dictionary."""
        config_data = {
            "metadata": {
                "name": "test-agent"
                # Missing required fields
            },
            "model": {
                "provider": "invalid_provider",  # Invalid provider
                "model_id": "gpt-4"
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        result = SchemaValidator.validate_dict(config_data)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_config_with_warnings(self):
        """Test configuration that's valid but has warnings."""
        config_data = {
            "metadata": {
                "name": "test-agent",
                "description": "Test agent",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "gpt-4",
                "parameters": {
                    "temperature": 2.0,  # Very high temperature - should warn
                    "max_tokens": 50     # Very low max_tokens - should warn
                }
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        result = SchemaValidator.validate_dict(config_data)
        assert result.is_valid
        assert len(result.warnings) > 0
    
    def test_yaml_file_validation(self):
        """Test validation of YAML file."""
        config_data = {
            "metadata": {
                "name": "test-agent",
                "description": "Test agent",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "gpt-4"
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            result = SchemaValidator.validate_yaml_file(temp_path)
            assert result.is_valid
        finally:
            Path(temp_path).unlink()
    
    def test_json_file_validation(self):
        """Test validation of JSON file."""
        config_data = {
            "metadata": {
                "name": "test-agent",
                "description": "Test agent",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "gpt-4"
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            result = SchemaValidator.validate_json_file(temp_path)
            assert result.is_valid
        finally:
            Path(temp_path).unlink()
    
    def test_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = SchemaValidator.validate_file("nonexistent.yaml")
        assert not result.is_valid
        assert "File not found" in result.errors[0]
    
    def test_get_json_schema(self):
        """Test getting JSON schema."""
        schema = SchemaValidator.get_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "metadata" in schema["properties"]
        assert "model" in schema["properties"]


class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    def test_load_valid_yaml_config(self):
        """Test loading a valid YAML configuration."""
        config_data = ConfigLoader.get_default_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_config(temp_path)
            assert config.metadata.name == "my-react-agent"
            assert config.model.provider.value == "openai"
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_with_env_vars(self):
        """Test loading configuration with environment variable substitution."""
        import os
        
        # Set test environment variable
        os.environ["TEST_AGENT_NAME"] = "env-test-agent"
        os.environ["TEST_MODEL"] = "gpt-3.5-turbo"
        
        config_data = {
            "metadata": {
                "name": "${TEST_AGENT_NAME}",
                "description": "Test agent with env vars",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "${TEST_MODEL}"
            },
            "tools": [],
            "prompt": {
                "system_message": "You are a helpful assistant."
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_config(temp_path)
            assert config.metadata.name == "env-test-agent"
            assert config.model.model_id == "gpt-3.5-turbo"
        finally:
            Path(temp_path).unlink()
            # Clean up environment variables
            del os.environ["TEST_AGENT_NAME"]
            del os.environ["TEST_MODEL"]
    
    def test_load_config_with_defaults(self):
        """Test loading configuration with default values."""
        config_data = {
            "metadata": {
                "name": "test-agent",
                "description": "Test agent",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "model_id": "gpt-4"
            }
        }
        
        defaults = {
            "tools": [],
            "prompt": {
                "system_message": "Default system message"
            },
            "memory": {
                "type": "conversation_buffer",
                "config": {}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_config(temp_path, defaults=defaults)
            assert config.prompt.system_message == "Default system message"
            assert config.memory.type.value == "conversation_buffer"
        finally:
            Path(temp_path).unlink()
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config_data = ConfigLoader.get_default_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            ConfigLoader.save_config(config_data, temp_path, format="yaml")
            
            # Verify file was created and can be loaded
            loaded_config = ConfigLoader.load_config_dict(temp_path)
            assert loaded_config["metadata"]["name"] == config_data["metadata"]["name"]
        finally:
            Path(temp_path).unlink()
    
    def test_create_example_config(self):
        """Test creating example configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            ConfigLoader.create_example_config(temp_path)
            
            # Verify file was created and is valid
            result = SchemaValidator.validate_file(temp_path)
            assert result.is_valid
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__]) 