# Epic 6: Learning Diagnostics & Progress Dashboard

Users can view a progress dashboard with retention curves, vocabulary growth, SRS health metrics, calendar views, study streaks, and AI-generated diagnostic insights (time-of-day patterns, category weaknesses, cross-language interference). Dashboard implements progressive intelligence reveal (Day 1 basic stats → Week 2+ full diagnostics).

## Story 6.1: Diagnostic Signal Capture & Pattern Detection Engine

As the **system**,
I want to capture diagnostic signals from every review and detect learning patterns in the background,
So that actionable insights can be surfaced to users as their data accumulates.

**Acceptance Criteria:**

**Given** a user completes a card review (FR26)
**When** the review is recorded
**Then** diagnostic signals are captured: timestamp, response_time_ms, difficulty rating, card category (vocabulary hierarchy), session_id, session_length, language, parallel_mode_active
**And** signals are stored in srs_reviews (already created in Epic 4) with additional metadata columns via Alembic migration

**Given** a user has accumulated ≥7 days of review data with ≥50 total reviews (FR27)
**When** the diagnostics background worker runs
**Then** time-of-day retention patterns are detected (e.g., "retention drops 35% after 9pm for IT terms")
**And** recommendations are generated and stored

**Given** a user has ≥30 reviews within a vocabulary category (FR28)
**When** the diagnostics worker analyzes category data
**Then** category-specific weakness patterns are detected (e.g., "networking terms consistently rated Hard")

**Given** a user has ≥20 parallel-mode reviews for a given term (FR29)
**When** the diagnostics worker analyzes cross-language data
**Then** cross-language interference patterns are detected (e.g., "JP retention drops when reviewing same term in parallel mode")

**Given** insufficient data for a pattern type
**When** the worker checks thresholds
**Then** that pattern type is skipped — no false insights generated

## Story 6.2: Progress Dashboard — Stats & Metrics

As a **user**,
I want to view my vocabulary count, cards mastered, review completion rate, and study streak on a progress dashboard,
So that I can track my overall learning progress at a glance.

**Acceptance Criteria:**

**Given** a user navigates to the Dashboard page
**When** the page loads (`GET /api/v1/dashboard/stats`)
**Then** 3 DashCard components display per UX-DR7:
  1. Retention Rate (percentage + delta vs last week, up/down indicator)
  2. Words Mastered (count + delta this week)
  3. Review Streak (days + "current" label)
**And** each DashCard uses bg-zinc-100 border border-zinc-200 rounded-[10px] p-5 styling
**And** delta indicators use green for positive, amber for negative

**Given** a user views vocabulary stats (FR33)
**When** the stats section loads
**Then** current vocabulary count, cards mastered, and review completion rate are displayed

**Given** a user views their study streak (FR34)
**When** the streak data loads
**Then** active study streak (consecutive days with ≥1 review) and historical consistency are shown
**And** no guilt messaging for broken streaks — just the number

## Story 6.3: Activity Chart & Calendar Views

As a **user**,
I want to view 14-day activity charts and calendar views of my learning activity,
So that I can visualize my study patterns and consistency over time.

**Acceptance Criteria:**

**Given** a user is on the Dashboard
**When** the activity section loads (`GET /api/v1/dashboard/activity`)
**Then** a 14-day bar chart (ActivityChart component) displays per UX-DR8
**And** bars use zinc-600, today's bar uses zinc-900, empty days use zinc-100
**And** chart height is 80px
**And** time range toggle tabs (7d / 14d / 30d) are available via shadcn/ui Tabs

**Given** a user views calendar views (FR32)
**When** they switch to daily or weekly view
**Then** learning activity is displayed with review counts per day
**And** the layout is responsive: 3-column on desktop, 2-column on tablet, 1-column stack on mobile

## Story 6.4: Diagnostic Insights Dashboard (Progressive Reveal)

As a **user**,
I want to view AI-generated diagnostic insights on my dashboard that progressively unlock as my data grows,
So that I discover actionable patterns about my learning without information overload.

**Acceptance Criteria:**

**Given** a user is on the Dashboard with Day 1-2 of data (UX-DR20)
**When** the insights section loads
**Then** only basic stats are shown (cards reviewed, accuracy)
**And** an encouragement message: "Building your insights... Complete a few review sessions and we'll show your learning patterns."

**Given** a user has Day 3-5 of data (UX-DR20)
**When** the insights section loads
**Then** 1-2 simple micro-insights appear (e.g., "Your accuracy is highest in the morning!")

**Given** a user has Week 2+ of data (FR30, UX-DR20)
**When** the insights section loads
**Then** full diagnostic InsightCard list displays per UX-DR5 (expandable variant)
**And** each InsightCard shows: severity icon (info/warning/success), title, short description
**And** clicking expands to: detailed explanation + recommended action + optional action button
**And** insights include: time-of-day patterns (FR27), category weaknesses (FR28), cross-language interference (FR29)

**Given** a user dismisses an insight
**When** they click dismiss
**Then** the insight fades to lower priority (not deleted)
**And** dismissed insights remain accessible in the full insights list

## Story 6.5: Retention Curves & Vocabulary Growth Visualization

As a **user**,
I want to view retention curves and vocabulary growth over time,
So that I can see evidence-based proof that my learning strategy is working.

**Acceptance Criteria:**

**Given** a user is on the Dashboard (FR31)
**When** the visualization section loads (`GET /api/v1/dashboard/retention`)
**Then** a retention curve chart shows recall accuracy over time intervals (1d, 3d, 7d, 14d, 30d)
**And** a vocabulary growth line chart shows cumulative terms added over time
**And** SRS health metrics display: cards in each state (new, learning, review, mastered)
**And** charts use accessible patterns: not color-alone, `role="img"` with descriptive `aria-label`
**And** Skeleton loading states match chart layout per UX-DR17
