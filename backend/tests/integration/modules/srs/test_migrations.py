from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, cast

from alembic.config import Config
from pytest import MonkeyPatch
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from src.app.core.config import settings

ALEMBIC_INI_PATH = Path(__file__).resolve().parents[4] / "alembic.ini"
SRS_BASELINE_REVISION = "5c2e3a4f9b11"
SRS_HEAD_REVISION = "b8d0a9c4e271"

SchemaSnapshot = dict[str, set[str]]


def _run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coroutine)


def _build_alembic_config() -> Config:
    return Config(str(ALEMBIC_INI_PATH))


async def _reset_public_schema() -> None:
    engine = create_async_engine(settings.test_database_url, echo=False)
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
        await connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
    await engine.dispose()


async def _insert_legacy_card() -> int:
    engine = create_async_engine(settings.test_database_url, echo=False)
    async with engine.begin() as connection:
        user_id = await connection.scalar(
            text(
                """
                INSERT INTO users (clerk_id, email, display_name, tier)
                VALUES (:clerk_id, :email, :display_name, 'free')
                RETURNING id
                """
            ),
            {
                "clerk_id": "legacy_srs_user",
                "email": "legacy-srs@example.com",
                "display_name": "Legacy SRS",
            },
        )
        if user_id is None:
            msg = "Legacy SRS user insert failed"
            raise AssertionError(msg)

        card_id = await connection.scalar(
            text(
                """
                INSERT INTO srs_cards (user_id, term_id, due_at, fsrs_state)
                VALUES (:user_id, :term_id, now() - interval '2 days', '{}'::jsonb)
                RETURNING id
                """
            ),
            {"user_id": int(user_id), "term_id": 9001},
        )
    await engine.dispose()

    if card_id is None:
        msg = "Legacy SRS card insert failed"
        raise AssertionError(msg)

    return int(card_id)


async def _inspect_srs_schema() -> SchemaSnapshot:
    engine = create_async_engine(settings.test_database_url, echo=False)
    async with engine.connect() as connection:
        schema = await connection.run_sync(
            lambda sync_connection: {
                "columns": {
                    column["name"] for column in inspect(sync_connection).get_columns("srs_cards")
                },
                "indexes": {
                    index["name"] for index in inspect(sync_connection).get_indexes("srs_cards")
                },
                "review_columns": {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("srs_reviews")
                },
                "review_indexes": {
                    index["name"] for index in inspect(sync_connection).get_indexes("srs_reviews")
                },
                "unique_constraints": {
                    constraint["name"]
                    for constraint in inspect(sync_connection).get_unique_constraints("srs_cards")
                },
                "tables": set(inspect(sync_connection).get_table_names()),
            }
        )
    await engine.dispose()
    return cast(SchemaSnapshot, schema)


async def _fetch_card(card_id: int) -> dict[str, Any]:
    engine = create_async_engine(settings.test_database_url, echo=False)
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT language, stability, difficulty, reps, lapses, fsrs_state
                FROM srs_cards
                WHERE id = :card_id
                """
            ),
            {"card_id": card_id},
        )
        row = result.mappings().one()
    await engine.dispose()
    return dict(row)


def test_srs_migration_backfills_legacy_cards_and_adds_constraints(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", settings.test_database_url)
    _run_async(_reset_public_schema())
    alembic_config = _build_alembic_config()

    try:
        command.upgrade(alembic_config, SRS_BASELINE_REVISION)
        legacy_card_id = _run_async(_insert_legacy_card())
        command.upgrade(alembic_config, SRS_HEAD_REVISION)

        schema = _run_async(_inspect_srs_schema())
        migrated_card = _run_async(_fetch_card(legacy_card_id))

        command.downgrade(alembic_config, "8b2c4d6e7f80")
        downgraded_schema = _run_async(_inspect_srs_schema())
    finally:
        _run_async(_reset_public_schema())

    migrated_fsrs_state = migrated_card["fsrs_state"]
    assert isinstance(migrated_fsrs_state, dict)

    assert "srs_reviews" in schema["tables"]
    assert {
        "id",
        "user_id",
        "term_id",
        "language",
        "fsrs_state",
        "due_at",
        "stability",
        "difficulty",
        "reps",
        "lapses",
        "created_at",
        "updated_at",
    }.issubset(schema["columns"])
    assert "ix_srs_cards_user_id_due_at" in schema["indexes"]
    assert "uq_srs_cards_user_id_term_id_language" in schema["unique_constraints"]
    assert {"session_length_s", "parallel_mode_active"}.issubset(schema["review_columns"])
    assert "ix_srs_reviews_user_reviewed" in schema["review_indexes"]
    assert "session_length_s" not in downgraded_schema["review_columns"]
    assert "parallel_mode_active" not in downgraded_schema["review_columns"]
    assert "ix_srs_reviews_user_reviewed" not in downgraded_schema["review_indexes"]
    assert migrated_card["language"] == "en"
    assert migrated_card["reps"] == 0
    assert migrated_card["lapses"] == 0
    assert migrated_fsrs_state["card_id"] == legacy_card_id
    assert migrated_fsrs_state["state"] == 1
    assert migrated_fsrs_state["due"]
