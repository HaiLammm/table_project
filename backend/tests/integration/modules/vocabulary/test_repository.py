from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.app.db.base import Base
from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl


@pytest_asyncio.fixture
async def vocabulary_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert VocabularyTermModel.__table__ is not None
    assert VocabularyDefinitionModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def test_vocabulary_repository_create_get_search_and_children(
    vocabulary_schema: None,
    async_session: AsyncSession,
) -> None:
    repository = VocabularyRepositoryImpl(async_session)

    root = await repository.create_term(
        VocabularyTerm(term="IT", language="en", part_of_speech="category"),
    )
    category = await repository.create_term(
        VocabularyTerm(
            term="Networking",
            language="en",
            parent_id=root.id,
            part_of_speech="category",
        ),
    )
    term = await repository.create_term(
        VocabularyTerm(
            term="network protocol",
            language="en",
            parent_id=category.id,
            part_of_speech="noun",
        ),
    )
    await repository.create_definition(
        VocabularyDefinition(
            term_id=term.id,
            language="en",
            definition="A set of rules for network communication.",
            examples=["TCP is a protocol."],
            source="seed",
        ),
    )

    loaded = await repository.get_term_by_id(term.id)
    search_results = await repository.search_terms("protocol")
    children = await repository.get_children(category.id)

    assert loaded is not None
    assert loaded.term == "network protocol"
    assert loaded.definitions[0].definition == "A set of rules for network communication."
    assert [result.id for result in search_results] == [term.id]
    assert [child.term for child in children] == ["network protocol"]


async def test_vocabulary_repository_bulk_create_terms_is_idempotent(
    vocabulary_schema: None,
    async_session: AsyncSession,
) -> None:
    repository = VocabularyRepositoryImpl(async_session)
    parent = await repository.create_term(
        VocabularyTerm(term="TOEIC", language="en", part_of_speech="category"),
    )
    batch = [
        VocabularyTerm(
            term="invoice",
            language="en",
            parent_id=parent.id,
            part_of_speech="noun",
            definitions=[
                VocabularyDefinition(
                    language="en",
                    definition="A bill sent to a customer.",
                    source="seed",
                    examples=["The supplier emailed the invoice."],
                ),
            ],
        ),
    ]

    first_insert = await repository.bulk_create_terms(batch)
    second_insert = await repository.bulk_create_terms(batch)

    term_count = await async_session.scalar(select(func.count(VocabularyTermModel.id)))
    definition_count = await async_session.scalar(
        select(func.count(VocabularyDefinitionModel.id)),
    )

    assert len(first_insert) == 1
    assert len(second_insert) == 1
    assert first_insert[0].id == second_insert[0].id
    assert term_count == 2
    assert definition_count == 1
