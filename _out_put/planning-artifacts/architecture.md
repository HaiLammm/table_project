---
stepsCompleted:
  - "step-01-init"
  - "step-02-context"
  - "step-03-starter"
  - "step-04-decisions"
  - "step-05-patterns"
  - "step-06-structure"
  - "step-07-validation"
  - "step-08-complete"
lastStep: 8
status: 'complete'
completedAt: '2026-05-04'
inputDocuments:
  - "prd.md"
  - "product-brief-table_project.md"
  - "product-brief-table_project-distillate.md"
  - "ux-design-specification.md"
  - "research/technical-vocabulary-learning-system-research-2026-04-30.md"
documentCounts:
  prd: 1
  briefs: 2
  uxDesign: 1
  research: 1
  projectDocs: 0
workflowType: 'architecture'
project_name: 'table_project'
user_name: 'Lem'
date: '2026-05-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

9 functional requirement groups identified for MVP:

1. **Authentication** — Email/password + Google OAuth (Clerk or Supabase Auth)
2. **Onboarding** — 5-question survey → AI learning plan → first review < 3 minutes
3. **Core SRS Engine** — FSRS via py-fsrs, JSONB state storage, daily review queue, 3-keystroke review loop
4. **Bilingual Vocabulary Cards** — Single-language default + parallel mode toggle (Tab), EN-JP with Vietnamese UI
5. **Learning Diagnostics Engine** — Pattern detection: time-of-day retention effects, category-specific weakness, cross-language interference
6. **Database Waterfall** — LLM auto-enrichment pipeline + JMdict cross-validation + central corpus sync
7. **Personal Collections** — Create, organize, CSV import, corpus browsing
8. **Progress Dashboard** — Retention curves, vocabulary growth, SRS health metrics, calendar views (daily/weekly)
9. **Pre-seeded Corpus** — 3,000–5,000 IT/TOEIC/JLPT N3–N2 terms (one-time LLM batch job)

**Non-Functional Requirements:**

| NFR | Target | Architectural Impact |
|-----|--------|---------------------|
| API p95 latency | < 200ms (non-LLM) | Async handlers, connection pooling, caching |
| LLM p95 latency | < 3s, TTFT < 800ms | SSE streaming, provider gateway with fallback |
| LLM cost/user/day | < $0.02 | Prompt caching, Batch API, result caching (Redis), multi-provider routing |
| Cache hit rate | > 70% after 4 weeks | L1 in-process + L2 Redis + L3 CDN layered strategy |
| Domain test coverage | ≥ 90% | Hexagonal architecture, ports & adapters pattern |
| Application test coverage | ≥ 70% | Repository pattern, dependency injection |
| Error rate | < 0.5% | Sentry, structured logging, graceful degradation |
| Auto-enrichment satisfaction | ≥ 85% | JMdict cross-validation, structured outputs, Pydantic validation |
| Time-to-first-review | < 3 min | Pre-seeded corpus, minimal onboarding steps |
| Infra cost (100 users) | ≤ $50/month | Serverless-friendly hosting, aggressive caching |

**UX-Driven Architectural Requirements:**

- **Keyboard-first review flow** — Space → 1/2/3/4 → auto-advance (3 keystrokes/card). Client-side state management optimized for zero-latency card transitions.
- **Progressive intelligence reveal** — Data-gated: Day 1 (basic stats) → Day 3-5 (micro-insights) → Week 2+ (full diagnostics). Background analytics pipeline required.
- **Diagnostic micro-insertions** — Insight cards inline every ~5 cards in review flow. Pre-computed insights server-side.
- **Command palette (⌘K)** — Full-text search on vocabulary terms. PostgreSQL `tsvector` indexing required.
- **Offline awareness** — MVP online-only, but architecture must accommodate IndexedDB sync later. Last-write-wins sufficient.
- **Design system** — shadcn/ui + Tailwind CSS, zinc-based monochrome palette, dark chrome + light canvas.
- **Responsive** — Desktop-first (sidebar 240px + content 720px), tablet (icon sidebar 56px), mobile (hamburger overlay).
- **Accessibility** — WCAG 2.1 AA, Radix UI primitives, axe-core in CI, keyboard navigation throughout.

### Scale & Complexity

- **Primary domain:** Full-stack web application (SPA/PWA) + Python API backend
- **Complexity level:** Medium-High
- **Estimated architectural components:** 8 bounded contexts (auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard)
- **Real-time features:** None — SSE only for LLM streaming responses
- **Multi-tenancy:** Single-tenant SaaS (per-user data isolation via JWT claims)
- **Regulatory:** No special compliance beyond GDPR-style export/delete

### Technical Constraints & Dependencies

| Constraint | Source | Impact |
|-----------|--------|--------|
| FastAPI (Python) backend | User-specified | Entire backend ecosystem must align with Python |
| Next.js 16 (App Router) frontend | PRD | Server Components, TanStack Query, shadcn/ui |
| FSRS algorithm | PRD + Research | py-fsrs library, JSONB state storage |
| JMdict cross-validation | PRD | jamdict library, ~170K entries, validate all JP definitions before display |
| Modular Monolith | PRD + Research | Hexagonal (Ports & Adapters) within each bounded context |
| Freemium from Day 1 | PRD | Tier-based rate limiting, feature gating (50 active SRS cards free) |
| Solo/small team | Project context | Avoid microservices overhead, optimize for DX |
| 14-week MVP timeline | PRD | Prioritize vertical slices, defer browser extension + offline |

### Cross-Cutting Concerns Identified

1. **LLM Gateway** — All LLM calls routed through internal gateway: provider routing, prompt caching, cost tracking, fallback, structured output validation. The single most important architectural decision.
2. **Authentication & Authorization** — JWT propagation across all modules, per-route scopes, tier-based feature gating.
3. **Caching Strategy** — 3 layers (L1 in-process LRU, L2 Redis, L3 CDN). Critical for LLM cost control.
4. **Error Handling & Observability** — Sentry + structured logs + cost tracking dashboard. Graceful degradation on LLM provider outage.
5. **Data Validation** — Pydantic v2 triple-use: request validator + LLM tool schema + domain DTO.
6. **Background Processing** — ARQ + Redis for LLM enrichment queue, daily SRS queue pre-computation.
7. **Bilingual Content Handling** — Multi-script typography (Latin + Japanese + Vietnamese), unicode-range font switching, per-language FSRS tracking.

## Starter Template Evaluation

### Primary Technology Domain

Split-stack web application: Next.js 16 frontend (TypeScript) + FastAPI backend (Python). Two separate starter approaches required.

### Starter Options Considered

| Starter | Evaluated For | Verdict |
|---------|--------------|---------|
| `create-next-app` (official CLI) | Frontend | **Selected** — clean, up-to-date, minimal, pairs with shadcn/ui |
| Next Shadcn Dashboard Starter | Frontend | Rejected — admin dashboard layout doesn't match review-centric UX |
| Full Stack FastAPI Template (Tiangolo) | Backend | Rejected — SQLModel not SQLAlchemy, flat structure not hexagonal |
| fastapi-ddd-cookiecutter | Backend | Rejected — repository pattern yes, but outdated tooling (pip, not uv/ruff) |
| fastapi-template-uv | Backend | Rejected — good tooling (uv + ruff + mypy) but flat structure, no DDD/hexagonal |
| Custom scaffold | Backend | **Selected** — no existing template combines full required stack |

### Selected Frontend Starter: `create-next-app` + shadcn/ui

**Rationale:** Official CLI provides clean, up-to-date foundation. The review-centric UX (not admin dashboard) means starting minimal and building custom components (ReviewCard, RatingButton, InsightCard) on shadcn/ui primitives is more efficient than stripping features from a dashboard template. shadcn/ui's Radix UI primitives provide built-in keyboard navigation and accessibility — critical for the keyboard-first review flow.

**Initialization Commands:**

```bash
pnpm create next-app table-project-web --typescript --tailwind --eslint --app --src-dir
cd table-project-web
npx shadcn@latest init
```

**Architectural Decisions Provided by Starter:**

- **Language & Runtime:** TypeScript (strict), Node.js, React 19
- **Styling:** Tailwind CSS v4
- **Build Tooling:** Turbopack (Next.js 16 default)
- **Routing:** App Router with `src/app/` directory
- **Import Alias:** `@/*`
- **Linting:** ESLint

