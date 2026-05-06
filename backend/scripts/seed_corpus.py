import argparse
import asyncio
import json
import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import request

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.db.session import async_session_factory
from src.app.modules.dictionary.application.services import JMdictService
from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY_HIERARCHY: dict[str, dict[str, dict[str, Any]]] = {
    "IT": {
        "Networking": {},
        "Security": {},
        "Database": {},
        "DevOps": {},
    },
    "TOEIC": {
        "Business": {},
        "Finance": {},
        "Meetings": {},
        "Email": {},
    },
    "JLPT N3": {
        "Workplace": {},
        "Technology": {},
        "Daily Life": {},
    },
    "JLPT N2": {
        "Business": {},
        "Technology": {},
        "Documentation": {},
    },
}


class SeedDefinition(BaseModel):
    language: str
    definition: str
    ipa: str | None = None
    examples: list[str] = Field(default_factory=list)


class SeedTerm(BaseModel):
    term: str
    language: str
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str
    definitions: list[SeedDefinition] = Field(default_factory=list)


class SeedEnvelope(BaseModel):
    terms: list[SeedTerm] = Field(default_factory=list)


@dataclass(slots=True)
class SeedRunStats:
    categories_processed: int = 0
    terms_processed: int = 0
    jmdict_checked: int = 0
    jmdict_validated: int = 0


class SeedGenerator(Protocol):
    async def generate_terms(
        self,
        *,
        category_path: tuple[str, ...],
        target_count: int,
    ) -> list[SeedTerm]: ...


class DefinitionValidator(Protocol):
    def is_definition_valid(self, term: str, definition: str) -> bool: ...


