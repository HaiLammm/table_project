from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class VocabularyDefinition:
    language: str
    definition: str
    source: str
    id: int | None = None
    term_id: int | None = None
    ipa: str | None = None
    examples: list[str] = field(default_factory=list)
    validated_against_jmdict: bool = False
    created_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class VocabularyTerm:
    term: str
    language: str
    id: int | None = None
    parent_id: int | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None
    definitions: list[VocabularyDefinition] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source: str | None = None
