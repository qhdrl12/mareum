#!/usr/bin/env python3
"""
Simple test script for schema validation system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.schema_validator import SchemaValidator
from src.utils.config_loader import ConfigLoader


def test_example_config():
    """Test the example configuration file."""
    print("🧪 Testing example configuration file...")
    
    # Test validation
    result = SchemaValidator.validate_file("examples/example_agent.yaml")
    print(f"Validation result: {result}")
    
    if result.is_valid:
        print("✅ Example configuration is valid!")
        if result.warnings:
            print("\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
    else:
        print("❌ Example configuration is invalid!")
        print("\n🔴 Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    return result.is_valid


def test_config_loading():
    """Test configuration loading."""
    print("\n🧪 Testing configuration loading...")
    
    try:
        # Set test environment variables
        import os
        os.environ['KB_API_TOKEN'] = 'test_kb_token'
        os.environ['TICKET_API_TOKEN'] = 'test_ticket_token'
        os.environ['OPENAI_API_KEY'] = 'test_openai_key'
        
        config = ConfigLoader.load_config("examples/example_agent.yaml")
        print("✅ Configuration loaded successfully!")
        print(f"Agent name: {config.metadata.name}")
        print(f"Model: {config.model.provider.value}/{config.model.name}")
        print(f"Tools: {len(config.tools)} tools configured")
        
        # Clean up test environment variables
        del os.environ['KB_API_TOKEN']
        del os.environ['TICKET_API_TOKEN']
        del os.environ['OPENAI_API_KEY']
        
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def test_json_schema_generation():
    """Test JSON schema generation."""
    print("\n🧪 Testing JSON schema generation...")
    
    try:
        schema = SchemaValidator.get_json_schema()
        print("✅ JSON schema generated successfully!")
        print(f"Schema has {len(schema.get('properties', {}))} top-level properties")
        
        # Save schema to file
        SchemaValidator.save_json_schema("schema.json")
        print("✅ Schema saved to schema.json")
        return True
    except Exception as e:
        print(f"❌ JSON schema generation failed: {e}")
        return False


def test_default_config():
    """Test default configuration creation."""
    print("\n🧪 Testing default configuration creation...")
    
    try:
        ConfigLoader.create_example_config("examples/default_agent.yaml")
        print("✅ Default configuration created!")
        
        # Validate the created config
        result = SchemaValidator.validate_file("examples/default_agent.yaml")
        if result.is_valid:
            print("✅ Default configuration is valid!")
        else:
            print("❌ Default configuration is invalid!")
            for error in result.errors:
                print(f"  - {error}")
        
        return result.is_valid
    except Exception as e:
        print(f"❌ Default configuration creation failed: {e}")
        return False


def test_vllm_config():
    """Test vLLM configuration file."""
    print("\n🧪 Testing vLLM configuration file...")
    
    try:
        # Set test environment variables for vLLM
        import os
        os.environ['VLLM_API_KEY'] = 'test_vllm_key'
        
        result = SchemaValidator.validate_file("examples/vllm_agent.yaml")
        if result.is_valid:
            print("✅ vLLM configuration is valid!")
            config = ConfigLoader.load_config("examples/vllm_agent.yaml")
            print(f"Provider: {config.model.provider.value}")
            print(f"Base URL: {config.model.base_url}")
        else:
            print("❌ vLLM configuration is invalid!")
            for error in result.errors:
                print(f"  - {error}")
        
        # Clean up
        del os.environ['VLLM_API_KEY']
        return result.is_valid
    except Exception as e:
        print(f"❌ vLLM configuration test failed: {e}")
        return False


def test_bedrock_config():
    """Test AWS Bedrock configuration file."""
    print("\n🧪 Testing AWS Bedrock configuration file...")
    
    try:
        # Set test environment variables for Bedrock
        import os
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_aws_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_aws_secret'
        os.environ['LAMBDA_FUNCTION_NAME'] = 'test_function'
        os.environ['AWS_SIGNATURE'] = 'test_signature'
        os.environ['MILVUS_TOKEN'] = 'test_milvus_token'
        
        result = SchemaValidator.validate_file("examples/bedrock_agent.yaml")
        if result.is_valid:
            print("✅ Bedrock configuration is valid!")
            config = ConfigLoader.load_config("examples/bedrock_agent.yaml")
            print(f"Provider: {config.model.provider.value}")
            print(f"Region: {config.model.region}")
            print(f"Model: {config.model.name}")
        else:
            print("❌ Bedrock configuration is invalid!")
            for error in result.errors:
                print(f"  - {error}")
        
        # Clean up
        del os.environ['AWS_ACCESS_KEY_ID']
        del os.environ['AWS_SECRET_ACCESS_KEY']
        del os.environ['LAMBDA_FUNCTION_NAME']
        del os.environ['AWS_SIGNATURE']
        del os.environ['MILVUS_TOKEN']
        return result.is_valid
    except Exception as e:
        print(f"❌ Bedrock configuration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting schema validation system tests...\n")
    
    tests = [
        test_example_config,
        test_config_loading,
        test_json_schema_generation,
        test_default_config,
        test_vllm_config,
        test_bedrock_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 50)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Schema validation system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 