# LangGraph Test Project

A **practical ReAct agent implementation** using LangGraph with streamlined tool integration and Docker deployment support.

## 🎯 Overview

This project demonstrates a working ReAct (Reasoning and Acting) agent implementation using LangGraph with support for built-in tools and MCP (Model Context Protocol) integration. The focus is on **simplicity and deployability** rather than comprehensive feature coverage.

## ✨ Key Features

- 🤖 **ReAct Agent**: LangGraph-based reasoning and acting agent
- 🛠️ **Dual Tool Support**: Built-in LangChain tools + MCP tools via HTTP
- 🐳 **Docker Ready**: Complete containerization with docker-compose
- 🔧 **OpenAI Integration**: GPT-4 and other OpenAI models
- 📝 **YAML Configuration**: Simple agent configuration via YAML
- 🌐 **FastAPI Server**: RESTful API for web integration
- 📊 **Health Monitoring**: Built-in health checks and logging

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Clone and setup
git clone <repository>
cd langgraph-test

# Create environment file
echo "OPENAI_API_KEY=your_openai_api_key" > .env

# Start everything with MCP math tools
make compose-up

# Test the API
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 15 + 23?"}'
```

### Option 2: Single Container
```bash
# Deploy with built-in tools only
make docker-deploy

# Deploy with MCP tools
make docker-deploy CONFIG=mcp_agent.yaml
```

## 📁 Project Structure

```
├── src/
│   ├── agents/
│   │   └── react_agent.py       # ReAct agent implementation
│   ├── api/
│   │   ├── app.py              # FastAPI application
│   │   └── models.py           # API request/response models
│   ├── core/
│   │   ├── tool_registry.py    # Tool loading and management
│   │   └── config_parser.py    # Configuration processing
│   ├── schemas/
│   │   └── agent_config.py     # Pydantic configuration models
│   └── tools/
│       └── builtin_tools.py    # Built-in LangChain tools
├── examples/
│   ├── configs/                # Agent configuration examples
│   └── mcp_servers/
│       └── math_server.py      # Example MCP math server
├── scripts/
│   ├── docker.sh              # Docker management script
│   └── run_api_server.py      # API server runner
├── docker-compose.yml         # Multi-service Docker setup
├── Dockerfile                 # Main API server image
├── Dockerfile.mcp            # MCP server image
└── Makefile                  # Development and deployment commands
```

## 🛠️ Supported Features

### Current Implementation
- **LLM Providers**: OpenAI, OpenAI-compatible APIs
- **Tool Types**: 
  - Built-in: `calculator`, `web_search`, `file_manager`
  - MCP: Math tools via HTTP (extendable)
- **Memory**: Simple buffer and conversation window
- **Deployment**: Docker, docker-compose
- **API**: FastAPI with health checks

### Configuration Schema
```yaml
metadata:
  name: "my-agent"
  description: "ReAct agent with tool integration"

model:
  provider: "openai"
  name: "gpt-4"
  api_key: "OPENAI_API_KEY"
  parameters:
    temperature: 0.7
    max_tokens: 1000

tools:
  # Built-in LangChain tools
  - type: "builtin"
    name: "calculator"
  
  # MCP tools via HTTP
  - type: "mcp"
    name: "math_tools"
    url: "http://mcp-server:3001/mcp"
    timeout: 30

prompt:
  system_prompt: |
    You are a helpful AI assistant with access to various tools.
    Use these tools to solve problems and answer questions accurately.
```

## 🧪 Available Tools

### Built-in Tools
- **`calculator`**: Basic mathematical operations
- **`web_search`**: Web search functionality (mock implementation)
- **`file_manager`**: File read/write operations

### MCP Tools (via HTTP)
- **Math Server**: Addition, subtraction, multiplication, division, power, square root
- Extensible to any HTTP-accessible MCP server

## 🔧 Usage Examples

### API Integration
```bash
# Start services
make compose-up

# Chat with math tools
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate the square root of 144 and multiply by 5"}'

# Response includes tool usage
{
  "response": "The square root of 144 is 12, and 12 multiplied by 5 equals 60.",
  "tools_used": ["square_root", "multiply"]
}
```

### Python Integration
```python
from src.agents.react_agent import ReActAgent

# Load agent from configuration
agent = ReActAgent("examples/configs/mcp_agent.yaml")
await agent.initialize()

# Run with tool usage
response = await agent.run("What is 157 × 89?")
print(response["response"])  # "157 × 89 = 13,973"
print(response["tools_used"])  # ["multiply"]
```

## 🐳 Docker Commands (via Makefile)

```bash
# Development
make install              # Install dependencies
make test                # Run tests
make lint                # Code linting

# Docker (scripts/docker.sh)
make docker-deploy       # Full deployment
make docker-logs         # View logs
make docker-stop         # Stop container

# Docker Compose
make compose-up          # Start all services
make compose-logs        # View all logs
make compose-down        # Stop all services

# Utilities
make check-env           # Check environment setup
make list-configs        # Show available configs
```

## 🔑 Environment Setup

Create a `.env` file in the project root:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
LOG_LEVEL=INFO
```

For MCP/Cursor integration, add to `.cursor/mcp.json`:
```json
{
  "env": {
    "OPENAI_API_KEY": "your_openai_api_key"
  }
}
```

## 🧪 Testing

```bash
# Run all tests
make test

# Test with Docker
make docker-deploy
curl http://localhost:8000/health

# Test MCP integration
make compose-up
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 + 37?"}'
```

## 🚧 Limitations & Future Work

### Current Limitations
- **LLM Providers**: Only OpenAI and compatible APIs
- **Vector Databases**: Not yet implemented (schema defined but unused)
- **Memory Types**: Basic implementations only
- **Tools**: Limited built-in tools, MCP via HTTP only

### Roadmap
- Additional LLM providers (Anthropic, Google, Mistral)
- Vector database integration (FAISS, Milvus)
- Enhanced memory management
- More built-in tools
- WebSocket support for MCP
- Streaming responses

## 📄 License

MIT License - see LICENSE file for details.

---

**Note**: This is a **practical implementation** focused on deployability and real-world usage rather than comprehensive feature coverage. The configuration schema supports more features than currently implemented to enable future extensibility.
