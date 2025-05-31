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
            ctx = error_detail.get('ctx', {})
            
            if error_type == 'missing':
                errors.append(f"❌ 필수 필드가 누락되었습니다: '{path}'\n   💡 해결방법: 해당 필드를 추가해주세요.")
            
            elif error_type == 'string_type':
                errors.append(f"❌ 문자열 타입이 필요합니다: '{path}'\n   💡 해결방법: 값을 문따옴표로 감싸주세요. 예: \"your_value\"")
            
            elif error_type == 'dict_type':
                errors.append(f"❌ 딕셔너리 타입이 필요합니다: '{path}'\n   💡 해결방법: 중괄호를 사용하거나 YAML 객체 형태로 작성해주세요. 예: {{}}")
            
            elif error_type == 'list_type':
                errors.append(f"❌ 리스트 타입이 필요합니다: '{path}'\n   💡 해결방법: 대괄호를 사용하거나 YAML 배열 형태로 작성해주세요. 예: []")
            
            elif error_type == 'enum':
                # Enum 값들 추출
                enum_values = []
                if 'expected' in ctx:
                    # Pydantic v2 format: 'expected' contains allowed values
                    expected = ctx['expected']
                    if hasattr(expected, '__iter__') and not isinstance(expected, str):
                        enum_values = list(expected)
                    else:
                        enum_values = [expected]
                else:
                    # Fallback: parse from error message
                    import re
                    match = re.search(r"Input should be (.+)", error_msg)
                    if match:
                        enum_str = match.group(1)
                        # Extract quoted values, removing extra quotes
                        raw_values = re.findall(r"'([^']*)'", enum_str)
                        enum_values = [v.strip("'\"") for v in raw_values]
                
                if enum_values:
                    values_str = ", ".join(f"'{v}'" for v in enum_values)
                    errors.append(f"❌ 잘못된 값입니다: '{path}'\n   💡 허용된 값: {values_str}")
                else:
                    errors.append(f"❌ 잘못된 값입니다: '{path}'\n   💡 해결방법: {error_msg}")
            
            elif error_type == 'model_type':
                # Nested model validation error
                if 'prompt' in path.lower():
                    errors.append(f"❌ Prompt 설정이 잘못되었습니다: '{path}'\n   💡 해결방법: 'system_prompt' 필드가 포함된 객체를 제공해주세요.")
                elif 'tool' in path.lower():
                    errors.append(f"❌ Tool 설정이 잘못되었습니다: '{path}'\n   💡 해결방법: 'name', 'description', 'type' 필드가 포함된 객체를 제공해주세요.")
                else:
                    errors.append(f"❌ 객체 구조가 잘못되었습니다: '{path}'\n   💡 해결방법: 올바른 구조의 객체를 제공해주세요.")
            
            elif error_type == 'value_error':
                # Custom validator errors
                if 'url' in error_msg.lower() or 'endpoint' in path.lower():
                    errors.append(f"❌ 잘못된 URL 형식입니다: '{path}'\n   💡 해결방법: 'http://' 또는 'https://'로 시작하는 유효한 URL을 입력해주세요.")
                elif 'api_key' in path.lower():
                    errors.append(f"❌ API 키 형식이 잘못되었습니다: '{path}'\n   💡 해결방법: 유효한 API 키를 입력하거나 환경변수명을 사용해주세요.")
                else:
                    errors.append(f"❌ 값 검증 오류: '{path}'\n   💡 상세정보: {error_msg}")
            
            elif error_type == 'type_error':
                errors.append(f"❌ 타입 오류: '{path}'\n   💡 해결방법: {error_msg}")
            
            elif error_type == 'extra_forbidden':
                errors.append(f"❌ 허용되지 않는 필드입니다: '{path}'\n   💡 해결방법: 해당 필드를 제거하거나 올바른 필드명으로 변경해주세요.")
            
            else:
                # 기타 에러들에 대한 fallback
                errors.append(f"❌ 오류 ({error_type}): '{path}'\n   💡 상세정보: {error_msg}")
        
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