**Critical Post-Init Setup (UX Checklist):**

Design tokens, fonts, and color system must be baked into Tailwind config immediately after init — before any component development begins. This prevents default-pattern drift that requires later refactoring.

1. Configure `tailwind.config.ts` with zinc-based monochrome design tokens from UX spec
2. Set up Inter Variable + Noto Sans JP Variable + JetBrains Mono font stack in `globals.css` with `unicode-range` for automatic script switching
3. Override shadcn/ui `components.json` with project theme (dark chrome + light canvas palette)
4. Configure CSS custom properties for semantic color tokens (`--bg`, `--surface`, `--chrome-bg`, etc.)
5. Set up responsive breakpoints: mobile (<640px), tablet (640-1024px), desktop (>1024px)

**Frontend File Structure:**

```
src/
├── app/                   # Next.js App Router pages
├── components/
│   ├── ui/                # shadcn/ui components (auto-generated)
│   ├── review/            # ReviewCard, RatingButton, InsightCard
│   ├── collections/       # CollectionCard
│   ├── dashboard/         # DashCard, StatChip, ActivityChart
│   ├── onboarding/        # OnboardingStep
│   └── layout/            # Sidebar, Topbar
├── lib/                   # Utilities, API client
└── hooks/                 # Custom React hooks
```

### Selected Backend Starter: Custom Scaffold

**Rationale:** No existing template combines uv + Ruff + mypy + async SQLAlchemy 2.0 + Alembic async + Hexagonal/DDD module structure. Building from `uv init` with explicit dependency additions is more reliable than adapting a misaligned template. The DDD module structure (domain/application/infrastructure/api per bounded context) is non-negotiable for the 8-context architecture.

**Initialization Commands:**

```bash
uv init backend --python 3.12
cd backend

# Core dependencies
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings redis arq

# Dev dependencies
uv add --dev ruff mypy pytest pytest-asyncio pytest-mock httpx pre-commit

# Alembic async template
alembic init -t async alembic
```

**Architectural Decisions:**

- **Language & Runtime:** Python 3.12, async-native
- **Package Manager:** uv (10-100x faster than pip)
- **Linting & Formatting:** Ruff (replaces black + isort + flake8)
- **Type Checking:** mypy (strict mode)
- **Testing:** pytest + pytest-asyncio + pytest-mock + httpx.AsyncClient
- **ORM:** SQLAlchemy 2.0 async with asyncpg driver
- **Migrations:** Alembic async template
- **Background Tasks:** ARQ + Redis
- **Validation:** Pydantic v2 (triple-use: request/response, LLM tool schema, domain DTO)
- **Pre-commit:** Ruff + mypy hooks

**Backend File Structure:**

```
backend/
├── src/app/
│   ├── core/              # config, security, deps, middleware
│   ├── db/                # SQLAlchemy base, async session factory, migrations
│   ├── llm/               # LLM gateway (provider routing, caching, cost tracking)
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── api/
│   │   ├── vocabulary/    # (same shape)
│   │   ├── srs/           # (same shape)
│   │   ├── collections/   # (same shape)
│   │   ├── enrichment/    # (same shape)
│   │   ├── intent/        # (same shape)
│   │   ├── dictionary/    # (same shape)
│   │   └── dashboard/     # (same shape)
│   └── main.py            # app factory
├── tests/
│   ├── unit/              # domain + application (fast, no DB)
│   ├── integration/       # repository + DB (Postgres in CI)
│   └── e2e/               # full HTTP via AsyncClient
├── alembic/
├── pyproject.toml          # uv managed, ruff + mypy config
├── Dockerfile              # multi-stage, python:3.12-slim + uv
├── docker-compose.yml      # Postgres + Redis for local dev
└── .pre-commit-config.yaml # Ruff + mypy hooks
```

**Sprint 0 Validation Checklist:**

Before writing any feature code, validate the scaffold end-to-end:

1. Run one Alembic migration (create → alter → verify) against Postgres
2. Serve one health endpoint through FastAPI
3. Execute one pytest with async SQLAlchemy session fixture
4. Render one Next.js page with shadcn/ui component + design tokens applied
5. CI pipeline green: lint → typecheck → unit tests → build (GitHub Actions)

**Note:** Project initialization using these commands should be the first implementation story.

### Party Mode Review Summary

Starter template decisions were reviewed by Winston (Architect), Amelia (Dev), and Sally (UX):

- **Consensus:** All three agreed on `create-next-app` + shadcn/ui for frontend
- **Winston's input:** Custom backend scaffold is justified since no template fits, but validate quickly — "ship fast > perfect architecture"
- **Amelia's input:** Lock pre-commit rules, env config, and test fixtures immediately; add `pytest-mock`; CI skeleton in Sprint 0
- **Sally's input:** Design tokens + fonts + color system must be configured before any component development — UX setup checklist added above

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**

All critical decisions are now resolved. The following decisions were made collaboratively, building on existing technical research and PRD constraints.

**Deferred Decisions (Post-MVP):**

- Offline-first sync strategy (IndexedDB + service worker) — architecture accommodates but MVP ships online-only
- Browser extension architecture (Plasmo + MV3) — deferred to weeks 15-18
- CRDT for collaborative features (Yjs) — only needed for shared Study Group dashboards
- Knowledge graph storage (pgvector) — future feature
- Mobile native app architecture — web-first validation first

### Data Architecture

| Decision | Choice | Version | Rationale |
|----------|--------|---------|-----------|
| Primary database | PostgreSQL | 16 | Supports JSONB (FSRS state), ltree (hierarchical vocab), tsvector (full-text search), recursive CTEs |
| Database hosting | **Neon** | Serverless | Pure Postgres focus, instant copy-on-write branching for migration testing, native serverless driver for Vercel, MCP server + VS Code integration. No need for Supabase's BaaS features since auth uses Clerk. |
| Cache layer | Redis via **Upstash** | Serverless | ARQ job queue, LLM enrichment cache, rate-limit counters, session data. Pay-per-request, free tier sufficient for MVP. |
| ORM | SQLAlchemy 2.0 async | 2.0+ | asyncpg driver, async_sessionmaker, Depends() injection. Not SQLModel — need full control for hexagonal pattern. |
| Migrations | Alembic async template | Latest | `alembic init -t async`, async_engine_from_config. Zero-downtime: add nullable → backfill → add NOT NULL. CONCURRENTLY for indexes. |
| Data validation | Pydantic v2 | 2.x | Triple-use: request/response validators, LLM tool-input schemas, domain DTOs. Single source of truth. |
| FSRS state storage | JSONB on srs_cards | — | Algorithm evolution without schema migrations. Indexed `due_at` for fast "today's queue" queries. |
| Hierarchical vocab | Adjacency list (parent_id) | — | MVP start. Add ltree denormalized column later for fast subtree queries. Recursive CTEs sufficient at 3-5 level depth. |
| Full-text search | PostgreSQL tsvector | — | Command palette (⌘K) vocabulary search. Index on vocabulary_terms. |

**Caching Strategy (3 layers):**

| Layer | Technology | What It Caches | TTL |
|-------|-----------|---------------|-----|
| L1 (in-process) | Python LRU | JMdict lookups, hot user profiles | Process lifetime |
| L2 (distributed) | Upstash Redis | LLM enrichment results (key: hash of term+lang+level), rate-limit counters, ARQ job queue | 30 days (enrichment), sliding (sessions) |
| L3 (edge) | Vercel CDN | Static dictionary JSON shards, public collection data, font files | Long-lived, revalidate on deploy |

### Authentication & Security

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth provider | **Clerk** | Pre-built UI components save significant dev time for solo team. 10K free MAU sufficient for MVP. Excellent Next.js integration (<10 min setup). FastAPI verifies Clerk JWTs via middleware. |
| Token strategy | JWT — short-lived access (15 min) + refresh rotation | Standard Clerk flow. Access tokens verified in FastAPI Depends() middleware. |
| Authorization | Per-route scopes via FastAPI Security() | Scopes: `vocab:read`, `vocab:write`, `admin:read`. Extension and web app issued tokens with different scopes. |
| Tier gating | Middleware checks user tier from Clerk metadata | Free (50 active SRS cards, 5 LLM enrichments/day), Student, Professional. Enforced at API layer. |
| Rate limiting | SlowAPI + Redis | Per-user quotas on LLM endpoints. Auto-tighten when daily spend exceeds threshold. |
| API key security | Server-side only | LLM API keys never exposed to browser or extension. All LLM calls route through backend gateway. |
| Input validation | Pydantic constraints + prompt delimiters | min_length, max_length, Field(pattern=...). LLM prompts include explicit user-content delimiters to mitigate prompt injection. |
| Data privacy | GDPR-style export/delete from Day 1 | Encrypt at rest (Neon handles), never log full vocabulary content. Export and delete user data endpoints. |

