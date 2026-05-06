# Story 4.2: ReviewCard Component & Card Reveal Flow

Status: review

## Story

As a **user**,
I want to see vocabulary cards in a clean review interface and reveal answers with a single keypress,
so that I can focus on recall without UI distractions.

## Acceptance Criteria

1. **Given** a user is on the Today's Queue page with cards due **When** the page loads **Then** the first card displays in front state: term (28px, #09090B), Japanese reading (18px, #3F3F46), part-of-speech/level tag (13px, #71717A), session counter "1/24" per UX-DR3 **And** "Press [Space] to reveal answer" hint is shown **And** the card uses `bg-zinc-100 border border-zinc-200 rounded-[14px] p-10` styling
2. **Given** a user presses Space (or taps the card on mobile) **When** the card transitions to revealed state **Then** definition, IPA (JetBrains Mono), example sentence (gray bg with left border), and CEFR level appear below the term **And** Tab key toggles Japanese definition (parallel mode) for this card only **And** the rating buttons appear below the revealed content **And** the reveal transition is ≤150ms (instant swap if prefers-reduced-motion)
3. **Given** the queue header loads **When** cards are due **Then** StatChip components display: card count, estimated time, retention rate

## Tasks / Subtasks

- [x] Task 1: Create SRS types (AC: all)
  - [x] Create `frontend/src/types/srs.ts` with: SrsCard, DueCardsResponse, QueueStatsResponse, ReviewRequest, ReviewResponse types
  - [x] Types must match backend API schemas from story 4-1 (id, term_id, language, due_at, fsrs_state, stability, difficulty, reps, lapses)
