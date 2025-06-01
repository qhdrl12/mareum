"""
Pydantic models for ReAct agent configuration schema.

This module defines the complete schema for YAML/JSON configuration files
that users will use to define their ReAct agents.

이 모듈은 사용자가 ReAct 에이전트를 정의하기 위해 사용할 YAML/JSON 설정 파일의
완전한 스키마를 정의합니다.

TODO: MCP(Model Context Protocol) 통합 예정
- ToolConfig, ToolParameter 클래스는 MCP 표준으로 대체될 예정입니다.
- 현재 도구 관련 구조는 임시적이며, MCP 도구 스키마로 전면 재설계됩니다.
- 검색 키워드: "TODO: MCP"
"""

from typing import Any, Dict, List, Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class LLMProvider(str, Enum):
    """
    Supported LLM providers.

    지원되는 대형 언어 모델(LLM) 제공업체를 정의하는 열거형 클래스입니다.
    현재 OpenAI, OpenAI 호환 API(vLLM 등), AWS Bedrock을 지원합니다.
    """

    OPENAI = "openai"  # OpenAI의 공식 API (GPT-4, GPT-3.5-turbo 등)
    OPENAI_COMPATIBLE = "openai_compatible"  # vLLM 및 기타 OpenAI 호환 API
    AWS_BEDROCK = "aws_bedrock"  # AWS Bedrock의 Claude 모델


class MemoryType(str, Enum):
    """
    Supported memory types.

    에이전트가 사용할 수 있는 메모리 타입을 정의하는 열거형 클래스입니다.
    대화 기록을 유지하는 다양한 버퍼 방식을 지원합니다.
    """

    SIMPLE_BUFFER = "simple_buffer"  # 간단한 버퍼 방식
    CONVERSATION_BUFFER_WINDOW = (
        "conversation_buffer_window"  # 최근 N개의 대화 기록 유지
    )


class VectorProvider(str, Enum):
    """
    Supported vector database providers.

    지원되는 벡터 데이터베이스 제공업체를 정의하는 열거형 클래스입니다.
    지식 베이스 구축과 유사도 검색에 사용됩니다.
    """

    FAISS = "faiss"  # Facebook AI Similarity Search (로컬/인메모리)
    MILVUS = "milvus"  # 오픈소스 벡터 데이터베이스


