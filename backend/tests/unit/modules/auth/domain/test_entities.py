from datetime import UTC, datetime

from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.value_objects import UserTier


def test_user_entity_defaults_to_free_tier() -> None:
    now = datetime.now(UTC)

    user = User(
        clerk_id="user_123",
        email="lem@example.com",
        display_name="Lem",
        created_at=now,
        updated_at=now,
    )

    assert user.id is None
    assert user.tier is UserTier.FREE
    assert user.created_at == now
    assert user.updated_at == now


def test_user_tier_values_match_story_contract() -> None:
    assert UserTier.FREE.value == "free"
    assert UserTier.STUDENT.value == "student"
    assert UserTier.PROFESSIONAL.value == "professional"
