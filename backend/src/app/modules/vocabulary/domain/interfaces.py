from abc import ABC, abstractmethod

from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm


class VocabularyRepository(ABC):
    @abstractmethod
    async def create_term(self, term: VocabularyTerm) -> VocabularyTerm:
        raise NotImplementedError

    @abstractmethod
    async def create_definition(
        self,
        definition: VocabularyDefinition,
    ) -> VocabularyDefinition:
        raise NotImplementedError

    @abstractmethod
    async def get_term_by_id(self, term_id: int | None) -> VocabularyTerm | None:
        raise NotImplementedError

    @abstractmethod
    async def search_terms(
        self,
        query: str,
        *,
        language: str | None = None,
        limit: int = 20,
    ) -> list[VocabularyTerm]:
        raise NotImplementedError

    @abstractmethod
    async def get_children(self, parent_id: int | None) -> list[VocabularyTerm]:
        raise NotImplementedError

    @abstractmethod
    async def bulk_create_terms(self, terms: list[VocabularyTerm]) -> list[VocabularyTerm]:
        raise NotImplementedError

    @abstractmethod
    async def list_terms(
        self,
        *,
        page: int,
        page_size: int,
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[VocabularyTerm], int]:
        raise NotImplementedError

    @abstractmethod
    async def find_by_user_and_term(
        self,
        term: str,
        language: str,
        user_id: int | None = None,
    ) -> VocabularyTerm | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_value(self, term: str, language: str) -> VocabularyTerm | None:
        raise NotImplementedError
