# Project Scoping & Phased Development

## MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP — validate that unified bilingual vocabulary learning with diagnostic intelligence solves a real pain point for Vietnamese IT bilingual learners better than the fragmented Anki + Duolingo status quo.

**Core Hypothesis:** Vietnamese IT professionals will adopt a bilingual vocabulary platform that eliminates deck-building overhead, provides diagnostic insights on retention failures, and maintains a self-growing corpus — if the first review session starts within 3 minutes of signup.

**Resource Requirements:** Solo mid-level full-stack developer, 14 weeks. Two-person team (backend + frontend) reduces to 8–10 weeks. Required skills: Python/FastAPI async, PostgreSQL, TypeScript/Next.js, LLM API integration.

## MVP Feature Set (Phase 1 — 14 Weeks)

**Core User Journeys Supported:** Journey 1 (Minh — primary success path), Journey 2 (Lan — import/error recovery), Journey 3 (Hùng — mobile commute learner, partial — mobile-responsive review).

**Must-Have Capabilities:**

| Capability | Description | Journey |
|-----------|-------------|---------|
| Authentication | Email/password + Google OAuth + LINE OAuth | 1, 2, 3 |
| Onboarding | 5-question survey → AI-generated learning plan → first review < 3 min | 1, 3 |
| FSRS Review Engine | py-fsrs integration, JSONB state storage, daily review queue with priority (overdue > due > new) | 1, 2, 3 |
| Bilingual Vocabulary Cards | Single-language default view + optional parallel mode toggle. Per-language retention tracking. | 1, 2, 3 |
| Structured Vocabulary Request | Form-based request (topic, level, count) → DB query → LLM fill gap → preview → confirm | 1 |
| Auto-enrichment Pipeline | LLM generates definitions, IPA, CEFR, examples. JMdict cross-validation for Japanese. Pydantic schema validation. | 1, 2, 3 |
| Database Waterfall | Enrichment results sync to central corpus. Deduplication and validation before merge. | 1, 2, 3 |
| CSV Import | Import with error handling, preview, partial import capability. UTF-8 BOM, TSV preferred. | 2 |
| Personal Collections | Create, organize, browse. Collection → SRS bridge controls (start learning, pause). | 1, 3 |
| Pre-seeded Corpus | 3,000–5,000 IT/TOEIC/JLPT N3–N2 terms via one-time LLM batch job, JMdict validated. | 3 |
| Learning Diagnostics (Basic) | Time-of-day retention effects, category-specific weakness detection, cross-language interference (parallel mode). | 1, 3 |
| Progress Dashboard | Retention curves, vocabulary growth, SRS health metrics, calendar views (daily/weekly). | 1, 3 |
| User Flag System | Flag incorrect definitions → temporarily hide → route to moderation queue. | 2 |
| Content Moderation Queue | Admin view of flagged content, approve/reject/fix workflow. | 4 |
| Admin Operations Dashboard | LLM cost tracking, enrichment queue status, cache hit rate, basic alerts. | 4 |
| Freemium Tier Gating | Free (50 active SRS cards, 5 enrichments/day) vs Student (unlimited). Rate limiting per tier. | All |
| Mobile-responsive UI | Card review, quick-add, dashboard summary functional on mobile viewport ≥375px. | 3 |

## Post-MVP Features

**Phase 2 — Fast-Follow (Weeks 15–18):**

| Feature | Rationale |
|---------|-----------|
| Chat-based vocabulary request | Natural language intent parser replaces structured form. Progressive clarification for ambiguous requests. |
| Browser extension (Plasmo + TypeScript) | Double-click word capture from web pages. Auth handshake with backend. Save-to-inbox flow. |
| Anki APKG import | genanki-based parser for standard and common custom note types. |
| Quizlet import (best-effort) | CSV-based import from Quizlet export. No API integration (Quizlet has no public export API). |
| Enhanced diagnostics | Richer pattern analysis, more recommendation types, weekly AI summary. |
| Advanced calendar views | Monthly and yearly views. GitHub-style contribution heatmap. |
| Shareable diagnostic reports | PDF export, embeddable progress widgets, tutor-facing views. |

**Phase 3 — Vision (6+ Months Post-MVP):**

| Feature | Gate Condition |
|---------|---------------|
| Four-skill modules (Listening, Speaking, Reading, Writing) | Vocabulary MAU ≥ 1,000 and D30 retention > 15% |
| Korean-English language corridor | EN-JP corpus exceeds 20,000 validated terms with ≥85% satisfaction |
| Knowledge graph visualization | Corpus reaches sufficient density for meaningful semantic connections |
| B2B/Corporate plans | Organic adoption at Vietnamese IT companies creates inbound demand |
| Marketplace for user-generated content packs | Active creator community emerges organically |
| Mobile native apps | Web PWA usage data justifies native investment |
| Multi-signal SRS adaptation | Sufficient cross-skill usage data accumulated (post 4-skill launch) |

## Risk Mitigation Strategy

**Technical Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM enrichment quality insufficient for Japanese | Users learn wrong kanji — trust destroyed | JMdict cross-check mandatory before display; user flag system; Sprint 5–6 quality spike to benchmark LLM providers on Vietnamese bilingual content |
| FSRS cold-start for imported cards | Poor review scheduling for first week | System recalibrates through initial reviews (3–5 days); warn users that scheduling improves after first week |
| Offline sync conflicts | Data loss or duplicate reviews | Last-write-wins with per-record updated_at timestamps; sufficient for single-user MVP |

**Market Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| EN-JP bilingual niche too small | Insufficient users to sustain business | Validate with 10–15 user interviews before launch; architecture supports Korean-English as second corridor |
| Users don't value diagnostics | Core differentiator fails | In-app survey at 2-week mark; if <50% find diagnostics valuable, pivot to corpus quality as primary value prop |
| Free tier too generous / too restrictive | Poor conversion or poor activation | Start with 50 cards / 5 enrichments free; A/B test limits in Month 2 based on conversion data |

**Resource Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Solo developer burnout over 14 weeks | Delayed or abandoned launch | Strict sprint boundaries; cut browser extension and APKG import to fast-follow (already done); stub LLM with fake provider for first 3 sprints |
| Fewer resources than planned | Cannot ship full MVP | Minimum viable cut: Auth + FSRS Engine + CSV Import + Basic Dashboard (no diagnostics, no auto-enrichment). Manual corpus seeding replaces Database Waterfall. ~8 weeks. |
