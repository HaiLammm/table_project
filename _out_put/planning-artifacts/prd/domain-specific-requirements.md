# Domain-Specific Requirements

## Compliance & Regulatory

- **COPPA/FERPA:** Not directly applicable — target audience is adults 18+, not K-12. If university partnerships are pursued, FERPA awareness will be needed.
- **GDPR-lite approach:** Data export and deletion endpoints implemented from Day 1. Users in Japan fall under APPI (Act on Protection of Personal Information) — similar to GDPR. Users in Vietnam fall under PDPD (Personal Data Protection Decree 13/2023). Both require explicit consent for data collection and the right to deletion.
- **JMdict licensing:** CC BY-SA 3.0 — used for validation only (not as primary corpus source). Proper attribution required in app footer and documentation.

## Technical Constraints

- **LLM content safety:** All LLM-generated Japanese definitions must be cross-validated against JMdict before user display. Unvalidated definitions are flagged with a warning indicator. User reporting mechanism for incorrect content is mandatory.
- **Data isolation:** User vocabulary lists and learning patterns are personal data. No sharing of individual learning data without explicit consent. Aggregated, anonymized data may be used for corpus improvement.
- **Multi-region considerations:** Users in Vietnam and Japan. Data stored in a single region (Asia-Pacific) with sub-200ms latency to both countries. No data residency requirements currently mandated, but architecture should support region-specific storage if regulations change.

## Content Moderation

- **Auto-enrichment quality gate:** LLM outputs validated against structured schema (Pydantic) + JMdict cross-check for Japanese. Outputs failing validation enter a moderation queue rather than being shown to users.
- **User flag system:** Any user can flag a definition as incorrect. Flagged items are temporarily hidden and routed to admin review.
- **Corpus integrity:** Central corpus updates from Database Waterfall undergo deduplication and validation before merging. No raw LLM output enters the shared corpus without validation.

## Domain Risk Mitigations

| Risk | Domain Impact | Mitigation |
|------|--------------|------------|
| LLM teaches wrong kanji/reading | Users learn incorrect Japanese — trust destroyed | JMdict cross-check mandatory; user flag system; human review queue |
| Learning data breach | Personal vocabulary reveals professional domain, exam prep status | Encrypt at rest; minimize PII in logs; GDPR-style export/delete |
| Free-tier abuse (LLM cost spike) | Unsustainable costs before revenue | Per-user rate limits; Batch API for bulk; auto-tighten on cost threshold |
| Accessibility gaps | Excludes users with disabilities | WCAG 2.1 AA compliance for core learning flows; keyboard navigation; screen reader support for card review |
| Content bias in LLM outputs | Vietnamese-specific examples may be culturally inappropriate | Review prompt templates for cultural sensitivity; user feedback loop |
