from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.app.modules.dashboard.application.services import (
    DiagnosticsService,
    _detect_category_weakness,
    _detect_cross_language_interference,
    _detect_time_of_day_pattern,
)
from src.app.modules.dashboard.domain.entities import DiagnosticInsight
from src.app.modules.dashboard.domain.interfaces import DiagnosticRepository, ReviewAnalyticsRow
from src.app.modules.dashboard.domain.value_objects import PatternType


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
    language: str = "en",
    parallel_mode_active: bool = False,
    term_id: int | None = 101,
    card_id: int = 201,
    term_text: str = "protocol",
) -> ReviewAnalyticsRow:
    reviewed_at = datetime.now(UTC) - timedelta(days=days_ago)
    reviewed_at = reviewed_at.replace(hour=hour, minute=0, second=0, microsecond=0)
    return {
        "reviewed_at": reviewed_at,
        "rating": rating,
        "response_time_ms": response_time_ms,
        "term_category": category,
        "term_text": term_text,
        "language": language,
        "parallel_mode_active": parallel_mode_active,
        "term_id": term_id,
        "card_id": card_id,
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


async def test_compute_insights_skips_time_of_day_when_review_count_is_below_fifty() -> None:
    analytics = []
    for days_ago in range(8):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1100, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=12000, category="verb")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=13, rating=4, response_time_ms=1500, category="verb")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=15, rating=4, response_time_ms=1600, category="noun")
        )

    repository = InMemoryDiagnosticRepository(analytics)
    service = DiagnosticsService(repository)

    insights = await service.compute_insights(user_id=7)

    assert all(insight.type is not PatternType.TIME_OF_DAY_PATTERN for insight in insights)


async def test_compute_insights_generates_full_diagnostics_after_two_weeks() -> None:
    analytics = []
    for days_ago in range(15):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=900, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=15000, category="verb")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=13, rating=4, response_time_ms=1800, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=16, rating=4, response_time_ms=1500, category="verb")
        )

    repository = InMemoryDiagnosticRepository(analytics)
    service = DiagnosticsService(repository)

    insights = await service.compute_insights(user_id=7)

    assert len(insights) == 3
    assert all(insight.confidence_score == 1.0 for insight in insights)
    assert any(insight.action_href == "/dashboard" for insight in insights)
    assert {insight.delivery_interval for insight in insights} == {5}


def test_time_of_day_pattern_skips_when_history_is_shorter_than_seven_days() -> None:
    analytics = [
        make_row(days_ago=days_ago % 6, hour=8, rating=4, response_time_ms=1000, category="noun")
        for days_ago in range(30)
    ]
    analytics.extend(
        make_row(days_ago=days_ago % 6, hour=22, rating=1, response_time_ms=1000, category="noun")
        for days_ago in range(30)
    )

    insight = _detect_time_of_day_pattern(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is None


def test_time_of_day_pattern_skips_when_review_count_is_below_fifty() -> None:
    analytics = []
    for days_ago in range(7):
        analytics.append(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1000, category="noun")
        )
        analytics.append(
            make_row(days_ago=days_ago, hour=22, rating=1, response_time_ms=1000, category="noun")
        )

    insight = _detect_time_of_day_pattern(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is None


def test_time_of_day_pattern_detects_when_thresholds_are_met() -> None:
    analytics = []
    for days_ago in range(10):
        analytics.extend(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1000, category="noun")
            for _ in range(3)
        )
        analytics.extend(
            make_row(days_ago=days_ago, hour=22, rating=1, response_time_ms=1000, category="noun")
            for _ in range(3)
        )

    insight = _detect_time_of_day_pattern(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is not None
    assert insight.type is PatternType.TIME_OF_DAY_PATTERN


def test_category_weakness_skips_when_each_category_has_fewer_than_thirty_reviews() -> None:
    analytics = []
    for days_ago in range(10):
        analytics.extend(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1000, category="noun")
            for _ in range(2)
        )
        analytics.extend(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=1000, category="verb")
            for _ in range(2)
        )

    insight = _detect_category_weakness(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is None


def test_category_weakness_detects_when_categories_meet_threshold() -> None:
    analytics = []
    for days_ago in range(15):
        analytics.extend(
            make_row(days_ago=days_ago, hour=8, rating=4, response_time_ms=1000, category="noun")
            for _ in range(2)
        )
        analytics.extend(
            make_row(days_ago=days_ago, hour=20, rating=1, response_time_ms=1000, category="verb")
            for _ in range(2)
        )

    insight = _detect_category_weakness(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is not None
    assert insight.type is PatternType.CATEGORY_SPECIFIC_WEAKNESS


def test_cross_language_interference_skips_when_parallel_reviews_are_below_threshold() -> None:
    analytics = [
        make_row(
            days_ago=index % 10,
            hour=20,
            rating=1,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=True,
            term_id=501,
            card_id=900 + index,
        )
        for index in range(19)
    ]
    analytics.extend(
        make_row(
            days_ago=index % 10,
            hour=8,
            rating=4,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=False,
            term_id=501,
            card_id=950 + index,
        )
        for index in range(10)
    )

    insight = _detect_cross_language_interference(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is None


def test_cross_language_interference_detects_significant_parallel_drop() -> None:
    analytics = [
        make_row(
            days_ago=index % 10,
            hour=20,
            rating=1,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=True,
            term_id=501,
            card_id=900 + index,
            term_text="protocol",
            language="jp",
        )
        for index in range(20)
    ]
    analytics.extend(
        make_row(
            days_ago=index % 10,
            hour=8,
            rating=4,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=False,
            term_id=501,
            card_id=950 + index,
            term_text="protocol",
            language="jp",
        )
        for index in range(20)
    )

    insight = _detect_cross_language_interference(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is not None
    assert insight.type is PatternType.CROSS_LANGUAGE_INTERFERENCE
    assert insight.icon == "languages"
    assert "protocol" in insight.text


def test_cross_language_interference_skips_when_delta_is_not_significant() -> None:
    analytics = [
        make_row(
            days_ago=index % 10,
            hour=20,
            rating=3 if index < 17 else 2,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=True,
            term_id=501,
            card_id=900 + index,
        )
        for index in range(20)
    ]
    analytics.extend(
        make_row(
            days_ago=index % 10,
            hour=8,
            rating=4 if index < 18 else 2,
            response_time_ms=1200,
            category="noun",
            parallel_mode_active=False,
            term_id=501,
            card_id=950 + index,
        )
        for index in range(20)
    )

    insight = _detect_cross_language_interference(
        user_id=7,
        analytics=analytics,
        confidence_score=0.8,
    )

    assert insight is None


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
