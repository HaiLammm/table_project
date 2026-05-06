import base64
import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from svix.webhooks import Webhook

from src.app.core import security as security_module
from src.app.core.config import settings
from src.app.main import app
from src.app.modules.auth.api.router import get_arq_pool
from src.app.modules.auth.infrastructure.models import (
    DataExportModel,
    UserModel,
    UserPreferencesModel,
)
from src.app.workers import export_worker as export_worker_module


class StubSigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class StubJwksClient:
    def __init__(self, key: object) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, _token: str) -> StubSigningKey:
        return StubSigningKey(self._key)


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[object, ...]]] = []

    async def enqueue_job(self, name: str, *args: object) -> None:
        self.jobs.append((name, args))


class FakeDeleteResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, status_code: int = 204) -> None:
        self.status_code = status_code
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)

    async def delete(self, url: str, headers: dict[str, str]) -> FakeDeleteResponse:
        self.calls.append((url, headers))
        return FakeDeleteResponse(self.status_code)


def build_svix_secret(raw_secret: bytes) -> str:
    return f"whsec_{base64.b64encode(raw_secret).decode()}"


async def create_authenticated_user(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    clerk_id: str,
    email: str,
) -> dict[str, str]:
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


async def test_data_export_request_status_and_download(
    auth_client: AsyncClient,
    async_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_pool = FakeArqPool()
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_arq_pool() -> FakeArqPool:
        return fake_pool

    app.dependency_overrides[get_arq_pool] = override_get_arq_pool
    monkeypatch.setattr(settings, "data_export_storage_path", tmp_path / "exports")
    monkeypatch.setattr(export_worker_module, "async_session_factory", session_factory)

    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_export_123",
        email="export@example.com",
    )

    export_response = await auth_client.post(
        "/api/v1/users/me/data-export",
        headers=auth_headers,
    )

    assert export_response.status_code == 200
    assert export_response.json()["status"] == "pending"

    export_id = export_response.json()["export_id"]
    assert fake_pool.jobs == [("process_data_export", (export_id,))]

    worker_result = await export_worker_module.process_data_export({}, export_id)
    assert worker_result == "ready"

    status_response = await auth_client.get(
        f"/api/v1/users/me/data-export/{export_id}",
        headers=auth_headers,
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "ready"
    assert status_response.json()["download_url"].endswith(
        f"/api/v1/users/me/data-export/{export_id}?download=true"
    )

    download_response = await auth_client.get(
        f"/api/v1/users/me/data-export/{export_id}?download=true",
        headers=auth_headers,
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/zip"

    with ZipFile(io.BytesIO(download_response.content)) as archive:
        assert sorted(archive.namelist()) == [
            "collections.json",
            "diagnostics.json",
            "learning_patterns.json",
            "preferences.json",
            "profile.json",
            "review_history.json",
            "vocabulary_terms.json",
        ]
        profile = json.loads(archive.read("profile.json"))

    assert profile["email"] == "export@example.com"


async def test_account_deletion_rejects_mismatched_confirmation_email(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_delete_mismatch",
        email="delete-mismatch@example.com",
    )

    delete_response = await auth_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=auth_headers,
        json={"confirmation_email": "wrong@example.com"},
    )

    assert delete_response.status_code == 400
    assert delete_response.json() == {
        "error": {
            "code": "account_deletion_error",
            "message": "Confirmation email does not match current user",
            "details": None,
        }
    }

    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    assert me_response.status_code == 200


async def test_account_deletion_removes_user_preferences_exports_and_user(
    auth_client: AsyncClient,
    async_engine: AsyncEngine,
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_pool = FakeArqPool()
    fake_http_client = FakeAsyncClient()
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_arq_pool() -> FakeArqPool:
        return fake_pool

    app.dependency_overrides[get_arq_pool] = override_get_arq_pool
    monkeypatch.setattr(settings, "data_export_storage_path", tmp_path / "exports")
    monkeypatch.setattr(settings, "clerk_secret_key", "sk_test_123")
    monkeypatch.setattr(export_worker_module, "async_session_factory", session_factory)
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: fake_http_client)

    auth_headers = await create_authenticated_user(
        auth_client,
        monkeypatch,
        clerk_id="user_delete_success",
        email="delete-success@example.com",
    )

    me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["id"]

    preferences_response = await auth_client.put(
        "/api/v1/users/me/preferences",
        headers=auth_headers,
        json={
            "learning_goal": "workplace",
            "english_level": "intermediate",
            "japanese_level": "n4",
            "daily_study_minutes": 30,
            "it_domain": "backend",
            "notification_email": False,
            "notification_review_reminder": True,
        },
    )
    assert preferences_response.status_code == 200

    export_response = await auth_client.post(
        "/api/v1/users/me/data-export",
        headers=auth_headers,
    )
    assert export_response.status_code == 200

    export_id = export_response.json()["export_id"]
    assert await export_worker_module.process_data_export({}, export_id) == "ready"

    export_file = tmp_path / "exports" / str(user_id) / f"{export_id}.zip"
    assert export_file.exists()

    delete_response = await auth_client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=auth_headers,
        json={"confirmation_email": "delete-success@example.com"},
    )

    assert delete_response.status_code == 204
    assert fake_http_client.calls == [
        (
            "https://api.clerk.com/v1/users/user_delete_success",
            {"Authorization": "Bearer sk_test_123"},
        ),
    ]
    assert not export_file.exists()

    user_result = await async_session.execute(select(UserModel).where(UserModel.id == user_id))
    preferences_result = await async_session.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id),
    )
    exports_result = await async_session.execute(
        select(DataExportModel).where(DataExportModel.user_id == user_id),
    )

    assert user_result.scalar_one_or_none() is None
    assert preferences_result.scalar_one_or_none() is None
    assert exports_result.scalar_one_or_none() is None

    deleted_me_response = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    assert deleted_me_response.status_code == 401
    assert deleted_me_response.json()["error"]["code"] == "user_not_found"
