# Requirements Inventory

## Functional Requirements

FR1: Users can register an account using email/password, Google OAuth, or LINE OAuth.
FR2: Users can log in and maintain authenticated sessions across browser tabs.
FR3: Users can complete an onboarding survey (current level, goal, domain, daily study time, language priority) to receive an AI-generated learning plan.
FR4: Users can view and edit their profile settings (languages, level, goals, daily study budget, notification preferences).
FR5: Users can request export of all their personal data (vocabulary, reviews, learning patterns).
FR6: Users can request permanent deletion of their account and all associated data.
FR7: Users can browse and search the pre-seeded vocabulary corpus by topic, CEFR level, and JLPT level.
FR8: Users can view a vocabulary term with its definition, IPA, examples, CEFR level, and related terms in a single-language view (English or Japanese).
FR9: Users can toggle parallel mode to view both English and Japanese definitions side-by-side for any term.
FR10: Users can add a new vocabulary term manually with basic information (term, language, optional definition).
FR11: Users can request a vocabulary set via structured form (topic, level, count) and receive LLM-enriched terms to preview and confirm.
FR12: Users can import vocabulary from CSV files with error preview, partial import, and handling of malformed records.
FR13: Users can view the hierarchical vocabulary tree (e.g., IT → Networking → Router/Switch/Protocol).
FR14: The system auto-enriches new vocabulary terms with definitions, IPA, CEFR level, examples, and related terms via LLM pipeline.
FR15: The system cross-validates all LLM-generated Japanese definitions against JMdict before displaying to users.
FR16: The system syncs validated enrichment results to the central corpus (Database Waterfall) after deduplication.
FR17: Users can review vocabulary cards scheduled by the FSRS algorithm in a daily review queue prioritized as overdue > due > new.
FR18: Users can rate each card review (Again, Hard, Good, Easy) to update FSRS scheduling state.
FR19: The system tracks retention per language independently for bilingual terms.
FR20: Users can view their upcoming review schedule (number of cards due today, tomorrow, this week).
FR21: The system recalibrates FSRS scheduling for imported cards within 3–5 days of initial reviews.
FR22: Users can create, rename, and delete personal vocabulary collections.
FR23: Users can add and remove vocabulary terms from collections.
FR24: Users can browse collections and view terms organized within each collection.
FR25: Users can start a learning session from a collection (bridge collection to SRS: start learning, pause, archive).
FR26: The system captures diagnostic signals per review: timestamp, response time, difficulty rating, card category, and session length.
FR27: The system detects time-of-day retention patterns and surfaces recommendations after ≥7 days of review data with ≥50 total reviews.
FR28: The system detects category-specific weakness patterns after ≥30 reviews within a vocabulary category.
FR29: The system detects cross-language interference patterns when parallel mode is active, after ≥20 parallel-mode reviews for a given term.
FR30: Users can view diagnostic insights and recommendations on their dashboard.
FR31: Users can view a progress dashboard with retention curves, vocabulary growth over time, and SRS health metrics.
FR32: Users can view calendar views of their learning activity (daily and weekly).
FR33: Users can view their current vocabulary count, cards mastered, and review completion rate.
FR34: Users can view their active study streak and historical learning consistency.
FR35: Users can flag any vocabulary definition as incorrect or inappropriate.
FR36: Flagged definitions are temporarily hidden from display and routed to a moderation queue.
FR37: The system displays a warning indicator on definitions that have not been cross-validated against JMdict.
FR38: The system enforces free-tier limits (50 active SRS cards, 5 LLM enrichments per day).
FR39: Users can upgrade from free to Student tier to unlock unlimited cards, full diagnostics, and import/export.
FR40: The system gates features by subscription tier and displays appropriate upgrade prompts when limits are reached.
FR41: Administrators can view an operations dashboard showing LLM cost tracking, enrichment queue status, and cache hit rate.
FR42: Administrators can review and resolve flagged content in a moderation queue (approve, reject, or fix definitions).
FR43: Administrators can configure per-tier rate limits for LLM enrichment endpoints.
FR44: The system alerts administrators when LLM spending exceeds configurable daily thresholds.
FR45: Administrators can seed new vocabulary terms into the central corpus.

## NonFunctional Requirements

