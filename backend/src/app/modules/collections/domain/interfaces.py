from abc import ABC, abstractmethod

from src.app.modules.collections.domain.entities import Collection, CollectionTermEntry


class CollectionRepository(ABC):
    @abstractmethod
    async def create(self, collection: Collection) -> Collection:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, collection_id: int, user_id: int) -> Collection | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[Collection]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, collection: Collection) -> Collection:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, collection_id: int, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_term_count(self, collection_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_mastery_percent(self, collection_id: int, user_id: int) -> int:
        raise NotImplementedError


class CollectionTermRepository(ABC):
    @abstractmethod
    async def add_term(self, collection_id: int, term_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_terms_bulk(self, collection_id: int, term_ids: list[int]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def remove_term(self, collection_id: int, term_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def term_exists_in_collection(self, collection_id: int, term_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_terms_by_collection(
        self,
        collection_id: int,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[CollectionTermEntry], int]:
        raise NotImplementedError
