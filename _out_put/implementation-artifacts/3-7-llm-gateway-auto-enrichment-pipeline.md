# Story 3.7: LLM Gateway & Auto-Enrichment Pipeline

Status: review

## Story

As the **system**,
I want an LLM Gateway that routes enrichment requests to multiple providers with caching, cost tracking, and JMdict validation,
so that vocabulary enrichment is reliable, cost-effective, and accurate.

## Acceptance Criteria (BDD)

1. **Given** a term needs enrichment (FR14)
   **When** the enrichment worker processes the job
   **Then** the LLM Gateway checks Redis cache first (key: hash of term+lang+level)
   **And** on cache miss, routes to the configured provider (Claude Haiku -> Gemini Flash -> DeepSeek fallback)
   **And** the LLM returns structured output validated against a Pydantic schema (definition, IPA, CEFR level, examples, related terms)
   **And** Japanese definitions are cross-validated against JMdict via the dictionary module (FR15)
   **And** validated results are stored in `vocabulary_definitions` with `source='llm'` and `validated_against_jmdict=true/false`
   **And** results are cached in Redis (TTL: 30 days)

2. **Given** enrichment results pass validation
   **When** the corpus sync worker runs (Database Waterfall - FR16)
   **Then** enriched terms are deduplicated against the central corpus
   **And** new validated terms are merged into the central corpus

3. **Given** an LLM provider fails
   **When** the gateway detects the failure
   **Then** it retries up to 3 times with exponential backoff (NFR33)
   **And** falls back to the next configured provider
   **And** failed jobs route to a dead-letter queue for admin review
   **And** per-user daily cost is tracked and remains below $0.02 (NFR19)

## Tasks / Subtasks

- [x] Task 1: Build the backend LLM gateway foundation (AC: 1, 3)
  - [x] 1.1 Add runtime HTTP support and gateway configuration in `backend/pyproject.toml`, `backend/src/app/core/config.py`, and `backend/.env.example` for provider API keys, model IDs, Redis TTLs, and daily cost cap
  - [x] 1.2 Create a top-level `backend/src/app/llm/` package for `gateway.py`, `cache.py`, `cost_tracker.py`, `schemas.py`, and provider adapters so `modules/enrichment/` stays orchestration-only
  - [x] 1.3 Define normalized Pydantic schemas for both single-term enrichment and structured-request preview candidates; validate every provider response through these schemas before persistence
  - [x] 1.4 Implement provider routing in this exact order: Anthropic primary, Gemini secondary, DeepSeek tertiary fallback
  - [x] 1.5 Implement Redis result caching with key format based on normalized `term + language + level` and TTL of 30 days
  - [x] 1.6 Implement cost tracking from provider token usage into a Redis daily bucket keyed by `user_id` when available, otherwise a temporary `anonymous/system` bucket until auth is wired into vocabulary routes

- [x] Task 2: Replace the corpus-only structured request path with a gateway-backed preview/confirm flow (AC: 1, 2, 3)
  - [x] 2.1 Upgrade `backend/src/app/modules/enrichment/application/services.py` so `find_terms_for_request()` returns corpus hits first, then fills request gaps with LLM-generated candidates
  - [x] 2.2 Change `POST /api/v1/vocabulary_requests/preview` to return a `preview_id` plus stable `candidate_id` values for both corpus and generated candidates
  - [x] 2.3 Store preview candidates server-side in Redis with a short TTL so confirm does not trust the browser to resend raw LLM payloads
  - [x] 2.4 Change `POST /api/v1/vocabulary_requests/confirm` to accept `preview_id` plus selected candidate IDs, reuse existing term IDs for corpus hits, and create/upsert new `vocabulary_terms` + `vocabulary_definitions` for generated candidates
  - [x] 2.5 Persist only fields supported by the current schema: term metadata on `vocabulary_terms`, definition/IPA/examples/source/JMdict flag on `vocabulary_definitions`; keep `related_terms` as preview/domain-only data in this story
  - [x] 2.6 Enqueue corpus-sync work only for confirmed/generated terms that were actually persisted

