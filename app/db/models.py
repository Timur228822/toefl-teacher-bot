"""
SQLAlchemy ORM models for TOEFL Teacher.

Tables:
  - users          — registered Telegram users
  - practice_sessions — each practice attempt (reading / listening / speaking / writing)
  - user_settings   — per-user preferences
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""


# ── Enums ───────────────────────────────────────────────────


class SkillType(str, enum.Enum):
    READING = "reading"
    LISTENING = "listening"
    SPEAKING = "speaking"
    WRITING = "writing"


class ProficiencyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ── Models ──────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # relationships
    sessions: Mapped[list["PracticeSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill: Mapped[SkillType] = mapped_column(Enum(SkillType), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, default=30.0)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relationships
    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<PracticeSession(user_id={self.user_id}, skill={self.skill}, score={self.score})>"


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    proficiency_level: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel), default=ProficiencyLevel.INTERMEDIATE
    )
    daily_goal: Mapped[int] = mapped_column(Integer, default=3)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    target_score: Mapped[int] = mapped_column(Integer, default=100)

    # relationships
    user: Mapped["User"] = relationship(back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, level={self.proficiency_level})>"


class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False) # store as datetime but use date part
    main_task: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON string
    drill: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON string
    vocabulary: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON string
    completed_step: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<DailyPlan(user_id={self.user_id}, date={self.date})>"
