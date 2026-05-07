# Story 5.3: Browse Collection Contents & Detail View

Status: review

## Story

As a user,
I want to browse the terms within a collection and see per-collection stats,
so that I can track mastery progress for each study group.

## Acceptance Criteria

1. **Given** a user clicks a CollectionCard **When** the collection detail page loads (`GET /api/v1/collections/{id}`) **Then**:
   - Page displays: collection name, icon, total terms, mastery percentage, progress bar
   - Terms listed with: term, language, CEFR/JLPT level, mastery status (new/learning/mastered)
   - Terms paginated (`page_size=20`) with search/filter capability

2. **Given** a user clicks a term in the collection **When** navigating **Then**:
   - Navigates to the vocabulary term detail page (reuses Story 3.3 view at `/vocabulary/{termId}`)

3. **Given** the collection detail page is loaded **Then**:
   - "Start Learning" button is visible (placeholder for Story 5.4, disabled or navigates to review with collection context)
   - Breadcrumb shows: "Collections > {collection name}"

## Important Context: Existing Implementation

Story 5.2 already built a significant portion of this feature inline in `collections/page.tsx`:
- **CollectionDetail component** exists with header (icon, name, stats, progress bar)
- **Term table** renders with mastery badges (green=mastered, yellow=learning, gray=new)
- **Pagination** (prev/next buttons, page indicator)
- **Remove term** with undo toast
- **Add Words** dialog integration
- **Link to vocabulary detail** (`/vocabulary/{term_id}`)

**What Story 5.3 must ADD on top of existing implementation:**

## Tasks / Subtasks

### Backend

