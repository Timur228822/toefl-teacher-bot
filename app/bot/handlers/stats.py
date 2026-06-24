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
    if stats['total_sessions'] == 0:
        text = "Not enough practice data yet. Complete Writing or Daily Practice first."
    else:
        last_res_str = ""
        for r in stats.get("last_results", []):
            last_res_str += f"  • {r['skill'].capitalize()}: {r['score']}/5.0\n"
        if not last_res_str:
            last_res_str = "  No results yet.\n"
            
        top_errors_str = ""
        for e in stats.get("top_errors", []):
            top_errors_str += f"  • {e['type']}: {e['count']} times\n"
        if not top_errors_str:
            top_errors_str = "  No errors logged.\n"

        text = (
            "📊 <b>Stats</b>\n\n"
            f"🔥 <b>Streak:</b> {stats.get('streak', 0)} days\n\n"
            f"📝 <b>Last results:</b>\n{last_res_str}\n"
            f"⚠️ <b>Top errors:</b>\n{top_errors_str}"
        )

    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
