"""
Configuration file loader with environment variable substitution and validation.
"""

import os
import re
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..core.config_parser import ConfigParser


class ConfigLoader:
    """Loader for ReAct agent configuration files with advanced features."""
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    @staticmethod
    def load_config(
        file_path: Union[str, Path],
        validate: bool = True,
        substitute_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load and parse configuration file.
        
        Args:
            file_path: Path to configuration file
            validate: Whether to validate the configuration
            substitute_env_vars: Whether to substitute environment variables
            defaults: Default values to merge with loaded config
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Load raw data
        raw_data = ConfigLoader._load_raw_data(file_path)
        
        # Substitute environment variables
        if substitute_env_vars:
            raw_data = ConfigLoader._substitute_env_vars(raw_data)
        
        # Apply defaults
        if defaults:
            raw_data = ConfigLoader._merge_defaults(raw_data, defaults)
        
        # Validate if requested using ConfigParser
        if validate:
            try:
                # Use ConfigParser for validation with schema.json
                parser = ConfigParser(schema_path="schema.json")
                parser.validate_configuration(raw_data)
            except Exception as e:
                raise ValueError(f"Configuration validation failed: {e}")
        
        return raw_data
    
    @staticmethod
    def load_config_dict(
        file_path: Union[str, Path],
        validate: bool = True,
        substitute_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load configuration as dictionary without creating AgentConfig instance.
        
        This method is now identical to load_config for simplicity.
        
        Args:
            file_path: Path to configuration file
            validate: Whether to validate the configuration
            substitute_env_vars: Whether to substitute environment variables
            defaults: Default values to merge with loaded config
            
        Returns:
            Configuration dictionary
        """
        return ConfigLoader.load_config(
            file_path=file_path,
            validate=validate,
            substitute_env_vars=substitute_env_vars,
            defaults=defaults
        )
    
    @staticmethod
    def _load_raw_data(file_path: Path) -> Dict[str, Any]:
        """Load raw data from YAML file."""
        if file_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ValueError(f"Only YAML files are supported. Got: {file_path.suffix}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def _substitute_env_vars(data: Any) -> Any:
        """
        Recursively substitute environment variables in configuration data.
        
        Supports syntax: ${VAR_NAME} or ${VAR_NAME:default_value}
        """
        if isinstance(data, dict):
            return {key: ConfigLoader._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [ConfigLoader._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            return ConfigLoader._substitute_string_env_vars(data)
        else:
            return data
    
    @staticmethod
    def _substitute_string_env_vars(text: str) -> str:
        """Substitute environment variables in a string."""
        def replace_var(match):
            var_expr = match.group(1)
            
            # Check if default value is provided
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    raise ValueError(f"Environment variable '{var_name}' not found and no default provided")
                return value
        
        return ConfigLoader.ENV_VAR_PATTERN.sub(replace_var, text)
    
    @staticmethod
    def _merge_defaults(config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge default values with configuration.
        
        Config values take precedence over defaults.
        """
        result = defaults.copy()
        
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = ConfigLoader._merge_defaults(value, result[key])
            else:
                # Override with config value
                result[key] = value
        
        return result
    
    @staticmethod
    def save_config(
        config: Dict[str, Any],
        file_path: Union[str, Path],
        format: str = "yaml"
    ) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration dictionary to save
            file_path: Output file path
            format: Output format (only 'yaml' supported)
        """
        if format != "yaml":
            raise ValueError("Only YAML format is supported")
        
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as YAML
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        Get default configuration structure.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "metadata": {
                "name": "default_agent",
                "description": "A basic ReAct agent configuration",
                "version": "1.0.0"
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4",
                "credentials_key": "OPENAI_API_KEY",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            },
            "prompt": {
                "system_prompt": "You are a helpful AI assistant. Use the available tools to help answer questions and complete tasks."
            },
            "memory": {
                "type": "conversation_buffer_window",
                "config": {
                    "k": 10
                }
            },
            "tools": []
        }
    
    @staticmethod
    def create_example_config(file_path: Union[str, Path]) -> None:
        """
        Create an example configuration file.
        
        Args:
            file_path: Path where to save the example config
        """
        config = ConfigLoader.get_default_config()
        ConfigLoader.save_config(config, file_path) 