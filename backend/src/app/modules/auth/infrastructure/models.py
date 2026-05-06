from sqlalchemy import Index, Integer, String, text
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
