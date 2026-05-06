from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.auth.domain.value_objects import UserTier


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clerk_id: str
    email: str
    display_name: str | None
    tier: UserTier
    created_at: datetime
    updated_at: datetime


class ClerkEmailAddressPayload(BaseModel):
    id: str | None = None
    email_address: str


class ClerkWebhookUserPayload(BaseModel):
    id: str
    email_addresses: list[ClerkEmailAddressPayload] = Field(default_factory=list)
    primary_email_address_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class WebhookPayload(BaseModel):
    type: Literal["user.created", "user.updated", "user.deleted"]
    data: ClerkWebhookUserPayload


class WebhookSyncResponse(BaseModel):
    status: Literal["synced", "ignored"]
    event_type: Literal["user.created", "user.updated", "user.deleted"]
    user: UserResponse | None = None
