from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    icon: str = Field(min_length=1, max_length=16)

    @field_validator("name", "icon")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Value cannot be empty"
            raise ValueError(msg)
        return stripped


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, min_length=1, max_length=16)

    @field_validator("name", "icon")
    @classmethod
    def validate_optional_non_empty_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            msg = "Value cannot be empty"
            raise ValueError(msg)
        return stripped

    @model_validator(mode="after")
    def validate_payload(self) -> "CollectionUpdate":
        if self.name is None and self.icon is None:
            msg = "At least one field must be provided"
            raise ValueError(msg)
        return self


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str
    term_count: int
    mastery_percent: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CollectionListResponse(BaseModel):
    items: list[CollectionResponse]


class AddTermRequest(BaseModel):
    term_id: int = Field(ge=1)


class AddTermsRequest(BaseModel):
    term_ids: list[int] = Field(min_length=1)


class AddTermsResponse(BaseModel):
    added: int
    skipped: int


class CollectionTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    term_id: int
    term: str
    language: str
    mastery_status: Literal["new", "learning", "mastered"]
    added_at: datetime | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None


class CollectionTermListResponse(BaseModel):
    items: list[CollectionTermResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class CollectionCSVImportError(BaseModel):
    row: int
    error: str


class CollectionCSVImportResponse(BaseModel):
    added: int
    skipped: int
    errors: list[CollectionCSVImportError]