NFR1: Non-LLM API endpoints respond within 200ms at p95 under normal load.
NFR2: LLM enrichment endpoints respond within 3 seconds at p95, with time-to-first-token < 800ms for streaming responses.
NFR3: Card review interaction (flip, rate) completes with < 100ms perceived latency (client-side, no server round-trip required for flip).
NFR4: Dashboard initial load (after login) achieves Time to Interactive < 3.5 seconds.
NFR5: Landing page achieves Largest Contentful Paint < 2.5 seconds and Cumulative Layout Shift < 0.1.
NFR6: CSV import processes up to 5,000 records within 30 seconds, with progress indication for imports > 500 records.
NFR7: Daily review queue computation (fetching due cards for a user) completes within 100ms for users with up to 10,000 cards.
NFR8: All data encrypted in transit (TLS 1.3) and at rest (managed PostgreSQL encryption).
NFR9: Authentication uses short-lived access tokens (15-minute expiry) with refresh token rotation.
NFR10: LLM API keys are stored server-side only — never exposed to browser or extension clients.
NFR11: Per-user rate limiting enforced on all LLM enrichment endpoints (configurable per subscription tier).
NFR12: User vocabulary lists and learning patterns are never logged in application logs. Structured logs use PII scrubbing.
NFR13: User-content delimiters used in all LLM prompts to mitigate prompt injection from user-submitted vocabulary.
NFR14: GDPR-compliant data export and deletion endpoints operational from Day 1.
NFR15: System supports 100 concurrent active users on MVP infrastructure (≤ $50/month).
NFR16: Architecture supports 10x user growth (1,000 concurrent users) with horizontal scaling without architectural redesign.
NFR17: LLM enrichment pipeline handles traffic spikes via queue-based async processing — degrading gracefully.
NFR18: Central vocabulary corpus supports up to 100,000 validated terms without query performance degradation.
NFR19: Daily LLM cost per active user remains below $0.02 through prompt caching, Batch API, and provider routing.
NFR20: Core learning flows conform to WCAG 2.1 Level AA.
NFR21: Full keyboard navigation supported for the card review workflow.
NFR22: Screen reader support via ARIA labels for interactive components and live regions for dynamic content updates.
NFR23: Color contrast meets minimum 4.5:1 for normal text and 3:1 for large text. Status indicators use shape/icon differentiation in addition to color.
NFR24: UI respects prefers-reduced-motion and prefers-color-scheme user preferences.
NFR25: LLM provider gateway supports switching between multiple LLM providers without application code changes.
NFR26: CSV import supports UTF-8 encoding with BOM, tab-separated values, and hierarchical tag notation.
NFR27: JMdict cross-validation operates against a locally-cached dataset (~170K entries), not an external API call.
NFR28: Offline card review functions via PWA with client-side persistent storage — reviews sync when connectivity is restored.
NFR29: All API endpoints documented via framework-native auto-generated OpenAPI specification.
NFR30: System achieves 99.5% uptime for core learning flows. Maintenance windows scheduled outside peak hours.
NFR31: LLM provider outage does not block card review or dashboard access — only auto-enrichment degrades gracefully.
NFR32: Database backups run daily with point-in-time recovery capability.
NFR33: Failed enrichment jobs retry up to 3 times with exponential backoff before routing to a dead-letter queue.
NFR34: Background job failure rate remains below 1% of total jobs processed.

## Additional Requirements

- Architecture specifies a **custom scaffold** backend (uv + FastAPI + SQLAlchemy 2.0 async + Alembic async + Hexagonal/DDD) and **create-next-app + shadcn/ui** frontend — Sprint 0 must set up both scaffolds with CI/CD validation.
- 8 bounded contexts (auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard) each following hexagonal (ports & adapters) module structure.
- LLM Gateway as internal module: multi-provider routing (Claude Haiku, Gemini Flash, DeepSeek), prompt caching, cost tracking, fallback, structured output validation via Pydantic.
- Infrastructure: Neon (PostgreSQL 16), Upstash Redis (ARQ queue + LLM cache + rate limits), Clerk (auth), Railway (backend hosting), Vercel (frontend hosting).
- ARQ + Redis for background processing: LLM enrichment queue, daily SRS queue pre-computation, Database Waterfall corpus sync.
- Outbox pattern for cross-context domain events (pending_events table flushed by ARQ worker).
- Pre-seeded corpus: 3,000–5,000 IT/TOEIC/JLPT N3–N2 terms via one-time LLM batch job with JMdict validation.
- JMdict integration: jamdict library, ~170K entries, LRU cached in-process.
- FSRS state stored as JSONB on srs_cards table; py-fsrs library for algorithm.
- Hierarchical vocabulary: adjacency list (parent_id) with recursive CTEs; ltree deferred post-MVP.
- Full-text search: PostgreSQL tsvector on vocabulary_terms for ⌘K command palette.
- CI/CD: GitHub Actions — backend (Ruff → mypy → pytest → Docker build), frontend (ESLint → tsc → vitest → next build).
- Sprint 0 validation: one Alembic migration, one health endpoint, one pytest, one shadcn/ui page, CI green.

