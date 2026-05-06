# Story 2.1: User Registration & Login with Clerk

Status: in-progress

## Story

As a **new user**,
I want to register using email/password, Google OAuth, or LINE OAuth, and log in with persistent sessions across browser tabs,
so that I can securely access my learning data from any device.

## Acceptance Criteria

1. **Given** a visitor is on the sign-up page **When** they register with email/password, Google OAuth, or LINE OAuth **Then** a Clerk account is created and the user is redirected to the onboarding flow **And** a corresponding user record is created in the backend database (via Clerk webhook sync) **And** the user record stores: clerk_id, email, display_name, tier (default: free), created_at

2. **Given** a registered user is on the sign-in page **When** they log in with their credentials **Then** a Clerk session is established with short-lived JWT (15-minute access token + refresh rotation) **And** the session persists across browser tabs **And** authenticated API requests include the Clerk JWT in the Authorization header **And** the backend `get_current_user` dependency verifies the JWT and extracts user identity

3. **Given** a user is not authenticated **When** they try to access any `(app)/*` route **Then** they are redirected to the sign-in page via Next.js middleware

## Tasks / Subtasks

- [ ] Task 1: Install and configure Clerk in frontend (AC: #1, #2, #3)
  - [x] Install `@clerk/nextjs`
  - [ ] Add `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` to `.env.local`
  - [x] Wrap root layout with `<ClerkProvider>`
  - [x] Create `src/middleware.ts` using `clerkMiddleware()` — protect `(app)/*` routes, allow `/sign-in`, `/sign-up`, `/api/clerk-webhook`
  - [x] Create `src/app/sign-in/[[...sign-in]]/page.tsx` with Clerk `<SignIn />` component
  - [x] Create `src/app/sign-up/[[...sign-up]]/page.tsx` with Clerk `<SignUp />` component
  - [x] Update `.env.local.example` with Clerk env vars and sign-in/sign-up URLs

- [x] Task 2: Create backend auth domain layer (AC: #1, #2)
  - [x] `modules/auth/domain/entities.py` — User entity with: id, clerk_id, email, display_name, tier, created_at, updated_at
  - [x] `modules/auth/domain/value_objects.py` — UserTier enum (free, student, professional)
  - [x] `modules/auth/domain/exceptions.py` — AuthenticationError, AuthorizationError, UserNotFoundError
  - [x] `modules/auth/domain/interfaces.py` — UserRepository abstract class

- [x] Task 3: Create backend auth infrastructure layer (AC: #1)
  - [x] `modules/auth/infrastructure/models.py` — SQLAlchemy `users` table: id (serial PK), clerk_id (unique, indexed), email (unique), display_name, tier (default 'free'), created_at, updated_at (use TimestampMixin)
  - [x] `modules/auth/infrastructure/repository.py` — UserRepository impl: get_by_clerk_id, get_by_id, create, update
  - [x] Create Alembic migration for `users` table

- [x] Task 4: Create backend auth application layer (AC: #1)
  - [x] `modules/auth/application/services.py` — UserSyncService: sync_from_clerk_webhook (create or update user from webhook payload)

- [x] Task 5: Implement Clerk JWT verification in backend (AC: #2)
  - [x] Add `PyJWT[crypto]` to backend dependencies
  - [x] Add `clerk_publishable_key`, `clerk_secret_key`, `clerk_jwks_url` to `core/config.py` Settings
  - [x] Implement `core/security.py` — `get_current_user` FastAPI dependency: extract JWT from Authorization header, verify via Clerk JWKS (RS256), extract sub (clerk_id), lookup user in DB
  - [x] Cache JWKS keys in-memory (refresh every 1h)

- [x] Task 6: Create backend auth API layer (AC: #1, #2)
  - [x] `modules/auth/api/schemas.py` — UserResponse, WebhookPayload Pydantic models
  - [x] `modules/auth/api/dependencies.py` — `get_current_user` re-export, `require_tier` dependency
  - [x] `modules/auth/api/router.py` — endpoints:
    - `GET /api/v1/users/me` — returns current user profile (protected)
    - `POST /api/v1/auth/webhook` — Clerk webhook receiver (verify svix signature, sync user)
  - [x] Mount auth_router in `main.py`

- [ ] Task 7: Create Clerk webhook route in frontend (AC: #1)
  - [x] `src/app/api/clerk-webhook/route.ts` — Next.js API route that receives Clerk webhooks and forwards `user.created`/`user.updated`/`user.deleted` events to backend `/api/v1/auth/webhook`
  - [ ] Alternative: configure Clerk webhook to hit backend directly (preferred if backend is publicly accessible)

- [x] Task 8: Create frontend API client with auth (AC: #2)
  - [x] `src/lib/api-client.ts` — fetch wrapper that injects Clerk JWT via `useAuth().getToken()` into Authorization header
  - [x] `src/lib/query-client.ts` — TanStack Query client config

- [x] Task 9: Write tests (AC: #1, #2, #3)
  - [x] Backend unit: `tests/unit/modules/auth/domain/test_entities.py` — User entity, UserTier enum
  - [x] Backend unit: `tests/unit/modules/auth/application/test_services.py` — UserSyncService (mocked repo)
  - [x] Backend integration: `tests/integration/modules/auth/test_repository.py` — UserRepository with real Postgres
  - [x] Backend e2e: `tests/e2e/test_auth_flow.py` — webhook → create user → get /users/me with JWT

- [ ] Task 10: Verify end-to-end (AC: #1, #2, #3)
  - [ ] Sign up via Clerk UI → user created in Clerk + backend DB
  - [ ] Sign in → JWT issued → GET /users/me returns user data
  - [ ] Unauthenticated access to `(app)/*` redirects to sign-in
  - [ ] Session persists across browser tabs

## Dev Notes

### Technical Stack (This Story)

| Technology | Version | Purpose |
|-----------|---------|---------|
| @clerk/nextjs | Latest | Frontend auth UI + middleware |
| PyJWT[crypto] | Latest | Backend JWT verification (RS256) |
| svix | Latest (Python) | Clerk webhook signature verification |
| Clerk | SaaS | Auth provider (10K free MAU) |

### Architecture Constraints — MUST FOLLOW

- **Hexagonal layers**: domain/ NEVER imports infrastructure/ or api/
- **Naming**: snake_case for Python, PascalCase for React components, snake_case for DB/API
- **Error format**: `{error: {code, message, details}}` for all API errors
- **Pydantic models**: Required for all API boundaries — no raw dicts
- **Dependencies**: Use `Depends()` for all injectable dependencies
- **Logging**: structlog with bound context — never `print()`

### Current Codebase State (Files Being Modified)

**`backend/src/app/core/security.py`** — Currently a placeholder docstring. Will be replaced with `get_current_user` Clerk JWT verification dependency.

**`backend/src/app/core/config.py`** — Currently has: project_name, environment, debug, api_v1_prefix, database_url, test_database_url, redis_url. Add: clerk_publishable_key, clerk_secret_key, clerk_jwks_url.

**`backend/src/app/core/dependencies.py`** — Currently a placeholder docstring. Add shared `get_current_user` re-export.

**`backend/src/app/main.py`** — Currently has health_router only. Add auth_router mount + CORS middleware.

**`frontend/src/app/layout.tsx`** — Currently wraps children in TooltipProvider. Wrap with `<ClerkProvider>` as outermost provider.

**`frontend/src/app/(app)/layout.tsx`** — Currently wraps children in AppShell. No changes needed — middleware handles auth redirect.

**`frontend/.env.local.example`** — Exists with placeholder Clerk keys. Update with sign-in/sign-up URL env vars.

### Backend Auth Module Structure (Create)

```
modules/auth/
├── domain/
│   ├── entities.py       # User dataclass: id, clerk_id, email, display_name, tier, timestamps
│   ├── value_objects.py  # UserTier(StrEnum): free, student, professional
│   ├── exceptions.py     # AuthenticationError, AuthorizationError, UserNotFoundError
│   └── interfaces.py     # AbstractUserRepository(ABC)
├── application/
│   └── services.py       # UserSyncService.sync_from_webhook(payload) → User
├── infrastructure/
│   ├── models.py         # SQLAlchemy: users table (id, clerk_id, email, display_name, tier, timestamps)
│   └── repository.py     # UserRepository: get_by_clerk_id, get_by_id, create, update
└── api/
    ├── schemas.py        # UserResponse, WebhookPayload (Pydantic)
    ├── dependencies.py   # get_current_user, require_tier
    └── router.py         # GET /users/me, POST /auth/webhook
```

### Frontend Routes (Create)

```
src/
├── app/
│   ├── sign-in/[[...sign-in]]/page.tsx    # NEW: Clerk SignIn
│   ├── sign-up/[[...sign-up]]/page.tsx    # NEW: Clerk SignUp
│   └── api/clerk-webhook/route.ts         # NEW: Webhook forwarder (optional)
├── lib/
│   ├── api-client.ts                      # NEW: Fetch + Clerk JWT injection
│   └── query-client.ts                    # NEW: TanStack Query config
└── middleware.ts                           # NEW: Clerk auth middleware
```

### Database Schema: `users` Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    clerk_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_clerk_id ON users (clerk_id);
```

### Clerk JWT Verification Pattern

```python
# core/security.py
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
jwks_client = PyJWKClient(settings.clerk_jwks_url, cache_keys=True, lifespan=3600)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    token = credentials.credentials
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
    clerk_id = payload["sub"]
    user = await user_repo.get_by_clerk_id(session, clerk_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### Clerk Webhook Verification

Use `svix` library to verify webhook signatures. Clerk sends webhooks with `svix-id`, `svix-timestamp`, `svix-signature` headers.

```python
from svix.webhooks import Webhook
wh = Webhook(settings.clerk_webhook_secret)
payload = wh.verify(body, headers)  # raises on invalid signature
```

### Frontend Middleware Pattern

```typescript
// src/middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/clerk-webhook(.*)',
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()
  }
})

export const config = {
  matcher: ['/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)'],
}
```

### CORS Configuration

Backend must allow frontend origin for cross-origin requests:

```python
# In main.py create_application()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # from settings in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Previous Story Intelligence

**From Story 1.4 (CI/CD):**
- Frontend directory is `frontend/` (renamed from `table-project-web/`), package name still "table-project-web"
- CI workflows trigger on `backend/**` and `table-project-web/**` paths — may need updating after rename
- Backend uses `uv` for package management, not pip
- Docker compose uses ports 15432 (Postgres) and 6380 (Redis) — non-standard
- `astral-sh/setup-uv@v6` for CI
- Frontend uses `eslint.config.mjs` (not `.eslintrc.json`) — Next.js 16 flat config

**From Story 1.3 (App Shell):**
- AppShell component at `src/components/layout/` with Sidebar + Topbar
- Route group `(app)/` with layout.tsx wrapping children in AppShell
- Sidebar has 4 nav items: Today's Queue, Collections, Dashboard, Settings

**From Story 1.1 (Backend Scaffold):**
- SQLAlchemy Base and TimestampMixin in `db/base.py`
- Async session factory in `db/session.py`
- Alembic async template configured with one baseline migration
- health_router at `/api/v1/health`

**IMPORTANT — Next.js 16 Warning:**
`frontend/AGENTS.md` states: "This is NOT the Next.js you know. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code." Dev agent MUST check Next.js 16 docs for `middleware.ts` and API route patterns before implementing.

### Anti-Patterns to AVOID

- Do NOT create custom auth UI — use Clerk's pre-built `<SignIn />` and `<SignUp />` components
- Do NOT store JWT tokens in localStorage or cookies manually — Clerk manages sessions
- Do NOT call Clerk API from backend to verify tokens — use JWKS public key verification via PyJWT
- Do NOT skip webhook signature verification — use svix library
- Do NOT add Clerk SDK to backend — backend only verifies JWTs
- Do NOT modify the existing AppShell or Sidebar components in this story
- Do NOT implement onboarding redirect in this story — that's Story 2.2
- Do NOT use `pip install` — use `uv add` for backend dependencies
- Do NOT hardcode Clerk keys — use environment variables via Settings

### References

- [Source: _out_put/planning-artifacts/epics/epic-2-user-authentication-onboarding-profile.md#Story 2.1]
- [Source: _out_put/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _out_put/planning-artifacts/architecture.md#Backend Module Structure]
- [Source: _out_put/planning-artifacts/architecture.md#API & Communication Patterns]
- [Source: _out_put/planning-artifacts/architecture.md#Process Patterns - Authentication Flow]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#User Journey - First-Time Onboarding]
- [Source: _out_put/implementation-artifacts/1-4-cicd-pipeline-deployment-configuration.md]
- [Source: _out_put/implementation-artifacts/1-1-initialize-backend-scaffold.md]
- [Clerk Next.js Quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart)
- [Clerk Manual JWT Verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
- [Clerk Webhooks](https://clerk.com/docs/guides/development/webhooks/syncing)

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `pnpm build`
- `pnpm lint`
- `pnpm test`
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy .`
- `docker compose up -d postgres redis`
- `DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:15432/table_project_test" uv run alembic upgrade head`

### Completion Notes List

- Implemented frontend Clerk integration with root `ClerkProvider`, protected `src/middleware.ts`, Clerk sign-in/sign-up routes, webhook forwarder, and auth-aware API/query client utilities.
- Implemented backend auth vertical slice with domain entities/interfaces, SQLAlchemy `users` model + repository, Clerk webhook sync service, Clerk JWT verification, `GET /api/v1/users/me`, `POST /api/v1/auth/webhook`, CORS, and consistent API error envelopes.
- Added backend unit, integration, and e2e coverage for entity/service/repository/auth flow behavior; all backend tests, frontend tests, frontend build, backend lint, and backend mypy checks pass locally.
- Story remains `in-progress` because manual Clerk configuration and browser verification are still pending: real Clerk keys were not written to `frontend/.env.local`, direct Clerk-to-backend webhook configuration depends on deployment accessibility, and sign-up/sign-in/session-persistence checks require an interactive browser with Clerk credentials.

### File List

- `_out_put/implementation-artifacts/2-1-user-registration-login-with-clerk.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
- `backend/alembic/env.py`
- `backend/alembic/versions/1cc5f6af6b47_add_users_table.py`
- `backend/pyproject.toml`
- `backend/src/app/core/config.py`
- `backend/src/app/core/dependencies.py`
- `backend/src/app/core/security.py`
- `backend/src/app/main.py`
- `backend/src/app/modules/auth/api/__init__.py`
- `backend/src/app/modules/auth/api/dependencies.py`
- `backend/src/app/modules/auth/api/router.py`
- `backend/src/app/modules/auth/api/schemas.py`
- `backend/src/app/modules/auth/application/__init__.py`
- `backend/src/app/modules/auth/application/services.py`
- `backend/src/app/modules/auth/domain/entities.py`
- `backend/src/app/modules/auth/domain/exceptions.py`
- `backend/src/app/modules/auth/domain/interfaces.py`
- `backend/src/app/modules/auth/domain/value_objects.py`
- `backend/src/app/modules/auth/infrastructure/__init__.py`
- `backend/src/app/modules/auth/infrastructure/models.py`
- `backend/src/app/modules/auth/infrastructure/repository.py`
- `backend/tests/conftest.py`
- `backend/tests/e2e/test_auth_flow.py`
- `backend/tests/integration/modules/auth/test_repository.py`
- `backend/tests/unit/modules/auth/application/test_services.py`
- `backend/tests/unit/modules/auth/domain/test_entities.py`
- `backend/uv.lock`
- `frontend/.env.local.example`
- `frontend/package.json`
- `frontend/pnpm-lock.yaml`
- `frontend/src/app/api/clerk-webhook/route.ts`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/app/sign-in/[[...sign-in]]/page.tsx`
- `frontend/src/app/sign-up/[[...sign-up]]/page.tsx`
- `frontend/src/lib/api-client.ts`
- `frontend/src/lib/query-client.ts`
- `frontend/src/middleware.ts`
