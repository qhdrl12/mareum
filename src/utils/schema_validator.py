"""
Schema validation utilities for ReAct agent configurations.
"""

import json
import yaml
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from pydantic import ValidationError

from ..schemas.agent_config import AgentConfig


class ValidationResult:
    """Result of schema validation."""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid
    
    def __str__(self) -> str:
        """String representation of validation result."""
        if self.is_valid:
            result = "✅ Validation passed"
            if self.warnings:
                result += f" with {len(self.warnings)} warning(s)"
        else:
            result = f"❌ Validation failed with {len(self.errors)} error(s)"
        
        return result
    
    def get_detailed_report(self) -> str:
        """Get detailed validation report."""
        lines = [str(self)]
        
        if self.errors:
            lines.append("\n🔴 Errors:")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"  {i}. {error}")
        
        if self.warnings:
            lines.append("\n🟡 Warnings:")
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {warning}")
        
        return "\n".join(lines)


class SchemaValidator:
    """Validator for ReAct agent configuration schemas."""
    
    @staticmethod
    def validate_dict(config_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration data from a dictionary.
        
        Args:
            config_data: Configuration data as dictionary
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        try:
            # Attempt to create AgentConfig instance
            agent_config = AgentConfig(**config_data)
            
            # Additional custom validations
            warnings = []
            
            # Check for common issues
            warnings.extend(SchemaValidator._check_common_issues(agent_config))
            
            return ValidationResult(is_valid=True, warnings=warnings)
            
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                error_msg = f"{field_path}: {error['msg']}"
                if error.get('input') is not None:
                    error_msg += f" (got: {error['input']})"
                errors.append(error_msg)
            
            return ValidationResult(is_valid=False, errors=errors)
        
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Unexpected error: {str(e)}"])
    
    @staticmethod
    def validate_yaml_file(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate YAML configuration file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ValidationResult(is_valid=False, errors=[f"File not found: {file_path}"])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                return ValidationResult(is_valid=False, errors=["Empty or invalid YAML file"])
            
            return SchemaValidator.validate_dict(data)
            
        except yaml.YAMLError as e:
            return ValidationResult(is_valid=False, errors=[f"YAML parsing error: {str(e)}"])
        
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Error reading file: {str(e)}"])
    
    @staticmethod
    def validate_json_file(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate JSON configuration file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ValidationResult(is_valid=False, errors=[f"File not found: {file_path}"])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return SchemaValidator.validate_dict(data)
            
        except json.JSONDecodeError as e:
            return ValidationResult(is_valid=False, errors=[f"JSON parsing error: {str(e)}"])
        
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Error reading file: {str(e)}"])
    
    @staticmethod
    def validate_file(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate configuration file (auto-detect format).
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            return SchemaValidator.validate_yaml_file(file_path)
        elif file_path.suffix.lower() == '.json':
            return SchemaValidator.validate_json_file(file_path)
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported file format: {file_path.suffix}. Use .yaml, .yml, or .json"]
            )
    
    @staticmethod
    def _check_common_issues(config: AgentConfig) -> List[str]:
        """
        Check for common configuration issues that might cause problems.
        
        Args:
            config: Validated AgentConfig instance
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check model parameters
        if config.model.parameters:
            params = config.model.parameters
            
            # Temperature warnings
            if 'temperature' in params:
                temp = params['temperature']
                if temp == 0:
                    warnings.append("Temperature is set to 0 - responses will be deterministic")
                elif temp > 1.5:
                    warnings.append("Temperature is very high (>1.5) - responses may be incoherent")
            
            # Max tokens warnings
            if 'max_tokens' in params:
                max_tokens = params['max_tokens']
                if max_tokens < 100:
                    warnings.append("max_tokens is very low (<100) - responses may be truncated")
                elif max_tokens > 4000:
                    warnings.append("max_tokens is very high (>4000) - may increase costs significantly")
        
        # Check tools
        if len(config.tools) > 10:
            warnings.append(f"Large number of tools ({len(config.tools)}) may impact performance")
        
        # Check memory configuration
        if config.memory and config.memory.type.value == "conversation_buffer":
            warnings.append("Using conversation_buffer memory without limit may cause context overflow")
        
        # Check knowledge configuration
        if config.knowledge:
            search_config = config.knowledge.search_config
            if search_config.get('top_k', 5) > 20:
                warnings.append("High top_k value in knowledge search may impact performance")
        
        return warnings
    
    @staticmethod
    def get_json_schema() -> Dict[str, Any]:
        """
        Get the JSON schema for agent configuration.
        
        Returns:
            JSON schema dictionary
        """
        return AgentConfig.schema()
    
    @staticmethod
    def save_json_schema(file_path: Union[str, Path]) -> None:
        """
        Save the JSON schema to a file.
        
        Args:
            file_path: Path where to save the schema
        """
        schema = SchemaValidator.get_json_schema()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False) 