## UX Design Requirements

UX-DR1: Implement the zinc-based monochromatic design system with CSS custom properties (--bg, --surface, --chrome-bg, --accent, etc.) matching the "Light Canvas, Dark Chrome, Gray Cards" palette from the UX spec.
UX-DR2: Configure the multi-script font stack — Inter Variable (Latin/Vietnamese), Noto Sans JP Variable (Japanese), JetBrains Mono (IPA/code) — with CSS unicode-range for automatic script switching and +2px line-height adjustment for Japanese text.
UX-DR3: Build the ReviewCard component with front/revealed/transitioning states, bilingual layout (term-main 28px, term-jp 18px, term-pos 13px), Space to reveal, 150ms card transition (respecting prefers-reduced-motion).
UX-DR4: Build the RatingButton component with 4 variants (again/hard/good/easy), semantic color hover states (red-50, amber-50, green-50, zinc-100), keyboard activation (1/2/3/4), interval display, and ARIA labels.
UX-DR5: Build the InsightCard component with inline and expandable variants, dark background (#18181B), severity icons (info/warning/success), and dismiss capability.
UX-DR6: Build the CollectionCard component with icon, name, term count, mastery percentage, progress bar (zinc-600 fill), and "create" variant (dashed border, + icon).
UX-DR7: Build the DashCard component for dashboard metric display with large number + delta indicator (up/down direction).
UX-DR8: Build the ActivityChart component — 14-day bar chart with gray bars (zinc-600), today bar darker (zinc-900), empty days (zinc-100), 80px height.
UX-DR9: Build the OnboardingStep component — single-question-per-screen, progress dots, selected state fills black (#18181B), full-width centered layout, back/skip support.
UX-DR10: Build the StatChip component for compact inline stat display in queue header.
UX-DR11: Implement the app shell layout — dark sidebar (240px, zinc-900) with 4 navigation items (Today's Queue, Collections, Dashboard, Settings), topbar (56px) with breadcrumb + ⌘K + avatar, content area max-width 720px centered.
UX-DR12: Implement responsive breakpoints — mobile (<640px: sidebar hidden/hamburger, full-width cards, 2x2 rating buttons), tablet (640-1024px: icon sidebar 56px), desktop (>1024px: full sidebar 240px).
UX-DR13: Implement keyboard-first review flow — Space (reveal), 1/2/3/4 (rate), Tab (toggle JP), Ctrl+Z (undo within 3s), Esc (end session), auto-advance after rating.
UX-DR14: Implement the 3-tier button hierarchy — Primary (bg-zinc-900 text-zinc-50), Secondary (bg-white border-zinc-200), Ghost (text-zinc-500) — with max 1 primary button per screen.
UX-DR15: Implement toast notification system — dark background (zinc-900), 4 types (success/undo/error/info) with colored left border, bottom-right positioning, max 3 stacked.
UX-DR16: Implement empty states for all screens (Today's Queue "All caught up!", Collections "No collections yet", Search "No results", Dashboard "Building your insights...") with centered icon + title + description + action button.
UX-DR17: Implement loading states using shadcn/ui Skeleton components matching exact content layout — no full-page spinners.
UX-DR18: Implement diagnostic micro-insertion pattern — InsightCard appears inline every ~5 cards during review flow, dark background, read → Space → continue.
UX-DR19: Implement session-end intelligence summary — show deltas (cards graduated, patterns detected, tomorrow's estimate), not just absolutes.
UX-DR20: Implement progressive intelligence reveal — Day 1-2 (basic stats only), Day 3-5 (first micro-insights), Week 2+ (full diagnostic dashboard).
UX-DR21: Implement WCAG 2.1 AA accessibility — visible focus indicators (ring-2 ring-zinc-900), focus trap in modals, skip-to-content link, ARIA live regions for card counter and toasts, screen reader announcements for card reveal/rate/session complete.
UX-DR22: Implement warm return screen — after absence show "24 cards ready. ~4 min estimated." instead of guilt messaging.
UX-DR23: Implement review flow sidebar auto-collapse — sidebar minimizes during active review to maximize focus, breadcrumb shows live progress "Reviewing · 5 / 24".
UX-DR24: Implement the Command Palette (⌘K) — full-screen overlay with backdrop blur, auto-focused search, results grouped (Pages, Collections, Words), keyboard navigation.
UX-DR25: Implement per-card rating feedback — subtle border color flash (100ms): Again red-300, Hard amber-300, Good green-300, Easy zinc-400. Respects prefers-reduced-motion.
UX-DR26: Implement mobile touch interactions — tap card to reveal, tap rating buttons, swipe left to reveal (alternative), 2x2 rating button grid on mobile, 44x44px minimum touch targets.

## FR Coverage Map

| FR | Epic | Brief Description |
|---|---|---|
| FR1 | Epic 2 | Register with email/Google/LINE OAuth |
| FR2 | Epic 2 | Login and session management |
| FR3 | Epic 2 | Onboarding survey → AI learning plan |
| FR4 | Epic 2 | Profile settings management |
| FR5 | Epic 2 | Personal data export (GDPR) |
| FR6 | Epic 2 | Account deletion (GDPR) |
| FR7 | Epic 3 | Browse/search vocabulary corpus |
| FR8 | Epic 3 | View term in single-language view |
| FR9 | Epic 3 | Parallel bilingual mode toggle |
| FR10 | Epic 3 | Add vocabulary term manually |
| FR11 | Epic 3 | Structured vocabulary request (LLM) |
| FR12 | Epic 3 | CSV import with error handling |
| FR13 | Epic 3 | Hierarchical vocabulary tree |
| FR14 | Epic 3 | Auto-enrichment via LLM pipeline |
| FR15 | Epic 3 | JMdict cross-validation |
| FR16 | Epic 3 | Database Waterfall corpus sync |
| FR17 | Epic 4 | FSRS daily review queue |
| FR18 | Epic 4 | Card rating (Again/Hard/Good/Easy) |
| FR19 | Epic 4 | Per-language retention tracking |
| FR20 | Epic 4 | Upcoming review schedule |
| FR21 | Epic 4 | FSRS recalibration for imports |
| FR22 | Epic 5 | Create/rename/delete collections |
| FR23 | Epic 5 | Add/remove terms from collections |
| FR24 | Epic 5 | Browse collection contents |
| FR25 | Epic 5 | Start learning session from collection |
| FR26 | Epic 6 | Capture diagnostic signals per review |
| FR27 | Epic 6 | Time-of-day retention patterns |
| FR28 | Epic 6 | Category-specific weakness detection |
| FR29 | Epic 6 | Cross-language interference detection |
| FR30 | Epic 6 | View diagnostic insights on dashboard |
| FR31 | Epic 6 | Progress dashboard (retention curves, growth) |
| FR32 | Epic 6 | Calendar views (daily/weekly) |
| FR33 | Epic 6 | Vocabulary count, mastered, completion rate |
| FR34 | Epic 6 | Study streak and consistency |
| FR35 | Epic 7 | Flag incorrect definitions |
| FR36 | Epic 7 | Hide flagged definitions, route to moderation |
| FR37 | Epic 7 | Warning indicator for unvalidated content |
| FR38 | Epic 7 | Free-tier limit enforcement |
| FR39 | Epic 7 | Upgrade from free to Student tier |
| FR40 | Epic 7 | Feature gating by subscription tier |
| FR41 | Epic 7 | Admin operations dashboard |
| FR42 | Epic 7 | Admin content moderation queue |
| FR43 | Epic 7 | Admin rate limit configuration |
| FR44 | Epic 7 | Admin LLM cost alerts |
| FR45 | Epic 7 | Admin corpus seeding |
