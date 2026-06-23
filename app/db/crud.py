"""
CRUD helpers — thin async wrappers around common DB operations.

Every function takes an AsyncSession so callers control the transaction boundary.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PracticeSession, SkillType, User, UserSettings


# ── Users ───────────────────────────────────────────────────


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """Return existing user or create a new one with default settings."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()  # get user.id

        # default settings
        settings = UserSettings(user_id=user.id)
        session.add(settings)

    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ── Practice Sessions ──────────────────────────────────────


async def create_practice_session(
    session: AsyncSession,
    user_id: int,
    skill: SkillType,
    prompt_text: str | None = None,
    user_answer: str | None = None,
    feedback: str | None = None,
    score: float | None = None,
) -> PracticeSession:
    ps = PracticeSession(
        user_id=user_id,
        skill=skill,
        prompt_text=prompt_text,
        user_answer=user_answer,
        feedback=feedback,
        score=score,
    )
    session.add(ps)
    await session.flush()
    return ps


async def get_user_stats(
    session: AsyncSession,
    user_id: int,
    days: int = 30,
) -> dict:
    """Aggregate stats for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # total sessions
    total_q = (
        select(func.count(PracticeSession.id))
        .where(PracticeSession.user_id == user_id)
        .where(PracticeSession.created_at >= since)
    )

    # avg score
    avg_q = (
        select(func.avg(PracticeSession.score))
        .where(PracticeSession.user_id == user_id)
        .where(PracticeSession.created_at >= since)
        .where(PracticeSession.score.isnot(None))
    )

    # per-skill breakdown
    skill_q = (
        select(
            PracticeSession.skill,
            func.count(PracticeSession.id).label("cnt"),
            func.avg(PracticeSession.score).label("avg_score"),
        )
        .where(PracticeSession.user_id == user_id)
        .where(PracticeSession.created_at >= since)
        .group_by(PracticeSession.skill)
    )

    total_res = await session.execute(total_q)
    avg_res = await session.execute(avg_q)
    skill_res = await session.execute(skill_q)

    return {
        "total_sessions": total_res.scalar() or 0,
        "avg_score": round(avg_res.scalar() or 0.0, 1),
        "by_skill": {
            row.skill.value: {"sessions": row.cnt, "avg_score": round(row.avg_score or 0.0, 1)}
            for row in skill_res.all()
        },
        "period_days": days,
    }


async def get_user_settings(session: AsyncSession, user_id: int) -> UserSettings | None:
    stmt = select(UserSettings).where(UserSettings.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