class AgentMetadata(BaseModel):
    """
    Agent metadata information.

    에이전트의 메타데이터 정보를 정의하는 클래스입니다.
    에이전트의 이름, 버전, 소유자, 설명, 태그 등의 기본 정보를 포함합니다.
    """

    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    version: str = Field(default="1.0.0", description="Agent version")
    owner: Optional[str] = Field(None, description="Agent owner/creator")
    description: Optional[str] = Field(
        None, description="Agent description", max_length=500
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Agent tags for categorization"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """
        Validate agent name format.

        에이전트 이름의 형식을 검증합니다.
        영숫자, 하이픈(-), 언더스코어(_)만 허용됩니다.

        Args:
            v (str): 검증할 에이전트 이름

        Returns:
            str: 검증된 에이전트 이름

        Raises:
            ValueError: 이름 형식이 올바르지 않은 경우
        """
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Agent name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v


class ModelConfig(BaseModel):
    """
    LLM model configuration.

    대형 언어 모델(LLM)의 설정을 정의하는 클래스입니다.
    모델 제공업체, 모델명, 인증 정보, API 엔드포인트, 모델 파라미터 등을 포함합니다.
    """

    provider: LLMProvider = Field(..., description="LLM provider")
    name: str = Field(
        ..., description="Model name (e.g., 'gpt-4', 'claude-3-5-sonnet')"
    )
    api_key: str = Field(
        ..., description="Environment variable name for API credentials"
    )
    base_url: Optional[str] = Field(
        None,
        description="Base URL for OpenAI-compatible APIs (required for openai_compatible)",
    )
    region: Optional[str] = Field(
        None, description="AWS region (required for aws_bedrock)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Model-specific parameters (temperature, max_tokens, etc.)",
    )

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v):
        """
        Validate model parameters.

        모델 파라미터의 유효성을 검증합니다.
        temperature는 0-2 범위, max_tokens는 양의 정수여야 합니다.

        Args:
            v (Dict[str, Any]): 검증할 모델 파라미터 딕셔너리

        Returns:
            Dict[str, Any]: 검증된 모델 파라미터

        Raises:
            ValueError: 파라미터 값이 유효하지 않은 경우
        """
        if v is None:
            return {}

        # 공통 파라미터 검증
        if "temperature" in v:
            temp = v["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                raise ValueError("Temperature must be a number between 0 and 2")

        if "max_tokens" in v:
            max_tokens = v["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1:
                raise ValueError("max_tokens must be a positive integer")

        return v

    @model_validator(mode="after")
    def validate_provider_config(self):
        """
        Validate provider-specific configuration.

        제공업체별 특정 설정의 유효성을 검증합니다.
        - OpenAI 호환: base_url 필수
        - AWS Bedrock: region 필수, Claude 모델만 지원

        Returns:
            ModelConfig: 검증된 모델 설정 객체

        Raises:
            ValueError: 제공업체별 필수 설정이 누락된 경우
        """
        if self.provider == LLMProvider.OPENAI_COMPATIBLE:
            if not self.base_url:
                raise ValueError("OpenAI-compatible providers require base_url")

        elif self.provider == LLMProvider.AWS_BEDROCK:
            if not self.region:
                raise ValueError("AWS Bedrock requires region")
            if not self.name.startswith("claude-"):
                raise ValueError("AWS Bedrock currently only supports Claude models")

        return self


class MemoryConfig(BaseModel):
    """
    Memory configuration for the agent.

    에이전트의 메모리 설정을 정의하는 클래스입니다.
    대화 기록 유지 방식과 관련 설정을 포함합니다.
    """

    type: MemoryType = Field(..., description="Type of memory to use")
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Memory-specific configuration"
    )

    @model_validator(mode="after")
    def validate_memory_config(self):
        """
        Validate memory configuration based on type.

        메모리 타입에 따른 설정의 유효성을 검증합니다.
        대화 버퍼 윈도우의 경우 k(윈도우 크기) 값을 검증하고 기본값을 설정합니다.

        Returns:
            MemoryConfig: 검증된 메모리 설정 객체

        Raises:
            ValueError: 윈도우 크기가 양의 정수가 아닌 경우
        """
        if self.config is None:
            self.config = {}

        if self.type in [
            MemoryType.SIMPLE_BUFFER,
            MemoryType.CONVERSATION_BUFFER_WINDOW,
        ]:
            if "k" not in self.config:
                self.config["k"] = 5  # 기본값: 최근 5개 대화
            elif not isinstance(self.config["k"], int) or self.config["k"] < 1:
                raise ValueError("Window size (k) must be a positive integer")

        return self


class ToolType(str, Enum):
    """
    Tool integration types.
    
    도구 통합 타입을 정의합니다.
    """
    BUILTIN = "builtin"  # LangChain BaseTool implementations
    MCP = "mcp"  # MCP servers via streamable_http


class ToolConfig(BaseModel):
    """
    Simplified tool configuration supporting BaseTool and MCP.
    
    BaseTool과 MCP를 지원하는 간소화된 도구 설정입니다.
    """
    type: ToolType = Field(..., description="Tool type: builtin or mcp")
    name: str = Field(..., description="Tool name or identifier")
    
    # MCP-specific fields (only used when type is "mcp")
    url: Optional[str] = Field(None, description="MCP server URL (required for mcp type)")
    timeout: int = Field(default=30, description="Connection timeout in seconds for MCP")
    
    @model_validator(mode='after')
    def validate_mcp_config(self):
        """Validate MCP-specific configuration."""
        if self.type == ToolType.MCP:
            if not self.url:
                raise ValueError("url is required when type is 'mcp'")
        elif self.type == ToolType.BUILTIN:
            # For builtin tools, MCP fields should not be used
            if self.url:
                raise ValueError("url is not used for builtin tools")
        return self


class KnowledgeConfig(BaseModel):
    """
    Knowledge base configuration.

    지식 베이스 설정을 정의하는 클래스입니다.
    벡터 데이터베이스, 임베딩 모델, 검색 설정 등을 포함합니다.
    """

    provider: VectorProvider = Field(..., description="Vector database provider")
    credentials_key: Optional[str] = Field(
        None, description="Environment variable for credentials"
    )
    collection_name: str = Field(..., description="Collection/index name")
    embedding_model: Optional[str] = Field(
        "text-embedding-ada-002", description="Embedding model"
    )
    search_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Search configuration (top_k, score_threshold, etc.)",
    )

    @field_validator("search_config")
    @classmethod
    def validate_search_config(cls, v):
        """
        Validate search configuration.

        검색 설정의 유효성을 검증합니다.
        top_k는 양의 정수, score_threshold는 0-1 범위의 값이어야 합니다.

        Args:
            v (Dict[str, Any]): 검증할 검색 설정 딕셔너리

        Returns:
            Dict[str, Any]: 검증된 검색 설정

        Raises:
            ValueError: 설정 값이 유효하지 않은 경우
        """
        if v is None:
            v = {}

        # 기본값 설정
        if "top_k" not in v:
            v["top_k"] = 5  # 기본값: 상위 5개 결과 반환
        elif not isinstance(v["top_k"], int) or v["top_k"] < 1:
            raise ValueError("top_k must be a positive integer")

        if "score_threshold" in v:
            threshold = v["score_threshold"]
            if (
                not isinstance(threshold, (int, float))
                or threshold < 0
                or threshold > 1
            ):
                raise ValueError("score_threshold must be a number between 0 and 1")

        return v


class PromptConfig(BaseModel):
    """
    Prompt configuration for the agent.

    에이전트의 프롬프트 설정을 정의하는 클래스입니다.
    시스템 프롬프트와 ReAct 템플릿을 포함합니다.
    """

    system_prompt: str = Field(
        ..., description="System prompt for the agent", min_length=1
    )
    react_template: Optional[str] = Field(
        None, description="Custom ReAct template (uses default if not provided)"
    )

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v):
        """
        Validate system prompt.

        시스템 프롬프트의 유효성을 검증합니다.
        빈 문자열이나 공백만 있는 프롬프트는 허용되지 않습니다.

        Args:
            v (str): 검증할 시스템 프롬프트

        Returns:
            str: 검증되고 정리된 시스템 프롬프트

        Raises:
            ValueError: 프롬프트가 비어있는 경우
        """
        if len(v.strip()) == 0:
            raise ValueError("System prompt cannot be empty")
        return v.strip()


class AgentConfig(BaseModel):
    """
    Complete agent configuration schema.

    에이전트의 전체 설정을 정의하는 메인 클래스입니다.
    모델, 메모리, 지식베이스, 도구, 프롬프트 등 에이전트의 모든 구성 요소를 포함합니다.
    """

    metadata: AgentMetadata = Field(..., description="Agent metadata")
    agent_type: Literal["react"] = Field(
        "react", description="Agent type (fixed as 'react' for v1.0)"
    )
    model: ModelConfig = Field(..., description="LLM model configuration")
    memory: Optional[MemoryConfig] = Field(None, description="Memory configuration")
    knowledge: Optional[KnowledgeConfig] = Field(
        None, description="Knowledge base configuration"
    )
    tools: List[ToolConfig] = Field(
        default_factory=list, description="Tool configurations (BaseTool and MCP)"
    )
    prompt: Optional[PromptConfig] = Field(None, description="Prompt configuration")

    @model_validator(mode="after")
    def validate_config(self):
        """
        Validate complete agent configuration.

        에이전트 설정의 전체 유효성을 검증합니다.
        - 모델과 지식베이스 임베딩 모델의 호환성 검증
        - 프로바이더별 필수 설정 검증

        Returns:
            AgentConfig: 검증된 에이전트 설정 객체

        Raises:
            ValueError: 설정이 유효하지 않은 경우
        """
        # Validate embedding model compatibility
        if self.knowledge and self.knowledge.embedding_model:
            if (
                self.model.provider == LLMProvider.OPENAI
                and "ada-002" not in self.knowledge.embedding_model
            ):
                # This is just a warning, not an error
                pass

        return self

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Generate JSON schema for this configuration.

        이 설정에 대한 JSON 스키마를 생성합니다.
        외부 도구나 검증에 사용할 수 있습니다.

        Returns:
            Dict[str, Any]: JSON 스키마 딕셔너리
        """
        return self.model_json_schema()

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "AgentConfig":
        """
        Load configuration from YAML file.

        YAML 파일에서 에이전트 설정을 로드합니다.

        Args:
            file_path (str): YAML 파일 경로

        Returns:
            AgentConfig: 로드된 에이전트 설정 객체

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            yaml.YAMLError: YAML 파싱 오류
            ValidationError: 설정 검증 오류
        """
        import yaml

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml_file(self, file_path: str) -> None:
        """
        Save configuration to YAML file.

        에이전트 설정을 YAML 파일로 저장합니다.

        Args:
            file_path (str): 저장할 YAML 파일 경로

        Raises:
            IOError: 파일 쓰기 오류
        """
        import yaml

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.model_dump(),
                f,
                default_flow_style=False,  # 블록 스타일 사용
                allow_unicode=True,  # 유니코드 허용
                sort_keys=False,  # 키 정렬 안함
            )
