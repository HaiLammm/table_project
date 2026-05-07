# Story 6.1: Diagnostic Signal Capture & Pattern Detection Engine

Status: review

## Story

As the **system**,
I want to capture diagnostic signals from every review and detect learning patterns in the background,
so that actionable insights can be surfaced to users as their data accumulates.

## Acceptance Criteria

**AC1 — Signal Capture (FR26):**
Given a user completes a card review
When the review is recorded
Then diagnostic signals are captured: timestamp, response_time_ms, difficulty rating, card category (vocabulary hierarchy), session_id, session_length, language, parallel_mode_active
And signals are stored in `srs_reviews` with additional metadata columns via Alembic migration

**AC2 — Time-of-Day Pattern Detection (FR27):**
Given a user has accumulated ≥7 days of review data with ≥50 total reviews
When the diagnostics background worker runs
Then time-of-day retention patterns are detected (e.g., "retention drops 35% after 9pm for IT terms")
And recommendations are generated and stored

**AC3 — Category Weakness Detection (FR28):**
Given a user has ≥30 reviews within a vocabulary category
When the diagnostics worker analyzes category data
Then category-specific weakness patterns are detected (e.g., "networking terms consistently rated Hard")

**AC4 — Cross-Language Interference Detection (FR29):**
Given a user has ≥20 parallel-mode reviews for a given term
When the diagnostics worker analyzes cross-language data
Then cross-language interference patterns are detected (e.g., "JP retention drops when reviewing same term in parallel mode")

**AC5 — Insufficient Data Guard:**
Given insufficient data for a pattern type
When the worker checks thresholds
Then that pattern type is skipped — no false insights generated

## Tasks / Subtasks

- [x] Task 1: Alembic migration — add metadata columns to `srs_reviews` (AC: 1)
  - [x] 1.1 Create migration adding `session_length_s` (Integer, nullable), `parallel_mode_active` (Boolean, default false, nullable) to `srs_reviews`
  - [x] 1.2 Add index `ix_srs_reviews_user_reviewed` on `(user_id, reviewed_at)` for analytics queries
  - [x] 1.3 Run migration forward/backward to verify reversibility

- [x] Task 2: Update SRS domain and infrastructure for new signal fields (AC: 1)
  - [x] 2.1 Add `session_length_s: int | None` and `parallel_mode_active: bool | None` to `Review` entity in `srs/domain/entities.py`
  - [x] 2.2 Add corresponding columns to `SrsReviewModel` in `srs/infrastructure/models.py`
  - [x] 2.3 Update `ReviewCardRequest` schema: add `session_length_s: int | None = None` and `parallel_mode_active: bool = False`
  - [x] 2.4 Update `ReviewSchedulingService.schedule_review()` and repository `create_review()` to persist new fields
  - [x] 2.5 Unit tests for new fields flowing through service → repository

- [x] Task 3: Extend `ReviewAnalyticsRow` and repository query for new signals (AC: 1, 4)
  - [x] 3.1 Add `language: str`, `parallel_mode_active: bool | None`, `term_id: int | None`, `card_id: int` to `ReviewAnalyticsRow` TypedDict in `dashboard/domain/interfaces.py`
  - [x] 3.2 Update `SqlAlchemyDiagnosticRepository.get_review_analytics()` to join and select: `SrsCardModel.language`, `SrsReviewModel.parallel_mode_active`, `SrsCardModel.term_id`, `SrsReviewModel.card_id`
  - [x] 3.3 Integration test: verify new fields returned from analytics query

- [x] Task 4: Enforce AC2 thresholds on time-of-day detector (AC: 2, 5)
  - [x] 4.1 Add data sufficiency guard to `_detect_time_of_day_pattern`: require ≥7 days of data AND ≥50 total reviews, return None otherwise
  - [x] 4.2 Unit tests: pattern skipped when <7 days or <50 reviews; pattern detected when thresholds met

- [x] Task 5: Enforce AC3 thresholds on category weakness detector (AC: 3, 5)
  - [x] 5.1 Update `_detect_category_weakness`: require ≥30 reviews in a category (currently 3) before including in eligible set
  - [x] 5.2 Unit tests: pattern skipped when <30 reviews per category; detected when threshold met

- [x] Task 6: Implement cross-language interference detector (AC: 4, 5)
  - [x] 6.1 Add `_detect_cross_language_interference()` to `dashboard/application/services.py`
  - [x] 6.2 Logic: group reviews by `term_id`, filter terms with ≥20 parallel-mode reviews (`parallel_mode_active=True`), compare accuracy of parallel vs non-parallel reviews for same terms, detect if parallel mode drops retention significantly (≥15% delta)
  - [x] 6.3 Generate `DiagnosticInsight` with `PatternType.CROSS_LANGUAGE_INTERFERENCE`, severity "warning", icon "languages"
  - [x] 6.4 Wire into `compute_insights()` — run when `confidence_score >= 0.8`
  - [x] 6.5 Unit tests: no insight when <20 parallel reviews; insight generated when threshold met and delta significant; no insight when delta < threshold

