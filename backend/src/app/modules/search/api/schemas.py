from pydantic import BaseModel

from src.app.modules.vocabulary.api.schemas import VocabularyTermResponse


class SearchPageResponse(BaseModel):
    id: str
    title: str
    href: str


class SearchCollectionResponse(BaseModel):
    id: str
    title: str
    href: str


class SearchResponse(BaseModel):
    pages: list[SearchPageResponse]
    collections: list[SearchCollectionResponse]
    words: list[VocabularyTermResponse]
