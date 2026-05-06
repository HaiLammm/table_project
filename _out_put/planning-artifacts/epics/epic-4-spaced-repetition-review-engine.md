# Epic 4: Spaced Repetition Review Engine

Users can review vocabulary cards scheduled by FSRS in a daily queue (overdue > due > new), rate cards with keyboard-first flow (Space → 1/2/3/4 → auto-advance), toggle per-card bilingual view, view upcoming schedule, and receive session-end intelligence summaries. Includes diagnostic micro-insertions, rating feedback, and mobile touch support.

## Story 4.1: SRS Data Model & FSRS Integration

As the **system**,
I want SRS cards with FSRS state stored as JSONB and a daily review queue computed by the scheduling algorithm,
So that users receive optimally-spaced reviews based on proven memory science.

**Acceptance Criteria:**

**Given** the SRS module is initialized
**When** Alembic migration runs
**Then** `srs_cards` table is created with: id, user_id, term_id, language (en/jp), fsrs_state (JSONB), due_at, stability, difficulty, reps, lapses, created_at, updated_at
**And** `srs_reviews` table is created with: id, card_id, user_id, rating (1-4), reviewed_at, response_time_ms, session_id
**And** an index exists on `srs_cards(user_id, due_at)` for fast queue queries
**And** py-fsrs library is integrated in the SRS domain service
**And** the daily queue endpoint (`GET /api/v1/srs_cards/due`) returns cards prioritized: overdue > due > new
**And** queue computation completes within 100ms for users with up to 10,000 cards (NFR7)

**Given** a user adds a vocabulary term to their SRS
**When** the SRS card is created
**Then** FSRS state is initialized with default parameters
**And** the card appears in the next review queue
**And** retention is tracked per language independently for bilingual terms (FR19)

## Story 4.2: ReviewCard Component & Card Reveal Flow

As a **user**,
I want to see vocabulary cards in a clean review interface and reveal answers with a single keypress,
So that I can focus on recall without UI distractions.

**Acceptance Criteria:**

