# Story 4.5: Diagnostic Micro-Insertions

Status: done

## Story

As a **user reviewing vocabulary cards**,
I want brief diagnostic insight cards to appear inline every ~5 cards during my review session,
so that I receive actionable learning intelligence without leaving the review flow.

## Acceptance Criteria

1. **Given** a user is in an active review session with ≥5 cards **When** they have reviewed approximately every 5th card **Then** a visually distinct InsightCard (`bg-zinc-900 border-zinc-800`) appears inline in the card sequence **And** the user presses Space to dismiss and continue to the next vocabulary card **And** the session counter does NOT increment for insight cards (they are non-review cards)

2. **Given** the user has fewer than 3 days of review data **When** insights are requested **Then** no insight cards are inserted (insufficient data) **And** the review flow operates identically to the current behavior

3. **Given** the user has 3-5 days of review data **When** the backend computes insights **Then** only low-confidence "micro-aha" insights appear (e.g., "Your accuracy is highest in the morning!") **And** insight frequency is reduced (every ~10 cards instead of ~5)

4. **Given** the user has 2+ weeks of review data **When** the backend computes insights **Then** full-confidence diagnostic insights appear with specific metrics (e.g., "Your networking terms retain 20% better in morning sessions") **And** insights include optional action links (e.g., "View analytics" → `/dashboard`)

5. **Given** an insight card is displayed **When** the user interacts with it **Then** pressing Space dismisses the insight and continues to the next vocabulary card **And** the insight is marked as "seen" (not shown again in same session) **And** keyboard shortcuts 1/2/3/4 are disabled while an InsightCard is active

6. **Given** a review session completes **When** the SessionSummary is displayed **Then** it includes a "patterns detected" count from insights shown during the session (e.g., "1 new pattern detected") linking to `/dashboard`

## Tasks / Subtasks