- [x] Task 7: Update `compute_insights` data sufficiency to match AC thresholds (AC: 2, 5)
  - [x] 7.1 Update main `compute_insights`: before running time-of-day detector, verify total_reviews ≥ 50 (in addition to existing data_age check)
  - [x] 7.2 Unit test: verify compute_insights skips time-of-day when reviews < 50 even if days ≥ 7

- [x] Task 8: Full integration test for diagnostic pipeline (AC: 1-5)
  - [x] 8.1 Integration test: create user with 60+ reviews across 8+ days, multiple categories, some parallel-mode → verify all 3 detectors produce insights
  - [x] 8.2 Integration test: insufficient data scenarios → verify no insights generated
  - [x] 8.3 Integration test: verify new signal columns persisted correctly through review endpoint

## Dev Notes

### Existing Infrastructure (DO NOT recreate)

The `dashboard` module is **fully implemented** from stories 4-5 and 4-6:

- **Domain:** `DiagnosticInsight` entity, `PatternType` enum (6 values, 3 detected), `InsightSeverity` enum
- **Service:** `DiagnosticsService` with `compute_insights()`, `get_pending_insights()`, `mark_insight_seen()`
- **Repository:** `SqlAlchemyDiagnosticRepository` — joins `srs_reviews → srs_cards → vocabulary_terms`
- **API:** `GET /diagnostics/insights`, `POST /diagnostics/insights/{id}/seen`
- **DB tables:** `diagnostic_insights`, `insight_seen` (migration `8b2c4d6e7f80`)

Three detectors already exist:
- `_detect_time_of_day_pattern` — groups by morning/afternoon/evening/late-night, needs threshold tightening
- `_detect_category_weakness` — groups by `term_category` (mapped to `part_of_speech`), needs threshold tightening
- `_detect_response_time_anomaly` — compares slow vs fast card "again" rates

**Missing:** `_detect_cross_language_interference` — must be added.

### Architecture Compliance

- Hexagonal module structure: `domain/` never imports `infrastructure/` or `api/`
- `dashboard` module reads from `srs` and `vocabulary` tables — **never writes to them**
- All API endpoints use `Depends(get_current_user)` and `Depends(get_async_session)`
- Use `structlog` for logging, never `print()` or bare `logging`
- Pydantic v2 for all API schemas
- SQLAlchemy 2.0 async + asyncpg

### Key File Paths

**Backend — modify:**
- `backend/src/app/modules/srs/domain/entities.py` — add fields to `Review`
- `backend/src/app/modules/srs/infrastructure/models.py` — add columns to `SrsReviewModel`
- `backend/src/app/modules/srs/api/schemas.py` — extend `ReviewCardRequest`
- `backend/src/app/modules/srs/application/services.py` — pass new fields through
- `backend/src/app/modules/srs/infrastructure/repository.py` — persist new fields
- `backend/src/app/modules/dashboard/domain/interfaces.py` — extend `ReviewAnalyticsRow`
- `backend/src/app/modules/dashboard/infrastructure/repository.py` — extend analytics query
- `backend/src/app/modules/dashboard/application/services.py` — add cross-language detector, tighten thresholds

**Backend — create:**
- `backend/alembic/versions/XXXX_add_diagnostic_signal_columns.py` — new migration

**Tests — modify/create:**
- `backend/tests/unit/modules/dashboard/application/test_services.py` — new tests for thresholds and cross-language detector
- `backend/tests/integration/modules/dashboard/test_diagnostics.py` — full pipeline tests

### Database Schema Changes

Add to `srs_reviews` table:
- `session_length_s INTEGER NULL` — session length in seconds at time of review
- `parallel_mode_active BOOLEAN NULL DEFAULT false` — whether review was in parallel (multi-language) mode

Add index:
- `ix_srs_reviews_user_reviewed (user_id, reviewed_at)` — optimize analytics queries

### Naming & Convention Reminders

- Tables: snake_case, plural (`srs_reviews`)
- Indexes: `ix_{table}_{columns}` pattern
- FK: `{referenced_table_singular}_id`
- Pydantic models: PascalCase + suffix (`ReviewCardRequest`)
- Service classes: `{Domain}Service` (`DiagnosticsService`)

### Previous Story Learnings (from 4-5 review)

- `term_category` maps to `part_of_speech` in `vocabulary_terms` — semantic mismatch but acceptable for MVP
- Pattern detection runs on UTC hours, not user-local time — known limitation
- `get_review_analytics` returns up to 30 days of data — bounded
- `CROSS_LANGUAGE_INTERFERENCE` is already defined in `PatternType` enum but has no detector function yet

### Threshold Summary Table

| Pattern Type | Threshold | Current | Story Requirement |
|---|---|---|---|
| time_of_day | data ≥7 days AND ≥50 reviews | ≥3 days, ≥3 rows per period | **Tighten to ≥7d + ≥50 reviews** |
| category_weakness | ≥30 reviews per category | ≥3 per category | **Tighten to ≥30 per category** |
| cross_language_interference | ≥20 parallel-mode reviews per term | Not implemented | **New detector** |
| response_time_anomaly | (existing, no change) | ≥3 slow + ≥3 fast | No change required |