### API & Communication Patterns

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API style | RESTful JSON | Standard HTTP endpoints. Easy to cache, mock, test. OpenAPI auto-generated by FastAPI. |
| LLM streaming | Server-Sent Events (SSE) | FastAPI StreamingResponse + text/event-stream. For chat-based intent parser responses. |
| API documentation | Auto-generated OpenAPI (Swagger/ReDoc) | FastAPI built-in. Frontend contract from OpenAPI spec. |
| Error handling | Structured error responses | `{error: string, code: string, details?: object}`. Never expose stack traces. Sentry captures full context server-side. |
| LLM gateway | Internal module (`app/llm/gateway.py`) | Single point for: provider routing (Claude Haiku ↔ Gemini Flash ↔ DeepSeek), prompt caching, retry/fallback, cost tracking, structured output validation via Pydantic. |
| Background processing | ARQ + Redis | Async-native, matches FastAPI's async def pattern. LLM enrichment queue, daily SRS queue pre-computation, corpus sync (Database Waterfall CronBot). |
| Cross-context events | Outbox pattern | `pending_events` table flushed by ARQ worker. E.g., CardMastered event → dashboard read model updates async. Avoids two-phase commit. |

### Frontend Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Server state | **TanStack Query** | Data fetching, caching, mutations, optimistic updates. Manages API data lifecycle. |
| Client state | **Zustand** | Review session state (current card, revealed/hidden, timer), UI state (sidebar collapsed, parallel mode). Fast, minimal (~2KB), no re-fetch triggers. |
| Component library | shadcn/ui + Radix UI primitives | Copy-paste ownership, built-in accessibility (ARIA, keyboard nav, focus management). Customized for bilingual card layouts. |
| Styling | Tailwind CSS v4 | Utility-first, CSS custom properties for design tokens, responsive prefixes, dark mode via class strategy. |
| Typography | Inter Variable + Noto Sans JP Variable + JetBrains Mono | Multi-script rendering via CSS unicode-range. Inter for Latin/Vietnamese, Noto Sans JP for Japanese, JetBrains Mono for IPA/code. |
| Routing | Next.js App Router | File-based routing, Server Components for static pages, Client Components for interactive review flow. |
| Performance | Turbopack (dev), Vercel Edge (prod) | Fast dev rebuilds. Edge caching for static dictionary lookups. |
| Accessibility | WCAG 2.1 AA | axe-core in CI (fails on violations), Lighthouse accessibility min 90, ESLint jsx-a11y plugin. Radix UI provides baseline. |

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend hosting | **Railway** | Simplest DX for solo team. Push-to-deploy from GitHub. Predictable pricing ($5/mo hobby + usage). Handles always-on ARQ workers well (no cold start). Docker support available but optional. |
| Frontend hosting | **Vercel** | Native Next.js platform. Edge caching, automatic preview deployments per PR. Free hobby tier. |
| Database | **Neon** (PostgreSQL 16) | Serverless, instant branching, free tier sufficient for MVP. |
| Redis | **Upstash** | Serverless, pay-per-request. ARQ queue + LLM cache + rate limits. Free tier for MVP. |
| CI/CD | **GitHub Actions** | lint (Ruff) → typecheck (mypy) → unit tests → integration tests (Postgres service container) → build Docker → deploy. |
| Error tracking | **Sentry** (free tier) | Python + JavaScript SDKs. PII scrubbing enabled. |
| Logging | **structlog** → JSON → Better Stack or Railway logs | Structured logging with request context. |
| Container | Multi-stage Docker | `python:3.12-slim` base, `uv` for dependency install. `gunicorn -k uvicorn.workers.UvicornWorker`. |
| Process model | gunicorn + uvicorn workers | `2*CPU+1` workers, async-native. |

**MVP Infrastructure Cost Estimate (100 active users):**

| Service | Cost/month |
|---------|-----------|
| Railway (backend, 2 services: API + ARQ worker) | $10-20 |
| Vercel (frontend, hobby) | $0 |
| Neon (PostgreSQL, free/pro) | $0-19 |
| Upstash (Redis, free tier) | $0 |
| Clerk (auth, <10K MAU) | $0 |
| Sentry (free tier) | $0 |
| LLM (with prompt caching + Batch API) | $5-15 |
| **Total** | **$15-54/month** |

### Decision Impact Analysis

**Implementation Sequence:**

1. **Sprint 0:** Project scaffold (frontend + backend), CI/CD pipeline, Neon DB + Upstash Redis provisioned, Clerk auth configured, design tokens applied
2. **Sprint 1-2:** Auth module (Clerk JWT verification in FastAPI), Vocabulary CRUD (first hexagonal vertical slice), first Alembic migration
3. **Sprint 3-4:** SRS engine (py-fsrs integration, JSONB state, daily queue endpoint), review flow frontend (ReviewCard + RatingButton)
4. **Sprint 5-6:** LLM gateway + enrichment pipeline (ARQ workers, structured outputs, JMdict cross-validation, prompt caching)
5. **Sprint 7-8:** Collections + CSV import, command palette (⌘K with tsvector search)
6. **Sprint 9-10:** Dashboard + diagnostics (TanStack Query for data, Zustand for UI state, progressive reveal logic)
7. **Sprint 11-12:** Pre-seeded corpus (LLM batch job), onboarding flow, polish
8. **Sprint 13-14:** Hardening, load testing, soft launch

**Cross-Component Dependencies:**

```
Clerk Auth ──→ All API endpoints (JWT middleware)
    │
    ├──→ Tier gating ──→ LLM rate limits
    │                     │
    │                     ▼
    │              LLM Gateway ──→ Enrichment pipeline
    │                     │         │
    │                     ▼         ▼
    │              Redis (Upstash) ←── ARQ workers
    │
    ▼
Neon (PostgreSQL) ←── SQLAlchemy async
    │
    ├──→ vocabulary module ──→ srs module ──→ dashboard module
    │         │
    │         ▼
    │    dictionary module (JMdict, read-only)
    │
    └──→ collections module
```

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 8 areas where AI agents could make different implementation choices. All resolved below.

### Naming Patterns

**Database Naming (PostgreSQL):**

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | snake_case, plural | `vocabulary_terms`, `srs_cards`, `srs_reviews` |
| Columns | snake_case | `created_at`, `fsrs_state`, `parent_id` |
| Foreign keys | `{referenced_table_singular}_id` | `user_id`, `term_id`, `collection_id` |
| Indexes | `ix_{table}_{column(s)}` | `ix_srs_cards_due_at`, `ix_vocabulary_terms_parent_id` |
| Unique constraints | `uq_{table}_{column(s)}` | `uq_users_email` |

**API Naming (REST):**

| Element | Convention | Example |
|---------|-----------|---------|
| Endpoints | snake_case, plural nouns | `/api/v1/vocabulary_terms`, `/api/v1/srs_cards` |
| Route params | snake_case | `/api/v1/vocabulary_terms/{term_id}` |
| Query params | snake_case | `?page_size=20&sort_by=due_at` |
| Versioning | URL prefix | `/api/v1/...` |
| Actions (non-CRUD) | Verb suffix | `/api/v1/srs_cards/{id}/review`, `/api/v1/collections/{id}/import` |

**Python Code (Backend):**

| Element | Convention | Example |
|---------|-----------|---------|
| Modules/packages | snake_case | `vocabulary`, `srs_engine` |
| Classes | PascalCase | `VocabularyTerm`, `SRSCard`, `EnrichmentService` |
| Functions/methods | snake_case | `get_due_cards()`, `schedule_review()` |
| Variables | snake_case | `term_id`, `review_count` |
| Constants | UPPER_SNAKE_CASE | `MAX_DAILY_ENRICHMENTS`, `FSRS_DEFAULT_PARAMS` |
| Pydantic models | PascalCase + suffix | `VocabularyTermCreate`, `SRSCardResponse`, `EnrichmentJobSchema` |
| Repository classes | `{Entity}Repository` | `VocabularyRepository`, `SRSCardRepository` |
| Service classes | `{Domain}Service` | `VocabularyEnrichmentService`, `ReviewSchedulingService` |
| FastAPI routers | `{module}_router` | `vocabulary_router`, `srs_router` |

