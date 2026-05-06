from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base, TimestampMixin


class VocabularyTermModel(TimestampMixin, Base):
    __tablename__ = "vocabulary_terms"
    __table_args__ = (
        CheckConstraint("language IN ('en', 'jp')", name="ck_vocabulary_terms_language"),
        UniqueConstraint("term", "language", name="uq_vocabulary_terms_term_language"),
        Index("ix_vocabulary_terms_parent_id", "parent_id"),
        Index("ix_vocabulary_terms_language", "language"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("vocabulary_terms.id", ondelete="CASCADE"),
        nullable=True,
    )
    cefr_level: Mapped[str | None] = mapped_column(String(5), nullable=True)
    jlpt_level: Mapped[str | None] = mapped_column(String(5), nullable=True)
    part_of_speech: Mapped[str | None] = mapped_column(String(30), nullable=True)


class VocabularyDefinitionModel(Base):
    __tablename__ = "vocabulary_definitions"
    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'jp')",
            name="ck_vocabulary_definitions_language",
        ),
        CheckConstraint(
            "source IN ('seed', 'user', 'llm')",
            name="ck_vocabulary_definitions_source",
        ),
        Index("ix_vocabulary_definitions_term_id", "term_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        ForeignKey("vocabulary_terms.id", ondelete="CASCADE"),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    ipa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    examples: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    validated_against_jmdict: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
