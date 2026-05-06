from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CSVRowPreview(BaseModel):
    row_number: int
    term: str | None
    language: str | None
    definition: str | None
    tags: str | None
    status: Literal["valid", "warning", "error"]
    error_message: str | None = None


class CSVImportPreviewResponse(BaseModel):
    total_rows: int
    valid_count: int
    warning_count: int
    error_count: int
    preview_rows: list[CSVRowPreview]
    detected_columns: list[str]


class CSVImportResultResponse(BaseModel):
    imported_count: int
    review_count: int
    duplicates_skipped: int
    errors: list[dict]


class VocabularyTermCreateRequest(BaseModel):
    term: str = Field(min_length=1, max_length=100)
    language: Literal["en", "jp"]
    definition: str | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None


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
