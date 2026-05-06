# Story 3.3: View Vocabulary Term (Single-Language & Parallel Mode)

Status: review

## Story

As a **user**,
I want to view a vocabulary term with its definition, IPA, examples, and level in single-language or parallel bilingual mode,
so that I can study terms with the appropriate cognitive load for my learning stage.

## Acceptance Criteria

1. **Given** a user selects a vocabulary term **When** the term detail page loads (`GET /api/v1/vocabulary_terms/{term_id}`) **Then** the term is displayed in single-language view (default) showing: term, definition, IPA (JetBrains Mono font), example sentences, CEFR level, JLPT level, part of speech, related terms (FR8)
2. **Given** a user selects a vocabulary term **Then** Japanese text renders in Noto Sans JP, Latin in Inter, IPA in JetBrains Mono (automatic via unicode-range)
3. **Given** a user toggles parallel mode (FR9) **When** they click the parallel toggle or press `Tab` **Then** both English and Japanese definitions are displayed side-by-side
4. **Given** parallel mode is toggled **Then** the toggle state persists for the session
5. **Given** a definition has not been cross-validated against JMdict (FR37) **When** it is displayed **Then** a warning indicator icon appears next to the definition

## Tasks / Subtasks

- [x] Task 1: Create term detail page route and component (AC: #1, #2)
  - [x] `frontend/src/app/(app)/vocabulary/[termId]/page.tsx` — term detail page with dynamic route
  - [x] Fetch term via `GET /api/v1/vocabulary_terms/{term_id}` using TanStack Query
  - [x] Display: term heading (28px, 600wt), reading, metadata tags (part_of_speech, CEFR badge, JLPT badge)
  - [x] Display: definition, IPA (`font-mono` / JetBrains Mono), example sentences (gray bg with left border)
  - [x] Display: related terms via `GET /api/v1/vocabulary_terms/{term_id}/children`
  - [x] JMdict warning indicator for `validated_against_jmdict === false` (AC: #5)
  - [x] Loading skeleton state, error state, 404 handling
- [x] Task 2: Create useVocabularyTerm hook (AC: #1)
  - [x] `frontend/src/hooks/useVocabularyTerm.ts`
  - [x] Uses `vocabularyKeys.detail(termId)` query key
  - [x] Returns `VocabularyTerm` from existing API endpoint
- [x] Task 3: Implement parallel mode toggle (AC: #3, #4)
  - [x] `frontend/src/components/vocabulary/LanguageToggle.tsx` — toggle button component
  - [x] `Tab` keyboard shortcut to toggle parallel view on detail page
  - [x] Side-by-side layout: EN definition left, JP definition right
  - [x] Session persistence: store toggle state in `sessionStorage`
  - [x] Single-language default: show only definitions matching term's primary language
- [x] Task 4: Apply bilingual typography (AC: #2)
  - [x] Ensure `Noto Sans JP` loaded with unicode-range for CJK (U+3040-309F, U+30A0-30FF, U+4E00-9FFF)
  - [x] Ensure `JetBrains Mono` applied to IPA text (`/ˈprɑːtəkɔːl/`)
  - [x] Japanese text: line-height 1.8 (vs Latin 1.6)
  - [x] Verify font-face declarations in `globals.css` — added `.font-ipa` and `.text-jp` utilities
- [x] Task 5: Navigate from vocabulary list to detail (AC: #1)
  - [x] Wire term cards in `vocabulary/page.tsx` to link to `/vocabulary/{termId}`
  - [x] Back navigation from detail page
- [x] Task 6: Frontend tests (AC: #1, #3, #5)
  - [x] `frontend/src/app/(app)/vocabulary/[termId]/page.test.tsx`
  - [x] Test: renders term details (term, definition, IPA, examples, levels)
  - [x] Test: parallel toggle shows/hides bilingual definitions
  - [x] Test: JMdict warning shown when `validated_against_jmdict` is false
  - [x] Test: loading and error states

## Dev Notes

### Existing Codebase Patterns (MUST FOLLOW)

**Backend endpoint already exists** — `GET /api/v1/vocabulary_terms/{term_id}` in `backend/src/app/modules/vocabulary/api/router.py` (lines 60-77). Returns `VocabularyTermResponse` with definitions eagerly loaded. **No backend changes needed for this story.**

**Frontend API Client** — use `useApiClient()` from `frontend/src/lib/api-client.ts`. Pattern:
```typescript
const client = useApiClient()
const data = await client<VocabularyTerm>(`/vocabulary_terms/${termId}`)
```

**TanStack Query Pattern** — see `frontend/src/hooks/useVocabularySearch.ts`:
```typescript
import { useQuery } from '@tanstack/react-query'
import { vocabularyKeys } from '@/lib/query-keys'
import { useApiClient } from '@/lib/api-client'
```

**Query Keys** (already in `frontend/src/lib/query-keys.ts`):
```typescript
vocabularyKeys.detail(id: number) // ['vocabulary', 'detail', id]
vocabularyKeys.children(parentId: number) // ['vocabulary', 'children', parentId]
```

**Frontend Types** (already in `frontend/src/types/vocabulary.ts`):
- `VocabularyTerm` — id, term, language, parent_id, cefr_level, jlpt_level, part_of_speech, definitions[], created_at
- `VocabularyDefinition` — id, language, definition, ipa, examples[], source, validated_against_jmdict

### Parallel Mode Implementation

**Single-Language View (Default):**
- Show definitions where `definition.language` matches `term.language`
- Display: term heading, reading (if JP), metadata tags, definition text, IPA, examples

**Parallel View (Toggle ON):**
- Show ALL definitions grouped by language side-by-side
- Left column: English definitions
- Right column: Japanese definitions
- Use CSS grid: `grid-cols-1 md:grid-cols-2 gap-6`

**Toggle State Persistence:**
- Use `sessionStorage` key `vocabulary_parallel_mode` (boolean)
- Or if Zustand `useUIStore` already exists, add `parallelMode` flag there
- Check existing Zustand stores before creating new state management

### Typography CSS

Ensure these font declarations exist (add to `globals.css` if missing):
```css
/* IPA text */
.font-ipa { font-family: 'JetBrains Mono', 'Fira Code', monospace; }

/* Japanese text line-height adjustment */
.text-jp { line-height: 1.8; }
```

Unicode-range auto-switching should already work via Next.js font config. Verify in `frontend/src/app/layout.tsx` that fonts are loaded.

### Component Styling (Follow UX Spec)

- Card: `bg-white border border-zinc-200 rounded-[14px] p-10 shadow-sm`
- Term heading: `text-2xl font-semibold text-zinc-950` (28px)
- Metadata: `text-sm text-zinc-500`
- IPA: `font-mono text-sm text-zinc-600`
- Examples: `bg-zinc-100 border-l-2 border-zinc-300 px-4 py-3 text-sm`
- Level badges: shadcn/ui `Badge` component
- JMdict warning: `AlertTriangle` icon from lucide-react, `text-amber-500`
- Empty/error: centered icon + title + description pattern

### What This Story Does NOT Include

- No new backend endpoints or migrations (everything exists from 3.1 + 3.2)
- No enrichment panel or LLM trigger (Story 3.7)
- No term creation/edit (Story 3.4)
- No command palette integration (Story 3.8)
- No cross-language interference tracking for diagnostics (Story 6.x)

### Previous Story Intelligence (from 3-2)

**Key learnings from Story 3.2:**
- `useApiClient()` hook returns a typed client function
- `useDebounce` was implemented as custom hook — reuse pattern
- Vocabulary page at `frontend/src/app/(app)/vocabulary/page.tsx` with term cards
- shadcn/ui components: `Badge`, `Skeleton`, `Input`, `Select` already used
- Term cards display: term, language, level tags, definition preview
- No authentication required on vocabulary endpoints (public read)
- Dev agent: openai/gpt-5.4; unit tests 8/8, frontend tests 6/6

### Project Structure Notes

Frontend files to CREATE:
- `frontend/src/app/(app)/vocabulary/[termId]/page.tsx` (NEW)
- `frontend/src/app/(app)/vocabulary/[termId]/page.test.tsx` (NEW)
- `frontend/src/hooks/useVocabularyTerm.ts` (NEW)
- `frontend/src/components/vocabulary/LanguageToggle.tsx` (NEW)

Frontend files to UPDATE:
- `frontend/src/app/(app)/vocabulary/page.tsx` — add Link to term detail from term cards
- `frontend/src/app/globals.css` — add `.font-ipa` and `.text-jp` utility classes if not present
- `frontend/src/app/layout.tsx` — verify/add JetBrains Mono and Noto Sans JP font imports

Backend files: **NONE** — all endpoints already exist from Stories 3.1 and 3.2.

### References

- [Source: _out_put/planning-artifacts/epics/epic-3-vocabulary-management-enrichment-pipeline.md#Story 3.3]
- [Source: _out_put/planning-artifacts/architecture.md#Component Strategy — LanguageToggle]
- [Source: _out_put/planning-artifacts/architecture.md#Typography — Font Stack, unicode-range]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Single-Language Focus, Bilingual on Demand]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Component Strategy — ReviewCard anatomy]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Visual Design Foundation — Color System]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Keyboard Shortcuts — Tab toggle]
- [Source: backend/src/app/modules/vocabulary/api/router.py — GET /{term_id} endpoint]
- [Source: frontend/src/types/vocabulary.ts — VocabularyTerm, VocabularyDefinition]
- [Source: frontend/src/lib/query-keys.ts — vocabularyKeys.detail, vocabularyKeys.children]
- [Source: _out_put/implementation-artifacts/3-2-browse-search-vocabulary-corpus.md — previous story learnings]

## Dev Agent Record

### Agent Model Used

openai/gpt-5.4

### Debug Log References

Lint fix: Removed `title` prop from AlertTriangle icon (not valid for Lucide), wrapped in span instead.

### Completion Notes List

- Created `useVocabularyTerm` hook for fetching single vocabulary term with `vocabularyKeys.detail(termId)` query key
- Created `useVocabularyTermChildren` hook for fetching related terms
- Created `LanguageToggle` component with Languages icon from lucide-react
- Created term detail page at `frontend/src/app/(app)/vocabulary/[termId]/page.tsx` with:
  - Single-language view (default): filters definitions by term's primary language
  - Parallel mode: side-by-side English and Japanese definitions using CSS grid
  - Tab keyboard shortcut to toggle parallel view
  - Session persistence via `vocabulary_parallel_mode` sessionStorage key
  - JMdict warning indicator (amber AlertTriangle icon) for unvalidated definitions
  - Loading skeleton, error state, and 404 handling
- Linked term cards in vocabulary list to detail page using Next.js Link
- Added `.font-ipa` and `.text-jp` utility classes in globals.css
- Added 9 passing tests for vocabulary term detail page

### File List

New files created:
- `frontend/src/hooks/useVocabularyTerm.ts`
- `frontend/src/components/vocabulary/LanguageToggle.tsx`
- `frontend/src/app/(app)/vocabulary/[termId]/page.tsx`
- `frontend/src/app/(app)/vocabulary/[termId]/page.test.tsx`

Modified files:
- `frontend/src/app/(app)/vocabulary/page.tsx` — added Link wrapper around TermCard
- `frontend/src/app/globals.css` — added `.font-ipa` and `.text-jp` utility classes