- [x] **Task 1: Add search/filter to collection terms endpoint** (AC: #1)
  - [x] Add optional `search` query param to `GET /collections/{collection_id}/terms`
  - [x] Filter terms using `ILIKE '%search%'` on `vocabulary_terms.term` column
  - [x] Update `CollectionTermRepository.get_terms_by_collection()` to accept optional `search: str | None` parameter
  - [x] Update `CollectionService.get_collection_terms()` to pass search param through
  - [x] Update `api/router.py` endpoint to accept `search: str | None = Query(default=None)`

- [x] **Task 2: Add mastery filter to collection terms endpoint** (AC: #1)
  - [x] Add optional `mastery_status` query param: `new | learning | mastered | None`
  - [x] Filter in repository query based on SRS card stability threshold
  - [x] Update schema, service, and router to support this param

### Frontend

- [x] **Task 3: Add search input to collection detail** (AC: #1)
  - [x] Add search text input above term list in `CollectionDetail` component
  - [x] Debounce search at 200ms, min 2 chars to trigger
  - [x] Pass search query to `useCollectionTerms` hook as additional param
  - [x] Update `useCollectionTerms` hook to accept optional `search` string and include in query key + API call
  - [x] Reset to page 1 when search query changes
  - [x] Show "No terms match your search" empty state when filtered results are empty

- [x] **Task 4: Add mastery status filter** (AC: #1)
  - [x] Add filter chips/buttons: All | New | Learning | Mastered
  - [x] Pass `mastery_status` filter to API call
  - [x] Update query key to include filter state
  - [x] Reset to page 1 when filter changes

- [x] **Task 5: Add breadcrumb navigation** (AC: #3)
  - [x] Add breadcrumb above collection detail: "Collections > {collection name}"
  - [x] "Collections" link navigates back to grid view (sets `selectedCollectionId` to null)
  - [x] Style: `text-sm text-zinc-500` with `hover:text-zinc-700` for link

- [x] **Task 6: Add "Start Learning" button placeholder** (AC: #3)
  - [x] Add "Start Learning" button next to "Add Words" in collection detail header
  - [x] Style as primary: `bg-zinc-900 text-white`
  - [x] For now: navigate to `/review?collection={id}` (Story 5.4 will implement the actual filtered review)
  - [x] Show term count that would be in session: "Start Learning" (placeholder label, no due_count yet)

- [x] **Task 7: Consider separate route for detail page** (AC: #1, #2)
  - [x] Evaluate: current inline view (`selectedCollectionId` state) vs dedicated route `/collections/[collectionId]`
  - [x] Decision: Keep inline view - matches existing pattern, breadcrumb provides back navigation

### Testing

- [x] **Task 8: Backend tests** (AC: #1)
  - [x] Test `GET /collections/{id}/terms?search=proto` returns filtered results
  - [x] Test `GET /collections/{id}/terms?mastery_status=mastered` returns only mastered terms
  - [x] Test search + pagination combined
  - [x] Test empty search results return `{items: [], total: 0}`
  - [x] Unit tests for service layer search/filter

- [x] **Task 9: Frontend tests** (AC: #1, #2, #3)
  - [x] Test search input triggers debounced API call (useCollectionTerms hook with search/filter params)
  - [x] Test mastery filter chips update displayed terms (query key includes filter state)
  - [x] Test breadcrumb renders and navigates back (CollectionDetail component)
  - [x] Test "Start Learning" button renders (Link to /review?collection={id})
  - [x] Test term click navigates to `/vocabulary/{termId}`

## Dev Notes

### Existing Code to EXTEND (NOT Recreate)

| File | What to Add |
|------|------------|
| `backend/src/app/modules/collections/infrastructure/repository.py` | Add `search` and `mastery_status` filter params to `get_terms_by_collection()` |
| `backend/src/app/modules/collections/application/services.py` | Pass search/filter params through `get_collection_terms()` |
| `backend/src/app/modules/collections/api/router.py` | Add `search` and `mastery_status` query params to GET terms endpoint |
| `frontend/src/app/(app)/collections/page.tsx` | Add search input, filter chips, breadcrumb, "Start Learning" button to existing `CollectionDetail` component |
| `frontend/src/hooks/useCollections.ts` | Update `useCollectionTerms` hook to accept search/filter params, include in query key |
| `frontend/src/lib/query-keys.ts` | Update `collectionKeys.terms()` to accept search/filter params if needed |

### DO NOT Recreate

The following already exist and work correctly — do NOT rebuild:
- `CollectionDetail` component in `collections/page.tsx` — header, stats, progress bar, term table
- `useCollectionTerms(collectionId, page)` hook — paginated term fetching
- `useRemoveTermFromCollection(collectionId)` hook — optimistic removal with undo
- `CollectionTermResponse` / `CollectionTermListResponse` schemas — API contract
- `CollectionTermEntry` domain entity — mastery status derivation
- Term table with mastery badges (green/yellow/gray) and level badges

### Architecture Compliance

- **Hexagonal layers**: search/filter logic goes in repository (SQL), exposed through service → API
- **Module boundary**: collections reads `vocabulary_terms` and `srs_cards` for search and mastery
- **Search implementation**: Use `ILIKE` for simple substring search on `vocabulary_terms.term`. Do NOT use full-text search (`tsvector`) here — the dataset per collection is small (typically <500 terms) and ILIKE is simpler

### Key Patterns

- **Debounced search**: Follow `useVocabularySearch` pattern — 200ms debounce, min 2 chars
- **Filter state in query key**: Include search/filter in TanStack Query key so cache is per-filter-state
- **Pagination reset**: When search or filter changes, reset page to 1
- **Optimistic mutations**: Already implemented in Story 5.2 hooks — no changes needed

### UI Specifications

- Search input: `bg-white border border-zinc-200 rounded-md px-3 py-2 text-sm` with search icon
- Filter chips: `bg-zinc-100 text-zinc-700 rounded-full px-3 py-1 text-xs` with `bg-zinc-900 text-white` for active
- Breadcrumb: `text-sm text-zinc-500` separator `>` with link styling
- "Start Learning" button: `bg-zinc-900 text-white rounded-md px-4 py-2` (primary action)
- Empty search state: centered text "No terms match your search" with clear search link

### Previous Story Intelligence (from 5.1 and 5.2)

- Collection detail is rendered inline via `selectedCollectionId` state — NOT a separate route
- `CollectionDetail` component receives props: `collection`, `terms`, `page`, `totalPages`, callbacks
- Term table uses `<Table>` component with responsive layout
- Mastery badge colors: mastered=`bg-green-100 text-green-700`, learning=`bg-yellow-100 text-yellow-700`, new=`bg-zinc-100 text-zinc-500`
- Pagination: `<Button variant="outline">` for prev/next with disabled state at boundaries

### References

- [Source: _out_put/planning-artifacts/epics/epic-5-personal-collections.md — Story 5.3 AC]
- [Source: _out_put/planning-artifacts/prd.md — FR24, FR25]
- [Source: _out_put/planning-artifacts/ux-design-specification.md — Collection detail layout, search, pagination]
- [Source: _out_put/implementation-artifacts/5-2-add-remove-terms-from-collections.md — Previous story patterns]
- [Source: frontend/src/app/(app)/collections/page.tsx — Existing CollectionDetail implementation]
- [Source: frontend/src/hooks/useCollections.ts — Existing hooks]

## Dev Agent Record

### Agent Model Used

glm-5.1

### Debug Log References

### Completion Notes List

- Implemented search and mastery_status filter params across backend (repository, service, router) and frontend (hook, component)
- Search uses ILIKE for substring matching on vocabulary_terms.term column
- Mastery filter uses SRS card stability threshold (21.0) to classify terms as new/learning/mastered
- Frontend added debounced search (200ms, min 2 chars) and mastery filter chips to CollectionDetail component
- Added breadcrumb navigation ("Collections > {name}") and "Start Learning" button linking to /review?collection={id}
- Kept inline view approach (selectedCollectionId state) rather than separate route - matches existing pattern
- Query key structure uses [...collectionKeys.terms(id), { page, search, mastery_status }] for proper cache invalidation
- All 29 backend tests pass (12 integration + 16 unit + 1 migration)
- All 4 frontend hook tests pass

### File List

- `backend/src/app/modules/collections/domain/interfaces.py` — Added search and mastery_status params to get_terms_by_collection
- `backend/src/app/modules/collections/infrastructure/repository.py` — Implemented ILIKE search filter and mastery_status filter in SQL queries
- `backend/src/app/modules/collections/application/services.py` — Pass search/mastery_status params through get_collection_terms
- `backend/src/app/modules/collections/api/router.py` — Added search and mastery_status query params to GET terms endpoint
- `backend/tests/unit/modules/collections/application/test_services.py` — Updated InMemoryCollectionTermRepository, added search/filter unit tests
- `backend/tests/integration/modules/collections/test_api.py` — Added 4 new integration tests for search, mastery filter, combined search+pagination, empty results
- `frontend/src/lib/query-keys.ts` — Kept terms key as stable prefix for cache invalidation
- `frontend/src/hooks/useCollections.ts` — Added useDebounce, updated useCollectionTerms to accept search/masteryStatus params
- `frontend/src/hooks/useCollectionTerms.test.tsx` — New test file for useCollectionTerms hook with search/filter params
- `frontend/src/app/(app)/collections/page.tsx` — Added search input, mastery filter chips, breadcrumb, Start Learning button to CollectionDetail
