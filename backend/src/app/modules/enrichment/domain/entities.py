from dataclasses import dataclass


@dataclass
class EnrichedTerm:
    term_id: int | None
    term: str
    language: str
    definition: str | None
    ipa: str | None
    cefr_level: str | None
    jlpt_level: int | None
    examples: list[str]
    source: str
    candidate_id: str | None = None
    preview_id: str | None = None
    validated_against_jmdict: bool = False