- [x] Task 3: Wire the background auto-enrichment pipeline for manual add and CSV import flows (AC: 1, 3)
  - [x] 3.1 Create `backend/src/app/workers/enrichment_worker.py` and register it in `backend/src/app/workers/arq_settings.py` with `max_tries=3`
  - [x] 3.2 Replace the `# TODO: trigger enrichment job when Story 3.7 is implemented` placeholder in `VocabularyService.create_user_term()` with a real enqueue step
  - [x] 3.3 Replace the CSV import enrichment TODO in `VocabularyService.import_csv()` with real enqueue logic for newly persisted terms only
  - [x] 3.4 Make jobs idempotent with custom ARQ job IDs and cache keys because ARQ uses pessimistic execution and jobs may run more than once
  - [x] 3.5 Route terminal failures to a Redis-backed dead-letter queue and structured logs for future admin review

- [x] Task 4: Implement the Database Waterfall sync boundary without re-architecting the whole data model (AC: 2)
  - [x] 4.1 Add a corpus sync service/worker that deduplicates persisted LLM-enriched terms against the existing central `vocabulary_terms` corpus
  - [x] 4.2 Ensure sync is idempotent and one-way; re-running the same sync must not create duplicate terms or duplicate definitions
  - [x] 4.3 Do not introduce a new user-vocabulary table, moderation UI, or admin dashboard in this story

- [x] Task 5: Update the frontend request preview contract so generated terms are confirmable (AC: 1, 2)
  - [x] 5.1 Update `frontend/src/types/vocabulary.ts`, `useVocabularyRequest.ts`, and `useConfirmVocabularyRequest.ts` for the new `preview_id` + candidate selection contract
  - [x] 5.2 Update `frontend/src/components/vocabulary/VocabularyRequestPreview.tsx` so LLM-generated candidates are selectable instead of being disabled when `term_id` is null
  - [x] 5.3 Remove the current "LLM enrichment coming soon" placeholder copy and replace it with real generated/validated status plus graceful degradation copy only when providers fail or budget caps prevent gap fill
  - [x] 5.4 Preserve the existing add-term and CSV import UX wording around background enrichment; this story makes that wording true rather than introducing a new frontend flow

- [x] Task 6: Add tests and observability that match the real failure modes (AC: all)
  - [x] 6.1 Unit tests for provider response parsing, cache-key normalization, JMdict validation mapping, fallback order, and daily cost calculations
  - [x] 6.2 Worker tests for retry behavior, exponential backoff, idempotent re-run, and DLQ routing after the final failure
  - [x] 6.3 Integration tests for `preview` and `confirm` covering corpus-only hits, mixed corpus+LLM candidates, cache hits, provider fallback, and JP validation flags
  - [x] 6.4 Regression tests proving `create_user_term()` and CSV import now enqueue enrichment work
  - [x] 6.5 Frontend tests for candidate selection, confirm payload shape, and degraded preview states

## Dev Notes

### Story Intent

This story closes the deliberate placeholders left by Stories 3.4, 3.5, and 3.6:

- Story 3.4 already tells the user "Term added - enriching..."
- Story 3.5 created a pluggable enrichment interface but only returned corpus matches
- Story 3.6 imported terms and explicitly deferred enrichment job triggering to Story 3.7

The implementation must therefore do two things at once:

1. Support **synchronous** LLM-backed preview generation for `/vocabulary_requests/preview`
2. Support **asynchronous** ARQ-backed enrichment for add-term and CSV import flows

Do not split these into separate architectures. They should share the same lower-level gateway, cache, schema validation, cost tracking, and JMdict validation logic.

### Current Code You Must Extend

**`backend/src/app/modules/enrichment/application/services.py`**
- Current state: `CorpusOnlyEnrichmentService` only queries existing corpus terms and returns `source="corpus"`
- Story 3.7 change: upgrade this service so it becomes the orchestration layer for corpus-first lookup plus LLM gap-fill for structured requests
- Preserve: the public `find_terms_for_request()` entry point so Story 3.5's route shape evolves instead of being replaced by a parallel path

