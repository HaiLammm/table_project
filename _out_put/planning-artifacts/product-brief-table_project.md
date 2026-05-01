---
title: "Product Brief: table_project"
status: "complete"
created: "2026-05-01"
updated: "2026-05-01"
inputs:
  - "_out_put/brainstorming/brainstorming-session-2026-04-29-2325.md"
  - "_out_put/planning-artifacts/research/technical-vocabulary-learning-system-research-2026-04-30.md"
---

# Product Brief: TableProject — Bilingual Vocabulary Mastery Platform

## Executive Summary

Vietnamese students and IT professionals studying both English and Japanese face a frustrating reality: no existing tool lets them learn vocabulary across both languages in a unified, intelligent system. They bounce between Anki (powerful but painful to set up) and Duolingo (easy but shallow), maintaining separate decks, separate apps, and separate mental models — with no way to see how they're actually progressing or where they're falling behind.

TableProject is a bilingual vocabulary learning platform built on the FSRS spaced repetition algorithm that lets users learn a single word with both its English and Japanese meanings — simultaneously or one at a time, as the learner chooses. At its core is the **Learning Diagnostics Engine**: an analytics layer that doesn't just track progress — it diagnoses *why* specific words aren't sticking and recommends targeted strategies to fix retention gaps. The system's self-growing vocabulary corpus (the "Database Waterfall") compounds with every user interaction, creating a defensible content asset that improves over time.

The timing is right: LLM costs have dropped ~80% since 2024 (making per-card AI-generated examples, mnemonics, and contextual notes cost fractions of a cent), the FSRS algorithm is mature and open-source, and Vietnam's growing economic ties with Japan (~450K Vietnamese workers/students in Japan) have created a large, underserved bilingual learner population with no purpose-built tool.

**The promise: from signup to your first bilingual flashcard review in under 3 minutes.** No deck building. No configuration. Just learning.

## The Problem

A Vietnamese IT professional preparing for both a TOEIC exam and JLPT N2 faces this daily routine: open Anki to review English flashcards they spent hours creating, switch to a separate Japanese deck with different formatting, then check Duolingo for gamified practice that teaches irrelevant vocabulary. Nowhere can they see that they consistently fail words related to networking terminology across *both* languages — or that their retention drops every Thursday because they skip evening reviews.

The core problems:
- **Fragmented tools**: No platform supports simultaneous EN-JP vocabulary learning. Users maintain parallel, disconnected systems.
- **Blind learning**: Existing apps show streaks and scores but never explain *why* certain words don't stick or *what to do about it*.
- **Setup tax**: Anki's power comes at the cost of hours of deck creation and maintenance — a barrier that eliminates most learners before they start.
- **Shallow alternatives**: Duolingo and similar apps optimize for engagement metrics, not actual vocabulary retention.

## The Solution

TableProject provides a unified vocabulary learning experience with three pillars:

