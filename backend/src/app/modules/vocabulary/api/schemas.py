from datetime import datetime

from pydantic import BaseModel, Field


class VocabularyDefinitionResponse(BaseModel):
    id: int
    language: str
    definition: str
    ipa: str | None = None
    examples: list[str] = Field(default_factory=list)
    source: str
    validated_against_jmdict: bool = False

    model_config = {"from_attributes": True}


class VocabularyTermResponse(BaseModel):
    id: int
    term: str
    language: str
    parent_id: int | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None
    definitions: list[VocabularyDefinitionResponse] = Field(default_factory=list)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VocabularyTermListResponse(BaseModel):
    items: list[VocabularyTermResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class VocabularySearchParams(BaseModel):
    query: str
    language: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class VocabularyFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    cefr_level: str | None = None
    jlpt_level: str | None = None
    parent_id: int | None = None
