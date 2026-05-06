# Functional Requirements

## User Management & Authentication

- **FR1:** Users can register an account using email/password, Google OAuth, or LINE OAuth.
- **FR2:** Users can log in and maintain authenticated sessions across browser tabs.
- **FR3:** Users can complete an onboarding survey (current level, goal, domain, daily study time, language priority) to receive an AI-generated learning plan.
- **FR4:** Users can view and edit their profile settings (languages, level, goals, daily study budget, notification preferences).
- **FR5:** Users can request export of all their personal data (vocabulary, reviews, learning patterns).
- **FR6:** Users can request permanent deletion of their account and all associated data.

## Vocabulary Management

- **FR7:** Users can browse and search the pre-seeded vocabulary corpus by topic, CEFR level, and JLPT level.
- **FR8:** Users can view a vocabulary term with its definition, IPA, examples, CEFR level, and related terms in a single-language view (English or Japanese).
- **FR9:** Users can toggle parallel mode to view both English and Japanese definitions side-by-side for any term.
- **FR10:** Users can add a new vocabulary term manually with basic information (term, language, optional definition).
- **FR11:** Users can request a vocabulary set via structured form (topic, level, count) and receive LLM-enriched terms to preview and confirm.
- **FR12:** Users can import vocabulary from CSV files with error preview, partial import, and handling of malformed records.
- **FR13:** Users can view the hierarchical vocabulary tree (e.g., IT → Networking → Router/Switch/Protocol).
- **FR14:** The system auto-enriches new vocabulary terms with definitions, IPA, CEFR level, examples, and related terms via LLM pipeline.
- **FR15:** The system cross-validates all LLM-generated Japanese definitions against JMdict before displaying to users.
- **FR16:** The system syncs validated enrichment results to the central corpus (Database Waterfall) after deduplication.

## Spaced Repetition & Review

- **FR17:** Users can review vocabulary cards scheduled by the FSRS algorithm in a daily review queue prioritized as overdue > due > new.
- **FR18:** Users can rate each card review (Again, Hard, Good, Easy) to update FSRS scheduling state.
- **FR19:** The system tracks retention per language independently for bilingual terms.
- **FR20:** Users can view their upcoming review schedule (number of cards due today, tomorrow, this week).
- **FR21:** The system recalibrates FSRS scheduling for imported cards within 3–5 days of initial reviews.

## Personal Collections

- **FR22:** Users can create, rename, and delete personal vocabulary collections.
- **FR23:** Users can add and remove vocabulary terms from collections.
- **FR24:** Users can browse collections and view terms organized within each collection.
- **FR25:** Users can start a learning session from a collection (bridge collection to SRS: start learning, pause, archive).

## Learning Diagnostics

- **FR26:** The system captures diagnostic signals per review: timestamp, response time, difficulty rating, card category, and session length.
- **FR27:** The system detects time-of-day retention patterns and surfaces recommendations (e.g., "review technical vocabulary in morning sessions") after a user accumulates ≥7 days of review data with ≥50 total reviews.
- **FR28:** The system detects category-specific weakness patterns (e.g., "networking terms consistently rated Hard") after a user accumulates ≥30 reviews within a vocabulary category.
- **FR29:** The system detects cross-language interference patterns when parallel mode is active, after a user accumulates ≥20 parallel-mode reviews for a given term.
- **FR30:** Users can view diagnostic insights and recommendations on their dashboard.

## Progress Dashboard & Analytics

- **FR31:** Users can view a progress dashboard with retention curves, vocabulary growth over time, and SRS health metrics.
- **FR32:** Users can view calendar views of their learning activity (daily and weekly).
- **FR33:** Users can view their current vocabulary count, cards mastered, and review completion rate.
- **FR34:** Users can view their active study streak and historical learning consistency.

## Content Quality & Moderation

- **FR35:** Users can flag any vocabulary definition as incorrect or inappropriate.
- **FR36:** Flagged definitions are temporarily hidden from display and routed to a moderation queue.
- **FR37:** The system displays a warning indicator on definitions that have not been cross-validated against JMdict.

## Subscription & Access Control

- **FR38:** The system enforces free-tier limits (50 active SRS cards, 5 LLM enrichments per day).
- **FR39:** Users can upgrade from free to Student tier to unlock unlimited cards, full diagnostics, and import/export.
- **FR40:** The system gates features by subscription tier and displays appropriate upgrade prompts when limits are reached.

## Administration & Operations

- **FR41:** Administrators can view an operations dashboard showing LLM cost tracking, enrichment queue status, and cache hit rate.
- **FR42:** Administrators can review and resolve flagged content in a moderation queue (approve, reject, or fix definitions).
- **FR43:** Administrators can configure per-tier rate limits for LLM enrichment endpoints.
- **FR44:** The system alerts administrators when LLM spending exceeds configurable daily thresholds.
- **FR45:** Administrators can seed new vocabulary terms into the central corpus.
