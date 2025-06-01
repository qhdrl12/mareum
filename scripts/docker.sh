#!/bin/bash
# Simple Docker build and run script for ReAct Agent API

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration
IMAGE_NAME="react-agent-api"
CONTAINER_NAME="react-agent-api"
PORT="8000"
CONFIG_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        *)
            COMMAND="$1"
            shift
            ;;
    esac
done

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_info "Environment variables loaded from .env"
else
    print_warning ".env file not found. Using defaults."
fi

# Build Docker image
build_image() {
    print_info "Building Docker image: ${IMAGE_NAME}..."
    docker build -t ${IMAGE_NAME}:latest .
    print_success "Docker image built successfully"
}

# Run container
run_container() {
    # Set config file parameter
    local docker_cmd="python scripts/run_api_server.py --host 0.0.0.0 --port 8000"
    if [ -n "${CONFIG_FILE}" ]; then
        docker_cmd="${docker_cmd} --config ${CONFIG_FILE}"
        print_info "Using config file: ${CONFIG_FILE}"
    else
        print_warning "No config file specified, using default from container"
    fi
    
    print_info "Running container: ${CONTAINER_NAME}..."
    print_info "Docker command: ${docker_cmd}"
    
    # Stop and remove existing container if exists
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
        print_info "Stopping existing container..."
        docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
        docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
    fi
    
    # Run new container
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8000 \
        --env-file .env \
        --restart unless-stopped \
        ${IMAGE_NAME}:latest \
        ${docker_cmd}
    
    print_success "Container started successfully"
    print_info "API available at: http://localhost:${PORT}"
}

# Check container health
health_check() {
    print_info "Checking container health..."
    
    for i in {1..12}; do
        if curl -f http://localhost:${PORT}/health >/dev/null 2>&1; then
            print_success "Service is healthy!"
            return 0
        fi
        print_info "Waiting for service to start... (${i}/12)"
        sleep 5
    done
    
    print_error "Health check failed"
    return 1
}

# Show logs
show_logs() {
    print_info "Showing container logs..."
    docker logs -f ${CONTAINER_NAME}
}

# Stop container
stop_container() {
    print_info "Stopping container..."
    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
    print_success "Container stopped"
}

# Container status
status() {
    print_info "Container status:"
    docker ps -a | grep ${CONTAINER_NAME} || echo "Container not found"
    
    echo ""
    print_info "Available endpoints:"
    echo "  - Health: http://localhost:${PORT}/health"
    echo "  - API Docs: http://localhost:${PORT}/docs"
    echo "  - Chat API: http://localhost:${PORT}/chat"
}

# Clean up
cleanup() {
    print_warning "Removing container and image..."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
        docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
        docker rmi ${IMAGE_NAME}:latest >/dev/null 2>&1 || true
        print_success "Cleanup completed"
    fi
}

# Quick deploy (build + run + health check)
deploy() {
    build_image
    run_container
    health_check
    status
}

# Show help
show_help() {
    echo "🐳 ReAct Agent API - Simple Docker Management"
    echo ""
    echo "Usage: $0 [command] [--config CONFIG_FILE]"
    echo ""
    echo "Options:"
    echo "  --config FILE    Agent config file path (e.g., examples/configs/openai_compatible.yaml)"
    echo ""
    echo "Commands:"
    echo "  build     - Build Docker image"
    echo "  run       - Run container"
    echo "  stop      - Stop container"
    echo "  restart   - Restart container (stop + run)"
    echo "  logs      - Show container logs"
    echo "  status    - Show container status"
    echo "  health    - Check service health"
    echo "  cleanup   - Remove container and image"
    echo "  deploy    - Full deployment (build + run + health check)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 deploy --config examples/configs/openai_compatible.yaml"
    echo "  $0 run --config examples/configs/openai_compatible.yaml"
    echo "  $0 restart --config examples/configs/openai_compatible.yaml"
}

# Main command handling
case "${COMMAND:-$1}" in
    "build")
        build_image
        ;;
    "run")
        run_container
        ;;
    "stop")
        stop_container
        ;;
    "restart")
        stop_container
        run_container
        ;;
    "logs")
        show_logs
        ;;
    "status")
        status
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "deploy")
        deploy
        ;;
    *)
        show_help
        exit 1
        ;;
esac
