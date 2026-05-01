---
stepsCompleted:
  - "step-01-init"
  - "step-02-discovery"
  - "step-02b-vision"
  - "step-02c-executive-summary"
  - "step-03-success"
inputDocuments:
  - "product-brief-table_project.md"
  - "product-brief-table_project-distillate.md"
  - "research/technical-vocabulary-learning-system-research-2026-04-30.md"
  - "../brainstorming/brainstorming-session-2026-04-29-2325.md"
documentCounts:
  briefs: 2
  research: 1
  brainstorming: 1
  projectDocs: 0
workflowType: 'prd'
classification:
  projectType: "web_app"
  domain: "data-driven edtech platform"
  complexity: "medium-high"
  projectContext: "greenfield"
---

# Product Requirements Document - table_project

**Author:** Lem
**Date:** 2026-05-01

## Executive Summary

TableProject is a bilingual vocabulary mastery platform purpose-built for Vietnamese IT professionals and students who need to acquire English and Japanese technical vocabulary simultaneously. Unlike Duolingo — which gamifies at the expense of depth — and Anki — which demands hours of manual deck creation — TableProject delivers serious, accurate, no-nonsense vocabulary learning powered by the FSRS spaced repetition algorithm with zero setup overhead.

The platform solves a concrete gap: no existing tool supports unified EN-JP vocabulary learning for Vietnamese speakers. Users currently maintain separate apps, separate decks, and separate mental models — with no visibility into *why* specific words fail to stick. TableProject eliminates this fragmentation by treating each vocabulary term as a bilingual object with independent per-language retention tracking, and layering a Learning Diagnostics Engine that identifies forgetting patterns, correlates them with learner behavior (time-of-day, category, session length), and prescribes targeted interventions.

The system's self-growing vocabulary corpus — the Database Waterfall — transforms every user interaction into a shared data asset. When a user encounters an unknown term, an LLM enrichment pipeline generates definitions, IPA, CEFR level, and contextual examples, cross-validated against JMdict for Japanese accuracy before display. This corpus compounds over time, creating a defensible bilingual dataset tuned to Vietnamese speakers' learning patterns that no competitor can quickly replicate.

The MVP targets Vietnam-based desktop learners (university students and early-career IT developers) preparing for TOEIC and JLPT examinations, with a pre-seeded corpus of 3,000–5,000 high-value IT/TOEIC/JLPT N3–N2 terms. Time-to-first-review: under 3 minutes from signup.

### What Makes This Special

**1. Serious learning, not gamification theater.** Every feature serves retention and mastery. FSRS ensures scientifically-optimal review scheduling. No XP, no hearts, no leagues — just measurable vocabulary growth.

**2. Diagnostic intelligence, not progress bars.** The Learning Diagnostics Engine doesn't just track *what* you've learned — it diagnoses *why* specific words aren't sticking and recommends concrete fixes: "Your networking terms drop 35% after 9pm → review technical vocabulary in morning sessions."

**3. Self-growing corpus as strategic moat.** The Database Waterfall creates a collective data flywheel: every enrichment request strengthens the central corpus. After 6–12 months of active use, this bilingual dataset — validated against JMdict, tuned to Vietnamese learners — becomes a unique asset that positions TableProject not merely as an edtech app, but as a niche language intelligence platform.

**4. Zero-friction bilingual architecture.** Single-language view by default (low cognitive load), with optional parallel mode for cross-language exploration. One word, two languages, tracked independently — no separate decks, no context switching.

## Project Classification

- **Project Type:** Web Application (SPA/PWA) — Next.js 16 App Router frontend + FastAPI Python backend
- **Domain:** Data-Driven EdTech Platform — vocabulary learning with LLM-powered content generation and self-growing data flywheel
- **Complexity:** Medium-High — 8 bounded contexts, LLM multi-provider gateway, offline-first sync, browser extension, FSRS algorithm integration, bilingual dictionary validation
- **Project Context:** Greenfield — new product, no existing codebase
- **Architecture:** Modular Monolith with Hexagonal (Ports & Adapters) pattern
- **Business Model:** Freemium — Free tier (50 active SRS cards) / Student (~$4–5/mo) / Professional (~$8–10/mo)

## Success Criteria

### User Success

