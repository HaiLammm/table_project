from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import insert

from src.app.modules.collections.infrastructure.models import CollectionModel, CollectionTermModel
from src.app.modules.srs.infrastructure.models import SrsCardModel


async def create_test_user(auth_client, monkeypatch, *, clerk_id, email):
    import json
    import base64
    from uuid import uuid4

    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from svix.webhooks import Webhook

    from src.app.core import security as security_module
    from src.app.core.config import settings

    webhook_secret = f"whsec_{base64.b64encode(b'table-project-test-secret').decode()}"
    now = datetime.now(UTC)
    msg_id = f"msg_{uuid4().hex}"

    monkeypatch.setattr(settings, "clerk_webhook_secret", webhook_secret)
    monkeypatch.setattr(settings, "clerk_jwks_url", "https://clerk.test/.well-known/jwks.json")
    security_module.get_jwks_client.cache_clear()

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    class StubSigningKey:
        def __init__(self, key):
            self.key = key

    class StubJwksClient:
        def __init__(self, key):
            self._key = key

        def get_signing_key_from_jwt(self, _token):
            return StubSigningKey(self._key)

    monkeypatch.setattr(security_module, "get_jwks_client", lambda: StubJwksClient(public_key))

    webhook_payload = {
        "type": "user.created",
        "data": {
            "id": clerk_id,
            "email_addresses": [{"id": f"email_{uuid4().hex}", "email_address": email}],
            "primary_email_address_id": None,
            "first_name": "Collection",
            "last_name": "Test",
        },
    }
    webhook_body = json.dumps(webhook_payload)
    webhook_signature = Webhook(webhook_secret).sign(msg_id, now, webhook_body)

    await auth_client.post(
        "/api/v1/auth/webhook",
        content=webhook_body,
        headers={
            "content-type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": str(int(now.timestamp())),
            "svix-signature": webhook_signature,
        },
    )

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


async def seed_collection_with_terms(async_session, user_id, term_ids):
    result = await async_session.execute(
        insert(CollectionModel).values(user_id=user_id, name="Test Collection", icon="📚")
    )
    collection_id = result.inserted_primary_key[0]

    if term_ids:
        values = [{"collection_id": collection_id, "term_id": tid} for tid in term_ids]
        await async_session.execute(insert(CollectionTermModel).values(values))

    await async_session.commit()
    return collection_id


async def seed_srs_cards(async_session, user_id, term_ids, *, language="en", due_at=None):
    now = due_at or datetime.now(UTC)
    for idx, term_id in enumerate(term_ids):
        async_session.add(
            SrsCardModel(
                user_id=user_id,
                term_id=term_id,
                language=language,
                due_at=now - timedelta(hours=idx + 1),
                fsrs_state={"step": idx},
            )
        )
    await async_session.commit()


@pytest.mark.asyncio
async def test_queue_with_collection_id_returns_only_collection_cards(
    auth_client, async_session, monkeypatch
):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_queue_coll",
        email="queue-coll@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    term_ids = [9001, 9002, 9003, 9004]
    collection_id = await seed_collection_with_terms(async_session, user_id, term_ids[:2])
    await seed_srs_cards(async_session, user_id, term_ids)

    response = await auth_client.get(
        f"/api/v1/srs_cards/queue?mode=full&collection_id={collection_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    returned_term_ids = [item["term_id"] for item in data["items"]]
    assert set(returned_term_ids) == {9001, 9002}
    assert data["total_count"] == 2


@pytest.mark.asyncio
async def test_queue_without_collection_id_returns_all_cards(
    auth_client, async_session, monkeypatch
):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_queue_all",
        email="queue-all@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    term_ids = [9101, 9102, 9103]
    await seed_collection_with_terms(async_session, user_id, term_ids[:1])
    await seed_srs_cards(async_session, user_id, term_ids)

    response = await auth_client.get(
        "/api/v1/srs_cards/queue?mode=full",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3


@pytest.mark.asyncio
async def test_queue_stats_with_collection_id(auth_client, async_session, monkeypatch):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_stats_coll",
        email="stats-coll@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    term_ids = [9201, 9202, 9203]
    collection_id = await seed_collection_with_terms(async_session, user_id, term_ids)
    await seed_srs_cards(async_session, user_id, term_ids)

    response = await auth_client.get(
        f"/api/v1/srs_cards/queue-stats?collection_id={collection_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["due_count"] == 3


@pytest.mark.asyncio
async def test_create_cards_for_collection_creates_missing_cards(
    auth_client, async_session, monkeypatch
):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_create_coll",
        email="create-coll@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    term_ids = [9301, 9302, 9303]
    collection_id = await seed_collection_with_terms(async_session, user_id, term_ids)
    await seed_srs_cards(async_session, user_id, term_ids[:1])

    response = await auth_client.post(
        "/api/v1/srs_cards/cards/create-for-collection",
        headers=auth_headers,
        json={"collection_id": collection_id, "language": "en"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 2
    assert data["skipped_count"] == 0


@pytest.mark.asyncio
async def test_create_cards_for_collection_skips_existing(auth_client, async_session, monkeypatch):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_create_skip",
        email="create-skip@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    term_ids = [9401, 9402]
    collection_id = await seed_collection_with_terms(async_session, user_id, term_ids)
    await seed_srs_cards(async_session, user_id, term_ids)

    response = await auth_client.post(
        "/api/v1/srs_cards/cards/create-for-collection",
        headers=auth_headers,
        json={"collection_id": collection_id, "language": "en"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 0
    assert data["skipped_count"] == 0


@pytest.mark.asyncio
async def test_create_cards_for_collection_nonexistent_collection(auth_client, monkeypatch):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_create_nonexist",
        email="create-nonexist@example.com",
    )

    response = await auth_client.post(
        "/api/v1/srs_cards/cards/create-for-collection",
        headers=auth_headers,
        json={"collection_id": 999999, "language": "en"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_cards_for_collection_other_users_collection(
    auth_client, async_session, monkeypatch
):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_create_other1",
        email="create-other1@example.com",
    )
    auth_headers2 = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_create_other2",
        email="create-other2@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user1_id = me_response.json()["id"]

    term_ids = [9501, 9502]
    collection_id = await seed_collection_with_terms(async_session, user1_id, term_ids)

    response = await auth_client.post(
        "/api/v1/srs_cards/cards/create-for-collection",
        headers=auth_headers2,
        json={"collection_id": collection_id, "language": "en"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_empty_collection_returns_zero_cards(auth_client, async_session, monkeypatch):
    auth_headers = await create_test_user(
        auth_client,
        monkeypatch=monkeypatch,
        clerk_id="user_empty_coll",
        email="empty-coll@example.com",
    )
    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    collection_id = await seed_collection_with_terms(async_session, user_id, [])

    response = await auth_client.get(
        f"/api/v1/srs_cards/queue?mode=full&collection_id={collection_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert data["items"] == []