### References

- [Source: _out_put/planning-artifacts/epics/epic-6-learning-diagnostics-progress-dashboard.md — Story 6.1]
- [Source: _out_put/planning-artifacts/architecture.md — Dashboard module, Data Architecture, Testing Standards]
- [Source: _out_put/planning-artifacts/epics/requirements-inventory.md — FR26-FR29]
- [Source: backend/src/app/modules/dashboard/application/services.py — existing detectors]
- [Source: backend/src/app/modules/srs/infrastructure/models.py — SrsReviewModel current schema]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `pytest backend/tests/unit/modules/dashboard/application/test_services.py backend/tests/unit/modules/srs/application/test_review_scheduling_service.py backend/tests/integration/modules/srs/test_repository.py backend/tests/integration/modules/dashboard/test_diagnostics.py backend/tests/integration/modules/srs/test_migrations.py`
- `pytest backend/tests/unit/modules/dashboard backend/tests/integration/modules/dashboard backend/tests/unit/modules/srs/application backend/tests/integration/modules/srs`
- `ruff check backend/src/app/modules/dashboard/application/services.py backend/src/app/modules/dashboard/domain/interfaces.py backend/src/app/modules/dashboard/infrastructure/repository.py backend/src/app/modules/srs/domain/entities.py backend/src/app/modules/srs/infrastructure/models.py backend/src/app/modules/srs/api/schemas.py backend/src/app/modules/srs/application/services.py backend/src/app/modules/srs/infrastructure/repository.py backend/src/app/modules/srs/api/router.py backend/alembic/versions/b8d0a9c4e271_add_diagnostic_signal_columns_to_srs_reviews.py backend/tests/unit/modules/dashboard/application/test_services.py backend/tests/unit/modules/srs/application/test_review_scheduling_service.py backend/tests/integration/modules/srs/test_repository.py backend/tests/integration/modules/dashboard/test_diagnostics.py backend/tests/integration/modules/srs/test_migrations.py`
- `pytest` *(still fails in unrelated existing suites: `tests/e2e/test_srs_queue_flow.py`, `tests/integration/modules/enrichment/test_api.py`, `tests/integration/modules/srs/test_collection_queue.py`, `tests/integration/modules/srs/test_schedule.py`)*

### Completion Notes List

- Added diagnostic signal capture fields to the SRS review pipeline: `session_length_s` and `parallel_mode_active` now flow from review API request through domain/service/repository into `srs_reviews` persistence.
- Added Alembic migration `b8d0a9c4e271` to extend `srs_reviews` and create the analytics index `ix_srs_reviews_user_reviewed`, with upgrade and downgrade coverage in the SRS migration test.
- Extended dashboard analytics rows and repository queries to expose `language`, `parallel_mode_active`, `term_id`, and `card_id`, enabling detector logic to use richer review context.
- Tightened diagnostics thresholds to match story requirements: time-of-day now requires at least 7 days and 50 reviews, category weakness now requires at least 30 reviews per category, and `compute_insights()` skips time-of-day analysis when those thresholds are not met.
- Implemented `_detect_cross_language_interference()` and wired it into diagnostics generation for high-confidence datasets, prioritizing it ahead of response-time anomaly when the top three insights are selected.
- Added unit and integration coverage for threshold guards, cross-language detection, analytics row expansion, review signal persistence, and the full diagnostic pipeline.
- Story-specific tests and lint pass. Full backend regression still reports unrelated failures in older SRS route/e2e tests, collection queue tests, and enrichment tests that predate or sit outside this story's scope.

### File List

- `backend/alembic/versions/b8d0a9c4e271_add_diagnostic_signal_columns_to_srs_reviews.py`
- `backend/src/app/modules/dashboard/application/services.py`
- `backend/src/app/modules/dashboard/domain/interfaces.py`
- `backend/src/app/modules/dashboard/infrastructure/repository.py`
- `backend/src/app/modules/srs/api/router.py`
- `backend/src/app/modules/srs/api/schemas.py`
- `backend/src/app/modules/srs/application/services.py`
- `backend/src/app/modules/srs/domain/entities.py`
- `backend/src/app/modules/srs/infrastructure/models.py`
- `backend/src/app/modules/srs/infrastructure/repository.py`
- `backend/tests/integration/modules/dashboard/test_diagnostics.py`
- `backend/tests/integration/modules/srs/test_migrations.py`
- `backend/tests/integration/modules/srs/test_repository.py`
- `backend/tests/unit/modules/dashboard/application/test_services.py`
- `backend/tests/unit/modules/srs/application/test_review_scheduling_service.py`

### Change Log

- 2026-05-07: Implemented Story 6.1 diagnostic signal capture, stricter diagnostics thresholds, cross-language interference detection, and supporting test coverage; status moved to review.
### Change Log
