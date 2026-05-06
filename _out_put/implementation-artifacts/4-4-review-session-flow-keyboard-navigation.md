# Story 4.4: Review Session Flow & Keyboard Navigation

Status: ready-for-dev

## Story

As a **user**,
I want a complete keyboard-driven review session with auto-advance, undo, and session exit,
so that I can complete my daily reviews in 3 keystrokes per card without touching the mouse.

## Acceptance Criteria

1. **Given** a user starts a review session **When** the review page is active **Then** the sidebar auto-collapses to maximize focus **And** the breadcrumb shows live progress: "Reviewing · 5 / 24" **And** the full keyboard flow works: Space (reveal) → 1/2/3/4 (rate) → auto-advance to next card **And** Esc ends the session early (shows session summary)

2. **Given** a user rates a card **When** they press Ctrl+Z within 3 seconds **Then** the last rating is undone, the previous card reappears in revealed state **And** a toast shows "Card rated {label} — Ctrl+Z to undo" per UX-DR15

3. **Given** a user closes the app mid-session **When** they return **Then** the session resumes from the last unrated card (progress saved per-card)

4. **Given** a user has 0 cards due **When** the Today's Queue loads **Then** an empty state displays: "All caught up!" with suggestions (add words, review weak cards) per UX-DR16

## Tasks / Subtasks

