# Story 1.1: Initialize Backend Scaffold with FastAPI & Hexagonal Structure

Status: review

## Story

As a **developer**,
I want a fully configured FastAPI backend scaffold with hexagonal module structure, async SQLAlchemy, Alembic migrations, and dev tooling (Ruff, mypy, pytest),
so that all future feature development follows consistent architecture patterns from day one.

## Acceptance Criteria

1. **Given** the backend directory does not exist **When** the developer runs the initialization commands **Then** the project is created with uv, Python 3.12, all core dependencies installed:
   - fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, redis, arq
   - Dev: ruff, mypy, pytest, pytest-asyncio, pytest-mock, httpx, pre-commit

2. **Given** dependencies are installed **When** the developer inspects the project structure **Then** the hexagonal module structure exists for all 8 bounded contexts (auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard) with `domain/`, `application/`, `infrastructure/`, `api/` subdirectories each containing `__init__.py`

3. **Given** the project is initialized **When** Alembic is configured **Then** Alembic is initialized with the async template (`alembic init -t async alembic`) and `env.py` uses `async_engine_from_config`

4. **Given** the backend is running **When** a GET request is sent to `/api/v1/health` **Then** it returns 200 OK with a JSON response

5. **Given** Docker is available **When** `docker compose up -d` is run **Then** local PostgreSQL 16 and Redis containers start and are accessible

6. **Given** the project is initialized **When** the developer inspects `pyproject.toml` **Then** it contains Ruff, mypy, and pytest configuration sections

7. **Given** the project is initialized **When** the developer inspects `.pre-commit-config.yaml` **Then** Ruff and mypy hooks are configured

8. **Given** local Postgres is running **When** one Alembic migration is created and applied **Then** the migration succeeds against the local Postgres database

9. **Given** local Postgres is running **When** `uv run pytest` is executed **Then** at least one test passes using an async SQLAlchemy session fixture

## Tasks / Subtasks

