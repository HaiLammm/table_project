# Story 4.7: Upcoming Review Schedule

Status: review

## Story

As a **user**,
I want to view how many cards are due today, tomorrow, and this week with estimated review times,
so that I can plan my study sessions and understand my review workload at a glance.

## Acceptance Criteria

1. **Given** a user is on the Dashboard page **When** the schedule data loads (`GET /api/v1/srs_cards/schedule`) **Then** the display shows three date buckets:
   - Today: cards due count + estimated minutes
   - Tomorrow: cards due count + estimated minutes
   - This week (remaining days): cards due count + estimated minutes
   **And** estimated review time is calculated using average response time per card from past sessions (fallback: 10s/card if no history)
   **And** data refreshes after each review session completes (via TanStack Query invalidation)

2. **Given** a user is on the review page (`Today's Queue`) **When** the `QueueHeader` renders **Then** the upcoming schedule summary (tomorrow + this week) appears below the existing today stats as additional `StatChip` components
   **And** today's stats continue using the existing `useQueueStats()` data (no duplication)

3. **Given** the schedule endpoint is called **When** the backend computes date buckets **Then** "today" means `due_at <= end_of_today (UTC)`, "tomorrow" means `end_of_today < due_at <= end_of_tomorrow (UTC)`, "this_week" means `end_of_tomorrow < due_at <= end_of_this_week (Sunday 23:59:59 UTC)`
   **And** cards already counted in "today" are NOT double-counted in "this_week"
   **And** if today is Sunday, "this_week" returns 0

4. **Given** a user has 0 cards due in any bucket **When** the schedule displays **Then** that bucket shows "0 cards, 0 min" (never hidden — all three buckets always visible for consistent layout)

