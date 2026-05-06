# Story 4.3: RatingButton Component & Card Rating

Status: review

## Story

As a **user**,
I want to rate each card (Again/Hard/Good/Easy) with keyboard shortcuts showing next-review intervals,
so that I can self-assess quickly and trust the scheduling system.

## Acceptance Criteria

1. **Given** a card is in revealed state **When** the rating buttons appear **Then** 4 buttons display: Again (1), Hard (2), Good (3), Easy (4) with next-review interval below each (e.g., "<1m", "6m", "1d", "4d") **And** each button has semantic color hover: Again (`hover:bg-red-50`), Hard (`hover:bg-amber-50`), Good (`hover:bg-green-50`), Easy (`hover:bg-zinc-100`) **And** buttons have ARIA label: "Rate as {label}, next review in {interval}"
2. **Given** a user presses 1, 2, 3, or 4 (or taps a rating button on mobile) **When** the rating is submitted (`POST /api/v1/srs_cards/{id}/review`) **Then** py-fsrs calculates the new FSRS state and next due_at **And** the review is recorded in srs_reviews (rating, response_time_ms, timestamp) **And** a subtle border color flash appears (100ms): Again `border-red-300`, Hard `border-amber-300`, Good `border-green-300`, Easy `border-zinc-400` **And** the next card auto-advances (slide transition <=150ms) **And** the session counter updates
3. **Given** a user on mobile **When** rating buttons display **Then** buttons render in a 2x2 grid layout **And** minimum touch target is 48x48px with 8px gap

## Tasks / Subtasks

