# LangGraph Test Project Makefile

.PHONY: help install test lint format clean
.PHONY: docker-build docker-run docker-stop docker-logs docker-status docker-health docker-cleanup docker-deploy
.PHONY: compose-up compose-down compose-build compose-logs compose-status compose-restart
.PHONY: docker-shell compose-shell

# Configuration
CONFIG_DIR := examples/configs
DEFAULT_CONFIG := $(CONFIG_DIR)/openai_compatible.yaml
MCP_CONFIG := $(CONFIG_DIR)/mcp_agent.yaml
MCP_COMPOSE_CONFIG := $(CONFIG_DIR)/mcp_agent.yaml

# Default target
help: ## Show this help message
	@echo "🚀 LangGraph Test Project - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "📦 Development Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(install|test|lint|format|clean|dev)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🐳 Docker Commands (scripts/docker.sh):"
	@grep -E '^docker-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[34m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🐙 Docker Compose Commands:"
	@grep -E '^compose-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[35m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Quick Start Examples:"
	@echo "  make docker-deploy                    # Deploy with default config"
	@echo "  make docker-deploy CONFIG=mcp_agent.yaml # Deploy with MCP tools"
	@echo "  make compose-up                       # Start with Docker Compose + MCP"
	@echo "  make compose-logs                     # View compose logs"

# Development Commands
install: ## Install dependencies
	pip install -e .[dev]

test: ## Run all tests
	python -m pytest tests/ -v

test-fast: ## Run tests excluding slow ones
	python -m pytest tests/ -v -m "not slow"

lint: ## Run linting
	python -m black --check src/ tests/
	python -m isort --check-only src/ tests/
	python -m mypy src/

format: ## Format code
	python -m black src/ tests/
	python -m isort src/ tests/

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

ci: lint test ## Run continuous integration checks (lint + test)

dev-setup: install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to verify everything works"

# Docker Commands (using scripts/docker.sh)
docker-build: ## Build Docker image using docker.sh
	@echo "🏗️ Building Docker image..."
	@./scripts/docker.sh build

docker-run: ## Run container using docker.sh (use CONFIG=file.yaml to specify config)
	@echo "🚀 Running container..."
	@if [ -n "$(CONFIG)" ]; then \
		echo "Using config: $(CONFIG_DIR)/$(CONFIG)"; \
		./scripts/docker.sh run --config $(CONFIG_DIR)/$(CONFIG); \
	else \
		echo "Using default config"; \
		./scripts/docker.sh run; \
	fi

docker-stop: ## Stop container using docker.sh
	@echo "🛑 Stopping container..."
	@./scripts/docker.sh stop

docker-restart: ## Restart container using docker.sh (use CONFIG=file.yaml to specify config)
	@echo "🔄 Restarting container..."
	@if [ -n "$(CONFIG)" ]; then \
		echo "Using config: $(CONFIG_DIR)/$(CONFIG)"; \
		./scripts/docker.sh restart --config $(CONFIG_DIR)/$(CONFIG); \
	else \
		echo "Using default config"; \
		./scripts/docker.sh restart; \
	fi

docker-logs: ## Show container logs using docker.sh
	@echo "📋 Showing container logs..."
	@./scripts/docker.sh logs

docker-status: ## Show container status using docker.sh
	@echo "📊 Container status:"
	@./scripts/docker.sh status

docker-health: ## Check container health using docker.sh
	@echo "🏥 Checking container health..."
	@./scripts/docker.sh health

docker-cleanup: ## Remove container and image using docker.sh
	@echo "🧹 Cleaning up Docker resources..."
	@./scripts/docker.sh cleanup

docker-deploy: ## Full deployment using docker.sh (build + run + health check)
	@echo "🚀 Full deployment..."
	@if [ -n "$(CONFIG)" ]; then \
		echo "Using config: $(CONFIG_DIR)/$(CONFIG)"; \
		./scripts/docker.sh deploy --config $(CONFIG_DIR)/$(CONFIG); \
	else \
		echo "Using default config"; \
		./scripts/docker.sh deploy; \
	fi

docker-deploy-mcp: ## Deploy with MCP agent configuration
	@echo "🚀 Deploying with MCP agent..."
	@./scripts/docker.sh deploy --config $(MCP_CONFIG)

docker-shell: ## Get shell access to running container
	@echo "🐚 Accessing container shell..."
	@docker exec -it react-agent-api /bin/bash

# Docker Compose Commands
compose-up: ## Start services with docker-compose (includes MCP server)
	@echo "🐙 Starting services with Docker Compose..."
	@docker-compose up -d
	@echo "✅ Services started. API: http://localhost:8000, MCP: http://localhost:3001"

compose-down: ## Stop and remove services with docker-compose
	@echo "🛑 Stopping Docker Compose services..."
	@docker-compose down

compose-build: ## Build services with docker-compose
	@echo "🏗️ Building Docker Compose services..."
	@docker-compose build

compose-rebuild: ## Rebuild and restart services
	@echo "🔨 Rebuilding and restarting services..."
	@docker-compose down
	@docker-compose build --no-cache
	@docker-compose up -d

compose-logs: ## Show logs from all compose services
	@echo "📋 Showing Docker Compose logs..."
	@docker-compose logs -f

compose-logs-api: ## Show logs from API server only
	@echo "📋 Showing API server logs..."
	@docker-compose logs -f api-server

compose-logs-mcp: ## Show logs from MCP server only
	@echo "📋 Showing MCP server logs..."
	@docker-compose logs -f mcp-server

compose-status: ## Show status of compose services
	@echo "📊 Docker Compose services status:"
	@docker-compose ps

compose-restart: ## Restart compose services
	@echo "🔄 Restarting Docker Compose services..."
	@docker-compose restart

compose-shell: ## Get shell access to API server container
	@echo "🐚 Accessing API server container shell..."
	@docker-compose exec api-server /bin/bash

compose-shell-mcp: ## Get shell access to MCP server container
	@echo "🐚 Accessing MCP server container shell..."
	@docker-compose exec mcp-server /bin/bash

# Utility Commands
check-env: ## Check if .env file exists and show status
	@echo "🔍 Checking environment setup..."
	@if [ -f .env ]; then \
		echo "✅ .env file found"; \
		echo "🔑 Environment variables:"; \
		grep -E '^[A-Z_]+=.+' .env | sed 's/=.*/=***/' || true; \
	else \
		echo "❌ .env file not found"; \
		echo "💡 Create .env file with required variables (see README.md)"; \
	fi

list-configs: ## List available configuration files
	@echo "📁 Available configuration files:"
	@ls -la $(CONFIG_DIR)/*.yaml | awk '{print "  " $$9}' | sed 's|$(CONFIG_DIR)/||'

# Quick deployment shortcuts
quick-start: check-env compose-up ## Quick start with compose (check env + start services)

quick-deploy: check-env docker-deploy ## Quick deploy with docker.sh (check env + deploy)

quick-mcp: check-env docker-deploy-mcp ## Quick deploy with MCP configuration 