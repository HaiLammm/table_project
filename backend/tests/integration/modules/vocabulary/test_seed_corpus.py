from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from scripts.seed_corpus import SeedDefinition, SeedTerm, seed_corpus
from src.app.db.base import Base
from src.app.modules.dictionary.application.services import JMdictService
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)


class FakeSeedGenerator:
    async def generate_terms(
        self,
        *,
        category_path: tuple[str, ...],
        target_count: int,
    ) -> list[SeedTerm]:
        assert target_count > 0
        if category_path[-1] != "Networking":
            return []

        return [
            SeedTerm(
                term="protocol",
                language="en",
                cefr_level="B2",
                jlpt_level=None,
                part_of_speech="noun",
                definitions=[
                    SeedDefinition(
                        language="en",
                        definition="A standard set of communication rules.",
                        ipa="/ˈprəʊ.tə.kɒl/",
                        examples=["HTTP is a protocol."],
                    ),
                ],
            ),
            SeedTerm(
                term="規約",
                language="jp",
                cefr_level=None,
                jlpt_level="N2",
                part_of_speech="noun",
                definitions=[
                    SeedDefinition(
                        language="en",
                        definition="agreement",
                        ipa=None,
                        examples=["会社の規約を確認する。"],
                    ),
                ],
            ),
        ]


class FakeJMdictService(JMdictService):
    def __init__(self) -> None:
        super().__init__(dictionary_factory=lambda: None)
        self.checked_terms: list[tuple[str, str]] = []

    def is_definition_valid(self, term: str, definition: str) -> bool:
        self.checked_terms.append((term, definition))
        return term == "規約" and definition == "agreement"


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


async def test_seed_corpus_creates_hierarchy_and_skips_existing_terms(
    vocabulary_schema: None,
    async_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    dictionary_service = FakeJMdictService()
    category_hierarchy: dict[str, dict[str, dict[str, object]]] = {"IT": {"Networking": {}}}

    await seed_corpus(
        session_factory=session_factory,
        generator=FakeSeedGenerator(),
        dictionary_service=dictionary_service,
        category_hierarchy=category_hierarchy,
        target_term_count=8,
    )
    await seed_corpus(
        session_factory=session_factory,
        generator=FakeSeedGenerator(),
        dictionary_service=dictionary_service,
        category_hierarchy=category_hierarchy,
        target_term_count=8,
    )

    async with session_factory() as session:
        terms = list(
            (
                await session.execute(
                    select(VocabularyTermModel).order_by(VocabularyTermModel.id.asc())
                )
            )
            .scalars()
            .all(),
        )
        definitions = list(
            (
                await session.execute(
                    select(VocabularyDefinitionModel).order_by(VocabularyDefinitionModel.id.asc()),
                )
            )
            .scalars()
            .all(),
        )

    assert [term.term for term in terms] == ["IT", "Networking", "protocol", "規約"]
    assert terms[1].parent_id == terms[0].id
    assert terms[2].parent_id == terms[1].id
    assert terms[3].parent_id == terms[1].id
    assert len(definitions) == 2
    assert definitions[0].validated_against_jmdict is False
    assert definitions[1].validated_against_jmdict is True
    assert dictionary_service.checked_terms == [("規約", "agreement")]