**TypeScript/React Code (Frontend):**

| Element | Convention | Example |
|---------|-----------|---------|
| Components | PascalCase | `ReviewCard`, `RatingButton`, `InsightCard` |
| Component files | PascalCase.tsx | `ReviewCard.tsx`, `RatingButton.tsx` |
| Hooks | camelCase with `use` prefix | `useReviewSession`, `useDueCards` |
| Hook files | camelCase.ts | `useReviewSession.ts` |
| Utilities | camelCase | `formatInterval()`, `calculateMastery()` |
| Constants | UPPER_SNAKE_CASE | `RATING_LABELS`, `KEYBOARD_SHORTCUTS` |
| Types/interfaces | PascalCase | `VocabularyTerm`, `ReviewSession`, `DiagnosticInsight` |
| Zustand stores | `use{Domain}Store` | `useReviewStore`, `useUIStore` |
| TanStack Query keys | `{domain}Keys` object | `vocabularyKeys.list()`, `srsKeys.dueCards()` |

### Format Patterns

**API Response Formats:**

```json
// Success — direct data, no wrapper
{"id": 123, "term": "protocol", "language": "en", "created_at": "2026-05-04T10:30:00Z"}

// List — array with pagination metadata
{"items": [...], "total": 1234, "page": 1, "page_size": 20, "has_next": true}

// Error — consistent structure
{"error": {"code": "TERM_NOT_FOUND", "message": "Vocabulary term with id 999 not found", "details": null}}
```

**Data Exchange Conventions:**

- JSON field naming: **snake_case** (matches Python backend, frontend transforms via TanStack Query)
- Dates: ISO 8601 strings in UTC (`2026-05-04T10:30:00Z`)
- Null handling: include field with `null` value, never omit
- IDs: integer (PostgreSQL serial/bigserial)
- Booleans: `true`/`false` (never 1/0)
- Enums in API: lowercase strings (`"again"`, `"hard"`, `"good"`, `"easy"`)

### Structure Patterns

**Backend Module Structure (every bounded context follows this):**

```
modules/{context}/
├── domain/
│   ├── entities.py        # Domain entities (pure Python, no framework imports)
│   ├── value_objects.py   # Value objects
│   ├── exceptions.py      # Domain-specific exceptions
│   └── interfaces.py      # Repository interfaces (abstract classes)
├── application/
│   ├── services.py        # Use cases / orchestration
│   └── dtos.py            # Application-layer DTOs (if distinct from API schemas)
├── infrastructure/
│   ├── models.py          # SQLAlchemy ORM models
│   └── repository.py      # Repository implementations
└── api/
    ├── router.py           # FastAPI router
    ├── schemas.py          # Pydantic request/response models
    └── dependencies.py     # FastAPI Depends() for this module
```

**Rules:**

- `domain/` NEVER imports from `infrastructure/` or `api/` — dependency flows inward
- `infrastructure/` implements interfaces defined in `domain/`
- `api/schemas.py` may differ from `domain/entities.py` (API shape ≠ domain shape)
- One router per module, mounted in `main.py`

**Frontend Component Structure:**

```
src/components/{feature}/
├── ReviewCard.tsx          # Component
├── ReviewCard.test.tsx     # Co-located test
├── RatingButton.tsx
├── RatingButton.test.tsx
└── index.ts                # Barrel export
```

**Rules:**

- Frontend tests co-located with components (`.test.tsx` next to `.tsx`)
- Backend tests in separate `tests/` directory (unit/integration/e2e split)
- One component per file, named same as component
- Barrel exports (`index.ts`) per feature folder

### Communication Patterns

**Domain Events (Outbox pattern):**

```python
# Event naming: {Entity}{PastTenseVerb}
# Examples: CardReviewed, TermEnriched, CollectionCreated, CardMastered

# Event payload structure:
{
    "event_type": "CardReviewed",
    "occurred_at": "2026-05-04T10:30:00Z",
    "payload": {
        "card_id": 123,
        "user_id": 456,
        "rating": 3,
        "previous_state": {...},
        "new_state": {...}
    }
}
```

**Zustand Store Pattern:**

```typescript
// One store per domain concern, never one mega-store
// useReviewStore — review session state only
// useUIStore — sidebar, theme, parallel mode

interface ReviewStore {
  currentCardIndex: number
  isRevealed: boolean
  sessionCards: Card[]
  revealCard: () => void
  rateCard: (rating: 1 | 2 | 3 | 4) => void
  nextCard: () => void
}
```

**TanStack Query Pattern:**

```typescript
// Query key factory per domain
export const srsKeys = {
  all: ['srs'] as const,
  dueCards: () => [...srsKeys.all, 'due'] as const,
  card: (id: number) => [...srsKeys.all, 'card', id] as const,
}

// Mutations invalidate related queries
useMutation({
  mutationFn: reviewCard,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: srsKeys.dueCards() })
  }
})
```

### Process Patterns

**Error Handling:**

- Backend: Domain exceptions defined in `domain/exceptions.py`, translated to HTTP exceptions at the API layer boundary
- Frontend: TanStack Query global error handler + component-level onError callbacks
- Never show raw error messages to user — map to user-friendly text
- Never expose stack traces in API responses

**Loading States:**

- Use shadcn/ui `Skeleton` matching exact layout of loaded content
- Page-level: shell (sidebar + topbar) loads instantly, skeleton in content area only
- Button loading: spinner replaces text, button disabled, same width
- Never full-page spinner

**Authentication Flow:**

- Clerk handles all auth UI (sign-in, sign-up, user profile)
- Frontend: `useAuth()` hook from Clerk SDK, protect routes via middleware
- Backend: `get_current_user` dependency extracts user from Clerk JWT, raises 401 if invalid
- Every API endpoint receives `current_user` via `Depends(get_current_user)`

**Logging:**

```python
# structlog with bound context
import structlog
logger = structlog.get_logger()

# Always include: user_id, request_id, module
logger.info("card_reviewed", user_id=user.id, card_id=card.id, rating=rating)
logger.warning("enrichment_quota_exceeded", user_id=user.id, daily_count=count)
logger.error("llm_provider_failed", provider="anthropic", error=str(e))

# Levels: DEBUG (dev only), INFO (business events), WARNING (degraded), ERROR (failures)
# Never log: full vocabulary content, JWT tokens, LLM API keys
```

### Enforcement Guidelines

**All AI Agents MUST:**

1. Follow naming conventions exactly — no exceptions, no "creative" variations
2. Place code in the correct hexagonal layer (domain never imports infrastructure)
3. Use Pydantic models for all API boundaries — no raw dicts in/out of endpoints
4. Write co-located tests (frontend) or properly categorized tests (backend unit/integration/e2e)
5. Use `Depends()` for all injectable dependencies — never instantiate services directly in routes
6. Return consistent error response format — `{error: {code, message, details}}`
7. Use structlog with bound context — never `print()` or bare `logging`
8. Handle loading states with Skeleton components — never spinners or blank screens

**Pattern Verification:**

- Ruff + mypy in pre-commit catch naming/type violations
- ESLint jsx-a11y catches accessibility violations
- PR review checklist: hexagonal layer compliance, naming conventions, test coverage
- CI fails on: lint errors, type errors, test failures, accessibility violations

## Project Structure & Boundaries

### Complete Project Directory Structure

**Monorepo Root:**

```
table_project/
├── README.md
├── .github/
│   └── workflows/
│       ├── ci-backend.yml          # Ruff → mypy → pytest → Docker build
│       ├── ci-frontend.yml         # ESLint → tsc → vitest → next build
│       └── deploy.yml              # Railway (backend) + Vercel (frontend)
├── backend/                        # FastAPI Python backend
└── table-project-web/              # Next.js 16 frontend
```

**Backend — Full Structure:**