class AnthropicSeedGenerator:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or ""
        self._model = model or os.getenv("VOCABULARY_SEED_MODEL") or "claude-3-5-haiku-latest"
        self._timeout_seconds = timeout_seconds

    async def generate_terms(
        self,
        *,
        category_path: tuple[str, ...],
        target_count: int,
    ) -> list[SeedTerm]:
        if not self._api_key:
            msg = "ANTHROPIC_API_KEY is required to generate the seeded vocabulary corpus"
            raise RuntimeError(msg)

        raw_payload = await asyncio.to_thread(
            self._request_seed_batch,
            category_path,
            target_count,
        )
        envelope = SeedEnvelope.model_validate_json(self._extract_json_payload(raw_payload))
        return envelope.terms

    def _request_seed_batch(
        self,
        category_path: tuple[str, ...],
        target_count: int,
    ) -> str:
        prompt = self._build_prompt(category_path=category_path, target_count=target_count)
        payload = json.dumps(
            {
                "model": self._model,
                "max_tokens": 8192,
                "temperature": 0.2,
                "system": (
                    "You generate clean JSON for vocabulary seeding. "
                    "Return only valid JSON with a top-level 'terms' array."
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
        ).encode("utf-8")
        http_request = request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "content-type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))

        return "\n".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )

    @staticmethod
    def _extract_json_payload(payload: str) -> str:
        stripped = payload.strip()
        if stripped.startswith("```"):
            lines = [line for line in stripped.splitlines() if not line.startswith("```")]
            return "\n".join(lines).strip()

        return stripped

    @staticmethod
    def _build_prompt(*, category_path: tuple[str, ...], target_count: int) -> str:
        path_text = " > ".join(category_path)
        return (
            f"Generate {target_count} vocabulary terms for category path: {path_text}. "
            "Cover IT, TOEIC, or JLPT vocabulary precisely for that category. "
            "Each item must include term, language (en or jp), optional cefr_level, optional "
            "jlpt_level, part_of_speech, and at least one definition with language, definition, "
            "optional ipa, and examples. Return strict JSON matching this schema: "
            '{"terms": [{"term": "", "language": "en", "cefr_level": null, '
            '"jlpt_level": null, "part_of_speech": "noun", "definitions": '
            '[{"language": "en", "definition": "", "ipa": null, "examples": []}]}]}.'
        )


async def seed_corpus(
    *,
    session_factory: async_sessionmaker[AsyncSession] = async_session_factory,
    generator: SeedGenerator | None = None,
    dictionary_service: DefinitionValidator | None = None,
    category_hierarchy: Mapping[str, Any] = DEFAULT_CATEGORY_HIERARCHY,
    target_term_count: int = 3200,
) -> SeedRunStats:
    logging.basicConfig(level=logging.INFO)
    generator = generator or AnthropicSeedGenerator()
    dictionary_service = dictionary_service or JMdictService()
    stats = SeedRunStats()
    leaf_count = max(_count_leaf_categories(category_hierarchy), 1)
    terms_per_leaf = max(1, target_term_count // leaf_count)

    async with session_factory() as session:
        repository = VocabularyRepositoryImpl(session)
        await _seed_category_tree(
            repository=repository,
            generator=generator,
            dictionary_service=dictionary_service,
            stats=stats,
            tree=category_hierarchy,
            parent_id=None,
            path=(),
            terms_per_leaf=terms_per_leaf,
        )

    logger.info(
        "seed_corpus_completed",
        extra={
            "categories_processed": stats.categories_processed,
            "terms_processed": stats.terms_processed,
            "jmdict_checked": stats.jmdict_checked,
            "jmdict_validated": stats.jmdict_validated,
        },
    )
    return stats


async def _seed_category_tree(
    *,
    repository: VocabularyRepositoryImpl,
    generator: SeedGenerator,
    dictionary_service: DefinitionValidator,
    stats: SeedRunStats,
    tree: Mapping[str, Any],
    parent_id: int | None,
    path: tuple[str, ...],
    terms_per_leaf: int,
) -> None:
    for category_name, children in tree.items():
        category_term = VocabularyTerm(
            term=category_name,
            language="en",
            parent_id=parent_id,
            part_of_speech="category",
        )
        persisted_category = (await repository.bulk_create_terms([category_term]))[0]
        stats.categories_processed += 1
        current_path = (*path, category_name)

        if isinstance(children, Mapping) and children:
            await _seed_category_tree(
                repository=repository,
                generator=generator,
                dictionary_service=dictionary_service,
                stats=stats,
                tree=children,
                parent_id=persisted_category.id,
                path=current_path,
                terms_per_leaf=terms_per_leaf,
            )
            continue

        generated_terms = await generator.generate_terms(
            category_path=current_path,
            target_count=terms_per_leaf,
        )
        prepared_terms: list[VocabularyTerm] = []
        for seed_term in generated_terms:
            existing_term = await repository.get_term_by_value(seed_term.term, seed_term.language)
            if existing_term is not None:
                continue

            prepared_terms.append(
                _build_vocabulary_term(
                    seed_term=seed_term,
                    parent_id=persisted_category.id,
                    dictionary_service=dictionary_service,
                    stats=stats,
                ),
            )

        stats.terms_processed += len(prepared_terms)
        if prepared_terms:
            await repository.bulk_create_terms(prepared_terms)
        logger.info(
            "seed_category_processed",
            extra={
                "category": " > ".join(current_path),
                "terms_processed": len(prepared_terms),
                "jmdict_checked": stats.jmdict_checked,
                "jmdict_validated": stats.jmdict_validated,
            },
        )


def _build_vocabulary_term(
    *,
    seed_term: SeedTerm,
    parent_id: int | None,
    dictionary_service: DefinitionValidator,
    stats: SeedRunStats,
) -> VocabularyTerm:
    definitions: list[VocabularyDefinition] = []
    for seed_definition in seed_term.definitions:
        validated_against_jmdict = False
        if seed_term.language == "jp":
            stats.jmdict_checked += 1
            validated_against_jmdict = dictionary_service.is_definition_valid(
                seed_term.term,
                seed_definition.definition,
            )
            if validated_against_jmdict:
                stats.jmdict_validated += 1

        definitions.append(
            VocabularyDefinition(
                language=seed_definition.language,
                definition=seed_definition.definition,
                ipa=seed_definition.ipa,
                examples=list(seed_definition.examples),
                source="seed",
                validated_against_jmdict=validated_against_jmdict,
            ),
        )

    return VocabularyTerm(
        term=seed_term.term,
        language=seed_term.language,
        parent_id=parent_id,
        cefr_level=seed_term.cefr_level,
        jlpt_level=seed_term.jlpt_level,
        part_of_speech=seed_term.part_of_speech,
        definitions=definitions,
    )


def _count_leaf_categories(tree: Mapping[str, Any]) -> int:
    count = 0
    for children in tree.values():
        if isinstance(children, Mapping) and children:
            count += _count_leaf_categories(children)
        else:
            count += 1

    return count


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the preloaded vocabulary corpus")
    parser.add_argument(
        "--target-term-count",
        type=int,
        default=3200,
        help="Total number of generated vocabulary terms across leaf categories.",
    )
    return parser


async def _run_from_cli() -> None:
    args = build_argument_parser().parse_args()
    await seed_corpus(target_term_count=args.target_term_count)


if __name__ == "__main__":
    asyncio.run(_run_from_cli())
