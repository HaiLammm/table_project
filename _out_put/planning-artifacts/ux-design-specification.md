---
stepsCompleted:
  - "step-01-init"
  - "step-02-discovery"
inputDocuments:
  - "prd.md"
  - "product-brief-table_project.md"
  - "product-brief-table_project-distillate.md"
  - "research/technical-vocabulary-learning-system-research-2026-04-30.md"
documentCounts:
  prd: 1
  briefs: 2
  research: 1
  projectDocs: 0
workflowType: 'ux-design'
classification:
  projectType: "web_app"
  domain: "data-driven edtech platform"
  complexity: "medium-high"
  projectContext: "greenfield"
---

# UX Design Specification table_project

**Author:** Lem
**Date:** 2026-05-02

---

## Executive Summary

### Project Vision

TableProject is a bilingual vocabulary mastery platform purpose-built for Vietnamese IT professionals and students acquiring English and Japanese technical vocabulary simultaneously. The platform differentiates through three pillars: (1) FSRS-powered spaced repetition with zero setup overhead, (2) a Learning Diagnostics Engine that diagnoses *why* specific words fail to stick and prescribes targeted interventions, and (3) a self-growing vocabulary corpus (Database Waterfall) that compounds with every user interaction.

The UX must embody the product's core philosophy: **serious learning, not gamification theater**. Every interaction should feel purposeful, efficient, and intelligence-driven. The platform targets desktop-first web usage (Next.js 16 PWA) with a path to mobile web optimization post-MVP.

Key UX promise: **From signup to first bilingual flashcard review in under 3 minutes.**

### Target Users

**Primary — Vietnamese IT Bilingual Learner (MVP focus)**

- **In Vietnam:** University students and early-career developers preparing for TOEIC and JLPT N2 simultaneously. They study at home on desktop, are price-sensitive, value efficiency over gamification, and need IT-specific vocabulary (code reviews, documentation, standups). These users are the MVP build target.
- **In Japan:** Vietnamese workers/engineers maintaining English for global tech work while improving Japanese for workplace survival. They learn during commutes (mobile web), need practical daily vocabulary, and have higher willingness to pay.

**Secondary**

- **JLPT/TOEIC test-takers:** Focused exam prep with structured vocabulary by JLPT level (N5–N1) or TOEIC score band. Need clear progress metrics toward exam readiness.
- **"Anki refugees":** Power users frustrated by Anki's deck-building overhead who want equivalent SRS effectiveness without the setup tax. Likely to import existing Anki decks via CSV/APKG.

**User Tech Savviness:** Intermediate to high — IT professionals and CS students comfortable with web applications. Not intimidated by data-rich dashboards but impatient with unnecessary complexity.

**Primary Device:** Desktop (laptop/monitor) for focused study sessions. Mobile web as secondary for quick reviews during commute.

### Key Design Challenges

1. **Bilingual Cognitive Load Management** — Presenting English and Japanese vocabulary simultaneously risks cognitive overload. The design must implement a clean single-language default view with an intuitive parallel mode toggle, making the transition between modes feel natural rather than mode-switching friction. The UX must clearly communicate when parallel mode adds value versus when single-language focus is optimal.

2. **Diagnostics as Personal Tutor, Not Data Dump** — The Learning Diagnostics Engine is the product's "aha moment" (target: 70% of 2-week users discover a previously unknown weakness). The dashboard must translate raw analytics into actionable, conversational insights — e.g., "Your networking terms drop 35% after 9pm — try morning sessions" — not scatter plots and percentages. The challenge is making intelligence feel human and immediately actionable.

3. **Zero-Friction Onboarding Flow** — The 5-question survey → AI-generated learning plan → first review path must complete in under 3 minutes. Every extra screen, loading state, or decision point risks abandonment. The UX must minimize cognitive decisions during onboarding while still gathering enough information to personalize the experience meaningfully.

4. **Cold-Start Dashboard Experience** — New users face an empty analytics dashboard for the first 1–2 weeks. The UX must design a compelling "day 1 through day 14" progressive reveal: estimated learning curves from FSRS parameters on Day 1, first pattern insights after 3 days of data, and full diagnostics by Week 2. Empty states must feel like anticipation, not absence.

5. **SRS Review Efficiency and "Chore Fatigue"** — Target users will complete 10+ reviews daily. The review flow must be optimized for speed (minimal clicks/taps per card), clear feedback loops, and session-level progress indicators that prevent the "endless grind" feeling. Keyboard shortcuts are essential for desktop power users.

### Design Opportunities

1. **"Amazon Review Dashboard" Concept** — A breakthrough UX pattern from brainstorming: weekly strategy sessions presented as star-rating breakdowns with recommendations and Q&A format. This transforms the typical learning dashboard from passive display into an active coaching conversation, creating a unique competitive advantage no vocabulary app currently offers.

2. **Shareable Diagnostic Reports as Growth Engine** — Every weakness analysis exported or shared becomes a product demo in Vietnamese study groups, Zalo communities, and tutor relationships. The UX for sharing must be frictionless and visually compelling — designed to spark curiosity in viewers who are not yet users.

3. **Progressive Disclosure of Intelligence** — Start simple (learn + review), then gradually surface Diagnostics Engine insights as user data accumulates. This creates a natural "aha moment" trajectory: Day 1 = clean SRS, Day 3 = first pattern hint, Week 2 = full diagnostic profile. The product gets smarter visibly, rewarding continued use.

4. **Single-Language to Parallel Mode Micro-Interactions** — The transition between single-language and parallel bilingual view is an opportunity for delightful micro-interactions that make cross-language exploration feel like discovery rather than mode-switching. Well-designed transitions here reinforce the product's unique bilingual value proposition.
