"""
Pydantic models for ReAct agent configuration schema.

This module defines the complete schema for YAML/JSON configuration files
that users will use to define their ReAct agents.
"""

from typing import Any, Dict, List, Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"  # For vLLM and other OpenAI-compatible APIs
    AWS_BEDROCK = "aws_bedrock"  # For AWS Bedrock Claude


class MemoryType(str, Enum):
    """Supported memory types."""
    CONVERSATION_BUFFER_WINDOW = "conversation_buffer_window"  # Simple recent conversation history


class VectorProvider(str, Enum):
    """Supported vector database providers."""
    FAISS = "faiss"
    MILVUS = "milvus"


class AgentMetadata(BaseModel):
    """Agent metadata information."""
    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    version: str = Field(default="1.0.0", description="Agent version")
    owner: Optional[str] = Field(None, description="Agent owner/creator")
    description: Optional[str] = Field(None, description="Agent description", max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list, description="Agent tags for categorization")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate agent name format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Agent name must contain only alphanumeric characters, hyphens, and underscores')
        return v


class ModelConfig(BaseModel):
    """LLM model configuration."""
    provider: LLMProvider = Field(..., description="LLM provider")
    name: str = Field(..., description="Model name (e.g., 'gpt-4', 'claude-3-5-sonnet')")
    credentials_key: str = Field(..., description="Environment variable name for API credentials")
    base_url: Optional[str] = Field(None, description="Base URL for OpenAI-compatible APIs (required for openai_compatible)")
    region: Optional[str] = Field(None, description="AWS region (required for aws_bedrock)")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Model-specific parameters (temperature, max_tokens, etc.)"
    )
    
    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v):
        """Validate model parameters."""
        if v is None:
            return {}
        
        # Common parameter validation
        if 'temperature' in v:
            temp = v['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                raise ValueError('Temperature must be a number between 0 and 2')
        
        if 'max_tokens' in v:
            max_tokens = v['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens < 1:
                raise ValueError('max_tokens must be a positive integer')
        
        return v
    
    @model_validator(mode='after')
    def validate_provider_config(self):
        """Validate provider-specific configuration."""
        if self.provider == LLMProvider.OPENAI_COMPATIBLE:
            if not self.base_url:
                raise ValueError('OpenAI-compatible providers require base_url')
        
        elif self.provider == LLMProvider.AWS_BEDROCK:
            if not self.region:
                raise ValueError('AWS Bedrock requires region')
            if not self.name.startswith('claude-'):
                raise ValueError('AWS Bedrock currently only supports Claude models')
        
        return self


class MemoryConfig(BaseModel):
    """Memory configuration for the agent."""
    type: MemoryType = Field(..., description="Type of memory to use")
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Memory-specific configuration"
    )
    
    @model_validator(mode='after')
    def validate_memory_config(self):
        """Validate memory configuration based on type."""
        if self.config is None:
            self.config = {}
        
        if self.type == MemoryType.CONVERSATION_BUFFER_WINDOW:
            if 'k' not in self.config:
                self.config['k'] = 5  # Default to 5 recent conversations
            elif not isinstance(self.config['k'], int) or self.config['k'] < 1:
                raise ValueError('Window size (k) must be a positive integer')
        
        return self


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, boolean, etc.)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value if not required")


class ToolConfig(BaseModel):
    """Tool configuration."""
    name: str = Field(..., description="Tool name", min_length=1)
    description: str = Field(..., description="Tool description")
    type: Literal["api", "function", "builtin"] = Field(..., description="Tool type")
    
    # For API tools
    endpoint: Optional[str] = Field(None, description="API endpoint URL")
    method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="HTTP headers")
    
    # For function tools
    module: Optional[str] = Field(None, description="Python module path")
    function: Optional[str] = Field(None, description="Function name")
    
    # Tool parameters
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    
    @model_validator(mode='after')
    def validate_tool_config(self):
        """Validate tool configuration based on type."""
        if self.type == 'api':
            if not self.endpoint:
                raise ValueError('API tools require an endpoint')
        
        elif self.type == 'function':
            if not self.module or not self.function:
                raise ValueError('Function tools require module and function')
        
        elif self.type == 'builtin':
            # Builtin tools are predefined, no additional config needed
            pass
        
        return self


class KnowledgeConfig(BaseModel):
    """Knowledge base configuration."""
    provider: VectorProvider = Field(..., description="Vector database provider")
    credentials_key: Optional[str] = Field(None, description="Environment variable for credentials")
    collection_name: str = Field(..., description="Collection/index name")
    embedding_model: Optional[str] = Field("text-embedding-ada-002", description="Embedding model")
    search_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Search configuration (top_k, score_threshold, etc.)"
    )
    
    @field_validator('search_config')
    @classmethod
    def validate_search_config(cls, v):
        """Validate search configuration."""
        if v is None:
            v = {}
        
        # Set defaults
        if 'top_k' not in v:
            v['top_k'] = 5
        elif not isinstance(v['top_k'], int) or v['top_k'] < 1:
            raise ValueError('top_k must be a positive integer')
        
        if 'score_threshold' in v:
            threshold = v['score_threshold']
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                raise ValueError('score_threshold must be a number between 0 and 1')
        
        return v


class PromptConfig(BaseModel):
    """Prompt configuration for the agent."""
    system_prompt: str = Field(..., description="System prompt for the agent", min_length=1)
    react_template: Optional[str] = Field(
        None,
        description="Custom ReAct template (uses default if not provided)"
    )
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v):
        """Validate system prompt."""
        if len(v.strip()) == 0:
            raise ValueError('System prompt cannot be empty')
        return v.strip()


class AgentConfig(BaseModel):
    """Complete agent configuration schema."""
    metadata: AgentMetadata = Field(..., description="Agent metadata")
    agent_type: Literal["react"] = Field("react", description="Agent type (fixed as 'react' for v1.0)")
    model: ModelConfig = Field(..., description="LLM model configuration")
    memory: Optional[MemoryConfig] = Field(None, description="Memory configuration")
    tools: List[ToolConfig] = Field(default_factory=list, description="Available tools")
    knowledge: Optional[KnowledgeConfig] = Field(None, description="Knowledge base configuration")
    prompt: PromptConfig = Field(..., description="Prompt configuration")
    
    model_config = {
        "extra": "forbid",  # Forbid extra fields
        "validate_assignment": True,
        "use_enum_values": True
    }
        
    @field_validator('tools')
    @classmethod
    def validate_tools(cls, v):
        """Validate tools list."""
        if len(v) == 0:
            raise ValueError('At least one tool must be configured')
        
        # Check for duplicate tool names
        tool_names = [tool.name for tool in v]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError('Tool names must be unique')
        
        return v
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for this configuration."""
        return self.model_json_schema()
    
    @classmethod
    def from_yaml_file(cls, file_path: str) -> "AgentConfig":
        """Load configuration from YAML file."""
        import yaml
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    @classmethod
    def from_json_file(cls, file_path: str) -> "AgentConfig":
        """Load configuration from JSON file."""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def to_yaml_file(self, file_path: str) -> None:
        """Save configuration to YAML file."""
        import yaml
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.model_dump(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
    
    def to_json_file(self, file_path: str) -> None:
        """Save configuration to JSON file."""
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.model_dump(),
                f,
                indent=2,
                ensure_ascii=False
            ) 