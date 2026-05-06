# Story 4.3: RatingButton Component & Card Rating

Status: ready-for-dev

## Story

As a **user**,
I want to rate each card (Again/Hard/Good/Easy) with keyboard shortcuts showing next-review intervals,
so that I can self-assess quickly and trust the scheduling system.

## Acceptance Criteria

1. **Given** a card is in revealed state, **When** the rating buttons appear, **Then** 4 buttons display: Again (1), Hard (2), Good (3), Easy (4) with next-review interval below each (e.g., "<1m", "6m", "1d", "4d"). Each button has semantic color hover: Again (red-50), Hard (amber-50), Good (green-50), Easy (zinc-100). Buttons have ARIA label: "Rate as {label}, next review in {interval}".

2. **Given** a user presses 1, 2, 3, or 4 (or taps a rating button on mobile), **When** the rating is submitted (`POST /api/v1/srs_cards/{id}/review`), **Then** py-fsrs calculates the new FSRS state and next due_at. The review is recorded in srs_reviews (rating, response_time_ms, timestamp). A subtle border color flash appears (100ms): Again red-300, Hard amber-300, Good green-300, Easy zinc-400. The next card auto-advances (slide transition <=150ms). The session counter updates.

3. **Given** a user on mobile, **When** rating buttons display, **Then** buttons render in a 2x2 grid layout. Minimum touch target is 48x48px with 8px gap.

## Tasks / Subtasks

