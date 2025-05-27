"""
Configuration file loader with environment variable substitution and validation.

ReAct 에이전트 설정 파일을 로드하고 환경 변수 치환 및 검증을 수행하는 모듈입니다.
YAML 형식의 설정 파일을 읽어 파이썬 딕셔너리로 변환하며, 환경 변수 치환과 스키마 검증을 지원합니다.
"""

import os
import re
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..core.config_parser import ConfigParser


class ConfigLoader:
    """
    Loader for ReAct agent configuration files with advanced features.
    
    ReAct 에이전트 설정 파일을 로드하는 고급 기능을 제공하는 클래스입니다.
    
    주요 기능:
    - YAML 설정 파일 로드 및 파싱
    - 환경 변수 자동 치환 (${VAR_NAME} 또는 ${VAR_NAME:default} 형식)
    - ConfigParser를 통한 스키마 검증
    - 기본값 병합 및 설정 저장
    - 예제 설정 파일 생성
    
    사용 예시:
        # 기본 로드
        config = ConfigLoader.load_config("config.yaml")
        
        # 환경 변수 치환 없이 로드
        config = ConfigLoader.load_config("config.yaml", substitute_env_vars=False)
        
        # 검증 없이 로드
        config = ConfigLoader.load_config("config.yaml", validate=False)
    """
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    """환경 변수 패턴을 매칭하는 정규표현식. ${VAR_NAME} 또는 ${VAR_NAME:default} 형식을 지원합니다."""
    
    @staticmethod
    def load_config(
        file_path: Union[str, Path],
        validate: bool = True,
        substitute_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load and parse configuration file.
        
        설정 파일을 로드하고 파싱하는 메인 메서드입니다.
        YAML 파일을 읽어 파이썬 딕셔너리로 변환하며, 선택적으로 환경 변수 치환,
        기본값 병합, 스키마 검증을 수행합니다.
        
        처리 순서:
        1. 파일 존재 여부 확인
        2. YAML 파일 로드
        3. 환경 변수 치환 (선택적)
        4. 기본값 병합 (선택적)
        5. 스키마 검증 (선택적)
        
        Args:
            file_path (Union[str, Path]): 로드할 설정 파일의 경로
            validate (bool): 스키마 검증 수행 여부. 기본값은 True
            substitute_env_vars (bool): 환경 변수 치환 수행 여부. 기본값은 True
            defaults (Optional[Dict[str, Any]]): 병합할 기본값 딕셔너리. None이면 병합하지 않음
            
        Returns:
            Dict[str, Any]: 로드되고 처리된 설정 딕셔너리
            
        Raises:
            FileNotFoundError: 설정 파일이 존재하지 않는 경우
            ValueError: 스키마 검증에 실패한 경우
            yaml.YAMLError: YAML 파싱에 실패한 경우
            
        Example:
            >>> config = ConfigLoader.load_config("agent.yaml")
            >>> print(config['metadata']['name'])
            'my_agent'
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
        
        AgentConfig 인스턴스를 생성하지 않고 딕셔너리로만 설정을 로드합니다.
        현재는 load_config 메서드와 동일한 기능을 제공하며, 하위 호환성을 위해 유지됩니다.
        
        이 메서드는 이전 버전과의 호환성을 위해 제공되며, 내부적으로는 load_config를 호출합니다.
        새로운 코드에서는 load_config를 직접 사용하는 것을 권장합니다.
        
        Args:
            file_path (Union[str, Path]): 로드할 설정 파일의 경로
            validate (bool): 스키마 검증 수행 여부. 기본값은 True
            substitute_env_vars (bool): 환경 변수 치환 수행 여부. 기본값은 True
            defaults (Optional[Dict[str, Any]]): 병합할 기본값 딕셔너리
            
        Returns:
            Dict[str, Any]: 로드된 설정 딕셔너리
            
        Note:
            이 메서드는 향후 버전에서 제거될 수 있습니다. load_config 사용을 권장합니다.
        """
        return ConfigLoader.load_config(
            file_path=file_path,
            validate=validate,
            substitute_env_vars=substitute_env_vars,
            defaults=defaults
        )
    
    @staticmethod
    def _load_raw_data(file_path: Path) -> Dict[str, Any]:
        """
        Load raw data from YAML file.
        
        YAML 파일에서 원시 데이터를 로드하는 내부 메서드입니다.
        파일 확장자를 검증하고 YAML 파서를 사용하여 데이터를 로드합니다.
        
        지원되는 확장자:
        - .yaml
        - .yml
        
        Args:
            file_path (Path): 로드할 YAML 파일의 경로
            
        Returns:
            Dict[str, Any]: 파싱된 YAML 데이터. 빈 파일인 경우 빈 딕셔너리 반환
            
        Raises:
            ValueError: 지원되지 않는 파일 확장자인 경우
            yaml.YAMLError: YAML 파싱 오류가 발생한 경우
            IOError: 파일 읽기 오류가 발생한 경우
            
        Note:
            이 메서드는 YAML 전용으로 설계되었으며, JSON 지원은 제거되었습니다.
        """
        if file_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ValueError(f"Only YAML files are supported. Got: {file_path.suffix}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def _substitute_env_vars(data: Any) -> Any:
        """
        Recursively substitute environment variables in configuration data.
        
        설정 데이터에서 환경 변수를 재귀적으로 치환하는 내부 메서드입니다.
        딕셔너리, 리스트, 문자열을 재귀적으로 순회하며 환경 변수 패턴을 찾아 치환합니다.
        
        지원되는 환경 변수 형식:
        - ${VAR_NAME}: 환경 변수 값으로 치환. 변수가 없으면 오류 발생
        - ${VAR_NAME:default_value}: 환경 변수 값으로 치환. 변수가 없으면 기본값 사용
        
        Args:
            data (Any): 환경 변수 치환을 수행할 데이터 (딕셔너리, 리스트, 문자열 등)
            
        Returns:
            Any: 환경 변수가 치환된 데이터. 원본과 동일한 타입 유지
            
        Raises:
            ValueError: 필수 환경 변수가 설정되지 않았고 기본값도 없는 경우
            
        Example:
            >>> data = {"api_key": "${API_KEY}", "url": "${BASE_URL:http://localhost}"}
            >>> # API_KEY=secret123 환경 변수가 설정된 경우
            >>> result = ConfigLoader._substitute_env_vars(data)
            >>> print(result)
            {'api_key': 'secret123', 'url': 'http://localhost'}
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
        """
        Substitute environment variables in a string.
        
        문자열에서 환경 변수 패턴을 찾아 실제 환경 변수 값으로 치환하는 내부 메서드입니다.
        정규표현식을 사용하여 ${VAR_NAME} 또는 ${VAR_NAME:default} 패턴을 찾고 치환합니다.
        
        치환 규칙:
        1. ${VAR_NAME} 형식: os.getenv(VAR_NAME)로 치환. 없으면 ValueError 발생
        2. ${VAR_NAME:default} 형식: os.getenv(VAR_NAME, default)로 치환
        3. 콜론(:) 뒤의 모든 텍스트는 기본값으로 처리
        4. 변수명과 기본값의 앞뒤 공백은 자동으로 제거
        
        Args:
            text (str): 환경 변수 치환을 수행할 문자열
            
        Returns:
            str: 환경 변수가 치환된 문자열
            
        Raises:
            ValueError: 필수 환경 변수가 설정되지 않았고 기본값도 없는 경우
            
        Example:
            >>> # API_KEY=secret123, BASE_URL 미설정
            >>> text = "Key: ${API_KEY}, URL: ${BASE_URL:http://localhost:8080}"
            >>> result = ConfigLoader._substitute_string_env_vars(text)
            >>> print(result)
            'Key: secret123, URL: http://localhost:8080'
        """
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
        
        기본값 딕셔너리와 설정 딕셔너리를 병합하는 내부 메서드입니다.
        설정 값이 기본값보다 우선순위를 가지며, 중첩된 딕셔너리는 재귀적으로 병합됩니다.
        
        병합 규칙:
        1. 설정에 있는 값이 기본값보다 우선
        2. 중첩된 딕셔너리는 재귀적으로 병합
        3. 리스트나 기타 타입은 설정 값으로 완전 대체
        4. 설정에 없는 키는 기본값에서 가져옴
        
        Args:
            config (Dict[str, Any]): 사용자 설정 딕셔너리 (우선순위 높음)
            defaults (Dict[str, Any]): 기본값 딕셔너리 (우선순위 낮음)
            
        Returns:
            Dict[str, Any]: 병합된 설정 딕셔너리
            
        Example:
            >>> defaults = {"model": {"temperature": 0.7, "max_tokens": 1000}, "debug": True}
            >>> config = {"model": {"temperature": 0.9}, "name": "my_agent"}
            >>> result = ConfigLoader._merge_defaults(config, defaults)
            >>> print(result)
            {
                'model': {'temperature': 0.9, 'max_tokens': 1000},
                'debug': True,
                'name': 'my_agent'
            }
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
        
        설정 딕셔너리를 YAML 파일로 저장하는 메서드입니다.
        디렉토리가 존재하지 않으면 자동으로 생성하며, 읽기 쉬운 형식으로 저장합니다.
        
        저장 옵션:
        - 블록 스타일 사용 (default_flow_style=False)
        - 키 정렬 안함 (원본 순서 유지)
        - 2칸 들여쓰기
        - UTF-8 인코딩
        
        Args:
            config (Dict[str, Any]): 저장할 설정 딕셔너리
            file_path (Union[str, Path]): 저장할 파일 경로
            format (str): 출력 형식. 현재는 "yaml"만 지원
            
        Returns:
            None
            
        Raises:
            ValueError: 지원되지 않는 형식을 지정한 경우
            IOError: 파일 쓰기 권한이 없거나 디스크 공간이 부족한 경우
            yaml.YAMLError: YAML 직렬화 오류가 발생한 경우
            
        Example:
            >>> config = {"metadata": {"name": "test_agent"}}
            >>> ConfigLoader.save_config(config, "output/agent.yaml")
            # output/agent.yaml 파일이 생성됨
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
        
        기본 에이전트 설정 구조를 반환하는 메서드입니다.
        새로운 에이전트를 생성하거나 예제 설정을 만들 때 사용할 수 있습니다.
        
        기본 설정 포함 사항:
        - 기본 메타데이터 (이름, 설명, 버전)
        - OpenAI GPT-4 모델 설정
        - 기본 시스템 프롬프트
        - 대화 버퍼 윈도우 메모리 (최근 10개 메시지)
        - 빈 도구 목록
        
        Returns:
            Dict[str, Any]: schema.json과 호환되는 기본 설정 딕셔너리
            
        Note:
            반환되는 설정은 schema.json의 요구사항을 모두 만족하며,
            바로 사용하거나 필요에 따라 수정할 수 있습니다.
            
        Example:
            >>> default = ConfigLoader.get_default_config()
            >>> default['metadata']['name'] = 'my_custom_agent'
            >>> ConfigLoader.save_config(default, 'my_agent.yaml')
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
        
        예제 설정 파일을 생성하는 편의 메서드입니다.
        get_default_config()에서 반환된 기본 설정을 지정된 경로에 YAML 파일로 저장합니다.
        
        생성되는 파일의 특징:
        - 완전한 기본 에이전트 설정
        - schema.json과 완전 호환
        - 바로 사용 가능한 형태
        - 주석이나 설명은 포함되지 않음 (순수 설정만)
        
        Args:
            file_path (Union[str, Path]): 생성할 예제 설정 파일의 경로
            
        Returns:
            None
            
        Raises:
            IOError: 파일 생성 권한이 없거나 디스크 공간이 부족한 경우
            
        Example:
            >>> ConfigLoader.create_example_config("examples/basic_agent.yaml")
            # examples/basic_agent.yaml 파일이 기본 설정으로 생성됨
            
        Note:
            이 메서드는 내부적으로 get_default_config()와 save_config()를 사용합니다.
            더 복잡한 예제가 필요한 경우 examples/configs/ 디렉토리의 파일들을 참조하세요.
        """
        config = ConfigLoader.get_default_config()
        ConfigLoader.save_config(config, file_path) 