# LangGraph ReAct Agent Configuration Schema

A comprehensive YAML/JSON schema validation system for configuring ReAct (Reasoning and Acting) agents using LangGraph with **simplified tool integration**.

## 🎯 Overview

This project provides a robust schema validation system that allows users to define AI agents through simple YAML configuration files. The system focuses on practical, implementable features with **streamlined tool integration** supporting just two types: **Built-in LangChain BaseTool implementations** and **MCP tools via streamable_http**.

## ✨ Key Features

- 📝 **YAML/JSON Configuration**: Define agents through simple configuration files
- 🔧 **Multiple LLM Providers**: OpenAI, AWS Bedrock, OpenAI-compatible APIs
- 🧠 **Memory Management**: Conversation history with configurable windows
- 🔍 **Knowledge Base Integration**: FAISS and Milvus vector databases
- 🛠️ **Ultra-simple Tool Integration**: Just two types - builtin and MCP
- ⚡ **Streamable HTTP Only**: Simple name + URL configuration for web UIs
- 🎯 **Zero Configuration Overhead**: MCP servers provide all their tools automatically

## 🚀 Supported Features

### LLM Providers
- **OpenAI**: Standard OpenAI API (GPT-4, GPT-3.5-turbo, etc.)
- **OpenAI Compatible**: vLLM and other OpenAI-compatible APIs  
- **AWS Bedrock**: Claude models via AWS Bedrock

### Tool Integration (Simplified)
- **Built-in Tools**: LangChain BaseTool implementations (calculator, web_search, file_manager, knowledge_search)
- **MCP Tools**: Model Context Protocol servers via streamable_http (weather, math, custom APIs)

### Memory Types
- **Conversation Buffer Window**: Recent conversation history (configurable size)

### Vector Databases
- **FAISS**: Facebook AI Similarity Search (local/in-memory)
- **Milvus**: Open-source vector database

## 📁 Project Structure

```
├── src/
│   ├── schemas/
│   │   └── agent_config.py      # Pydantic models for simplified configuration
│   ├── core/
│   │   └── tool_registry.py     # Simplified tool registry for builtin + MCP
│   ├── agents/
│   │   ├── react_agent.py       # ReAct agent with simplified tools
│   │   └── tools.py             # Built-in LangChain BaseTool implementations
│   └── utils/
│       └── config_loader.py     # Configuration loading utilities
├── examples/
│   ├── configs/
│   │   ├── example_agent.yaml   # Mixed builtin + MCP example
│   │   └── mcp_agent.yaml       # Pure MCP example
│   └── mcp_servers/
│       └── math_server.py       # Example MCP server
└── tests/
    ├── test_config_parser.py    # Unit tests
    └── test_integration.py      # Integration tests
```

## 🛠️ Installation

```bash
# Install core dependencies
pip install pydantic pyyaml langchain langgraph

# Install MCP integration
pip install langchain-mcp-adapters

# Or install all at once
pip install -r requirements.txt
```

## 📝 Configuration Examples

### Simplified Tool Integration Example
```yaml
metadata:
  name: "my-agent"
  description: "AI assistant with simplified tool integration"

model:
  provider: "openai"
  name: "gpt-4"
  api_key: "OPENAI_API_KEY"

# Two types of tools: builtin and mcp
tools:
  # Built-in LangChain BaseTool implementations
  - type: "builtin"
    name: "calculator"
  
  - type: "builtin"
    name: "web_search"
  
  - type: "builtin"
    name: "file_manager"

  # MCP tools via streamable_http (just name + URL!)
  - type: "mcp"
    name: "weather"
    url: "http://weather-service:8000/mcp"

  - type: "mcp"
    name: "math_tools"
    url: "http://math-service:8000/mcp"

prompt:
  system_prompt: |
    You are a helpful AI assistant with access to built-in tools and MCP services.
    Use these tools intelligently to answer questions and solve problems.
```

