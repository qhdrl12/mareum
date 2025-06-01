"""
Centralized test data for all test modules.
"""

# Valid configurations
VALID_CONFIGS = {
    "basic": {
        "metadata": {
            "name": "test-agent",
            "version": "1.0.0",
            "description": "Basic test agent"
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4o-mini",
            "api_key": "OPENAI_API_KEY"
        },
        "prompt": {
            "system_prompt": "You are a helpful assistant."
        }
    },
    
    "openai_compatible": {
        "metadata": {
            "name": "openai-compatible-agent",
            "version": "1.0.0",
            "description": "Test OpenAI-compatible agent configuration"
        },
        "model": {
            "provider": "openai_compatible",
            "name": "gpt-4o-mini",
            "api_key": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        "prompt": {
            "system_prompt": "You are a helpful assistant that uses OpenAI-compatible APIs and has access to tools."
        },
        "tools": [
            {
                "type": "builtin",
                "name": "calculator",
                "description": "Perform mathematical calculations"
            },
            {
                "type": "builtin", 
                "name": "web_search",
                "description": "Search the web for information"
            }
        ]
    },
    
    "with_tools": {
        "metadata": {
            "name": "agent-with-tools",
            "version": "1.0.0",
            "description": "Test agent with tools"
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4o-mini",
            "api_key": "OPENAI_API_KEY"
        },
        "prompt": {
            "system_prompt": "You are a helpful assistant with access to tools."
        },
        "tools": [
            {
                "type": "mcp",
                "name": "calculator",
                "description": "Basic calculator for mathematical operations",
                "url": "stdio://python -m tests.mock_mcp_server"
            }
        ]
    }
}

# Invalid configurations for error testing
INVALID_CONFIGS = {
    "missing_name": {
        "metadata": {
            "version": "1.0.0"
            # Missing required 'name' field
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4o-mini",
            "api_key": "OPENAI_API_KEY"
        }
    },
    
    "missing_model": {
        "metadata": {
            "name": "test-agent",
            "version": "1.0.0"
        }
        # Missing required 'model' field
    },
    
    "invalid_provider": {
        "metadata": {
            "name": "test-agent",
            "version": "1.0.0"
        },
        "model": {
            "provider": "invalid_provider",  # Invalid provider
            "name": "gpt-4",
            "api_key": "TEST_KEY"
        }
    },
    
    "missing_api_key": {
        "metadata": {
            "name": "test-agent",
            "version": "1.0.0"
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4o-mini"
            # Missing required 'api_key' field
        }
    }
}

# Test queries for different scenarios
TEST_QUERIES = {
    "simple_greeting": "Hello! Can you introduce yourself?",
    "calculation": "Calculate 45 * 67 + 123. Show me the step-by-step calculation.",
    "tool_forcing": "Use the calculator tool to compute 12 * 8",
    "complex_math": "What is the square root of 144 plus 25 times 3?",
    "story_request": "Tell me a short story about a robot learning to cook.",
    "reasoning": "If I have 5 apples and I eat 2, then buy 3 more, how many apples do I have?",
    "empty": "",
    "very_long": "A" * 1000 + " Please respond to this very long query."
}

# Expected responses for validation
EXPECTED_RESPONSE_PATTERNS = {
    "greeting_keywords": ["hello", "assistant", "help", "I am", "my name"],
    "calculation_keywords": ["calculate", "result", "answer", "*", "+", "="],
    "tool_usage_indicators": ["calculator", "tool", "using", "computed"],
    "math_result_patterns": [r"\d+", r"=\s*\d+", r"result.+\d+"]
}

# API test data
API_TEST_DATA = {
    "valid_requests": [
        {"message": "Hello, how are you?"},
        {"message": "Calculate 10 + 5"},
        {"message": "What is 2 * 3?"}
    ],
    
    "invalid_requests": [
        {},  # Missing message
        {"invalid_field": "test"},  # Wrong field name
        {"message": None},  # Null message
        {"message": 123}  # Non-string message
    ],
    
    "edge_case_requests": [
        {"message": ""},  # Empty message
        {"message": " "},  # Whitespace only
        {"message": "A" * 10000}  # Very long message
    ]
}

# Tool test data
TOOL_TEST_DATA = {
    "calculator_expressions": [
        "2 + 2",
        "10 * 5",
        "100 / 4",
        "15 - 7",
        "2 ** 3",
        "sqrt(16)"
    ],
    
    "search_queries": [
        "python programming",
        "machine learning",
        "FastAPI documentation"
    ],
    
    "file_operations": [
        ("list", "."),
        ("read", "README.md"),
        ("exists", "pyproject.toml")
    ]
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "concurrent_requests": 5,
    "max_response_time": 30.0,  # seconds
    "stress_test_duration": 60,  # seconds
    "memory_threshold": 500  # MB
}

# Test constants for better maintainability
TEST_CONSTANTS = {
    "max_response_time": 30.0,  # seconds
    "short_timeout": 15.0,  # seconds for quick operations
    "concurrent_request_count": 3,  # number of concurrent requests to test
    "rapid_fire_count": 10,  # number of rapid fire requests
    "memory_test_iterations": 5,  # iterations for memory stability tests
    "min_success_rate": 0.7,  # minimum success rate for concurrent tests
    "high_success_rate": 0.8,  # minimum success rate for stability tests
}

# Simplified validation helpers
VALIDATION_HELPERS = {
    "required_response_fields": ["response"],
    "optional_response_fields": ["metadata", "tool_calls", "tools_used"],
    "valid_status_codes": [200, 400, 413, 422, 500],  # API status codes
}

# Error message patterns for validation
ERROR_PATTERNS = {
    "config_validation": [
        "Invalid YAML format",
        "mapping values are not allowed",
        "Configuration validation failed",
        "Missing required field",
        "Invalid value"
    ],
    "api_errors": [
        "validation error",
        "field required",
        "invalid request"
    ],
    "agent_errors": [
        "Agent not initialized",
        "Configuration error",
        "Tool execution failed"
    ]
} 