```
backend/
├── pyproject.toml                  # uv managed: deps, ruff config, mypy config, pytest config
├── uv.lock
├── Dockerfile                      # Multi-stage: python:3.12-slim + uv
├── docker-compose.yml              # Postgres 16 + Redis for local dev
├── .pre-commit-config.yaml         # Ruff + mypy hooks
├── .env.example                    # Template for local env vars
├── alembic/
│   ├── alembic.ini
│   ├── env.py                      # Async engine config
│   └── versions/                   # Migration files
├── scripts/
│   ├── seed_corpus.py              # One-time: LLM batch job for 3-5K pre-seeded terms
│   └── load_jmdict.py              # One-time: Load JMdict data for cross-validation
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory, router mounting, middleware
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py           # Pydantic Settings: env vars, tier limits, LLM keys
│       │   ├── security.py         # Clerk JWT verification, get_current_user dependency
│       │   ├── dependencies.py     # Shared Depends(): db session, current_user, rate limiter
│       │   ├── middleware.py       # Request ID, structlog binding, CORS, error handler
│       │   ├── exceptions.py       # Base app exceptions, HTTP exception mapper
│       │   └── logging.py          # structlog configuration
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py             # SQLAlchemy DeclarativeBase, common mixins (TimestampMixin)
│       │   ├── session.py          # async_sessionmaker, get_async_session dependency
│       │   └── events.py           # Outbox table model, event dispatcher
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── gateway.py          # Multi-provider router: Claude Haiku / Gemini Flash / DeepSeek
│       │   ├── providers/
│       │   │   ├── __init__.py
│       │   │   ├── anthropic.py    # Claude Haiku adapter
│       │   │   ├── google.py       # Gemini Flash adapter
│       │   │   └── deepseek.py     # DeepSeek adapter
│       │   ├── cache.py            # Redis-backed LLM result cache (hash of term+lang+level)
│       │   ├── cost_tracker.py     # Per-user daily cost tracking
│       │   └── schemas.py          # Pydantic: EnrichmentRequest, EnrichmentResult
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── arq_settings.py     # ARQ worker config, Redis connection
│       │   ├── enrichment_worker.py  # Process LLM enrichment queue
│       │   ├── srs_worker.py       # Daily SRS queue pre-computation
│       │   └── corpus_sync.py      # Database Waterfall: local → central corpus sync
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── auth/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # User, UserTier
│       │   │   │   ├── value_objects.py  # Tier (enum: free/student/professional)
│       │   │   │   └── exceptions.py     # AuthenticationError, AuthorizationError
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # UserProfileService (sync Clerk → local DB)
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── models.py         # SQLAlchemy: users table
│       │   │   │   └── repository.py     # UserRepository
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/auth/*, /api/v1/users/me
│       │   │       ├── schemas.py        # UserResponse, UserPreferencesUpdate
│       │   │       └── dependencies.py   # get_current_user, require_tier
│       │   ├── vocabulary/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # VocabularyTerm, VocabularyDefinition
│       │   │   │   ├── value_objects.py  # Language(en/jp), CEFRLevel, JLPTLevel
│       │   │   │   ├── exceptions.py     # TermNotFoundError, DuplicateTermError
│       │   │   │   └── interfaces.py     # VocabularyRepository (abstract)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # VocabularyService (CRUD, search, hierarchy)
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── models.py         # vocabulary_terms, vocabulary_definitions tables
│       │   │   │   └── repository.py     # VocabularyRepository (SQLAlchemy impl)
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/vocabulary_terms/*
│       │   │       ├── schemas.py        # TermCreate, TermResponse, TermSearchParams
│       │   │       └── dependencies.py
│       │   ├── srs/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # SRSCard, Review
│       │   │   │   ├── value_objects.py  # Rating(again/hard/good/easy), FSRSState
│       │   │   │   ├── exceptions.py     # CardNotDueError, FreeTierLimitError
│       │   │   │   └── interfaces.py     # SRSCardRepository (abstract)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # ReviewSchedulingService (py-fsrs integration)
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── models.py         # srs_cards (fsrs_state JSONB), srs_reviews tables
│       │   │   │   └── repository.py     # SRSCardRepository (due_at queries)
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/srs_cards/*, /api/v1/srs_cards/{id}/review
│       │   │       ├── schemas.py        # DueCardsResponse, ReviewRequest, ReviewResponse
│       │   │       └── dependencies.py
│       │   ├── collections/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # Collection, CollectionTerm
│       │   │   │   ├── exceptions.py     # CollectionNotFoundError
│       │   │   │   └── interfaces.py     # CollectionRepository (abstract)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # CollectionService (CRUD, CSV import)
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── models.py         # collections, collection_terms tables
│       │   │   │   └── repository.py     # CollectionRepository
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/collections/*, /api/v1/collections/{id}/import
│       │   │       ├── schemas.py        # CollectionCreate, CollectionResponse, CSVImportRequest
│       │   │       └── dependencies.py
│       │   ├── enrichment/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # EnrichmentJob, EnrichmentResult
│       │   │   │   ├── value_objects.py  # EnrichmentStatus(pending/processing/completed/failed)
│       │   │   │   ├── exceptions.py     # EnrichmentQuotaExceededError
│       │   │   │   └── interfaces.py     # EnrichmentRepository (abstract)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # VocabularyEnrichmentService (LLM orchestration)
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── models.py         # enrichment_jobs table
│       │   │   │   └── repository.py     # EnrichmentRepository
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/enrichments/*
│       │   │       ├── schemas.py        # EnrichmentRequest, EnrichmentResponse
│       │   │       └── dependencies.py
│       │   ├── intent/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # IntentResult, ParsedAction
│       │   │   │   └── value_objects.py  # IntentType(search/add/review/navigate)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # IntentParserService (LLM-based ⌘K intent parsing)
│       │   │   ├── infrastructure/
│       │   │   │   └── __init__.py
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/intent/parse (SSE streaming)
│       │   │       └── schemas.py        # IntentRequest, IntentResponse
│       │   ├── dictionary/
│       │   │   ├── __init__.py
│       │   │   ├── domain/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entities.py       # DictionaryEntry
│       │   │   │   └── interfaces.py     # DictionaryLookup (abstract)
│       │   │   ├── application/
│       │   │   │   ├── __init__.py
│       │   │   │   └── services.py       # JMdictValidationService
│       │   │   ├── infrastructure/
│       │   │   │   ├── __init__.py
│       │   │   │   └── jmdict_adapter.py # jamdict wrapper, LRU cached
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── router.py         # /api/v1/dictionary/lookup
│       │   │       └── schemas.py        # LookupRequest, LookupResponse
│       │   └── dashboard/
│       │       ├── __init__.py
│       │       ├── domain/
│       │       │   ├── __init__.py
│       │       │   ├── entities.py       # DiagnosticInsight, RetentionStats, LearningPattern
│       │       │   └── value_objects.py  # PatternType(time_of_day/category/cross_language)
│       │       ├── application/
│       │       │   ├── __init__.py
│       │       │   └── services.py       # DiagnosticsService, ProgressAnalyticsService
│       │       ├── infrastructure/
│       │       │   ├── __init__.py
│       │       │   ├── models.py         # Read models / materialized views for dashboard
│       │       │   └── repository.py     # DashboardRepository (read-optimized queries)
│       │       └── api/
│       │           ├── __init__.py
│       │           ├── router.py         # /api/v1/dashboard/*, /api/v1/diagnostics/*
│       │           ├── schemas.py        # DashboardStatsResponse, InsightResponse
│       │           └── dependencies.py
└── tests/
    ├── conftest.py                 # Shared fixtures: async session, test user, mock Redis
    ├── factories.py                # Factory Boy: UserFactory, TermFactory, CardFactory
    ├── unit/
    │   ├── modules/
    │   │   ├── auth/
    │   │   │   └── domain/
    │   │   │       └── test_entities.py
    │   │   ├── vocabulary/
    │   │   │   ├── domain/
    │   │   │   │   └── test_entities.py
    │   │   │   └── application/
    │   │   │       └── test_services.py
    │   │   ├── srs/
    │   │   │   ├── domain/
    │   │   │   │   └── test_entities.py      # FSRS state transitions
    │   │   │   └── application/
    │   │   │       └── test_services.py      # Review scheduling logic
    │   │   ├── enrichment/
    │   │   │   └── application/
    │   │   │       └── test_services.py      # LLM orchestration (mocked)
    │   │   └── dashboard/
    │   │       └── application/
    │   │           └── test_services.py      # Diagnostic pattern detection
    │   └── llm/
    │       ├── test_gateway.py               # Provider routing, fallback
    │       └── test_cost_tracker.py
    ├── integration/
    │   ├── modules/
    │   │   ├── vocabulary/
    │   │   │   └── test_repository.py        # Real Postgres
    │   │   ├── srs/
    │   │   │   └── test_repository.py        # due_at queries
    │   │   └── collections/
    │   │       └── test_repository.py        # CSV import
    │   └── llm/
    │       └── test_cache.py                 # Real Redis
    └── e2e/
        ├── test_auth_flow.py                 # Sign up → JWT → protected endpoint
        ├── test_review_flow.py               # Get due → review → rate → next
        └── test_enrichment_flow.py           # Request enrichment → LLM → JMdict validate → store
```

