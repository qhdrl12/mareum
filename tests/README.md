# Tests for LangGraph Test Project

This directory contains the test suite for the LangGraph Test project, organized into a structured hierarchy for better maintainability and efficiency.

## 📁 Test Structure

```
tests/
├── conftest.py                 # Shared pytest fixtures and configuration
├── test_data.py               # Centralized test data and constants
├── run_tests.py               # Test runner script (in project root)
├── pytest.ini                 # pytest configuration (in project root)
├── unit/                      # Unit tests (fast, isolated)
│   ├── test_config_parser.py
│   ├── test_tool_compatibility.py
│   └── test_config_parser_legacy.py
├── integration/               # Integration tests (cross-component)
│   ├── test_agent_integration.py
│   ├── test_react_agent.py
│   └── test_integration.py
├── api/                      # API endpoint tests
│   ├── test_api_endpoints.py
│   └── test_api_comprehensive.py
├── performance/              # Performance and load tests
│   └── test_performance.py
├── debug/                    # Debug utilities and scripts
│   └── debug_mcp_single.py
├── test_async_operations.py  # Async operation tests
└── test_error_handling.py    # Error handling tests
```

## 🏃‍♂️ Running Tests

### Using the Test Runner Script

The project includes a convenient test runner script (`run_tests.py`) with various options:

```bash
# Run default tests (fast tests, excluding slow ones)
python run_tests.py

# Run all tests
python run_tests.py --all

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --api
python run_tests.py --performance

# Run with coverage
python run_tests.py --unit --coverage

# Run tests in parallel
python run_tests.py --fast --parallel 4

# Verbose output
python run_tests.py --unit --verbose
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test categories using markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m api              # API tests only
pytest -m performance      # Performance tests only
pytest -m "not slow"       # Exclude slow tests
pytest -m smoke            # Smoke tests only

# Run specific test directories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run in parallel
pytest -n 4
```

## 🔖 Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests requiring multiple components
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.performance` - Performance and load tests
- `@pytest.mark.slow` - Tests that take longer to execute
- `@pytest.mark.mcp` - MCP (Model Context Protocol) specific tests
- `@pytest.mark.smoke` - Basic smoke tests for CI/CD
- `@pytest.mark.regression` - Regression tests for bug fixes
- `@pytest.mark.asyncio` - Async tests (automatically applied)

## 🧪 Test Types

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Minimal, mostly mocked
- **Examples**: Configuration parsing, utility functions, individual classes

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and workflows
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: May require real services or files
- **Examples**: Agent initialization, end-to-end workflows

### API Tests (`tests/api/`)
- **Purpose**: Test REST API endpoints
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: FastAPI test client, may require initialized agent
- **Examples**: HTTP endpoints, request/response validation

### Performance Tests (`tests/performance/`)
- **Purpose**: Test system performance and resource usage
- **Speed**: Slow (10+ seconds per test)
- **Dependencies**: May require significant resources
- **Examples**: Load testing, memory usage, throughput measurement

## 🔧 Test Configuration

### Shared Fixtures (`conftest.py`)
- `sample_valid_config` - Standard valid configuration
- `openai_compatible_config` - OpenAI-compatible configuration
- `config_parser` - ConfigParser instance
- `react_agent` - Initialized ReActAgent (async)
- `agent_manager` - AgentManager instance (async)
- `api_client` - FastAPI test client
- `mock_openai_api` - Mocked OpenAI API responses
- `test_utils` - Test utility functions

### Test Data (`test_data.py`)
Centralized test data including:
- Valid and invalid configurations
- Test queries for different scenarios
- Expected response patterns
- API test data
- Performance test parameters
- Error message patterns

## 📊 Coverage

Run tests with coverage to ensure comprehensive testing:

```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
# View coverage report at htmlcov/index.html
```

## 🐛 Debugging Tests

### Debug Directory
The `tests/debug/` directory contains utilities for debugging:
- `debug_mcp_single.py` - Debug single MCP operations

### Running Individual Tests
```bash
# Run a specific test file
pytest tests/unit/test_config_parser.py -v

# Run a specific test function
pytest tests/unit/test_config_parser.py::TestConfigParser::test_init -v

# Run with debugging output
pytest tests/unit/test_config_parser.py -v -s
```

## 🚀 CI/CD Integration

For continuous integration, use these commands:

```bash
# Quick smoke tests
python run_tests.py --smoke

# Fast test suite for PR checks
python run_tests.py --fast --coverage

# Full test suite for releases
python run_tests.py --all --coverage
```

## 📝 Test Writing Guidelines

1. **Use appropriate markers** to categorize tests
2. **Leverage shared fixtures** from `conftest.py`
3. **Use test data** from `test_data.py` for consistency
4. **Include docstrings** explaining test purpose
5. **Assert meaningful messages** for better debugging
6. **Clean up resources** in test teardown
7. **Test both success and failure cases**
8. **Use parametrized tests** for multiple scenarios
9. **Keep tests focused** and single-purpose
10. **Document complex test scenarios**

## 🔍 Test Quality Metrics

- **Unit Test Coverage**: Aim for >90%
- **Integration Test Coverage**: Aim for >80%
- **Performance Regression**: Track response times
- **Error Coverage**: Test all error paths
- **API Coverage**: Test all endpoints and methods

## 🤝 Contributing

When adding new tests:

1. Place tests in the appropriate directory (`unit/`, `integration/`, `api/`, `performance/`)
2. Add appropriate markers
3. Use shared fixtures and test data when possible
4. Update this README if adding new test categories
5. Ensure tests are deterministic and can run in isolation
6. Include both positive and negative test cases

For questions about testing, please refer to the project documentation or contact the maintainers. 