- [x] Task 2: Create useDueCards hook (AC: #1, #3)
  - [x] `frontend/src/hooks/useDueCards.ts` — TanStack Query hook fetching `GET /srs_cards/queue`
  - [x] Join card data with vocabulary term data (each card has term_id → fetch term details)
  - [x] Use existing `srsKeys.queue(mode)` query key from `lib/query-keys.ts`
  - [x] Use existing `useApiClient()` from `lib/api-client.ts`
- [x] Task 3: Create useQueueStats hook (AC: #3)
  - [x] `frontend/src/hooks/useQueueStats.ts` — TanStack Query hook fetching `GET /srs_cards/queue-stats`
  - [x] Use existing `srsKeys.queueStats()` query key
- [x] Task 4: Extend useReviewStore (AC: #1, #2)
  - [x] Add to existing `stores/review-store.ts`: currentCardIndex, isRevealed, showJpDefinition, sessionCards[], revealCard(), nextCard(), toggleJpDefinition(), resetSession()
  - [x] Keep existing queueMode state
- [x] Task 5: Create ReviewCard component (AC: #1, #2)
  - [x] `frontend/src/components/review/ReviewCard.tsx`
  - [x] Front state: term (text-xl font-semibold text-text-primary), reading (text-base text-text-secondary), POS/level badge (text-xs text-text-muted), session counter top-right
  - [x] Revealed state: add definition, IPA (font-mono), example sentence (bg-zinc-50 border-l-2 border-zinc-300 pl-3 py-2), CEFR badge
  - [x] Tab toggles JP definition (only when revealed) — per-card toggle via store's showJpDefinition
  - [x] Styling: `bg-zinc-100 border border-zinc-200 rounded-[14px] p-10 text-center`
  - [x] Card transition: 150ms, respects `prefers-reduced-motion` (instant swap)
  - [x] Space hint: `<kbd>` element styled `bg-zinc-800 border-zinc-700 text-zinc-200`
  - [x] Accessibility: `role="article"`, `aria-label="Vocabulary card: {term}"`, rating button group `role="group" aria-label="Rate your recall"`
- [x] Task 6: Update QueueHeader with retention rate StatChip (AC: #3)
  - [x] Add retention rate StatChip to existing `QueueHeader.tsx` (requires data from queue-stats)
  - [x] Pass retention stat from parent if available
- [x] Task 7: Build Review page (AC: #1, #2, #3)
  - [x] Replace placeholder in `frontend/src/app/(app)/review/page.tsx`
  - [x] Layout: QueueHeader → CatchUpBanner (if overdue≥100) → ReviewCard → RatingButtons placeholder
  - [x] Empty state when 0 due cards: "All caught up!" message with suggestions
  - [x] Loading state: Skeleton matching card layout
  - [x] Wire keyboard handler: Space to reveal (when not revealed)
  - [x] Use useDueCards + useQueueStats + useReviewStore
- [x] Task 8: Add keyboard event handling (AC: #2)
  - [x] Create `frontend/src/hooks/useReviewKeyboard.ts`
  - [x] Space: reveal card (only when in front state)
  - [x] Tab: toggle JP definition (only when revealed)
  - [x] Prevent default Space scroll behavior
  - [x] Only active when review page is focused (cleanup on unmount)
- [x] Task 9: Write component tests (AC: #1, #2)
  - [x] `ReviewCard.test.tsx` — render front state, test Space reveal, test Tab JP toggle
  - [x] Co-located with component per project convention
- [x] Task 10: Update srsKeys if needed (AC: all)
  - [x] Add `srsKeys.card(id)` key for individual card queries if needed
  - [x] Add `srsKeys.dueCards()` alias if different from queue

## Dev Notes

### CRITICAL: Story 4-1 Dependency

This story depends on story 4-1 (SRS Data Model & FSRS Integration) being implemented first. The backend endpoints this story consumes:
- `GET /api/v1/srs_cards/queue` — returns due cards with term_id, language, due_at, fsrs_state
- `GET /api/v1/srs_cards/queue-stats` — returns due_count, estimated_minutes, has_overdue, overdue_count

If 4-1 is not yet deployed, use mock data matching the expected API response shapes.

### Existing Code State (UPDATE files)

| File | Current State | What Changes |
|------|--------------|-------------|
| `frontend/src/app/(app)/review/page.tsx` | Placeholder stub ("Coming soon") | Full review page with QueueHeader, ReviewCard, keyboard handling |
| `frontend/src/stores/review-store.ts` | Only queueMode state | Add currentCardIndex, isRevealed, showJpDefinition, sessionCards, actions |
| `frontend/src/components/review/index.ts` | Exports CatchUpBanner, QueueHeader | Add ReviewCard export |
| `frontend/src/components/review/QueueHeader.tsx` | Shows dueCount + estimatedMinutes StatChips | Add retention rate StatChip |
| `frontend/src/lib/query-keys.ts` | srsKeys has queueStats(), queue(mode) | Possibly add card(id) key |

### NEW files to create

| File | Purpose |
|------|---------|
| `frontend/src/types/srs.ts` | SRS card types matching backend API |
| `frontend/src/hooks/useDueCards.ts` | TanStack Query for fetching due cards |
| `frontend/src/hooks/useQueueStats.ts` | TanStack Query for queue stats |
| `frontend/src/hooks/useReviewKeyboard.ts` | Keyboard event handler for review flow |
| `frontend/src/components/review/ReviewCard.tsx` | Main review card component |
| `frontend/src/components/review/ReviewCard.test.tsx` | Co-located tests |

### MUST PRESERVE

- Existing `CatchUpBanner` component — use it on review page when overdueCount ≥ 100
- Existing `QueueHeader` component — extend, don't replace
- Existing `useReviewStore` queueMode state and setQueueMode action
- Existing barrel export in `components/review/index.ts` — add new exports
- Existing `srsKeys` query keys — extend, don't modify existing keys
- `useApiClient()` pattern from `lib/api-client.ts` — all API calls go through this

### Card Data Shape

Each due card from the backend has `term_id` but NOT the vocabulary term details. The frontend needs to join SRS card data with vocabulary term data to display:
- `term` (string) — the word itself
- Japanese reading (from vocabulary definitions)
- `part_of_speech`, `cefr_level`, `jlpt_level`
- `definitions` array with IPA, examples

**Strategy:** Either fetch term details alongside due cards (batch endpoint), or use existing `vocabularyKeys.detail(termId)` for each card. Recommend fetching all needed term data in a single query with the due cards response (backend story 4-1's `DueCardResponse` may need to include term data — if not, use per-card vocabulary queries with TanStack Query's prefetching).

### UX Specifications (from UX Design Doc)

**Card Front State:**
```
┌─────────────────────────────────────────┐
│ ENGLISH (lang indicator)      1 / 24    │
│                                         │
│            protocol                     │  ← 28px (#09090B) font-semibold
│           プロトコル                      │  ← 18px (#3F3F46)
│         noun · IT · B2                  │  ← 13px (#71717A)
│                                         │
│  ─────────────────────────────────────  │
│       Press [Space] to reveal answer    │
└─────────────────────────────────────────┘
```

**Card Revealed State (adds below term):**
- Definition text (16px, #3F3F46)
- IPA in JetBrains Mono (`font-mono`)
- Example sentence: `bg-zinc-50 border-l-2 border-zinc-300 pl-3 py-2 text-sm text-text-secondary`
- CEFR level badge
- Tab → shows Japanese definition inline (for bilingual terms only)
- Rating buttons zone appears (placeholder for story 4-3)

**Styling tokens:**
- Card: `bg-zinc-100 border border-zinc-200 rounded-[14px] p-10`
- Kbd hint: `bg-zinc-800 border-zinc-700 text-zinc-200 rounded px-1.5 text-xs`
- Transition: 150ms, `@media (prefers-reduced-motion: reduce)` → instant

**Empty state (0 cards due):**
- Icon centered, "All caught up!" title, suggestions to add words or review weak cards
- Single CTA button "Add Words" linking to vocabulary page

### Responsive Behavior

| Breakpoint | Card padding | Term size | Rating layout |
|------------|-------------|-----------|---------------|
| Mobile (<640px) | `p-6` | 24px | 2x2 grid (story 4-3) |
| Tablet (640-1024px) | `p-8` | 26px | Row of 4 |
| Desktop (>1024px) | `p-10` | 28px | Row of 4 |

### Accessibility

- `role="article"` on card wrapper, `aria-label="Vocabulary card: {term}"`
- `aria-live="polite"` region for session counter updates
- Space key handling: `event.preventDefault()` to stop page scroll
- Focus management: card should be focusable (`tabIndex={0}`)
- All text meets WCAG AA contrast (zinc-900 on zinc-100 = 17.4:1)

### Architecture Compliance

- **Component pattern:** Compose on shadcn/ui Card primitive
- **State management:** Zustand for review session state (isRevealed, currentCardIndex), TanStack Query for server data
- **File organization:** Components in `components/review/`, hooks in `hooks/`, tests co-located
- **Barrel exports:** Update `components/review/index.ts`
- **API pattern:** Use `useApiClient()` hook → `createApiClient(getToken)` for all fetches
- **Naming:** PascalCase components, camelCase hooks, types in `types/srs.ts`

### Testing Standards

- Co-located tests: `ReviewCard.test.tsx` next to `ReviewCard.tsx`
- Testing library: Vitest + React Testing Library (existing project setup)
- Test front state rendering, Space key reveal, Tab JP toggle, empty state
- Mock API responses for TanStack Query tests

### Previous Story Intelligence (4-1)

Story 4-1 establishes:
- Backend SRS card model with FSRS state stored as JSONB
- `GET /api/v1/srs_cards/queue` returns cards ordered overdue > due > new
- `GET /api/v1/srs_cards/queue-stats` returns due_count, estimated_minutes, has_overdue, overdue_count
- `POST /api/v1/srs_cards/{id}/review` for rating (used by story 4-3, not this story)
- SRS card has: id, term_id, language, due_at, fsrs_state, stability, difficulty, reps, lapses

### Note on Rating Buttons

This story renders a **placeholder zone** for rating buttons when the card is revealed. The actual RatingButton component and rating submission logic are in **story 4-3**. Do NOT implement rating functionality here — just reserve the visual space and show a disabled placeholder like "Rating buttons will appear here" or render empty div with min-height.

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.2]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#ReviewCard Component]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Experience Mechanics — The Review Cycle]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Responsive Design]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend Architecture — TanStack Query, Zustand]
- [Source: _out_put/planning-artifacts/architecture.md#Component Boundaries]

## Dev Agent Record

### Agent Model Used

deepseek-v4-pro

### Debug Log References

- TypeScript typecheck: passed (no errors)
- ReviewCard tests: 9/9 passed
- Full review test suite: 3 files, 12 tests passed
- Existing tests (vocabulary): 12 pre-existing failures unrelated to this story

### Completion Notes List

- Created `frontend/src/types/srs.ts` with SrsCard, DueCardsResponse, QueueStatsResponse, ReviewRequest, ReviewResponse, SessionCard types matching backend API schemas from story 4-1
- Created `frontend/src/hooks/useDueCards.ts` — TanStack Query hook that fetches due cards and enriches them with vocabulary term data via parallel `useQueries` for each term_id
- Created `frontend/src/hooks/useQueueStats.ts` — TanStack Query hook for queue stats
- Extended `frontend/src/stores/review-store.ts` with session state (currentCardIndex, isRevealed, showJpDefinition, sessionCards) and actions (setSessionCards, revealCard, nextCard, toggleJpDefinition, resetSession) while preserving existing queueMode
- Created `frontend/src/components/review/ReviewCard.tsx` with front/revealed states, responsive styling (p-6/p-8/p-10), 150ms transition respecting reduced motion, kbd Space hint, JP definition toggle, rating placeholder, accessibility attributes
- Created `frontend/src/hooks/useReviewKeyboard.ts` — keyboard handler for Space (reveal) and Tab (toggle JP definition), with cleanup on unmount
- Updated `frontend/src/components/review/QueueHeader.tsx` with optional retentionRate StatChip
- Updated `frontend/src/lib/query-keys.ts` with srsKeys.card(id) and srsKeys.dueCards() keys
- Replaced `frontend/src/app/(app)/review/page.tsx` placeholder with full review page featuring QueueHeader, CatchUpBanner, ReviewCard, loading/error/empty states, and keyboard handling
- Created `frontend/src/components/review/ReviewCard.test.tsx` with 9 tests covering front state rendering, revealed state, Space hint visibility, JP definition toggle, accessibility, edge cases (null term, missing English definition)
- Updated `frontend/src/components/review/index.ts` barrel export to include ReviewCard

### File List

- `frontend/src/types/srs.ts` (NEW)
- `frontend/src/hooks/useDueCards.ts` (NEW)
- `frontend/src/hooks/useQueueStats.ts` (NEW)
- `frontend/src/hooks/useReviewKeyboard.ts` (NEW)
- `frontend/src/stores/review-store.ts` (MODIFIED)
- `frontend/src/components/review/ReviewCard.tsx` (NEW)
- `frontend/src/components/review/ReviewCard.test.tsx` (NEW)
- `frontend/src/components/review/QueueHeader.tsx` (MODIFIED)
- `frontend/src/components/review/index.ts` (MODIFIED)
- `frontend/src/lib/query-keys.ts` (MODIFIED)
- `frontend/src/app/(app)/review/page.tsx` (MODIFIED)