**Frontend — Full Structure:**

```
table-project-web/
├── package.json
├── pnpm-lock.yaml
├── next.config.ts
├── tailwind.config.ts              # Zinc palette, design tokens, responsive breakpoints
├── tsconfig.json
├── components.json                 # shadcn/ui config (dark chrome + light canvas theme)
├── .env.local.example              # NEXT_PUBLIC_CLERK_*, NEXT_PUBLIC_API_URL
├── .eslintrc.json                  # Next.js ESLint + jsx-a11y plugin
├── vitest.config.ts
├── public/
│   ├── fonts/
│   │   ├── inter-variable.woff2
│   │   ├── noto-sans-jp-variable.woff2
│   │   └── jetbrains-mono.woff2
│   └── icons/
│       └── favicon.ico
├── src/
│   ├── app/
│   │   ├── globals.css             # Tailwind directives, @font-face, CSS custom properties
│   │   ├── layout.tsx              # Root: ClerkProvider, QueryClientProvider, fonts
│   │   ├── page.tsx                # Landing / redirect to dashboard
│   │   ├── sign-in/
│   │   │   └── [[...sign-in]]/
│   │   │       └── page.tsx        # Clerk SignIn component
│   │   ├── sign-up/
│   │   │   └── [[...sign-up]]/
│   │   │       └── page.tsx        # Clerk SignUp component
│   │   ├── onboarding/
│   │   │   └── page.tsx            # 5-question survey → AI plan
│   │   ├── (app)/                  # Authenticated layout group
│   │   │   ├── layout.tsx          # Sidebar + Topbar + CommandPalette shell
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx        # Main command center dashboard
│   │   │   ├── review/
│   │   │   │   └── page.tsx        # SRS review session (keyboard-first flow)
│   │   │   ├── vocabulary/
│   │   │   │   ├── page.tsx        # Vocabulary browser / search
│   │   │   │   └── [termId]/
│   │   │   │       └── page.tsx    # Single term detail + enrichment
│   │   │   ├── collections/
│   │   │   │   ├── page.tsx        # My collections list
│   │   │   │   ├── [collectionId]/
│   │   │   │   │   └── page.tsx    # Collection detail + terms
│   │   │   │   └── import/
│   │   │   │       └── page.tsx    # CSV import
│   │   │   ├── diagnostics/
│   │   │   │   └── page.tsx        # Learning diagnostics dashboard
│   │   │   └── settings/
│   │   │       └── page.tsx        # User preferences + Clerk UserProfile
│   │   └── api/
│   │       └── clerk-webhook/
│   │           └── route.ts        # Clerk webhook → sync user data to backend
│   ├── components/
│   │   ├── ui/                     # shadcn/ui generated (Button, Card, Dialog, Skeleton, etc.)
│   │   ├── review/
│   │   │   ├── ReviewCard.tsx      # Bilingual card with flip animation
│   │   │   ├── ReviewCard.test.tsx
│   │   │   ├── RatingButton.tsx    # 1-4 difficulty rating
│   │   │   ├── RatingButton.test.tsx
│   │   │   ├── InsightCard.tsx     # Diagnostic micro-insertion every ~5 cards
│   │   │   ├── InsightCard.test.tsx
│   │   │   ├── ReviewSession.tsx   # Session orchestrator (Space→reveal, 1234→rate)
│   │   │   ├── ReviewSession.test.tsx
│   │   │   └── index.ts
│   │   ├── vocabulary/
│   │   │   ├── TermCard.tsx        # Vocabulary term display
│   │   │   ├── TermCard.test.tsx
│   │   │   ├── EnrichmentPanel.tsx # LLM enrichment trigger + result display
│   │   │   ├── EnrichmentPanel.test.tsx
│   │   │   ├── LanguageToggle.tsx  # Single-lang ↔ parallel mode (Tab key)
│   │   │   ├── LanguageToggle.test.tsx
│   │   │   └── index.ts
│   │   ├── collections/
│   │   │   ├── CollectionCard.tsx
│   │   │   ├── CollectionCard.test.tsx
│   │   │   ├── CSVImporter.tsx
│   │   │   ├── CSVImporter.test.tsx
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   │   ├── DashCard.tsx        # Stat card wrapper
│   │   │   ├── DashCard.test.tsx
│   │   │   ├── StatChip.tsx        # Small inline stat
│   │   │   ├── RetentionChart.tsx  # Retention curves
│   │   │   ├── ActivityCalendar.tsx # Daily/weekly calendar view
│   │   │   ├── ProgressiveInsight.tsx # Data-gated insight (Day 1 → Week 2+)
│   │   │   └── index.ts
│   │   ├── onboarding/
│   │   │   ├── OnboardingStep.tsx  # Survey step component
│   │   │   ├── LearningPlanCard.tsx # AI-generated plan display
│   │   │   └── index.ts
│   │   └── layout/
│   │       ├── Sidebar.tsx         # Desktop: 240px, tablet: 56px icons, mobile: hamburger
│   │       ├── Sidebar.test.tsx
│   │       ├── Topbar.tsx          # Breadcrumb + user menu
│   │       ├── CommandPalette.tsx   # ⌘K full-text search
│   │       ├── CommandPalette.test.tsx
│   │       └── index.ts
│   ├── hooks/
│   │   ├── useReviewSession.ts     # Review flow state machine
│   │   ├── useDueCards.ts          # TanStack Query: fetch due cards
│   │   ├── useVocabularySearch.ts  # TanStack Query: search + debounce
│   │   ├── useEnrichment.ts        # TanStack Mutation: trigger enrichment
│   │   ├── useKeyboardShortcuts.ts # Global hotkey registration
│   │   └── useProgressiveInsight.ts # Data-gated insight display logic
│   ├── stores/
│   │   ├── useReviewStore.ts       # Zustand: current card, revealed, session state
│   │   └── useUIStore.ts           # Zustand: sidebar collapsed, parallel mode, theme
│   ├── lib/
│   │   ├── api-client.ts           # Fetch wrapper: base URL, Clerk token injection, error handling
│   │   ├── query-client.ts         # TanStack QueryClient config (staleTime, gcTime, retries)
│   │   ├── query-keys.ts           # All query key factories (vocabularyKeys, srsKeys, etc.)
│   │   ├── utils.ts                # Date formatting, mastery calculation, cn() helper
│   │   └── constants.ts            # KEYBOARD_SHORTCUTS, RATING_LABELS, TIER_LIMITS
│   ├── types/
│   │   ├── vocabulary.ts           # VocabularyTerm, VocabularyDefinition
│   │   ├── srs.ts                  # SRSCard, Review, Rating, FSRSState
│   │   ├── collection.ts          # Collection, CollectionTerm
│   │   ├── dashboard.ts            # DiagnosticInsight, RetentionStats
│   │   ├── enrichment.ts           # EnrichmentJob, EnrichmentResult
│   │   └── api.ts                  # PaginatedResponse<T>, ApiError
│   └── middleware.ts               # Clerk auth middleware: protect /app/* routes
└── tests/
    └── e2e/                        # Playwright E2E tests (if added)
        └── review-flow.spec.ts
```

### Architectural Boundaries

**API Boundaries:**

| Boundary | Consumer → Provider | Contract |
|----------|-------------------|----------|
| Frontend → Backend | Next.js → FastAPI | REST JSON, `/api/v1/*`, Clerk JWT in Authorization header |
| Backend → LLM Providers | LLM Gateway → Claude/Gemini/DeepSeek | HTTP, provider-specific SDKs wrapped in gateway adapters |
| Backend → Neon | SQLAlchemy async → PostgreSQL | asyncpg connection pool, Alembic migrations |
| Backend → Upstash | Redis client → Redis | ARQ jobs, LLM cache, rate-limit counters |
| Backend → Clerk | JWT verification + webhook | Clerk SDK, JWKS public key validation |
| Frontend → Clerk | Clerk React SDK | Pre-built auth UI, useAuth() hook |

