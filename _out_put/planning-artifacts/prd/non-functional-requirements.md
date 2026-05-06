# Non-Functional Requirements

## Performance

- **NFR1:** Non-LLM API endpoints respond within 200ms at p95 under normal load.
- **NFR2:** LLM enrichment endpoints respond within 3 seconds at p95, with time-to-first-token < 800ms for streaming responses.
- **NFR3:** Card review interaction (flip, rate) completes with < 100ms perceived latency (client-side, no server round-trip required for flip).
- **NFR4:** Dashboard initial load (after login) achieves Time to Interactive < 3.5 seconds.
- **NFR5:** Landing page achieves Largest Contentful Paint < 2.5 seconds and Cumulative Layout Shift < 0.1.
- **NFR6:** CSV import processes up to 5,000 records within 30 seconds, with progress indication for imports > 500 records.
- **NFR7:** Daily review queue computation (fetching due cards for a user) completes within 100ms for users with up to 10,000 cards.

## Security

- **NFR8:** All data encrypted in transit (TLS 1.3) and at rest (managed PostgreSQL encryption).
- **NFR9:** Authentication uses short-lived access tokens (15-minute expiry) with refresh token rotation.
- **NFR10:** LLM API keys are stored server-side only — never exposed to browser or extension clients.
- **NFR11:** Per-user rate limiting enforced on all LLM enrichment endpoints (configurable per subscription tier).
- **NFR12:** User vocabulary lists and learning patterns are never logged in application logs. Structured logs use PII scrubbing.
- **NFR13:** User-content delimiters used in all LLM prompts to mitigate prompt injection from user-submitted vocabulary.
- **NFR14:** GDPR-compliant data export and deletion endpoints operational from Day 1 (APPI/PDPD compliance for Japan/Vietnam users).

## Scalability

- **NFR15:** System supports 100 concurrent active users on MVP infrastructure (≤ $50/month).
- **NFR16:** Architecture supports 10x user growth (1,000 concurrent users) with horizontal scaling of stateless API workers and read replicas, without architectural redesign.
- **NFR17:** LLM enrichment pipeline handles traffic spikes via queue-based async processing — degrading gracefully to longer enrichment times rather than failing.
- **NFR18:** Central vocabulary corpus supports up to 100,000 validated terms without query performance degradation on hierarchical lookups.
- **NFR19:** Daily LLM cost per active user remains below $0.02 through prompt caching, Batch API, and provider routing.

## Accessibility

- **NFR20:** Core learning flows (card review, onboarding, collection browsing) conform to WCAG 2.1 Level AA.
- **NFR21:** Full keyboard navigation supported for the card review workflow — no mouse required for the primary learning loop.
- **NFR22:** Screen reader support via ARIA labels for interactive components and live regions for dynamic content updates.
- **NFR23:** Color contrast meets minimum 4.5:1 for normal text and 3:1 for large text. Status indicators (retention red/yellow/green) use shape/icon differentiation in addition to color.
- **NFR24:** UI respects `prefers-reduced-motion` and `prefers-color-scheme` user preferences.

## Integration & Interoperability

- **NFR25:** LLM provider gateway supports switching between multiple LLM providers without application code changes.
- **NFR26:** CSV import supports UTF-8 encoding with BOM, tab-separated values, and hierarchical tag notation (Subject::Unit::Topic).
- **NFR27:** JMdict cross-validation operates against a locally-cached dataset (~170K entries), not an external API call, ensuring zero external dependency for Japanese validation.
- **NFR28:** Offline card review functions via PWA with client-side persistent storage — reviews completed offline sync automatically when connectivity is restored via background sync capability.
- **NFR29:** All API endpoints documented via framework-native auto-generated OpenAPI specification.

## Reliability

- **NFR30:** System achieves 99.5% uptime for core learning flows (card review, SRS scheduling). Maintenance windows scheduled outside peak hours (18:00–23:00 ICT).
- **NFR31:** LLM provider outage does not block card review or dashboard access — only auto-enrichment degrades gracefully (queued for retry).
- **NFR32:** Database backups run daily with point-in-time recovery capability (managed PostgreSQL feature).
- **NFR33:** Failed enrichment jobs retry up to 3 times with exponential backoff before routing to a dead-letter queue for admin review.
- **NFR34:** Background job failure rate remains below 1% of total jobs processed.

