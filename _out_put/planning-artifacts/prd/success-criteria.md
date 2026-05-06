# Success Criteria

## User Success

- **Vocabulary retention effectiveness:** ≥90% recall accuracy at 14-day intervals; ≥85% at 30-day intervals (for users completing ≥80% of scheduled reviews). FSRS benchmark: ~91% at 14 days with default parameters.
- **Zero-friction activation:** Time from signup to first review session < 3 minutes. No deck building, no configuration required.
- **Early engagement hook:** ≥40% of new users complete 3+ review sessions within their first 7 days.
- **Diagnostic "aha" moment:** ≥70% of users who reach 2 weeks of activity report that the dashboard helped them identify a vocabulary weakness they didn't previously recognize. This is the core value-proving moment.
- **Sustained learning behavior:** Median 25+ cards added per week; 10+ reviews completed per day among active users.

## Business Success

- **Month 1 acquisition target:** 10,000 registered users through community seeding (Vietnamese-in-Japan Facebook groups, JLPT prep Zalo communities, Vietnamese IT Discord/Telegram channels) and content marketing.
- **Product retention:** D7 ≥ 30%, D30 ≥ 15%.
- **Conversion to paid:** ≥5% free-to-Student tier conversion within 30 days of signup (target: 500 paid users from initial 10,000).
- **Revenue sustainability:** Break-even at ~200–300 paid users on Student tier (~$4–5/mo). Target: achieve break-even by Month 3.

## Technical Success

- **API performance:** p95 latency < 200ms for non-LLM endpoints.
- **LLM responsiveness:** p95 latency < 3s for enrichment; time-to-first-token < 800ms for streaming responses.
- **Cost discipline:** Daily LLM cost per active user < $0.02. Total MVP infrastructure ≤ $50/month for first 100 active users.
- **Corpus quality:** Auto-enrichment user satisfaction ("looks good" rate) ≥ 85%. All Japanese definitions cross-validated against JMdict before display.
- **Cache efficiency:** LLM enrichment cache hit rate > 70% after 4 weeks of operation.
- **Code quality:** Domain layer test coverage ≥ 90%; application layer ≥ 70%. Sentry error rate < 0.5% of requests.

## Measurable Outcomes

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
