"""
Configuration file loader with environment variable substitution and validation.
"""

import os
import re
import yaml
import json
from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..schemas.agent_config import AgentConfig
from .schema_validator import SchemaValidator, ValidationResult


class ConfigLoader:
    """Loader for ReAct agent configuration files with advanced features."""
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    @staticmethod
    def load_config(
        file_path: Union[str, Path],
        validate: bool = True,
        substitute_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ) -> AgentConfig:
        """
        Load and parse configuration file.
        
        Args:
            file_path: Path to configuration file
            validate: Whether to validate the configuration
            substitute_env_vars: Whether to substitute environment variables
            defaults: Default values to merge with loaded config
            
        Returns:
            AgentConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
            yaml.YAMLError: If YAML parsing fails
            json.JSONDecodeError: If JSON parsing fails
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
        
        # Validate if requested
        if validate:
            result = SchemaValidator.validate_dict(raw_data)
            if not result.is_valid:
                error_msg = f"Configuration validation failed:\n{result.get_detailed_report()}"
                raise ValueError(error_msg)
        
        # Create AgentConfig instance
        return AgentConfig(**raw_data)
    
    @staticmethod
    def load_config_dict(
        file_path: Union[str, Path],
        validate: bool = True,
        substitute_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load configuration as dictionary without creating AgentConfig instance.
        
        Args:
            file_path: Path to configuration file
            validate: Whether to validate the configuration
            substitute_env_vars: Whether to substitute environment variables
            defaults: Default values to merge with loaded config
            
        Returns:
            Configuration dictionary
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
        
        # Validate if requested
        if validate:
            result = SchemaValidator.validate_dict(raw_data)
            if not result.is_valid:
                error_msg = f"Configuration validation failed:\n{result.get_detailed_report()}"
                raise ValueError(error_msg)
        
        return raw_data
    
    @staticmethod
    def _load_raw_data(file_path: Path) -> Dict[str, Any]:
        """Load raw data from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif file_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
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
        config: Union[AgentConfig, Dict[str, Any]],
        file_path: Union[str, Path],
        format: str = "yaml"
    ) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            file_path: Output file path
            format: Output format ('yaml' or 'json')
        """
        file_path = Path(file_path)
        
        # Convert to dict if AgentConfig
        if isinstance(config, AgentConfig):
            data = config.model_dump()
        else:
            data = config
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            elif format.lower() == 'json':
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'")
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        Get a default configuration template.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "metadata": {
                "name": "my-react-agent",
                "description": "A ReAct agent for task automation",
                "version": "1.0.0",
                "owner": "Your Name",
                "tags": ["react", "automation"]
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4",
                "credentials_key": "OPENAI_API_KEY",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 1.0
                }
            },
            "tools": [
                {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "type": "builtin",
                    "parameters": [
                        {
                            "name": "query",
                            "type": "string",
                            "description": "Search query",
                            "required": True
                        }
                    ]
                }
            ],
            "memory": {
                "type": "conversation_buffer_window",
                "config": {
                    "k": 10
                }
            },
            "prompt": {
                "system_prompt": "You are a helpful AI assistant that uses tools to solve problems step by step."
            }
        }
    
    @staticmethod
    def create_example_config(file_path: Union[str, Path]) -> None:
        """
        Create an example configuration file.
        
        Args:
            file_path: Path where to save the example config
        """
        config = ConfigLoader.get_default_config()
        ConfigLoader.save_config(config, file_path, format="yaml") 