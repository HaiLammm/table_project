# Epic List

## Epic 1: Project Foundation & Developer Infrastructure
Set up both frontend (Next.js 16 + shadcn/ui) and backend (FastAPI + Hexagonal/DDD) scaffolds, CI/CD pipeline, database provisioning, design system tokens, app shell layout, and Sprint 0 end-to-end validation.
**FRs covered:** None directly (infrastructure prerequisite)
**Additional Reqs:** Custom scaffold, CI/CD, Sprint 0 validation, Neon/Upstash/Clerk/Railway/Vercel setup
**UX-DRs:** UX-DR1, UX-DR2, UX-DR11, UX-DR12, UX-DR14, UX-DR17

## Epic 2: User Authentication, Onboarding & Profile
Users can register (email/Google/LINE OAuth), log in with persistent sessions, complete a 5-question onboarding survey to receive an AI-generated learning plan, manage profile settings, and exercise data privacy rights (export/delete).
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6
**UX-DRs:** UX-DR9, UX-DR22

## Epic 3: Vocabulary Management & Enrichment Pipeline
Users can browse/search the pre-seeded vocabulary corpus, view terms in single-language or parallel bilingual mode, add terms manually, request LLM-enriched vocabulary sets via structured form, import from CSV, and view the hierarchical vocabulary tree. The system auto-enriches terms via LLM, cross-validates Japanese definitions against JMdict, and syncs validated results to the central corpus (Database Waterfall).
**FRs covered:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16
**UX-DRs:** UX-DR24

## Epic 4: Spaced Repetition Review Engine
Users can review vocabulary cards scheduled by FSRS in a daily queue (overdue > due > new), rate cards with keyboard-first flow (Space → 1/2/3/4 → auto-advance), toggle per-card bilingual view, view upcoming schedule, and receive session-end intelligence summaries. Includes diagnostic micro-insertions, rating feedback, and mobile touch support.
**FRs covered:** FR17, FR18, FR19, FR20, FR21
**UX-DRs:** UX-DR3, UX-DR4, UX-DR5 (inline), UX-DR10, UX-DR13, UX-DR15, UX-DR18, UX-DR19, UX-DR23, UX-DR25, UX-DR26

## Epic 5: Personal Collections
Users can create, rename, and delete personal vocabulary collections, add/remove terms, browse collection contents, and start focused learning sessions from a collection (bridge to SRS).
**FRs covered:** FR22, FR23, FR24, FR25
**UX-DRs:** UX-DR6, UX-DR16

## Epic 6: Learning Diagnostics & Progress Dashboard
Users can view a progress dashboard with retention curves, vocabulary growth, SRS health metrics, calendar views, study streaks, and AI-generated diagnostic insights (time-of-day patterns, category weaknesses, cross-language interference). Dashboard implements progressive intelligence reveal (Day 1 basic stats → Week 2+ full diagnostics).
**FRs covered:** FR26, FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34
**UX-DRs:** UX-DR5 (expandable), UX-DR7, UX-DR8, UX-DR20

## Epic 7: Content Moderation, Subscription Gating & Admin Operations
Users can flag incorrect definitions (hidden + routed to moderation). System enforces free-tier limits, displays upgrade prompts, and gates features by subscription tier. Administrators can view operations dashboard (LLM costs, enrichment queue, cache hit rate), manage moderation queue, configure rate limits, receive cost alerts, and seed corpus terms.
**FRs covered:** FR35, FR36, FR37, FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR45

---
