import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.auth.domain.entities import DataExport, User, UserPreferences
from src.app.modules.auth.domain.exceptions import DataExportNotFoundError, UserNotFoundError
from src.app.modules.auth.domain.interfaces import (
    DataExportRepository,
    UserPreferencesRepository,
    UserRepository,
)
from src.app.modules.auth.domain.value_objects import (
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
    UserTier,
)
from src.app.modules.auth.infrastructure.models import (
    DataExportModel,
    UserModel,
    UserPreferencesModel,
)

logger = structlog.get_logger().bind(module="auth_repository")


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        clerk_id=model.clerk_id,
        email=model.email,
        display_name=model.display_name,
        tier=UserTier(model.tier),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_preferences_domain(model: UserPreferencesModel) -> UserPreferences:
    return UserPreferences(
        id=model.id,
        user_id=model.user_id,
        learning_goal=LearningGoal(model.learning_goal),
        english_level=EnglishLevel(model.english_level),
        japanese_level=JapaneseLevel(model.japanese_level),
        daily_study_minutes=model.daily_study_minutes,
        it_domain=ITDomain(model.it_domain),
        notification_email=model.notification_email,
        notification_review_reminder=model.notification_review_reminder,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_data_export_domain(model: DataExportModel) -> DataExport:
    return DataExport(
        id=model.id,
        user_id=model.user_id,
        status=model.status,
        file_path=model.file_path,
        created_at=model.created_at,
        expires_at=model.expires_at,
    )


class SqlAlchemyUserRepository(UserRepository, UserPreferencesRepository, DataExportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.clerk_id == clerk_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def create(self, user: User) -> User:
        model = UserModel(
            clerk_id=user.clerk_id,
            email=user.email,
            display_name=user.display_name,
            tier=user.tier.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_user_created", clerk_id=model.clerk_id)
        return _to_domain(model)

    async def update(self, user: User) -> User:
        if user.id is None:
            msg = "User id is required for updates"
            raise UserNotFoundError(msg)

        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        model.clerk_id = user.clerk_id
        model.email = user.email
        model.display_name = user.display_name
        model.tier = user.tier.value

        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_user_updated", clerk_id=model.clerk_id)
        return _to_domain(model)

    async def delete_by_id(self, user_id: int) -> None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        if model is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        await self._session.delete(model)
        await self._session.commit()
        logger.info("auth_user_deleted", user_id=user_id)

    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        result = await self._session.execute(
            select(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_preferences_domain(model)

    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        result = await self._session.execute(
            select(UserPreferencesModel).where(
                UserPreferencesModel.user_id == preferences.user_id
            ),
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = UserPreferencesModel(user_id=preferences.user_id)
            self._session.add(model)

        model.learning_goal = preferences.learning_goal.value
        model.english_level = preferences.english_level.value
        model.japanese_level = preferences.japanese_level.value
        model.daily_study_minutes = preferences.daily_study_minutes
        model.it_domain = preferences.it_domain.value
        model.notification_email = preferences.notification_email
        model.notification_review_reminder = preferences.notification_review_reminder

        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_user_preferences_upserted", user_id=model.user_id)
        return _to_preferences_domain(model)

    async def delete_by_user_id(self, user_id: int) -> None:
        await self._session.execute(
            delete(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id),
        )
        await self._session.commit()

        logger.info("auth_user_preferences_deleted", user_id=user_id)

    async def create_data_export(self, data_export: DataExport) -> DataExport:
        model = DataExportModel(
            user_id=data_export.user_id,
            status=data_export.status,
            file_path=data_export.file_path,
            expires_at=data_export.expires_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_data_export_created", export_id=model.id, user_id=model.user_id)
        return _to_data_export_domain(model)

    async def get_data_export_by_id(self, export_id: int) -> DataExport | None:
        result = await self._session.execute(
            select(DataExportModel).where(DataExportModel.id == export_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_data_export_domain(model)

    async def list_data_exports_by_user_id(self, user_id: int) -> list[DataExport]:
        result = await self._session.execute(
            select(DataExportModel)
            .where(DataExportModel.user_id == user_id)
            .order_by(DataExportModel.created_at.desc()),
        )
        return [_to_data_export_domain(model) for model in result.scalars().all()]

    async def update_data_export(self, data_export: DataExport) -> DataExport:
        if data_export.id is None:
            msg = "Data export id is required for updates"
            raise DataExportNotFoundError(msg)

        result = await self._session.execute(
            select(DataExportModel).where(DataExportModel.id == data_export.id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Data export not found"
            raise DataExportNotFoundError(msg)

        model.status = data_export.status
        model.file_path = data_export.file_path
        model.expires_at = data_export.expires_at

        await self._session.commit()
        await self._session.refresh(model)

        logger.info("auth_data_export_updated", export_id=model.id, user_id=model.user_id)
        return _to_data_export_domain(model)

    async def delete_data_exports_by_user_id(self, user_id: int) -> None:
        await self._session.execute(
            delete(DataExportModel).where(DataExportModel.user_id == user_id)
        )
        await self._session.commit()

        logger.info("auth_data_exports_deleted", user_id=user_id)
