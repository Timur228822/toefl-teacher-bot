"""
Speaking section handler.

Manages speaking practice prompts and (future) voice-message evaluation.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard

router = Router(name="speaking")


@router.callback_query(F.data == "menu:speaking")
async def cb_speaking(callback: CallbackQuery) -> None:
    text = (
        "🎙 <b>Speaking Practice</b>\n\n"
        "TOEFL Speaking has 4 tasks:\n"
        "  • <b>Task 1</b> — Independent: express your opinion\n"
        "  • <b>Tasks 2-4</b> — Integrated: read + listen, then speak\n\n"
        "💡 <b>How it works:</b>\n"
        "  1. I'll send you a prompt\n"
        "  2. You record a voice message (15-45 sec)\n"
        "  3. AI evaluates your response on delivery, "
        "language use, and topic development\n\n"
        "🔄 <i>Voice evaluation via Ollama is being integrated. "
        "Send any voice message to test the pipeline.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