**`backend/src/app/modules/enrichment/api/router.py`**
- Current state: preview only returns corpus matches; confirm only accepts `term_ids`
- Story 3.7 change: preview must return `preview_id` + candidate IDs, and confirm must resolve preview candidates server-side before persistence
- Preserve: thin router pattern; business logic belongs in services

**`backend/src/app/modules/vocabulary/application/services.py`**
- Current state: `create_user_term()` and `import_csv()` both contain Story 3.7 TODO markers for enrichment job enqueueing
- Story 3.7 change: replace those TODOs instead of creating another job-trigger path elsewhere
- Preserve: CSV import chunking and response shape; enrichment should happen after persistence, not before

**`backend/src/app/workers/arq_settings.py`**
- Current state: only `noop` and `process_data_export` are registered
- Story 3.7 change: register enrichment and corpus sync workers here
- Preserve: central worker registration and shared Redis settings

**`backend/scripts/seed_corpus.py`**
- Current state: already demonstrates Anthropic Messages API usage, JSON payload extraction, and JMdict validation during corpus seeding
- Story 3.7 change: reuse ideas, prompt structure, and normalization patterns where helpful
- Preserve: do not copy its blocking `urllib` approach into async runtime code; gateway calls should be async

**`frontend/src/components/vocabulary/VocabularyRequestPreview.tsx`**
- Current state: shows "LLM enrichment coming soon" and disables candidates that do not have a `term_id`
- Story 3.7 change: generated candidates must become selectable and confirmable
- Preserve: same page/route and general preview-confirm UX from Story 3.5

**`frontend/src/hooks/useConfirmVocabularyRequest.ts`**
- Current state: posts `{ term_ids }`
- Story 3.7 change: post `preview_id` and selected candidate IDs
- Preserve: invalidate vocabulary queries and return to `/vocabulary` after success

### Architecture Guardrails

1. Create the new gateway under `backend/src/app/llm/`, not inside the router, to align with the architecture plan even though that package does not exist yet.
2. Keep `modules/enrichment/` as the orchestration boundary between HTTP routes, workers, and persistence.
3. Keep all LLM provider credentials server-side only. No frontend provider calls, no browser-exposed keys.
4. Prefer `httpx.AsyncClient` for provider calls. The backend is async end-to-end, and blocking request code would be the wrong fit here.
5. Use Redis for four distinct concerns:
   - 30-day term enrichment result cache
   - short-lived preview candidate cache
   - daily cost counters
   - dead-letter queue payload storage
6. Treat every ARQ job as at-least-once. Jobs can be retried or replayed after cancellation.
7. Do not invent a new SQL schema for `related_terms`. The current database only needs persisted term metadata plus definition records.
8. Do not solve user-vocabulary ownership in this story. The current repo does not yet model that fully; keep signatures ready for `user_id` but do not introduce a new join table.

### Preview / Confirm Contract Guardrails

The current Story 3.5 confirm contract (`term_ids`) is insufficient for generated candidates. Use this shape instead:

```json
{
  "preview_id": "uuid-or-random-token",
  "selected_candidate_ids": ["cand_1", "cand_4", "cand_7"]
}
```

The preview response should return:

- `preview_id`
- `terms`
- each term with `candidate_id`
- `source` (`corpus` or `llm`)
- `term_id` only when the candidate already exists in the corpus
- `validated_against_jmdict` for Japanese output

This lets the confirm endpoint create or reuse persisted records without trusting the client to resend raw generated definitions.

### Persistence Rules

- `definition`, `ipa`, `examples`, `source="llm"`, and `validated_against_jmdict` belong in `vocabulary_definitions`
- `cefr_level`, `jlpt_level`, and `part_of_speech` belong on `vocabulary_terms`
- `related_terms` should remain preview/domain-only for now
- If a term already exists, reuse it and add/update the definition rather than inserting a duplicate term
- Corpus sync runs only for persisted/confirmed enrichment results, never for abandoned preview candidates

### Current Project Structure Notes

There is one important architecture-to-reality mismatch to preserve in the story context:

