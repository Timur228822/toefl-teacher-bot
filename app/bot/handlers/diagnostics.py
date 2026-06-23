"""
Diagnostics section handler.

Lets the user run a quick diagnostic test for any TOEFL skill.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard, diagnostics_keyboard

router = Router(name="diagnostics")


@router.callback_query(F.data == "menu:diagnostics")
async def cb_diagnostics_menu(callback: CallbackQuery) -> None:
    text = (
        "📝 <b>Diagnostics</b>\n\n"
        "Take a quick diagnostic test to assess your current TOEFL level.\n"
        "Choose a skill to begin:"
    )
    await callback.message.edit_text(text, reply_markup=diagnostics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("diag:"))
async def cb_diagnostics_skill(callback: CallbackQuery) -> None:
    skill = callback.data.split(":")[1]
    skill_labels = {
        "reading": "📖 Reading",
        "listening": "🎧 Listening",
        "speaking": "🎙 Speaking",
        "writing": "✍️ Writing",
    }
    label = skill_labels.get(skill, skill.capitalize())

    text = (
        f"📝 <b>Diagnostic: {label}</b>\n\n"
        f"Starting your {skill} diagnostic...\n"
        "🔄 <i>This feature is being prepared. "
        "The AI will generate a diagnostic passage and questions for you.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
