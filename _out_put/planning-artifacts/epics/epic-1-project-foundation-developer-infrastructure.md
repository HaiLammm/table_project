# Epic 1: Project Foundation & Developer Infrastructure

Set up both frontend (Next.js 16 + shadcn/ui) and backend (FastAPI + Hexagonal/DDD) scaffolds, CI/CD pipeline, database provisioning, design system tokens, app shell layout, and Sprint 0 end-to-end validation.

## Story 1.1: Initialize Backend Scaffold with FastAPI & Hexagonal Structure

As a **developer**,
I want a fully configured FastAPI backend scaffold with hexagonal module structure, async SQLAlchemy, Alembic migrations, and dev tooling (Ruff, mypy, pytest),
So that all future feature development follows consistent architecture patterns from day one.

**Acceptance Criteria:**

**Given** the backend directory does not exist
**When** the developer runs the initialization commands
**Then** the project is created with uv, Python 3.12, all core dependencies installed (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, redis, arq)
**And** dev dependencies are installed (ruff, mypy, pytest, pytest-asyncio, pytest-mock, httpx, pre-commit)
**And** the hexagonal module structure exists for all 8 bounded contexts (auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard) with domain/application/infrastructure/api subdirectories
**And** Alembic is initialized with async template
**And** a health endpoint (`GET /api/v1/health`) returns 200 OK
**And** docker-compose.yml provides local PostgreSQL 16 and Redis
**And** pyproject.toml contains Ruff, mypy, and pytest configuration
**And** .pre-commit-config.yaml has Ruff + mypy hooks
**And** one Alembic migration can be created and applied successfully against the local Postgres
**And** one pytest test passes using an async SQLAlchemy session fixture

## Story 1.2: Initialize Frontend Scaffold with Next.js 16 & shadcn/ui

As a **developer**,
I want a fully configured Next.js 16 App Router frontend with shadcn/ui, Tailwind CSS v4, TypeScript strict mode, and the project file structure,
So that all frontend development starts from a consistent, accessible foundation.

**Acceptance Criteria:**

**Given** the frontend directory does not exist
**When** the developer runs create-next-app and shadcn/ui init
**Then** the project is created with TypeScript, Tailwind, ESLint, App Router, src directory
**And** shadcn/ui is initialized with the project theme configuration
**And** the zinc-based monochromatic design system CSS custom properties are configured in globals.css (--bg, --surface, --chrome-bg, --border, --text-primary, --text-secondary, --text-muted, --accent, etc.) per UX-DR1
**And** the multi-script font stack is configured (Inter Variable, Noto Sans JP Variable, JetBrains Mono) with unicode-range per UX-DR2
**And** responsive breakpoints are configured (mobile <640px, tablet 640-1024px, desktop >1024px) per UX-DR12
**And** the 3-tier button hierarchy is available (Primary/Secondary/Ghost) per UX-DR14
**And** Skeleton loading components are configured per UX-DR17
**And** the frontend directory structure matches Architecture spec (components/ui, components/review, components/layout, hooks, stores, lib, types)
**And** one page renders with a shadcn/ui component and design tokens applied
**And** ESLint and TypeScript compilation pass without errors

## Story 1.3: App Shell Layout (Sidebar, Topbar, Content Area)

As a **user**,
I want a consistent app navigation shell with dark sidebar, topbar with breadcrumb, and centered content area,
So that I can navigate between app sections efficiently on any device.

**Acceptance Criteria:**

**Given** a user is on any authenticated page
**When** the page loads
**Then** a dark sidebar (240px, zinc-900) displays 4 navigation items: Today's Queue, Collections, Dashboard, Settings per UX-DR11
**And** each nav item has an icon + label + optional badge (count)
**And** the active nav item is highlighted (bg-zinc-800 text-zinc-50)
**And** a topbar (56px) shows breadcrumb (current location) + ⌘K search trigger + user avatar
**And** the main content area is max-width 720px, centered horizontally
**And** on tablet (640-1024px), sidebar collapses to icon-only (56px) per UX-DR12
**And** on mobile (<640px), sidebar is hidden behind hamburger, slides in as overlay per UX-DR12
**And** all navigation items are keyboard accessible (Tab + Enter)
**And** sidebar has appropriate ARIA landmarks (`<nav>`)

## Story 1.4: CI/CD Pipeline & Deployment Configuration

As a **developer**,
I want automated CI/CD pipelines for both frontend and backend with linting, type checking, tests, and deployment,
So that code quality is enforced and deployments are automated from the main branch.

**Acceptance Criteria:**

**Given** code is pushed to the repository
**When** a GitHub Actions workflow triggers
**Then** backend pipeline runs: Ruff check → mypy → pytest (unit) → pytest (integration with Postgres service container) → Docker build
**And** frontend pipeline runs: ESLint → tsc --noEmit → vitest → next build
**And** backend Dockerfile uses multi-stage build (python:3.12-slim + uv)
**And** .env.example files exist for both frontend and backend with all required environment variables
**And** Railway deployment is configured for backend (API + ARQ worker as separate services)
**And** Vercel deployment is configured for frontend with auto-deploy from main
**And** Neon PostgreSQL database is provisioned
**And** Upstash Redis is provisioned
**And** all pipelines pass green on initial scaffold code
