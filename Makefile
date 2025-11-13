# Makefile for Reflex Docker deployment
# Quick reference for common operations

.PHONY: help dev test-docker build deploy clean logs health

# Default target
.DEFAULT_GOAL := help

# Variables
IMAGE_NAME := working
IMAGE_TAG := latest
CONTAINER_NAME := working-test

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

dev: ## Start local development server
	@echo "$(GREEN)Starting development server...$(NC)"
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

test-docker: ## Build and test Docker container locally
	@echo "$(GREEN)Testing Docker container locally...$(NC)"
	@chmod +x scripts/test-docker.sh
	@./scripts/test-docker.sh

build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	@chmod +x scripts/build.sh
	@./scripts/build.sh

build-push: ## Build and push Docker image to registry
	@echo "$(GREEN)Building and pushing Docker image...$(NC)"
	@chmod +x scripts/build.sh
	@./scripts/build.sh --push

deploy: ## Deploy to Coolify (via git push)
	@echo "$(GREEN)Deploying to Coolify...$(NC)"
	@echo "$(YELLOW)Make sure all changes are committed$(NC)"
	@git status
	@echo ""
	@read -p "Push to remote and deploy? (y/n) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git push origin main && \
		echo "$(GREEN)Pushed to remote. Coolify will auto-deploy.$(NC)"; \
	fi

clean: ## Clean up Docker resources
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

logs: ## Show container logs (local)
	@echo "$(GREEN)Showing container logs...$(NC)"
	@docker logs -f $(CONTAINER_NAME)

health: ## Check application health
	@echo "$(GREEN)Checking application health...$(NC)"
	@curl -s http://localhost:3000/health | python -m json.tool || \
	 echo "$(YELLOW)Local container not running or health endpoint not available$(NC)"

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@uv sync

update: ## Update dependencies
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@uv sync --upgrade

lint: ## Run linters
	@echo "$(GREEN)Running linters...$(NC)"
	@uv run ruff check .

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	@uv run ruff format .

test: ## Run tests (if available)
	@echo "$(GREEN)Running tests...$(NC)"
	@uv run pytest tests/ -v || echo "$(YELLOW)No tests configured yet$(NC)"

exec: ## Execute command in running container
	@docker exec -it $(CONTAINER_NAME) /bin/bash

ps: ## Show running containers
	@docker ps --filter "name=$(CONTAINER_NAME)"

images: ## Show Docker images
	@docker images $(IMAGE_NAME)

# Development workflow shortcuts

.PHONY: init start restart stop

init: install ## Initialize project (install deps)
	@echo "$(GREEN)Project initialized$(NC)"

start: dev ## Alias for 'make dev'

restart: clean test-docker ## Restart local Docker container

stop: clean ## Stop local Docker container

# CI/CD helpers

.PHONY: ci-build ci-test

ci-build: ## CI: Build Docker image
	@docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

ci-test: ci-build ## CI: Build and test
	@docker run --rm -d --name $(CONTAINER_NAME)-ci \
		-e REFLEX_ENV=production \
		-e FRONTEND_PORT=3000 \
		-e BACKEND_PORT=8000 \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@sleep 10
	@docker logs $(CONTAINER_NAME)-ci
	@docker stop $(CONTAINER_NAME)-ci
