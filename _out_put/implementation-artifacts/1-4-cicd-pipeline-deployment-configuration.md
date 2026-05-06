# Story 1.4: CI/CD Pipeline & Deployment Configuration

Status: ready-for-dev

## Story

As a **developer**,
I want automated CI/CD pipelines for both frontend and backend with linting, type checking, tests, and deployment,
so that code quality is enforced and deployments are automated from the main branch.

## Acceptance Criteria

1. **Given** code is pushed to the repository **When** a GitHub Actions workflow triggers **Then** the backend pipeline runs: Ruff check → mypy → pytest (unit) → pytest (integration with Postgres service container) → Docker build

2. **Given** code is pushed to the repository **When** a GitHub Actions workflow triggers **Then** the frontend pipeline runs: ESLint → tsc --noEmit → vitest → next build

3. **Given** the backend Dockerfile exists **When** the Docker build step runs **Then** it uses multi-stage build (python:3.12-slim + uv) and produces a valid production image

4. **Given** the project is initialized **When** the developer checks for `.env.example` files **Then** both frontend and backend have `.env.example` (or `.env.local.example`) with all required environment variables documented

5. **Given** Railway deployment is configured **When** code is merged to main **Then** backend deploys automatically as two separate services: API (gunicorn+uvicorn) and ARQ worker

6. **Given** Vercel deployment is configured **When** code is merged to main **Then** frontend auto-deploys with preview deployments per PR

7. **Given** infrastructure is provisioned **When** the developer checks cloud services **Then** Neon PostgreSQL database is provisioned and accessible

8. **Given** infrastructure is provisioned **When** the developer checks cloud services **Then** Upstash Redis is provisioned and accessible

9. **Given** all pipelines are configured **When** running against the initial scaffold code **Then** all pipelines pass green

## Tasks / Subtasks

