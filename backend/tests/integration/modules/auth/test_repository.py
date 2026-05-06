from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.value_objects import UserTier
from src.app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository


async def test_user_repository_create_get_update(
    auth_schema: None,
    async_session: AsyncSession,
) -> None:
    repository = SqlAlchemyUserRepository(async_session)

    created_user = await repository.create(
        User(
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
        ),
    )

    assert created_user.id is not None
    assert created_user.tier is UserTier.FREE

    user_by_clerk_id = await repository.get_by_clerk_id("user_123")
    assert user_by_clerk_id is not None
    assert user_by_clerk_id.email == "lem@example.com"

    updated_user = await repository.update(
        User(
            id=created_user.id,
            clerk_id=created_user.clerk_id,
            email="lem.updated@example.com",
            display_name="Lem Updated",
            tier=UserTier.STUDENT,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
        ),
    )

    assert updated_user.email == "lem.updated@example.com"
    assert updated_user.display_name == "Lem Updated"
    assert updated_user.tier is UserTier.STUDENT

    user_by_id = await repository.get_by_id(created_user.id)
    assert user_by_id is not None
    assert user_by_id.email == "lem.updated@example.com"
    assert user_by_id.tier is UserTier.STUDENT
