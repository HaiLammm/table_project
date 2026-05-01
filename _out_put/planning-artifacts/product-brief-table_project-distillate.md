---
title: "Product Brief Distillate: table_project"
type: llm-distillate
source: "product-brief-table_project.md"
created: "2026-05-01"
purpose: "Token-efficient context for downstream PRD creation"
---

# Product Brief Distillate: TableProject

## Rejected Ideas (do not re-propose)

- **Dual Language Listening Bridge** (#59) — listen to same content EN+JP and summarize cross-language. Rejected: too complex for MVP, deferred post-MVP
- **GraphQL for dashboard queries** — adds complexity not justified at MVP; REST is sufficient; revisit only if dashboard query patterns demand it
- **Microservices architecture** — rejected for MVP; modular monolith chosen; single team + 14-week timeline makes microservices overhead unjustified; extraction points preserved for future
- **Building auth from scratch** — rejected; use Clerk or Supabase Auth; OAuth 2.0 + JWT with short-lived access tokens (15 min) + refresh rotation
- **Gamification/league system** — not a differentiator; Duolingo owns this; TableProject wins on depth + intelligence, not engagement tricks
- **Mobile native apps for MVP** — web-first responsive; native apps deferred to post-validation
- **Community features (forums, exchanges)** — deferred; not core to vocabulary learning value prop

## Requirements Hints

- **Card display**: Default single-language view (EN or JP based on study mode); user toggles parallel mode for side-by-side bilingual display
- **SRS engine**: FSRS via py-fsrs library; store FSRS state as JSONB to allow algorithm evolution without schema migrations; MVP ships standard FSRS, multi-signal adaptation (response speed, cross-skill usage) is Phase 2
- **Auto-enrichment output schema**: `{term, ipa, definition_vi, definition_en, examples[], cefr_level, related_terms[]}` — Pydantic validates same schema as request validator + LLM tool schema + domain DTO (triple use)
- **JMdict cross-check**: All LLM-generated Japanese definitions must be validated against JMdict (~170K entries) before display; hallucinated definitions are a trust-killer
- **Pre-seeded corpus**: 3,000-5,000 EN-JP vocabulary terms for IT/TOEIC/JLPT N3-N2 via one-time LLM batch job cross-validated against JMdict — must be ready before launch
- **Hierarchical vocabulary**: Tree format (IT → Networking → Router/Switch/Protocol); adjacency list (parent_id) for MVP, ltree denormalized index later; recursive CTEs fast at 3-5 level depth
- **Import**: CSV import in MVP; Anki APKG and Quizlet import in fast-follow (weeks 15-18)
- **Browser extension**: Deferred to fast-follow (weeks 15-18); Plasmo + TypeScript + React; word capture from web pages
- **Dashboard sub-dashboards**: Main Command Center + 5 sub-dashboards (Speaking, Listening, Reading, Writing, SRS/Vocabulary) + Calendar views (Daily/Weekly/Monthly/Yearly) — full scope is post-MVP; MVP ships progress tracking with basic pattern detection
- **Diagnostic signals captured per review**: timestamp, response time, difficulty rating, card category, session length
- **Diagnostic patterns to detect at MVP**: time-of-day retention effects, category-specific weakness, cross-language interference (when parallel mode active)
- **Freemium from Day 1**: Free tier (50 active SRS cards, 5 LLM enrichments/day, basic progress); Student ~99-119K VND/mo; Professional ~199-249K VND/mo
- **Onboarding**: 5-question survey → AI-generated learning plan; time-to-first-review-session < 5 minutes
- **User retention targets**: D7 ≥ 30%, D30 ≥ 15%; median 25+ cards added/week; 10+ reviews/day

## Technical Context

- **Backend**: FastAPI (Python 3.12) — fixed constraint; SQLAlchemy 2.0 async + Alembic + Pydantic v2 + py-fsrs + jamdict + ARQ + Redis + PostgreSQL 16
- **Frontend**: TypeScript + Next.js 16 (App Router) + TanStack Query + shadcn/ui + Tailwind
- **Architecture**: Modular Monolith with Hexagonal (Ports & Adapters) pattern; 8 bounded contexts: auth, vocabulary, srs, collections, enrichment, intent, dictionary, dashboard
- **LLM integration**: Internal gateway wrapping all providers (Claude Haiku / Gemini Flash / DeepSeek) from Day 1; prompt caching (90% off reads) + Batch API (50% off) for 70-90% cost reduction
- **LLM pricing snapshot (April 2026)**: Claude Haiku $0.25/$1.25 per M tokens, Gemini 2.0 Flash $0.10/$0.40, DeepSeek V3.2 $0.14 input — prices fell ~80% from 2024 to 2026
- **Per-user LLM cost**: Power user (50 enrichments/day) = ~$0.05-0.15/month with caching + Batch
- **Database**: PostgreSQL with adjacency list; FSRS state as JSONB; IndexedDB for offline-first client
- **Core schema tables**: users, vocabulary_terms (parent_id + ltree_path), vocabulary_definitions (definition_vi, definition_en, examples_jsonb, cefr_level), collections, collection_terms, srs_cards (fsrs_state_jsonb, due_at), srs_reviews, enrichment_jobs
- **Hosting**: Fly.io or Cloud Run (backend) + Vercel (frontend) + Neon or Supabase (Postgres) + Upstash (Redis); total MVP infra $15-50/month for 100 active users
- **Auth**: Clerk or Supabase Auth; OAuth 2.0 + JWT
- **Technical KPIs**: API p95 < 200ms, LLM p95 < 3s (TTFT < 800ms), daily LLM cost/user < $0.02, domain test coverage ≥ 90%, cache hit rate > 70% after 4 weeks, auto-enrichment satisfaction ≥ 85%
- **MVP timeline**: 14 weeks (~3.5 months) for solo mid-level dev; 8-10 weeks for 2-person team

## Detailed User Scenarios

- **Vietnamese IT dev in Vietnam** preparing for TOEIC + JLPT N2: studies at home on desktop, price-sensitive (student tier), needs IT-specific vocabulary (code reviews, documentation, standups), learns both EN + JP for career advancement
- **Vietnamese engineer in Japan**: maintains English for global tech work, improves Japanese for workplace survival, learns during commutes (mobile web), higher willingness to pay, needs practical vocabulary for daily work interactions
- **JLPT/TOEIC test-taker**: Focused exam prep, needs structured vocabulary by JLPT level (N5-N1) or TOEIC score band, wants clear progress metrics toward exam readiness
- **The "Anki refugee"**: Power user frustrated by setup tax, wants Anki's SRS effectiveness without the deck-building overhead; likely to import existing Anki decks via CSV/APKG

## Competitive Intelligence

- **Anki**: Open-source, FSRS since v23.10, most powerful/customizable. Gaps: steep learning curve, no built-in bilingual support, no analytics dashboard, intimidating UI. Free desktop, $24.99 iOS. Community plugins could add bilingual features but cannot replicate diagnostic engine or self-growing corpus
- **Duolingo**: 40+ languages, ~22% adoption in Vietnam, gamified. Gaps: aggressive monetization (hearts system), irrelevant vocabulary, no bilingual learning, weak grammar, no meaningful analytics. Users report "forced translation" approach
- **Migaku**: Immersion-based, integrated with Netflix/YouTube. Gaps: not for beginners, no bilingual EN-JP, no Vietnamese learner support
- **Taalhammer**: AI-powered SRS, full-sentence recall. Gaps: no Japanese support, no bilingual pairing, no analytics dashboard
- **Beelinguapp**: Side-by-side bilingual text reading. Gaps: passive learning only, no SRS, no vocabulary drilling
- **Key insight**: Users bounce between Duolingo (easy but shallow) and Anki (powerful but painful) — demand exists for middle ground that is both effective and accessible
- **FSRS benchmark**: Outperforms SM-2 for 99.6% of users, reduces reviews by 20-30%. Open-source = not a moat by itself
- **Market size**: Global language learning $101.5B (2026) → $649B (2035) at 22.9% CAGR; online/app segment $24.39B (2026); Asia-Pacific 45.75% of revenue; mobile 62% of online segment

## Breakthrough Concepts from Brainstorming

- **Database Waterfall** (#9): Local DB → LLM API fill gap → CronBot sync central DB. Primary technical moat; corpus compounds with usage; defensible after 6-12 months
- **Amazon Review Dashboard** (#113): Weekly strategy session with star-rating breakdown, recommendations, Q&A format — breakthrough UX concept for learning analytics
- **Unified Vocabulary Pipeline** (#125): Single pipeline for all vocabulary entry points (manual, import, browser extension, LLM enrichment)
- **Knowledge Graph** (#164): Vocabulary interconnections visualized as a graph; shows related terms, semantic clusters, learning pathways
- **Skill Radar Chart**: 6 axes (Speaking/Listening/Reading/Writing/Vocabulary/Grammar) with month-over-month overlay for weakness identification

## Strategic Opportunities (from reviewers, not yet committed)

- **IT-domain vocabulary as wedge**: Curated IT corpus from real GitHub issues, Jira tickets, tech docs — immediately high-value for highest-LTV segment
- **Shareable diagnostic reports**: Export PDF weakness reports, embeddable progress widgets, tutor-facing views — every shared report is a product demo
- **Database Waterfall as data flywheel**: Collective corpus becomes unique bilingual dataset; could power Vietnamese-speaker-specific FSRS scheduling parameters and difficulty ratings
- **Korean-English as second corridor**: Vietnam-Korea migration (~200K Vietnamese in South Korea) — same architecture, minimal changes, doubles TAM
- **Partnership channels**: Japanese language schools (Đông Du, Sakura), IT recruitment agencies (FPT Japan, Sun Asterisk, Rikkeisoft), FSRS open-source community
- **Vocabulary challenges**: User-created themed word collections (e.g., "N3 Kanji for software engineers") — user-generated growth + social proof in Facebook/Zalo groups
- **Position as "vocabulary OS for Vietnamese going global"** rather than "a better flashcard app" — elevates product category, justifies premium pricing

## Open Questions

- **Cognitive interference**: Single-language default with parallel toggle was chosen, but no user research validates whether parallel mode helps or hinders retention — needs A/B testing post-launch
- **Vietnamese LLM quality**: Auto-enrichment satisfaction target (85%) set without benchmarking LLM output quality for Vietnamese bilingual content — spike needed during development
- **TAM/SAM/SOM**: No formal market sizing done; 450K Vietnamese in Japan is total population, not segmented by IT/bilingual study behavior — user interviews recommended before launch
- **Cache hit rate assumption**: 70% after 4 weeks assumes significant vocabulary overlap across users; if interests are diverse (IT vs medical vs travel), overlap may be lower
- **Monetization in VN market**: Student tier at 99-119K VND/month is reasonable but untested; may need annual discount or institutional licensing for adoption

## MVP Feature Priority (from brainstorming IDs)

- **Must-haves (Phase 1)**: Authentication (#186-192) + Main Dashboard (#94-97) + Calendar (#103-106) + Core Learning Engine (#1-13, #125, #128, #152, #168, #172, #177, #182) + Personal Collections (#126-134)
- **Growth features**: Referral program (7 days Premium free), Year-in-Review viral sharing (Spotify Wrapped style), onboarding personalization (5-question survey → AI plan)
- **Pricing tiers brainstormed**: Free (SRS 50 words, basic skills) + Student $4.99/mo + Professional $9.99/mo + annual discount; B2B Corporate $6/user/mo
- **Marketplace idea**: User-generated content packs with 70/30 revenue split — deferred post-MVP
