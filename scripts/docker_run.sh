#!/bin/bash

# Docker Run Script for LangGraph Agent
# This script builds and runs the container using only Dockerfile

set -e

# Default values
IMAGE_NAME="langgraph-agent"
TAG="latest"
CONTAINER_NAME="langgraph-agent-container"
CONFIG_PATH="examples/configs/example_agent.yaml"
HOST_PORT="8000"
CONTAINER_PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config PATH      Path to agent configuration YAML file (default: examples/configs/example_agent.yaml)"
    echo "  -p, --port PORT        Host port to bind to (default: 8000)"
    echo "  -n, --name NAME        Container name (default: langgraph-agent-container)"
    echo "  -t, --tag TAG          Image tag (default: latest)"
    echo "  --build-only           Only build the image, don't run container"
    echo "  --stop                 Stop and remove existing container"
    echo "  --logs                 Show container logs"
    echo "  --shell                Open shell in running container"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                              # Build and run with defaults"
    echo "  $0 --config my_agent.yaml --port 8080          # Custom config and port"
    echo "  $0 --build-only                                # Only build image"
    echo "  $0 --stop                                       # Stop container"
    echo "  $0 --logs                                       # Show logs"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -p|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --stop)
            STOP_CONTAINER=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --shell)
            OPEN_SHELL=true
            shift
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
if [[ ! -f "Dockerfile" ]]; then
    echo -e "${RED}Error: Dockerfile not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

# Stop container if requested
if [[ "$STOP_CONTAINER" == true ]]; then
    echo -e "${YELLOW}Stopping and removing container: $CONTAINER_NAME${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}Container stopped and removed.${NC}"
    exit 0
fi

# Show logs if requested
if [[ "$SHOW_LOGS" == true ]]; then
    echo -e "${BLUE}Showing logs for container: $CONTAINER_NAME${NC}"
    docker logs -f "$CONTAINER_NAME"
    exit 0
fi

# Open shell if requested
if [[ "$OPEN_SHELL" == true ]]; then
    echo -e "${BLUE}Opening shell in container: $CONTAINER_NAME${NC}"
    docker exec -it "$CONTAINER_NAME" /bin/bash
    exit 0
fi

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p data logs

# Build Docker image
echo -e "${GREEN}Building Docker image: $IMAGE_NAME:$TAG${NC}"
docker build -t "$IMAGE_NAME:$TAG" .

if [[ "$BUILD_ONLY" == true ]]; then
    echo -e "${GREEN}Image built successfully: $IMAGE_NAME:$TAG${NC}"
    exit 0
fi

# Validate config file
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo -e "${RED}Error: Configuration file not found: $CONFIG_PATH${NC}"
    exit 1
fi

# Stop existing container if running
echo -e "${YELLOW}Stopping existing container if running...${NC}"
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Run container
echo -e "${GREEN}Starting container: $CONTAINER_NAME${NC}"
echo "Image: $IMAGE_NAME:$TAG"
echo "Config: $CONFIG_PATH"
echo "Port: $HOST_PORT -> $CONTAINER_PORT"
echo ""

# Check if .env file exists for environment variables
ENV_FILE_ARGS=""
if [[ -f ".env" ]]; then
    ENV_FILE_ARGS="--env-file .env"
    echo -e "${BLUE}Using .env file for environment variables${NC}"
fi

# Run the container
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$HOST_PORT:$CONTAINER_PORT" \
    $ENV_FILE_ARGS \
    -v "$(pwd)/$CONFIG_PATH:/app/config.yaml:ro" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    "$IMAGE_NAME:$TAG" \
    python main.py --config /app/config.yaml --host 0.0.0.0 --port $CONTAINER_PORT

echo -e "${GREEN}Container started successfully!${NC}"
echo ""
echo "🌐 Access the API at: http://localhost:$HOST_PORT"
echo "📖 API Documentation: http://localhost:$HOST_PORT/docs"
echo "💚 Health Check: http://localhost:$HOST_PORT/health"
echo ""
echo "📋 Useful commands:"
echo "  View logs:    $0 --logs"
echo "  Stop:         $0 --stop"
echo "  Shell access: $0 --shell"
echo ""
echo "Check container status:"
echo "  docker ps"
echo "  docker logs $CONTAINER_NAME" 