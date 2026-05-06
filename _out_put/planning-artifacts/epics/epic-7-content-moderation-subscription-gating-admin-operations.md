# Epic 7: Content Moderation, Subscription Gating & Admin Operations

Users can flag incorrect definitions (hidden + routed to moderation). System enforces free-tier limits, displays upgrade prompts, and gates features by subscription tier. Administrators can view operations dashboard (LLM costs, enrichment queue, cache hit rate), manage moderation queue, configure rate limits, receive cost alerts, and seed corpus terms.

## Story 7.1: User Content Flagging & Moderation Queue

As a **user**,
I want to flag vocabulary definitions that are incorrect or inappropriate,
So that content quality is maintained and I can trust the definitions I'm learning.

**Acceptance Criteria:**

**Given** a user views a vocabulary definition (FR35)
**When** they click the flag icon
**Then** a flag is recorded via `POST /api/v1/vocabulary_definitions/{id}/flag` with reason (incorrect/inappropriate/other)
**And** the flagged definition is temporarily hidden from display (FR36)
**And** a replacement message shows: "This definition has been flagged for review"
**And** the flag is routed to the admin moderation queue

**Given** a definition has not been cross-validated against JMdict (FR37)
**When** it is displayed anywhere in the app
**Then** a warning indicator (icon + tooltip: "Not yet validated against JMdict") appears next to the definition

**Given** an admin opens the moderation queue (FR42)
**When** the queue loads (`GET /api/v1/admin/moderation`)
**Then** flagged definitions are listed with: term, definition, flag reason, flag count, flagged_at
**And** for each item, admin can: Approve (unhide), Reject (permanently remove), Fix (edit definition and approve)
**And** approved definitions are unhidden; rejected definitions are permanently removed

## Story 7.2: Subscription Tier Enforcement & Upgrade Prompts

As a **user**,
I want the system to enforce my subscription tier limits and show me clear upgrade paths when I hit them,
So that I understand what I get for free and what requires a paid subscription.

**Acceptance Criteria:**

**Given** a free-tier user (FR38)
**When** they attempt to add a 51st active SRS card
**Then** the action is blocked with a clear message: "Free tier limit: 50 active SRS cards. Upgrade to Student for unlimited cards."
**And** an "Upgrade" button links to the upgrade flow

**Given** a free-tier user
**When** they attempt a 6th LLM enrichment in a day (FR38)
**Then** the enrichment is blocked: "Daily enrichment limit reached (5/5). Upgrade to Student for unlimited enrichments."

**Given** a free-tier user encounters any tier-gated feature (FR40)
**When** the feature is restricted
**Then** appropriate upgrade prompts display (not error messages — friendly upsell)
**And** the prompt clearly states what the upgrade unlocks

**Given** a user wants to upgrade (FR39)
**When** they click "Upgrade" from any prompt or from Settings
**Then** they are presented with tier comparison: Free vs Student ($4-5/mo)
**And** Student tier unlocks: unlimited SRS cards, full diagnostics, import/export, unlimited enrichments
**And** upgrade is processed (payment integration — Stripe or similar)
**And** tier change takes effect immediately (Clerk metadata updated, backend tier check refreshed)

## Story 7.3: Admin Operations Dashboard

As an **administrator**,
I want an operations dashboard showing LLM costs, enrichment queue status, and cache hit rate,
So that I can monitor platform health and control costs proactively.

**Acceptance Criteria:**

**Given** an admin navigates to the admin dashboard (FR41)
**When** the page loads (`GET /api/v1/admin/dashboard`)
**Then** the dashboard displays:
  1. LLM Cost Tracking: today's spend, daily budget, spend trend (7-day chart)
  2. Enrichment Queue Status: pending jobs, processing, completed today, failed (with retry option)
  3. Cache Hit Rate: current percentage, target (70%), trend
**And** all metrics refresh on page load (not real-time polling at MVP)

**Given** an admin views failed enrichment jobs
**When** they click on a failed job
**Then** they see: term, error message, retry count, last attempt timestamp
**And** they can retry the job or route to dead-letter queue

## Story 7.4: Admin Rate Limit Configuration & Cost Alerts

As an **administrator**,
I want to configure per-tier rate limits and receive alerts when LLM spending exceeds thresholds,
So that I can prevent cost overruns and maintain platform sustainability.

**Acceptance Criteria:**

**Given** an admin navigates to rate limit settings (FR43)
**When** they view the configuration
**Then** per-tier rate limits are displayed: Free (5 enrichments/day), Student (unlimited), Professional (unlimited)
**And** limits are editable via `PUT /api/v1/admin/config/rate_limits`
**And** changes take effect immediately

**Given** daily LLM spend exceeds a configurable threshold (FR44)
**When** the cost tracking system detects the overage
**Then** an alert is created and visible on the admin dashboard
**And** the alert shows: current spend, threshold, projected daily total, recommended action
**And** admin can take action: tighten free-tier limits, switch to Batch API, or acknowledge

## Story 7.5: Admin Corpus Seeding & Management

As an **administrator**,
I want to seed new vocabulary terms into the central corpus,
So that I can proactively expand the shared vocabulary base for common learning domains.

**Acceptance Criteria:**

**Given** an admin wants to seed new terms (FR45)
**When** they use the corpus seeding interface (`POST /api/v1/admin/corpus/seed`)
**Then** they can submit terms individually or in batch (CSV upload)
**And** each term is auto-enriched via the LLM pipeline (reuses Epic 3 enrichment)
**And** Japanese definitions are cross-validated against JMdict before entering the corpus
**And** seeded terms go through deduplication against existing corpus
**And** a summary shows: X terms added, Y duplicates skipped, Z validation failures
