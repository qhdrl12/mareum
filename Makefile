# LangGraph Test Project Makefile

.PHONY: help install test lint format clean

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

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