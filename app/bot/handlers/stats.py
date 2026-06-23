"""
Stats handler.

Shows user's practice statistics pulled from the database.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.db.crud import get_user_by_telegram_id, get_user_stats
from app.db.session import get_session

router = Router(name="stats")


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user is None:
            await callback.message.edit_text(
                "⚠️ User not found. Please /start first.",
                reply_markup=back_to_menu_keyboard(),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        stats = await get_user_stats(session, user.id, days=30)

    # ── Format stats message ────────────────────────────────
    skill_lines = []
    for skill_name in ("reading", "listening", "speaking", "writing"):
        data = stats["by_skill"].get(skill_name)
        if data:
            emoji = {"reading": "📖", "listening": "🎧", "speaking": "🎙", "writing": "✍️"}[skill_name]
            skill_lines.append(
                f"  {emoji} {skill_name.capitalize()}: "
                f"{data['sessions']} sessions · avg {data['avg_score']}/30"
            )

    skill_block = "\n".join(skill_lines) if skill_lines else "  No practice sessions yet."

    text = (
        "📊 <b>Your Statistics</b> (last 30 days)\n\n"
        f"🔢 Total sessions: <b>{stats['total_sessions']}</b>\n"
        f"⭐ Average score:  <b>{stats['avg_score']}</b>/30\n\n"
        f"<b>By skill:</b>\n{skill_block}\n\n"
        "💡 <i>Keep practicing daily to see your progress!</i>"
    )

    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
