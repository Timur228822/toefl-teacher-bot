"""
Daily Practice handler.

Provides daily practice prompts across all TOEFL skills.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard

router = Router(name="daily_practice")


@router.callback_query(F.data == "menu:daily_practice")
async def cb_daily_practice(callback: CallbackQuery) -> None:
    text = (
        "📚 <b>Daily Practice</b>\n\n"
        "Your daily practice plan is tailored to your proficiency level.\n\n"
        "Today's tasks:\n"
        "  1️⃣  Read a passage & answer 3 questions\n"
        "  2️⃣  Listen to a lecture excerpt & summarise\n"
        "  3️⃣  Respond to an independent speaking prompt\n\n"
        "🔄 <i>AI-generated practice content coming soon. "
        "The Ollama backend will create fresh tasks each day.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