- The architecture document still describes the frontend root as `table-project-web/`
- The actual repo uses `frontend/`

Follow the **real repo paths** when editing code. Use the architecture document for boundaries and patterns, not for literal top-level folder names.

### Files to Create

**Backend**
- `backend/src/app/llm/__init__.py`
- `backend/src/app/llm/gateway.py`
- `backend/src/app/llm/cache.py`
- `backend/src/app/llm/cost_tracker.py`
- `backend/src/app/llm/schemas.py`
- `backend/src/app/llm/providers/__init__.py`
- `backend/src/app/llm/providers/anthropic.py`
- `backend/src/app/llm/providers/google.py`
- `backend/src/app/llm/providers/deepseek.py`
- `backend/src/app/workers/enrichment_worker.py`
- `backend/src/app/workers/corpus_sync.py` if sync is split into a separate worker
- Unit tests for gateway/provider/cache/cost logic

**Frontend**
- No mandatory new route is required
- Add new files only if a dedicated preview DTO helper or UI state helper becomes necessary

### Files to Update

**Backend**
- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/src/app/core/config.py`
- `backend/src/app/modules/enrichment/api/dependencies.py`
- `backend/src/app/modules/enrichment/api/router.py`
- `backend/src/app/modules/enrichment/api/schemas.py`
- `backend/src/app/modules/enrichment/application/services.py`
- `backend/src/app/modules/enrichment/domain/entities.py`
- `backend/src/app/modules/enrichment/domain/interfaces.py`
- `backend/src/app/modules/vocabulary/application/services.py`
- `backend/src/app/modules/vocabulary/infrastructure/repository.py`
- `backend/src/app/workers/arq_settings.py`
- relevant backend tests under `backend/tests/unit/` and `backend/tests/integration/`

**Frontend**
- `frontend/src/types/vocabulary.ts`
- `frontend/src/hooks/useVocabularyRequest.ts`
- `frontend/src/hooks/useConfirmVocabularyRequest.ts`
- `frontend/src/components/vocabulary/VocabularyRequestPreview.tsx`
- `frontend/src/components/vocabulary/VocabularyRequestPreview.test.tsx`
- `frontend/src/app/(app)/vocabulary/request/page.tsx` if the page needs loading/degraded-state adjustments

### Testing Requirements

**Backend unit tests**
- Provider parsing for Anthropic, Gemini, and DeepSeek responses
- Cache-key normalization (`term + language + level`)
- Cost calculation from token usage
- JP definition validation against `JMdictService`
- Fallback order and normalized failure mapping

**Backend worker tests**
- retry path using ARQ `Retry(defer=...)`
- idempotent re-run for the same enrichment job
- DLQ write after final failed attempt
- corpus sync deduplication

**Backend integration tests**
- preview with corpus-only results
- preview with mixed corpus + generated candidates
- preview cache hit avoids second live provider call
- confirm creates new persisted terms/definitions for generated candidates
- confirm reuses existing term IDs for corpus hits
- add-term enqueue regression
- CSV import enqueue regression

**Frontend tests**
- generated candidates are selectable even without a persisted `term_id`
- confirm request posts `preview_id` and selected candidate IDs
- degraded preview state renders without the old "coming soon" placeholder

### Latest Technical Information (Verified 2026-05-06)

**Anthropic**
- Current model overview lists `claude-haiku-4-5` as the latest Haiku alias and `claude-haiku-4-5-20251001` as the snapshot ID
- The current seed script default `claude-3-5-haiku-latest` is stale for new gateway work and should not be copied into Story 3.7
- The Claude API remains centered on the Messages API (`POST /v1/messages`)
- Anthropic also documents a Message Batches API for future cost optimization, but that is not required to complete this story

**Google Gemini**
- Stable production naming includes `gemini-2.5-flash`
- Structured outputs support `responseMimeType: "application/json"` and `responseJsonSchema`
- Google explicitly recommends validating structured-output responses in application code even when the JSON is schema-shaped
- Use the stable `gemini-2.5-flash` fallback model here, not a preview-only Gemini 3 example copied from docs

**DeepSeek**
- Current docs list `deepseek-v4-flash` and `deepseek-v4-pro`
- The legacy aliases `deepseek-chat` and `deepseek-reasoner` are compatibility aliases slated for deprecation
- DeepSeek supports JSON Output and exposes both OpenAI-format and Anthropic-format base URLs
- DeepSeek error docs explicitly call out retry-after-wait behavior for `500` and `503`, which matches this story's fallback/retry requirements

**ARQ**
- Official ARQ docs for v0.28.0 state that jobs may run more than once because of pessimistic execution
- ARQ custom `_job_id` values can prevent duplicate enqueue for the same work item
- ARQ `Retry(defer=...)` supports incremental backoff and default retry semantics
- ARQ startup/shutdown hooks are the right place to manage shared async clients

### References

- [Source: _out_put/planning-artifacts/epics/epic-3-vocabulary-management-enrichment-pipeline.md - Story 3.7]
- [Source: _out_put/planning-artifacts/prd/functional-requirements.md - FR11, FR14, FR15, FR16, FR41, FR43, FR44]
- [Source: _out_put/planning-artifacts/prd/non-functional-requirements.md - NFR2, NFR10, NFR11, NFR12, NFR13, NFR17, NFR19, NFR25, NFR31, NFR33, NFR34]
- [Source: _out_put/planning-artifacts/prd/user-journeys.md - admin dashboard, queue status, failed import recovery]
- [Source: _out_put/planning-artifacts/ux-design-specification.md - effortless adding vocabulary, auto-enrichment within seconds]
- [Source: _out_put/planning-artifacts/architecture.md - caching strategy, LLM gateway, ARQ workers, project boundaries, data flow]
- [Source: _out_put/implementation-artifacts/3-4-add-vocabulary-term-manually.md - background enrichment expectation]
- [Source: _out_put/implementation-artifacts/3-5-structured-vocabulary-request.md - pluggable enrichment interface and current preview flow]
- [Source: _out_put/implementation-artifacts/3-6-csv-import-with-error-handling.md - import-triggered enrichment TODOs and batch-processing constraints]
- [Source: backend/scripts/seed_corpus.py - existing Anthropic JSON generation and JMdict validation patterns]
- [Source: backend/src/app/modules/dictionary/application/services.py - cached JMdict validation behavior]
- [Source: backend/src/app/modules/enrichment/api/router.py - current preview/confirm contract]
- [Source: backend/src/app/modules/enrichment/application/services.py - current corpus-only implementation]
- [Source: backend/src/app/modules/vocabulary/application/services.py - Story 3.7 TODO hooks]
- [External: Anthropic Models Overview - https://docs.anthropic.com/en/docs/about-claude/models/overview]
- [External: Anthropic Messages API - https://docs.anthropic.com/en/api/messages]
- [External: Google Gemini Models - https://ai.google.dev/gemini-api/docs/models]
- [External: Google Gemini Structured Outputs - https://ai.google.dev/gemini-api/docs/structured-output]
- [External: DeepSeek Models & Pricing - https://api-docs.deepseek.com/quick_start/pricing]
- [External: DeepSeek Error Codes - https://api-docs.deepseek.com/quick_start/error_codes]
- [External: ARQ Documentation - https://arq-docs.helpmanual.io/]

### Previous Story Intelligence

**From Story 3.4**
- The UI already tells users that new terms are "enriching"; this story must make that claim operational
- The repo already uses `useApiClient()` plus mutation hooks as the frontend data-access pattern

**From Story 3.5**
- The enrichment interface was intentionally made pluggable so Story 3.7 could slot in without inventing a second request flow
- `VocabularyRequestPreview.tsx` currently treats `term_id === null` as non-selectable; that behavior must change for generated candidates
- `bulk_add_to_user_vocabulary()` is only sufficient for the corpus-only placeholder path and should not be treated as the final generated-candidate contract

**From Story 3.6**
- CSV import already preserves fast response time by separating import work from deferred enrichment
- Story 3.6 explicitly left Story 3.7 TODO markers in `VocabularyService`; close those exact gaps here

### Git Intelligence

Recent history shows these implementation patterns:

- `feat#3-1` style commit prefixes are already used within the Epic 3 vocabulary work
- vocabulary features are implemented as async FastAPI services with SQLAlchemy async repositories
- ARQ is already in production use for data export, so Story 3.7 should extend that worker model instead of introducing a second queue system
- recent vocabulary stories added both backend and frontend tests together; keep that cross-layer discipline here

