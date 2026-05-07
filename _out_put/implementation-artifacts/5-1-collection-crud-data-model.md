# Story 5.1: Collection CRUD & Data Model

Status: review

## Story

As a **user**,
I want to create, rename, and delete personal vocabulary collections,
so that I can organize my vocabulary by topic, exam, or project.

## Acceptance Criteria

1. **Database Schema** — Alembic migration creates:
   - `collections` table: `id`, `user_id`, `name`, `icon`, `created_at`, `updated_at`
   - `collection_terms` table: `id`, `collection_id`, `term_id`, `added_at`
   - Unique constraint: `uq_collections_user_id_name` (user cannot have duplicate collection names)
   - FK `collection_terms.collection_id` → `collections.id` ON DELETE CASCADE
   - FK `collection_terms.term_id` → `vocabulary_terms.id` ON DELETE CASCADE
   - Index: `ix_collections_user_id`, `ix_collection_terms_collection_id`

2. **Collections Grid** — `/collections` page displays 2-column grid (1-column mobile) of `CollectionCard` components. Each card shows: icon, name, term count, mastery %, progress bar (zinc-600 fill). A "+" card with dashed border appears at end.

3. **Empty State** — When no collections exist, show "No collections yet" with "+ New Collection" action (UX-DR16).

4. **Create Collection** — Click "+ New Collection" → dialog with name + icon picker → `POST /api/v1/collections` → new card appears immediately (optimistic update).

5. **Rename** — Dropdown menu → "Rename" → inline edit (click name → edit → Enter to save, Esc to cancel).

6. **Delete** — Dropdown menu → "Delete" → confirmation: "Delete '{name}'? The {N} terms will remain in your library but won't be grouped." → `DELETE /api/v1/collections/{id}` removes collection + collection_terms associations, NOT vocabulary terms.

## Tasks / Subtasks

