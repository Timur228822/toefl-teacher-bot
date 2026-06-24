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


# ── Daily Plans ─────────────────────────────────────────────

from app.db.models import DailyPlan
import json

async def get_daily_plan(session: AsyncSession, user_id: int, target_date: datetime.date) -> DailyPlan | None:
    """Get the daily plan for a specific date."""
    # SQLite stores datetime, but we just need to filter by date part. 
    # To be safe across dialects and for simplicity, let's just use Python filtering
    # or cast. Let's compare date range for the target_date.
    start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    
    stmt = (
        select(DailyPlan)
        .where(DailyPlan.user_id == user_id)
        .where(DailyPlan.date >= start_of_day)
        .where(DailyPlan.date < end_of_day)
        .order_by(DailyPlan.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_daily_plan(
    session: AsyncSession, 
    user_id: int, 
    plan_data: dict
) -> DailyPlan:
    """Create a new daily plan."""
    main_task = json.dumps(plan_data.get("main_task", {}), ensure_ascii=False)
    drill = json.dumps(plan_data.get("drill", {}), ensure_ascii=False)
    vocabulary = json.dumps(plan_data.get("vocab", []), ensure_ascii=False)
    
    dp = DailyPlan(
        user_id=user_id,
        date=datetime.now(timezone.utc),
        main_task=main_task,
        drill=drill,
        vocabulary=vocabulary,
        completed_step=0
    )
    session.add(dp)
    await session.flush()
    return dp
