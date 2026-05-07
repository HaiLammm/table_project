from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(slots=True, kw_only=True)
class Collection:
    user_id: int
    name: str
    icon: str
    id: int | None = None
    term_count: int = 0
    mastery_percent: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class CollectionTerm:
    collection_id: int
    term_id: int
    id: int | None = None
    added_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class CollectionTermEntry:
    term_id: int
    term: str
    language: str
    mastery_status: Literal["new", "learning", "mastered"]
    added_at: datetime | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None
