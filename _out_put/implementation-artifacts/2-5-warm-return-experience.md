# Story 2.5: Warm Return Experience

Status: review

## Story

As a returning user,
I want the app to welcome me back without guilt messaging after any absence,
So that I feel comfortable returning to my learning at any time.

## Acceptance Criteria

1. **Neutral Queue Context Line**
   - Given a returning user opens the app (Today's Queue is the landing page)
   - When they have been absent for 1+ days
   - Then the queue displays a neutral context line: "{N} cards ready. ~{M} min estimated." per UX-DR22
   - And no streak-loss messaging, no "you missed X days" guilt
   - And FSRS has silently rescheduled cards during absence (overdue cards prioritized)

2. **Catch-Up Mode for Extended Absence**
   - Given a returning user has 100+ overdue cards after extended absence
   - When the queue loads
   - Then a "catch-up mode" suggestion appears: "You have {N} cards. We suggest starting with the 30 most overdue."
   - And the user can accept catch-up mode or review the full queue

## Tasks / Subtasks

### Backend

- [x] Task 1: Queue Stats API Endpoint (AC: #1)
  - [x] 1.1 Create `GET /api/v1/srs_cards/queue-stats` endpoint in `modules/srs/api/router.py` — returns `{ due_count, estimated_minutes, has_overdue, overdue_count }`
  - [x] 1.2 Add `QueueStatsService` in `modules/srs/application/services.py` — queries `srs_cards` where `due_at <= now()` for current user, calculates estimated time (~10 seconds/card)
  - [x] 1.3 Add `QueueStatsResponse` Pydantic schema in `modules/srs/api/schemas.py`
  - [x] 1.4 Add `SrsCardRepository.get_queue_stats(user_id)` in `modules/srs/infrastructure/repository.py` — single query: `SELECT COUNT(*), COUNT(*) FILTER (WHERE due_at < now() - interval '1 day') FROM srs_cards WHERE user_id = $1 AND due_at <= now()`
  - [x] 1.5 Mount SRS router in `main.py` with prefix `/api/v1/srs_cards`

- [x] Task 2: Catch-Up Mode Endpoint (AC: #2)
  - [x] 2.1 Create `GET /api/v1/srs_cards/queue?mode=catchup&limit=30` endpoint — returns the 30 most overdue cards sorted by `due_at ASC`
  - [x] 2.2 Create `GET /api/v1/srs_cards/queue` endpoint — returns full due queue sorted by `due_at ASC` with pagination
  - [x] 2.3 Add `QueueMode` enum value object: `full`, `catchup`
  - [x] 2.4 Add `DueCardsResponse` schema with pagination metadata

- [x] Task 3: Backend Tests (AC: #1, #2)
  - [x] 3.1 Unit tests for `QueueStatsService` — zero cards, normal queue, 100+ overdue
  - [x] 3.2 Integration tests for queue-stats and queue endpoints
  - [x] 3.3 Test catch-up mode returns exactly 30 most overdue cards

### Frontend

- [x] Task 4: Dashboard / Queue Landing Page (AC: #1)
  - [x] 4.1 Replace placeholder in `(app)/dashboard/page.tsx` with Today's Queue view
  - [x] 4.2 Create `QueueHeader.tsx` in `components/review/` — displays neutral context line: "{N} cards ready. ~{M} min estimated." Uses `StatChip` components
  - [x] 4.3 Add TanStack Query hook `useQueueStats()` fetching `GET /api/v1/srs_cards/queue-stats`
  - [x] 4.4 Add query keys: `srsKeys.all`, `srsKeys.queueStats()`, `srsKeys.queue(mode)`
  - [x] 4.5 Handle empty state: "All caught up! No cards due for review. Come back tomorrow or add new words." with "Add Words" action button

- [x] Task 5: Catch-Up Mode UI (AC: #2)
  - [x] 5.1 Create `CatchUpBanner.tsx` in `components/review/` — shown when `overdue_count >= 100`. Message: "You have {N} cards. We suggest starting with the 30 most overdue." Two buttons: "Start catch-up" (primary) and "Review all" (secondary)
  - [x] 5.2 Wire catch-up acceptance to `GET /api/v1/srs_cards/queue?mode=catchup&limit=30`
  - [x] 5.3 Store selected queue mode in Zustand `useReviewStore` — first Zustand store in the project

- [x] Task 6: Frontend Tests (AC: #1, #2)
  - [x] 6.1 Vitest tests for QueueHeader — renders correct count and time estimate
  - [x] 6.2 Vitest tests for CatchUpBanner — shows/hides based on overdue_count threshold
  - [x] 6.3 Vitest tests for empty state rendering

## Dev Notes

### Architecture Compliance

- **Hexagonal layers**: domain → application → infrastructure → api. Domain NEVER imports infrastructure.
- **SRS module**: Code goes in `modules/srs/` — already scaffolded with empty subdirectories (domain/, application/, infrastructure/, api/).
- **Dependency injection**: Use `Depends()` for all services. Follow auth module pattern.
- **Pydantic schemas**: All API boundaries use Pydantic v2 models. No raw dicts.
- **Error format**: `{"error": {"code": "...", "message": "...", "details": null}}`
- **Logging**: structlog only. Never `print()`. Never log PII.
- **API naming**: snake_case, plural nouns. `/api/v1/srs_cards/queue-stats`

### Critical Dependency Note

**This story does NOT require a full FSRS/SRS implementation.** The SRS data model and review engine are Epic 4 stories. This story only needs:
1. The `srs_cards` table to exist (create via Alembic migration with minimal schema: id, user_id, term_id, due_at, fsrs_state JSONB, created_at, updated_at)
2. A query that counts cards where `due_at <= now()`
3. A query that returns cards sorted by `due_at ASC`

The FSRS algorithm integration, review flow, and card rating are handled in Epic 4 stories (4-1 through 4-4). This story creates the **queue stats + catch-up mode** infrastructure that Epic 4 will build upon.

**Decision**: Create `srs_cards` table migration in this story with the minimal columns needed. Epic 4 Story 4-1 will extend it with full FSRS state columns if needed.

### Existing Code to Extend (UPDATE files)

| File | What to Add |
|------|-------------|
| `frontend/src/app/(app)/dashboard/page.tsx` | Replace "Coming soon" placeholder with Today's Queue view |
| `frontend/src/lib/query-keys.ts` | Add `srsKeys` query key factory |
| `backend/src/app/main.py` | Mount SRS router |

### New Files

| File | Purpose |
|------|---------|
| `backend/src/app/modules/srs/domain/entities.py` | SrsCard dataclass (minimal) |
| `backend/src/app/modules/srs/domain/value_objects.py` | QueueMode enum |
| `backend/src/app/modules/srs/domain/interfaces.py` | SrsCardRepository interface |
| `backend/src/app/modules/srs/domain/exceptions.py` | SRS domain exceptions |
| `backend/src/app/modules/srs/application/services.py` | QueueStatsService |
| `backend/src/app/modules/srs/infrastructure/models.py` | SrsCardModel (SQLAlchemy) |
| `backend/src/app/modules/srs/infrastructure/repository.py` | SqlAlchemySrsCardRepository |
| `backend/src/app/modules/srs/api/router.py` | Queue stats + queue endpoints |
| `backend/src/app/modules/srs/api/schemas.py` | QueueStatsResponse, DueCardsResponse |
| `backend/src/app/modules/srs/api/dependencies.py` | get_current_user, service DI |
| `backend/alembic/versions/xxx_add_srs_cards_table.py` | srs_cards table migration |
| `frontend/src/components/review/QueueHeader.tsx` | Neutral context line display |
| `frontend/src/components/review/CatchUpBanner.tsx` | Catch-up mode suggestion |
| `frontend/src/components/review/index.ts` | Barrel exports |
| `frontend/src/stores/review-store.ts` | First Zustand store — queue mode state |

### SRS Cards Table Schema (Minimal for this story)

```sql
CREATE TABLE srs_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    term_id INTEGER,  -- nullable until vocabulary module exists
    due_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    fsrs_state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_srs_cards_user_id_due_at ON srs_cards (user_id, due_at);
```

### UX Requirements

- **Neutral tone**: No guilt, no streaks, no "you missed X days". Only: "{N} cards ready. ~{M} min estimated."
- **Empty state**: Centered vertically. Icon ✓ (40px, text-zinc-400). Title: "All caught up!" (lg semibold). Description: "No cards due for review. Come back tomorrow or add new words." Action: "Add Words" button (primary).
- **Catch-up banner**: Appears inline above queue content when `overdue_count >= 100`. Not a modal. Two buttons: "Start catch-up" (primary bg-zinc-900) and "Review all" (secondary outlined).
- **Estimated time**: Calculate as `Math.ceil(due_count * 10 / 60)` minutes (10 seconds per card average).
- **Queue header**: Use `StatChip` component pattern from UX spec — compact inline stats.
- **Responsive**: Content area max 720px centered. Mobile-friendly with touch targets 44px minimum.

### Anti-Patterns to Avoid

- Do NOT add streak counters or streak-loss messaging anywhere
- Do NOT show "Welcome back!" or "You've been away for X days" — just show the queue
- Do NOT implement the full review flow (Space to reveal, rating) — that's Epic 4
- Do NOT implement FSRS algorithm — that's Story 4-1
- Do NOT create a separate "return" page or route — the dashboard IS the warm return
- Do NOT use localStorage for queue state — Zustand store syncs with server via TanStack Query
- Do NOT add the vocabulary_terms table — that's Epic 3

### Previous Story Intelligence (Story 2-4)

- **Backend pattern**: Services follow hexagonal architecture. DI via `Depends()`. Repository pattern with SQLAlchemy async.
- **Frontend pattern**: TanStack Query for server state, Zustand for UI state (stores/ dir exists but empty — this story creates the first store).
- **Query keys**: `frontend/src/lib/query-keys.ts` has `userKeys` factory. Add `srsKeys` following same pattern.
- **Testing**: Vitest with jsdom for frontend (fixed in fe36b8c). pytest + httpx.AsyncClient for backend.
- **Alembic**: Async template. Migrations in `backend/alembic/versions/`.

### Zustand Store Pattern (First Store)

Follow architecture spec pattern:
```typescript
// frontend/src/stores/review-store.ts
import { create } from 'zustand'

interface ReviewStore {
  queueMode: 'full' | 'catchup'
  setQueueMode: (mode: 'full' | 'catchup') => void
}

export const useReviewStore = create<ReviewStore>((set) => ({
  queueMode: 'full',
  setQueueMode: (mode) => set({ queueMode: mode }),
}))
```

### References

- [Source: _out_put/planning-artifacts/epics/epic-2-user-authentication-onboarding-profile.md — Story 2.5]
- [Source: _out_put/planning-artifacts/architecture.md — SRS Module, Zustand Stores, TanStack Query, API Patterns]
- [Source: _out_put/planning-artifacts/ux-design-specification.md — Warm Return UI, Empty States, Dashboard, UX-DR22]
- [Source: _out_put/implementation-artifacts/2-4-data-export-account-deletion.md — Previous Story Patterns]
- [Source: frontend/src/lib/query-keys.ts — Existing query key factory]
- [Source: frontend/src/app/(app)/dashboard/page.tsx — Current placeholder to replace]

## Dev Agent Record

### Agent Model Used

gpt-5.4

### Debug Log References

- `cd frontend && pnpm add zustand`
- `cd frontend && pnpm test`
- `cd frontend && pnpm lint`
- `cd frontend && pnpm build`
- `cd backend && uv run pytest tests/unit`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy`
- `cd backend && docker compose up -d postgres redis`
- `cd backend && uv run pytest`
- `cd backend && docker compose down`

### Completion Notes List

- Added the first `modules/srs/` implementation slice with a minimal `srs_cards` table, queue domain types, SQLAlchemy repository queries, queue stats service, and `/api/v1/srs_cards/queue-stats` plus `/api/v1/srs_cards/queue` endpoints so the app can measure due work without implementing the full review engine.
- Implemented catch-up mode by clamping `mode=catchup` requests to the 30 most overdue cards sorted by `due_at ASC`, while keeping paginated full-queue access for normal review loading.
- Replaced the dashboard placeholder with a real Today&apos;s Queue experience and reused it for the authenticated landing page `/`, including the neutral context line, empty state, queue preview, and an inline catch-up banner with no streak or guilt messaging.
- Added the first Zustand store in the repo for queue mode selection, introduced `srsKeys` TanStack Query keys, and added `zustand` to the frontend dependency set via `pnpm`.
- Added backend unit/e2e coverage and frontend Vitest coverage for queue stats, queue pagination, catch-up selection thresholding, and empty-state rendering; backend pytest, backend ruff, backend mypy, frontend test, frontend lint, and frontend build all passed. The existing Next.js middleware deprecation warning remains unchanged.

### File List

- `_out_put/implementation-artifacts/2-5-warm-return-experience.md`
- `_out_put/implementation-artifacts/sprint-status.yaml`
- `backend/alembic/versions/5c2e3a4f9b11_add_srs_cards_table.py`
- `backend/src/app/main.py`
- `backend/src/app/modules/srs/api/dependencies.py`
- `backend/src/app/modules/srs/api/router.py`
- `backend/src/app/modules/srs/api/schemas.py`
- `backend/src/app/modules/srs/application/services.py`
- `backend/src/app/modules/srs/domain/entities.py`
- `backend/src/app/modules/srs/domain/exceptions.py`
- `backend/src/app/modules/srs/domain/interfaces.py`
- `backend/src/app/modules/srs/domain/value_objects.py`
- `backend/src/app/modules/srs/infrastructure/models.py`
- `backend/src/app/modules/srs/infrastructure/repository.py`
- `backend/tests/e2e/test_srs_queue_flow.py`
- `backend/tests/unit/modules/srs/application/test_queue_services.py`
- `frontend/package.json`
- `frontend/pnpm-lock.yaml`
- `frontend/src/app/(app)/dashboard/page.test.tsx`
- `frontend/src/app/(app)/dashboard/page.tsx`
- `frontend/src/app/(app)/page.tsx`
- `frontend/src/components/review/CatchUpBanner.test.tsx`
- `frontend/src/components/review/CatchUpBanner.tsx`
- `frontend/src/components/review/QueueHeader.test.tsx`
- `frontend/src/components/review/QueueHeader.tsx`
- `frontend/src/components/review/index.ts`
- `frontend/src/lib/query-keys.ts`
- `frontend/src/stores/review-store.ts`

### Change Log

- 2026-05-06: Implemented Story 2.5 warm return queue infrastructure across backend SRS APIs, minimal data model migration, Today&apos;s Queue dashboard/landing UI, catch-up mode state, and automated tests; story is ready for review.
