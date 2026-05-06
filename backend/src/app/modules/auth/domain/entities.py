from dataclasses import dataclass
from datetime import datetime

from src.app.modules.auth.domain.value_objects import UserTier


@dataclass(slots=True, kw_only=True)
class User:
    clerk_id: str
    email: str
    display_name: str | None
    tier: UserTier = UserTier.FREE
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
