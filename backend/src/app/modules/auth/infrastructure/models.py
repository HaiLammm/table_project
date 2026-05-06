from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base, TimestampMixin
from src.app.modules.auth.domain.value_objects import UserTier


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_clerk_id", "clerk_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserTier.FREE.value,
        server_default=text("'free'"),
    )


class UserPreferencesModel(TimestampMixin, Base):
    __tablename__ = "user_preferences"
    __table_args__ = (Index("ix_user_preferences_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    learning_goal: Mapped[str] = mapped_column(String(50), nullable=False)
    english_level: Mapped[str] = mapped_column(String(20), nullable=False)
    japanese_level: Mapped[str] = mapped_column(String(10), nullable=False)
    daily_study_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15,
        server_default=text("15"),
    )
    it_domain: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="general_it",
        server_default=text("'general_it'"),
    )
    notification_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    notification_review_reminder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
