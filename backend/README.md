# Table Project Backend

## Local Development

1. Copy `.env.example` to `.env` and adjust values for your machine.
2. Install dependencies with `uv sync --frozen`.
3. Start infrastructure with `docker compose up -d postgres redis`.
4. Run the FastAPI app locally with `uv run uvicorn src.app.main:app --reload`.

## Quality Gates

- Lint: `uv run ruff check .`
- Type check: `uv run mypy src tests`
- Unit tests: `uv run pytest tests/unit -v`
- Integration tests: `uv run pytest tests/integration -v`
- Production image build: `docker build -t table-project-backend .`

The GitHub Actions workflow at `.github/workflows/ci-backend.yml` runs the same sequence on pushes and pull requests that touch `backend/**`.

## Railway Deployment

Railway can deploy directly from GitHub using the existing Dockerfile in `backend/`.

### API service

- Root directory: `backend`
- Builder: Dockerfile
- Start command: use the Dockerfile default CMD
- Deploy command: `alembic upgrade head`

### Worker service

- Root directory: `backend`
- Builder: Dockerfile
- Start command override: `arq src.app.workers.arq_settings.WorkerSettings`
- Deploy command: none required

### Required Railway environment variables

- `DATABASE_URL`
- `REDIS_URL`
- `ENVIRONMENT=production`
- `API_V1_PREFIX=/api/v1`
- `CLERK_SECRET_KEY`
- Any future LLM provider keys used by enrichment services

## Neon PostgreSQL

1. Create a project in the Neon console.
2. Keep the default `main` branch for production.
3. Create a `dev` branch for isolated development work.
4. Use the pooled connection string for the API service.
5. Replace the scheme with `postgresql+asyncpg://` for the async SQLAlchemy application URL.
6. Keep a direct connection string available for one-off admin or migration troubleshooting.

Example application URL:

```text
postgresql+asyncpg://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require
```

## Upstash Redis

1. Create a Redis database in the Upstash console.
2. Pick the region closest to the Railway deployment region.
3. Use the TLS connection string in Railway.
4. Reuse the same `REDIS_URL` for both the API service and the ARQ worker.

Example worker cache URL:

```text
rediss://default:password@hostname:port
```