### Pure MCP Example
```yaml
metadata:
  name: "mcp-only-agent"
  description: "Agent powered entirely by MCP tools"

model:
  provider: "openai"
  name: "gpt-4"
  api_key: "OPENAI_API_KEY"

# Only MCP tools
tools:
  - type: "mcp"
    name: "weather"
    url: "http://weather-service:8000/mcp"

  - type: "mcp"
    name: "calculator"
    url: "http://math-service:8000/mcp"

  - type: "mcp"
    name: "business_api"
    url: "https://api.company.com/mcp"
    timeout: 45

prompt:
  system_prompt: |
    You are an AI assistant powered by MCP tools.
    Use weather, math, and business API tools to help users.
```

### Built-in Tools Only Example
```yaml
metadata:
  name: "builtin-agent"
  description: "Agent using only built-in tools"

model:
  provider: "openai"
  name: "gpt-4"
  api_key: "OPENAI_API_KEY"

# Only built-in tools
tools:
  - type: "builtin"
    name: "calculator"
  
  - type: "builtin"
    name: "web_search"
  
  - type: "builtin"
    name: "file_manager"
  
  - type: "builtin"
    name: "knowledge_search"

knowledge:
  provider: "faiss"
  collection_name: "local-docs"
  embedding_model: "text-embedding-ada-002"

prompt:
  system_prompt: |
    You are a helpful AI assistant with built-in tools.
    Use calculator, web search, file management, and knowledge search to help users.
```

## 🧪 Available Built-in Tools

The system includes these LangChain BaseTool implementations:

- **`calculator`**: Basic mathematical calculations
- **`web_search`**: Web search functionality (mock implementation)
- **`file_manager`**: File read/write/list operations
- **`knowledge_search`**: Knowledge base search functionality

## 🔧 Usage

### Basic Agent Usage
```python
from src.agents.react_agent import ReActAgent

# Load agent from configuration
agent = ReActAgent("examples/configs/example_agent.yaml")

# Initialize and run
await agent.initialize()
response = await agent.run("What is 25 + 37?")
print(response["response"])  # Built-in calculator or MCP math tools will be used
```

### MCP Server Setup

Create a simple MCP server (see `examples/mcp_servers/math_server.py`):
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math Tools")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    # Run as HTTP server for streamable_http transport
    mcp.run(transport="streamable_http", port=8000)
```

Configure your agent:
```yaml
tools:
  - type: "mcp"
    name: "math_tools"
    url: "http://localhost:8000/mcp"
```

### Web UI Benefits

This ultra-simplified approach is perfect for web-based configuration interfaces:
- **Minimal inputs**: Just tool type, name, and URL (for MCP)
- **Zero complex setup**: No need for command, args, env variables, or filtering
- **Remote deployment**: All MCP servers are HTTP-accessible
- **Easy testing**: Can test MCP endpoints with curl/Postman
- **Automatic discovery**: MCP servers provide all their available tools

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
- **Unit Tests**: Configuration parsing, schema validation, tool registry
- **Integration Tests**: End-to-end configuration loading, tool initialization
- ✅ All configuration files validated against schema
- ✅ Built-in and MCP tool integration
- ✅ Error handling and edge cases

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

## 🎨 Key Benefits

- **Type Safety**: Full Pydantic validation with detailed error messages
- **Environment Variables**: Automatic substitution of `${VAR_NAME}` patterns
- **Ultra-simple Tools**: Just two types - builtin LangChain tools and MCP via HTTP
- **Web UI Ready**: Perfect for web-based agent configuration interfaces
- **Zero Configuration Overhead**: MCP servers only need name + URL, provide all tools automatically
- **Extensible**: Easy to add new built-in tools or MCP servers

## 🚧 Roadmap

This version focuses on simplified, implementable tool integration. Future enhancements may include:

- Additional LLM providers (Anthropic direct, Google, etc.)
- More memory types (summary, vector-based)
- Additional vector databases (Pinecone, ChromaDB, etc.)
- Enhanced built-in tools
- Streaming support
- Multi-agent configurations

## 📄 License

MIT License - see LICENSE file for details.