- [x] Task 1: Initialize project with uv (AC: #1)
  - [x] Run `uv init backend --python 3.12`
  - [x] Add core dependencies: `uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings redis arq`
  - [x] Add dev dependencies: `uv add --dev ruff mypy pytest pytest-asyncio pytest-mock httpx pre-commit`
  - [x] Add structlog: `uv add structlog`

- [x] Task 2: Create hexagonal module structure (AC: #2)
  - [x] Create `src/app/` package with `__init__.py` and `main.py`
  - [x] Create `src/app/core/` with: `__init__.py`, `config.py`, `security.py`, `dependencies.py`, `middleware.py`, `exceptions.py`, `logging.py`
  - [x] Create `src/app/db/` with: `__init__.py`, `base.py`, `session.py`
  - [x] Create 8 module directories under `src/app/modules/`: auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard
  - [x] Each module gets 4 subdirectories: domain/, application/, infrastructure/, api/ — each with `__init__.py`

- [x] Task 3: Configure Alembic async (AC: #3, #8)
  - [x] Run `alembic init -t async alembic`
  - [x] Configure `alembic.ini` with sqlalchemy.url placeholder
  - [x] Update `env.py` to use `async_engine_from_config` and import project Base metadata
  - [x] Create one initial migration (e.g., health_check table or empty baseline) and verify it applies

- [x] Task 4: Implement health endpoint (AC: #4)
  - [x] Create FastAPI app factory in `src/app/main.py`
  - [x] Add `GET /api/v1/health` returning `{"status": "ok"}`
  - [x] Mount with `/api/v1` prefix

- [x] Task 5: Create docker-compose.yml (AC: #5)
  - [x] PostgreSQL 16 service (port 5432, with env vars for user/password/db)
  - [x] Redis service (port 6379)
  - [x] Named volume for Postgres data persistence

- [x] Task 6: Configure dev tooling (AC: #6, #7)
  - [x] Add Ruff config to `pyproject.toml` (line-length=99, target Python 3.12, select rules)
  - [x] Add mypy config to `pyproject.toml` (strict mode, async plugins)
  - [x] Add pytest config to `pyproject.toml` (asyncio_mode="auto")
  - [x] Create `.pre-commit-config.yaml` with Ruff and mypy hooks
  - [x] Create `.env.example` with all required environment variables

- [x] Task 7: Create core infrastructure files (AC: #9)
  - [x] `src/app/core/config.py` — Pydantic Settings class reading from env vars (DATABASE_URL, REDIS_URL, etc.)
  - [x] `src/app/db/base.py` — SQLAlchemy DeclarativeBase with TimestampMixin (created_at, updated_at)
  - [x] `src/app/db/session.py` — async_sessionmaker, `get_async_session` async generator dependency
  - [x] `src/app/core/logging.py` — structlog configuration (JSON output, bound context)

- [x] Task 8: Write first passing test (AC: #9)
  - [x] Create `tests/conftest.py` with async SQLAlchemy session fixture (uses test database)
  - [x] Create `tests/unit/test_health.py` testing the health endpoint via httpx.AsyncClient
  - [x] Verify `uv run pytest` passes

- [x] Task 9: Create Dockerfile (not in AC but required by architecture)
  - [x] Multi-stage Dockerfile: python:3.12-slim base, uv for dependency install
  - [x] Production stage with gunicorn + uvicorn worker

## Dev Notes

### Technical Stack (Verified Latest Versions — May 2026)

| Technology | Version | Notes |
|-----------|---------|-------|
| Python | 3.12 | Specified in architecture |
| uv | 0.11.x | Package manager |
| FastAPI | 0.136.x | Latest stable |
| SQLAlchemy | 2.0.49 | Async with asyncpg |
| Alembic | 1.18.x | Async template |
| Pydantic | 2.13.x | Settings + validation |
| Ruff | Latest | Replaces black + isort + flake8 |
| py-fsrs | 6.3.x | FSRS 6 model (not needed this story, but note version) |
| structlog | Latest | JSON structured logging |

### Architecture Constraints — MUST FOLLOW

- **Hexagonal layer rule**: `domain/` NEVER imports from `infrastructure/` or `api/`. Dependency flows inward only.
- **Naming**: snake_case everywhere (Python, DB, API). Classes PascalCase. Constants UPPER_SNAKE_CASE.
- **Pydantic Settings** for all config — never `os.environ` directly.
- **structlog** for logging — never `print()` or bare `logging`.
- **Error format**: `{"error": {"code": "...", "message": "...", "details": null}}`
- **API prefix**: All endpoints under `/api/v1/`

### Backend File Structure (Target)

```
backend/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
├── .env.example
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── security.py      (placeholder — implemented in Epic 2)
│       │   ├── dependencies.py  (placeholder)
│       │   ├── middleware.py     (placeholder)
│       │   ├── exceptions.py
│       │   └── logging.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── session.py
│       └── modules/
│           ├── __init__.py
│           ├── auth/
│           │   ├── __init__.py
│           │   ├── domain/      (__init__.py only)
│           │   ├── application/ (__init__.py only)
│           │   ├── infrastructure/ (__init__.py only)
│           │   └── api/         (__init__.py only)
│           ├── vocabulary/      (same shape)
│           ├── srs/             (same shape)
│           ├── collections/     (same shape)
│           ├── enrichment/      (same shape)
│           ├── intent/          (same shape)
│           ├── dictionary/      (same shape)
│           └── dashboard/       (same shape)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_health.py
│   ├── integration/
│   └── e2e/
```

### Pydantic Settings Config Pattern

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/table_project"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

### SQLAlchemy Async Session Pattern

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

### Test Fixture Pattern

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.app.main import app
from src.app.db.session import get_async_session

@pytest.fixture
async def async_session():
    # Use test database URL
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/table_project_test")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

### Docker Compose Pattern

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: table_project
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### Anti-Patterns to AVOID

- Do NOT use SQLModel — use SQLAlchemy 2.0 directly per architecture decision
- Do NOT create a flat project structure — hexagonal modules are mandatory
- Do NOT use pip or poetry — uv is the package manager
- Do NOT use `print()` for logging — use structlog
- Do NOT put business logic in route handlers — routes call services
- Do NOT hardcode config values — use Pydantic Settings
- Do NOT create `requirements.txt` — uv uses `pyproject.toml` + `uv.lock`
- Do NOT skip `__init__.py` files — every package needs one

### Project Structure Notes

- Backend lives in `backend/` directory at project root (not `table_project/`)
- Frontend will live in `table-project-web/` (Story 1.2)
- Monorepo root contains `.github/workflows/`, README.md, and both subdirectories

### References

- [Source: _out_put/planning-artifacts/architecture.md#Selected Backend Starter: Custom Scaffold]
- [Source: _out_put/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _out_put/planning-artifacts/architecture.md#Backend File Structure]
- [Source: _out_put/planning-artifacts/epics/epic-1-project-foundation-developer-infrastructure.md#Story 1.1]
- [Source: _out_put/planning-artifacts/prd/non-functional-requirements.md]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `uv init backend --python 3.12`
- `uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic pydantic-settings redis arq`
- `uv add --dev ruff mypy pytest pytest-asyncio pytest-mock httpx pre-commit`
- `uv add structlog gunicorn`
- `uv run alembic init -t async alembic`
- `docker compose up -d`
- `uv run alembic upgrade head`
- `uv run ruff check .`
- `uv run mypy src tests`
- `uv run pytest`
- `uv run uvicorn src.app.main:app --host 127.0.0.1 --port 8000`

### Completion Notes List

- Initialized a new `backend/` uv project with Python 3.12 and the FastAPI, SQLAlchemy async, Alembic, Redis, ARQ, structlog, Ruff, mypy, pytest, and pre-commit toolchain.
- Created the `src/app` scaffold, core config/logging/db packages, and the full hexagonal module package tree for auth, vocabulary, srs, collections, enrichment, intent, dictionary, and dashboard.
- Configured Alembic async support, generated a baseline migration, and verified `uv run alembic upgrade head` against the local Dockerized PostgreSQL instance.
- Added `GET /api/v1/health`, async SQLAlchemy test fixtures, and a passing health test; verified the live endpoint returns `{"status": "ok"}`.
- Added backend Docker artifacts and a local `.gitignore`; host port mappings use `15432` for PostgreSQL and `6380` for Redis because this machine already has services bound to `5432` and `6379`.

### File List

- `backend/.env.example`
- `backend/.gitignore`
- `backend/.pre-commit-config.yaml`
- `backend/.python-version`
- `backend/Dockerfile`
- `backend/README.md`
- `backend/alembic.ini`
- `backend/alembic/README`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/6c09355b7a98_baseline.py`
- `backend/docker-compose.yml`
- `backend/pyproject.toml`
- `backend/src/__init__.py`
- `backend/src/app/__init__.py`
- `backend/src/app/main.py`
- `backend/src/app/core/__init__.py`
- `backend/src/app/core/config.py`
- `backend/src/app/core/dependencies.py`
- `backend/src/app/core/exceptions.py`
- `backend/src/app/core/logging.py`
- `backend/src/app/core/middleware.py`
- `backend/src/app/core/security.py`
- `backend/src/app/db/__init__.py`
- `backend/src/app/db/base.py`
- `backend/src/app/db/session.py`
- `backend/src/app/modules/__init__.py`
- `backend/src/app/modules/auth/__init__.py`
- `backend/src/app/modules/auth/api/__init__.py`
- `backend/src/app/modules/auth/application/__init__.py`
- `backend/src/app/modules/auth/domain/__init__.py`
- `backend/src/app/modules/auth/infrastructure/__init__.py`
- `backend/src/app/modules/collections/__init__.py`
- `backend/src/app/modules/collections/api/__init__.py`
- `backend/src/app/modules/collections/application/__init__.py`
- `backend/src/app/modules/collections/domain/__init__.py`
- `backend/src/app/modules/collections/infrastructure/__init__.py`
- `backend/src/app/modules/dashboard/__init__.py`
- `backend/src/app/modules/dashboard/api/__init__.py`
- `backend/src/app/modules/dashboard/application/__init__.py`
- `backend/src/app/modules/dashboard/domain/__init__.py`
- `backend/src/app/modules/dashboard/infrastructure/__init__.py`
- `backend/src/app/modules/dictionary/__init__.py`
- `backend/src/app/modules/dictionary/api/__init__.py`
- `backend/src/app/modules/dictionary/application/__init__.py`
- `backend/src/app/modules/dictionary/domain/__init__.py`
- `backend/src/app/modules/dictionary/infrastructure/__init__.py`
- `backend/src/app/modules/enrichment/__init__.py`
- `backend/src/app/modules/enrichment/api/__init__.py`
- `backend/src/app/modules/enrichment/application/__init__.py`
- `backend/src/app/modules/enrichment/domain/__init__.py`
- `backend/src/app/modules/enrichment/infrastructure/__init__.py`
- `backend/src/app/modules/intent/__init__.py`
- `backend/src/app/modules/intent/api/__init__.py`
- `backend/src/app/modules/intent/application/__init__.py`
- `backend/src/app/modules/intent/domain/__init__.py`
- `backend/src/app/modules/intent/infrastructure/__init__.py`
- `backend/src/app/modules/srs/__init__.py`
- `backend/src/app/modules/srs/api/__init__.py`
- `backend/src/app/modules/srs/application/__init__.py`
- `backend/src/app/modules/srs/domain/__init__.py`
- `backend/src/app/modules/srs/infrastructure/__init__.py`
- `backend/src/app/modules/vocabulary/__init__.py`
- `backend/src/app/modules/vocabulary/api/__init__.py`
- `backend/src/app/modules/vocabulary/application/__init__.py`
- `backend/src/app/modules/vocabulary/domain/__init__.py`
- `backend/src/app/modules/vocabulary/infrastructure/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/e2e/.gitkeep`
- `backend/tests/integration/.gitkeep`
- `backend/tests/unit/test_health.py`
- `backend/uv.lock`

### Change Log

- 2026-05-05: Implemented Story 1.1 backend scaffold with FastAPI, async SQLAlchemy, Alembic, Docker, dev tooling, and initial tests.
