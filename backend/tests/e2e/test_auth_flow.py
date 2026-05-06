import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient
from svix.webhooks import Webhook

from src.app.core import security as security_module
from src.app.core.config import settings


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


async def test_auth_flow_webhook_sync_and_current_user(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
            "id": "user_123",
            "email_addresses": [
                {
                    "id": "email_123",
                    "email_address": "lem@example.com",
                },
            ],
            "primary_email_address_id": "email_123",
            "first_name": "Lem",
            "last_name": "Nguyen",
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
    assert webhook_response.json()["status"] == "synced"
    assert webhook_response.json()["user"]["email"] == "lem@example.com"

    access_token = jwt.encode(
        {
            "sub": "user_123",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        private_key,
        algorithm="RS256",
    )

    me_response = await auth_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["clerk_id"] == "user_123"
    assert me_response.json()["email"] == "lem@example.com"
    assert me_response.json()["tier"] == "free"


async def test_auth_flow_gets_defaults_and_updates_user_preferences(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
            "id": "user_456",
            "email_addresses": [
                {
                    "id": "email_456",
                    "email_address": "settings@example.com",
                },
            ],
            "primary_email_address_id": "email_456",
            "first_name": "Settings",
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
            "sub": "user_456",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        private_key,
        algorithm="RS256",
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    initial_preferences_response = await auth_client.get(
        "/api/v1/users/me/preferences",
        headers=auth_headers,
    )

    assert initial_preferences_response.status_code == 200
    assert initial_preferences_response.json() == {
        "learning_goal": "general",
        "english_level": "beginner",
        "japanese_level": "none",
        "daily_study_minutes": 15,
        "it_domain": "general_it",
        "notification_email": True,
        "notification_review_reminder": True,
    }

    update_response = await auth_client.put(
        "/api/v1/users/me/preferences",
        headers=auth_headers,
        json={
            "learning_goal": "workplace",
            "english_level": "intermediate",
            "japanese_level": "n3",
            "daily_study_minutes": 30,
            "it_domain": "backend",
            "notification_email": False,
            "notification_review_reminder": False,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "learning_goal": "workplace",
        "english_level": "intermediate",
        "japanese_level": "n3",
        "daily_study_minutes": 30,
        "it_domain": "backend",
        "notification_email": False,
        "notification_review_reminder": False,
    }

    refreshed_preferences_response = await auth_client.get(
        "/api/v1/users/me/preferences",
        headers=auth_headers,
    )

    assert refreshed_preferences_response.status_code == 200
    assert refreshed_preferences_response.json() == update_response.json()
