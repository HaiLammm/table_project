from datetime import datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats, SrsCard
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode
from src.app.modules.srs.infrastructure.models import SrsCardModel

logger = structlog.get_logger().bind(module="srs_repository")


def _to_domain(model: SrsCardModel) -> SrsCard:
    return SrsCard(
        id=model.id,
        user_id=model.user_id,
        term_id=model.term_id,
        due_at=model.due_at,
        fsrs_state=model.fsrs_state,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemySrsCardRepository(SrsCardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        overdue_cutoff = now - timedelta(days=1)
        result = await self._session.execute(
            select(
                func.count(SrsCardModel.id),
                func.count(SrsCardModel.id).filter(SrsCardModel.due_at < overdue_cutoff),
            ).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            ),
        )
        due_count, overdue_count = result.one()

        logger.info("srs_queue_stats_loaded", user_id=user_id)
        return QueueStats(
            due_count=int(due_count or 0),
            overdue_count=int(overdue_count or 0),
            estimated_minutes=0,
        )

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        total_result = await self._session.execute(
            select(func.count(SrsCardModel.id)).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            ),
        )
        total_count = int(total_result.scalar_one() or 0)

        result = await self._session.execute(
            select(SrsCardModel)
            .where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            )
            .order_by(SrsCardModel.due_at.asc(), SrsCardModel.id.asc())
            .offset(offset)
            .limit(limit),
        )

        logger.info(
            "srs_due_cards_loaded",
            user_id=user_id,
            mode=mode.value,
            limit=limit,
            offset=offset,
        )
        return DueCardsPage(
            items=[_to_domain(model) for model in result.scalars().all()],
            total_count=total_count,
            mode=mode,
            limit=limit,
            offset=offset,
        )
