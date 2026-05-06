import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import UserNotFoundError
from src.app.modules.auth.domain.interfaces import UserRepository
from src.app.modules.auth.domain.value_objects import UserTier
from src.app.modules.auth.infrastructure.models import UserModel

logger = structlog.get_logger().bind(module="auth_repository")


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        clerk_id=model.clerk_id,
        email=model.email,
        display_name=model.display_name,
        tier=UserTier(model.tier),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.clerk_id == clerk_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def create(self, user: User) -> User:
        model = UserModel(
            clerk_id=user.clerk_id,
            email=user.email,
            display_name=user.display_name,
            tier=user.tier.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_user_created", clerk_id=model.clerk_id)
        return _to_domain(model)

    async def update(self, user: User) -> User:
        if user.id is None:
            msg = "User id is required for updates"
            raise UserNotFoundError(msg)

        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        model.clerk_id = user.clerk_id
        model.email = user.email
        model.display_name = user.display_name
        model.tier = user.tier.value

        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_user_updated", clerk_id=model.clerk_id)
        return _to_domain(model)