- [ ] Task 1: Create RatingButton component (AC: #1, #3)
  - [ ] Create `frontend/src/components/review/RatingButton.tsx` with variant-based semantic colors
  - [ ] Create `frontend/src/components/review/RatingButton.test.tsx` with tests for all variants, hover states, ARIA, mobile layout
  - [ ] Implement responsive layout: row of 4 on desktop/tablet, 2x2 grid on mobile (<640px)
- [ ] Task 2: Create useSubmitReview hook (AC: #2)
  - [ ] Create `frontend/src/hooks/useSubmitReview.ts` — TanStack Query `useMutation` for `POST /api/v1/srs_cards/{id}/review`
  - [ ] Track response_time_ms from card reveal to rating submission
  - [ ] On success: call `nextCard()` from review store, invalidate relevant queries
- [ ] Task 3: Wire rating into ReviewCard (AC: #1, #2)
  - [ ] Replace placeholder div (lines 124-130) in `ReviewCard.tsx` with `<RatingButtons />` group
  - [ ] Pass `onRate` callback that triggers mutation + border flash + auto-advance
  - [ ] Implement 100ms border color flash animation (respects prefers-reduced-motion)
- [ ] Task 4: Add keyboard shortcuts 1-4 (AC: #2)
  - [ ] Extend `useReviewKeyboard.ts` to handle keys 1-4 when `isRevealed === true`
  - [ ] Each key triggers the same `onRate` flow as button tap
- [ ] Task 5: Update exports and types (AC: all)
  - [ ] Add `RatingButton` to `frontend/src/components/review/index.ts` barrel export
  - [ ] Update `frontend/src/types/srs.ts` if needed (ReviewRequest currently uses string rating but backend expects int 1-4 — reconcile)
- [ ] Task 6: Screen reader announcements (AC: #1, #2)
  - [ ] `role="group"` + `aria-label="Rate your recall"` on button container
  - [ ] After rating: announce "Rated as {label}. Next review in {interval}. Card {n} of {total}." via `aria-live="polite"`

## Dev Notes

### CRITICAL: Frontend ReviewRequest vs Backend ReviewCardRequest Mismatch

The frontend `ReviewRequest` type in `frontend/src/types/srs.ts` (line 34) uses `rating: "again" | "hard" | "good" | "easy"` (string). The backend `ReviewCardRequest` in `backend/src/app/modules/srs/api/schemas.py` (line 43) expects `rating: int` (1-4). The mutation hook must convert: Again=1, Hard=2, Good=3, Easy=4. Also, the frontend type uses `elapsed_ms` but the backend expects `response_time_ms`. Fix the frontend type or map in the hook.

### Backend Endpoint (Already Implemented in 4-1)

```
POST /api/v1/srs_cards/{card_id}/review
Request:  { rating: 1-4, response_time_ms: int|null, session_id: UUID|null }
Response: { ...SrsCardResponse, next_due_at: datetime, interval_display: string }
```

The `interval_display` field (e.g., "<1m", "6m", "1d", "4d") comes from the backend — use it directly for the interval label below each button. To show predicted intervals BEFORE the user rates, you need to either:
- Call `POST` with a dry-run param (not implemented), OR
- Compute locally using card stability/difficulty (complex), OR
- Show static labels ("< 1 min", "~10 min", "~1 day", "~4 days") as approximation

**Recommended approach:** Show static approximate labels initially. The exact interval appears in the response after rating (useful for the screen reader announcement).

### Existing Code State — Files to Modify

| File | Current State | What Changes |
|------|--------------|-------------|
| `frontend/src/components/review/ReviewCard.tsx` | Has placeholder div at lines 124-130 with "Rating buttons will appear here" | Replace with RatingButtons component; add border flash state |
| `frontend/src/hooks/useReviewKeyboard.ts` | Handles Space (reveal) and Tab (JP toggle) | Add 1/2/3/4 key handlers when `isRevealed === true` |
| `frontend/src/components/review/index.ts` | Exports CatchUpBanner, QueueHeader, ReviewCard | Add RatingButton export |
| `frontend/src/stores/review-store.ts` | Has `nextCard()` action that increments index and resets revealed/JP state | May need `revealedAt` timestamp for response_time_ms tracking |
| `frontend/src/app/(app)/review/page.tsx` | Renders ReviewCard without onRate prop | Pass onRate callback or let ReviewCard own the mutation |

### New Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/review/RatingButton.tsx` | Single rating button with variant styling |
| `frontend/src/components/review/RatingButton.test.tsx` | Tests for RatingButton |
| `frontend/src/hooks/useSubmitReview.ts` | TanStack Query useMutation for POST review |

### MUST PRESERVE

- Existing `ReviewCard` front/revealed state rendering — only replace the placeholder div
- Existing `useReviewKeyboard` Space/Tab handlers — add 1-4 alongside
- Existing `useReviewStore` state shape and actions — extend, don't break
- Existing barrel exports in `index.ts` — append, don't replace
- `useApiClient()` pattern from `lib/api-client.ts` for all API calls
- Session counter, card flip, JP toggle all must continue working

### RatingButton Component Spec (from UX)

```typescript
interface RatingButtonProps {
  variant: 'again' | 'hard' | 'good' | 'easy'
  keyNumber: 1 | 2 | 3 | 4
  label: string        // "Again", "Hard", "Good", "Easy"
  interval: string     // "<1m", "6m", "1d", "4d"
  onRate: () => void
  disabled?: boolean
}
```

**States:**
- default: white bg, zinc-200 border
- hover:again: red-50 bg, red border tint
- hover:hard: amber-50 bg, amber border tint
- hover:good: green-50 bg, green border tint
- hover:easy: zinc-100 bg, zinc border
- active: scale(0.97), bg intensifies
- disabled: opacity 0.4, cursor not-allowed

**Border flash after rating (100ms):**
- Again: border-red-300
- Hard: border-amber-300
- Good: border-green-300
- Easy: border-zinc-400
- Respects `prefers-reduced-motion` — no flash if reduced motion enabled

**Responsive layout:**
- Desktop/Tablet (>=640px): horizontal row of 4 buttons
- Mobile (<640px): 2x2 grid, min 48x48px touch target, 8px gap

### Accessibility Requirements

- Button group: `role="group"` + `aria-label="Rate your recall"`
- Each button: `aria-label="Rate as {label}, next review in {interval}"`
- After rating announcement: `aria-live="polite"` — "Rated as {label}. Next review in {interval}. Card {n} of {total}."
- Focus indicators: `ring-2 ring-zinc-900 ring-offset-2` on `:focus-visible`
- Rating colors are bg tints only — text labels always visible (not color-dependent)

### Response Time Tracking

Track milliseconds from card reveal to rating submission. Options:
1. Store `revealedAt: number | null` in Zustand store (set in `revealCard()` action)
2. Use a ref in the ReviewCard component
3. Use a ref in the useSubmitReview hook

**Recommended:** Add `revealedAt` to review store — set `Date.now()` in `revealCard()`, read it when submitting.

### Animation: Card Transition After Rating

After successful rating:
1. Border flash (100ms) with semantic color
2. Call `nextCard()` from store (increments index, resets isRevealed)
3. Next card slides in (<=150ms transition already handled by ReviewCard's `transition-all duration-150`)
4. If `currentCardIndex >= sessionCards.length`, session is complete (story 4-6 handles summary — for now just show empty state or loop)

### Project Structure Notes

- Component location: `frontend/src/components/review/` — matches existing pattern
- Hook location: `frontend/src/hooks/` — matches useDueCards, useQueueStats pattern
- Test co-location: `*.test.tsx` alongside component — matches ReviewCard.test.tsx pattern
- Use CVA or inline Tailwind conditionals for variant styling (project does not use CVA — use conditional className merging with `cn()` utility if available, or template literals)

### Previous Story Intelligence (from 4-1 and 4-2)

**From 4-1:** `fsrs` v6.3.1 no longer exposes `reps`/`lapses` on `Card` — tracked explicitly in domain. Review persistence is atomic with card locking. Backend expects `rating: int` 1-4.

**From 4-2:** ReviewCard has accessible `role="article"`, `tabIndex={0}`. Session cards loaded into Zustand store. Keyboard handler is in a separate `useReviewKeyboard` hook. Rating placeholder exists at lines 124-130 with `role="group" aria-label="Rate your recall"` already set.

### IMPORTANT: Next.js Version

Read `node_modules/next/dist/docs/` for any API changes before writing code. This project may use a newer Next.js version with breaking changes.

### References

- [Source: _out_put/planning-artifacts/epics — Epic 4, Story 4.3]
- [Source: _out_put/planning-artifacts/architecture.md — SRS module, review flow, component structure]
- [Source: _out_put/planning-artifacts/ux-design-specification.md — RatingButton spec, micro-interactions, accessibility]
- [Source: _out_put/implementation-artifacts/4-1-srs-data-model-fsrs-integration.md — backend review endpoint, py-fsrs integration]
- [Source: _out_put/implementation-artifacts/4-2-reviewcard-component-card-reveal-flow.md — ReviewCard component, keyboard hook, store shape]
- [Source: backend/src/app/modules/srs/api/schemas.py — ReviewCardRequest, ReviewCardResponse]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

### Change Log
