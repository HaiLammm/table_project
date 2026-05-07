# Deferred Work

## Deferred from: code review of 4-5-diagnostic-micro-insertions (2026-05-07)

- PatternType enum has 3 unimplemented pattern types (CROSS_LANGUAGE_INTERFERENCE, SESSION_LENGTH_EFFECT, DAY_OF_WEEK_PATTERN) — future story scope
- Dashboard reads from srs/vocabulary module internals via direct ORM model imports — matches spec's "read model" pattern, restructure later if needed
- get_review_analytics returns unbounded result set — 30-day cap limits size, add pagination if performance issues arise
- patternsDetected sourced from local counter (insightsSeen), not server-validated — minor UX gap, could add server tracking later
- datetime.now(UTC) vs DB server time clock drift — negligible for most deployments
- No index on expires_at for expiration filter — premature optimization for current data volumes