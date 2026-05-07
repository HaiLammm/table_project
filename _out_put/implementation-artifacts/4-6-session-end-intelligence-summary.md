# Story 4.6: Session-End Intelligence Summary

Status: review

## Story

As a **user completing a review session**,
I want a concise session-end summary that shows what changed in this session and what tomorrow looks like (cards graduated, patterns detected, tomorrow's estimate),
so that each session feels connected to my long-term learning trajectory rather than just a count of cards reviewed — without streaks, confetti, or gamified noise.

## Acceptance Criteria

1. **Given** a user completes all cards in the current review session or exits early with `Esc` **When** the summary screen renders **Then** it shows the completed-session headline, cards reviewed, session duration, and delta-focused intelligence lines for:
   - cards graduated to mastered this session (only when `> 0`)
   - new patterns detected this session (only when `> 0`, links to `/dashboard`, carried forward from Story 4.5)
   - tomorrow's estimate (`~N cards, ~M min`, always shown)

   **And** it keeps the existing primary actions `View Dashboard` and `Add Words`
   **And** it restores the sidebar back to non-review mode (`setReviewInProgress(false)` already wired in 4-4)
   **And** it does **not** add confetti, streaks, XP, or celebratory animation.

2. **Given** a delta value is zero **When** the summary renders **Then** that individual delta line is hidden instead of displaying a zero-value placeholder
   **And** if the user ended early with cards still remaining, any remaining-count text is secondary context only and must not replace the delta summary.

3. **Given** the backend computes session-end stats for a review session UUID **When** it evaluates whether a card graduated this session **Then** a card counts as graduated only if:
   - the review row for this session has `previous_stability < 21.0`
   - the card's persisted post-review `srs_cards.stability >= 21.0`

   **And** the implementation reuses the existing `srs_reviews.previous_stability` and `srs_reviews.session_id` columns
   **And** no schema migration is introduced for Story 4.6
   **And** stability exactly `21.0` counts as graduated (boundary inclusive).

4. **Given** the backend computes tomorrow's estimate **When** session stats are requested **Then** it counts the current user's `srs_cards` where `due_at <= end_of_tomorrow (UTC)`
   **And** returns `tomorrow_due_count`
   **And** returns `tomorrow_estimated_minutes = ceil(tomorrow_due_count * 10 / 60)` (10 seconds average per card)
   **And** `0` due cards returns `0` minutes.

5. **Given** the session summary fetches backend stats after the session ends **When** the stats query resolves **Then** the frontend prefers backend-derived `cards_reviewed` and `lapsed_card_ids` over optimistic local counters so undo/resume flows remain accurate
   **And** while stats are loading the summary shows a lightweight skeleton instead of stale placeholder numbers
   **And** if the stats query fails, the summary degrades gracefully to local data (cards reviewed + duration only — no graduation, no tomorrow estimate, no Review Again button).

6. **Given** the session has cards rated `Again` **When** the summary screen renders **Then** a `Review Again` action is shown
   **And** clicking it starts a fresh mini-session containing only the lapsed cards from the just-finished session (filtered from already-loaded `sessionCards` against backend `lapsed_card_ids`, preserving original order)
   **And** the mini-session uses the same `ReviewCard` / keyboard flow already established in Stories 4.2–4.5
   **And** it starts with a fresh review-session UUID
   **And** if `lapsed_card_ids` is empty, the `Review Again` action is hidden.

## Tasks / Subtasks

- [x] **Task 1: Add backend session-stats read model in the `srs` module (AC: #3, #4, #5, #6)**
  - [ ] Add `SessionStats` dataclass to `backend/src/app/modules/srs/domain/entities.py`:
    ```python
    @dataclass
    class SessionStats:
        cards_reviewed: int
        cards_graduated: int
        cards_lapsed: int
        lapsed_card_ids: list[int]
        tomorrow_due_count: int
        tomorrow_estimated_minutes: int
    ```
  - [ ] Add `SessionStatsResponse` to `backend/src/app/modules/srs/api/schemas.py` (1:1 with dataclass, snake_case)
  - [ ] Add `GET /api/v1/srs_cards/session-stats?session_id={uuid}` endpoint to `backend/src/app/modules/srs/api/router.py`, reusing `get_review_scheduling_service` dependency
  - [ ] Add `ReviewSchedulingService.get_session_stats(user_id, session_id)` to `backend/src/app/modules/srs/application/services.py`
  - [ ] Add repository methods to `backend/src/app/modules/srs/infrastructure/repository.py`:
    - `get_session_reviews(user_id, session_id)` — returns reviews joined with current card stability (avoid N+1)
    - `count_due_cards_for_date(user_id, date_end)` — count `srs_cards.due_at <= date_end`
  - [ ] Add corresponding abstract methods in `backend/src/app/modules/srs/domain/interfaces.py`
  - [ ] Define `MASTERY_STABILITY_THRESHOLD = 21.0` as a module-level constant in `services.py` (or `domain/value_objects.py` if preferred)

- [x] **Task 2: Reuse the existing review-session UUID end-to-end (AC: #3, #5, #6)**
  - [ ] **Do NOT** introduce a second `sessionId` field in `useReviewStore`. The frontend already has a per-session UUID stored as `diagnosticsSessionId` in `frontend/src/app/(app)/review/page.tsx` (created for Story 4.5). This UUID is the canonical review-session id for Story 4.6.
  - [ ] Pass `diagnosticsSessionId` into every `useRatingMutation.mutate()` payload via `ReviewRequest.session_id` (currently passed as `null`)
  - [ ] Preserve `diagnosticsSessionId` in `review_session_progress` (localStorage) so session resume keeps the same backend session grouping
  - [ ] Optional refactor: rename `diagnosticsSessionId` → `reviewSessionId` for clarity, but **keep read-compatibility** for the existing localStorage key during resume so users with persisted sessions don't lose them

- [x] **Task 3: Add frontend query plumbing for session stats (AC: #1, #4, #5)**
  - [ ] Create `frontend/src/hooks/useSessionStats.ts` — TanStack Query hook for `GET /api/v1/srs_cards/session-stats?session_id={uuid}`, using the established `useApiClient()` pattern (consistent with `useRatingMutation`)
  - [ ] Extend `frontend/src/lib/query-keys.ts` with `srsKeys.sessionStats(sessionId)` — do NOT invent a new key namespace
  - [ ] Add `SessionStatsResponse` type to `frontend/src/types/srs.ts`:
    ```typescript
    interface SessionStatsResponse {
      cards_reviewed: number
      cards_graduated: number
      cards_lapsed: number
      lapsed_card_ids: number[]
      tomorrow_due_count: number
      tomorrow_estimated_minutes: number
    }
    ```
  - [ ] Hook is `enabled` only when `showSessionSummary === true && sessionId !== null`

- [x] **Task 4: Upgrade `SessionSummary` to the intelligence-summary UI (AC: #1, #2, #6)**
  - [ ] Update `frontend/src/components/review/SessionSummary.tsx` props:
    ```typescript
    type SessionSummaryProps = {
      cardsReviewed: number
      sessionDurationMs: number
      cardsRemaining: number
      patternsDetected?: number          // existing — from insightsSeen (Story 4.5)
      cardsGraduated?: number            // NEW — from session stats API
      cardsLapsed?: number               // NEW — from session stats API
      tomorrowDueCount?: number          // NEW
      tomorrowEstimatedMinutes?: number  // NEW
      onDismiss: () => void
      onReviewAgain?: () => void         // NEW — only used when cardsLapsed > 0
    }
    ```
  - [ ] All new props optional with default `0` / `undefined` — existing callers must continue to work without modification
  - [ ] Render delta lines conditionally per visual spec below
  - [ ] Render `Review Again` button only when `cardsLapsed > 0` AND `onReviewAgain` is provided
  - [ ] Keep `cardsRemaining` line visually secondary; only show when `> 0`
  - [ ] Use the existing duration formatter (or add helper if missing): `<60s → "45s"`, `<10m → "3m 42s"`, `<60m → "12m"`, `60m+ → "1h 12m"`

- [x] **Task 5: Wire session-stats data into the review page summary (AC: #1, #5)**
  - [ ] Update `frontend/src/app/(app)/review/page.tsx`:
    - Call `useSessionStats(diagnosticsSessionId)` when `showSessionSummary === true`
    - While stats are pending, render a lightweight skeleton (pulsing bars in the delta-line area)
    - On success: pass `cards_graduated`, `cards_lapsed`, `tomorrow_due_count`, `tomorrow_estimated_minutes` to `SessionSummary`
    - **Prefer backend `cards_reviewed`** for the headline once stats resolve — the local `cardsReviewed` counter is not authoritative after undo/resume
    - On error: silently fall back to local store data (cards reviewed + duration only). No error UI; this is a "best-effort enhancement" not a critical path
    - Keep `patternsDetected={insightsSeen}` sourced from Story 4.5's frontend diagnostics flow — **do NOT** move pattern-count logic into the SRS endpoint

- [x] **Task 6: Implement `Review Again` mini-session from backend lapsed-card data (AC: #6)**
  - [ ] Add `handleReviewAgain` to `review/page.tsx`:
    ```
    1. Filter the already-loaded sessionCards array (in original order) against
       sessionStats.lapsed_card_ids
    2. If filtered array is empty, no-op (button should already be hidden)
    3. Generate a fresh session UUID for the mini-session
    4. Clear persisted review_session_progress (so resume can't point at completed session)
    5. Call store.startSession(filteredLapsedCards) reusing the existing primitive
    6. Hide SessionSummary, set reviewInProgress = true
    ```
  - [ ] **Do not** refetch `/api/v1/srs_cards/due` — `Review Again` is a local replay
  - [ ] **Do not** track lapsed cards in the frontend store — backend `lapsed_card_ids` is the single source of truth (handles undo correctly)
  - [ ] On mini-session completion, the same flow runs again recursively (a Review Again session can itself produce lapsed cards)

- [x] **Task 7: Keep store and keyboard behavior additive (AC: #1, #2, #6)**
  - [ ] Reuse existing `startSession`, `endSession`, `dismissSessionSummary` actions in `frontend/src/stores/review-store.ts` where possible
  - [ ] **Do not** rework `useReviewKeyboard.ts` — Story 4.6 continues using the existing keyboard loop from 4.4 and the insight-interruption behavior from 4.5
  - [ ] If any minimal store change is unavoidable for the mini-session flow, keep it consistent with current Zustand style and existing 33 state fields / 19 actions

- [x] **Task 8: Tests (AC: all)**
  - [ ] Backend unit tests — `backend/tests/unit/modules/srs/application/test_session_stats.py` (NEW):
    - graduation threshold crossing (`previous_stability < 21.0` AND post `>= 21.0`)
    - card already above threshold (was reviewed but didn't cross — should NOT count)
    - boundary: `stability == 21.0` exactly (counts as graduated)
    - lapsed extraction: reviews with `rating == 1` → ordered distinct card_ids
    - tomorrow estimate at 0 cards (returns 0 minutes)
    - tomorrow estimate at non-zero cards (correct ceiling math)
    - empty session: all zeros, empty list
    - undo-tolerant: session with reviews that have been undone → counts only persisted rows
  - [ ] Backend integration tests — `backend/tests/integration/modules/srs/test_session_stats.py` (NEW):
    - seed cards + reviews with known stability values, call `/session-stats`, verify counters and `lapsed_card_ids` order
    - verify tomorrow's due count against real DB query
    - verify response matches `SessionStatsResponse` schema
  - [ ] Frontend component tests — update `frontend/src/components/review/SessionSummary.test.tsx`:
    - graduated line shown when `> 0`, hidden when `0`
    - tomorrow estimate always shown
    - patterns line link to `/dashboard` when `> 0`
    - `Review Again` button visible when `cardsLapsed > 0`, hidden when `0`
    - `Review Again` callback fires
    - backward compat: existing call sites with old props only → no crash, no new lines rendered
  - [ ] Frontend page/hook tests if repo style covers them (`useSessionStats` enable/disable, fallback on error)

## Dev Notes

### Story Foundation

- Epic 4.6 defines the core summary content: cards reviewed, session duration, graduated delta, detected patterns, tomorrow estimate.
- UX explicitly frames this as a **delta-focused summary**, not a gamified completion screen ("accomplishment over guilt").
- Story 4.5 already wired `patternsDetected` from `insightsSeen` — Story 4.6 must preserve that continuity rather than re-deriving diagnostic counts in the SRS backend.
- Story 4.6 is a read-model + UI change. **No schema migration required** — `srs_reviews.session_id` and `srs_reviews.previous_stability` already exist (added in 4.1 / 4.4).

### Existing Code State (UPDATE files)

| File | Current State | What Story 4.6 Changes |
|------|---------------|-------------------------|
| `frontend/src/components/review/SessionSummary.tsx` | ~75 lines. Props: `cardsReviewed`, `sessionDurationMs`, `cardsRemaining`, `patternsDetected?`, `onDismiss`. Basic stats + 2 buttons. | Add `cardsGraduated?`, `cardsLapsed?`, `tomorrowDueCount?`, `tomorrowEstimatedMinutes?`, `onReviewAgain?`. Conditional delta lines. `Review Again` button. Backward-compatible. |
| `frontend/src/components/review/SessionSummary.test.tsx` | ~121 lines, 5 tests. | Add tests for graduated, tomorrow estimate, Review Again button, backward compat. |
| `frontend/src/app/(app)/review/page.tsx` | ~516 lines. Owns `diagnosticsSessionId`, localStorage resume, insights flow, undo, SessionSummary rendering. Passes 5 props to SessionSummary. | Reuse `diagnosticsSessionId` for SRS rating mutations. Add `useSessionStats(sessionId)` call. Pass new props to SessionSummary. Add `handleReviewAgain`. Loading skeleton during stats fetch. Graceful fallback on error. |
| `frontend/src/stores/review-store.ts` | ~260 lines. 33 state fields, 19 actions. Has session lifecycle, summary visibility, insights, undo metadata, current session cards. | Minimal changes — reuse existing `startSession` / `endSession` / `dismissSessionSummary`. **Do NOT add a parallel `sessionId` field**. |
| `frontend/src/lib/query-keys.ts` | Has `srsKeys.queueStats()`, `srsKeys.queue(mode)`, `srsKeys.dueCards()`, `diagnosticsKeys.pendingInsights(sessionId)`. | Extend `srsKeys` with `sessionStats(sessionId)`. |
| `frontend/src/types/srs.ts` | `ReviewRequest` already supports optional `session_id`. | Add `SessionStatsResponse` type. |
| `backend/src/app/modules/srs/api/schemas.py` | `ReviewCardRequest` already includes `session_id` (line 42–46). | Add `SessionStatsResponse`. |
| `backend/src/app/modules/srs/api/router.py` | ~156 lines, 6 endpoints. Review endpoint already forwards `session_id` (line 114–127). | Add `GET /session-stats` endpoint. |
| `backend/src/app/modules/srs/application/services.py` | ~238 lines. `ReviewSchedulingService.review_card()` persists `session_id` and previous stability (line 101–189). `QueueStatsService` exists. | Add `get_session_stats(user_id, session_id)` to `ReviewSchedulingService`. |
| `backend/src/app/modules/srs/domain/entities.py` | `SrsCard`, `Review`, `ReviewResult`, `QueueStats`, `DueCardsPage`. | Add `SessionStats` dataclass. |
| `backend/src/app/modules/srs/domain/interfaces.py` | `SrsCardRepository` with CRUD + queue + undo methods. | Add `get_session_reviews()` and `count_due_cards_for_date()` abstract methods. |
| `backend/src/app/modules/srs/infrastructure/repository.py` | `SqlAlchemySrsCardRepository`. | Implement the two new repository methods. |
| `backend/src/app/modules/srs/infrastructure/models.py` | `SrsReviewModel` already has `session_id`, `previous_stability`, etc. (line 73–104). | **No change** — schema already has everything needed. |

### New Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useSessionStats.ts` | TanStack Query hook for `GET /session-stats` |
| `backend/tests/unit/modules/srs/application/test_session_stats.py` | Unit tests for graduation/lapsed/tomorrow calculations |
| `backend/tests/integration/modules/srs/test_session_stats.py` | Integration coverage for `/session-stats` endpoint |

### MUST PRESERVE

- **Existing review loop**: `Space → reveal → 1/2/3/4 → auto-advance → session summary` is unchanged. Only the summary display is enhanced.
- **Story 4.5 diagnostics flow**: `patternsDetected` continues to come from `insightsSeen` in the frontend session flow. `pendingInsights`, `currentInsight`, `isShowingInsight`, `usePendingInsights`, `useInsightSeenMutation` — all untouched.
- **Existing session resume behavior**: `review_session_progress` continues to restore the current review session when queue card ids still match.
- **Existing undo flow**: Story 4.6 must not break the review undo path or double-count reviews after undo. Counts derive from persisted DB rows, not optimistic frontend increments.
- **All existing `useReviewStore` state/actions**: extend, don't replace. The 33 state fields and 19 actions stay.
- **Existing `useReviewKeyboard` handlers**: no changes.
- **Existing `srsKeys` query key factory**: extend with `sessionStats()`, don't modify existing keys.
- **`useApiClient()` pattern**: all new API calls go through this.
- **Module boundaries**: session summary stats live in `srs`; diagnostics remain in `dashboard`.
- **Existing summary actions**: `View Dashboard` and `Add Words` remain present.
- **`useUIStore` sidebar restoration**: `setReviewInProgress(false)` is already called in `handleEndSession` and the auto-session-end useEffect.
- **All current tests must continue passing.**

### Architecture Compliance

- **Canonical review-session UUID**: `diagnosticsSessionId` in `review/page.tsx` already represents the live review session (created in 4.5). Reuse it as the canonical session UUID for both diagnostics endpoints AND SRS session-stats. Creating a second parallel UUID would split the truth: backend stats and diagnostics would aggregate over different keys.
- **SRS owns session summary stats**: `cards_reviewed`, graduated counts, lapsed cards, tomorrow estimate live in the `srs` module — they're direct SRS session/read-model concerns.
- **Dashboard remains read-only diagnostics**: Do NOT move diagnostic pattern counting into the SRS endpoint. Story 4.5 already established `insightsSeen` as the summary's pattern source.
- **No migration needed**: `srs_reviews.session_id` and `srs_reviews.previous_stability` already exist; this is a read-model/API/UI change.
- **Hexagonal architecture**: session stats follows the same domain → application → infrastructure → api layering.
- **Naming**: PascalCase components, camelCase hooks/stores, snake_case backend / API JSON.
- **Logging**: structlog with `user_id`, `session_id` context.
- **Error format**: same `{error: {code, message, details}}` envelope from backend.

### Backend Session-Stats Contract

```python
class SessionStatsResponse(BaseModel):
    cards_reviewed: int
    cards_graduated: int
    cards_lapsed: int
    lapsed_card_ids: list[int]
    tomorrow_due_count: int
    tomorrow_estimated_minutes: int
```

Notes:
- `cards_reviewed` comes from persisted session reviews, not the optimistic frontend counter.
- `cards_lapsed` can be derived from `len(lapsed_card_ids)`, but returning both simplifies the frontend.
- `lapsed_card_ids` returned in original review order (for `Review Again` ordering).
- `session_duration_ms` is **not** in the response — the page already tracks `sessionStartedAt` / `sessionCompletedAt` locally.

### Session-Stats Computation (Backend)

```python
MASTERY_STABILITY_THRESHOLD = 21.0  # days — interval > 3 weeks = mastered

async def get_session_stats(
    self, user_id: int, session_id: UUID
) -> SessionStats:
    # 1. Load all persisted reviews for this user/session, joined with current
    #    card stability (single query — no N+1)
    reviews = await self._repository.get_session_reviews(user_id, session_id)

    if not reviews:
        return SessionStats(
            cards_reviewed=0,
            cards_graduated=0,
            cards_lapsed=0,
            lapsed_card_ids=[],
            tomorrow_due_count=0,
            tomorrow_estimated_minutes=0,
        )

    cards_graduated = 0
    lapsed_card_ids: list[int] = []
    seen_lapsed: set[int] = set()

    for review in reviews:
        # Lapsed: rating == 1 (Again). Preserve original review order, dedupe.
        if review.rating == 1 and review.card_id not in seen_lapsed:
            lapsed_card_ids.append(review.card_id)
            seen_lapsed.add(review.card_id)

        # Graduated: previous_stability < threshold AND current card stability >= threshold
        if (
            review.previous_stability is not None
            and review.previous_stability < MASTERY_STABILITY_THRESHOLD
            and review.current_card_stability is not None
            and review.current_card_stability >= MASTERY_STABILITY_THRESHOLD
        ):
            cards_graduated += 1

    # Tomorrow's queue estimate
    tomorrow_end = (datetime.now(UTC) + timedelta(days=1)).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    tomorrow_due_count = await self._repository.count_due_cards_for_date(
        user_id, tomorrow_end
    )
    # 0 cards → 0 minutes (per AC #4)
    tomorrow_estimated_minutes = (
        math.ceil(tomorrow_due_count * 10 / 60) if tomorrow_due_count > 0 else 0
    )

    return SessionStats(
        cards_reviewed=len(reviews),
        cards_graduated=cards_graduated,
        cards_lapsed=len(lapsed_card_ids),
        lapsed_card_ids=lapsed_card_ids,
        tomorrow_due_count=tomorrow_due_count,
        tomorrow_estimated_minutes=tomorrow_estimated_minutes,
    )
```

**SQL optimization** — graduation count via single JOIN (avoid N+1 card lookups):

```sql
SELECT r.card_id, r.rating, r.previous_stability, c.stability AS current_stability
FROM srs_reviews r
JOIN srs_cards c ON r.card_id = c.id
WHERE r.session_id = :session_id
  AND r.user_id = :user_id
ORDER BY r.reviewed_at ASC;
```

**Implementation guardrails:**
- Prefer set-based SQL / repository aggregation over N+1 card lookups.
- Treat `stability == 21.0` as graduated (boundary inclusive).
- Return `0` estimated minutes when `tomorrow_due_count == 0`.
- Keep the read-model **tolerant of undone/replaced reviews** by relying on persisted rows after undo cleanup. The `review_card.undo` flow in 4.4 deletes the latest review row, so this query naturally reflects post-undo state.

### SessionSummary Visual Spec

```
┌─────────────────────────────────────┐
│  Session Complete                   │
│─────────────────────────────────────│
│                                     │
│  24 cards reviewed in 3m 42s        │
│                                     │
│  ✦ 3 cards graduated to mastered    │  ← text-green-700, only if > 0
│  ✦ 1 new pattern detected           │  ← text-blue-600 link → /dashboard, only if > 0
│  ✦ Tomorrow: ~18 cards, ~3 min      │  ← text-zinc-600, always shown
│                                     │
│  [Review Again] [Dashboard] [Add]   │  ← Review Again only if cards_lapsed > 0
└─────────────────────────────────────┘
```

**Styling tokens:**
- Container: `bg-zinc-100 border border-zinc-200 rounded-[14px] p-10 text-center`
- Header: `text-lg font-semibold text-text-primary`
- Headline (cards reviewed in duration): `text-sm text-text-secondary`
- Delta lines (general): `text-sm text-zinc-600` with `✦` prefix (U+2726, NOT an emoji)
- Graduated line: add `text-green-700` accent
- Pattern line: `text-blue-600` rendered as Next.js `<Link href="/dashboard">`
- Tomorrow line: neutral `text-zinc-600`
- Primary button "View Dashboard": `bg-zinc-900 text-zinc-50`
- Secondary buttons "Add Words" / "Review Again": `bg-white border border-zinc-200 text-zinc-700`
- `Review Again` only mounts when `cardsLapsed > 0` AND `onReviewAgain` provided

**Duration formatter:**
```typescript
function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  if (totalSeconds < 60) return `${totalSeconds}s`
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  if (minutes < 10) return `${minutes}m ${seconds}s`
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remMinutes = minutes % 60
  return `${hours}h ${remMinutes}m`
}
```

**Loading skeleton (while `useSessionStats` is pending):**
- Show the headline (`24 cards reviewed in 3m 42s`) immediately from local store data
- Render 2–3 pulsing `bg-zinc-200 rounded h-4 w-3/5` bars in place of delta lines
- Buttons render normally (View Dashboard, Add Words always available)
- `Review Again` button is hidden until stats resolve (we don't know `lapsed_card_ids` yet)

### Review Again Flow

```
Completed session summary opens
  → useSessionStats(diagnosticsSessionId) resolves with lapsed_card_ids
  → user clicks "Review Again"
  → handleReviewAgain():
      1. Filter sessionCards (in original order) by lapsed_card_ids
      2. If filtered is empty → no-op (button should already be hidden)
      3. Generate fresh review-session UUID (replaces diagnosticsSessionId for the mini-session)
      4. Clear persisted review_session_progress in localStorage
      5. store.startSession(filteredLapsedCards) — reuses existing primitive
      6. Hide SessionSummary, set reviewInProgress = true
  → Mini-session begins with only lapsed cards
  → On completion (all cards or Esc):
      → New SessionSummary opens
      → useSessionStats(newSessionId) fires
      → Recursive flow: a Review Again session can itself produce lapsed cards
```

**Guardrails:**
- Do NOT refetch `/api/v1/srs_cards/due` before starting the mini-session.
- Do NOT rebuild a second review UI or alternate store.
- Do NOT track lapsed cards in the frontend store — backend `lapsed_card_ids` is the single source of truth (correct under undo).
- If `lapsed_card_ids` is empty after filtering, hide the button instead of starting an empty session.

### Session ID Lifecycle (Corrected — Single UUID)

```
Session start (mount or startSession):
  diagnosticsSessionId = crypto.randomUUID()    ← already created in page.tsx (Story 4.5)
  → No new field added to useReviewStore

Each rating mutation:
  useRatingMutation.mutate({
    cardId, rating, responseTimeMs,
    sessionId: diagnosticsSessionId             ← previously null, now active
  })
  → Backend stores session_id in srs_reviews row

Session end (all cards or Esc):
  → showSessionSummary = true
  → useSessionStats(diagnosticsSessionId) fires
  → Backend computes stats from srs_reviews WHERE session_id = ?
  → Stats displayed in SessionSummary

Review Again:
  → New UUID generated, replaces diagnosticsSessionId
  → review_session_progress cleared
  → Old session stats remain in DB (different session_id)

Dismiss / Navigate away:
  → diagnosticsSessionId cleared via existing dismiss/reset path
```

### UX Guardrails

- The summary is about **accomplishment over guilt** and **delta over absolute totals**.
- No celebratory animation, streak copy, badges, XP counters, or shame-oriented wording.
- Tomorrow estimate reads as calm planning information, not pressure.
- `Review Again` is a practical recovery path, not a gamified CTA.
- Hide zero-value lines entirely rather than showing `0 cards graduated` (zero-value lines feel like nagging).

### Testing Standards

- **Backend unit tests** (`test_session_stats.py`): graduation threshold crossing, boundary at exactly `21.0`, lapsed extraction with order/dedup, tomorrow estimate (0 and non-zero), empty session, undo-tolerant counting.
- **Backend integration tests**: seed real cards/reviews with `session_id`, call `/session-stats`, verify counts and `lapsed_card_ids` against DB, verify schema.
- **Frontend component tests**: graduated line shown/hidden, tomorrow estimate, Review Again button visibility, backward compat with existing call sites.
- **Frontend page/hook tests** (if repo style covers them): `useSessionStats` `enabled` gating, error fallback to local data, loading skeleton renders before resolution.
- **Tooling**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend).

### Previous Story Intelligence

**Story 4.5 (Diagnostic Micro-Insertions):**
- `insightsSeen` already in `useReviewStore`, already passed to `SessionSummary` as `patternsDetected` — Story 4.6 keeps this wiring untouched.
- `diagnosticsSessionId` already in `review/page.tsx` and persisted in localStorage resume payload — **this is the canonical UUID Story 4.6 reuses**.
- Diagnostics endpoints already use the live session UUID; do not modify the dashboard module.
- `pendingInsights`, `currentInsight`, `isShowingInsight`, `usePendingInsights`, `useInsightSeenMutation` — untouched.

**Story 4.4 (Review Session Flow & Keyboard Navigation):**
- `SessionSummary` already exists as the completion/Esc screen — this story upgrades it.
- `sessionStartedAt`, `sessionCompletedAt`, `cardsReviewed`, `showSessionSummary`, `endSession()`, `dismissSessionSummary()` — exist, used as-is.
- `review_session_progress` already stores resume data — extend to keep `diagnosticsSessionId` stable across resume.
- `srs_reviews.previous_stability` and other previous-state columns already persisted by `review_card()` — critical for graduated detection.
- Undo flow with Ctrl+Z is the key correctness driver: summary counts must reflect persisted post-undo state, not optimistic frontend increments.
- localStorage session persistence — unaffected.

**Story 4.3 (Rating Flow):**
- `useRatingMutation` already posts `ReviewRequest` to `/api/v1/srs_cards/{id}/review`.
- `ReviewCardRequest.session_id` exists in both frontend and backend contracts; Story 4.6 activates it from `diagnosticsSessionId`.

**Story 4.1 (SRS Data Model):**
- `srs_reviews` table has `session_id UUID` column, nullable.
- `srs_cards` has `stability`, `reps`, `lapses` — used for graduation threshold check.

### Git Intelligence

- Recent commits follow `feat#X-Y:` and `fix#X-Y:` prefixes.
- Backend, frontend, and tests typically ship in the same commit for a story-sized feature.
- Query hooks and component tests are part of the established implementation pattern.
- Barrel exports updated in `index.ts` files when adding new components/hooks.

### References

- [Source: _out_put/planning-artifacts/epics/epic-4-spaced-repetition-review-engine.md#Story 4.6 Session-End Intelligence Summary (lines 128-145)]
- [Source: _out_put/planning-artifacts/prd/functional-requirements.md#FR17-FR20-FR26-FR33 (lines 27-31, 42, 52)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Accomplishment over guilt (lines 183-186)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Session Complete summary (lines 480-499)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Review journey flow and Review Again (lines 786-798)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Insight cadence and delta emphasis (lines 806-807)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Delta-focused summaries (lines 917-918)]
- [Source: _out_put/planning-artifacts/architecture.md#CardMastered event → dashboard read model (line 324)]
- [Source: _out_put/planning-artifacts/architecture.md#Frontend Zustand & TanStack Query (lines 330-331)]
- [Source: _out_put/planning-artifacts/architecture.md#TypeScript naming/query key conventions (lines 453-457)]
- [Source: _out_put/planning-artifacts/architecture.md#dashboard READ ONLY boundary (lines 1062-1069)]
- [Source: _out_put/planning-artifacts/architecture.md#Review session data flow (lines 1132-1139)]
- [Source: _out_put/implementation-artifacts/4-5-diagnostic-micro-insertions.md — insightsSeen, diagnosticsSessionId, dashboard module]
- [Source: _out_put/implementation-artifacts/4-4-review-session-flow-keyboard-navigation.md — SessionSummary, session state, previous_stability, undo]
- [Source: _out_put/implementation-artifacts/4-3-ratingbutton-component-card-rating.md — useRatingMutation, session_id field]
- [Source: _out_put/implementation-artifacts/4-1-srs-data-model-fsrs-integration.md — srs_reviews, session_id column]
- [Source: frontend/src/app/(app)/review/page.tsx#SavedSessionProgress and diagnosticsSessionId (lines 29-37, 129-141, 150-185)]
- [Source: frontend/src/app/(app)/review/page.tsx#rating payload and SessionSummary render (lines 273-296, 438-451)]
- [Source: frontend/src/stores/review-store.ts#session summary and undo state (lines 21-32, 175-181, 199-258)]
- [Source: frontend/src/components/review/SessionSummary.tsx#current summary UI (lines 9-15, 40-69)]
- [Source: frontend/src/lib/query-keys.ts#srsKeys and diagnosticsKeys (lines 9-20)]
- [Source: backend/src/app/modules/srs/api/schemas.py#ReviewCardRequest.session_id (lines 42-46)]
- [Source: backend/src/app/modules/srs/api/router.py#review endpoint forwards session_id (lines 114-127)]
- [Source: backend/src/app/modules/srs/application/services.py#review_card persists previous stability and session_id (lines 101-189)]
- [Source: backend/src/app/modules/srs/domain/entities.py#Review fields (lines 24-37)]
- [Source: backend/src/app/modules/srs/infrastructure/models.py#SrsReviewModel session_id and previous state (lines 73-104)]

## Dev Agent Record

### Agent Model Used

glm-5.1

### Debug Log References

- `uv run pytest tests/unit/modules/srs/application/test_session_stats.py -v` — 13 passed
- `uv run pytest tests/integration/modules/srs/test_session_stats.py -v` — 5 passed
- `uv run ruff check src/app/modules/srs tests/unit/modules/srs tests/integration/modules/srs` — only pre-existing warning
- `pnpm test src/components/review/SessionSummary.test.tsx` — 17 passed
- `pnpm test src/components/review/ --run` — 43 passed (all review component tests)
- `uv run pytest tests/unit/modules/srs/ tests/integration/modules/srs/ -v` — 46 passed (all SRS tests)

### Completion Notes List

- Backend: Added `SessionStats` and `SessionReviewRow` dataclasses, `SessionStatsResponse` schema, `GET /session-stats` endpoint, `get_session_stats` service method with `MASTERY_STABILITY_THRESHOLD=21.0`, repository methods `get_session_reviews` and `count_due_cards_for_date`
- Backend: No schema migration needed — reuses existing `srs_reviews.session_id` and `srs_reviews.previous_stability` columns
- Frontend: `useSessionStats` hook with TanStack Query, `srsKeys.sessionStats(sessionId)` query key, `SessionStatsResponse` type
- Frontend: `SessionSummary` upgraded with delta lines (graduated, patterns, tomorrow estimate), `Review Again` button, loading skeleton, backward-compatible new optional props
- Frontend: `diagnosticsSessionId` now passed as `session_id` in rating mutations for end-to-end session tracking
- Frontend: `handleReviewAgain` filters `sessionCards` against backend `lapsed_card_ids`, generates fresh session UUID, clears localStorage progress, starts mini-session
- All existing tests remain passing (46 backend SRS tests, 43 frontend review tests)
- Existing in-memory test repositories updated to implement new abstract methods

### File List

**Backend - Modified:**
- backend/src/app/modules/srs/domain/entities.py — Added `SessionStats` and `SessionReviewRow` dataclasses
- backend/src/app/modules/srs/domain/interfaces.py — Added `get_session_reviews()` and `count_due_cards_for_date()` abstract methods
- backend/src/app/modules/srs/api/schemas.py — Added `SessionStatsResponse`
- backend/src/app/modules/srs/api/router.py — Added `GET /session-stats` endpoint
- backend/src/app/modules/srs/api/dependencies.py — Unchanged (reuses existing `get_review_scheduling_service`)
- backend/src/app/modules/srs/application/services.py — Added `get_session_stats()` and `MASTERY_STABILITY_THRESHOLD`
- backend/src/app/modules/srs/infrastructure/repository.py — Implemented `get_session_reviews()` and `count_due_cards_for_date()`

**Backend - New:**
- backend/tests/unit/modules/srs/application/test_session_stats.py — 13 unit tests for session stats logic
- backend/tests/integration/modules/srs/test_session_stats.py — 5 integration tests

**Backend - Updated (fixed abstract method implementations):**
- backend/tests/unit/modules/srs/application/test_review_scheduling_service.py — Added missing abstract methods
- backend/tests/unit/modules/srs/application/test_queue_services.py — Added missing abstract methods
- backend/tests/unit/modules/srs/application/test_undo_service.py — Added missing abstract methods

**Frontend - Modified:**
- frontend/src/app/(app)/review/page.tsx — Added `useSessionStats`, `handleReviewAgain`, wired new props to `SessionSummary`, passed `session_id` in rating mutations
- frontend/src/components/review/SessionSummary.tsx — Upgraded with delta lines, `Review Again` button, loading skeleton, new optional props
- frontend/src/components/review/SessionSummary.test.tsx — 17 tests (expanded from 5)
- frontend/src/lib/query-keys.ts — Added `srsKeys.sessionStats(sessionId)`
- frontend/src/types/srs.ts — Added `SessionStatsResponse` type, optional `session_id` already existed

**Frontend - New:**
- frontend/src/hooks/useSessionStats.ts — TanStack Query hook for session stats
