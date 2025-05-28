"""
Configuration parser and validator for ReAct Agent configurations.

This module provides a ConfigParser class that loads and validates
YAML configuration files against a JSON schema, with automatic
application of default values.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


class ConfigParseError(Exception):
    """Exception raised when configuration parsing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors


class ConfigParser:
    """YAML configuration parser with schema validation and default value application."""
    
    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        """
        Initialize ConfigParser with optional schema file.
        
        Args:
            schema_path: Path to JSON schema file for validation
        """
        self.schema_path = schema_path
        self._schema = None
    
    def _load_schema(self) -> Dict[str, Any]:
        """
        Load and cache the JSON schema for validation.
        
        Returns:
            The loaded schema as a dictionary
            
        Raises:
            ConfigParseError: If schema file cannot be loaded
        """
        if self._schema is not None:
            return self._schema
            
        if self.schema_path is None:
            # Default to schema.json in project root
            schema_path = Path(__file__).parent.parent.parent / "schema.json"
        else:
            schema_path = Path(self.schema_path)
            
        if not schema_path.exists():
            raise ConfigParseError(f"Schema file not found: {schema_path}")
            
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigParseError(f"Invalid JSON in schema file: {e}")
        except Exception as e:
            raise ConfigParseError(f"Error loading schema file: {e}")
            
        return self._schema
    
    def _parse_yaml_content(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML configuration content from string.
        
        Args:
            content: YAML configuration content as string
            
        Returns:
            Parsed configuration as dictionary
            
        Raises:
            ConfigParseError: If YAML parsing fails
        """
        content = content.strip()
        if not content:
            raise ConfigParseError("Configuration content is empty")
            
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ConfigParseError(f"Unexpected error parsing YAML configuration: {e}")
    
    def parse_from_string(self, content: str) -> Dict[str, Any]:
        """
        Parse configuration from YAML string content.
        
        Args:
            content: YAML configuration content as string
            
        Returns:
            Parsed and validated configuration
            
        Raises:
            ConfigParseError: If parsing fails
            ConfigValidationError: If validation fails
        """
        # Parse the YAML content
        config_data = self._parse_yaml_content(content)
        
        # Validate against schema
        validated_config = self.validate_configuration(config_data)
        
        # Normalize the configuration
        normalized_config = self.normalize_configuration(validated_config)
        
        return normalized_config
    
    def parse_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse configuration from YAML file.
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            Parsed and validated configuration
            
        Raises:
            ConfigParseError: If file reading or parsing fails
            ConfigValidationError: If validation fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigParseError(f"Configuration file not found: {file_path}")
            
        # Validate file extension
        if file_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ConfigParseError(f"Only YAML files (.yaml, .yml) are supported. Got: {file_path.suffix}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ConfigParseError(f"Error reading configuration file: {e}")
            
        return self.parse_from_string(content)
    
    def validate_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration against the JSON schema.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validated configuration data
            
        Raises:
            ConfigValidationError: If validation fails
        """
        schema = self._load_schema()
        
        try:
            validate(instance=config_data, schema=schema)
            return config_data
        except JsonSchemaValidationError as e:
            # Format validation errors into user-friendly messages
            errors = self._format_validation_errors(e)
            raise ConfigValidationError(
                "Configuration validation failed",
                errors
            )
        except Exception as e:
            raise ConfigValidationError(
                f"Unexpected validation error: {e}",
                [str(e)]
            )
    
    def _format_validation_errors(self, error: JsonSchemaValidationError) -> List[str]:
        """
        Format JSON schema validation errors into user-friendly messages.
        
        Args:
            error: The validation error from jsonschema
            
        Returns:
            List of formatted error messages
        """
        errors = []
        
        # Primary error
        if error.absolute_path:
            path = " -> ".join(str(p) for p in error.absolute_path)
            errors.append(f"At '{path}': {error.message}")
        else:
            errors.append(f"At root: {error.message}")
        
        # Add context from the validator if available
        if hasattr(error, 'context') and error.context:
            for context_error in error.context:
                if context_error.absolute_path:
                    path = " -> ".join(str(p) for p in context_error.absolute_path)
                    errors.append(f"  At '{path}': {context_error.message}")
                else:
                    errors.append(f"  {context_error.message}")
        
        return errors
    
    def normalize_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize configuration data by applying default values and ensuring
        all required fields are properly formatted.
        
        Args:
            config_data: The validated configuration data
            
        Returns:
            Normalized configuration data
        """
        schema = self._load_schema()
        
        # Apply default values recursively
        normalized_data = self._apply_defaults(config_data.copy(), schema)
        
        return normalized_data
    
    def _apply_defaults(self, data: Dict[str, Any], schema: Dict[str, Any], path: str = ""):
        """
        Recursively apply default values from schema to configuration data.
        
        Args:
            data: Configuration data to apply defaults to
            schema: JSON schema with default values
            path: Current path in the configuration (for debugging)
            
        Returns:
            Configuration data with defaults applied
        """
        if schema.get("type") == "object" and "properties" in schema:
            # Handle object properties
            for prop_name, prop_schema in schema["properties"].items():
                if "default" in prop_schema and prop_name not in data:
                    data[prop_name] = prop_schema["default"]
                elif prop_name in data and prop_schema.get("type") == "object":
                    # Recursively apply defaults for nested objects
                    data[prop_name] = self._apply_defaults(
                        data[prop_name], 
                        prop_schema, 
                        f"{path}.{prop_name}" if path else prop_name
                    )
        
        return data


# Convenience function for easy usage
def load_config(config_path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load and parse a configuration file.
    
    Args:
        config_path: Path to the YAML configuration file
        schema_path: Optional path to JSON schema file for validation
        
    Returns:
        Parsed and validated configuration
        
    Raises:
        ConfigParseError: If file reading or parsing fails
        ConfigValidationError: If validation fails
    """
    parser = ConfigParser(schema_path=schema_path)
    return parser.parse_from_file(config_path) 