**Module Boundaries (Backend — Allowed Dependencies):**

```
auth          → (none — foundational, others depend on it)
vocabulary    → dictionary (JMdict validation)
srs           → vocabulary (term references)
collections   → vocabulary (term references)
enrichment    → vocabulary (write enriched data), dictionary (JMdict cross-check), llm/ (gateway)
intent        → llm/ (streaming intent parsing)
dictionary    → (none — read-only JMdict wrapper)
dashboard     → srs (review data), vocabulary (term data) — READ ONLY via repository queries
```

**Forbidden Dependencies:**

- No module imports another module's `infrastructure/` or `api/` layer directly
- Cross-module communication goes through application services or domain events (outbox)
- `dashboard` never writes to `srs` or `vocabulary` — strictly read models
- `dictionary` is a pure query module — no mutations, no domain events

**Component Boundaries (Frontend):**

| Boundary | Rule |
|----------|------|
| `components/ui/` | shadcn/ui primitives only — no business logic, no API calls |
| `components/{feature}/` | Feature components — may use hooks, but no direct fetch calls |
| `hooks/` | Data fetching + state logic — TanStack Query, Zustand, keyboard events |
| `stores/` | Client-only state — never triggers API calls directly (hooks do that) |
| `lib/api-client.ts` | Single point for all backend HTTP calls — Clerk token injection here |
| `types/` | Shared TypeScript interfaces — mirrors backend API schemas |

**Data Boundaries:**

| Data Domain | Owner Module | Storage | Access Pattern |
|-------------|-------------|---------|---------------|
| Users & profiles | auth | `users` table | Read: all modules via `get_current_user` dependency |
| Vocabulary terms & definitions | vocabulary | `vocabulary_terms`, `vocabulary_definitions` | Write: vocabulary, enrichment. Read: srs, collections, dashboard |
| SRS cards & reviews | srs | `srs_cards`, `srs_reviews` | Write: srs. Read: dashboard |
| Collections | collections | `collections`, `collection_terms` | Write: collections. Read: dashboard |
| Enrichment jobs | enrichment | `enrichment_jobs` | Write: enrichment. Read: enrichment only |
| Domain events | core (db/) | `pending_events` (outbox) | Write: any module. Read: ARQ worker |
| JMdict data | dictionary | In-memory (jamdict) + LRU cache | Read-only: enrichment, dictionary |
| LLM cache | llm/ | Upstash Redis | Write: llm/. Read: llm/ (transparent) |

### Requirements to Structure Mapping

| FR Group | Backend Modules | Frontend Routes & Components | Key Files |
|----------|----------------|------------------------------|-----------|
| **1. Authentication** | `modules/auth/` | `sign-in/`, `sign-up/`, `middleware.ts` | `security.py`, `Sidebar.tsx` (user menu) |
| **2. Onboarding** | `modules/auth/` (preferences), `modules/enrichment/` (AI plan) | `onboarding/page.tsx` | `OnboardingStep.tsx`, `LearningPlanCard.tsx` |
| **3. Core SRS Engine** | `modules/srs/` | `review/page.tsx` | `ReviewSession.tsx`, `ReviewCard.tsx`, `RatingButton.tsx`, `useReviewStore.ts` |
| **4. Bilingual Cards** | `modules/vocabulary/`, `modules/dictionary/` | `vocabulary/`, `review/` | `LanguageToggle.tsx`, `TermCard.tsx`, `jmdict_adapter.py` |
| **5. Diagnostics** | `modules/dashboard/` | `diagnostics/page.tsx`, `dashboard/` | `DiagnosticsService`, `ProgressiveInsight.tsx`, `InsightCard.tsx` |
| **6. Database Waterfall** | `modules/enrichment/`, `workers/`, `llm/` | `vocabulary/[termId]/` | `enrichment_worker.py`, `corpus_sync.py`, `EnrichmentPanel.tsx` |
| **7. Collections** | `modules/collections/` | `collections/` | `CollectionCard.tsx`, `CSVImporter.tsx` |
| **8. Progress Dashboard** | `modules/dashboard/` | `dashboard/page.tsx` | `DashCard.tsx`, `RetentionChart.tsx`, `ActivityCalendar.tsx` |
| **9. Pre-seeded Corpus** | `scripts/seed_corpus.py` | (N/A — backend batch job) | `seed_corpus.py`, `load_jmdict.py` |

### Integration Points

**Internal Communication:**

- **Synchronous (in-process):** Module A's service calls Module B's service via dependency injection. Example: `EnrichmentService` calls `DictionaryService.validate()` and `VocabularyService.update_definition()`.
- **Asynchronous (outbox → ARQ):** Domain events written to `pending_events` table, flushed by ARQ worker. Example: `CardMastered` event → dashboard read model update.

**External Integrations:**

| External Service | Integration Point | Backend File |
|-----------------|-------------------|-------------|
| Clerk (Auth) | JWT verification, webhook sync | `core/security.py`, `api/clerk-webhook/route.ts` |
| Claude Haiku API | LLM enrichment | `llm/providers/anthropic.py` |
| Gemini Flash API | LLM enrichment (fallback) | `llm/providers/google.py` |
| DeepSeek API | LLM enrichment (cost-optimized) | `llm/providers/deepseek.py` |
| Neon PostgreSQL | Primary data store | `db/session.py`, `alembic/` |
| Upstash Redis | Cache + queue | `llm/cache.py`, `workers/arq_settings.py` |
| Sentry | Error tracking | `core/middleware.py` |
| JMdict | JP definition validation | `modules/dictionary/infrastructure/jmdict_adapter.py` |

**Data Flow — Review Session:**

```
User presses Space → ReviewSession.tsx (Zustand: reveal card)
User presses 1-4 → useReviewSession hook → api-client.ts POST /api/v1/srs_cards/{id}/review
  → FastAPI router → ReviewSchedulingService.schedule_review()
    → py-fsrs calculates next state → SRSCardRepository.update()
    → Outbox: CardReviewed event
  → Response: next card data
  → TanStack Query cache update → ReviewSession renders next card
```

**Data Flow — Enrichment (Database Waterfall):**

```
User requests enrichment → EnrichmentPanel.tsx → POST /api/v1/enrichments/
  → EnrichmentService → check Redis cache (hit? return cached)
  → Cache miss → ARQ job queued → enrichment_worker.py
    → LLM Gateway → provider (Claude Haiku / Gemini Flash)
    → Pydantic validation → JMdictValidationService.validate()
    → VocabularyRepository.store_definition()
    → Redis cache write
    → corpus_sync (periodic) → central corpus DB
  → SSE stream or polling → EnrichmentPanel updates
```

### File Organization Patterns

**Configuration:**

- Backend: `.env` files for secrets, `core/config.py` (Pydantic Settings) for typed access. Never import `os.environ` directly.
- Frontend: `.env.local` for Clerk keys + API URL. `NEXT_PUBLIC_` prefix for client-side vars.
- Shared: `docker-compose.yml` for local Postgres + Redis. CI uses GitHub Actions service containers.

**Source Organization:**

- Backend: Vertical slices by bounded context (`modules/{context}/`). Shared infrastructure in `core/`, `db/`, `llm/`.
- Frontend: Routes in `app/`, components by feature, hooks by concern, types mirroring backend schemas.

**Test Organization:**

- Backend: `tests/unit/` (fast, no I/O) → `tests/integration/` (real Postgres/Redis) → `tests/e2e/` (full HTTP). Mirror module structure.
- Frontend: Co-located `.test.tsx` for unit tests. `tests/e2e/` for Playwright (post-MVP).

### Development Workflow Integration

**Local Development:**

```bash
# Terminal 1: Backend
cd backend && docker compose up -d  # Postgres + Redis
uv run uvicorn src.app.main:app --reload --port 8000

# Terminal 2: ARQ Worker
cd backend && uv run arq src.app.workers.arq_settings.WorkerSettings

# Terminal 3: Frontend
cd table-project-web && pnpm dev    # Next.js dev server on :3000
```

