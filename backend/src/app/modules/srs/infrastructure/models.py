from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base, TimestampMixin


class SrsCardModel(TimestampMixin, Base):
    __tablename__ = "srs_cards"
    __table_args__ = (
        CheckConstraint("language IN ('en', 'jp')", name="ck_srs_cards_language"),
        Index("ix_srs_cards_user_id_due_at", "user_id", "due_at"),
        UniqueConstraint(
            "user_id",
            "term_id",
            "language",
            name="uq_srs_cards_user_id_term_id_language",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    term_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
        server_default=text("'en'"),
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    fsrs_state: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    reps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    lapses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )


class SrsReviewModel(Base):
    __tablename__ = "srs_reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 4", name="ck_srs_reviews_rating"),
        Index("ix_srs_reviews_card_id", "card_id"),
        Index("ix_srs_reviews_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("srs_cards.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[PythonUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    previous_fsrs_state: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    previous_stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_lapses: Mapped[int | None] = mapped_column(Integer, nullable=True)