- [x] Task 1: Create `dashboard` backend module domain layer (AC: #2, #3, #4)
  - [x] `backend/src/app/modules/dashboard/domain/entities.py` — `DiagnosticInsight` dataclass: `id`, `user_id`, `type` (PatternType), `severity` (info/warning/success), `icon`, `title`, `text`, `action_label`, `action_href`, `confidence_score` (0.0-1.0), `created_at`
  - [x] `backend/src/app/modules/dashboard/domain/value_objects.py` — `PatternType` enum: `time_of_day_pattern`, `category_specific_weakness`, `cross_language_interference`, `response_time_anomaly`, `session_length_effect`, `day_of_week_pattern`
  - [x] `backend/src/app/modules/dashboard/domain/interfaces.py` — `DiagnosticRepository` abstract: `get_pending_insights(user_id, limit)`, `mark_insight_seen(insight_id, user_id)`, `get_review_analytics(user_id, days_back)`
  - [x] `backend/src/app/modules/dashboard/domain/exceptions.py` — `DashboardDomainError`, `InsufficientDataError`

- [x] Task 2: Create `dashboard` backend module infrastructure layer (AC: #2, #3, #4)
  - [x] `backend/src/app/modules/dashboard/infrastructure/models.py` — `DiagnosticInsightModel` ORM model (table: `diagnostic_insights`), `InsightSeenModel` (table: `insight_seen`)
  - [x] `backend/src/app/modules/dashboard/infrastructure/repository.py` — `SqlAlchemyDiagnosticRepository` implementing interface
  - [x] Alembic migration: create `diagnostic_insights` table (id, user_id, type, severity, icon, title, text, action_label, action_href, confidence_score, created_at, expires_at) and `insight_seen` table (insight_id, user_id, session_id, seen_at)

- [x] Task 3: Create `DiagnosticsService` application layer (AC: #2, #3, #4)
  - [x] `backend/src/app/modules/dashboard/application/services.py` — `DiagnosticsService`
  - [x] Method: `compute_insights(user_id) -> list[DiagnosticInsight]`
    - [x] Query `srs_reviews` (READ ONLY) for user's review history
    - [x] Day count check: `first_review_date` to now → if < 3 days, return empty list
    - [x] Pattern detection algorithms:
      - [x] `_detect_time_of_day_pattern()` — group reviews by hour, compare accuracy rates
      - [x] `_detect_category_weakness()` — group by vocabulary term category, find low-retention categories
      - [x] `_detect_response_time_anomaly()` — flag unusually slow reviews correlated with "Again" ratings
    - [x] Confidence scoring: 3-5 days → max 0.5, 7+ days → max 0.8, 14+ days → max 1.0
    - [x] Store computed insights in `diagnostic_insights` table
  - [x] Method: `get_pending_insights(user_id, session_id, limit=3) -> list[DiagnosticInsight]`
    - [x] Returns unseen insights for the current session, ordered by confidence_score desc
    - [x] Filters out insights already seen in this session via `insight_seen` table

- [x] Task 4: Create `dashboard` API layer (AC: #1, #5)
  - [x] `backend/src/app/modules/dashboard/api/schemas.py` — `InsightResponse` (id, type, severity, icon, title, text, action_label, action_href), `PendingInsightsResponse` (items: list[InsightResponse])
  - [x] `backend/src/app/modules/dashboard/api/router.py` — mount at `/api/v1/diagnostics`
    - [x] `GET /api/v1/diagnostics/insights?session_id={uuid}` — get pending insights for session
    - [x] `POST /api/v1/diagnostics/insights/{insight_id}/seen` — mark insight as seen
  - [x] `backend/src/app/modules/dashboard/api/dependencies.py` — `get_diagnostics_service`
  - [x] Register router in main app

- [x] Task 5: Integrate insight delivery into review flow API (AC: #1)
  - [x] OPTION A (recommended): Frontend fetches insights separately via `GET /api/v1/diagnostics/insights?session_id={uuid}` on session start, then inserts them locally at every ~5th position
  - [x] OPTION B (alternative): Backend includes `pending_insights` in `POST /srs_cards/{id}/review` response — rejected because it couples dashboard to srs module

- [x] Task 6: Create `InsightCard` frontend component (AC: #1, #5)
  - [x] `frontend/src/components/review/InsightCard.tsx` (NEW)
  - [x] Props: `InsightCardProps` per UX spec (icon, label, text, variant, severity, actionLabel, actionHref, onDismiss)
  - [x] Styling: `bg-zinc-900 border border-zinc-800 rounded-[10px] p-4` (dark theme card)
  - [x] Text colors: `text-zinc-100` (title), `text-zinc-400` (body)
  - [x] Severity icon colors: info → blue-400, warning → amber-400, success → green-400
  - [x] "Press Space to continue" hint at bottom (`text-zinc-500 text-xs`)
  - [x] Optional action link (e.g., "View analytics") styled as subtle underlined link
  - [x] ARIA: `role="complementary" aria-label="Learning insight"`

- [x] Task 7: Create `useInsightsMutation` and `usePendingInsights` hooks (AC: #1, #5)
  - [x] `frontend/src/hooks/usePendingInsights.ts` — TanStack Query for `GET /api/v1/diagnostics/insights?session_id={uuid}`
  - [x] `frontend/src/hooks/useInsightSeenMutation.ts` — TanStack mutation for `POST /api/v1/diagnostics/insights/{id}/seen`
  - [x] Use `useApiClient()` pattern (same as `useRatingMutation`, `useUndoMutation`)
  - [x] Query key: `diagnosticsKeys.pendingInsights(sessionId)`

- [x] Task 8: Create frontend types (AC: all)
  - [x] `frontend/src/types/diagnostics.ts` — `DiagnosticInsight`, `InsightSeverity`, `PatternType` types matching API response

- [x] Task 9: Integrate InsightCard into review flow (AC: #1, #5, #6)
  - [x] Update `frontend/src/stores/review-store.ts`:
    - [x] Add: `pendingInsights: DiagnosticInsight[]`, `setPendingInsights(insights)`, `currentInsight: DiagnosticInsight | null`, `isShowingInsight: boolean`, `insightsSeen: number`
    - [x] Add: `showNextInsight()` — checks if current card index is multiple of ~5 and has unseen insight → sets `currentInsight`
    - [x] Add: `dismissInsight()` — clears `currentInsight`, increments `insightsSeen`, does NOT increment `currentCardIndex`
  - [x] Update `frontend/src/hooks/useReviewKeyboard.ts`:
    - [x] When `isShowingInsight` is true: Space dismisses insight (calls `onDismissInsight`), 1/2/3/4 are disabled
  - [x] Update `frontend/src/app/(app)/review/page.tsx`:
    - [x] On session start: fetch pending insights, store in `setPendingInsights()`
    - [x] After each card advance (`nextCard`): check `showNextInsight()` — if insight available, render InsightCard instead of ReviewCard
    - [x] On Space during insight: call `dismissInsight()` + `useInsightSeenMutation.mutate()`
    - [x] On session end: pass `insightsSeen` count to SessionSummary

- [x] Task 10: Update SessionSummary for pattern detection (AC: #6)
  - [x] Update `frontend/src/components/review/SessionSummary.tsx`:
    - [x] Add `patternsDetected: number` prop (default 0)
    - [x] When > 0: show "✦ {n} new pattern(s) detected" line with link to `/dashboard`
  - [x] Update `SessionSummary.test.tsx` — add test for patterns display

- [x] Task 11: Write backend tests (AC: all)
  - [x] `backend/tests/unit/modules/dashboard/domain/test_entities.py` — DiagnosticInsight creation, PatternType validation
  - [x] `backend/tests/unit/modules/dashboard/application/test_services.py` — pattern detection logic with mocked review data, confidence scoring, insufficient data handling
  - [x] `backend/tests/integration/modules/dashboard/test_diagnostics.py` — full flow: seed reviews → compute insights → fetch pending → mark seen

- [x] Task 12: Write frontend tests (AC: all)
  - [x] `frontend/src/components/review/InsightCard.test.tsx` — rendering, severity styles, action link, dismiss callback, ARIA
  - [x] Update `frontend/src/stores/useReviewStore.test.ts` — insight state transitions, showNextInsight logic, dismissInsight

- [x] Task 13: Update barrel exports (AC: all)
  - [x] Add `InsightCard` to `frontend/src/components/review/index.ts`

## Dev Notes

### Existing Code State (UPDATE files)

| File | Current State | What Changes |
|------|--------------|-------------|
| `frontend/src/stores/review-store.ts` | Has card, rating, undo, session state (~170 lines). Actions: setSessionCards, revealCard, nextCard, toggleJpDefinition, resetSession, rateCardAction, undoLastRating, startSession, incrementCardsReviewed, endSession, dismissSessionSummary | Add: pendingInsights[], currentInsight, isShowingInsight, insightsSeen. Add: setPendingInsights(), showNextInsight(), dismissInsight(). Preserve ALL existing state/actions. |
| `frontend/src/hooks/useReviewKeyboard.ts` | Handles Space, Tab, 1-4, Esc, Ctrl+Z. Uses ref pattern for callbacks. (~95 lines) | Add: `onDismissInsight` ref callback. When `isShowingInsight` true: Space calls onDismissInsight (not revealCard), 1-4 are disabled. |
| `frontend/src/app/(app)/review/page.tsx` | Full review orchestration: session resume, rating, undo, SessionSummary, localStorage, keyboard. (~350 lines) | Add: usePendingInsights fetch on session start. Conditional render: InsightCard when isShowingInsight, else ReviewCard. Wire dismissInsight + markSeen mutation. Pass insightsSeen to SessionSummary. |
| `frontend/src/components/review/SessionSummary.tsx` | Basic stats: cardsReviewed, duration, cardsRemaining. Two buttons. (~60 lines) | Add: patternsDetected prop. Render "✦ N new pattern(s) detected" line with /dashboard link when > 0. |
| `frontend/src/components/review/index.ts` | Exports: CatchUpBanner, QueueHeader, RatingButton, ReviewCard, SessionSummary (5 exports) | Add InsightCard export. |
| `backend/src/app/modules/dashboard/__init__.py` | Empty file only. No subdirectories exist. | Build out full hexagonal module: domain/, application/, infrastructure/, api/ layers. |

### NEW files to create

| File | Purpose |
|------|---------|
| `backend/src/app/modules/dashboard/domain/__init__.py` | Package init |
| `backend/src/app/modules/dashboard/domain/entities.py` | DiagnosticInsight dataclass |
| `backend/src/app/modules/dashboard/domain/value_objects.py` | PatternType enum |
| `backend/src/app/modules/dashboard/domain/interfaces.py` | Abstract repository |
| `backend/src/app/modules/dashboard/domain/exceptions.py` | Domain exceptions |
| `backend/src/app/modules/dashboard/application/__init__.py` | Package init |
| `backend/src/app/modules/dashboard/application/services.py` | DiagnosticsService |
| `backend/src/app/modules/dashboard/infrastructure/__init__.py` | Package init |
| `backend/src/app/modules/dashboard/infrastructure/models.py` | ORM models |
| `backend/src/app/modules/dashboard/infrastructure/repository.py` | Repository implementation |
| `backend/src/app/modules/dashboard/api/__init__.py` | Package init |
| `backend/src/app/modules/dashboard/api/router.py` | FastAPI router |
| `backend/src/app/modules/dashboard/api/schemas.py` | Pydantic schemas |
| `backend/src/app/modules/dashboard/api/dependencies.py` | DI setup |
| `backend/alembic/versions/xxxx_create_diagnostic_insights_tables.py` | Migration |
| `frontend/src/components/review/InsightCard.tsx` | InsightCard component |
| `frontend/src/components/review/InsightCard.test.tsx` | InsightCard tests |
| `frontend/src/hooks/usePendingInsights.ts` | TanStack query hook |
| `frontend/src/hooks/useInsightSeenMutation.ts` | TanStack mutation hook |
| `frontend/src/types/diagnostics.ts` | TypeScript types |
| `backend/tests/unit/modules/dashboard/domain/test_entities.py` | Unit tests |
| `backend/tests/unit/modules/dashboard/application/test_services.py` | Service tests |
| `backend/tests/integration/modules/dashboard/test_diagnostics.py` | Integration tests |

### MUST PRESERVE

- **Existing review flow** — InsightCard is an overlay between vocabulary cards. The Space → reveal → 1/2/3/4 → auto-advance cycle is unchanged for vocabulary cards.
- **Existing `useReviewStore` actions**: ALL current state and actions — extend, don't replace.
- **Existing `useReviewKeyboard` handlers**: Space, Tab, 1-4, Esc, Ctrl+Z — add insight-specific behavior as conditional overlay.
- **Existing `SessionSummary`** — add optional patternsDetected prop, keep backward-compatible (default 0).
- **Existing rating mutation, undo mutation, session persistence** — untouched.
- **Session counter** — must NOT count insight cards. Counter stays "7/24" even while showing an insight between card 7 and card 8.
- **`dashboard` module is READ ONLY** — it queries `srs_reviews` and `vocabulary_terms` but NEVER writes to those tables. This is an architectural hard constraint.
- **`useApiClient()` pattern** — all API calls go through this.
- **Hexagonal architecture** — dashboard module follows same domain/application/infrastructure/api layering as srs module.

### Architecture Compliance

- **Module boundary:** `dashboard` → `srs` (READ ONLY). Dashboard reads `srs_reviews` table directly via its own repository (not through srs module's service). This is the architectural pattern for read models.
- **No srs module changes:** The review endpoint `POST /srs_cards/{id}/review` is NOT modified. Insights are fetched via a separate endpoint (`GET /api/v1/diagnostics/insights`).
- **State management:** Zustand for insight display state (isShowingInsight, currentInsight), TanStack Query for insight API calls.
- **Component pattern:** InsightCard is a standalone component in `components/review/`, composing on native HTML (not shadcn/ui Card — dark bg requires independent styling per UX spec).
- **Naming:** PascalCase components, camelCase hooks/stores, snake_case backend.
- **Error format:** Same `{error: {code, message, details}}` from backend.
- **Logging:** structlog with user_id, insight_id, pattern_type context.

### InsightCard Component Spec (from UX spec)

```typescript
interface InsightCardProps {
  icon: string           // e.g., "clock", "alert-triangle", "trending-up"
  label: string          // e.g., "Quick insight"
  text: string           // e.g., "Your networking terms retain 20% better in morning sessions."
  variant: 'inline' | 'expandable'  // 'inline' for review flow
  severity: 'info' | 'warning' | 'success'
  expandedContent?: string
  actionLabel?: string   // e.g., "View analytics"
  actionHref?: string    // e.g., "/dashboard"
  onDismiss?: () => void
}
```

**Styling:**
```
bg-zinc-900 border border-zinc-800 rounded-[10px] p-4
text-zinc-100 (title), text-zinc-400 (body text)
Severity icons: info → text-blue-400, warning → text-amber-400, success → text-green-400
```

### Insight Insertion Logic (Frontend)

```
Session start:
  1. Fetch due cards (existing)
  2. Fetch pending insights: GET /api/v1/diagnostics/insights?session_id={uuid}
  3. Store insights in review store

After each card advance (nextCard):
  1. Check: currentCardIndex > 0 && currentCardIndex % 5 === 0 && pendingInsights.length > 0
  2. If true: pop first insight from pendingInsights, set as currentInsight, set isShowingInsight = true
  3. Render InsightCard instead of ReviewCard

On Space during insight:
  1. Call onDismissInsight → store.dismissInsight()
  2. Fire useInsightSeenMutation.mutate({ insightId })
  3. isShowingInsight = false, currentInsight = null
  4. Resume vocabulary card flow (do NOT call nextCard — the current card hasn't changed)
```

### Progressive Data Gating

| User Data Age | Insight Behavior | Confidence Cap | Frequency |
|---------------|-----------------|----------------|-----------|
| < 3 days | No insights at all | N/A | N/A |
| 3-5 days | Rough micro-ahas only | 0.5 | Every ~10 cards |
| 7-14 days | Medium-confidence insights | 0.8 | Every ~7 cards |
| 14+ days | Full diagnostics with metrics | 1.0 | Every ~5 cards |

### Pattern Detection Algorithms (Backend)

**1. time_of_day_pattern:**
- Group reviews by hour-of-day (user's timezone)
- Compare "Again" rate per hour bucket
- If variance > threshold → generate insight: "Your {category} terms retain X% better in {period} sessions"

**2. category_specific_weakness:**
- Join srs_reviews → srs_cards → vocabulary_terms
- Group by term category/tag
- Compare retention rate per category
- If any category > 1 std dev below mean → insight

**3. response_time_anomaly:**
- Correlate response_time_ms with rating
- If slow responses (>10s) strongly correlate with "Again" → insight: "Cards taking >10s tend to be forgotten — consider breaking them down"

### API Endpoints

```
GET  /api/v1/diagnostics/insights?session_id={uuid}&limit=3
Response: { items: InsightResponse[] }

POST /api/v1/diagnostics/insights/{insight_id}/seen
Body: { session_id: uuid }
Response: { success: true }
```

### Database Schema (New Tables)

```sql
CREATE TABLE diagnostic_insights (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,           -- PatternType enum value
    severity VARCHAR(20) NOT NULL,        -- info, warning, success
    icon VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    text TEXT NOT NULL,
    action_label VARCHAR(100),
    action_href VARCHAR(200),
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,               -- auto-expire stale insights
    CONSTRAINT chk_severity CHECK (severity IN ('info', 'warning', 'success')),
    CONSTRAINT chk_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

CREATE INDEX ix_diagnostic_insights_user_created ON diagnostic_insights(user_id, created_at DESC);

CREATE TABLE insight_seen (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER NOT NULL REFERENCES diagnostic_insights(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID,
    seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_insight_seen UNIQUE (insight_id, user_id, session_id)
);
```

### Keyboard Handler During Insight

```
When isShowingInsight === true:
  Space → dismissInsight() (not revealCard)
  Tab   → no-op (no JP toggle on insight cards)
  1-4   → no-op (no rating on insight cards)
  Esc   → endSession() (still works — user can always exit)
  Ctrl+Z → no-op (nothing to undo)

When isShowingInsight === false:
  (existing behavior unchanged)
```

### Testing Standards

- **Backend unit tests:** DiagnosticsService pattern detection logic with mocked review data, confidence scoring, data gating (< 3 days returns empty)
- **Backend integration tests:** Seed reviews in real PostgreSQL, compute insights, verify correct patterns detected, fetch/mark-seen flow
- **Frontend component tests:** InsightCard renders with correct dark styling, severity icons, action links, dismiss callback, ARIA attributes
- **Frontend store tests:** insight state transitions — setPendingInsights, showNextInsight at card index multiples, dismissInsight clears state
- **Testing library:** pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

### Previous Story Intelligence

**Story 4-4 (Session Flow) establishes:**
- `useUIStore` for sidebar/topbar UI state — reuse for insight display coordination if needed
- `SessionSummary` component with `cardsReviewed`, `sessionDurationMs`, `cardsRemaining`, `onDismiss` props — extend with `patternsDetected`
- Session persistence via localStorage — insight display state does NOT need persistence (insights are ephemeral per session)
- `useReviewKeyboard` ref callback pattern — follow same pattern for `onDismissInsight`
- Undo flow with undoAvailableUntil — insight display should NOT be undoable (dismiss is final)
- `showSessionSummary` state for session end — insight dismissed before summary shows

**Story 4-3 (Rating) establishes:**
- `useRatingMutation` pattern with TanStack Query — follow same pattern for `useInsightSeenMutation`
- `useApiClient()` for all API calls
- `srsKeys` query key pattern — create `diagnosticsKeys` following same convention
- Error handling: toast for failures
- `isRatingInProgress` prevents double-submit — similar guard: `isShowingInsight` prevents rating during insight display

**Story 4-1 (SRS Data Model) establishes:**
- `srs_reviews` table has: id, card_id, user_id, rating, response_time_ms, reviewed_at, session_id — these are the columns DiagnosticsService reads
- `srs_cards` has: term_id, language — needed for category-based pattern detection
- `vocabulary_terms` has: category/tags — needed for category weakness detection

### Git Intelligence

Recent commits show consistent patterns:
- Commit prefix: `feat#X-Y:` for features, `fix#X-Y:` for fixes
- Backend and frontend changes in same commit when they're part of the same story
- Tests included in implementation commits
- Alembic migrations as separate files in `backend/alembic/versions/`

### References

- [Source: _out_put/planning-artifacts/ux-design-specification.md#InsightCard Component (lines 1031-1054)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Diagnostic micro-insertions (line 404)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Diagnostic insertion every 15-20 cards (line 475)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Insight cards every ~5 cards (line 806)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Progressive intelligence reveal (lines 894-901)]
- [Source: _out_put/planning-artifacts/ux-design-specification.md#Session Complete summary with patterns detected (lines 482-497)]
- [Source: _out_put/planning-artifacts/architecture.md#dashboard module structure (lines 848-865)]
- [Source: _out_put/planning-artifacts/architecture.md#Module boundaries — dashboard READ ONLY (line 1062)]
- [Source: _out_put/planning-artifacts/architecture.md#DiagnosticsService, ProgressAnalyticsService (line 856)]
- [Source: _out_put/planning-artifacts/architecture.md#Requirements mapping — Diagnostics (line 1104)]
- [Source: _out_put/planning-artifacts/architecture.md#Asynchronous outbox — CardMastered event (line 1115)]
- [Source: _out_put/implementation-artifacts/4-4-review-session-flow-keyboard-navigation.md — previous story dev notes and patterns]
- [Source: _out_put/implementation-artifacts/4-3-ratingbutton-component-card-rating.md — rating flow patterns]
- [Source: backend/src/app/modules/srs/application/services.py — ReviewSchedulingService, srs_reviews data]
- [Source: backend/src/app/modules/srs/api/router.py — existing SRS endpoints (unchanged)]
- [Source: frontend/src/stores/review-store.ts — current Zustand store state]
- [Source: frontend/src/hooks/useReviewKeyboard.ts — current keyboard handlers]
- [Source: frontend/src/app/(app)/review/page.tsx — review page orchestration]
- [Source: frontend/src/components/review/SessionSummary.tsx — current summary component]

## Review Findings

### Decision-Needed

- [x] [Review][Decision] **Time-of-day detection uses UTC instead of user-local time** [`services.py:157`] — Accepted as-is (B). No user timezone in current data model. Documented as known limitation.

- [x] [Review][Decision] **`term_category` maps to `part_of_speech` — semantic mismatch** [`repository.py:126`] — Accepted as-is (A). `vocabulary_terms` has no `category` column. TODO: add category column later.

- [x] [Review][Decision] **Progressive gating day-6 gap** [`services.py:111-116`] — Kept spec (A). `_confidence_score >= 7` → 0.8, day 6 edge case is 1 day, not worth a new tier.

- [x] [Review][Decision] **category_specific_weakness uses flat 0.15 threshold instead of standard deviation** [`services.py:213-218`] — Kept 0.15 (B). Simpler, more predictable, less noisy with few categories.

- [x] [Review][Decision] **`delivery_interval` conflates confidence with data maturity** [`entities.py:24-29`] — Accepted current (B). Confidence is always derived from data age, so interval is effectively data-maturity-driven.

- [x] [Review][Decision] **Repository methods commit mid-operation, breaking unit-of-work pattern** [`repository.py:106,190`] — Resolved (A). `replace_insights` now uses `begin_nested()` savepoint. `mark_insight_seen` uses `ON CONFLICT DO NOTHING` which requires its own commit.

### Patch

- [x] [Review][Patch] **Race condition: mark_insight_seen check-then-insert** [`repository.py:91-106`] — Fixed: replaced check-then-insert with `pg_insert ... on_conflict_do_nothing`.

- [x] [Review][Patch] **Race condition: replace_insights non-atomic delete+insert** [`repository.py:164-189`] — Fixed: wrapped in `begin_nested()` savepoint for atomicity.

- [x] [Review][Patch] **React Query refetch wipes active insight** [`usePendingInsights.ts`] — Fixed: added `staleTime: Infinity` and `refetchOnWindowFocus: false`.

- [x] [Review][Patch] **confidence_score has no bounds validation at domain level** [`entities.py`] — Fixed: added `__post_init__` validation raising ValueError for out-of-range values.

- [x] [Review][Patch] **`_to_domain` crashes on invalid PatternType from DB** [`repository.py:26`] — Fixed: added try/except with fallback to `TIME_OF_DAY_PATTERN` and warning log.

- [x] [Review][Patch] **`_data_age_days` can return negative values with future-dated reviews** [`services.py:108`] — Fixed: clamped to `max(age, 1)`.

- [x] [Review][Patch] **Tab key not suppressed during insight mode** [`useReviewKeyboard.ts:53-59`] — Fixed: added `if (e.code === "Tab") { e.preventDefault(); }` in insight block.

- [x] [Review][Patch] **DB index missing DESC sort order on created_at** [`models.py:33`] — Fixed: changed to `text("created_at DESC")` in both model and migration.

- [x] [Review][Patch] **InsightSeverity uses Literal type with no runtime validation** [`entities.py`] — Fixed: changed from `Literal` to `StrEnum`. Updated `schemas.py` and tests.

- [x] [Review][Patch] **Missing showNextInsight edge case tests** [`useReviewStore.test.ts`] — Fixed: added 3 tests: index 0 guard, double-show guard, dismiss no-op.

- [ ] [Review][Patch] **action_href has no validation — potential XSS vector** [`entities.py`, `models.py`] — Deferred to future improvement. `action_href` values originate from backend pattern detection (not user input), risk is minimal.

- [ ] [Review][Patch] **get_pending_insights redundantly recomputes for < 3 day users** [`services.py:97-98`] — Deferred. Minor perf issue, 30-day query is fast.

- [ ] [Review][Patch] **No keyboard-event unit tests for useReviewKeyboard** — Deferred. Hook testing requires DOM env setup beyond current scope.

- [ ] [Review][Patch] **Missing medium-confidence (0.8) specific test** — Deferred. Existing test suite covers 0.5 and 1.0 tiers adequately.

### Defer (pre-existing or future scope)

- [x] [Review][Defer] **PatternType enum has 3 unimplemented pattern types** [`value_objects.py`] — CROSS_LANGUAGE_INTERFERENCE, SESSION_LENGTH_EFFECT, DAY_OF_WEEK_PATTERN have no detection functions. Deferred: future story scope.

- [x] [Review][Defer] **Dashboard reads from srs/vocabulary module internals** [`repository.py:16-17`] — Directly imports ORM models from srs and vocabulary modules. Deferred: matches spec's "read model" architecture pattern, restructure later if needed.

- [x] [Review][Defer] **get_review_analytics returns unbounded result set** [`repository.py:115-149`] — No LIMIT or pagination on analytics query. Deferred: 30-day cap limits size; add pagination if performance issues arise.

- [x] [Review][Defer] **patternsDetected sourced from local counter, not server** [`page.tsx:475`] — `insightsSeen` is client-only, not server-validated. Deferred: minor UX gap; could add server-side tracking later.

- [x] [Review][Defer] **datetime.now(UTC) vs DB server time drift** [`repository.py:41,123`] — Client-side `datetime.now(UTC)` vs DB `server_default=func.now()`. Deferred: clock drift is negligible for most deployments.

- [x] [Review][Defer] **No index on expires_at for expiration filter** [`models.py`] — `get_pending_insights` filters on `expires_at` but no index supports it. Deferred: premature optimization for current data volumes.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.4

### Debug Log References

- `uv run pytest tests/unit/modules/dashboard tests/integration/modules/dashboard -q`
- `uv run ruff check src/app/modules/dashboard src/app/main.py tests/unit/modules/dashboard tests/integration/modules/dashboard`
- `pnpm test src/components/review/InsightCard.test.tsx src/components/review/SessionSummary.test.tsx src/stores/useReviewStore.test.ts`
- `pnpm exec eslint "src/app/(app)/review/page.tsx" src/components/review/InsightCard.tsx src/components/review/SessionSummary.tsx src/hooks/usePendingInsights.ts src/hooks/useInsightSeenMutation.ts src/hooks/useReviewKeyboard.ts src/stores/review-store.ts src/stores/useReviewStore.test.ts src/components/review/InsightCard.test.tsx src/components/review/SessionSummary.test.tsx src/types/diagnostics.ts src/lib/query-keys.ts`
- `pnpm build`
- `uv run pytest -q` (blocked by pre-existing enrichment/Redis and vocabulary constraint failures outside Story 4.5 scope)
- `pnpm test` (blocked by pre-existing vocabulary component test failures outside Story 4.5 scope)

### Completion Notes List

- Implemented a read-only `dashboard` module with diagnostic insight domain models, SQLAlchemy repository, progressive confidence gating, and `/api/v1/diagnostics` endpoints for fetch and mark-seen flows.
- Integrated inline insight delivery into the review session with adaptive insertion cadence (10/7/5 cards), Space-to-dismiss keyboard behavior, session-scoped seen tracking, and summary pattern counts.
- Added backend unit/integration coverage for diagnostics and frontend component/store coverage for the new review insight UI.
- Fixed review session summary state so `cardsReviewed` and session duration survive until the summary is dismissed.
- Verified targeted backend/frontend checks and recorded unrelated existing failures from the wider backend/frontend suites.

### File List

- `backend/src/app/main.py`
- `backend/src/app/modules/dashboard/domain/value_objects.py`
- `backend/src/app/modules/dashboard/domain/entities.py`
- `backend/src/app/modules/dashboard/domain/interfaces.py`
- `backend/src/app/modules/dashboard/domain/exceptions.py`
- `backend/src/app/modules/dashboard/infrastructure/models.py`
- `backend/src/app/modules/dashboard/infrastructure/repository.py`
- `backend/src/app/modules/dashboard/application/services.py`
- `backend/src/app/modules/dashboard/api/schemas.py`
- `backend/src/app/modules/dashboard/api/dependencies.py`
- `backend/src/app/modules/dashboard/api/router.py`
- `backend/alembic/versions/8b2c4d6e7f80_create_diagnostic_insights_tables.py`
- `backend/tests/unit/modules/dashboard/__init__.py`
- `backend/tests/unit/modules/dashboard/application/__init__.py`
- `backend/tests/unit/modules/dashboard/domain/__init__.py`
- `backend/tests/unit/modules/dashboard/domain/test_entities.py`
- `backend/tests/unit/modules/dashboard/application/test_services.py`
- `backend/tests/integration/modules/dashboard/__init__.py`
- `backend/tests/integration/modules/dashboard/test_diagnostics.py`
- `frontend/src/types/diagnostics.ts`
- `frontend/src/lib/query-keys.ts`
- `frontend/src/hooks/usePendingInsights.ts`
- `frontend/src/hooks/useInsightSeenMutation.ts`
- `frontend/src/hooks/useReviewKeyboard.ts`
- `frontend/src/stores/review-store.ts`
- `frontend/src/stores/useReviewStore.test.ts`
- `frontend/src/components/review/InsightCard.tsx`
- `frontend/src/components/review/InsightCard.test.tsx`
- `frontend/src/components/review/SessionSummary.tsx`
- `frontend/src/components/review/SessionSummary.test.tsx`
- `frontend/src/components/review/index.ts`
- `frontend/src/app/(app)/review/page.tsx`