**Given** a user is on the Today's Queue page with cards due
**When** the page loads
**Then** the first card displays in front state: term (28px, #09090B), Japanese reading (18px, #3F3F46), part-of-speech/level tag (13px, #71717A), session counter "1/24" per UX-DR3
**And** "Press [Space] to reveal answer" hint is shown
**And** the card uses bg-zinc-100 border border-zinc-200 rounded-[14px] p-10 styling

**Given** a user presses Space (or taps the card on mobile per UX-DR26)
**When** the card transitions to revealed state
**Then** definition, IPA (JetBrains Mono), example sentence (gray bg with left border), and CEFR level appear below the term
**And** Tab key toggles Japanese definition (parallel mode per FR9) for this card only
**And** the rating buttons appear below the revealed content
**And** the reveal transition is ≤150ms (instant swap if prefers-reduced-motion)

**Given** the queue header loads
**When** cards are due
**Then** StatChip components display: card count, estimated time, retention rate per UX-DR10

## Story 4.3: RatingButton Component & Card Rating

As a **user**,
I want to rate each card (Again/Hard/Good/Easy) with keyboard shortcuts showing next-review intervals,
So that I can self-assess quickly and trust the scheduling system.

**Acceptance Criteria:**

**Given** a card is in revealed state
**When** the rating buttons appear per UX-DR4
**Then** 4 buttons display: Again (1), Hard (2), Good (3), Easy (4) with next-review interval below each (e.g., "<1m", "6m", "1d", "4d")
**And** each button has semantic color hover: Again (red-50), Hard (amber-50), Good (green-50), Easy (zinc-100)
**And** buttons have ARIA label: "Rate as {label}, next review in {interval}"

**Given** a user presses 1, 2, 3, or 4 (or taps a rating button on mobile per UX-DR26)
**When** the rating is submitted (`POST /api/v1/srs_cards/{id}/review`)
**Then** py-fsrs calculates the new FSRS state and next due_at
**And** the review is recorded in srs_reviews (rating, response_time_ms, timestamp — FR26)
**And** a subtle border color flash appears (100ms): Again red-300, Hard amber-300, Good green-300, Easy zinc-400 per UX-DR25
**And** the next card auto-advances (slide transition ≤150ms) per UX-DR13
**And** the session counter updates

**Given** a user on mobile
**When** rating buttons display
**Then** buttons render in a 2x2 grid layout per UX-DR26
**And** minimum touch target is 48x48px with 8px gap

## Story 4.4: Review Session Flow & Keyboard Navigation

As a **user**,
I want a complete keyboard-driven review session with auto-advance, undo, and session exit,
So that I can complete my daily reviews in 3 keystrokes per card without touching the mouse.

**Acceptance Criteria:**

**Given** a user starts a review session
**When** the review page is active per UX-DR13
**Then** the sidebar auto-collapses to maximize focus per UX-DR23
**And** the breadcrumb shows live progress: "Reviewing · 5 / 24"
**And** the full keyboard flow works: Space (reveal) → 1/2/3/4 (rate) → auto-advance to next card
**And** Esc ends the session early (shows session summary)

**Given** a user rates a card
**When** they press Ctrl+Z within 3 seconds
**Then** the last rating is undone, the previous card reappears in revealed state
**And** a toast shows "Card rated {label} — Ctrl+Z to undo" per UX-DR15

**Given** a user closes the app mid-session
**When** they return
**Then** the session resumes from the last unrated card (progress saved per-card)

**Given** a user has 0 cards due
**When** the Today's Queue loads
**Then** an empty state displays: "All caught up!" with suggestions (add words, review weak cards) per UX-DR16

## Story 4.5: Diagnostic Micro-Insertions in Review Flow

As a **user**,
I want brief diagnostic insights to appear inline during my review session every ~5 cards,
So that I receive actionable learning intelligence without leaving the review flow.

**Acceptance Criteria:**

**Given** a user is in an active review session
**When** they have reviewed approximately 5 cards and a diagnostic insight is available
**Then** an InsightCard (inline variant) appears below the current card per UX-DR18
**And** the InsightCard uses dark background (#18181B) to distinguish from vocabulary cards per UX-DR5
**And** it shows: icon + severity indicator (info/warning/success) + short insight text
**And** example: "Quick insight: You rated 'protocol' as Hard 3 times this week. Consider reviewing networking terms in morning sessions."
**And** the user presses Space to dismiss and continue reviewing

**Given** insufficient review data exists (< 50 reviews)
**When** the system checks for insights
**Then** no insight cards are shown (progressive reveal — not forced)

## Story 4.6: Session-End Intelligence Summary

As a **user**,
I want a session summary that shows what changed (cards graduated, patterns detected, tomorrow's estimate) after completing my review,
So that I feel a sense of progress and connection to my long-term learning trajectory.

**Acceptance Criteria:**

**Given** a user completes all cards in the review queue (or presses Esc)
**When** the session summary screen displays per UX-DR19
**Then** it shows:
  - Total cards reviewed and session duration
  - Cards graduated to mastered this session (delta, not absolute)
  - New patterns detected (if any, links to Dashboard)
  - Tomorrow's estimate: card count + estimated time
**And** action buttons: "View Dashboard" (secondary), "Add Words" (secondary)
**And** no confetti, no streaks, no XP — clean intelligence summary
**And** the sidebar restores to its pre-review state

## Story 4.7: Upcoming Review Schedule

As a **user**,
I want to view how many cards are due today, tomorrow, and this week,
So that I can plan my study time and understand my review workload.

**Acceptance Criteria:**

**Given** a user is on Today's Queue or Dashboard
**When** the schedule data loads (`GET /api/v1/srs_cards/schedule`)
**Then** the display shows: cards due today, cards due tomorrow, cards due this week (FR20)
**And** estimated review time is calculated (based on average time per card from past sessions)
**And** data refreshes after each review session completes
