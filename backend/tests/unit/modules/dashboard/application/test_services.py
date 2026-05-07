from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.app.modules.dashboard.application.services import DiagnosticsService
from src.app.modules.dashboard.domain.entities import DiagnosticInsight
from src.app.modules.dashboard.domain.interfaces import DiagnosticRepository, ReviewAnalyticsRow


class InMemoryDiagnosticRepository(DiagnosticRepository):
    def __init__(self, analytics: Sequence[ReviewAnalyticsRow]) -> None:
        self.analytics = list(analytics)
        self.insights: list[DiagnosticInsight] = []
        self.replace_calls = 0
        self.seen_by_session: set[tuple[int, int, UUID]] = set()

    async def get_pending_insights(
        self,
        user_id: int,
        session_id: UUID,
        limit: int,
    ) -> list[DiagnosticInsight]:
        unseen = [
            insight
            for insight in self.insights
            if insight.user_id == user_id
            and (insight.id, user_id, session_id) not in self.seen_by_session
        ]
        return unseen[:limit]

    async def mark_insight_seen(self, insight_id: int, user_id: int, session_id: UUID) -> None:
        self.seen_by_session.add((insight_id, user_id, session_id))

    async def get_review_analytics(self, user_id: int, days_back: int) -> list[ReviewAnalyticsRow]:
        _ = (user_id, days_back)
        return list(self.analytics)

    async def count_active_insights(self, user_id: int) -> int:
        return len([insight for insight in self.insights if insight.user_id == user_id])

    async def replace_insights(self, user_id: int, insights: list[DiagnosticInsight]) -> None:
        self.replace_calls += 1
        self.insights = [
            DiagnosticInsight(
                id=index + 1,
                user_id=insight.user_id,
                type=insight.type,
                severity=insight.severity,
                icon=insight.icon,
                title=insight.title,
                text=insight.text,
                action_label=insight.action_label,
                action_href=insight.action_href,
                confidence_score=insight.confidence_score,
                created_at=insight.created_at,
                expires_at=insight.expires_at,
            )
            for index, insight in enumerate(insights)
            if insight.user_id == user_id
        ]


def make_row(
    *,
    days_ago: int,
    hour: int,
    rating: int,
    response_time_ms: int | None,
    category: str | None,
) -> ReviewAnalyticsRow:
    reviewed_at = datetime.now(UTC) - timedelta(days=days_ago)
    reviewed_at = reviewed_at.replace(hour=hour, minute=0, second=0, microsecond=0)
    return {
        "reviewed_at": reviewed_at,
        "rating": rating,
        "response_time_ms": response_time_ms,
        "term_category": category,
        "term_text": "protocol",
    }


async def test_compute_insights_returns_empty_with_less_than_three_days_of_history() -> None:
    repository = InMemoryDiagnosticRepository(
        [
            make_row(days_ago=1, hour=8, rating=4, response_time_ms=1200, category="noun"),
            make_row(days_ago=0, hour=20, rating=1, response_time_ms=12000, category="verb"),
        ]
    )
    service = DiagnosticsService(repository)

    insights = await service.compute_insights(user_id=7)

    assert insights == []
    assert repository.insights == []


async def test_compute_insights_generates_low_confidence_micro_aha_for_early_history() -> None:
    analytics = []
    for days_ago in range(4):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1100, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=12000, category="verb")
        )

    repository = InMemoryDiagnosticRepository(analytics)
    service = DiagnosticsService(repository)

    insights = await service.compute_insights(user_id=7)

    assert len(insights) == 1
    assert insights[0].title == "Quick insight"
    assert "morning" in insights[0].text
    assert insights[0].confidence_score == 0.5
    assert insights[0].action_href is None
    assert insights[0].delivery_interval == 10


async def test_compute_insights_generates_full_diagnostics_after_two_weeks() -> None:
    analytics = []
    for days_ago in range(16):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=900, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=15000, category="verb")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=13, rating=3, response_time_ms=1800, category="noun")
        )

    repository = InMemoryDiagnosticRepository(analytics)
    service = DiagnosticsService(repository)

    insights = await service.compute_insights(user_id=7)

    assert len(insights) == 3
    assert all(insight.confidence_score == 1.0 for insight in insights)
    assert any(insight.action_href == "/dashboard" for insight in insights)
    assert {insight.delivery_interval for insight in insights} == {5}


async def test_get_pending_insights_computes_once_and_hides_seen_items() -> None:
    analytics = []
    for days_ago in range(8):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1000, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=12000, category="verb")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=13, rating=3, response_time_ms=1500, category="noun")
        )

    repository = InMemoryDiagnosticRepository(analytics)
    service = DiagnosticsService(repository)
    session_id = uuid4()

    first_batch = await service.get_pending_insights(user_id=7, session_id=session_id, limit=3)
    await service.mark_insight_seen(first_batch[0].id or 0, user_id=7, session_id=session_id)
    second_batch = await service.get_pending_insights(user_id=7, session_id=session_id, limit=3)

    assert repository.replace_calls == 1
    assert first_batch[0].id not in {insight.id for insight in second_batch}
