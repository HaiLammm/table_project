# Innovation & Novel Patterns

## Detected Innovation Areas

**1. Database Waterfall — Self-Growing Collective Corpus**
Unlike Anki (user-created only) or Duolingo (platform-curated, static), TableProject's vocabulary corpus grows automatically through user interactions. Each enrichment request generates validated vocabulary data that feeds back into the central corpus. This creates a data flywheel: more users → richer corpus → better experience → more users. After 6–12 months, the resulting bilingual dataset — tuned to Vietnamese speakers' learning patterns and cross-validated against JMdict — becomes a defensible asset no competitor can quickly replicate.

**2. Learning Diagnostics Engine — Prescriptive, Not Descriptive**
Existing tools show descriptive metrics (streaks, scores, completion percentages). TableProject's diagnostic engine correlates forgetting patterns with behavioral signals (time-of-day, category, session length, cross-language interference) to produce prescriptive recommendations. This shifts the value proposition from "track your learning" to "understand why you're failing and fix it."

**3. Bilingual Vocabulary as First-Class Entity**
No existing platform models a vocabulary term as a single bilingual object with independent per-language retention tracking. This architecture enables detection of cross-language interference patterns — e.g., identifying that a user's Japanese retention drops when reviewing the same term in parallel mode, suggesting single-language review for unstable terms.

**4. Conversational Vocabulary Acquisition Pipeline**
The chat-based intent parser combines natural language understanding, database querying, LLM enrichment, and user confirmation in a single conversational flow. This eliminates the traditional flashcard creation workflow entirely — users describe what they want to learn, and the system delivers enriched, categorized, SRS-ready cards.

## Market Context & Competitive Landscape

- **Anki**: Open-source FSRS, most powerful SRS. No bilingual model, no diagnostics, no auto-enrichment. Community plugins cannot replicate the diagnostic engine or self-growing corpus.
- **Duolingo**: 40+ languages, gamified. No bilingual EN-JP, no diagnostic intelligence, vocabulary is shallow and non-customizable.
- **Migaku**: Immersion-based (Netflix/YouTube). No bilingual pairing, no Vietnamese learner support, no diagnostic engine.
- **Closest analog**: None. The combination of self-growing corpus + diagnostic engine + bilingual entity model is novel in the vocabulary learning space.

## Validation Approach

1. **Database Waterfall validation**: Track corpus growth rate vs. cache hit rate over first 4 weeks. Target: >70% cache hit rate (indicating meaningful vocabulary overlap across users). If hit rate is low, the corpus is fragmenting and the flywheel isn't spinning.
2. **Diagnostic engine validation**: In-app survey at 2-week mark — "Did the dashboard help you identify a weakness you didn't know about?" Target: ≥70% yes. If below threshold, diagnostic patterns need tuning or different signals.
3. **Bilingual entity validation**: A/B test parallel mode vs. separate-deck mode for retention at 14 and 30 days. Measure cross-language interference detection accuracy.
4. **Chat acquisition validation**: Track completion rate of chat-based vocabulary requests (user confirms the generated set). Target: ≥80% confirmation rate. Low rate indicates intent parsing or enrichment quality issues.

## Innovation Risk Mitigation

| Innovation | Risk | Fallback |
|-----------|------|----------|
| Database Waterfall | Corpus fragments (low overlap across users) | Fall back to curated seed corpus + manual expansion; reduce LLM enrichment budget |
| Diagnostics Engine | Insufficient data in first 2 weeks for meaningful patterns | Show estimated learning curves from FSRS parameters on Day 1; surface first insights after 3 days of data |
| Bilingual Entity | Cross-language interference detection produces false positives | Default to single-language mode; make parallel mode opt-in with clear guidance |
| Chat Acquisition | Intent parser misinterprets requests | Provide structured form fallback alongside chat; use progressive clarification |
