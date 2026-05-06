from functools import lru_cache
from typing import Annotated

import jwt
import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.db.session import get_async_session
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import AuthenticationError, UserNotFoundError
from src.app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository

logger = structlog.get_logger().bind(module="auth_security")
security = HTTPBearer(auto_error=False)
CredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(security),
]
SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


@lru_cache
def get_jwks_client() -> PyJWKClient:
    if not settings.clerk_jwks_url:
        msg = "Clerk JWKS URL is not configured"
        raise AuthenticationError(msg)

    return PyJWKClient(
        settings.clerk_jwks_url,
        cache_keys=True,
        lifespan=3600,
    )


async def get_current_user(
    credentials: CredentialsDependency,
    session: SessionDependency,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        msg = "Missing bearer token"
        raise AuthenticationError(msg)

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
        )
    except (InvalidTokenError, PyJWKClientError, ValueError) as exc:
        logger.warning("auth_token_verification_failed", error=str(exc))
        msg = "Invalid Clerk token"
        raise AuthenticationError(msg) from exc

    clerk_id = payload.get("sub")
    if not isinstance(clerk_id, str) or not clerk_id:
        msg = "Clerk token missing subject"
        raise AuthenticationError(msg)

    repository = SqlAlchemyUserRepository(session)
    user = await repository.get_by_clerk_id(clerk_id)
    if user is None:
        logger.warning("auth_user_not_found", clerk_id=clerk_id)
        msg = "User not found"
        raise UserNotFoundError(msg)

    return user
