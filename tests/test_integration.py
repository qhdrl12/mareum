#!/usr/bin/env python3
"""
Integration tests for configuration parsing and validation system.
"""

import os
import pytest
from pathlib import Path

from src.core.config_parser import ConfigParser
from src.utils.config_loader import ConfigLoader


class TestConfigurationIntegration:
    """Integration tests for the configuration system."""
    
    def test_example_config(self):
        """Test the example configuration file."""
        parser = ConfigParser(schema_path="schema.json")
        config_data = parser.parse_from_file("examples/configs/example_agent.yaml")
        
        assert config_data is not None
        assert config_data.get('metadata', {}).get('name') == 'customer-support-agent'
        assert config_data.get('model', {}).get('provider') == 'openai'
        assert config_data.get('model', {}).get('name') == 'gpt-4'

    def test_config_loading(self):
        """Test configuration loading with environment variables."""
        # Set test environment variables
        os.environ['KB_API_TOKEN'] = 'test_kb_token'
        os.environ['TICKET_API_TOKEN'] = 'test_ticket_token'
        os.environ['OPENAI_API_KEY'] = 'test_openai_key'
        
        try:
            config = ConfigLoader.load_config("examples/configs/example_agent.yaml")
            
            assert config['metadata']['name'] == 'customer-support-agent'
            assert config['model']['provider'] == 'openai'
            assert config['model']['name'] == 'gpt-4'
            assert len(config['tools']) == 3
        finally:
            # Clean up test environment variables
            for key in ['KB_API_TOKEN', 'TICKET_API_TOKEN', 'OPENAI_API_KEY']:
                if key in os.environ:
                    del os.environ[key]

    def test_config_parser_validation(self):
        """Test ConfigParser validation functionality."""
        parser = ConfigParser(schema_path="schema.json")
        
        # Test valid configuration
        config_data = parser.parse_from_file("examples/configs/valid_agent.yaml")
        assert config_data is not None
        
        # Test schema validation
        parser.validate_configuration(config_data)  # Should not raise

    def test_default_config(self):
        """Test default configuration creation."""
        test_file = "test_default_agent.yaml"
        
        try:
            ConfigLoader.create_example_config(test_file)
            assert Path(test_file).exists()
            
            # Validate the created config
            parser = ConfigParser(schema_path="schema.json")
            config_data = parser.parse_from_file(test_file)
            parser.validate_configuration(config_data)
        finally:
            # Clean up test file
            if Path(test_file).exists():
                Path(test_file).unlink()

    def test_vllm_config(self):
        """Test vLLM configuration file."""
        # Set test environment variables for vLLM
        os.environ['VLLM_API_KEY'] = 'test_vllm_key'
        
        try:
            parser = ConfigParser(schema_path="schema.json")
            config_data = parser.parse_from_file("examples/configs/vllm_agent.yaml")
            parser.validate_configuration(config_data)
            
            config = ConfigLoader.load_config("examples/configs/vllm_agent.yaml")
            assert config['model']['provider'] == 'openai_compatible'
            assert 'base_url' in config['model']['parameters']
        finally:
            # Clean up
            if 'VLLM_API_KEY' in os.environ:
                del os.environ['VLLM_API_KEY']

    def test_bedrock_config(self):
        """Test AWS Bedrock configuration file."""
        # Set test environment variables for Bedrock
        env_vars = {
            'AWS_ACCESS_KEY_ID': 'test_aws_key',
            'AWS_SECRET_ACCESS_KEY': 'test_aws_secret',
            'LAMBDA_FUNCTION_NAME': 'test_function',
            'AWS_SIGNATURE': 'test_signature',
            'MILVUS_TOKEN': 'test_milvus_token'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            parser = ConfigParser(schema_path="schema.json")
            config_data = parser.parse_from_file("examples/configs/bedrock_agent.yaml")
            parser.validate_configuration(config_data)
            
            config = ConfigLoader.load_config("examples/configs/bedrock_agent.yaml")
            assert config['model']['provider'] == 'aws_bedrock'
            assert config['model']['parameters'].get('region') == 'us-east-1'
            assert config['model']['name'] == 'claude-3-5-sonnet-20241022'
        finally:
            # Clean up
            for key in env_vars:
                if key in os.environ:
                    del os.environ[key]

    @pytest.mark.parametrize("config_file", [
        "examples/configs/valid_agent.yaml",
        "examples/configs/default_agent.yaml",
        "examples/configs/example_agent.yaml",
        "examples/configs/bedrock_agent.yaml",
        "examples/configs/vllm_agent.yaml"
    ])
    def test_all_config_files(self, config_file):
        """Test all configuration files in examples/configs."""
        if not Path(config_file).exists():
            pytest.skip(f"Configuration file {config_file} not found")
        
        parser = ConfigParser(schema_path="schema.json")
        config_data = parser.parse_from_file(config_file)
        parser.validate_configuration(config_data)  # Should not raise


def test_configuration_system_cli():
    """Test the configuration system via CLI-style execution."""
    import subprocess
    import sys
    
    # Create a simple test script
    test_script = """
from src.core.config_parser import ConfigParser
from src.utils.config_loader import ConfigLoader

# Test basic functionality
parser = ConfigParser(schema_path="schema.json")
config_data = parser.parse_from_file("examples/configs/valid_agent.yaml")
parser.validate_configuration(config_data)

config = ConfigLoader.load_config("examples/configs/valid_agent.yaml")
print(f"✅ Configuration system working: {config['metadata']['name']}")
"""
    
    # Write and execute test script
    with open("temp_test.py", "w") as f:
        f.write(test_script)
    
    try:
        result = subprocess.run([sys.executable, "temp_test.py"], 
                              capture_output=True, text=True, cwd=".")
        assert result.returncode == 0
        assert "✅ Configuration system working" in result.stdout
    finally:
        if Path("temp_test.py").exists():
            Path("temp_test.py").unlink()


if __name__ == "__main__":
    # Allow running as standalone script for backward compatibility
    pytest.main([__file__, "-v"]) 