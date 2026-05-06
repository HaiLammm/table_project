from typing import Literal

from pydantic import BaseModel, Field


class VocabularyRequestCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    language: Literal["en", "jp"]
    level: str = Field(...)
    count: int = Field(..., ge=1, le=50)


class EnrichedTermResponse(BaseModel):
    term_id: int | None = None
    candidate_id: str | None = None
    term: str
    language: str
    definition: str | None = None
    ipa: str | None = None
    cefr_level: str | None = None
    jlpt_level: int | None = None
    examples: list[str] = Field(default_factory=list)
    source: str
    validated_against_jmdict: bool = False


class VocabularyRequestPreviewResponse(BaseModel):
    preview_id: str | None = None
    terms: list[EnrichedTermResponse]
    corpus_match_count: int
    gap_count: int
    requested_count: int


class VocabularyRequestConfirm(BaseModel):
    preview_id: str
    selected_candidate_ids: list[str] = Field(..., min_length=1)


class VocabularyRequestConfirmResponse(BaseModel):
    added_count: int
    skipped_count: int
