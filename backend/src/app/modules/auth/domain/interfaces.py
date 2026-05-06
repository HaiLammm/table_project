from abc import ABC, abstractmethod

from src.app.modules.auth.domain.entities import User, UserPreferences


class UserRepository(ABC):
    @abstractmethod
    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> User:
        raise NotImplementedError


class UserPreferencesRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        raise NotImplementedError
