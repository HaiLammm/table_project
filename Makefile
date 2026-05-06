.PHONY: help install dev dev-backend dev-frontend db-up db-down db-migrate db-downgrade db-revision lint lint-backend lint-frontend test test-backend test-frontend test-unit test-integration build seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ──────────────────────────────────────────────
# Installation
# ──────────────────────────────────────────────

install: ## Install all dependencies (backend + frontend)
	cd backend && uv sync
	cd frontend && pnpm install

# ──────────────────────────────────────────────
# Infrastructure
# ──────────────────────────────────────────────

db-up: ## Start Postgres + Redis containers
	cd backend && docker compose up -d

db-down: ## Stop Postgres + Redis containers
	cd backend && docker compose down

db-migrate: ## Run Alembic migrations to head
	cd backend && uv run alembic upgrade head

db-downgrade: ## Downgrade one Alembic migration
	cd backend && uv run alembic downgrade -1

db-revision: ## Create new Alembic migration (usage: make db-revision MSG="add foo table")
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

# ──────────────────────────────────────────────
# Development servers
# ──────────────────────────────────────────────

dev: ## Start backend + frontend in parallel
	$(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend: ## Start FastAPI dev server (port 8000)
	cd backend && uv run uvicorn src.app.main:app --reload --port 8000

dev-frontend: ## Start Next.js dev server (port 3000)
	cd frontend && pnpm dev

# ──────────────────────────────────────────────
# Linting & Type checking
# ──────────────────────────────────────────────

lint: lint-backend lint-frontend ## Lint everything

lint-backend: ## Ruff check + mypy
	cd backend && uv run ruff check src tests scripts
	cd backend && uv run ruff format --check src tests scripts
	cd backend && uv run mypy

lint-frontend: ## ESLint + TypeScript check
	cd frontend && pnpm lint
	cd frontend && pnpm tsc --noEmit

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend: ## Run all backend tests
	cd backend && uv run pytest

test-unit: ## Run backend unit tests only
	cd backend && uv run pytest tests/unit

test-integration: ## Run backend integration tests only
	cd backend && uv run pytest tests/integration

test-frontend: ## Run frontend tests
	cd frontend && pnpm test

# ──────────────────────────────────────────────
# Build
# ──────────────────────────────────────────────

build: ## Build frontend for production
	cd frontend && pnpm build

# ──────────────────────────────────────────────
# Data
# ──────────────────────────────────────────────

seed: ## Seed vocabulary corpus
	cd backend && uv run python -m scripts.seed_corpus