- [ ] Task 1: Add Alembic migration for undo support (AC: #2)
  - [ ] Add `previous_fsrs_state`, `previous_stability`, `previous_difficulty`, `previous_reps`, `previous_lapses` to `srs_reviews`
  - [ ] `backend/alembic/versions/xxxx_add_undo_support_to_srs_reviews.py`
  - [ ] Previous state columns: `previous_fsrs_state` (JSONB nullable), `previous_stability` (Float nullable), `previous_difficulty` (Float nullable), `previous_reps` (Integer nullable), `previous_lapses` (Integer nullable)

- [ ] Task 2: Update SrsReviewModel and entities for undo (AC: #2)
  - [ ] Add previous state columns to `srs/infrastructure/models.py` SrsReviewModel
  - [ ] Update `srs/domain/entities.py` Review entity with previous_state fields
  - [ ] Update `srs/infrastructure/repository.py` create_review / save_review_result to accept previous state

- [ ] Task 3: Store previous FSRS state during review (AC: #2)
  - [ ] Update `ReviewSchedulingService.review_card()` in `srs/application/services.py`
  - [ ] Before updating the card, capture the current fsrs_state, stability, difficulty, reps, lapses
  - [ ] Pass previous state to repository when creating Review record
  - [ ] CRITICAL: The old card state MUST be captured BEFORE `scheduler.review_card()` mutates it

- [ ] Task 4: Implement backend undo endpoint (AC: #2)
  - [ ] New method: `ReviewSchedulingService.undo_last_review(card_id, user_id)` in `services.py`
    - Get the most recent Review for this card/user (ordered by reviewed_at DESC, LIMIT 1)
    - Check the review was within undo window (optional server-side enforcement via config)
    - Read previous_* fields from the Review record
    - Restore those values onto the SrsCard (fsrs_state, stability, difficulty, reps, lapses)
    - Delete the Review record
    - Delete any pending CardReviewed outbox event for this review (if outbox used)
    - Recompute due_at from restored fsrs_state (parse Card.from_json → due)
    - Return the restored card with interval display
  - [ ] New endpoint: `POST /api/v1/srs_cards/{card_id}/review/undo` in `router.py`
  - [ ] New schema: `UndoReviewResponse` in `schemas.py` (same shape as ReviewCardResponse)
  - [ ] New dependency: `get_undo_service` in `dependencies.py`

- [ ] Task 5: Create useUIStore for sidebar/topbar state (AC: #1)
  - [ ] `frontend/src/stores/ui-store.ts` — Zustand store
  - [ ] State: `reviewInProgress: boolean`, `setReviewInProgress(active: boolean)`
  - [ ] State: `sidebarCollapsed: boolean`, `setSidebarCollapsed(collapsed: boolean)` (independent toggle for non-review uses)

- [ ] Task 6: Auto-collapse sidebar during review (AC: #1)
  - [ ] Update `frontend/src/components/layout/Sidebar.tsx`
  - [ ] Read `reviewInProgress` from useUIStore
  - [ ] When `reviewInProgress`: render icon-only mode (56px width), hide labels
  - [ ] Tablet (640-1024px): already icon-only, no change needed
  - [ ] Mobile: sidebar hidden behind hamburger regardless, no change
  - [ ] Transition: 200ms slide, respect prefers-reduced-motion
  - [ ] The `(app)/layout.tsx` where Sidebar is rendered may also need awareness (optional read-only passive)

- [ ] Task 7: Live breadcrumb during review (AC: #1)
  - [ ] Update `frontend/src/components/layout/Topbar.tsx`
  - [ ] When path is `/review` AND `reviewInProgress` is true: breadcrumb shows "Reviewing · 5 / 24"
  - [ ] Read `currentCardIndex` and `sessionCards.length` from useReviewStore
  - [ ] Format: `TableProject / Reviewing · {current+1} / {total}`
  - [ ] When Esc is pressed (session ends), breadcrumb returns to normal "Review"

- [ ] Task 8: Esc key — end session early with summary (AC: #1)
  - [ ] Add Esc handler to `useReviewKeyboard.ts`:
    - `e.code === "Escape"` → call `onEndSession` callback
    - Only active when `sessionCards.length > 0` (session is active)
  - [ ] End session logic in `review/page.tsx`:
    - Track `sessionStartedAt: number` (Date.now()) in store
    - Track `cardsReviewed: number` (increment on each successful rating)
    - On Esc: set `showSessionSummary = true`, `reviewInProgress = false`
    - Show SessionSummary component with: cards reviewed, session duration, cards remaining in queue

- [ ] Task 9: Create SessionSummary component (AC: #1)
  - [ ] `frontend/src/components/review/SessionSummary.tsx` (NEW)
  - [ ] Displays: total cards reviewed, session duration, cards remaining
  - [ ] Action buttons: "View Dashboard" (link to /dashboard), "Add Words" (link to /vocabulary)
  - [ ] Styling: `bg-zinc-100 border border-zinc-200 rounded-[14px] p-10 text-center`
  - [ ] Note: Full intelligence summary (graduated cards, patterns, tomorrow estimate) is story 4-6
  - [ ] This component provides only basic stats for mid-session exit

- [ ] Task 10: Extend useReviewStore for undo and session state (AC: #2, #3)
  - [ ] Add: `previousCardIndex: number | null` — index of the card we just left
  - [ ] Add: `sessionStartedAt: number | null` — Date.now() when session begins
  - [ ] Add: `cardsReviewed: number` — count of successfully rated cards
  - [ ] Add: `undoAvailableUntil: number | null` — Date.now() + 3000ms, null when no undo available
  - [ ] Add: `lastRatedCardId: number | null` — ID of the last card that was rated
  - [ ] Add: `ratingLabelForUndo: string | null` — "Again"/"Hard"/"Good"/"Easy" for the undo toast
  - [ ] Add `rateCardAction` that: stores previousCardIndex before advancing, sets undoAvailableUntil, sets lastRatedCardId
  - [ ] Add `undoLastRating()` that: decrements currentCardIndex back to previousCardIndex, sets isRevealed=true, clears undo state
  - [ ] Add `startSession(totalCards)` that: sets sessionStartedAt, cardsReviewed=0, sessionCards
  - [ ] Add `incrementCardsReviewed()` 
  - [ ] Add `endSession()` that: resets all session state
  - [ ] CRITICAL: Preserve ALL existing state/actions. New state is additive, no structural changes.

- [ ] Task 11: Implement Ctrl+Z undo flow in review page (AC: #2)
  - [ ] Add Ctrl+Z handler in `useReviewKeyboard.ts`:
    - `(e.ctrlKey || e.metaKey) && e.code === "KeyZ"` → call `onUndo` callback
    - Only active when `undoAvailableUntil` is not null AND `Date.now() < undoAvailableUntil`
    - `e.preventDefault()` to prevent browser undo
  - [ ] Create `useUndoMutation` hook:
    - `frontend/src/hooks/useUndoMutation.ts` (NEW)
    - POST to `/srs_cards/{card_id}/review/undo`
    - On success: invalidate `srsKeys.queue(queueMode)` and `srsKeys.queueStats()`
    - Return the restored card response
  - [ ] In `review/page.tsx`:
    - After successful rating: show toast "Card rated {label} — Ctrl+Z to undo" (5s duration, dark zinc-900 bg)
    - On Ctrl+Z: call undo mutation, on success call `undoLastRating()`, dismiss the toast
    - If undo API fails: show error toast "Unable to undo rating"
    - If 3 seconds pass: auto-clear undoAvailableUntil (useEffect with timer)

- [ ] Task 12: Session progress persistence (AC: #3)
  - [ ] On mount (`useEffect` in review/page.tsx): read localStorage key `review_session_progress`
    - Key shape: `{ cardIds: number[], currentIndex: number, sessionStartedAt: number | null }`
    - If the current queue cards match the saved cardIds (same IDs, same order first N match), restore `currentIndex`
    - If cards don't match (queue changed since last visit), discard saved progress
  - [ ] On unmount AND on every card advance: save to localStorage:
    - `{ cardIds: sessionCards.map(c => c.id), currentIndex: currentCardIndex, sessionStartedAt }`
    - Debounce writes (save at most every 500ms)
  - [ ] On session end (Esc or all cards done): clear localStorage `review_session_progress`

- [ ] Task 13: Update Toast component for undo (AC: #2)
  - [ ] If the project's Toast component doesn't support action links, add support:
    - Undo toast: `border-l-4 border-zinc-400 bg-zinc-900 text-zinc-100` + "Undo" action link
    - Duration: 5s, auto-dismiss
    - The "Undo" link triggers the same undo handler as Ctrl+Z
  - [ ] If a custom UndoToast wrapper is needed, create it in `components/ui/undo-toast.tsx`

- [ ] Task 14: Update review page orchestration (AC: #1, #2, #3)
  - [ ] On mount: set `reviewInProgress = true` in useUIStore (triggers sidebar collapse + breadcrumb)
  - [ ] On mount: check localStorage for session resume
  - [ ] Wire `startSession()` after `setSessionCards()`
  - [ ] Update `handleRate` to store undo data in store before advancing
  - [ ] After rating success: `incrementCardsReviewed()`, show undo toast, start 3s undo timer
  - [ ] On Esc: set `reviewInProgress = false`, show SessionSummary
  - [ ] On all cards completed: set `reviewInProgress = false`, show SessionSummary
  - [ ] On unmount cleanup: set `reviewInProgress = false`, save session progress

- [ ] Task 15: Write tests (AC: all)
  - [ ] Backend unit tests: undo service logic, state restoration, error cases (no review to undo)
    - `backend/tests/unit/modules/srs/application/test_undo_service.py` (NEW)
  - [ ] Backend integration tests: full undo flow via API, verify card state restored
    - `backend/tests/integration/modules/srs/test_undo.py` (NEW)
  - [ ] Frontend component tests:
    - `useReviewStore.test.ts` — undo action, session state transitions (NEW)
    - `SessionSummary.test.tsx` — renders stats, action buttons (NEW)
    - Update `useReviewKeyboard.test.ts` — Ctrl+Z and Esc handlers (MODIFY)

- [ ] Task 16: Update barrel exports (AC: all)
  - [ ] Add `SessionSummary` to `components/review/index.ts`
  - [ ] Add `useUIStore` export in stores/index.ts (if barrel exists)

## Dev Notes

### Existing Code State (UPDATE files)

| File | Current State | What Changes |
|------|--------------|-------------|
| `frontend/src/stores/review-store.ts` | currentCardIndex, isRevealed, isRatingInProgress, lastRating, revealedAt, sessionCards, rate/next/reveal/reset actions (79 lines) | Add: previousCardIndex, undoAvailableUntil, lastRatedCardId, ratingLabelForUndo, sessionStartedAt, cardsReviewed. Add: undoLastRating(), startSession(), incrementCardsReviewed(), endSession() |
| `frontend/src/hooks/useReviewKeyboard.ts` | Space (reveal), Tab (JP toggle), Digit1-4 (rate). Uses ref pattern for onRate callback. (60 lines) | Add: Esc handler (onEndSession ref callback), Ctrl+Z handler (onUndo ref callback). Keep ref pattern for new callbacks. |
| `frontend/src/app/(app)/review/page.tsx` | Uses useDueCards, useQueueStats, useReviewStore, useRatingMutation. handleRate callback. Loading/error/empty/active states. Cleanup calls resetSession(). (211 lines) | Add: useUIStore for reviewInProgress, useUndoMutation, SessionSummary rendering. Wire: session resume, undo flow, Esc handler, toast with undo action, session timing. Update cleanup: save progress, restore sidebar. |
| `frontend/src/components/review/ReviewCard.tsx` | Renders card front/revealed, rating buttons on revealed, border flash on rating. onRate, isRatingInProgress, lastRating props. Responsive padding (p-6/p-8/p-10). (194 lines) | May need: onUndo callback prop (for undo toast action link) — but undo is page-level, not card-level. Likely NO changes needed here. |
| `frontend/src/components/layout/Topbar.tsx` | Static breadcrumb from pageLabels map. Shows "TableProject / Review" for /review path. (86 lines) | Add: when reviewInProgress, show "Reviewing · 5 / 24" instead of "Review". Read from useReviewStore + useUIStore. |
| `frontend/src/components/layout/Sidebar.tsx` | Desktop: 240px full sidebar. Tablet: 56px icons. Mobile: Sheet overlay. Uses mobileOpen prop. (160 lines) | Add: read reviewInProgress from useUIStore. When true, render 56px icon-only on desktop. |
| `frontend/src/components/review/index.ts` | Exports CatchUpBanner, QueueHeader, RatingButton, ReviewCard (4 exports) | Add SessionSummary export. |
| `backend/src/app/modules/srs/infrastructure/models.py` | SrsCardModel (with fsrs fields), SrsReviewModel (id, card_id, user_id, rating, reviewed_at, response_time_ms, session_id) | Add: previous_fsrs_state (JSONB), previous_stability, previous_difficulty, previous_reps, previous_lapses to SrsReviewModel. |
| `backend/src/app/modules/srs/domain/entities.py` | SrsCard, Review, QueueStats, DueCardsPage, ReviewResult dataclasses | Add: previous_state fields to Review entity. |
| `backend/src/app/modules/srs/domain/interfaces.py` | SrsCardRepository with CRUD + queue methods | Add: get_last_review(card_id, user_id) → Review?, delete_review(review_id), undo_last_rating(card_id, user_id, previous_state) |
| `backend/src/app/modules/srs/domain/exceptions.py` | SrsDomainError, CardNotFoundError, CardNotDueError, DuplicateCardError | Add: NoReviewToUndoError |
| `backend/src/app/modules/srs/infrastructure/repository.py` | SqlAlchemySrsCardRepository with async methods | Add: get_last_review, delete_review, undo_last_rating implementations |
| `backend/src/app/modules/srs/application/services.py` | ReviewSchedulingService with review_card(), QueueStatsService (173 lines) | MODIFY review_card: capture previous state before mutating. ADD undo_last_review method. |
| `backend/src/app/modules/srs/api/router.py` | POST /srs_cards, GET /queue-stats, GET /queue, GET /due, POST /{id}/review (132 lines) | Add: POST /srs_cards/{card_id}/review/undo |
| `backend/src/app/modules/srs/api/schemas.py` | QueueStatsResponse, SrsCardResponse, Create/Review/Undo schemas (62 lines) | Add: UndoReviewResponse (same shape as ReviewCardResponse: id, due_at, fsrs_state, next_due_at, interval_display + stability, difficulty, reps, lapses) |
| `backend/src/app/modules/srs/api/dependencies.py` | get_queue_stats_service, get_review_scheduling_service | Add: get_srs_undo_service (or reuse get_review_scheduling_service) |

### NEW files to create

| File | Purpose |
|------|---------|
| `frontend/src/stores/ui-store.ts` | Zustand store for sidebar/topbar UI state (reviewInProgress, sidebarCollapsed) |
| `frontend/src/components/review/SessionSummary.tsx` | Basic session summary on Esc / completion |
| `frontend/src/components/review/SessionSummary.test.tsx` | Co-located tests |
| `frontend/src/hooks/useUndoMutation.ts` | TanStack Query mutation for POST /srs_cards/{id}/review/undo |
| `frontend/src/hooks/useReviewKeyboard.test.ts` | (if not already created by 4-2/4-3) keyboard handler tests |
| `backend/alembic/versions/xxxx_add_undo_fields_to_srs_reviews.py` | Migration for previous_state columns |
| `backend/tests/unit/modules/srs/application/test_undo_service.py` | Unit tests for undo logic |
| `backend/tests/integration/modules/srs/test_undo.py` | Integration tests for undo API |

### MUST PRESERVE

- **Existing rateCard flow** — The Space → reveal → 1/2/3/4 → auto-advance cycle already works. The undo feature is an additional layer on top. Do NOT restructure how ratings work.
- **Existing `useReviewStore` actions**: `setSessionCards`, `revealCard`, `nextCard`, `toggleJpDefinition`, `resetSession`, `setRatingInProgress`, `setLastRating` — extend, don't replace
- **Existing `useReviewKeyboard` handlers**: Space, Tab, Digit1-4 — add Esc and Ctrl+Z alongside
- **Existing `useRatingMutation`** — continues to work; undo is a separate mutation
- **Existing `useDueCards` and `useQueueStats`** — unchanged
- **Existing `ReviewCard`** — likely no changes needed; undo happens at page/session level
- **Existing `QueueHeader` and `CatchUpBanner`** — unchanged
- **Existing `RatingButton`** — unchanged
- **`useApiClient()` pattern** — all API calls go through this; undo mutation uses same pattern as `useRatingMutation`
- **Query invalidation pattern** — same `queryClient.invalidateQueries` for undo as rating
- **Existing error handling** — toast pattern for failures, 422 auto-skip pattern
- **Empty state for 0 cards due** — already implemented in story 4-2 (CheckCircle2 icon, "All caught up!" message, "Add Words" button). AC #4 is already satisfied. Do NOT re-implement.

### Undo Toast Specification (from UX spec, UX-DR15)

```
┌─────────────────────────────────────┐
│  Card rated Hard — Ctrl+Z to undo   │  ← border-l-4 border-zinc-400, bg-zinc-900 text-zinc-100
│                              [Undo] │  ← clickable action link
└─────────────────────────────────────┘
```

- Position: bottom-right (desktop), bottom-center (mobile)
- Duration: 5s auto-dismiss, or click "Undo" action
- The "Undo" link calls the same handler as Ctrl+Z

### Keyboard Handler Extension

```
Current handlers (stories 4-2, 4-3):
  Space → revealCard()              [when !isRevealed]
  Tab   → toggleJpDefinition()      [when isRevealed]
  1     → rateCard(1)              [when isRevealed && !isRatingInProgress]
  2     → rateCard(2)              [when isRevealed && !isRatingInProgress]
  3     → rateCard(3)              [when isRevealed && !isRatingInProgress]
  4     → rateCard(4)              [when isRevealed && !isRatingInProgress]

New handlers (this story):
  Esc     → endSession()           [when sessionCards.length > 0]
  Ctrl+Z  → undoLastRating()       [when undoAvailableUntil is active && Date.now() < undoAvailableUntil]
```

### Undo Flow Diagram

```
User presses 1/2/3/4 to rate
  → store.rateCardAction(rating)
    → Saves previousCardIndex (current), lastRatedCardId, ratingLabelForUndo
    → Sets undoAvailableUntil = Date.now() + 3000
  → useRatingMutation.mutate(...)
  → On success:
    - Show undo toast "Card rated {label} — Ctrl+Z to undo"
    - store.nextCard() → auto-advance
    - Save session progress to localStorage
    - Start 3s countdown timer
  → After 3s (timer fires):
    - Clear undoAvailableUntil, lastRatedCardId, ratingLabelForUndo
    - Dismiss undo toast if still visible
  → BEFORE 3s: User presses Ctrl+Z
    - Check Date.now() < undoAvailableUntil (true)
    - useUndoMutation.mutate({ cardId: lastRatedCardId })
    - On success:
      - store.undoLastRating() → previousCardIndex restored, isRevealed=true
      - Dismiss undo toast
      - Invalidate cache (queue, stats)
    - On error:
      - Show error toast "Unable to undo rating"
```

### Undo Backend Details

The undo endpoint uses previous state stored on the Review record:

```python
# In review_card() — BEFORE scheduler.review_card() mutates the card:
previous_state = {
    "fsrs_state": current_card.fsrs_state,
    "stability": current_card.stability,
    "difficulty": current_card.difficulty,
    "reps": current_card.reps,
    "lapses": current_card.lapses,
}
# ... then create review with previous_state fields ...

# In undo_last_review():
async def undo_last_review(self, card_id: int, user_id: int) -> ReviewResult:
    last_review = await self._repository.get_last_review(card_id, user_id)
    if not last_review:
        raise NoReviewToUndoError(card_id)

    card = await self._repository.get_card_by_id_for_update(card_id, user_id)
    if not card:
        raise CardNotFoundError(card_id)

    # Restore previous state
    card.fsrs_state = last_review.previous_fsrs_state
    card.stability = last_review.previous_stability
    card.difficulty = last_review.previous_difficulty
    card.reps = last_review.previous_reps
    card.lapses = last_review.previous_lapses

    # Recompute due_at from restored fsrs_state
    fsrs_card = Card.from_json(card.fsrs_state)
    card.due_at = fsrs_card.due  # UTC datetime

    # Delete the review record
    await self._repository.delete_review(last_review.id)

    # Compute interval display for response
    interval_display = self._format_interval(card.due_at)

    await self._repository.update_card(card)
    return ReviewResult(card=card, next_due_at=card.due_at, interval_display=interval_display)
```

### Session Persistence (localStorage)

```typescript
// Key shape stored in localStorage["review_session_progress"]
interface SessionProgress {
  cardIds: number[]        // IDs of cards in the session, in order
  currentIndex: number     // last completed card index
  sessionStartedAt: number // Date.now() from session start
}

// On page mount:
// 1. Read localStorage["review_session_progress"]
// 2. Compare saved cardIds[0..N] with fetched sessionCards[0..N].id
// 3. If first N match: restore currentCardIndex from saved progress
// 4. If mismatch (queue changed): discard saved progress, start fresh

// Debounced save (every 500ms max):
// Write to localStorage after each card advance, but throttle
```

### Sidebar Auto-Collapse Specification

```
Desktop (>1024px):
  Normal: 240px full sidebar with labels
  During review: 56px icon-only sidebar (auto-collapse)
  Transition: 200ms slide, respects prefers-reduced-motion

Tablet (640-1023px):
  Already icon-only (56px), no change needed

Mobile (<640px):
  Hidden behind hamburger, no change needed
```

Implementation in Sidebar.tsx:
- Read `reviewInProgress` from `useUIStore`
- When `true`: apply `w-[56px]` class, hide text labels, show only icons
- When `false`: normal `w-60` (240px) with labels

### Session Summary Component (basic, not full intelligence)

```
┌─────────────────────────────────────┐
│  Session Complete                   │
│─────────────────────────────────────│
│                                     │
│  12 cards reviewed in 2m 15s        │
│  12 cards remaining in queue        │
│                                     │
│  [View Dashboard]    [Add Words]    │
└─────────────────────────────────────┘
```

The full intelligence summary (cards graduated, patterns detected, tomorrow's estimate) is story 4-6. This story provides a basic summary.

### State Management Flow

```
useReviewStore:
  queueMode, currentCardIndex, isRevealed, showJpDefinition, sessionCards
  isRatingInProgress, lastRating, revealedAt
  + previousCardIndex, undoAvailableUntil, lastRatedCardId, ratingLabelForUndo
  + sessionStartedAt, cardsReviewed

  Actions (existing):
    setSessionCards, revealCard, nextCard, toggleJpDefinition, resetSession
    setRatingInProgress, setLastRating

  Actions (new):
    rateCardAction(rating, cardId, label):
      → sets previousCardIndex = currentCardIndex
      → sets lastRatedCardId = cardId
      → sets ratingLabelForUndo = label
      → sets undoAvailableUntil = Date.now() + 3000
    undoLastRating():
      → sets currentCardIndex = previousCardIndex
      → sets isRevealed = true
      → clears undoAvailableUntil, lastRatedCardId, ratingLabelForUndo
    startSession(cards):
      → sets sessionStartedAt = Date.now(), cardsReviewed = 0, sessionCards = cards
    incrementCardsReviewed():
      → cardsReviewed = cardsReviewed + 1
    endSession():
      → same as resetSession() but also clears sessionStartedAt, cardsReviewed

useUIStore:
  reviewInProgress: boolean
  sidebarCollapsed: boolean
  setReviewInProgress(active: boolean)
  setSidebarCollapsed(collapsed: boolean)
  toggleSidebarCollapsed()
```

### Architecture Compliance

- **State management:** Zustand for UI state (sidebar/review mode) and review session state, TanStack Query mutation for undo API call
- **Component pattern:** SessionSummary composes on shadcn/ui Card primitive
- **File organization:** Components in `components/review/`, hooks in `hooks/`, stores in `stores/`, tests co-located
- **API pattern:** useApiClient() for undo API call, same pattern as useRatingMutation
- **Hexagonal rule:** Backend undo service follows same domain/application/infrastructure layers as review_card
- **Naming:** PascalCase components, camelCase hooks/stores/utilities, snake_case backend
- **Error format:** Same `{error: {code, message, details}}` from backend
- **Logging:** structlog with card_id, user_id, rating context

### Testing Standards

- Backend unit tests: `tests/unit/modules/srs/application/test_undo_service.py` — test undo with and without review, test state restoration
- Backend integration tests: `tests/integration/modules/srs/test_undo.py` — test full undo via API, verify card state restored in DB, verify review record deleted
- Frontend: Co-located tests for SessionSummary, store tests for undo state transitions, keyboard tests for Ctrl+Z/Esc
- Testing library: Vitest + React Testing Library (frontend), pytest + pytest-asyncio (backend)

### Previous Story Intelligence

**Story 4-3 (RatingButton) establishes:**
- Rating flow: Space → reveal → 1/2/3/4 → POST /srs_cards/{id}/review → auto-advance
- `useRatingMutation` uses TanStack Query mutation with `onSuccess: invalidateQueries`
- `handleRate` callback in review/page.tsx orchestrates rating → store update → API call
- `revealedAt` timestamp tracks response_time_ms calculation
- `isRatingInProgress` prevents double-submit
- Border flash animation (100ms) on rating feedback
- Mobile 2x2 grid for rating buttons
- Toast for error handling

**Story 4-2 (ReviewCard) establishes:**
- Empty state for 0 cards due: "All caught up!" with CheckCircle2 icon and "Add Words" button — ALREADY IMPLEMENTED
- `useReviewKeyboard` hooks into window keydown, cleans up on unmount — follow same pattern for new Esc/Ctrl+Z handlers
- `useReviewStore` uses Zustand `create<Type>((set) => ...)` — extend with new state/actions
- Co-located test pattern
- `useApiClient()` for all API calls
- `useDueCards` enriches SRS cards with vocabulary term data — card `id` available for undo API

**Story 4-1 (SRS Data Model) establishes:**
- `review_card()` service method already locks card row and persists Review record atomically
- Backend `Review` entity stored in srs_reviews table
- `ReviewSchedulingService` uses py-fsrs for scheduling
- `_format_interval()` helper computes interval display strings

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.4]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Experience Mechanics — The Review Cycle (lines 437-499)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Keyboard Navigation (lines 1440-1451)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Undo Toast UX-DR15 (lines 1203-1217)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Sidebar Auto-Collapse UX-DR23]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Responsive Sidebar Behavior (lines 1260-1269)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Session Summary Component (lines 478-498)]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend Architecture — Zustand Stores (lines 553-568)]
- [Source: _out_put/planning-artifacts/architecture.md#Implementation Patterns — Process Patterns (lines 589-626)]
- [Source: _out_put/planning-artifacts/architecture.md#Data Flow — Review Session (lines 1130-1139)]
- [Source: backend/src/app/modules/srs/api/router.py — existing endpoints (lines 1-132)]
- [Source: backend/src/app/modules/srs/application/services.py — review_card method (lines 97-173)]
- [Source: backend/src/app/modules/srs/domain/entities.py — Review, SrsCard, ReviewResult]
- [Source: backend/src/app/modules/srs/infrastructure/models.py — SrsReviewModel]
- [Source: frontend/src/stores/review-store.ts — current store state (79 lines)]
- [Source: frontend/src/hooks/useReviewKeyboard.ts — current keyboard handlers (60 lines)]
- [Source: frontend/src/components/layout/Sidebar.tsx — sidebar component (160 lines)]
- [Source: frontend/src/components/layout/Topbar.tsx — breadcrumb component (86 lines)]
- [Source: frontend/src/app/(app)/review/page.tsx — review page with rating flow (211 lines)]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
