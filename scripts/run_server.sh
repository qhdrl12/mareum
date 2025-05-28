#!/bin/bash

# LangGraph Agent Server Runner
# This script helps you run the server with different configurations

set -e

# Default values
CONFIG_PATH=""
HOST="0.0.0.0"
PORT="8000"
RELOAD=false
LOG_LEVEL="info"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config PATH      Path to agent configuration YAML file"
    echo "  -h, --host HOST        Host to bind server to (default: 0.0.0.0)"
    echo "  -p, --port PORT        Port to bind server to (default: 8000)"
    echo "  -r, --reload           Enable auto-reload for development"
    echo "  -l, --log-level LEVEL  Set log level (debug|info|warning|error, default: info)"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --config examples/configs/example_agent.yaml"
    echo "  $0 --config examples/configs/example_agent.yaml --reload --log-level debug"
    echo "  $0 --port 8080 --host localhost"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -r|--reload)
            RELOAD=true
            shift
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if we're in the project root
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}Error: main.py not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" && ! -f ".venv/bin/activate" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected. Consider using a virtual environment.${NC}"
fi

# Validate config file if provided
if [[ -n "$CONFIG_PATH" ]]; then
    if [[ ! -f "$CONFIG_PATH" ]]; then
        echo -e "${RED}Error: Configuration file not found: $CONFIG_PATH${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using configuration: $CONFIG_PATH${NC}"
fi

# Build command
CMD="python main.py --host $HOST --port $PORT --log-level $LOG_LEVEL"

if [[ -n "$CONFIG_PATH" ]]; then
    CMD="$CMD --config $CONFIG_PATH"
fi

if [[ "$RELOAD" == true ]]; then
    CMD="$CMD --reload"
    echo -e "${YELLOW}Development mode: auto-reload enabled${NC}"
fi

# Print startup information
echo -e "${GREEN}Starting LangGraph Agent Server...${NC}"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log Level: $LOG_LEVEL"
echo "Command: $CMD"
echo ""

# Run the server
exec $CMD 