"""
Writing section handler.

Manages writing practice: independent & integrated essay prompts,
AI-powered feedback via Ollama.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard

router = Router(name="writing")


@router.callback_query(F.data == "menu:writing")
async def cb_writing(callback: CallbackQuery) -> None:
    text = (
        "✍️ <b>Writing Practice</b>\n\n"
        "TOEFL Writing has 2 tasks:\n"
        "  • <b>Integrated</b> — read a passage, listen to a lecture, "
        "write a summary (20 min, 150-225 words)\n"
        "  • <b>Academic Discussion</b> — contribute to an online "
        "discussion (10 min, 100+ words)\n\n"
        "💡 <b>How it works:</b>\n"
        "  1. I'll send you a prompt\n"
        "  2. Type your essay right here in the chat\n"
        "  3. AI scores you on development, organization, "
        "language use & mechanics\n\n"
        "🔄 <i>Essay evaluation engine is being connected to Ollama. "
        "Type any text to test the pipeline.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
