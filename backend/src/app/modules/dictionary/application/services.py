import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


def _build_jamdict() -> Any:
    from jamdict import Jamdict  # type: ignore[import-untyped]

    return Jamdict()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


@dataclass(frozen=True, slots=True)
class JMdictLookupEntry:
    headword: str
    glosses: tuple[str, ...]


class JMdictService:
    def __init__(self, dictionary_factory: Any | None = None) -> None:
        self._dictionary_factory = dictionary_factory or _build_jamdict
        self._dictionary: Any | None = None
        self._cached_lookup = lru_cache(maxsize=10000)(self._lookup_uncached)

    def _get_dictionary(self) -> Any:
        if self._dictionary is None:
            self._dictionary = self._dictionary_factory()

        return self._dictionary

    def lookup(self, term: str) -> tuple[JMdictLookupEntry, ...]:
        return self._cached_lookup(term)

    def _lookup_uncached(self, term: str) -> tuple[JMdictLookupEntry, ...]:
        result = self._get_dictionary().lookup(term)
        return tuple(self._normalize_entry(entry) for entry in result.entries)

    def is_definition_valid(self, term: str, definition: str) -> bool:
        normalized_definition = _normalize_text(definition)
        if not normalized_definition:
            return False

        for entry in self.lookup(term):
            for gloss in entry.glosses:
                normalized_gloss = _normalize_text(gloss)
                if not normalized_gloss:
                    continue
                if (
                    normalized_definition in normalized_gloss
                    or normalized_gloss in normalized_definition
                ):
                    return True

        return False

    @staticmethod
    def _normalize_entry(entry: Any) -> JMdictLookupEntry:
        glosses: list[str] = []
        for sense in entry.senses:
            glosses.extend(str(gloss) for gloss in getattr(sense, "gloss", []))

        return JMdictLookupEntry(headword=entry.text(), glosses=tuple(glosses))


async def preload_jmdict(service: JMdictService) -> None:
    await asyncio.to_thread(service.lookup, "protocol")