- [x] Task 1: Database migration + ORM models (AC: #1)
  - [x] 1.1 Create Alembic migration for `collections` and `collection_terms` tables
  - [x] 1.2 Create `CollectionModel` and `CollectionTermModel` in `modules/collections/infrastructure/models.py`
- [x] Task 2: Domain layer (AC: #1)
  - [x] 2.1 Create `Collection` and `CollectionTerm` entities in `domain/entities.py`
  - [x] 2.2 Create `CollectionNotFoundError`, `DuplicateCollectionError` in `domain/exceptions.py`
  - [x] 2.3 Create `CollectionRepository` abstract interface in `domain/interfaces.py`
- [x] Task 3: Infrastructure layer (AC: #1, #4, #5, #6)
  - [x] 3.1 Implement `CollectionRepository` in `infrastructure/repository.py`
  - [x] 3.2 Methods: `create`, `get_by_id`, `list_by_user`, `update`, `delete`, `get_term_count`, `get_mastery_percent`
- [x] Task 4: Application layer (AC: #4, #5, #6)
  - [x] 4.1 Create `CollectionService` in `application/services.py` with CRUD operations
  - [x] 4.2 Mastery % calculation: count of mastered SRS cards / total terms in collection
- [x] Task 5: API layer (AC: #4, #5, #6)
  - [x] 5.1 Create Pydantic schemas: `CollectionCreate`, `CollectionUpdate`, `CollectionResponse`, `CollectionListResponse`
  - [x] 5.2 Create router: `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`
  - [x] 5.3 Create dependencies.py with DI wiring
  - [x] 5.4 Register router in `src/app/api/routes.py` with prefix `/api/v1/collections`
- [x] Task 6: Frontend types + API hooks (AC: #2, #3, #4, #5, #6)
  - [x] 6.1 Create `frontend/src/types/collection.ts` with `Collection`, `CollectionResponse` types
  - [x] 6.2 Create `frontend/src/lib/query-keys.ts` — add `collectionKeys` namespace
  - [x] 6.3 Create `frontend/src/hooks/useCollections.ts` — `useCollections()`, `useCreateCollection()`, `useUpdateCollection()`, `useDeleteCollection()` with TanStack Query
- [x] Task 7: CollectionCard component (AC: #2, #3, #5, #6)
  - [x] 7.1 Create `frontend/src/components/collections/CollectionCard.tsx` with `default` and `create` variants
  - [x] 7.2 Dropdown menu with Rename/Delete actions using shadcn `DropdownMenu`
  - [x] 7.3 Inline rename: click name → input → Enter/Esc
  - [x] 7.4 Progress bar with `bg-zinc-600` fill
- [x] Task 8: Collections page (AC: #2, #3, #4)
  - [x] 8.1 Create `frontend/src/app/(app)/collections/page.tsx` with responsive grid
  - [x] 8.2 Empty state with illustration + CTA
  - [x] 8.3 Create collection dialog (name + icon picker)
  - [x] 8.4 Delete confirmation dialog
- [x] Task 9: Tests (all ACs)
  - [x] 9.1 Unit tests: `CollectionService` CRUD logic, mastery calculation
  - [x] 9.2 Integration tests: API endpoints with real DB
  - [x] 9.3 Component tests: `CollectionCard` variants, rename flow, delete confirmation
  - [x] 9.4 Page test: grid layout, empty state, create flow

## Dev Notes

### Backend Architecture — Hexagonal Pattern

Follow the exact same hexagonal pattern as `srs/` and `vocabulary/` modules:

```
modules/collections/
├── domain/
│   ├── entities.py       # @dataclass(slots=True, kw_only=True) — see vocabulary/domain/entities.py
│   ├── exceptions.py     # CollectionNotFoundError, DuplicateCollectionError
│   └── interfaces.py     # ABC with async methods — see srs/domain/interfaces.py
├── application/
│   └── services.py       # CollectionService — see srs/application/services.py
├── infrastructure/
│   ├── models.py         # SQLAlchemy 2.0 Mapped[] — see vocabulary/infrastructure/models.py
│   └── repository.py     # Async session — see srs/infrastructure/repository.py
└── api/
    ├── router.py         # FastAPI router — see srs/api/router.py
    ├── schemas.py        # Pydantic v2 models — see srs/api/schemas.py
    └── dependencies.py   # Annotated DI — see srs/api/dependencies.py (if exists) or inline in router
```

### ORM Models — Critical Patterns

Use `TimestampMixin` from `src.app.db.base` for `created_at`/`updated_at`. Use `Base` from same module. Follow exact patterns from `vocabulary/infrastructure/models.py`:
- `Mapped[int]` with `mapped_column(Integer, primary_key=True, autoincrement=True)` for IDs
- `ForeignKey("vocabulary_terms.id", ondelete="CASCADE")` for term references
- Named constraints: `uq_collections_user_id_name`, `ix_collections_user_id`
- `collection_terms.added_at` as `DateTime(timezone=True)` with `server_default=text("now()")`

### Mastery Percentage Calculation

Mastery % = (SRS cards with `stability >= 21.0` for terms in collection) / (total terms in collection) × 100. This requires a cross-module read query joining `collection_terms` → `srs_cards`. The `collections` module is allowed to read from `srs_cards` table (architecture: `collections → vocabulary` dependency, SRS data is read-only from collections perspective).

### Router Registration

Register in `backend/src/app/api/routes.py` following the pattern at line ~96-102:
```python
from src.app.modules.collections.api.router import router as collections_router
app.include_router(collections_router, prefix=f"{settings.api_v1_prefix}/collections")
```

### Frontend Patterns

- **Types**: Create `frontend/src/types/collection.ts` following `srs.ts` pattern
- **Query keys**: Add to `frontend/src/lib/query-keys.ts` — `collectionKeys = { all: ['collections'], list: () => [...collectionKeys.all, 'list'], detail: (id: number) => [...collectionKeys.all, id] }`
- **Hooks**: Follow `useRatingMutation.ts` / `useUpcomingSchedule.ts` patterns with `useApiClient()` and TanStack Query
- **Components**: Co-locate tests as `CollectionCard.test.tsx`
- **Page route**: `frontend/src/app/(app)/collections/page.tsx` — the `(app)` group provides the app shell layout

### CollectionCard Component Spec

```typescript
interface CollectionCardProps {
  icon: string;
  name: string;
  termCount: number;
  masteryPercent: number;
  variant?: 'default' | 'create';
  onClick: () => void;
  onRename?: (newName: string) => void;
  onDelete?: () => void;
}
```

Styling: `bg-zinc-100 border border-zinc-200 rounded-[10px] p-5`. Progress bar fill: `bg-zinc-600`. Create variant: dashed border, "+" icon centered.

Use shadcn `DropdownMenu` for card actions (Rename, Delete).

### Icon Picker

Use a simple emoji picker or a predefined set of ~20 category icons (book, globe, code, briefcase, etc.). Keep it minimal for MVP — a grid of emoji/icons in a popover.

### Existing Empty Collections Module

The `backend/src/app/modules/collections/` directory already exists with empty `__init__.py` files in all subdirectories. Fill these files — do NOT create a new module directory.

### Cross-Story Context

This is the first story in Epic 5. Stories 5.2-5.4 will add:
- 5.2: Add/remove terms (POST/DELETE `/collections/{id}/terms`), CSV import
- 5.3: Collection detail page with term list, pagination
- 5.4: Start focused review session from collection

Design the schema and API to support these future stories. The `collection_terms` join table is created in this story but primarily populated in 5.2.

### Testing Standards

- **Backend unit**: pytest + pytest-asyncio in `backend/tests/unit/modules/collections/`
- **Backend integration**: `backend/tests/integration/modules/collections/` — real DB
- **Frontend component**: Vitest + React Testing Library, co-located `.test.tsx`
- **Coverage targets**: Domain ≥ 90%, Application ≥ 70%

### Project Structure Notes

- Backend module path: `backend/src/app/modules/collections/` (already scaffolded)
- Frontend components: `frontend/src/components/collections/` (index.ts exists, empty)
- Frontend page: `frontend/src/app/(app)/collections/page.tsx` (NEW)
- Alembic migration: `backend/alembic/versions/` (NEW revision)

### References

- [Source: _out_put/planning-artifacts/epics/epic-5-personal-collections.md#Story 5.1]
- [Source: _out_put/planning-artifacts/architecture.md#Lines 778-796 — Collections module structure]
- [Source: _out_put/planning-artifacts/architecture.md#Lines 414-457 — Naming conventions]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Lines 1056-1074 — CollectionCard spec]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Lines 820-866 — Collections user journey]
- [Source: _out_put/planning-artifacts/prd/functional-requirements.md#FR22 — Collection CRUD]

## Dev Agent Record

### Agent Model Used

- `openai/gpt-5.4`

### Debug Log References

- `docker compose up -d postgres`
- `pytest backend/tests/unit/modules/collections backend/tests/integration/modules/collections`
- `pytest backend/tests`
- `ruff check backend/src/app/modules/collections backend/src/app/main.py backend/tests/unit/modules/collections backend/tests/integration/modules/collections`
- `npm test -- "src/components/collections/CollectionCard.test.tsx" "src/app/(app)/collections/page.test.tsx"`
- `npm test`
- `npm run lint -- "src/app/(app)/collections/page.tsx" "src/app/(app)/collections/page.test.tsx" "src/components/collections/CollectionCard.tsx" "src/components/collections/CollectionCard.test.tsx" "src/components/collections/index.ts" "src/components/ui/dropdown-menu.tsx" "src/hooks/useCollections.ts" "src/types/collection.ts" "src/lib/query-keys.ts"`
- `npm run build`

### Completion Notes List

- Added the `collections` and `collection_terms` schema via Alembic, including named constraints, cascade foreign keys, and indexed lookup paths.
- Implemented the backend collections module end-to-end with hexagonal domain, repository, service, API schemas, auth-aware router wiring, and a mastery percentage query over `collection_terms -> srs_cards`.
- Replaced the `/collections` placeholder with a responsive collections experience: empty state, 2-column grid, optimistic create flow, emoji icon picker, inline rename, and delete confirmation.
- Added backend unit + integration coverage for CRUD, mastery aggregation, API behavior, and migration shape, plus frontend component/page tests for the key user flows.
- Registered the collections router in `backend/src/app/main.py` because this repo does not currently use `src/app/api/routes.py`.
- Targeted collections validation is green; broader repo regressions still show unrelated existing failures in `backend/tests/e2e/test_srs_queue_flow.py`, `backend/tests/integration/modules/enrichment/test_api.py`, and frontend vocabulary tests under `frontend/src/components/vocabulary/` plus `frontend/src/components/vocabulary/VocabularyRequestForm.test.tsx`.

### File List

- `backend/alembic/versions/c2f7a9d4b6e1_create_collections_tables.py`
- `backend/src/app/main.py`
- `backend/src/app/modules/collections/api/dependencies.py`
- `backend/src/app/modules/collections/api/router.py`
- `backend/src/app/modules/collections/api/schemas.py`
- `backend/src/app/modules/collections/application/services.py`
- `backend/src/app/modules/collections/domain/entities.py`
- `backend/src/app/modules/collections/domain/exceptions.py`
- `backend/src/app/modules/collections/domain/interfaces.py`
- `backend/src/app/modules/collections/infrastructure/models.py`
- `backend/src/app/modules/collections/infrastructure/repository.py`
- `backend/tests/integration/modules/collections/__init__.py`
- `backend/tests/integration/modules/collections/test_api.py`
- `backend/tests/integration/modules/collections/test_migrations.py`
- `backend/tests/unit/modules/collections/__init__.py`
- `backend/tests/unit/modules/collections/application/__init__.py`
- `backend/tests/unit/modules/collections/application/test_services.py`
- `backend/tests/unit/modules/collections/test_entities.py`
- `frontend/src/app/(app)/collections/page.test.tsx`
- `frontend/src/app/(app)/collections/page.tsx`
- `frontend/src/components/collections/CollectionCard.test.tsx`
- `frontend/src/components/collections/CollectionCard.tsx`
- `frontend/src/components/collections/index.ts`
- `frontend/src/components/ui/dropdown-menu.tsx`
- `frontend/src/hooks/useCollections.ts`
- `frontend/src/lib/query-keys.ts`
- `frontend/src/types/collection.ts`

### Change Log

- 2026-05-07: Implemented Story 5.1 collection CRUD, data model, UI flows, and automated tests; story is ready for review.