- [ ] Task 1: Create backend CI workflow (AC: #1, #3, #9)
  - [ ] Create `.github/workflows/ci-backend.yml`
  - [ ] Trigger on push/PR for `backend/**` paths
  - [ ] Job steps: checkout → setup Python 3.12 → install uv → `uv sync` → `ruff check .` → `mypy src tests` → `pytest tests/unit` → pytest integration with Postgres service container → Docker build (build-only, no push)
  - [ ] Postgres 16 service container for integration tests
  - [ ] Set working-directory: `backend` for all steps
  - [ ] Cache uv dependencies for faster runs

- [ ] Task 2: Create frontend CI workflow (AC: #2, #9)
  - [ ] Create `.github/workflows/ci-frontend.yml`
  - [ ] Trigger on push/PR for `table-project-web/**` paths
  - [ ] Job steps: checkout → setup Node 22 → install pnpm → `pnpm install --frozen-lockfile` → `pnpm lint` → `pnpm exec tsc --noEmit` → `pnpm build`
  - [ ] Set working-directory: `table-project-web` for all steps
  - [ ] Cache pnpm store for faster runs
  - [ ] Note: vitest is not yet configured (no test files exist) — skip test step or add a placeholder test

- [ ] Task 3: Create frontend .env.local.example (AC: #4)
  - [ ] Create `table-project-web/.env.local.example` with:
    - `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
    - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder`
    - `CLERK_SECRET_KEY=sk_test_placeholder`
  - [ ] Verify backend `.env.example` already exists (it does — from Story 1.1)

- [ ] Task 4: Configure Railway deployment (AC: #5)
  - [ ] Create `railway.toml` or `railway.json` in `backend/` (if Railway needs explicit config)
  - [ ] Document Railway setup in a deployment section:
    - API service: Docker deploy from `backend/`, start command = Dockerfile CMD
    - ARQ worker service: same Docker image, override CMD to `arq src.app.workers.arq_settings.WorkerSettings`
    - Deploy command (pre-start): `alembic upgrade head`
    - Environment variables: DATABASE_URL, REDIS_URL, ENVIRONMENT=production, CLERK_SECRET_KEY, LLM API keys
  - [ ] Create `.github/workflows/deploy.yml` (optional — Railway auto-deploys from GitHub, may not need explicit workflow)
  - [ ] Note: actual Railway project creation requires manual setup via Railway dashboard or CLI with account auth

- [ ] Task 5: Configure Vercel deployment (AC: #6)
  - [ ] Create `vercel.json` in `table-project-web/` (if needed for monorepo root directory override)
  - [ ] Document Vercel setup:
    - Framework: Next.js (auto-detected)
    - Root directory: `table-project-web`
    - Build command: `pnpm build`
    - Output directory: `.next`
    - Environment variables: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY
  - [ ] Note: Vercel auto-deploys from GitHub — connect repo via Vercel dashboard

- [ ] Task 6: Provision Neon PostgreSQL (AC: #7)
  - [ ] Document Neon setup steps:
    - Create Neon project via console or CLI
    - Note connection string format for Railway env vars
    - Enable connection pooling (PgBouncer)
    - Create a `dev` branch for development (Neon branching feature)
  - [ ] Update backend `.env.example` with Neon connection string format comment

- [ ] Task 7: Provision Upstash Redis (AC: #8)
  - [ ] Document Upstash setup steps:
    - Create Upstash Redis instance via console
    - Note connection string format for Railway env vars
    - REST API available (optional — direct Redis protocol used by ARQ)
  - [ ] Update backend `.env.example` with Upstash connection string format comment

- [ ] Task 8: Verify all pipelines pass (AC: #9)
  - [ ] Push to a test branch, verify CI-backend passes green
  - [ ] Verify CI-frontend passes green
  - [ ] Fix any issues found during pipeline execution

## Dev Notes

### Technical Stack (Verified May 2026)

| Technology | Version | Notes |
|-----------|---------|-------|
| GitHub Actions | v4 actions | `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4` |
| Python | 3.12 | Match `backend/.python-version` |
| Node.js | 22.x | LTS, for frontend builds |
| pnpm | Latest | Frontend package manager |
| uv | 0.7.x+ | Backend package manager (already pinned in Dockerfile at 0.7.22) |
| Docker | Latest | For backend image build verification |
| Railway | Cloud | Push-to-deploy from GitHub |
| Vercel | Cloud | Native Next.js hosting |
| Neon | PostgreSQL 16 | Serverless database |
| Upstash | Redis 7 | Serverless cache + queue |

### Architecture Constraints — MUST FOLLOW

- **Monorepo structure**: `.github/workflows/` at project root, `backend/` and `table-project-web/` as subdirectories
- **Path-filtered triggers**: Backend CI triggers only on `backend/**` changes, frontend CI triggers only on `table-project-web/**` changes
- **No secrets in code**: All API keys, database URLs, etc. via GitHub Secrets → environment variables
- **Dockerfile already exists**: `backend/Dockerfile` is a multi-stage build with uv — do NOT recreate it
- **Docker compose ports**: Local dev uses `15432` (Postgres) and `6380` (Redis) because default ports were occupied on dev machine
- **Backend working directory**: All backend CI steps must use `working-directory: backend`
- **Frontend working directory**: All frontend CI steps must use `working-directory: table-project-web`

### CI Backend Workflow Pattern

```yaml
# .github/workflows/ci-backend.yml
name: CI Backend

on:
  push:
    branches: [main]
    paths: ['backend/**']
  pull_request:
    paths: ['backend/**']

defaults:
  run:
    working-directory: backend

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: table_project_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: uv sync --frozen

      - name: Ruff check
        run: uv run ruff check .

      - name: Mypy
        run: uv run mypy src tests

      - name: Unit tests
        run: uv run pytest tests/unit -v

      - name: Integration tests
        run: uv run pytest tests/integration -v
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/table_project_test
          REDIS_URL: redis://localhost:6379/0

  docker-build:
    runs-on: ubuntu-latest
    needs: lint-and-test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t table-project-backend .
        working-directory: backend
```

**Important notes:**
- CI service container uses standard port 5432 (not 15432 like local dev) — the DATABASE_URL env var in the integration test step must reflect this
- `astral-sh/setup-uv@v6` is the official uv GitHub Action — use it instead of manual curl install
- `uv sync --frozen` ensures lockfile is respected (fails if lockfile is out of date)

### CI Frontend Workflow Pattern

```yaml
# .github/workflows/ci-frontend.yml
name: CI Frontend

on:
  push:
    branches: [main]
    paths: ['table-project-web/**']
  pull_request:
    paths: ['table-project-web/**']

defaults:
  run:
    working-directory: table-project-web

jobs:
  lint-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: latest

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'
          cache-dependency-path: table-project-web/pnpm-lock.yaml

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Type check
        run: pnpm exec tsc --noEmit

      - name: Build
        run: pnpm build
```

**Important notes:**
- `pnpm/action-setup@v4` is the official pnpm action
- `cache-dependency-path` must point to the correct lockfile location in the monorepo
- No `vitest` step yet — test infrastructure doesn't exist. Add when first tests are written (Epic 2+)
- `turbopack.root` in `next.config.ts` is set to `process.cwd()` — this avoids monorepo root inference issues in CI

### Railway Deployment Configuration

Railway auto-deploys from GitHub. Two services from the same Docker image:

**API Service:**
- Root directory: `backend`
- Builder: Dockerfile
- Start command: (use Dockerfile CMD — `gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 src.app.main:app`)
- Deploy command: `alembic upgrade head` (runs migrations before starting)
- Environment variables:
  - `DATABASE_URL` (from Neon, replace `postgresql://` with `postgresql+asyncpg://`)
  - `REDIS_URL` (from Upstash)
  - `ENVIRONMENT=production`
  - `API_V1_PREFIX=/api/v1`

**ARQ Worker Service:**
- Same Docker image
- Start command override: `arq src.app.workers.arq_settings.WorkerSettings`
- No deploy command needed (no HTTP traffic)
- Same environment variables as API service

**Note:** Railway project and services must be created manually via Railway dashboard (https://railway.com). Link the GitHub repo, set root directory to `backend`, and configure environment variables. No `railway.toml` is strictly required — Railway detects Dockerfile automatically.

### Vercel Deployment Configuration

Vercel auto-deploys from GitHub. For monorepo setup:

```json
// table-project-web/vercel.json (only if needed)
{
  "$schema": "https://openapi.vercel.sh/vercel.json"
}
```

**Vercel project settings (via dashboard):**
- Framework preset: Next.js
- Root directory: `table-project-web`
- Build command: `pnpm build` (auto-detected)
- Output directory: `.next` (auto-detected)
- Install command: `pnpm install --frozen-lockfile`
- Node.js version: 22.x
- Environment variables:
  - `NEXT_PUBLIC_API_URL` (Railway backend URL)
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  - `CLERK_SECRET_KEY`

**Note:** Vercel project must be created via Vercel dashboard (https://vercel.com). Import from GitHub, set root directory to `table-project-web`. Preview deployments happen automatically on PRs.

### Neon PostgreSQL Setup

1. Create project at https://console.neon.tech
2. Default branch = `main` (production)
3. Create `dev` branch for development (instant copy-on-write)
4. Connection string format: `postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
5. For SQLAlchemy async: replace `postgresql://` with `postgresql+asyncpg://`
6. Enable connection pooling (PgBouncer) for production — use pooled connection string for API, direct for migrations

### Upstash Redis Setup

1. Create database at https://console.upstash.com
2. Choose region closest to Railway deployment region
3. Connection string format: `rediss://default:password@hostname:port` (TLS)
4. ARQ uses direct Redis protocol (not REST API)
5. Free tier: 10K commands/day — sufficient for MVP

### Environment Variables Summary

**Backend (.env.example — already exists, verify complete):**
```
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/table_project
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/table_project_test
REDIS_URL=redis://localhost:6380/0
ENVIRONMENT=development
DEBUG=false
# Production (Railway):
# DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
# REDIS_URL=rediss://default:pass@hostname:port
# ENVIRONMENT=production
```

**Frontend (.env.local.example — NEW):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
CLERK_SECRET_KEY=sk_test_placeholder
# Production (Vercel):
# NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app/api/v1
```

### Previous Story Intelligence

**Story 1.1 (Backend Scaffold):**
- Backend at `backend/` with uv, Python 3.12
- Dockerfile already exists: multi-stage, python:3.12-slim, uv 0.7.22, gunicorn+uvicorn
- docker-compose.yml: Postgres 16 (port 15432), Redis 7 (port 6380)
- `.env.example` exists with local dev URLs
- `pyproject.toml` has Ruff, mypy, pytest config
- Tests: `tests/unit/test_health.py` exists and passes
- `tests/integration/` and `tests/e2e/` have `.gitkeep` only
- Alembic configured with async template, one baseline migration exists

**Story 1.2 (Frontend Scaffold):**
- Frontend at `table-project-web/` with pnpm, Next.js 16.2.4
- `package.json` scripts: dev, build, start, lint
- No test runner configured yet (no vitest)
- `turbopack.root` set in `next.config.ts` — critical for CI build to work in monorepo
- `eslint.config.mjs` (not `.eslintrc.json`) — Next.js 16 pattern

**Story 1.3 (App Shell Layout):**
- Created Sidebar, Topbar, AppShell components in `src/components/layout/`
- Route group `(app)/` with placeholder pages for /, /collections, /dashboard, /settings
- Installed Sheet component (shadcn/ui) for mobile sidebar overlay
- Chrome tokens added to globals.css

### Project Structure (Files This Story Creates)

```
.github/
└── workflows/
    ├── ci-backend.yml              # NEW
    └── ci-frontend.yml             # NEW
backend/
├── .env.example                    # UPDATE: add production URL comments
table-project-web/
├── .env.local.example              # NEW
```

### Anti-Patterns to AVOID

- Do NOT create a deploy workflow that pushes Docker images — Railway and Vercel auto-deploy from GitHub
- Do NOT hardcode secrets in workflow files — use `${{ secrets.* }}` for any real credentials
- Do NOT run integration tests without a Postgres service container — they need a real database
- Do NOT use `pip install` in CI — use `uv sync` to match the lockfile exactly
- Do NOT use `npm` or `yarn` for frontend — use `pnpm` per architecture
- Do NOT create Neon/Upstash/Railway/Vercel accounts programmatically — document manual setup steps
- Do NOT modify the existing Dockerfile — it already works correctly
- Do NOT skip the `--frozen-lockfile` / `--frozen` flags in CI — lockfile integrity is essential
- Do NOT add Redis service container to CI — integration tests currently don't need Redis (no Redis-dependent tests exist yet)

### References

- [Source: _out_put/planning-artifacts/architecture.md#Infrastructure & Deployment]
- [Source: _out_put/planning-artifacts/architecture.md#CI Pipeline (GitHub Actions)]
- [Source: _out_put/planning-artifacts/architecture.md#Deployment]
- [Source: _out_put/planning-artifacts/architecture.md#MVP Infrastructure Cost Estimate]
- [Source: _out_put/planning-artifacts/architecture.md#Monorepo Root Structure]
- [Source: _out_put/planning-artifacts/epics/epic-1-project-foundation-developer-infrastructure.md#Story 1.4]
- [Source: _out_put/implementation-artifacts/1-1-initialize-backend-scaffold.md]
- [Source: _out_put/implementation-artifacts/1-2-initialize-frontend-scaffold.md]
- [Source: _out_put/implementation-artifacts/1-3-app-shell-layout.md]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
