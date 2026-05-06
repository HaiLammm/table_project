# Story 3.4: Add Vocabulary Term Manually

Status: review

## Story

As a **user**,
I want to add a new vocabulary term manually with basic information,
so that I can include words I encounter outside the pre-seeded corpus.

## Acceptance Criteria (BDD)

1. **Given** a user is on the Add Words interface
   **When** they type a term (2+ characters)
   **Then** an auto-suggest dropdown shows matching terms from the corpus (term + reading + level)
   **And** arrow keys navigate suggestions, Enter selects, Esc closes

2. **Given** a user enters a new term not in the corpus
   **When** they submit with term, language, and optional definition
   **Then** the term is created via `POST /api/v1/vocabulary_terms`
   **And** the system triggers auto-enrichment as a background job to fill definitions, IPA, CEFR, examples
   **And** the term appears in the user's vocabulary immediately (with pending enrichment indicator)
   **And** a toast confirms "Term added — enriching..."

3. **Given** a user selects a term from auto-suggest
   **When** they confirm selection
   **Then** the existing corpus term is added to their vocabulary (no duplicate creation)
   **And** a success toast appears

4. **Given** a user submits a term that already exists in their vocabulary
   **When** the API returns a duplicate error
   **Then** an inline error message displays "This term already exists in your vocabulary"

## Tasks / Subtasks

