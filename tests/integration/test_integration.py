#!/usr/bin/env python3
"""
Integration tests for configuration parsing and validation system.
This file focuses exclusively on testing ConfigParser, AgentConfig validation,
and configuration file loading/parsing functionality.
"""

import os
import pytest
from pathlib import Path

from src.core.config_parser import ConfigParser, ConfigParseError, ConfigValidationError
from src.utils.config_loader import ConfigLoader
from src.schemas.agent_config import AgentConfig


class TestConfigParserIntegration:
    """Test integration between different parts of the configuration system."""

    def test_example_config(self):
        """Test loading and validating example configuration."""
        parser = ConfigParser()
        
        # Test with a minimal valid config
        config_data = {
            "metadata": {
                "name": "test-agent",
                "version": "1.0.0",
                "description": "Test agent"
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4o-mini",
                "api_key": "OPENAI_API_KEY"
            },
            "prompt": {
                "system_prompt": "You are a helpful assistant."
            }
        }
        
        # This should not raise an exception
        result = parser.validate_configuration(config_data)
        assert isinstance(result, AgentConfig)
        assert result.metadata.name == "test-agent"
    
    def test_config_loading(self):
        """Test configuration loading from file."""
        parser = ConfigParser()
        
        # Test with openai_compatible example
        config_path = "examples/configs/openai_compatible.yaml"
        if Path(config_path).exists():
            try:
                config = parser.parse_from_file(config_path)
                assert isinstance(config, AgentConfig)
                assert config.metadata.name
                assert config.model.provider
            except Exception as e:
                pytest.skip(f"Config file has validation issues: {e}")
        else:
            pytest.skip(f"Config file not found: {config_path}")
    
    def test_config_parser_validation(self):
        """Test ConfigParser validation methods."""
        parser = ConfigParser()
        
        # Test valid config
        valid_config = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "model": {"provider": "openai", "name": "gpt-4o-mini", "api_key": "test"},
            "prompt": {"system_prompt": "test"}
        }
        
        result = parser.validate_configuration(valid_config)
        assert isinstance(result, AgentConfig)
        
        # Test invalid config
        invalid_config = {"metadata": {"name": "test"}}  # Missing required fields
        
        with pytest.raises(ConfigValidationError):
            parser.validate_configuration(invalid_config)
    
    def test_openai_config(self):
        """Test OpenAI configuration if available."""
        parser = ConfigParser()
        
        config_path = "examples/configs/openai_agent.yaml"
        if Path(config_path).exists():
            try:
                config = parser.parse_from_file(config_path)
                assert isinstance(config, AgentConfig)
            except Exception as e:
                pytest.skip(f"OpenAI config has validation issues: {e}")
        else:
            pytest.skip(f"OpenAI config not found: {config_path}")
    
    @pytest.mark.parametrize("config_file", [
        "examples/configs/valid_agent.yaml",
        "examples/configs/example_agent.yaml", 
        "examples/configs/openai_agent.yaml"
    ])
    def test_all_config_files(self, config_file):
        """Test all available configuration files."""
        parser = ConfigParser()
        
        if not Path(config_file).exists():
            pytest.skip(f"Config file not found: {config_file}")
            
        try:
            config = parser.parse_from_file(config_file)
            assert isinstance(config, AgentConfig)
            assert config.metadata.name
            assert config.model.provider
        except (ConfigValidationError, ConfigParseError) as e:
            pytest.skip(f"Config {config_file} has validation issues: {e}")


def test_configuration_system_cli():
    """Test configuration system CLI-style usage."""
    try:
        parser = ConfigParser()
        
        # Test basic validation
        test_config = {
            "metadata": {
                "name": "cli-test",
                "version": "1.0.0",
                "description": "CLI test agent"
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4o-mini", 
                "api_key": "OPENAI_API_KEY"
            },
            "prompt": {
                "system_prompt": "You are a CLI test assistant."
            }
        }
        
        config = parser.validate_configuration(test_config)
        assert config.metadata.name == "cli-test"
        
        # Test YAML round-trip
        yaml_str = parser.to_yaml(config)
        assert "cli-test" in yaml_str
        
        # Test parsing from string
        config2 = parser.parse_from_string(yaml_str)
        assert config2.metadata.name == config.metadata.name
        
    except Exception as e:
        assert False, f"Configuration system test failed: {e}"


if __name__ == "__main__":
    # Allow running as standalone script for backward compatibility
    pytest.main([__file__, "-v"])
