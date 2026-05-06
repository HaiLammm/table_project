# Story 4.1: SRS Data Model & FSRS Integration

Status: done

## Story

As the **system**,
I want SRS cards with FSRS state stored as JSONB and a daily review queue computed by the scheduling algorithm,
so that users receive optimally-spaced reviews based on proven memory science.

## Acceptance Criteria

1. **Given** the SRS module is initialized **When** Alembic migration runs **Then** `srs_cards` table has: id, user_id, term_id, language (en/jp), fsrs_state (JSONB), due_at, stability, difficulty, reps, lapses, created_at, updated_at
2. **Given** the SRS module is initialized **When** Alembic migration runs **Then** `srs_reviews` table is created with: id, card_id, user_id, rating (1-4), reviewed_at, response_time_ms, session_id
3. **Given** the SRS module is initialized **When** migration runs **Then** index exists on `srs_cards(user_id, due_at)` for fast queue queries
4. **Given** the system **When** py-fsrs library is integrated **Then** the SRS domain service uses py-fsrs `Scheduler` for all scheduling calculations
5. **Given** a user requests due cards **When** `GET /api/v1/srs_cards/due` is called **Then** cards return prioritized: overdue > due > new
6. **Given** a user with up to 10,000 cards **When** queue computation runs **Then** it completes within 100ms (NFR7)
7. **Given** a user adds a vocabulary term to SRS **When** the SRS card is created **Then** FSRS state is initialized with default parameters and card appears in next review queue
8. **Given** a bilingual term **When** SRS cards are created **Then** retention is tracked per language independently (FR19)

## Tasks / Subtasks