**1. Bilingual Learning with Optional Parallel Mode**
Each vocabulary card defaults to a single language view (EN or JP based on the user's active study mode), keeping cognitive load focused. Users can toggle **parallel mode** to see both English and Japanese definitions side-by-side — useful for exploring cross-language connections or when studying a concept that spans both languages. A word like "network" maps to both its English technical meaning and the Japanese ネットワーク, with shared and language-specific usage patterns. The system tracks retention per language independently, revealing cross-language interference patterns when parallel mode is active.

**2. Learning Diagnostics Engine**
Beyond tracking what users have learned, the engine analyzes *why* they haven't learned what they should have. It captures signals per review — timestamp, response time, difficulty rating, card category, session length — and detects actionable patterns:

- *"Your retention for networking terms drops 35% when reviewed after 9pm → Try reviewing technical vocabulary in morning sessions"*
- *"You consistently rate database-related words as Hard within 2 reviews → These terms need spaced introduction mode with 3 initial exposures before entering SRS"*
- *"Your Japanese retention for IT terms is 60% vs 85% for English → The kanji readings may need additional visual mnemonics"*

This is a personal learning strategist, not a progress bar.

**3. Self-Growing Vocabulary Engine (Database Waterfall)**
When a user encounters a word not in the system, an LLM enrichment pipeline generates definitions, examples, IPA, CEFR level, and related terms — cross-checked against JMdict (~170K entries) for Japanese accuracy before being shown to users. The enrichment syncs back to the central corpus. Every user interaction makes the system smarter for everyone. After 6-12 months of active use, this collective bilingual corpus — tuned to Vietnamese speakers' specific learning patterns — becomes a defensible asset no competitor can quickly replicate.

**Day 1 Content**: The platform launches pre-seeded with 3,000-5,000 high-value EN-JP vocabulary terms covering IT/TOEIC/JLPT N3-N2, generated via LLM batch processing and cross-validated against JMdict, ensuring new users never face an empty database.

## What Makes This Different

| Dimension | Anki | Duolingo | TableProject |
|-----------|------|----------|-------------|
| SRS Algorithm | FSRS (user-configured) | Hidden, non-customizable | FSRS at MVP; multi-signal adaptation in Phase 2 |
| Bilingual EN-JP | Manual separate decks | Separate courses | Single-language default + optional parallel mode |
| Analytics | Basic stats | Streaks & XP | Learning Diagnostics Engine: "why" + recommendations |
| Setup effort | Hours of deck building | Zero (but shallow) | Zero setup, pre-seeded deep content |
| Content growth | User-created only | Platform-curated | Self-growing via Database Waterfall |
| Cost per card | Free (user labor) | N/A (no cards) | Fractions of a cent (LLM-generated, cached) |

The real moat is not any single feature — it's the combination of the self-growing corpus (a collective data flywheel where thousands of Vietnamese learners surface and validate EN-JP word pairs), the Learning Diagnostics Engine (correlating forgetting patterns with learner behavior to prescribe interventions), and the bilingual learning model. FSRS is open-source and available to anyone; the intelligence and data layers on top are not.

## Who This Serves

**Primary Persona — "The Vietnamese IT Bilingual Learner"**
Vietnamese IT students and professionals who need domain-specific vocabulary across both English and Japanese. Two key sub-segments:

- **In Vietnam**: University students or early-career developers studying both languages for career advancement — preparing for TOEIC and JLPT simultaneously. They learn at home on desktop, are price-sensitive, and value efficiency over gamification.
- **In Japan**: Vietnamese workers/engineers already in Japan, maintaining English for global tech work while improving Japanese for workplace survival. They learn during commutes (mobile web), need practical vocabulary (code reviews, standups, daily conversation), and have higher willingness to pay.

The MVP prioritizes the first sub-segment (Vietnam-based learners on desktop) as the initial build target.

**Secondary: Vietnamese professionals preparing for language certifications**
TOEIC, IELTS, JLPT test-takers who need structured vocabulary building with clear progress visibility and weakness identification.

## Business Model

**Freemium from Day 1:**
- **Free tier**: 50 active SRS cards, 5 LLM enrichments/day, basic progress tracking
- **Student tier** (~99K-119K VND/month, ~$4-5): Unlimited cards, full diagnostics, import/export, browser extension
- **Professional tier** (~199K-249K VND/month, ~$8-10): Priority LLM enrichment, advanced analytics, API access

**Unit economics**: LLM cost per power user (50 enrichments/day) = ~$0.05-0.15/month with prompt caching + Batch API. Infrastructure: $15-50/month for 100 active users. Break-even estimated at ~200-300 paid users on Student tier.

## Success Criteria

- **Retention effectiveness**: ≥90% vocabulary retention at 14-day recall, ≥85% at 30-day recall (FSRS benchmark: ~91% at 14 days with default parameters; measured for users completing ≥80% of scheduled reviews)
- **Activation**: Time-to-first-review-session < 5 minutes; users completing 3+ review sessions in first 7 days ≥ 40%
- **Engagement**: Median 25+ cards added/week, 10+ reviews/day among active users
- **Product retention**: D7 ≥ 30%, D30 ≥ 15%
- **Diagnostic value**: ≥70% of users report the dashboard helped them identify a weakness they didn't know about (in-app survey after 2 weeks)
- **Corpus growth**: Auto-enrichment satisfaction ≥85%; cache hit rate >70% after 4 weeks of operation

## Scope

**MVP (14 weeks):**
- Authentication and user onboarding
- Core SRS engine with FSRS algorithm (py-fsrs)
- Bilingual EN-JP vocabulary cards with parallel definitions
- Personal collections and vocabulary organization
- Import from CSV (Anki APKG and Quizlet import deferred to fast-follow)
- Progress dashboard with basic diagnostics (pattern detection ships incrementally as user data accumulates)
- Pre-seeded corpus: 3,000-5,000 IT/TOEIC/JLPT terms

**Fast-follow (weeks 15-18):**
- Browser extension for word capture
- Anki APKG and Quizlet import
- Enhanced diagnostic recommendations

**Explicitly NOT in MVP:**
- Listening, speaking, reading, and writing skill modules (Phase 2+)
- Marketplace for user-generated content packs
- Corporate/B2B features
- Mobile native apps (web-first, responsive)
- Community features (forums, exchanges)
- Multi-signal SRS adaptation (Phase 2)

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM-generated content errors (especially Japanese kanji/context) | High | Cross-check all JP content against JMdict before display; user reporting system for errors; human review queue for flagged items |
| Cold-start dashboard — new users see empty analytics for first 2 weeks | High | Show estimated learning curves from Day 1 based on FSRS parameters; surface first diagnostic insights after just 3 days of data; set expectations in onboarding |
| Market size uncertainty — EN-JP bilingual niche may be small | Medium | Validate with 10-15 user interviews before launch; architecture supports adding Korean-English as second corridor (comparable Vietnam-Korea migration scale) |
| Competitive response — Anki community ships bilingual plugin | Medium | Database Waterfall corpus + diagnostic engine create switching costs that a plugin cannot replicate; focus on UX gap Anki cannot close |
| JMdict CC BY-SA 3.0 licensing for cross-check data | Low | Use JMdict for validation only (not as corpus source); attribute properly; keep generated corpus as original work |

## Go-to-Market

**First 100 users strategy:**
1. Seed communities: Vietnamese-in-Japan Facebook groups, JLPT prep Zalo communities, Vietnamese IT Discord/Telegram channels
2. Beta program: 50 early users with direct feedback loop; iterate on diagnostic features with real data
3. Content marketing: Vietnamese-language blog posts on SRS techniques, JLPT study strategies (SEO for this niche is thin = opportunity)
4. Partnership outreach: Japanese language schools in Vietnam (Đông Du, Sakura) and IT recruitment agencies (FPT Japan, Sun Asterisk, Rikkeisoft) as distribution channels

**Shareable diagnostic reports** — every weakness analysis a user exports is a product demo to their study group, tutor, or employer.

## Vision

TableProject starts as the best way to build vocabulary across English and Japanese. As the corpus matures and user data accumulates, it expands into a full four-skill language learning platform — Listening, Speaking, Reading, Writing — powered by the same Learning Diagnostics Engine.

**Phase gates for expansion:**
- **4-skill modules**: When vocabulary MAU reaches 1,000+ and D30 retention exceeds 15%
- **New language pairs** (e.g., Vietnamese-Korean): When EN-JP corpus exceeds 20,000 validated terms with ≥85% user satisfaction
- **B2B/Corporate**: When organic adoption at Vietnamese IT companies creates inbound demand

In 2-3 years, TableProject becomes the go-to platform for Vietnamese multilingual learners — not by competing with Duolingo on breadth, but by winning on depth, intelligence, and genuine learning outcomes. The self-growing database, tuned to Vietnamese speakers' cognitive patterns, becomes a unique bilingual dataset that powers increasingly personalized learning paths.
