.PHONY: help install run run-api shell test up down docker-logs clean

# Variables
PYTHON := poetry run python
BMO := poetry run bmo
API := poetry run uvicorn src.BMO.api.app:app

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using Poetry
	poetry install

run: ## Run BMO Assistant CLI
	$(BMO)

run-api: ## Run BMO API Server (FastAPI)
	$(API) --reload

shell: ## Open BMO in interactive shell (CLI session)
	$(BMO) --session interactive-shell

test: ## Run all tests
	poetry run pytest tests/

persistence-test: ## Run specific persistence test
	PYTHONPATH=src poetry run python tests/test_persistence.py

up: ## Build and start production environment (Docker Compose)
	docker compose up -d --build

down: ## Stop production environment
	docker compose down

logs: ## View Docker logs
	docker compose logs -f bmo

clean: ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
	@echo "✨ Workspace cleaned!"
