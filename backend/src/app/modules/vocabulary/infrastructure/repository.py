import structlog
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.domain.interfaces import VocabularyRepository
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)

logger = structlog.get_logger().bind(module="vocabulary_repository")


def _to_definition_domain(model: VocabularyDefinitionModel) -> VocabularyDefinition:
    return VocabularyDefinition(
        id=model.id,
        term_id=model.term_id,
        language=model.language,
        definition=model.definition,
        ipa=model.ipa,
        examples=list(model.examples),
        source=model.source,
        validated_against_jmdict=model.validated_against_jmdict,
        created_at=model.created_at,
    )


def _to_term_domain(
    model: VocabularyTermModel,
    definitions: list[VocabularyDefinition],
) -> VocabularyTerm:
    return VocabularyTerm(
        id=model.id,
        term=model.term,
        language=model.language,
        parent_id=model.parent_id,
        cefr_level=model.cefr_level,
        jlpt_level=model.jlpt_level,
        part_of_speech=model.part_of_speech,
        definitions=definitions,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class VocabularyRepositoryImpl(VocabularyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_term(self, term: VocabularyTerm) -> VocabularyTerm:
        model = VocabularyTermModel(
            term=term.term,
            language=term.language,
            parent_id=term.parent_id,
            cefr_level=term.cefr_level,
            jlpt_level=term.jlpt_level,
            part_of_speech=term.part_of_speech,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info("vocabulary_term_created", term=model.term, language=model.language)
        return _to_term_domain(model, [])

    async def create_definition(
        self,
        definition: VocabularyDefinition,
    ) -> VocabularyDefinition:
        if definition.term_id is None:
            msg = "Definition term_id is required"
            raise ValueError(msg)

        model = VocabularyDefinitionModel(
            term_id=definition.term_id,
            language=definition.language,
            definition=definition.definition,
            ipa=definition.ipa,
            examples=list(definition.examples),
            source=definition.source,
            validated_against_jmdict=definition.validated_against_jmdict,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info(
            "vocabulary_definition_created", term_id=model.term_id, language=model.language
        )
        return _to_definition_domain(model)

    async def get_term_by_id(self, term_id: int | None) -> VocabularyTerm | None:
        if term_id is None:
            return None

        result = await self._session.execute(
            select(VocabularyTermModel).where(VocabularyTermModel.id == term_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        definitions = await self._load_definitions([term_id])
        return _to_term_domain(model, definitions.get(term_id, []))

    async def get_term_by_value(self, term: str, language: str) -> VocabularyTerm | None:
        result = await self._session.execute(
            select(VocabularyTermModel).where(
                VocabularyTermModel.term == term,
                VocabularyTermModel.language == language,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        definitions = await self._load_definitions([model.id])
        return _to_term_domain(model, definitions.get(model.id, []))

    async def search_terms(
        self,
        query: str,
        *,
        language: str | None = None,
        limit: int = 20,
    ) -> list[VocabularyTerm]:
        vector = func.to_tsvector("simple", VocabularyTermModel.term)
        ts_query = func.plainto_tsquery("simple", query)
        statement = select(VocabularyTermModel).where(vector.op("@@")(ts_query))
        if language is not None:
            statement = statement.where(VocabularyTermModel.language == language)

        result = await self._session.execute(
            statement.order_by(
                func.ts_rank_cd(vector, ts_query).desc(), VocabularyTermModel.id.asc()
            ).limit(limit),
        )
        return [_to_term_domain(model, []) for model in result.scalars().all()]

    async def get_children(self, parent_id: int | None) -> list[VocabularyTerm]:
        result = await self._session.execute(
            select(VocabularyTermModel)
            .where(VocabularyTermModel.parent_id == parent_id)
            .order_by(VocabularyTermModel.term.asc(), VocabularyTermModel.id.asc()),
        )
        return [_to_term_domain(model, []) for model in result.scalars().all()]

    async def list_terms(
        self,
        *,
        page: int,
        page_size: int,
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[VocabularyTerm], int]:
        statement = select(VocabularyTermModel)
        count_statement = select(func.count(VocabularyTermModel.id))

        if cefr_level is not None:
            statement = statement.where(VocabularyTermModel.cefr_level == cefr_level)
            count_statement = count_statement.where(VocabularyTermModel.cefr_level == cefr_level)

        if jlpt_level is not None:
            statement = statement.where(VocabularyTermModel.jlpt_level == jlpt_level)
            count_statement = count_statement.where(VocabularyTermModel.jlpt_level == jlpt_level)

        if parent_id is not None:
            statement = statement.where(VocabularyTermModel.parent_id == parent_id)
            count_statement = count_statement.where(VocabularyTermModel.parent_id == parent_id)

        offset = (page - 1) * page_size
        statement = (
            statement.order_by(VocabularyTermModel.term.asc(), VocabularyTermModel.id.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self._session.execute(statement)
        count_result = await self._session.execute(count_statement)

        terms = [_to_term_domain(model, []) for model in result.scalars().all()]
        total = count_result.scalar_one()

        return terms, total

    async def bulk_create_terms(self, terms: list[VocabularyTerm]) -> list[VocabularyTerm]:
        persisted_ids: list[int] = []
        created_count = 0
        skipped_count = 0

        for term in terms:
            insert_result = await self._session.execute(
                insert(VocabularyTermModel)
                .values(
                    term=term.term,
                    language=term.language,
                    parent_id=term.parent_id,
                    cefr_level=term.cefr_level,
                    jlpt_level=term.jlpt_level,
                    part_of_speech=term.part_of_speech,
                )
                .on_conflict_do_nothing(index_elements=["term", "language"])
                .returning(VocabularyTermModel.id),
            )
            term_id = insert_result.scalar_one_or_none()
            created = term_id is not None

            if term_id is None:
                existing_id_result = await self._session.execute(
                    select(VocabularyTermModel.id).where(
                        VocabularyTermModel.term == term.term,
                        VocabularyTermModel.language == term.language,
                    ),
                )
                term_id = existing_id_result.scalar_one()
                skipped_count += 1
            else:
                created_count += 1

            if created and term.definitions:
                await self._session.execute(
                    insert(VocabularyDefinitionModel),
                    [
                        {
                            "term_id": term_id,
                            "language": definition.language,
                            "definition": definition.definition,
                            "ipa": definition.ipa,
                            "examples": list(definition.examples),
                            "source": definition.source,
                            "validated_against_jmdict": definition.validated_against_jmdict,
                        }
                        for definition in term.definitions
                    ],
                )

            persisted_ids.append(term_id)

        await self._session.commit()
        logger.info(
            "vocabulary_terms_bulk_upserted",
            created_count=created_count,
            skipped_count=skipped_count,
        )

        persisted_terms: list[VocabularyTerm] = []
        for term_id in persisted_ids:
            loaded = await self.get_term_by_id(term_id)
            if loaded is not None:
                persisted_terms.append(loaded)

        return persisted_terms

    async def _load_definitions(
        self,
        term_ids: list[int],
    ) -> dict[int, list[VocabularyDefinition]]:
        result = await self._session.execute(
            select(VocabularyDefinitionModel)
            .where(VocabularyDefinitionModel.term_id.in_(term_ids))
            .order_by(VocabularyDefinitionModel.id.asc()),
        )

        definitions_by_term_id: dict[int, list[VocabularyDefinition]] = {
            term_id: [] for term_id in term_ids
        }
        for model in result.scalars().all():
            definitions_by_term_id.setdefault(model.term_id, []).append(
                _to_definition_domain(model),
            )

        return definitions_by_term_id