- **Vocabulary retention effectiveness:** ≥90% recall accuracy at 14-day intervals; ≥85% at 30-day intervals (for users completing ≥80% of scheduled reviews). FSRS benchmark: ~91% at 14 days with default parameters.
- **Zero-friction activation:** Time from signup to first review session < 3 minutes. No deck building, no configuration required.
- **Early engagement hook:** ≥40% of new users complete 3+ review sessions within their first 7 days.
- **Diagnostic "aha" moment:** ≥70% of users who reach 2 weeks of activity report that the dashboard helped them identify a vocabulary weakness they didn't previously recognize. This is the core value-proving moment.
- **Sustained learning behavior:** Median 25+ cards added per week; 10+ reviews completed per day among active users.

### Business Success

- **Month 1 acquisition target:** 10,000 registered users through community seeding (Vietnamese-in-Japan Facebook groups, JLPT prep Zalo communities, Vietnamese IT Discord/Telegram channels) and content marketing.
- **Product retention:** D7 ≥ 30%, D30 ≥ 15%.
- **Conversion to paid:** ≥5% free-to-Student tier conversion within 30 days of signup (target: 500 paid users from initial 10,000).
- **Revenue sustainability:** Break-even at ~200–300 paid users on Student tier (~$4–5/mo). Target: achieve break-even by Month 3.

### Technical Success

- **API performance:** p95 latency < 200ms for non-LLM endpoints.
- **LLM responsiveness:** p95 latency < 3s for enrichment; time-to-first-token < 800ms for streaming responses.
- **Cost discipline:** Daily LLM cost per active user < $0.02. Total MVP infrastructure ≤ $50/month for first 100 active users.
- **Corpus quality:** Auto-enrichment user satisfaction ("looks good" rate) ≥ 85%. All Japanese definitions cross-validated against JMdict before display.
- **Cache efficiency:** LLM enrichment cache hit rate > 70% after 4 weeks of operation.
- **Code quality:** Domain layer test coverage ≥ 90%; application layer ≥ 70%. Sentry error rate < 0.5% of requests.

### Measurable Outcomes

| Metric | Target | Measurement Method | Timeframe |
|--------|--------|--------------------|-----------|
| Registered users | 10,000 | Analytics | Month 1 |
| D7 retention | ≥ 30% | Cohort analysis | Ongoing |
| D30 retention | ≥ 15% | Cohort analysis | Ongoing |
| Free → Paid conversion | ≥ 5% | Billing system | Month 1–3 |
| 14-day vocabulary recall | ≥ 90% | FSRS review data | Ongoing |
| Time-to-first-review | < 3 min | Onboarding analytics | Ongoing |
| Dashboard diagnostic value | ≥ 70% approval | In-app survey (2-week mark) | Month 2+ |
| LLM cost/active user/day | < $0.02 | Cost tracking dashboard | Ongoing |

## Product Scope

### MVP — Minimum Viable Product (14 weeks)

- Authentication: Email/password + Google OAuth via Clerk or Supabase Auth
- User onboarding: 5-question survey → AI-generated learning plan → first review in < 3 minutes
- Core SRS engine: FSRS algorithm via py-fsrs, JSONB state storage, daily review queue
- Bilingual EN-JP vocabulary cards: Single-language default view + optional parallel mode toggle
- Learning Diagnostics Engine: Basic pattern detection (time-of-day retention effects, category-specific weakness, cross-language interference)
- Database Waterfall: LLM auto-enrichment pipeline with JMdict cross-validation, central corpus sync
- Personal collections: Create, organize, import from CSV
- Progress dashboard: Retention curves, vocabulary growth, SRS health metrics, calendar views (daily/weekly)
- Pre-seeded corpus: 3,000–5,000 IT/TOEIC/JLPT N3–N2 terms

### Growth Features (Post-MVP, Weeks 15–18)

- Browser extension for web vocabulary capture (Plasmo + TypeScript)
- Anki APKG and Quizlet import
- Enhanced diagnostic recommendations with richer pattern analysis
- Advanced calendar views (monthly/yearly)
- Shareable diagnostic reports (PDF export, embeddable progress widgets)

### Vision (Future)

- Four-skill expansion: Listening, Speaking, Reading, Writing modules
- Korean-English as second language corridor (Vietnam-Korea migration market)
- Knowledge graph visualization of vocabulary interconnections
- B2B/Corporate plans with admin dashboards and custom content
- Marketplace for user-generated content packs
- Mobile native apps
- Multi-signal SRS adaptation (response speed, cross-skill usage patterns)

