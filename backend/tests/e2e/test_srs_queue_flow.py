import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core import security as security_module
from src.app.core.config import settings
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel


class StubSigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class StubJwksClient:
    def __init__(self, key: object) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, _token: str) -> StubSigningKey:
        return StubSigningKey(self._key)


def build_svix_secret(raw_secret: bytes) -> str:
    return f"whsec_{base64.b64encode(raw_secret).decode()}"


async def create_authenticated_user(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    clerk_id: str,
    email: str,
) -> dict[str, str]:
    from svix.webhooks import Webhook

    webhook_secret = build_svix_secret(b"table-project-test-secret")
    now = datetime.now(UTC)
    msg_id = f"msg_{uuid4().hex}"

    monkeypatch.setattr(settings, "clerk_webhook_secret", webhook_secret)
    monkeypatch.setattr(settings, "clerk_jwks_url", "https://clerk.test/.well-known/jwks.json")
    security_module.get_jwks_client.cache_clear()

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    monkeypatch.setattr(security_module, "get_jwks_client", lambda: StubJwksClient(public_key))

    webhook_payload = {
        "type": "user.created",
        "data": {
            "id": clerk_id,
            "email_addresses": [
                {
                    "id": f"email_{uuid4().hex}",
                    "email_address": email,
                },
            ],
            "primary_email_address_id": None,
            "first_name": "Queue",
            "last_name": "User",
        },
    }
    webhook_body = json.dumps(webhook_payload)
    webhook_signature = Webhook(webhook_secret).sign(msg_id, now, webhook_body)

    webhook_response = await auth_client.post(
        "/api/v1/auth/webhook",
        content=webhook_body,
        headers={
            "content-type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": str(int(now.timestamp())),
            "svix-signature": webhook_signature,
        },
    )
    assert webhook_response.status_code == 200

    access_token = jwt.encode(
        {
            "sub": clerk_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        private_key,
        algorithm="RS256",
    )

    return {"Authorization": f"Bearer {access_token}"}


async def seed_srs_cards(
    async_session: AsyncSession,
    auth_client: AsyncClient,
    auth_headers: dict[str, str],
    due_offsets: list[timedelta],
) -> None:
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    now = datetime.now(UTC)
    for index, offset in enumerate(due_offsets, start=1):
        async_session.add(
            SrsCardModel(
                user_id=user_id,
                term_id=index,
                language="en",
                due_at=now - offset,
                fsrs_state={"step": index},
            ),
        )
    await async_session.commit()


async def test_create_card_endpoint_initializes_fsrs_state(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_create_card",
        email="create-card@example.com",
    )

    response = await auth_client.post(
        "/api/v1/srs_cards",
        headers=auth_headers,
        json={"term_id": 501, "language": "en"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["term_id"] == 501
    assert payload["language"] == "en"
    assert payload["reps"] == 0
    assert payload["lapses"] == 0
    assert payload["stability"] is None
    assert payload["difficulty"] is None
    assert payload["fsrs_state"]["state"] == 1
    assert payload["fsrs_state"]["step"] == 0


async def test_review_card_endpoint_updates_schedule_and_creates_review_log(
    auth_client: AsyncClient,
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_review_card",
        email="review-card@example.com",
    )
    create_response = await auth_client.post(
        "/api/v1/srs_cards",
        headers=auth_headers,
        json={"term_id": 601, "language": "jp"},
    )
    created_card = create_response.json()
    session_id = str(uuid4())

    response = await auth_client.post(
        f"/api/v1/srs_cards/{created_card['id']}/review",
        headers=auth_headers,
        json={"rating": 3, "response_time_ms": 1400, "session_id": session_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created_card["id"]
    assert payload["language"] == "jp"
    assert payload["reps"] == 1
    assert payload["lapses"] == 0
    assert payload["stability"] is not None
    assert payload["difficulty"] is not None
    assert payload["next_due_at"] == payload["due_at"]
    assert payload["interval_display"]

    review_rows = await async_session.execute(select(SrsReviewModel))
    stored_review = review_rows.scalar_one()
    assert stored_review.card_id == created_card["id"]
    assert stored_review.rating == 3
    assert stored_review.response_time_ms == 1400
    assert str(stored_review.session_id) == session_id


async def test_create_card_endpoint_rejects_duplicate_term_language(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_duplicate_card",
        email="duplicate-card@example.com",
    )

    first_response = await auth_client.post(
        "/api/v1/srs_cards",
        headers=auth_headers,
        json={"term_id": 501, "language": "en"},
    )
    duplicate_response = await auth_client.post(
        "/api/v1/srs_cards",
        headers=auth_headers,
        json={"term_id": 501, "language": "en"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "duplicate_card"


async def test_queue_stats_endpoint_returns_due_and_overdue_counts(
    auth_client: AsyncClient,
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_queue_stats",
        email="queue-stats@example.com",
    )
    await seed_srs_cards(
        async_session,
        auth_client,
        auth_headers,
        [timedelta(hours=2), timedelta(days=2), timedelta(days=5)],
    )

    response = await auth_client.get("/api/v1/srs_cards/queue-stats", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "due_count": 3,
        "estimated_minutes": 1,
        "has_overdue": True,
        "overdue_count": 2,
    }


async def test_queue_endpoint_returns_full_queue_with_pagination(
    auth_client: AsyncClient,
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_queue_full",
        email="queue-full@example.com",
    )
    await seed_srs_cards(
        async_session,
        auth_client,
        auth_headers,
        [timedelta(days=5), timedelta(days=3), timedelta(days=1), timedelta(hours=2)],
    )

    response = await auth_client.get(
        "/api/v1/srs_cards/queue?mode=full&limit=2&offset=1",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["total_count"] == 4
    assert response.json()["limit"] == 2
    assert response.json()["offset"] == 1
    assert response.json()["mode"] == "full"
    assert [item["term_id"] for item in response.json()["items"]] == [2, 3]


async def test_due_alias_returns_thirty_most_overdue_cards_for_catchup(
    auth_client: AsyncClient,
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_queue_catchup",
        email="queue-catchup@example.com",
    )
    await seed_srs_cards(
        async_session,
        auth_client,
        auth_headers,
        [timedelta(days=140 - index) for index in range(45)],
    )

    response = await auth_client.get(
        "/api/v1/srs_cards/due?mode=catchup&limit=30&offset=9",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "catchup"
    assert response.json()["limit"] == 30
    assert response.json()["offset"] == 0
    assert response.json()["total_count"] == 45
    assert len(response.json()["items"]) == 30
    assert [item["term_id"] for item in response.json()["items"][:3]] == [1, 2, 3]
    assert response.json()["items"][-1]["term_id"] == 30
