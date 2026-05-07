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
COLLECTIONS_HEAD_REVISION = "7f8e9d1a2b3c"

SchemaSnapshot = dict[str, Any]


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


async def _inspect_collections_schema() -> SchemaSnapshot:
    engine = create_async_engine(settings.test_database_url, echo=False)
    async with engine.connect() as connection:
        schema = await connection.run_sync(
            lambda sync_connection: {
                "tables": set(inspect(sync_connection).get_table_names()),
                "collections_columns": {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("collections")
                },
                "collection_terms_columns": {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("collection_terms")
                },
                "collections_indexes": {
                    index["name"] for index in inspect(sync_connection).get_indexes("collections")
                },
                "collection_terms_indexes": {
                    index["name"]
                    for index in inspect(sync_connection).get_indexes("collection_terms")
                },
                "collections_unique_constraints": {
                    constraint["name"]
                    for constraint in inspect(sync_connection).get_unique_constraints(
                        "collections"
                    )
                },
                "collection_terms_unique_constraints": {
                    constraint["name"]
                    for constraint in inspect(sync_connection).get_unique_constraints(
                        "collection_terms"
                    )
                },
                "collection_terms_foreign_keys": inspect(sync_connection).get_foreign_keys(
                    "collection_terms"
                ),
            }
        )
    await engine.dispose()
    return cast(SchemaSnapshot, schema)


def test_collections_migration_creates_tables_and_constraints(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", settings.test_database_url)
    _run_async(_reset_public_schema())
    alembic_config = _build_alembic_config()

    try:
        command.upgrade(alembic_config, COLLECTIONS_HEAD_REVISION)
        schema = _run_async(_inspect_collections_schema())
    finally:
        _run_async(_reset_public_schema())

    assert {"collections", "collection_terms"}.issubset(schema["tables"])
    assert {
        "id",
        "user_id",
        "name",
        "icon",
        "created_at",
        "updated_at",
    }.issubset(schema["collections_columns"])
    assert {"id", "collection_id", "term_id", "added_at"}.issubset(
        schema["collection_terms_columns"]
    )
    assert "ix_collections_user_id" in schema["collections_indexes"]
    assert "ix_collection_terms_collection_id" in schema["collection_terms_indexes"]
    assert "ix_collection_terms_term_id" in schema["collection_terms_indexes"]
    assert "uq_collections_user_id_name" in schema["collections_unique_constraints"]
    assert (
        "uq_collection_terms_collection_id_term_id"
        in schema["collection_terms_unique_constraints"]
    )

    foreign_keys = {fk["referred_table"]: fk for fk in schema["collection_terms_foreign_keys"]}
    assert foreign_keys["collections"].get("options", {}).get("ondelete") == "CASCADE"
    assert foreign_keys["vocabulary_terms"].get("options", {}).get("ondelete") == "CASCADE"
