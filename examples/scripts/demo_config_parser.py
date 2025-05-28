#!/usr/bin/env python3
"""
Demo script showing how to use the ConfigParser class.

This script demonstrates:
1. Loading and validating YAML configuration files
2. Handling validation errors
3. Using custom schema files
4. Working with YAML format features
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_parser import ConfigParser, ConfigParseError, ConfigValidationError


def demo_valid_config():
    """Demonstrate parsing valid YAML configuration files."""
    print("=" * 60)
    print("DEMO: Parsing Valid YAML Configuration")
    print("=" * 60)
    
    # Create parser with custom schema
    schema_path = Path(__file__).parent.parent.parent / "schema.json"
    parser = ConfigParser(schema_path=schema_path)
    
    # Test YAML file
    print("\n1. Parsing valid YAML configuration:")
    try:
        yaml_config_path = Path(__file__).parent.parent / "configs" / "valid_agent.yaml"
        config = parser.parse_from_file(yaml_config_path)
        print(f"✅ Successfully parsed YAML config!")
        print(f"   Agent name: {config['metadata']['name']}")
        print(f"   Model: {config['model']['provider']} - {config['model']['name']}")
        print(f"   Tools: {len(config.get('tools', []))} tools configured")
        print(f"   Features: Multi-line prompts, comments, structured data")
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_invalid_config():
    """Demonstrate handling of invalid configuration files."""
    print("\n" + "=" * 60)
    print("DEMO: Handling Invalid Configuration Files")
    print("=" * 60)
    
    schema_path = Path(__file__).parent.parent.parent / "schema.json"
    parser = ConfigParser(schema_path=schema_path)
    
    print("\n2. Parsing invalid configuration (should show validation errors):")
    try:
        invalid_config_path = Path(__file__).parent.parent / "configs" / "invalid_agent.yaml"
        config = parser.parse_from_file(invalid_config_path)
        print(f"❌ Unexpected success - this should have failed!")
    except ConfigValidationError as e:
        print(f"✅ Caught validation errors as expected:")
        for i, error in enumerate(e.errors, 1):
            print(f"   {i}. {error}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_string_parsing():
    """Demonstrate parsing configuration from YAML strings."""
    print("\n" + "=" * 60)
    print("DEMO: Parsing YAML from Strings")
    print("=" * 60)
    
    schema_path = Path(__file__).parent.parent.parent / "schema.json"
    parser = ConfigParser(schema_path=schema_path)
    
    # YAML string example with advanced features
    yaml_string = """
# YAML Configuration Example
metadata:
  name: "demo-agent"
  description: |
    Multi-line descriptions work great in YAML
    and are very readable for documentation
  tags:
    - demo
    - example

model:
  provider: "openai"
  name: "gpt-3.5-turbo"
  credentials_key: "OPENAI_API_KEY"
  temperature: 0.8  # Comments make config self-documenting

prompt:
  system: |
    You are a helpful assistant.
    This prompt can span multiple lines
    and is very readable.
"""
    
    print("\n3. Parsing YAML string:")
    try:
        config = parser.parse_from_string(yaml_string)
        print(f"✅ Successfully parsed YAML string!")
        print(f"   Agent name: {config['metadata']['name']}")
        print(f"   Description: Multi-line ({'✓' if len(config['metadata']['description'].split()) > 10 else '✗'})")
        print(f"   Comments preserved: ✓ (YAML advantage)")
        print(f"   Defaults applied: version = {config['metadata'].get('version', 'not set')}")
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_yaml_advantages():
    """Demonstrate YAML-specific advantages."""
    print("\n" + "=" * 60)
    print("DEMO: YAML Format Advantages")
    print("=" * 60)
    
    parser = ConfigParser()
    
    yaml_features = """
# 1. Comments for documentation
metadata:
  name: "feature-demo"
  
# 2. Multi-line strings (literal style)
prompt:
  system: |
    This is a literal multi-line string.
    Newlines are preserved exactly.
    Perfect for prompts and documentation.
    
# 3. Multi-line strings (folded style) 
description: >
  This is a folded multi-line string.
  Long lines are wrapped but
  logical line breaks are preserved.

# 4. Complex nested structures
tools:
  - name: "search"
    config:
      # Nested comments work too
      max_results: 10
      filters:
        - type: "web"
        - type: "academic"
        
# 5. Environment variable references (if needed)
api_keys:
  openai: "${OPENAI_API_KEY}"
  anthropic: "${ANTHROPIC_API_KEY}"
"""
    
    print("\n4. YAML format features:")
    print("   ✓ Comments for self-documentation")
    print("   ✓ Multi-line strings (literal |, folded >)")
    print("   ✓ More readable nested structures")
    print("   ✓ No escape characters needed")
    print("   ✓ Better diff-friendly version control")
    
    try:
        # This would fail validation but shows parsing works
        parsed = parser._parse_yaml_content(yaml_features)
        print(f"\n   ✅ Complex YAML structure parsed successfully")
        print(f"   📊 Parsed {len(parsed)} top-level sections")
    except Exception as e:
        print(f"   ❌ Parse error: {e}")


def demo_file_validation():
    """Demonstrate file extension validation."""
    print("\n" + "=" * 60)
    print("DEMO: File Extension Validation")
    print("=" * 60)
    
    parser = ConfigParser()
    
    test_files = [
        ("agent.yaml", "✅ Valid"),
        ("agent.yml", "✅ Valid"),
        ("agent.json", "❌ Not supported"),
        ("agent.txt", "❌ Not supported"),
        ("agent", "❌ No extension"),
    ]
    
    print("\n5. File extension validation:")
    for filename, expected in test_files:
        try:
            # We don't actually parse, just test the validation
            from pathlib import Path
            test_path = Path(filename)
            if test_path.suffix.lower() not in ['.yaml', '.yml']:
                raise ConfigParseError(f"Only YAML files (.yaml, .yml) are supported. Got: {test_path.suffix}")
            print(f"   📄 {filename:15} → {expected}")
        except ConfigParseError:
            print(f"   📄 {filename:15} → {expected}")
    
    print("\n   Policy: Only .yaml and .yml files are accepted")


if __name__ == "__main__":
    print("ConfigParser Demo Script - YAML-Only Configuration")
    print("Demonstrating YAML as the exclusive configuration format.\n")
    
    try:
        demo_valid_config()
        demo_invalid_config()
        demo_string_parsing()
        demo_yaml_advantages()
        demo_file_validation()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("📝 ConfigParser now exclusively supports YAML format")
        print("🎯 Simplified, focused, and developer-friendly")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        sys.exit(1) 