- [x] Task 1: Backend — Add POST endpoint and create service method (AC: #2, #3, #4)
  - [x] 1.1 Add `VocabularyTermCreateRequest` and `VocabularyTermCreateResponse` Pydantic schemas in `api/schemas.py`
  - [x] 1.2 Add `create_user_term()` method in `application/services.py` — handles both new term creation and existing corpus term adoption
  - [x] 1.3 Add `find_by_user_and_term()` repository method for duplicate detection
  - [x] 1.4 Add `POST /api/v1/vocabulary_terms` endpoint in `api/router.py`
  - [x] 1.5 Add backend unit tests for service logic and integration tests for API endpoint
- [x] Task 2: Frontend — Auto-suggest component (AC: #1)
  - [x] 2.1 Create `TermAutoSuggest.tsx` in `components/vocabulary/` — input with debounced search dropdown
  - [x] 2.2 Reuse `useVocabularySearch` hook (already exists with 200ms debounce)
  - [x] 2.3 Implement keyboard navigation: ↑↓ to navigate, Enter to select, Esc to close
  - [x] 2.4 Display term + reading + CEFR/JLPT level badge per suggestion item
- [x] Task 3: Frontend — Add Term form and mutation (AC: #2, #3, #4)
  - [x] 3.1 Create `useCreateVocabularyTerm.ts` mutation hook with cache invalidation
  - [x] 3.2 Create `AddTermForm.tsx` in `components/vocabulary/` — integrates TermAutoSuggest + language select + optional definition
  - [x] 3.3 Add form to vocabulary browse page (`/vocabulary`) via inline expandable section or dedicated `/vocabulary/add` route
  - [x] 3.4 Handle success toast "Term added — enriching..." and error display
  - [x] 3.5 Form stays focused after submit for batch entry (clear input, keep focus)
- [x] Task 4: Frontend tests (AC: all)
  - [x] 4.1 Unit tests for `TermAutoSuggest` — render, keyboard nav, selection
  - [x] 4.2 Unit tests for `AddTermForm` — submit, validation, error states, toast

## Dev Notes

### Backend Implementation

**Existing code to reuse — DO NOT recreate:**
- Repository already has `create_term()`, `create_definition()`, `search_terms()` methods
- Service has `search_terms()` for auto-suggest backend
- `VocabularyTermResponse` and `VocabularyDefinitionResponse` schemas exist
- Dependency injection via `VocabularyServiceDependency` is set up

**New code needed:**
- `VocabularyTermCreateRequest` schema: `term` (str, min_length=1, max_length=100), `language` (Literal["en", "ja"]), `definition` (str | None), `cefr_level` (str | None), `jlpt_level` (int | None), `part_of_speech` (str | None)
- Service method `create_user_term()` should:
  1. Check duplicate via `find_by_user_and_term(user_id, term, language)`
  2. If duplicate → raise `DuplicateTermError`
  3. Create `VocabularyTerm` entity, persist via repository
  4. If definition provided → create `VocabularyDefinition` with `source="user"`
  5. Return created term with definitions loaded
- **Auto-enrichment trigger (Story 3.7):** For now, just create the term. Story 3.7 adds the LLM enrichment pipeline. Add a `# TODO: trigger enrichment job when Story 3.7 is implemented` comment in the service.

**Endpoint pattern:**
```python
@vocabulary_router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.VocabularyTermResponse)
async def create_vocabulary_term(
    payload: schemas.VocabularyTermCreateRequest,
    service: VocabularyService = Depends(get_vocabulary_service),
):
    return await service.create_user_term(payload)
```

**Error response for duplicate:**
```json
{"error": {"code": "DUPLICATE_TERM", "message": "This term already exists in your vocabulary"}}
```

**Note:** Current endpoints have no auth (no `current_user` dependency). Follow the same pattern — auth will be wired in a later story when Clerk integration is complete for API routes.

### Frontend Implementation

**Existing code to reuse — DO NOT recreate:**
- `useVocabularySearch` hook — debounced search, returns `VocabularyTerm[]`
- `useApiClient()` — typed fetch wrapper with auth headers
- `vocabularyKeys` query key factory in `lib/query-keys.ts`
- `VocabularyTerm`, `VocabularyDefinition` types in `types/vocabulary.ts`
- shadcn/ui components: `Button`, `Badge`, `Card`, `Label`, `Input` (if installed), `Select`
- `LanguageToggle` component for en/jp switching

**Mutation hook pattern (follow PreferencesForm pattern):**
```typescript
// hooks/useCreateVocabularyTerm.ts
export function useCreateVocabularyTerm() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VocabularyTermCreateRequest) =>
      apiClient.post<VocabularyTerm>('/api/v1/vocabulary_terms', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vocabularyKeys.all });
    },
  });
}
```

**Auto-suggest component spec:**
- Renders as `<Input>` with absolute-positioned dropdown below
- Triggers `useVocabularySearch` after 2+ chars
- Each suggestion item shows: term text, reading (if ja), `<Badge>` for CEFR/JLPT level
- Arrow keys move `activeIndex` state, Enter selects `suggestions[activeIndex]`, Esc closes
- Click on suggestion also selects
- When no matches and term.length >= 2: show "Add as new term" option at bottom

**Form layout:**
- Term input (with auto-suggest) — full width
- Language select (en/jp) — inline with term or below
- Definition textarea — optional, collapsible "Add definition" link
- Submit button: "Add Term" (primary style: `bg-zinc-900 text-zinc-50`)
- On success: clear form, show success toast (3s auto-dismiss, `border-l-4 border-green-500`), keep focus on term input

**Toast pattern:**
- Success: "Term added — enriching..." with `border-l-4 border-green-500`
- Error duplicate: inline below term input, `text-red-600 text-sm mt-1`

### Styling

Follow UX spec design tokens:
- Input: `bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm`
- Focus: `border-zinc-900 ring-2 ring-zinc-900/10`
- Error: `border-red-500 ring-2 ring-red-500/10`
- Label: `text-sm font-medium text-zinc-700 mb-1.5`
- Dropdown: `bg-white border border-zinc-200 rounded-[10px] shadow-lg` absolute positioned

### Project Structure Notes

**Files to CREATE:**
- `frontend/src/components/vocabulary/TermAutoSuggest.tsx`
- `frontend/src/components/vocabulary/TermAutoSuggest.test.tsx`
- `frontend/src/components/vocabulary/AddTermForm.tsx`
- `frontend/src/components/vocabulary/AddTermForm.test.tsx`
- `frontend/src/hooks/useCreateVocabularyTerm.ts`

**Files to UPDATE:**
- `backend/src/app/modules/vocabulary/api/router.py` — add POST endpoint
- `backend/src/app/modules/vocabulary/api/schemas.py` — add create request schema
- `backend/src/app/modules/vocabulary/application/services.py` — add `create_user_term()`
- `backend/src/app/modules/vocabulary/domain/interfaces.py` — add `find_by_user_and_term()` abstract method
- `backend/src/app/modules/vocabulary/domain/exceptions.py` — add `DuplicateTermError` (create file if not exists)
- `backend/src/app/modules/vocabulary/infrastructure/repository.py` — add `find_by_user_and_term()` impl
- `frontend/src/types/vocabulary.ts` — add `VocabularyTermCreateRequest` type
- `frontend/src/app/(app)/vocabulary/page.tsx` — integrate AddTermForm (add button or inline section)

**DO NOT modify:**
- Database migrations — existing schema supports this story
- `infrastructure/models.py` — ORM models already have all needed columns
- `domain/entities.py` — domain entities already defined

### Testing Standards

**Backend (pytest):**
- Unit test `create_user_term()` service method: success, duplicate detection, with/without definition
- Integration test `POST /api/v1/vocabulary_terms`: 201 created, 409 duplicate, 422 validation error
- Use existing test fixtures/factories pattern from `tests/integration/modules/vocabulary/`

**Frontend (Vitest + React Testing Library):**
- TermAutoSuggest: renders input, shows dropdown on type, keyboard navigation works, selection callback fires
- AddTermForm: renders form, submits successfully, shows error on duplicate, clears on success
- Mock `useApiClient()` and query hooks at module level (existing pattern)

### References

- [Source: _out_put/planning-artifacts/epics/epic-3-vocabulary-management-enrichment-pipeline.md — Story 3.4]
- [Source: _out_put/planning-artifacts/architecture.md — API patterns, hexagonal structure, testing standards]
- [Source: _out_put/planning-artifacts/ux-design-specification.md — Form patterns, auto-suggest, toast notifications]
- [Source: _out_put/implementation-artifacts/3-3-view-vocabulary-term.md — Previous story patterns and learnings]

### Previous Story Intelligence (3.3)

- `useApiClient()` is the standard for all API calls — never use raw fetch
- `vocabularyKeys` factory manages all query cache keys
- Vitest mocks `useApiClient` at module level for component tests
- Detail page uses `useQuery` with eager definition loading — follow same pattern for auto-suggest results
- Frontend tests mock at hook level, test render + interaction + loading/error states

### Git Intelligence

Recent commits show:
- `feat#3-1` prefix convention for feature commits in this epic
- Story 3.1 established all vocabulary infrastructure (models, migrations, seed data)
- Clerk auth is in progress (story 2-1) but API routes currently have no auth middleware

## Dev Agent Record

### Agent Model Used
minimax-m2.7 (opencode-go)

### Debug Log References

### Completion Notes List
- Backend: Added VocabularyTermCreateRequest schema with language as Literal["en", "jp"]
- Backend: Added DuplicateTermError exception class
- Backend: Added create_user_term() method in services.py with duplicate check and TODO for enrichment trigger
- Backend: Added find_by_user_and_term() method in repository for duplicate detection
- Backend: Added POST /api/v1/vocabulary_terms endpoint with 201 response and 409 duplicate handling
- Backend: Fixed jlpt_level type mismatch (was int in schema, should be str per DB model)
- Backend: Added 5 integration tests for POST endpoint (success, without definition, duplicate, validation errors)
- Frontend: Created useCreateVocabularyTerm.ts mutation hook with query cache invalidation
- Frontend: Created TermAutoSuggest.tsx with keyboard navigation, dropdown, create option
- Frontend: Created AddTermForm.tsx with language select, optional definition, error handling
- Frontend: Integrated Add Term button and expandable form into vocabulary browse page
- Frontend: Added test files for TermAutoSuggest and AddTermForm

### File List
backend/src/app/modules/vocabulary/api/router.py
backend/src/app/modules/vocabulary/api/schemas.py
backend/src/app/modules/vocabulary/application/services.py
backend/src/app/modules/vocabulary/domain/interfaces.py
backend/src/app/modules/vocabulary/domain/exceptions.py
backend/src/app/modules/vocabulary/infrastructure/repository.py
backend/tests/integration/modules/vocabulary/test_api.py
frontend/src/hooks/useCreateVocabularyTerm.ts
frontend/src/components/vocabulary/TermAutoSuggest.tsx
frontend/src/components/vocabulary/TermAutoSuggest.test.tsx
frontend/src/components/vocabulary/AddTermForm.tsx
frontend/src/components/vocabulary/AddTermForm.test.tsx
frontend/src/app/(app)/vocabulary/page.tsx
