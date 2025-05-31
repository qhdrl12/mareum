# LangGraph ReAct Agent Configuration Schema

A comprehensive YAML/JSON schema validation system for configuring ReAct (Reasoning and Acting) agents using LangGraph.

## 🎯 Overview

This project provides a robust schema validation system that allows users to define AI agents through simple YAML configuration files. The system focuses on practical, implementable features rather than comprehensive coverage.

## 🚀 Supported Providers

### LLM Providers
- **OpenAI**: Standard OpenAI API (GPT-4, GPT-3.5-turbo, etc.)
- **OpenAI Compatible**: vLLM and other OpenAI-compatible APIs
- **AWS Bedrock**: Claude models via AWS Bedrock

### Memory Types
- **Conversation Buffer Window**: Simple recent conversation history (default: 5 messages)

### Vector Databases
- **FAISS**: Facebook AI Similarity Search (local/in-memory)
- **Milvus**: Open-source vector database

## 📁 Project Structure

```
├── src/
│   ├── schemas/
│   │   └── agent_config.py      # Pydantic models for configuration
│   └── utils/
│       └── config_loader.py     # Configuration loading utilities
│   ├── core/
│   │   └── config_parser.py     # YAML configuration parser with schema validation
├── examples/
│   ├── example_agent.yaml       # Basic OpenAI example
│   ├── openai_agent.yaml         # OpenAI API example
│   └── bedrock_agent.yaml      # AWS Bedrock Claude example
└── tests/
    ├── test_config_parser.py    # Unit tests for ConfigParser
    └── test_integration.py      # Integration tests for the system
```

## 🛠️ Installation

```bash
# Install dependencies
uv add pydantic pyyaml

# Or with pip
pip install pydantic pyyaml
```

## 📝 Configuration Examples

### OpenAI Agent
```yaml
metadata:
  name: "my-agent"
  description: "AI assistant using OpenAI"

model:
  provider: "openai"
  name: "gpt-4"
  credentials_key: "OPENAI_API_KEY"
  parameters:
    temperature: 0.7
    max_tokens: 2000

memory:
  type: "conversation_buffer_window"
  config:
    k: 5

knowledge:
  provider: "faiss"
  collection_name: "my-knowledge-base"
  embedding_model: "text-embedding-ada-002"
```

### vLLM Agent (OpenAI Compatible)
```yaml
metadata:
  name: "vllm-agent"
  description: "Local vLLM deployment"

model:
  provider: "openai_compatible"
  name: "llama-2-7b-chat"
  credentials_key: "VLLM_API_KEY"
  base_url: "http://localhost:8000/v1"
  parameters:
    temperature: 0.7
    max_tokens: 1000

memory:
  type: "conversation_buffer_window"
  config:
    k: 5

knowledge:
  provider: "faiss"
  collection_name: "local-docs"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### AWS Bedrock Claude Agent
```yaml
metadata:
  name: "bedrock-agent"
  description: "Enterprise AWS Bedrock agent"

model:
  provider: "aws_bedrock"
  name: "claude-3-5-sonnet-20241022"
  credentials_key: "AWS_ACCESS_KEY_ID"
  region: "us-east-1"
  parameters:
    temperature: 0.7
    max_tokens: 2000

memory:
  type: "conversation_buffer_window"
  config:
    k: 5

knowledge:
  provider: "milvus"
  credentials_key: "MILVUS_TOKEN"
  collection_name: "enterprise-knowledge"
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run only unit tests
python -m pytest tests/test_config_parser.py -v

# Run only integration tests
python -m pytest tests/test_integration.py -v
```

The test suite includes:
- **Unit Tests (28 tests)**: ConfigParser functionality, YAML parsing, schema validation
- **Integration Tests (12 tests)**: End-to-end configuration loading, environment variable substitution, provider-specific validation
- ✅ All configuration files validated against schema.json
- ✅ Environment variable substitution and default value handling
- ✅ Provider-specific validation (OpenAI, vLLM, Bedrock)
- ✅ Error handling and edge cases

## 🔧 Usage

### Validate Configuration
```python
from src.core.config_parser import ConfigParser

# Validate a YAML file
parser = ConfigParser(schema_path="schema.json")
try:
    config_data = parser.parse_from_file("my_agent.yaml")
    parser.validate_configuration(config_data)
    print("✅ Configuration is valid!")
except Exception as e:
    print(f"❌ Validation error: {e}")
```

### Load Configuration
```python
from src.utils.config_loader import ConfigLoader

# Load and parse configuration
config = ConfigLoader.load_config("my_agent.yaml")
print(f"Agent: {config['metadata']['name']}")
print(f"Model: {config['model']['provider']}/{config['model']['name']}")
```

### Use JSON Schema
```python
from src.core.config_parser import ConfigParser

# Use existing JSON schema for validation
parser = ConfigParser(schema_path="schema.json")
config_data = parser.parse_from_file("my_agent.yaml")
```

## 🔑 Environment Variables

Set the following environment variables based on your chosen providers:

### OpenAI
```bash
OPENAI_API_KEY=your_openai_api_key
```

### vLLM (OpenAI Compatible)
```bash
VLLM_API_KEY=your_vllm_api_key  # Optional for local deployments
```

### AWS Bedrock
```bash
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### Vector Databases
```bash
# For Milvus
MILVUS_TOKEN=your_milvus_token

# FAISS requires no credentials (local/in-memory)
```

## 🎨 Features

- **Type Safety**: Full Pydantic validation with detailed error messages
- **Environment Variables**: Automatic substitution of `${VAR_NAME}` patterns
- **Provider Validation**: Specific validation rules for each LLM provider
- **Extensible**: Easy to add new providers and memory types
- **JSON Schema Export**: Generate schemas for external tooling
- **Comprehensive Testing**: Full test coverage with multiple provider examples

## 🚧 Roadmap

This initial version focuses on core, implementable features. Future enhancements may include:

- Additional LLM providers (Anthropic direct, Google, etc.)
- More memory types (summary, vector-based)
- Additional vector databases (Pinecone, ChromaDB, etc.)
- Advanced tool configurations
- Streaming support
- Multi-agent configurations

## 📄 License

MIT License - see LICENSE file for details.
