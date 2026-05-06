# User Journeys

## Journey 1: Minh — Vietnamese IT Dev in Vietnam (Primary Success Path)

**Persona:** Minh, 24, junior developer at FPT Software Da Nang. Studies both English (for code reviews and documentation) and Japanese (JLPT N2 goal within 6 months) after his team is assigned to collaborate with a Japanese partner company.

**Opening Scene:** Every evening Minh opens Anki to review two separate decks — English IT terms and Japanese JLPT N3. He spends 45 minutes per week just creating new cards from work documentation. His manager just announced the team will collaborate with a Japanese partner — Minh needs to reach JLPT N2 in 6 months while maintaining English for daily code reviews.

**Rising Action:** Minh discovers TableProject through a post in the "Vietnamese Developers Japan" Facebook group. Signs up with Google OAuth (or LINE OAuth for users in Japan) → completes a 5-question survey (current level, goal, IT domain, daily study time, language priority) → the system generates an AI learning plan automatically. In under 3 minutes, Minh is reviewing his first card — "deployment" with both its English meaning and Japanese equivalent (デプロイメント). He selects single-language mode (Japanese first, since it's weaker).

In his first week, Minh adds 30 networking terms via the structured vocabulary request form (topic: networking, level: medium, count: 30) → system queries the DB, LLM fills gaps → preview → confirm. No manual card creation needed. He also imports 200 terms from his old Anki deck via CSV.

**Climax:** After two weeks, the dashboard surfaces its first diagnostic insight: *"Your retention for database terms drops 40% when reviewed after 9pm → Try reviewing technical vocabulary in morning sessions."* Minh shifts his review schedule — retention improves noticeably. This is the moment he realizes TableProject isn't just a flashcard app — it's a **learning strategist**.

**Resolution:** By month 3, Minh has mastered 800+ bilingual IT terms. In his first meeting with the Japanese team, he understands 70% of the technical discussion without a translator. He upgrades to the Student tier because the value is undeniable.

**Requirements Revealed:** Onboarding flow, Google OAuth, survey → AI plan generation, structured vocabulary request (form-based), CSV import, FSRS review engine, single/parallel language toggle, Learning Diagnostics Engine with time-of-day pattern detection.

---

## Journey 2: Lan — The "Anki Refugee" (Primary Edge Case / Error Recovery)

**Persona:** Lan, 28, QA engineer at Rikkeisoft. She has 3,000+ Anki cards reviewed over 2 years, but her deck structure is chaotic — inconsistent tags, messy formatting — and she's exhausted from weekly card maintenance. She wants to migrate but fears losing her progress.

**Opening Scene:** Lan's Anki decks are a mess: HTML tags in definitions, multiple meanings crammed into single fields, inconsistent tag hierarchies. She spends 2+ hours per week on deck maintenance instead of actual learning. She wants out but is terrified of losing 2 years of SRS progress.

**Rising Action:** Lan signs up and attempts to import her CSV export from Anki (2,800 terms). The import parser encounters issues: 150 cards have non-standard formatting (embedded HTML, merged definitions). The system displays a clear preview with warnings: "2,650 cards parsed OK ✓ | 150 cards need review — non-standard format detected." Lan imports the 2,650 clean cards immediately and places the 150 problematic cards in a "Review Later" queue.

She tries parallel mode for the first time — seeing "inheritance" with both its OOP meaning (English) and 継承 (Japanese) side-by-side. She discovers cross-language connections she never noticed when using separate decks.

**Climax:** Auto-enrichment runs on the 150 problematic cards — the LLM re-parses and generates proper definitions. However, 12 Japanese cards receive hallucinated definitions (kanji used in wrong context). Lan flags these cards → the system acknowledges the reports, routes them to a moderation queue, and temporarily hides the Japanese definitions until they are re-validated against JMdict.

**Resolution:** Within one week, all 2,800 cards are clean, enriched, and automatically organized into the hierarchical vocabulary tree. FSRS state from Anki doesn't migrate directly, but the system recalibrates through 3–5 days of review. Lan saves 2+ hours per week compared to Anki maintenance.

**Requirements Revealed:** CSV import with error handling and preview, partial import capability, auto-enrichment batch processing, JMdict cross-validation, user flag/report system for incorrect definitions, content moderation queue, hierarchical auto-categorization, FSRS cold-start calibration.

---

## Journey 3: Hùng — Vietnamese Engineer in Japan (Primary Alternative Context)

**Persona:** Hùng, 31, backend engineer working in Tokyo on an all-Japanese team. He understands about 60% of the daily standup (conducted in Japanese) but struggles with keigo and domain-specific IT terms. His 45-minute train commute is prime study time, but Anki on mobile is clunky.

**Opening Scene:** Every morning Hùng sits through a standup meeting in Japanese, catching fragments but missing nuance — especially when colleagues use keigo or specialized IT terms. On the train home, he scrolls through Anki but the mobile experience is frustrating: tiny buttons, no context, cards he created months ago that no longer feel relevant.

**Rising Action:** Hùng uses TableProject on his mobile browser. The responsive layout displays cards optimized for small screens. He creates a collection called "Daily Standup Vocab" and adds new terms each day right after the meeting — types the term quickly, auto-enrichment fills in the definition and example sentence within seconds.

He discovers an "IT Workplace Japanese" collection in the pre-seeded corpus — 200 terms precisely matching his workplace context, no manual creation needed.

**Climax:** In week 3, the dashboard reveals: *"Your Japanese IT terms retention is 62% vs English IT terms at 88%. Cross-language interference detected when reviewing in parallel mode — recommend single-language mode for new JP terms; use parallel mode only for terms already stable."* Hùng adjusts his strategy accordingly.

**Resolution:** By month 2, Hùng is noticeably more confident in standups. He upgrades to the Professional tier for advanced analytics and unlimited enrichment to support his daily workflow. He shares his diagnostic report with his manager as evidence for a career development review.

**Requirements Revealed:** Mobile-responsive web UI, quick-add vocabulary flow, pre-seeded corpus browsing and discovery, collection management, cross-language interference detection, diagnostic report export and sharing, Professional tier feature gating.

---

## Journey 4: Tâm — System Admin / Solo Operator (Secondary Admin Journey)

**Persona:** Tâm is the solo developer and system administrator of TableProject. He monitors platform health, manages content quality, and controls costs before writing new features each day.

**Opening Scene:** Each morning before coding, Tâm checks the operations dashboard to ensure the platform is healthy and costs are within budget.

**Rising Action:** Tâm reviews the morning metrics: LLM cost dashboard shows yesterday's spend at $1.20 (within the $1.80 daily budget). The enrichment queue has 45 jobs pending and 3 failed (timeouts) — he retries the failed jobs. The content moderation queue has 8 user-flagged definitions: 5 need fixes (Japanese hallucinations confirmed), 3 are false positives he dismisses.

He notices the cache hit rate sitting at 65% (below the 70% target) → drills down to find a batch of new users requesting medical vocabulary (not in the corpus) → decides to seed 200 medical terms into the corpus proactively.

**Climax:** An alert fires: daily LLM spend is trending toward $2.50 due to a viral signup spike. Tâm temporarily tightens the free-tier rate limit from 5 to 3 enrichments per day and switches bulk enrichment to the Batch API (50% cheaper, 24-hour turnaround) to absorb the surge.

**Resolution:** Costs stabilize, new users still receive a good experience, and the corpus grows by 150 validated terms per day. The system remains healthy and within budget.

**Requirements Revealed:** Admin dashboard (LLM cost tracking, enrichment queue status, cache hit rate metrics), content moderation interface, configurable rate limit controls, LLM provider routing controls, corpus seeding tools, cost and performance alert system.

---

## Journey 5: Support Troubleshooting — Import Failure Recovery (Secondary)

**Persona:** Linh, a user who encounters an import failure, and Tâm (admin) who resolves it.

**Opening Scene:** Linh submits a feedback report: "Imported my Anki APKG file but it shows 0 cards — all my cards are gone."

**Rising Action:** Tâm (admin) investigates via the admin dashboard: the import job log shows Linh's APKG file uses a custom Anki note type with non-standard field names. The cards are not lost — they are sitting in a "failed import" queue with detailed error information. Tâm previews the failed records, identifies the field-mapping mismatch, and replies to Linh with step-by-step instructions to re-export from Anki as CSV with standard column headers.

**Resolution:** Linh re-exports to CSV and imports successfully — all 1,200 cards come through clean. Tâm creates a backlog ticket to improve the APKG parser to handle custom note types in a future release.

**Requirements Revealed:** User feedback/report submission system, import job logging with detailed error diagnostics, admin view of user import history, failed import recovery queue with preview capability.

---

## Journey Requirements Summary

| Capability Area | Journeys |
|----------------|----------|
| Onboarding & Authentication (Google/LINE OAuth, email/password, survey, AI plan) | 1, 3 |
| FSRS Review Engine (scheduling, daily queue, calibration) | 1, 2, 3 |
| Chat-based Vocabulary Request (intent parsing, DB query, LLM fill) | 1 |
| Import System (CSV/APKG, error handling, preview, partial import) | 2, 5 |
| Auto-enrichment Pipeline + JMdict Validation | 1, 2, 3 |
| Learning Diagnostics Engine (pattern detection, recommendations) | 1, 3 |
| Collections Management (create, organize, browse pre-seeded) | 1, 3 |
| Mobile-responsive Web UI | 3 |
| Content Moderation System (flag, queue, review, validate) | 2, 4 |
| Admin Operations Dashboard (costs, queues, cache, alerts) | 4 |
| Rate Limiting & Cost Controls (per-tier limits, provider routing) | 4 |
| User Feedback & Report System | 2, 5 |
| Diagnostic Report Export & Sharing | 3 |
| Pre-seeded Corpus Browsing & Discovery | 3 |
| Corpus Seeding & Management Tools | 4 |
