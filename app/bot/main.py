"""
TOEFL Teacher Bot — entry point.

Initialises the bot, registers all routers, creates DB tables, and starts polling.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine

# ── Handler routers ─────────────────────────────────────────
from app.bot.handlers.start import router as start_router
from app.bot.handlers.diagnostics import router as diagnostics_router
from app.bot.handlers.daily_practice import router as daily_practice_router
from app.bot.handlers.speaking import router as speaking_router
from app.bot.handlers.writing import router as writing_router
from app.bot.handlers.stats import router as stats_router
from app.bot.handlers.settings import router as settings_router

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def _create_tables() -> None:
    """Create all tables if they don't exist (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")


async def _on_startup(bot: Bot) -> None:
    await _create_tables()
    me = await bot.get_me()
    logger.info("Bot started: @%s (id=%d)", me.username, me.id)


async def _on_shutdown(bot: Bot) -> None:
    logger.info("Bot shutting down…")
    await engine.dispose()


async def main() -> None:
    _setup_logging()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Register routers in priority order
    dp.include_routers(
        start_router,
        diagnostics_router,
        daily_practice_router,
        speaking_router,
        writing_router,
        stats_router,
        settings_router,
    )

    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    logger.info("Starting polling…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