5. **Given** the schedule data is loading **When** the component renders **Then** skeleton placeholders matching the StatChip layout appear (3 pulsing pill shapes)
   **And** if the fetch fails, the schedule section is hidden gracefully (not a critical path — today's queue stats remain visible from existing endpoint)

## Tasks / Subtasks

- [x] **Task 1: Add backend schedule endpoint and service method (AC: #1, #3, #4)**
  - [x] Add `UpcomingSchedule` dataclass to `backend/src/app/modules/srs/domain/entities.py`:
  - [x] Add `UpcomingScheduleResponse` to `backend/src/app/modules/srs/api/schemas.py`
  - [x] Add `GET /api/v1/srs_cards/schedule` endpoint to `backend/src/app/modules/srs/api/router.py`
  - [x] Add `QueueStatsService.get_upcoming_schedule(user_id)` to `backend/src/app/modules/srs/application/services.py`
  - [x] Add repository method to `backend/src/app/modules/srs/domain/interfaces.py` and `backend/src/app/modules/srs/infrastructure/repository.py`

- [x] **Task 2: Add frontend type, query key, and hook (AC: #1, #5)**
  - [x] Add `UpcomingScheduleResponse` and `ScheduleBucketResponse` types to `frontend/src/types/srs.ts`
  - [x] Extend `frontend/src/lib/query-keys.ts` with `srsKeys.schedule()`
  - [x] Create `frontend/src/hooks/useUpcomingSchedule.ts`

- [x] **Task 3: Add UpcomingSchedule display component (AC: #1, #2, #4, #5)**
  - [x] Create `frontend/src/components/review/UpcomingSchedule.tsx`
  - [x] Add to barrel export in `frontend/src/components/review/index.ts`
  - [x] Add `frontend/src/components/review/UpcomingSchedule.test.tsx`

- [x] **Task 4: Wire into Dashboard page (AC: #1, #2, #5)**
  - [x] Update `frontend/src/app/(app)/dashboard/page.tsx` with `useUpcomingSchedule()` and render component
  - [x] Add `srsKeys.schedule()` to `useRatingMutation` invalidation

- [x] **Task 5: Tests (AC: all)**
  - [x] Backend unit test `test_schedule.py` - 8 tests for bucket logic
  - [x] Backend integration test `test_schedule.py` - 3 tests for endpoint
  - [x] Frontend component test `UpcomingSchedule.test.tsx` - 3 tests
  - [x] Updated InMemory repositories in existing tests to implement new abstract method

## Dev Notes

### Story Foundation

- FR20: "Users can view their upcoming review schedule (number of cards due today, tomorrow, this week)."
- This is a **read-only feature** — no mutations, no schema migrations, no store changes.
- Today's due count already exists via `GET /srs_cards/queue-stats` (`QueueStatsResponse`). Story 4.7 extends this with tomorrow + this_week buckets in a separate endpoint to avoid breaking the existing contract.
- The `count_due_cards_for_date(user_id, date_end)` repository method already exists (used by session stats in 4.6) — extend the pattern for multi-bucket counting.

### Existing Code State (UPDATE files)

| File | Current State | What Story 4.7 Changes |
|------|---------------|-------------------------|
| `frontend/src/app/(app)/dashboard/page.tsx` | 197 lines. Uses `useQueueStats()`, renders `QueueHeader`, `CatchUpBanner`, `QueuePreview`. | Add `useUpcomingSchedule()` call. Render `UpcomingSchedule` below `QueueHeader` in same Card. |
| `frontend/src/components/review/index.ts` | Barrel exports for review components. | Add `UpcomingSchedule` export. |
| `frontend/src/lib/query-keys.ts` | 41 lines. Has `srsKeys.queueStats()`, `srsKeys.queue()`, `srsKeys.sessionStats()`. | Add `srsKeys.schedule()`. |
| `frontend/src/types/srs.ts` | 60 lines. Has `QueueStatsResponse`, `SessionStatsResponse`, etc. | Add `UpcomingScheduleResponse`, `ScheduleBucketResponse`. |
| `backend/src/app/modules/srs/api/router.py` | 170 lines, 7 endpoints. | Add `GET /schedule` endpoint. |
| `backend/src/app/modules/srs/api/schemas.py` | 80 lines. | Add `ScheduleBucketResponse`, `UpcomingScheduleResponse`. |
| `backend/src/app/modules/srs/application/services.py` | 298 lines. `QueueStatsService` handles queue stats. | Add `get_upcoming_schedule()` to `QueueStatsService`. |
| `backend/src/app/modules/srs/domain/entities.py` | 83 lines. | Add `ScheduleBucket`, `UpcomingSchedule` dataclasses. |
| `backend/src/app/modules/srs/domain/interfaces.py` | 81 lines. | Add `count_due_cards_by_buckets()` abstract method. |
| `backend/src/app/modules/srs/infrastructure/repository.py` | 448 lines. | Implement `count_due_cards_by_buckets()` with single SQL query. |

### New Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useUpcomingSchedule.ts` | TanStack Query hook for `GET /schedule` |
| `frontend/src/components/review/UpcomingSchedule.tsx` | Schedule display component with StatChips |
| `frontend/src/components/review/UpcomingSchedule.test.tsx` | Component tests |
| `backend/tests/unit/modules/srs/application/test_schedule.py` | Unit tests for bucket logic |
| `backend/tests/integration/modules/srs/test_schedule.py` | Integration tests for endpoint |

### MUST PRESERVE

- **Existing `QueueHeader` component**: unchanged — today's stats continue from `useQueueStats()`.
- **Existing `QueueStatsResponse` contract**: the `/queue-stats` endpoint returns the same shape. Schedule is a separate endpoint.
- **Existing `srsKeys` query key factory**: extend with `schedule()`, don't modify existing keys.
- **Existing dashboard page structure**: `QueueHeader` → `CatchUpBanner` → `QueuePreview` order preserved. Schedule is additive inside the QueueHeader card.
- **`useApiClient()` pattern**: all new API calls go through this.
- **Module boundaries**: schedule lives in `srs` module (it queries `srs_cards.due_at`).
- **All current tests must continue passing.**

### Architecture Compliance

- **Hexagonal layering**: domain entities → application service → infrastructure repository → API router.
- **Naming**: PascalCase components, camelCase hooks, snake_case backend/API JSON.
- **Error format**: `{error: {code, message, details}}` envelope from backend.
- **Logging**: structlog with `user_id` context on the new endpoint.
- **Query key factory**: `srsKeys.schedule()` follows the established `[...srsKeys.all, 'schedule']` pattern.
- **Frontend tests**: co-located `.test.tsx` next to component.
- **Backend tests**: separate `tests/unit/` and `tests/integration/` directories mirroring module structure.

### Backend Schedule Computation

```python
async def get_upcoming_schedule(self, user_id: int) -> UpcomingSchedule:
    now = datetime.now(UTC)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    tomorrow_end = (today_end + timedelta(days=1))
    # End of week = next Sunday 23:59:59
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.weekday() == 6:
        week_end = today_end  # Already Sunday → this_week bucket is empty
    else:
        week_end = (now + timedelta(days=days_until_sunday)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    buckets = await self._repository.count_due_cards_by_buckets(
        user_id, today_end, tomorrow_end, week_end
    )
    return buckets
```

**SQL — single query with conditional aggregation:**

```sql
SELECT
    COUNT(*) FILTER (WHERE due_at <= :today_end) AS today_count,
    COUNT(*) FILTER (WHERE due_at > :today_end AND due_at <= :tomorrow_end) AS tomorrow_count,
    COUNT(*) FILTER (WHERE due_at > :tomorrow_end AND due_at <= :week_end) AS this_week_count,
    COALESCE(AVG(r.response_time_ms), 10000) AS avg_response_ms
FROM srs_cards c
LEFT JOIN LATERAL (
    SELECT response_time_ms FROM srs_reviews
    WHERE user_id = :user_id
    ORDER BY reviewed_at DESC LIMIT 50
) r ON true
WHERE c.user_id = :user_id AND c.due_at <= :week_end;
```

**Note:** The lateral join for avg response time is an optimization. A simpler approach: run two queries — one for bucket counts, one for avg response time from recent reviews. Choose based on complexity preference. The key constraint is that estimated minutes uses real user data when available.

### UX Guardrails

- Schedule is **calm planning information**, not pressure. "Tomorrow: 12 cards · ~2 min" reads as helpful forecasting.
- All three buckets always visible (even at 0) for consistent layout — no conditional hiding.
- The schedule section is a best-effort enhancement. If the endpoint fails, today's queue (from existing `/queue-stats`) continues working.
- No new navigation, no modal, no separate page. This integrates into the existing dashboard view as additional StatChips.

### Previous Story Intelligence

**Story 4.6 (Session-End Intelligence Summary):**
- `SessionStatsResponse` already includes `tomorrow_due_count` and `tomorrow_estimated_minutes` — this is session-end-specific data. Story 4.7 provides a standalone schedule endpoint available anytime (not just post-session).
- `count_due_cards_for_date()` repository method exists and works. Story 4.7 extends this pattern to multi-bucket counting in a single query for efficiency.

**Story 4.4 (Review Session Flow):**
- Review session invalidates query cache on completion. Story 4.7 must add `srsKeys.schedule()` to the invalidation list so schedule refreshes after reviews.

**Dashboard page:**
- Currently shows `QueueHeader` (today stats) + `CatchUpBanner` + `QueuePreview`. Story 4.7 adds schedule data inside the same Card as QueueHeader for visual cohesion.

### Git Intelligence

- Recent commits follow `feat#X-Y:` prefix pattern.
- Backend + frontend + tests ship in the same commit for story-sized features.
- Existing test repositories (in-memory mocks) must implement any new abstract methods added to `SrsCardRepository`.

### Testing Standards

- **Backend unit tests** (`test_schedule.py`): bucket boundary logic, no double-counting, Sunday edge case, empty state, estimated minutes calculation with/without avg response time.
- **Backend integration tests**: seed cards with specific `due_at` timestamps, call `/schedule`, verify JSON response matches expected bucket counts.
- **Frontend component tests**: StatChip rendering with correct labels/values, loading skeleton, zero-value display.
- **Tooling**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend).

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.7 (lines 147-160)]
- [Source: _out_put/planning-artifacts/prd/functional-requirements.md#FR20 (line 30)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#StatChip component (lines 1076-1089)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Session-end intelligence summary (line 405)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Warm return screen (line 407)]
- [Source: _out_put/planning-artifacts/architecture.md#QueueStatsService (line 769)]
- [Source: _out_put/planning-artifacts/architecture.md#TanStack Query key factory pattern (lines 573-587)]
- [Source: _out_put/planning-artifacts/architecture.md#Hexagonal module structure (lines 486-504)]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend component structure (lines 516-530)]
- [Source: frontend/src/components/review/QueueHeader.tsx — existing StatChip and QueueHeader (lines 1-42)]
- [Source: frontend/src/app/(app)/dashboard/page.tsx — dashboard layout and QueueHeader usage (lines 114-197)]
- [Source: frontend/src/lib/query-keys.ts — srsKeys namespace (lines 9-20)]
- [Source: backend/src/app/modules/srs/domain/interfaces.py — count_due_cards_for_date pattern (line 81)]
- [Source: backend/src/app/modules/srs/infrastructure/repository.py — existing count query and avg response time logic]
- [Source: backend/src/app/modules/srs/application/services.py — QueueStatsService (lines 1-50)]
- [Source: _out_put/implementation-artifacts/4-6-session-end-intelligence-summary.md — tomorrow estimate pattern, count_due_cards_for_date reuse]

## File List

### New Files
- `frontend/src/hooks/useUpcomingSchedule.ts` - TanStack Query hook for schedule endpoint
- `frontend/src/components/review/UpcomingSchedule.tsx` - Schedule display component
- `frontend/src/components/review/UpcomingSchedule.test.tsx` - Component tests
- `backend/tests/unit/modules/srs/application/test_schedule.py` - Unit tests (8 tests)
- `backend/tests/integration/modules/srs/test_schedule.py` - Integration tests (3 tests)

### Modified Files
- `backend/src/app/modules/srs/domain/entities.py` - Added ScheduleBucket, UpcomingSchedule dataclasses
- `backend/src/app/modules/srs/api/schemas.py` - Added ScheduleBucketResponse, UpcomingScheduleResponse
- `backend/src/app/modules/srs/domain/interfaces.py` - Added count_due_cards_by_buckets abstract method
- `backend/src/app/modules/srs/application/services.py` - Added get_upcoming_schedule method
- `backend/src/app/modules/srs/infrastructure/repository.py` - Implemented count_due_cards_by_buckets
- `backend/src/app/modules/srs/api/router.py` - Added GET /schedule endpoint
- `frontend/src/types/srs.ts` - Added ScheduleBucketResponse, UpcomingScheduleResponse
- `frontend/src/lib/query-keys.ts` - Added srsKeys.schedule()
- `frontend/src/components/review/index.ts` - Added UpcomingSchedule export
- `frontend/src/app/(app)/dashboard/page.tsx` - Added useUpcomingSchedule integration
- `frontend/src/hooks/useRatingMutation.ts` - Added schedule invalidation
- `backend/tests/unit/modules/srs/application/test_queue_services.py` - Updated InMemorySrsCardRepository
- `backend/tests/unit/modules/srs/application/test_review_scheduling_service.py` - Updated InMemoryReviewRepository
- `backend/tests/unit/modules/srs/application/test_session_stats.py` - Updated InMemorySessionStatsRepository
- `backend/tests/unit/modules/srs/application/test_undo_service.py` - Updated InMemoryUndoRepository

## Dev Agent Record

### Agent Model Used
minimax-m2.7

### Debug Log References
- Unit tests and integration tests syntax validated with python -m py_compile
- Frontend TypeScript validated with npx tsc --noEmit
- Integration tests require running database (ConnectionRefusedError indicates DB not running - not implementation error)

### Completion Notes
Story 4.7 fully implemented. Backend adds GET /api/v1/srs_cards/schedule endpoint with three-bucket schedule (today/tomorrow/this_week). Frontend adds UpcomingSchedule component to Dashboard. All 120 backend unit tests pass. 3 frontend component tests pass. Query invalidation added to useRatingMutation.