Relevant recent commits reviewed while creating this story:

- `b89926b` - expanded vocabulary pages, services, schemas, and tests
- `a29c170` - introduced the vocabulary data model, `JMdictService`, and seed-corpus patterns
- `d761f09` - established ARQ worker registration and a background-job pattern through data export

### Project Context Reference

No `project-context.md` files were present under the project root when this story was generated.

### Implementation Assumptions

- Redis-backed preview state and DLQ storage are acceptable for this story and avoid unnecessary schema churn
- Vocabulary routes still do not receive `current_user`; gateway/service APIs should therefore accept `user_id: int | None` so later auth wiring is additive rather than a breaking refactor

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

### Completion Notes List

- Story context created for Story 3.7
- Story marked `ready-for-dev`
- All implementation completed for Story 3.7
- LLM Gateway with provider routing (Anthropic -> Gemini -> DeepSeek)
- Redis caching with 30-day TTL for enrichment results
- Redis preview caching with short TTL for preview candidates
- Cost tracking with daily bucket per user
- GatewayEnrichmentService for corpus-first + LLM gap-fill
- Preview/confirm flow with preview_id and candidate_id
- ARQ enrichment worker with max_tries=3
- ARQ corpus sync worker with max_tries=2
- JMdict validation for Japanese terms
- Frontend updated for LLM-generated candidate selection
- Unit tests added for LLM module, enrichment services
- Updated test_services.py test fixtures
- Backend unit tests: 78 passed

