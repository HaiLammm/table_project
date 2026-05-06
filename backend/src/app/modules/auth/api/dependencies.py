from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends

from src.app.core.security import get_current_user as core_get_current_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import AuthorizationError
from src.app.modules.auth.domain.value_objects import UserTier

TIER_RANK = {
    UserTier.FREE: 0,
    UserTier.STUDENT: 1,
    UserTier.PROFESSIONAL: 2,
}
CurrentUserDependency = Annotated[User, Depends(core_get_current_user)]


async def get_current_user(
    current_user: CurrentUserDependency,
) -> User:
    return current_user


def require_tier(required_tier: UserTier) -> Callable[..., Awaitable[User]]:
    async def dependency(current_user: CurrentUserDependency) -> User:
        if TIER_RANK[current_user.tier] < TIER_RANK[required_tier]:
            msg = "Insufficient subscription tier"
            raise AuthorizationError(
                msg,
                details={
                    "required_tier": required_tier.value,
                    "current_tier": current_user.tier.value,
                },
            )

        return current_user

    return dependency