- [x] Task 1: Add py-fsrs dependency (AC: #4)
  - [x] `uv add fsrs` to backend/pyproject.toml
- [x] Task 2: Create Alembic migration for srs_cards schema changes (AC: #1, #3)
  - [x] Add columns: language (varchar 5, NOT NULL, default 'en'), stability (float), difficulty (float), reps (int, default 0), lapses (int, default 0)
  - [x] Verify existing index `ix_srs_cards_user_id_due_at` is preserved
  - [x] Add check constraint for language IN ('en', 'jp')
- [x] Task 3: Create Alembic migration for srs_reviews table (AC: #2)
  - [x] Create table: id (serial PK), card_id (FK→srs_cards.id CASCADE), user_id (FK→users.id CASCADE), rating (int, check 1-4), reviewed_at (timestamptz, default now()), response_time_ms (int, nullable), session_id (uuid, nullable)
  - [x] Add index: `ix_srs_reviews_card_id`, `ix_srs_reviews_user_id`
- [x] Task 4: Update SrsCardModel (AC: #1)
  - [x] Add language, stability, difficulty, reps, lapses columns to SQLAlchemy model
  - [x] Add check constraint for language
- [x] Task 5: Create SrsReviewModel (AC: #2)
  - [x] New SQLAlchemy model in `srs/infrastructure/models.py`
- [x] Task 6: Update domain entities (AC: #4, #7, #8)
  - [x] Add language, stability, difficulty, reps, lapses to SrsCard entity
  - [x] Add Rating value object (using StrEnum mapping to py-fsrs Rating)
  - [x] Add Review entity (card_id, user_id, rating, reviewed_at, response_time_ms, session_id)
  - [x] Add FSRSState helper for serializing py-fsrs Card ↔ JSONB
- [x] Task 7: Update repository interfaces (AC: #5, #7)
  - [x] Add `create_card(card: SrsCard) -> SrsCard`
  - [x] Add `update_card(card: SrsCard) -> SrsCard`
  - [x] Add `get_card_by_id(card_id: int, user_id: int) -> SrsCard | None`
  - [x] Add `create_review(review: Review) -> Review`
  - [x] Update `list_due_cards` to order: overdue first, then due, then new (by due_at ASC)
- [x] Task 8: Implement SRS service with py-fsrs (AC: #4, #5, #6, #7, #8)
  - [x] Create `ReviewSchedulingService` that wraps py-fsrs `Scheduler`
  - [x] Implement `create_card_for_term(user_id, term_id, language)` — initializes FSRS Card, serializes to JSONB
  - [x] Implement `review_card(card_id, user_id, rating, response_time_ms, session_id)` — calls scheduler.review_card(), persists new state + review log
  - [x] Keep existing `QueueStatsService` — update to use new fields for estimated_minutes
- [x] Task 9: Update/add API endpoints (AC: #5, #7)
  - [x] Add `POST /api/v1/srs_cards` — create SRS card for a term
  - [x] Add `POST /api/v1/srs_cards/{id}/review` — review a card (rating, response_time_ms, session_id)
  - [x] Update existing `GET /api/v1/srs_cards/queue` — ensure overdue>due>new ordering
  - [x] Update `GET /api/v1/srs_cards/queue-stats` — include estimated time from avg review data
  - [x] Add `GET /api/v1/srs_cards/due` as alias for queue (matches AC wording)
- [x] Task 10: Update API schemas (AC: all)
  - [x] `CreateSrsCardRequest` — term_id (int), language ('en'|'jp')
  - [x] `CreateSrsCardResponse` — full card response
  - [x] `ReviewCardRequest` — rating (1-4), response_time_ms (int, optional), session_id (uuid, optional)
  - [x] `ReviewCardResponse` — updated card state + next_due_at + interval display string
  - [x] Update `DueCardResponse` to include language, stability, difficulty, reps, lapses
- [x] Task 11: Write unit tests (AC: #4, #7, #8)
  - [x] Test FSRS state initialization (new card defaults)
  - [x] Test review_card with each rating (Again/Hard/Good/Easy) — verify state transitions
  - [x] Test per-language card creation (en vs jp for same term)
  - [x] Test queue ordering logic (overdue > due > new)
- [x] Task 12: Write integration tests (AC: #1, #2, #5, #6)
  - [x] Test create card → review → verify updated due_at in DB
  - [x] Test due queue returns cards in correct priority order
  - [x] Test queue performance with seeded data (100ms target)

### Review Findings

- [x] [Review][Patch] Review flow commits card state and review log separately, so a failed `create_review()` can advance scheduling without a matching audit row [backend/src/app/modules/srs/application/services.py:143]
- [x] [Review][Patch] Concurrent reviews can both pass the due check and overwrite each other because the card row is read and updated without locking or version checks [backend/src/app/modules/srs/application/services.py:105]
- [x] [Review][Patch] Duplicate-card protection exists only as a pre-insert lookup; without a DB unique constraint, concurrent create requests can still insert duplicate `(user_id, term_id, language)` cards [backend/src/app/modules/srs/infrastructure/repository.py:38]
- [x] [Review][Patch] Legacy `srs_cards` rows are not backfilled during migration, so empty/incomplete `fsrs_state` falls back to a fresh FSRS card on first review and loses prior schedule state [backend/alembic/versions/2e7d2c4c9f10_expand_srs_cards_with_fsrs_reviews.py:25]
- [x] [Review][Patch] Queue ordering still relies only on `due_at ASC`, which lets stale unreviewed "new" cards appear before reviewed due cards and violates overdue > due > new ordering [backend/src/app/modules/srs/infrastructure/repository.py:194]
- [x] [Review][Patch] Integration tests recreate schema with `Base.metadata.create_all()` instead of running Alembic, so AC1-AC3 migration behavior and index preservation are still unverified [backend/tests/integration/modules/srs/test_repository.py:18]

## Dev Notes

### Critical: py-fsrs Integration Pattern

**Library:** `fsrs` v6.3.1 (PyPI package name: `fsrs`)

```python
from fsrs import Scheduler, Card, Rating

scheduler = Scheduler()  # uses default FSRS-6 parameters

# Create new card
card = Card()  # immediately due

# Review card
card, review_log = scheduler.review_card(card, Rating.Good)

# Serialize for JSONB storage
json_str = card.to_json()

# Deserialize from JSONB
card = Card.from_json(json_str)
```

**FSRS State → JSONB mapping:** Store the entire `Card` object as JSON via `card.to_json()`. The Card object contains: due, stability, difficulty, elapsed_days, scheduled_days, reps, lapses, state, last_review. Also persist `stability`, `difficulty`, `reps`, `lapses` as top-level DB columns for query/reporting without JSON parsing.

**Rating enum mapping:**
- `Rating.Again` (1) — forgot
- `Rating.Hard` (2) — struggled
- `Rating.Good` (3) — hesitated
- `Rating.Easy` (4) — effortless

### Existing Code State (UPDATE files)

The SRS module already has a working scaffold. Key files to UPDATE (not create):

| File | Current State | What Changes |
|------|--------------|-------------|
| `backend/src/app/modules/srs/infrastructure/models.py` | SrsCardModel with id, user_id, term_id, due_at, fsrs_state | Add language, stability, difficulty, reps, lapses columns. Add SrsReviewModel class. |
| `backend/src/app/modules/srs/domain/entities.py` | SrsCard dataclass (basic), QueueStats, DueCardsPage | Add language, stability, difficulty, reps, lapses fields. Add Review entity. |
| `backend/src/app/modules/srs/domain/value_objects.py` | QueueMode enum only | Add Rating StrEnum (again/hard/good/easy mapping to 1-4) |
| `backend/src/app/modules/srs/domain/interfaces.py` | SrsCardRepository with get_queue_stats, list_due_cards | Add create_card, update_card, get_card_by_id, create_review methods |
| `backend/src/app/modules/srs/infrastructure/repository.py` | SqlAlchemySrsCardRepository (read-only) | Implement new write methods, update list_due_cards for priority ordering |
| `backend/src/app/modules/srs/application/services.py` | QueueStatsService (read-only) | Add ReviewSchedulingService with py-fsrs integration |
| `backend/src/app/modules/srs/api/router.py` | GET /queue-stats, GET /queue | Add POST / (create card), POST /{id}/review, GET /due alias |
| `backend/src/app/modules/srs/api/schemas.py` | QueueStatsResponse, DueCardResponse, DueCardsResponse | Add request/response schemas for create and review |
| `backend/src/app/modules/srs/api/dependencies.py` | get_queue_stats_service only | Add get_review_scheduling_service |
| `backend/src/app/modules/srs/domain/exceptions.py` | SrsDomainError base class only | Add CardNotFoundError, CardNotDueError, DuplicateCardError |

### MUST PRESERVE

- Existing `GET /queue-stats` and `GET /queue` endpoints continue to work
- SrsDomainError exception handler in `main.py` already registered
- SRS router mounted at `/api/v1/srs_cards` in `main.py`
- `QueueMode` (FULL/CATCHUP) logic in `QueueStatsService.get_due_cards`
- Overdue cutoff = `now - timedelta(days=1)` in existing queue stats

### Queue Priority Ordering

The existing `list_due_cards` orders by `due_at ASC, id ASC`. This naturally puts overdue cards first. For "new" cards (never reviewed, due_at = creation time), they appear after overdue/due cards since their due_at is more recent. No special ordering change needed — the current ordering already satisfies overdue > due > new.

### Architecture Compliance

- **Hexagonal layers:** domain/ never imports infrastructure/ or api/
- **Domain entities:** Pure Python dataclasses, no SQLAlchemy imports
- **Repository pattern:** Abstract interface in domain/interfaces.py, implementation in infrastructure/repository.py
- **Dependency injection:** All services injected via FastAPI Depends() in api/dependencies.py
- **Pydantic for API boundaries:** Request/response schemas in api/schemas.py
- **Naming:** snake_case for DB/API/Python, table names plural (`srs_cards`, `srs_reviews`)
- **Error format:** `{error: {code, message, details}}` via `build_error_payload`
- **Logging:** structlog with bound context (user_id, card_id, rating)

### Database Conventions

- FK naming: `{referenced_table_singular}_id` → `user_id`, `card_id`, `term_id`
- Index naming: `ix_{table}_{column(s)}` → `ix_srs_reviews_card_id`
- Check constraint naming: `ck_{table}_{column}` → `ck_srs_cards_language`
- Unique constraint naming: `uq_{table}_{column(s)}`
- Use `TimestampMixin` from `src.app.db.base` for created_at/updated_at

### Testing Standards

- **Unit tests:** `tests/unit/modules/srs/` — mock repository, test service logic with py-fsrs
- **Integration tests:** `tests/integration/modules/srs/` — real Postgres, test repository + migrations
- **Fixtures:** Use existing `conftest.py` patterns (async session, test user)
- **Assert patterns:** Use domain entities for assertions, not raw DB rows

### Project Structure Notes

All new code goes in existing `backend/src/app/modules/srs/` structure:
- `domain/entities.py` — Add Review entity
- `domain/value_objects.py` — Add Rating enum
- `domain/exceptions.py` — Add specific error classes
- `infrastructure/models.py` — Add SrsReviewModel, update SrsCardModel
- `infrastructure/repository.py` — Add write methods
- `application/services.py` — Add ReviewSchedulingService
- `api/router.py` — Add create/review endpoints
- `api/schemas.py` — Add request/response models
- `api/dependencies.py` — Add service factory

New Alembic migration in `backend/alembic/versions/`

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.1]
- [Source: _out_put/planning-artifacts/architecture.md#Data Architecture — FSRS state storage]
- [Source: _out_put/planning-artifacts/architecture.md#Implementation Patterns — Structure Patterns]
- [Source: _out_put/planning-artifacts/architecture.md#Module Boundaries — srs → vocabulary]
- [Source: _out_put/planning-artifacts/prd/non-functional-requirements.md#NFR7 — queue 100ms]
- [Source: py-fsrs GitHub — https://github.com/open-spaced-repetition/py-fsrs — v6.3.1 API]

### Latest Tech: py-fsrs v6.3.1

- Package: `fsrs` on PyPI (NOT `py-fsrs`)
- Uses FSRS-6 model with improved short-term review scheduling
- Default `desired_retention = 0.9` (90% target recall)
- `Scheduler()`, `Card()`, `Rating` are the core classes
- `card.to_json()` / `Card.from_json()` for serialization
- `scheduler.review_card(card, rating)` returns `(updated_card, review_log)`
- All datetime operations in UTC

## Dev Agent Record

### Agent Model Used

openai/gpt-5.4

### Debug Log References

- `uv add fsrs`
- `uv run pytest tests/unit/modules/srs/application/test_queue_services.py tests/unit/modules/srs/application/test_review_scheduling_service.py tests/integration/modules/srs/test_repository.py`
- `uv run pytest tests/unit/modules/srs tests/integration/modules/srs tests/e2e/test_srs_queue_flow.py`
- `uv run ruff check src/app/modules/srs tests/unit/modules/srs tests/integration/modules/srs tests/e2e/test_srs_queue_flow.py`
- `uv run mypy --follow-imports=silent src/app/modules/srs tests/unit/modules/srs/application/test_queue_services.py tests/unit/modules/srs/application/test_review_scheduling_service.py tests/integration/modules/srs/test_repository.py tests/e2e/test_srs_queue_flow.py`
- `uv run pytest` (repo-wide run still reports 5 unrelated enrichment failures tied to Redis/test data constraints)
- `uv run pytest tests/unit/modules/srs tests/integration/modules/srs tests/e2e/test_srs_queue_flow.py`
- `uv run ruff check src/app/modules/srs tests/unit/modules/srs tests/integration/modules/srs tests/e2e/test_srs_queue_flow.py`
- `uv run mypy --follow-imports=silent src/app/modules/srs tests/unit/modules/srs/application/test_queue_services.py tests/unit/modules/srs/application/test_review_scheduling_service.py tests/integration/modules/srs/test_repository.py tests/integration/modules/srs/test_migrations.py tests/e2e/test_srs_queue_flow.py`

### Completion Notes List

- Added `fsrs==6.3.1`, a new Alembic migration, and expanded SRS persistence with `language`, `stability`, `difficulty`, `reps`, `lapses`, plus `srs_reviews` audit rows.
- Implemented `ReviewSchedulingService`, FSRS JSONB serialization helpers, create/review write paths, `/due` alias, and queue-stats time estimation from average review duration when review telemetry exists.
- Verified Story 4.1 behavior with 26 passing SRS-focused unit/integration/e2e tests, including per-language card creation, duplicate protection, review rollback handling, due ordering, Alembic migration verification, and a 10k-card queue performance check under 100ms.
- `fsrs` v6.3.1 no longer exposes `reps`/`lapses` on `Card`; those counters are tracked explicitly in the SRS domain/database while `fsrs_state` stores the canonical py-fsrs card JSON.
- Resolved all 6 code-review findings by making review persistence atomic, locking cards during review, enforcing duplicate prevention at the database level, backfilling legacy FSRS state in the migration, and verifying migration behavior through Alembic-based integration coverage.

### File List

- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/alembic/versions/2e7d2c4c9f10_expand_srs_cards_with_fsrs_reviews.py`
- `backend/src/app/modules/srs/domain/entities.py`
- `backend/src/app/modules/srs/domain/value_objects.py`
- `backend/src/app/modules/srs/domain/interfaces.py`
- `backend/src/app/modules/srs/domain/exceptions.py`
- `backend/src/app/modules/srs/infrastructure/models.py`
- `backend/src/app/modules/srs/infrastructure/repository.py`
- `backend/src/app/modules/srs/application/services.py`
- `backend/src/app/modules/srs/api/schemas.py`
- `backend/src/app/modules/srs/api/dependencies.py`
- `backend/src/app/modules/srs/api/router.py`
- `backend/tests/unit/modules/srs/application/test_queue_services.py`
- `backend/tests/unit/modules/srs/application/test_review_scheduling_service.py`
- `backend/tests/integration/modules/srs/__init__.py`
- `backend/tests/integration/modules/srs/test_migrations.py`
- `backend/tests/integration/modules/srs/test_repository.py`
- `backend/tests/e2e/test_srs_queue_flow.py`

### Change Log

- 2026-05-06: Implemented Story 4.1 FSRS-backed SRS card creation/review flow, persistence migration, queue aliasing, and SRS-focused automated coverage.
- 2026-05-06: Addressed code review findings for atomic review persistence, duplicate prevention, queue ordering, legacy state backfill, and Alembic-backed migration verification.
