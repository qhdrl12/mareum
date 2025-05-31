"""
Pydantic-based configuration parser for ReAct Agent configurations.

This module provides a ConfigParser class that loads and validates
YAML configuration files using Pydantic models directly, eliminating
the need for separate JSON schema files.

schema.json이 없어도 되는 이유:
1. Pydantic이 런타임 타입 검증 제공
2. 더 강력한 커스텀 검증 로직
3. 자동 타입 변환 및 기본값 처리
4. 단일 소스 진실 (Single Source of Truth)
5. 더 나은 에러 메시지
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from src.schemas.agent_config import AgentConfig
from .exceptions import ConfigParseError, ConfigValidationError


class ConfigParser:
    """
    YAML configuration parser using Pydantic models.
    
    schema.json 대신 Pydantic 클래스를 직접 사용하는 이점:
    - 런타임 타입 안전성
    - 커스텀 검증 로직 (field_validator, model_validator)
    - 자동 타입 변환 (문자열 -> 정수, 등)
    - 더 명확한 에러 메시지
    - 단일 스키마 정의 (중복 제거)
    """
    
    def __init__(self):
        """Initialize Pydantic-based ConfigParser."""
        pass
    
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
    
    def parse_from_string(self, content: str) -> AgentConfig:
        """
        Parse configuration from YAML string content.
        
        Args:
            content: YAML configuration content as string
            
        Returns:
            Validated AgentConfig instance
            
        Raises:
            ConfigParseError: If parsing fails
            ConfigValidationError: If validation fails
        """
        # Parse the YAML content
        config_data = self._parse_yaml_content(content)
        
        # Validate using Pydantic
        return self.validate_configuration(config_data)
    
    def parse_from_file(self, file_path: Union[str, Path]) -> AgentConfig:
        """
        Parse configuration from YAML file.
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            Validated AgentConfig instance
            
        Raises:
            ConfigParseError: If file reading or parsing fails
            ConfigValidationError: If validation fails
        """
        file_path = Path(file_path)
        
        # Validate file extension first
        if file_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ConfigParseError(f"Only YAML files (.yaml, .yml) are supported. Got: {file_path.suffix}")
        
        if not file_path.exists():
            raise ConfigParseError(f"Configuration file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ConfigParseError(f"Error reading configuration file: {e}")
            
        return self.parse_from_string(content)
    
    def validate_configuration(self, config_data: Dict[str, Any]) -> AgentConfig:
        """
        Validate configuration using Pydantic model.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validated AgentConfig instance
            
        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            # Pydantic이 자동으로 검증, 타입 변환, 기본값 적용을 수행
            return AgentConfig(**config_data)
        except ValidationError as e:
            # Pydantic 에러를 사용자 친화적 메시지로 변환
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
    
    def _format_validation_errors(self, error: ValidationError) -> List[str]:
        """
        Format Pydantic validation errors into user-friendly messages.
        
        Args:
            error: The validation error from Pydantic
            
        Returns:
            List of formatted error messages
        """
        errors = []
        
        for error_detail in error.errors():
            # 경로 구성
            path = " -> ".join(str(p) for p in error_detail['loc']) if error_detail['loc'] else "root"
            
            # 에러 타입별 메시지 개선
            error_type = error_detail['type']
            error_msg = error_detail['msg']
            
            if error_type == 'missing':
                errors.append(f"Required field missing at '{path}': {error_msg}")
            elif error_type == 'value_error':
                errors.append(f"Invalid value at '{path}': {error_msg}")
            elif error_type == 'type_error':
                errors.append(f"Type error at '{path}': {error_msg}")
            else:
                errors.append(f"Error at '{path}': {error_msg} (type: {error_type})")
        
        return errors
    
    def to_dict(self, config: AgentConfig) -> Dict[str, Any]:
        """
        Convert AgentConfig instance to dictionary.
        
        Args:
            config: AgentConfig instance
            
        Returns:
            Configuration as dictionary
        """
        return config.model_dump()
    
    def to_yaml(self, config: AgentConfig, file_path: Optional[Union[str, Path]] = None) -> str:
        """
        Convert AgentConfig instance to YAML string or save to file.
        
        Args:
            config: AgentConfig instance
            file_path: Optional path to save YAML file
            
        Returns:
            YAML string representation
        """
        # mode='json'을 사용하여 Enum을 문자열로 직렬화
        yaml_str = yaml.dump(
            config.model_dump(mode='json'),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_str)
        
        return yaml_str 