#!/bin/bash
# Local Model Setup Script for OpenAI Compatible Testing

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

print_info "Setting up local model for OpenAI compatible testing..."

# Function to setup Ollama
setup_ollama() {
    print_info "Setting up Ollama..."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama not found. Installing..."
        
        # Install Ollama (Mac/Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install ollama
        else
            # Linux
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    else
        print_success "Ollama already installed"
    fi
    
    # Start Ollama service (if not running)
    print_info "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
    
    # Pull a small model
    print_info "Pulling small model (phi3:mini - ~2.2GB)..."
    ollama pull phi3:mini
    
    print_success "Ollama setup complete!"
    print_info "Model available at: http://localhost:11434/v1"
    print_info "Test with: curl http://localhost:11434/v1/models"
    
    return $OLLAMA_PID
}

# Function to test model
test_model() {
    local base_url=$1
    print_info "Testing model at $base_url..."
    
    # Test models endpoint
    curl -s "$base_url/models" | jq . || echo "Models endpoint test failed"
    
    # Test completion
    curl -s "$base_url/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "phi3:mini",
            "messages": [{"role": "user", "content": "Hello, respond with just OK"}],
            "max_tokens": 10
        }' | jq . || echo "Completion test failed"
}

# Function to update config file
update_config() {
    local config_file="examples/configs/openai_comaptible.yaml"
    print_info "Updating config file: $config_file"
    
    # Backup original
    cp "$config_file" "$config_file.backup"
    
    # Update config for local testing
    cat > "$config_file" << EOF
metadata:
  name: "local-test-agent"
  description: "Local testing agent using Ollama"

model:
  provider: "openai_compatible"
  name: "phi3:mini"
  api_key: "not-needed"
  base_url: "http://localhost:11434/v1"
  timeout: 30000
  max_retries: 3
  parameters:
    temperature: 0.7
    max_tokens: 1000

prompt:
  system_prompt: "You are a helpful AI assistant for testing purposes. Keep responses concise."

tools:
  - name: "search_knowledge_base"
    type: "function"
    description: "Search the knowledge base for information"
    parameters:
      - name: "query"
        type: "string"
        description: "Search query"
        required: true

memory:
  type: "simple_buffer"
  config:
    k: 5

knowledge:
  provider: "faiss"
  collection_name: "test-knowledge"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
EOF
    
    print_success "Config updated for local testing"
}

# Function to restore config
restore_config() {
    local config_file="examples/configs/openai_comaptible.yaml"
    if [ -f "$config_file.backup" ]; then
        mv "$config_file.backup" "$config_file"
        print_success "Config restored from backup"
    fi
}

# Main execution
case "${1:-setup}" in
    "setup")
        setup_ollama
        update_config
        print_success "Setup complete! Ready for testing."
        print_info "Run tests with: python tests/test_react_agent.py"
        ;;
    "test")
        test_model "http://localhost:11434/v1"
        ;;
    "restore")
        restore_config
        ;;
    "cleanup")
        restore_config
        pkill -f ollama || true
        print_success "Cleanup complete"
        ;;
    *)
        echo "Usage: $0 {setup|test|restore|cleanup}"
        echo "  setup   - Install and configure local model"
        echo "  test    - Test model endpoints"
        echo "  restore - Restore original config"
        echo "  cleanup - Stop services and restore config"
        ;;
esac 