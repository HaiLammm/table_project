# Story 5.2: Add & Remove Terms from Collections

Status: review

## Story

As a user,
I want to add and remove vocabulary terms from my collections,
so that I can curate focused study sets for specific learning goals.

## Acceptance Criteria

1. **Given** a user is on a collection detail page **When** they click "Add Words" **Then** they can add terms via 3 methods:
   - **Manual:** type term → auto-suggest from corpus → Enter to add
   - **Browse corpus:** search Database Waterfall → select terms → bulk add
   - **CSV import:** upload file → preview → confirm (reuses Epic 3 CSV import flow)
   - Each added term creates a `collection_terms` record via `POST /api/v1/collections/{id}/terms`
   - Duplicate detection warns if a term already exists in this collection

2. **Given** a user wants to remove a term from a collection **When** they select remove on a term **Then**:
   - The `collection_terms` association is deleted (the term and its SRS card remain)
   - A toast with undo option appears: "Term removed from collection — Undo"

## Tasks / Subtasks

### Backend

- [x] **Task 1: Extend domain layer** (AC: #1, #2)
  - [x] Add `CollectionTermRepository` interface to `domain/interfaces.py` with: `add_term`, `add_terms_bulk`, `remove_term`, `term_exists_in_collection`, `get_terms_by_collection`
  - [x] Add domain exceptions to `domain/exceptions.py`: `TermAlreadyInCollectionError(409)`, `TermNotInCollectionError(404)`

- [x] **Task 2: Implement repository** (AC: #1, #2)
  - [x] Add `SqlAlchemyCollectionTermRepository` to `infrastructure/repository.py`
  - [x] `add_term`: INSERT into `collection_terms`, handle unique constraint → `TermAlreadyInCollectionError`
  - [x] `add_terms_bulk`: batch INSERT with `on_conflict_do_nothing`, return count of actually inserted
  - [x] `remove_term`: DELETE from `collection_terms` WHERE collection_id AND term_id
  - [x] `term_exists_in_collection`: SELECT EXISTS
  - [x] `get_terms_by_collection`: JOIN `collection_terms` → `vocabulary_terms`, paginated, return `(list[VocabularyTerm], total_count)`
  - [x] Add unique constraint `uq_collection_terms_collection_id_term_id` on `(collection_id, term_id)` — requires Alembic migration

- [x] **Task 3: Extend service layer** (AC: #1, #2)
  - [x] Add to `CollectionService` in `application/services.py`:
    - `add_term_to_collection(user_id, collection_id, term_id)` — validates ownership + term existence + duplicate check
    - `add_terms_bulk(user_id, collection_id, term_ids: list[int])` — bulk add with duplicate skip, returns `{added: int, skipped: int}`
    - `remove_term_from_collection(user_id, collection_id, term_id)` — validates ownership, deletes association
    - `get_collection_terms(user_id, collection_id, page, page_size)` — paginated term list
    - `import_csv_to_collection(user_id, collection_id, file)` — reuse vocabulary CSV parser, then bulk add matched term_ids

- [x] **Task 4: Add API endpoints** (AC: #1, #2)
  - [x] `POST /collections/{collection_id}/terms` — body: `{term_id: int}` or `{term_ids: list[int]}` → add single/bulk
  - [x] `DELETE /collections/{collection_id}/terms/{term_id}` — remove term
  - [x] `GET /collections/{collection_id}/terms?page=1&page_size=20` — paginated term list
  - [x] `POST /collections/{collection_id}/import` — CSV file upload (reuse vocabulary CSV parser)
  - [x] Add Pydantic schemas: `AddTermRequest`, `AddTermsRequest`, `AddTermsResponse`, `CollectionTermResponse`, `CollectionTermListResponse`, `CollectionCSVImportResponse`

- [x] **Task 5: Alembic migration** (AC: #1)
  - [x] Add unique constraint on `collection_terms(collection_id, term_id)`
  - [x] Add index on `collection_terms(term_id)` for reverse lookups

### Frontend

- [x] **Task 6: Extend types and query keys** (AC: #1, #2)
  - [x] Add to `types/collection.ts`: `CollectionTerm`, `AddTermRequest`, `AddTermsResponse`, `CollectionTermListResponse`, `CollectionCSVImportResponse`
  - [x] Add to `lib/query-keys.ts`: `collectionKeys.terms(id)` key

- [x] **Task 7: Add hooks** (AC: #1, #2)
  - [x] `useCollectionTerms(collectionId, page)` — GET paginated terms
  - [x] `useAddTermToCollection(collectionId)` — POST mutation, invalidates `collectionKeys.terms(id)` and `collectionKeys.detail(id)` (term_count changes)
  - [x] `useAddTermsBulk(collectionId)` — POST mutation for bulk add
  - [x] `useRemoveTermFromCollection(collectionId)` — DELETE mutation with optimistic removal + undo support
  - [x] `useImportCSVToCollection(collectionId)` — POST file upload mutation

- [x] **Task 8: AddWordsDialog component** (AC: #1)
  - [x] Three-tab dialog: Manual | Import CSV | Browse Corpus
  - [x] **Manual tab:** text input with autocomplete dropdown, reuse `useVocabularySearch` hook (debounce 200ms, min 2 chars). On select → call add mutation. Show inline "Already in collection" warning on duplicate (409 response).
  - [x] **Browse tab:** search box using `useVocabularySearch` + results grid with checkboxes + "Add Selected" bulk button
  - [x] **CSV tab:** reuse drag-drop uploader pattern from vocabulary import. Preview first 10 rows → confirm → call import endpoint. Show results: added/skipped/errors count.

- [x] **Task 9: Term list with remove** (AC: #2)
  - [x] Term list in collection detail showing: term, reading, level, mastery status
  - [x] Remove button ("X") on each term row
  - [x] On remove: optimistic UI removal + toast "Term removed from collection — Undo"
  - [x] Undo: re-add term via add mutation within toast timeout (5 seconds auto-dismiss)
  - [x] Pagination (page_size=20)

- [x] **Task 10: Integration into CollectionsPage** (AC: #1, #2)
  - [x] Collection card click → collection detail view (or new page `/collections/[id]`)
  - [x] Detail view: header (icon, name, stats) + "Add Words" button + term list + pagination

### Testing

- [x] **Task 11: Backend tests** (AC: #1, #2)
  - [x] Unit tests for `CollectionService.add_term_to_collection`, `remove_term_from_collection`, `add_terms_bulk`
  - [x] Test duplicate detection returns 409
  - [x] Test remove preserves vocabulary term and SRS card
  - [x] Test CSV import reuses parser correctly
  - [x] Test ownership validation (user can't modify another user's collection)

- [x] **Task 12: Frontend tests** (AC: #1, #2)
  - [x] Test AddWordsDialog renders 3 tabs
  - [x] Test manual add with autocomplete
  - [x] Test remove with undo toast
  - [x] Test optimistic updates and rollback

## Dev Notes

### Architecture Compliance

- **Hexagonal architecture:** domain → application → infrastructure → api layers. Domain has ZERO framework imports.
- **Module boundary:** collections module can READ from `vocabulary_terms` and `srs_cards` tables but only WRITES to `collections` and `collection_terms`.
- **CSV import reuse:** Import vocabulary CSV parser from `backend/src/app/modules/vocabulary/application/csv_parser.py`. Do NOT duplicate parsing logic. The parser returns `ParseResult` with rows containing `term` field — match terms by name against `vocabulary_terms` table to get `term_id`s, then bulk-add to collection.

### Existing Code to Extend (NOT Create New)

| File | What to Add |
|------|------------|
| `backend/src/app/modules/collections/domain/interfaces.py` | `CollectionTermRepository` abstract class |
| `backend/src/app/modules/collections/domain/exceptions.py` | `TermAlreadyInCollectionError`, `TermNotInCollectionError` |
| `backend/src/app/modules/collections/infrastructure/repository.py` | `SqlAlchemyCollectionTermRepository` class |
| `backend/src/app/modules/collections/application/services.py` | Add term management methods to existing `CollectionService` |
| `backend/src/app/modules/collections/api/router.py` | Add 4 new endpoints to existing router |
| `backend/src/app/modules/collections/api/schemas.py` | Add term-related Pydantic schemas |
| `frontend/src/types/collection.ts` | Add term-related types |
| `frontend/src/lib/query-keys.ts` | Add `terms(id)` to existing `collectionKeys` |
| `frontend/src/hooks/useCollections.ts` | Add term mutation/query hooks |
| `frontend/src/app/(app)/collections/page.tsx` | Add collection detail navigation |

### Key Patterns from Previous Stories

- **Optimistic mutations:** Follow pattern in existing `useCreateCollection` — cancel queries, snapshot previous, update cache, rollback on error. See `frontend/src/hooks/useCollections.ts`.
- **Pagination:** Backend returns `{items: [...], total: int}`. Frontend passes `page` and `page_size` query params.
- **Auth:** All endpoints use `CurrentUserDependency` from `Depends(get_current_user)`. Validate `user.id` with `_require_user_id()`.
- **Error handling:** Domain exceptions have `status_code` and `code` fields. API layer catches domain exceptions → HTTPException. Frontend `ApiClientError` extracts message for toast display.
- **Structured logging:** `structlog.get_logger()` — log business events: `term_added_to_collection`, `term_removed_from_collection`, `csv_import_to_collection`.
- **DB model patterns:** Use `Mapped[int]` with `mapped_column(Integer, primary_key=True, autoincrement=True)`. ForeignKey with `ondelete="CASCADE"`. Named constraints: `uq_`, `ix_` prefixes.

### Vocabulary Search Reuse

The `useVocabularySearch(query)` hook already exists at `frontend/src/hooks/useVocabularySearch.ts`:
- Debounces at 200ms, triggers at >= 2 chars
- Calls `GET /api/v1/vocabulary_terms/search?query=...&limit=20`
- Backend uses PostgreSQL `plainto_tsquery` full-text search
- Returns ranked results — reuse directly in AddWordsDialog manual and browse tabs

### CSV Import Reuse

The CSV parser exists at `backend/src/app/modules/vocabulary/application/csv_parser.py`:
- `parse_csv(file_content: bytes) -> ParseResult` — auto-detects encoding, delimiter, maps columns
- Returns `ParseResult` with `rows: list[ParsedCSVRow]` each having `.term`, `.language`, etc.
- For collection import: parse CSV → extract term names → lookup term_ids from vocabulary_terms → bulk add to collection_terms
- Frontend patterns: `useCSVImportPreview` and `useCSVImport` hooks exist for vocabulary — follow same upload + preview + confirm pattern

### Database Migration Note

The `collection_terms` table already exists (created in Story 5.1 migration). This story needs a NEW migration to add:
- `UNIQUE(collection_id, term_id)` constraint — prevents duplicate term-collection pairs at DB level
- `INDEX(term_id)` — for efficient reverse lookups (which collections contain this term?)

### UI Specifications

- Cards: `bg-zinc-100 border border-zinc-200`
- Progress bar fill: `bg-zinc-600`
- Action buttons: `bg-zinc-900` with white text
- Toast: bottom-right position, 5-second auto-dismiss, "Undo" link triggers re-add
- AddWordsDialog: modal dialog with tab navigation (Manual | Import CSV | Browse Corpus)

### Project Structure Notes

- Backend module: `backend/src/app/modules/collections/` (hexagonal layout with api/, application/, domain/, infrastructure/)
- Frontend app route: `frontend/src/app/(app)/collections/` — may need `[id]/page.tsx` for detail view
- Frontend components: `frontend/src/components/collections/` — add `AddWordsDialog.tsx`, extend index exports
- Naming: PascalCase components, camelCase hooks with `use` prefix, snake_case API/DB

### References

- [Source: _out_put/planning-artifacts/epics/epic-5-personal-collections.md — Story 5.2 AC]
- [Source: _out_put/planning-artifacts/architecture.md — Collections module structure, API patterns]
- [Source: _out_put/planning-artifacts/prd.md — FR22, FR23, FR24, NFR11, NFR14]
- [Source: _out_put/planning-artifacts/ux-design.md — Add Words interface, Remove feedback UX]
- [Source: _out_put/implementation-artifacts/5-1-collection-crud-data-model.md — DB schema, ORM patterns, service patterns]
- [Source: backend/src/app/modules/vocabulary/application/csv_parser.py — CSV parsing reuse]
- [Source: frontend/src/hooks/useVocabularySearch.ts — Search hook reuse]
- [Source: frontend/src/hooks/useCollections.ts — Optimistic mutation patterns]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `pytest backend/tests/unit/modules/collections/application/test_services.py backend/tests/integration/modules/collections/test_api.py backend/tests/integration/modules/collections/test_migrations.py`
- `npm test -- "src/components/collections/AddWordsDialog.test.tsx" "src/hooks/useCollections.test.ts" "src/app/(app)/collections/page.test.tsx" "src/components/collections/CollectionCard.test.tsx"`
- `ruff check src/app/modules/collections tests/unit/modules/collections tests/integration/modules/collections`
- `npm run lint -- "src/app/(app)/collections/page.tsx" "src/app/(app)/collections/page.test.tsx" "src/components/collections/AddWordsDialog.tsx" "src/components/collections/AddWordsDialog.test.tsx" "src/components/collections/CollectionCard.tsx" "src/components/collections/CollectionCard.test.tsx" "src/components/collections/index.ts" "src/hooks/useCollections.ts" "src/hooks/useCollections.test.ts" "src/types/collection.ts" "src/lib/query-keys.ts"`
- `npm run build`
- `pytest` *(fails in pre-existing unrelated suites: `tests/e2e/test_srs_queue_flow.py`, `tests/integration/modules/enrichment/test_api.py`, `tests/integration/modules/srs/test_schedule.py`)*
- `npm test` *(fails in pre-existing unrelated frontend suites: `src/components/vocabulary/TermAutoSuggest.test.tsx`, `src/components/vocabulary/AddTermForm.test.tsx`, `src/components/vocabulary/VocabularyRequestForm.test.tsx`)*

### Completion Notes List

- Added end-to-end collection term management in the backend: domain contracts, repository implementation, service methods, API schemas/routes, and an Alembic migration for unique `(collection_id, term_id)` pairs plus reverse lookup indexing.
- Reused the shared vocabulary CSV parser for collection import, mapped CSV rows back to existing corpus terms, and exposed collection term pagination with `new / learning / mastered` status derived from SRS cards.
- Expanded the frontend collections experience with an inline detail view, paginated term list, remove-with-undo flow, optimistic cache updates, and a three-tab `AddWordsDialog` for manual add, corpus browse, and CSV import.
- Added backend unit/integration coverage for add/remove/bulk/import/migration behavior and frontend coverage for the dialog, detail flow, undo toast, and optimistic rollback logic.
- Collection-specific tests, lint, and production build pass. The full repo suites still report unrelated pre-existing failures in SRS/enrichment backend tests and vocabulary component tests.

### File List

- `backend/alembic/versions/7f8e9d1a2b3c_add_collection_term_uniqueness.py`
- `backend/src/app/modules/collections/api/dependencies.py`
- `backend/src/app/modules/collections/api/router.py`
- `backend/src/app/modules/collections/api/schemas.py`
- `backend/src/app/modules/collections/application/services.py`
- `backend/src/app/modules/collections/domain/entities.py`
- `backend/src/app/modules/collections/domain/exceptions.py`
- `backend/src/app/modules/collections/domain/interfaces.py`
- `backend/src/app/modules/collections/infrastructure/models.py`
- `backend/src/app/modules/collections/infrastructure/repository.py`
- `backend/tests/integration/modules/collections/test_api.py`
- `backend/tests/integration/modules/collections/test_migrations.py`
- `backend/tests/unit/modules/collections/application/test_services.py`
- `frontend/src/app/(app)/collections/page.tsx`
- `frontend/src/app/(app)/collections/page.test.tsx`
- `frontend/src/components/collections/AddWordsDialog.tsx`
- `frontend/src/components/collections/AddWordsDialog.test.tsx`
- `frontend/src/components/collections/index.ts`
- `frontend/src/hooks/useCollections.ts`
- `frontend/src/hooks/useCollections.test.ts`
- `frontend/src/lib/query-keys.ts`
- `frontend/src/types/collection.ts`

### Change Log

- 2026-05-07: Implemented Story 5.2 add/remove collection terms, collection CSV import, detail browsing flow, optimistic undo UX, and automated test coverage; story is ready for review.