- [x] Task 1: Create RatingButton component (AC: #1, #3)
  - [x] `frontend/src/components/review/RatingButton.tsx`
  - [x] Four variants: `again`, `hard`, `good`, `easy`
  - [x] Props: variant, keyNumber (1-4), label, interval, onRate, disabled
  - [x] Semantic hover colors per UX-DR4
  - [x] Active state: scale-[0.97] on press
  - [x] Disabled state: opacity-40 cursor-not-allowed
  - [x] kbd badge showing key number in corner
  - [x] Interval text below label ("<1m", "6m", "1d", "4d")
  - [x] ARIA: `aria-label="Rate as {label}, next review in {interval}"`
  - [x] Responsive: desktop row layout (flex-row), mobile 2x2 grid
- [x] Task 2: Create useRatingMutation hook (AC: #2)
  - [x] `frontend/src/hooks/useRatingMutation.ts`
  - [x] TanStack Query `useMutation` calling `POST /srs_cards/{card_id}/review`
  - [x] Use existing `useApiClient()` pattern
  - [x] Request body: `{ rating: number, response_time_ms: number | null }` per `ReviewRequest` type
  - [x] On success: invalidate `srsKeys.queue(queueMode)` and `srsKeys.queueStats()` queries
  - [x] Return the `ReviewResponse` data (next_due_at, interval_display)
- [x] Task 3: Integrate RatingButton into ReviewCard (AC: #1, #2)
  - [x] Replace the dashed-border placeholder div in `ReviewCard.tsx` with RatingButton row
  - [x] Accept `onRate` callback prop and derive rating intervals from API response
  - [x] Show loading state on the clicked button while mutation is pending
  - [x] Apply border flash animation (100ms) to card wrapper based on rating feedback
- [x] Task 4: Update useReviewKeyboard for rating keys (AC: #2)
  - [x] Add 1/2/3/4 key handlers to `useReviewKeyboard.ts`
  - [x] Only active when `isRevealed` is true
  - [x] Call the `rateCard` action from store
  - [x] Prevent default behavior for these keys
- [x] Task 5: Extend useReviewStore with rating state (AC: #2)
  - [x] Add to `review-store.ts`: `rateCard(rating: 1|2|3|4)` action, `lastRating` state, `isRatingInProgress` state
  - [x] `rateCard` triggers the mutation and calls `nextCard()` on success
  - [x] Track `lastRating` for the border flash visual feedback
  - [x] Clear `lastRating` after 100ms (the flash duration)
- [x] Task 6: Update review page for rating flow (AC: #2)
  - [x] Wire `useRatingMutation` in `review/page.tsx`
  - [x] Pass `onRate` handler from page → ReviewCard → RatingButton
  - [x] Handle mutation loading (disable all rating buttons) and error (toast + restore card)
  - [x] Compute response_time_ms: capture timestamp on reveal, diff on rate
- [x] Task 7: Mobile responsive layout (AC: #3)
  - [x] RatingButton row uses 2x2 grid on mobile (< 640px)
  - [x] Touch targets min 48x48px with 8px gap between buttons
  - [x] Buttons fill available width in grid
- [x] Task 8: Write component tests (AC: #1, #2, #3)
  - [x] `RatingButton.test.tsx` co-located with component
  - [x] Test all 4 variants render with correct labels and intervals
  - [x] Test hover states apply correct color classes
  - [x] Test click fires onRate callback
  - [x] Test disabled state prevents click
  - [x] Test ARIA labels
  - [x] Test mobile 2x2 grid layout
- [x] Task 9: Update barrel export (AC: all)
  - [x] Add `RatingButton` to `components/review/index.ts`

## Dev Notes

### Existing Code State (UPDATE files)

| File | Current State | What Changes |
|------|--------------|-------------|
| `frontend/src/components/review/ReviewCard.tsx` | Renders placeholder div for rating buttons when revealed (lines 124-131) | Replace placeholder with RatingButton row, add `onRate` and `isRatingInProgress` props |
| `frontend/src/stores/review-store.ts` | Has reveal, next, toggle, reset but no rating | Add `rateCard()`, `lastRating`, `isRatingInProgress`, `clearRating()` |
| `frontend/src/hooks/useReviewKeyboard.ts` | Handles Space (reveal) and Tab (JP toggle) | Add handlers for keys 1, 2, 3, 4 when card is revealed |
| `frontend/src/components/review/index.ts` | Exports CatchUpBanner, QueueHeader, ReviewCard | Add RatingButton export |
| `frontend/src/app/(app)/review/page.tsx` | Wires ReviewCard with reveal keyboard but no rating mutation | Add useRatingMutation, onRate handler, response time tracking |

### NEW files to create

| File | Purpose |
|------|---------|
| `frontend/src/components/review/RatingButton.tsx` | Four-variant rating button component |
| `frontend/src/components/review/RatingButton.test.tsx` | Co-located tests |
| `frontend/src/hooks/useRatingMutation.ts` | TanStack Query mutation for POST /srs_cards/{id}/review |

### MUST PRESERVE

- Existing `ReviewCard` front/revealed state logic — add to it, don't restructure
- Existing `useReviewStore` actions: `setSessionCards`, `revealCard`, `nextCard`, `toggleJpDefinition`, `resetSession`
- Existing `useReviewKeyboard` Space and Tab handlers
- Existing `useDueCards` and `useQueueStats` hooks — they continue to work unchanged
- Existing `srsKeys` query keys — extend if needed, don't modify existing
- Session counter display in ReviewCard (top-right "1/24")
- The CardNotDueError from backend — cards not due yet should not be ratable

### CRITICAL: Backend API Already Implemented

The rating endpoint `POST /api/v1/srs_cards/{card_id}/review` is fully implemented in story 4-1. Key API details:

**Request:**
```json
{
  "rating": 3,           // 1=Again, 2=Hard, 3=Good, 4=Easy
  "response_time_ms": 4500,
  "session_id": null      // optional UUID
}
```

**Response (`ReviewCardResponse`):**
```json
{
  "id": 123,
  "term_id": 456,
  "language": "en",
  "due_at": "2026-05-08T10:30:00Z",
  "fsrs_state": { ... },
  "stability": 3.14,
  "difficulty": 0.42,
  "reps": 5,
  "lapses": 0,
  "next_due_at": "2026-05-08T10:30:00Z",
  "interval_display": "1d"
}
```

The `interval_display` field (e.g., "&lt;1m", "6m", "2h", "1d", "4d") is computed by the `_format_interval()` helper in `backend/src/app/modules/srs/application/services.py:22-29`. Use it directly — do NOT compute intervals on the frontend.

### Rating Button Component Spec (from UX spec)

```typescript
interface RatingButtonProps {
  variant: 'again' | 'hard' | 'good' | 'easy'
  keyNumber: 1 | 2 | 3 | 4
  label: string          // "Again", "Hard", "Good", "Easy"
  interval: string       // "&lt;1m", "6m", "1d", "4d"  (from API response)
  onRate: () => void
  disabled?: boolean
}
```

**State Visuals:**

| State | Again | Hard | Good | Easy |
|-------|-------|------|------|------|
| Default | White bg, zinc-200 border | White bg, zinc-200 border | White bg, zinc-200 border | White bg, zinc-200 border |
| Hover | `bg-red-50 border-red-200 text-red-700` | `bg-amber-50 border-amber-200 text-amber-700` | `bg-green-50 border-green-200 text-green-700` | `bg-zinc-100 border-zinc-300 text-zinc-900` |
| Active | scale-[0.97] | scale-[0.97] | scale-[0.97] | scale-[0.97] |
| Disabled | `opacity-40 cursor-not-allowed` | `opacity-40 cursor-not-allowed` | `opacity-40 cursor-not-allowed` | `opacity-40 cursor-not-allowed` |

**Styling baseline:**
```
bg-white border border-zinc-200 rounded-[10px] py-2.5 px-2
text-center text-sm font-medium text-zinc-700
transition-colors duration-150
```

Each button shows: kbd badge (e.g., `[1]`) in corner → label text → interval text below.

### Border Flash Animation (AC #2)

When a rating is submitted successfully, the ReviewCard wrapper should briefly flash the rating's border color:

```
Again → border-red-300 (100ms)
Hard  → border-amber-300 (100ms)
Good  → border-green-300 (100ms)
Easy  → border-zinc-400 (100ms)
```

Implementation: add a transient CSS class that sets `border-{color}` then removes it after 100ms via `spliceTimeout`. Respect `prefers-reduced-motion` — instant no flash.

Do this in the review page or ReviewCard by tracking a `lastRating` state in the store, applying the border class for 100ms, then clearing.

### Response Time Calculation

The `response_time_ms` field in `ReviewRequest` measures time from card reveal to rating. Implement by:
1. Store `revealedAt: number` (Date.now()) in the store when `revealCard()` is called
2. On rate: `response_time_ms = Date.now() - revealedAt`

### Cache Invalidation

After a successful rating mutation:
- Invalidate `srsKeys.queue(queueMode)` — the due cards list changes
- Invalidate `srsKeys.queueStats()` — due count, estimated time change
- The `nextCard()` store action advances the local card index → next card renders immediately from existing cached data while background refetch happens

### Rating Flow Diagram

```
User presses 1/2/3/4 (or taps button)
  → useReviewKeyboard / RatingButton.onClick
  → store.rateCard(rating)
  → useRatingMutation.mutate({ cardId, rating, responseTimeMs })
  → POST /api/v1/srs_cards/{card_id}/review
  → Backend: py-fsrs schedules, persists review record
  → Response: { next_due_at, interval_display }
  → On success:
    - Apply border flash (100ms)
    - Invalidate queue and stats cache
    - store.nextCard() → auto-advance to next card
    - New card renders in front state
  → On error:
    - Show toast: "Failed to save rating. Please try again."
    - Restore card to revealed state (don't advance)
```

### Mobile 2x2 Grid (AC #3)

```html
<!-- Desktop: row of 4 -->
<div class="grid grid-cols-4 gap-2">
  <RatingButton ... />
</div>

<!-- Mobile (< 640px): 2x2 -->
<div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
  <RatingButton ... />
</div>
```

Each button: `min-h-[48px] min-w-[48px]` for touch targets (WCAG 2.5.5). On mobile, buttons fill grid cells in reading order (Again top-left, Hard top-right, Good bottom-left, Easy bottom-right).

### Keyboard Handler Extension

```
Current handlers (story 4-2):
  Space → revealCard()          [when !isRevealed]
  Tab   → toggleJpDefinition()  [when isRevealed]

New handlers (this story):
  1     → rateCard(1)           [when isRevealed]
  2     → rateCard(2)           [when isRevealed]
  3     → rateCard(3)           [when isRevealed]
  4     → rateCard(4)           [when isRevealed]
```

CRITICAL: Only handle digit keys `e.code === "Digit1"` (not Numpad1 to avoid conflicts during initial rollout).

### Error Handling

- **API error (network/5xx):** Show toast "Failed to save rating. Please try again." Use existing Toast pattern. The card stays in revealed state — user can retry the rating.
- **CardNotDueError (backend 422):** Card was already reviewed or scheduling conflict. Auto-advance to next card (skip silently). Log to console in dev.
- **Mutation already in progress:** Disable all rating buttons (`isRatingInProgress` = true). Prevents double-submit.

### Preventing Double-Rating

The `rateCard` action should check `isRatingInProgress` and return early if true. The mutation's `onMutate` sets it to true, `onSettled` sets it to false. This prevents a user from rapidly pressing keys and submitting the same card multiple times.

### No Internalization of Rating Labels

The Vietnamese target users are IT professionals comfortable with English. Keep rating labels as "Again", "Hard", "Good", "Easy" (not translated). This matches the Anki convention they're already familiar with.

### Previous Story Intelligence (4-2)

Story 4-2 establishes:
- `ReviewCard` renders a placeholder div with `role="group" aria-label="Rate your recall"` and dashed-border placeholder text "Rating buttons will appear here" — this entire block gets replaced
- `useReviewKeyboard` hooks into window keydown and cleans up on unmount — follow the same pattern for 1/2/3/4
- `useReviewStore` uses Zustand `create<Type>((set) => ...)` pattern — extend with additional state/actions
- `useApiClient()` returns a typed `ApiClient<T>` function — use it in the new mutation hook
- Query invalidation pattern: `queryClient.invalidateQueries({ queryKey: srsKeys.queue(mode) })`
- Co-located tests: `RatingButton.test.tsx` next to `RatingButton.tsx`
- Component file naming: PascalCase for component, .tsx extension
- Review page uses `"use client"` directive — all review components are client components
- `useDueCards` enriches SRS card data with vocabulary term data — the card's `id` field is available for the rating endpoint

### Architecture Compliance

- **Component pattern:** Compose on shadcn/ui Button primitive (extends its styling, don't import the component directly to avoid being too coupled)
- **State management:** Zustand for session-level rating state (isRatingInProgress, lastRating), TanStack Query mutation for API call
- **File organization:** Component in `components/review/`, hook in `hooks/`, tests co-located
- **API pattern:** Use `useApiClient()` hook → `createApiClient(getToken)` for all fetches
- **Naming:** PascalCase component, camelCase hooks, types in `types/srs.ts` (already exists)
- **Hexagonal rule:** Frontend never imports backend code directly — use the shared API contract from types
- **Error format:** Consistent `{error: {code, message, details}}` from API — mapped to user-friendly toast

### Testing Standards

- Co-located tests: `RatingButton.test.tsx` next to `RatingButton.tsx`
- Testing library: Vitest + React Testing Library
- Test scenarios:
  1. All 4 variants render with correct label, interval, and key number
  2. Click fires onRate callback
  3. Keyboard key presses fire the matching variant's onRate
  4. Disabled state prevents click and key handlers
  5. Hover states apply correct color classes (use CSS class assertions, not visual tests)
  6. ARIA label includes label and interval text
  7. Mobile 2x2 grid: buttons rendered in a grid with correct column count
  8. Active state: pressing applies scale transformation
- Mock `useApiClient` for mutation tests in page-level tests

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.3]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#RatingButton Component (lines 1002-1029)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Rating Feedback Flash & Micro-interactions (lines 1351-1353)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Responsive Rating Layout (lines 1391-1408)]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend Architecture — RatingButton.tsx (line 970)]
- [Source: _out_put/planning-artifacts/architecture.md#Implementation Patterns — Zustand Store (lines 553-567)]
- [Source: _out_put/planning-artifacts/architecture.md#API Patterns — POST /api/v1/srs_cards/{id}/review (line 1134)]
- [Source: backend/src/app/modules/srs/api/router.py — review_srs_card endpoint (lines 113-131)]
- [Source: backend/src/app/modules/srs/api/schemas.py — ReviewCardRequest/Response (lines 42-50)]
- [Source: frontend/src/types/srs.ts — ReviewRequest/ReviewResponse types (lines 33-42)]

## Dev Agent Record

### Agent Model Used

OpenCode (deepseek-v4-pro)

### Debug Log References

None — all tests pass, no debugging required.

### Completion Notes List

- Updated `ReviewRequest`/`ReviewResponse` types in `srs.ts` to match backend API (`rating: number`, `response_time_ms`, `next_due_at`, `interval_display`)
- Created `RatingButton` component with 4 variants (Again/Hard/Good/Easy), semantic hover colors, ARIA labels, keyboard badge, interval display, responsive 2x2 grid on mobile
- Created `useRatingMutation` hook using TanStack Query `useMutation` with cache invalidation for queue and stats
- Extended `review-store.ts` with `isRatingInProgress`, `lastRating`, `revealedAt` state and actions
- Updated `useReviewKeyboard` to handle Digit1-4 keys when card is revealed, using ref-based callback pattern
- Updated `ReviewCard` with border flash animation (100ms, respects `prefers-reduced-motion`), replaced placeholder with RatingButton grid
- Updated review page to orchestrate rating flow: response time tracking, mutation dispatch, error handling (422 auto-skip, others show toast), store state management
- Added `RatingButton` to barrel export
- Created `RatingButton.test.tsx` with 11 tests covering all variants, click handling, disabled state, ARIA labels, key badges, and interval display
- Updated existing `ReviewCard.test.tsx` to pass new required props
- All 20 review-related tests pass (11 RatingButton + 9 ReviewCard)
- 0 regressions in existing test suite
- TypeScript compiles cleanly (no errors)

### File List

- `frontend/src/types/srs.ts` — Updated `ReviewRequest`/`ReviewResponse` types, added `RatingValue` type
- `frontend/src/components/review/RatingButton.tsx` — NEW: Four-variant rating button component
- `frontend/src/components/review/RatingButton.test.tsx` — NEW: 11 component tests
- `frontend/src/hooks/useRatingMutation.ts` — NEW: TanStack Query mutation for POST /srs_cards/{id}/review
- `frontend/src/stores/review-store.ts` — Extended with rating state (isRatingInProgress, lastRating, revealedAt)
- `frontend/src/hooks/useReviewKeyboard.ts` — Extended with Digit1-4 rating key handlers
- `frontend/src/components/review/ReviewCard.tsx` — Replaced placeholder with RatingButton grid, added border flash animation
- `frontend/src/components/review/ReviewCard.test.tsx` — Updated props for new required fields
- `frontend/src/components/review/index.ts` — Added RatingButton to barrel export
- `frontend/src/app/(app)/review/page.tsx` — Wired useRatingMutation, handleRate callback, response time tracking