**CI Pipeline (GitHub Actions):**

```
backend:  ruff check → mypy → pytest (unit) → pytest (integration, Postgres service) → Docker build
frontend: eslint → tsc --noEmit → vitest → next build
deploy:   backend → Railway (Docker), frontend → Vercel (auto)
```

**Deployment:**

- Backend: Railway auto-deploys from `main` branch. Two services: API (gunicorn+uvicorn) + ARQ worker.
- Frontend: Vercel auto-deploys from `main`. Preview deployments per PR.
- Database migrations: `alembic upgrade head` runs as Railway deploy command before app starts.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**

All technology choices are mutually compatible with zero conflicts identified:

- FastAPI async + SQLAlchemy 2.0 async + asyncpg + Neon serverless — all async-native, shared event loop
- Clerk JWT + FastAPI `Depends()` middleware — standard pattern, Clerk JWKS verified server-side
- ARQ + Upstash Redis — ARQ is async-native, matches FastAPI's async def pattern
- Next.js 16 App Router + TanStack Query + Zustand — server state / client state cleanly separated
- shadcn/ui + Radix UI + Tailwind CSS v4 — complementary layers (primitives → components → styling)
- py-fsrs + JSONB storage — FSRS state natively serializable to JSON
- No contradictory decisions found

**Pattern Consistency:**

- Naming conventions are consistent and unambiguous: snake_case (Python/DB/API) ↔ PascalCase (React components/classes) ↔ camelCase (hooks/utils/JS variables)
- Hexagonal layer rule (domain never imports infrastructure) applied uniformly across all 8 bounded contexts
- Pydantic triple-use pattern consistent across enrichment pipeline
- Error response format `{error: {code, message, details}}` defined once, enforced everywhere
- Domain event naming (`{Entity}{PastTenseVerb}`) consistent with outbox pattern

**Structure Alignment:**

- Directory tree reflects hexagonal architecture (domain/application/infrastructure/api per module)
- Frontend routes map 1:1 with functional requirements
- Test structure (unit/integration/e2e) aligns with coverage targets (domain ≥90%, application ≥70%)
- CI pipeline enforces all defined patterns via Ruff, mypy, ESLint, axe-core

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**

| FR | Architectural Support | Status |
|----|----------------------|--------|
| 1. Authentication | Clerk + `modules/auth/` + JWT middleware + tier gating | ✅ Full |
| 2. Onboarding | `modules/auth/` (preferences) + `modules/enrichment/` (AI plan) + `onboarding/page.tsx` | ✅ Full |
| 3. Core SRS Engine | `modules/srs/` + py-fsrs + JSONB state + `review/page.tsx` + keyboard-first flow | ✅ Full |
| 4. Bilingual Cards | `modules/vocabulary/` + `modules/dictionary/` + `LanguageToggle.tsx` + unicode-range fonts | ✅ Full |
| 5. Diagnostics | `modules/dashboard/` + progressive reveal + `InsightCard.tsx` + ARQ background analytics | ✅ Full |
| 6. Database Waterfall | `modules/enrichment/` + `llm/gateway.py` + ARQ workers + Redis cache + JMdict validation | ✅ Full |
| 7. Collections | `modules/collections/` + CSV import + `collections/` routes | ✅ Full |
| 8. Progress Dashboard | `modules/dashboard/` + read models + TanStack Query + calendar views | ✅ Full |
| 9. Pre-seeded Corpus | `scripts/seed_corpus.py` + LLM batch job + JMdict cross-validation | ✅ Full |

**Non-Functional Requirements Coverage:**

| NFR | Target | Architectural Support | Status |
|-----|--------|----------------------|--------|
| API p95 < 200ms | Async handlers + connection pooling + Redis cache + Neon serverless | ✅ |
| LLM p95 < 3s | SSE streaming + multi-provider fallback + prompt caching | ✅ |
| LLM cost < $0.02/user/day | 3-layer cache (L1/L2/L3) + Batch API + provider routing | ✅ |
| Cache hit > 70% | Redis enrichment cache (30-day TTL) + LRU in-process + CDN | ✅ |
| Domain test ≥ 90% | Hexagonal isolation, domain layer has zero framework imports | ✅ |
| Error rate < 0.5% | Sentry + structlog + graceful degradation on LLM outage | ✅ |
| Enrichment satisfaction ≥ 85% | JMdict cross-validation + Pydantic structured outputs | ✅ |
| Time-to-first-review < 3 min | Pre-seeded corpus + minimal onboarding (5 questions) | ✅ |
| Infra ≤ $50/mo (100 users) | Cost estimate: $15-54/mo — within range | ✅ |

### Implementation Readiness Validation ✅

**Decision Completeness:**

- All technology choices documented with specific versions (Python 3.12, SQLAlchemy 2.0, Next.js 16, PostgreSQL 16, Tailwind v4)
- Initialization commands provided for both frontend and backend
- Sprint 0 validation checklist with 5 concrete acceptance criteria
- Code examples for all major patterns (domain events, Zustand stores, TanStack Query keys, structlog, error format)

**Structure Completeness:**

- Backend: 8 modules × 4 layers = 32 packages with detailed file listings
- Frontend: 7 component groups, 6 hooks, 2 stores, 6 type files, 10+ routes
- Test structure mirrors module structure for unit/integration/e2e
- CI/CD workflows defined for both frontend and backend

**Pattern Completeness:**

- 8 critical conflict points identified and resolved
- Enforcement guidelines: 8 mandatory rules for AI agents + 4 verification mechanisms
- Naming conventions cover all code elements (DB, API, Python, TypeScript)
- Process patterns complete: error handling, loading states, auth flow, logging

### Gap Analysis Results

**Critical Gaps:** None — all blocking decisions resolved.

**Important Gaps (non-blocking):**

1. **Database schema DDL not included** — Table column definitions will be created in Alembic migrations during implementation. Schema described textually (JSONB, parent_id, tsvector, etc.) is sufficient for architectural guidance.
2. **OpenAPI contract not pre-defined** — FastAPI auto-generates from Pydantic models, so explicit pre-definition is unnecessary.
3. **Monitoring/alerting thresholds** — Sentry configured, but specific alert rules are a post-MVP concern.

**Nice-to-Have Gaps:**

1. Load testing tool selection (k6/Locust) — deferred to Sprint 13-14
2. Backup/disaster recovery RTO/RPO — Neon handles backups natively
3. Feature flag system — tier gating sufficient for MVP

### Validation Issues Addressed

No critical or blocking issues found during validation. All architectural decisions are coherent, all requirements are covered, and implementation patterns are comprehensive enough for AI agents to implement consistently.

### Architecture Completeness Checklist

**Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — 16/16 checklist items passed, zero critical gaps, all 9 FR groups mapped to specific modules and files.

**Key Strengths:**

1. **Hexagonal discipline** — Clean dependency rules prevent spaghetti between 8 bounded contexts
2. **LLM cost architecture** — 3-layer cache + multi-provider routing + Batch API makes $0.02/user/day achievable
3. **Sprint 0 validation checklist** — Verifies scaffold end-to-end before any feature code
4. **Keyboard-first UX reflected in architecture** — Zustand for zero-latency state, pre-computed insights server-side
5. **Database Waterfall as data flywheel** — Clear pipeline from user request → LLM → JMdict → corpus → shared asset

**Areas for Future Enhancement:**

- Offline-first sync (IndexedDB + service worker) — architecture accommodates, MVP defers
- Browser extension (Plasmo + MV3) — weeks 15-18
- Knowledge graph visualization (pgvector) — future
- Mobile native apps — post-validation
- Multi-signal FSRS adaptation — Phase 2

### Implementation Handoff

**AI Agent Guidelines:**

- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries — especially hexagonal layer rules
- Refer to this document for all architectural questions
- When in doubt, check the naming conventions and structure patterns sections

**First Implementation Priority:**

```bash
# Sprint 0: Project Scaffold
# 1. Backend
uv init backend --python 3.12
cd backend
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings redis arq
uv add --dev ruff mypy pytest pytest-asyncio pytest-mock httpx pre-commit
alembic init -t async alembic

# 2. Frontend
pnpm create next-app table-project-web --typescript --tailwind --eslint --app --src-dir
cd table-project-web
npx shadcn@latest init

# 3. Validate: health endpoint → Alembic migration → pytest → shadcn component → CI green
```

