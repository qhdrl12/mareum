# LangGraph ReAct Agent Server

A comprehensive FastAPI server for running AI agents using LangGraph with YAML configuration.

## 🎯 Overview

This project provides a robust FastAPI server that allows users to deploy and interact with AI agents defined through simple YAML configuration files. The system includes comprehensive schema validation, Docker support, and RESTful APIs for agent interaction.

## 🚀 Quick Start

### Option 1: Run with Python (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with example configuration
python main.py --config examples/configs/example_agent.yaml

# Or use the convenience script
./scripts/run_server.sh --config examples/configs/example_agent.yaml --reload
```

### Option 2: Run with Docker (Production)

```bash
# Use the convenient Docker script
./scripts/docker_run.sh

# Or run manually with Docker commands
docker build -t langgraph-agent .
docker run -d \
  --name langgraph-agent-container \
  -p 8000:8000 \
  -v $(pwd)/examples/configs/example_agent.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  langgraph-agent \
  python main.py --config /app/config.yaml --host 0.0.0.0 --port 8000
```

### Option 3: Docker Compose (Simplified)

```bash
# If you prefer docker-compose (Redis removed)
docker-compose up --build
```

### Access the API

Once running, access:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Configuration Info**: http://localhost:8000/config

## 🌐 API Endpoints

### Chat with Agent
```bash
# Send a message to the agent
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me?",
    "session_id": "user123"
  }'
```

### Get Session Info
```bash
# Get information about a chat session
curl "http://localhost:8000/api/v1/chat/sessions/user123"
```

### Clear Session
```bash
# Clear a chat session
curl -X DELETE "http://localhost:8000/api/v1/chat/sessions/user123"
```

## 🛠️ Command Line Options

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH      Path to agent configuration YAML file
  -h, --host HOST        Host to bind server to (default: 0.0.0.0)
  -p, --port PORT        Port to bind server to (default: 8000)
  --reload               Enable auto-reload for development
  --log-level LEVEL      Set logging level (debug|info|warning|error)
  --help                 Show help message
```

## 🐳 Docker Configuration

### Docker Scripts

**Main Docker script** (`scripts/docker_run.sh`):
```bash
# Build and run with defaults
./scripts/docker_run.sh

# Custom configuration and port
./scripts/docker_run.sh --config my_agent.yaml --port 8080

# Only build the image
./scripts/docker_run.sh --build-only

# Stop container
./scripts/docker_run.sh --stop

# Show logs
./scripts/docker_run.sh --logs

# Open shell in container
./scripts/docker_run.sh --shell
```

### Dockerfile Features
- Multi-stage build for optimized image size
- Non-root user for security
- Health checks
- Proper logging and environment handling
- Python 3.11 with uv package manager

### Manual Docker Commands

```bash
# Build image
docker build -t langgraph-agent .

# Run container with config
docker run -d \
  --name langgraph-agent-container \
  -p 8000:8000 \
  -v $(pwd)/examples/configs/example_agent.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  langgraph-agent \
  python main.py --config /app/config.yaml

# View logs
docker logs -f langgraph-agent-container

# Stop and remove
docker stop langgraph-agent-container
docker rm langgraph-agent-container
```

### Environment Variables for Docker
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

## 🏗️ Project Structure

```
├── src/
│   ├── api/
│   │   ├── app.py               # FastAPI application factory
│   │   └── routers/
│   │       └── chat.py          # Chat API endpoints
│   ├── schemas/
│   │   ├── agent_config.py      # Pydantic models for configuration
│   │   └── chat.py              # Chat request/response models
│   ├── models/
│   │   └── agent.py             # Agent implementation
│   ├── core/
│   │   └── config_parser.py     # Configuration parsing and validation
│   └── utils/
│       └── config_loader.py     # Configuration loading utilities
├── examples/
│   └── configs/
│       └── example_agent.yaml   # Example agent configuration
├── scripts/
│   ├── run_server.sh           # Convenience script for Python execution
│   └── docker_run.sh           # Docker build and run script
├── Dockerfile                  # Production Docker image
├── docker-compose.yml         # Simplified Docker Compose (optional)
└── main.py                    # Server entry point
```

## 🚀 Supported Providers

### LLM Providers
- **OpenAI**: Standard OpenAI API (GPT-4, GPT-3.5-turbo, etc.)
- **OpenAI Compatible**: vLLM and other OpenAI-compatible APIs
- **AWS Bedrock**: Claude models via AWS Bedrock

### Memory Types
- **Conversation Buffer Window**: Simple recent conversation history (in-memory, default: 5 messages)

### Vector Databases
- **FAISS**: Facebook AI Similarity Search (local/in-memory)
- **Milvus**: Open-source vector database

## 💾 Session Storage

The current implementation uses **in-memory session storage** for simplicity. This means:
- Session data is stored in the application's memory
- Sessions are lost when the container/application restarts
- Suitable for development and testing
- For production, consider implementing persistent storage solutions

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
    max_messages: 5

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
    max_messages: 5

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
    max_messages: 5

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
- **Docker Ready**: Production-ready containerization
- **In-Memory Sessions**: Simple session management without external dependencies

## 🚧 Roadmap

This initial version focuses on core, implementable features. Future enhancements may include:

- Additional LLM providers (Anthropic direct, Google, etc.)
- Persistent session storage (Redis, Database)
- More memory types (summary, vector-based)
- Additional vector databases (Pinecone, ChromaDB, etc.)
- Advanced tool configurations
- Streaming support
- Multi-agent configurations

## 📄 License

MIT License - see LICENSE file for details.