### File List

**Created:**
- `backend/src/app/llm/__init__.py`
- `backend/src/app/llm/cache.py`
- `backend/src/app/llm/cost_tracker.py`
- `backend/src/app/llm/gateway.py`
- `backend/src/app/llm/schemas.py`
- `backend/src/app/llm/providers/__init__.py`
- `backend/src/app/llm/providers/anthropic.py`
- `backend/src/app/llm/providers/google.py`
- `backend/src/app/llm/providers/deepseek.py`
- `backend/src/app/workers/enrichment_worker.py`
- `backend/src/app/workers/corpus_sync.py`
- `backend/tests/unit/modules/llm/test_cache.py`
- `backend/tests/unit/modules/llm/test_cost_tracker.py`
- `backend/tests/unit/modules/llm/test_schemas.py`

**Updated:**
- `backend/src/app/core/config.py`
- `backend/.env.example`
- `backend/src/app/modules/enrichment/domain/interfaces.py`
- `backend/src/app/modules/enrichment/api/schemas.py`
- `backend/src/app/modules/enrichment/api/router.py`
- `backend/src/app/modules/enrichment/application/services.py`
- `backend/src/app/modules/enrichment/api/dependencies.py`
- `backend/src/app/modules/vocabulary/domain/interfaces.py`
- `backend/src/app/modules/vocabulary/infrastructure/repository.py`
- `backend/src/app/modules/vocabulary/infrastructure/models.py`
- `backend/src/app/modules/vocabulary/domain/entities.py`
- `backend/src/app/modules/vocabulary/application/services.py`
- `backend/src/app/workers/arq_settings.py`
- `backend/tests/unit/test_arq_settings.py`
- `backend/tests/unit/modules/enrichment/test_services.py`
- `backend/tests/unit/modules/vocabulary/application/test_services.py`
- `frontend/src/types/vocabulary.ts`
- `frontend/src/hooks/useVocabularyRequest.ts`
- `frontend/src/hooks/useConfirmVocabularyRequest.ts`
- `frontend/src/components/vocabulary/VocabularyRequestPreview.tsx`
- `frontend/src/components/vocabulary/VocabularyRequestPreview.test.tsx`
