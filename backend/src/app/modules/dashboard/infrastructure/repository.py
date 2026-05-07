from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.dashboard.domain.entities import DiagnosticInsight
from src.app.modules.dashboard.domain.exceptions import InsightNotFoundError
from src.app.modules.dashboard.domain.interfaces import DiagnosticRepository, ReviewAnalyticsRow
from src.app.modules.dashboard.domain.value_objects import PatternType
from src.app.modules.dashboard.infrastructure.models import (
    DiagnosticInsightModel,
    InsightSeenModel,
)
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel
from src.app.modules.vocabulary.infrastructure.models import VocabularyTermModel

logger = structlog.get_logger().bind(module="dashboard_repository")


def _to_domain(model: DiagnosticInsightModel) -> DiagnosticInsight:
    try:
        pattern_type = PatternType(model.type)
    except ValueError:
        pattern_type = PatternType.TIME_OF_DAY_PATTERN
        logger.warning("unknown_pattern_type", raw_type=model.type, fallback=pattern_type.value)
    return DiagnosticInsight(
        id=model.id,
        user_id=model.user_id,
        type=pattern_type,
        severity=model.severity,
        icon=model.icon,
        title=model.title,
        text=model.text,
        action_label=model.action_label,
        action_href=model.action_href,
        confidence_score=model.confidence_score,
        created_at=model.created_at,
        expires_at=model.expires_at,
    )


class SqlAlchemyDiagnosticRepository(DiagnosticRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending_insights(
        self,
        user_id: int,
        session_id: UUID,
        limit: int,
    ) -> list[DiagnosticInsight]:
        now = datetime.now(UTC)
        seen_subquery = select(InsightSeenModel.id).where(
            InsightSeenModel.insight_id == DiagnosticInsightModel.id,
            InsightSeenModel.user_id == user_id,
            InsightSeenModel.session_id == session_id,
        )
        result = await self._session.execute(
            select(DiagnosticInsightModel)
            .where(
                DiagnosticInsightModel.user_id == user_id,
                or_(
                    DiagnosticInsightModel.expires_at.is_(None),
                    DiagnosticInsightModel.expires_at > now,
                ),
                ~exists(seen_subquery),
            )
            .order_by(
                DiagnosticInsightModel.confidence_score.desc(),
                DiagnosticInsightModel.created_at.desc(),
                DiagnosticInsightModel.id.asc(),
            )
            .limit(limit),
        )
        return [_to_domain(model) for model in result.scalars().all()]

    async def mark_insight_seen(
        self,
        insight_id: int,
        user_id: int,
        session_id: UUID,
    ) -> None:
        insight_result = await self._session.execute(
            select(DiagnosticInsightModel).where(
                DiagnosticInsightModel.id == insight_id,
                DiagnosticInsightModel.user_id == user_id,
            )
        )
        insight = insight_result.scalar_one_or_none()
        if insight is None:
            msg = "Insight not found"
            raise InsightNotFoundError(msg, details={"insight_id": insight_id, "user_id": user_id})

        await self._session.execute(
            pg_insert(InsightSeenModel)
            .values(insight_id=insight_id, user_id=user_id, session_id=session_id)
            .on_conflict_do_nothing(
                constraint="uq_insight_seen",
            )
        )
        await self._session.commit()

        logger.info(
            "insight_seen_marked",
            user_id=user_id,
            insight_id=insight_id,
            pattern_type=insight.type,
        )

    async def get_review_analytics(
        self,
        user_id: int,
        days_back: int,
    ) -> list[ReviewAnalyticsRow]:
        cutoff = datetime.now(UTC) - timedelta(days=days_back)
        result = await self._session.execute(
            select(
                SrsReviewModel.reviewed_at,
                SrsReviewModel.rating,
                SrsReviewModel.response_time_ms,
                VocabularyTermModel.part_of_speech,
                VocabularyTermModel.term,
            )
            .join(SrsCardModel, SrsCardModel.id == SrsReviewModel.card_id)
            .outerjoin(VocabularyTermModel, VocabularyTermModel.id == SrsCardModel.term_id)
            .where(
                SrsReviewModel.user_id == user_id,
                SrsReviewModel.reviewed_at >= cutoff,
            )
            .order_by(SrsReviewModel.reviewed_at.asc()),
        )

        rows: list[ReviewAnalyticsRow] = []
        for reviewed_at, rating, response_time_ms, term_category, term_text in result.all():
            rows.append(
                {
                    "reviewed_at": reviewed_at,
                    "rating": rating,
                    "response_time_ms": response_time_ms,
                    "term_category": term_category,
                    "term_text": term_text,
                }
            )
        return rows

    async def count_active_insights(self, user_id: int) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(func.count(DiagnosticInsightModel.id)).where(
                DiagnosticInsightModel.user_id == user_id,
                or_(
                    DiagnosticInsightModel.expires_at.is_(None),
                    DiagnosticInsightModel.expires_at > now,
                ),
            )
        )
        return int(result.scalar_one() or 0)

    async def replace_insights(
        self,
        user_id: int,
        insights: list[DiagnosticInsight],
    ) -> None:
        async with self._session.begin_nested():
            await self._session.execute(
                delete(DiagnosticInsightModel).where(DiagnosticInsightModel.user_id == user_id)
            )

            for insight in insights:
                self._session.add(
                    DiagnosticInsightModel(
                        user_id=user_id,
                        type=insight.type.value,
                        severity=insight.severity.value
                        if hasattr(insight.severity, "value")
                        else insight.severity,
                        icon=insight.icon,
                        title=insight.title,
                        text=insight.text,
                        action_label=insight.action_label,
                        action_href=insight.action_href,
                        confidence_score=insight.confidence_score,
                        expires_at=insight.expires_at,
                    )
                )

        await self._session.commit()
        logger.info("diagnostic_insights_replaced", user_id=user_id, count=len(insights))
