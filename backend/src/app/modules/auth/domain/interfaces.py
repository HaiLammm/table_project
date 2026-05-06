from abc import ABC, abstractmethod

from src.app.modules.auth.domain.entities import DataExport, User, UserPreferences


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

    @abstractmethod
    async def delete_by_id(self, user_id: int) -> None:
        raise NotImplementedError


class UserPreferencesRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: int) -> None:
        raise NotImplementedError


class DataExportRepository(ABC):
    @abstractmethod
    async def create_data_export(self, data_export: DataExport) -> DataExport:
        raise NotImplementedError

    @abstractmethod
    async def get_data_export_by_id(self, export_id: int) -> DataExport | None:
        raise NotImplementedError

    @abstractmethod
    async def list_data_exports_by_user_id(self, user_id: int) -> list[DataExport]:
        raise NotImplementedError

    @abstractmethod
    async def update_data_export(self, data_export: DataExport) -> DataExport:
        raise NotImplementedError

    @abstractmethod
    async def delete_data_exports_by_user_id(self, user_id: int) -> None:
        raise NotImplementedError
