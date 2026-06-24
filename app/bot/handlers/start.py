"""
/start and main-menu handler.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard
from app.db.crud import get_or_create_user
from app.db.session import get_session

router = Router(name="start")

WELCOME_TEXT = (
    "🎓 <b>Welcome to TOEFL Teacher!</b>\n\n"
    "I'm your personal AI tutor for TOEFL iBT preparation.\n"
    "I'll help you practice all four sections:\n"
    "📖 Reading  •  🎧 Listening  •  🎙 Speaking  •  ✍️ Writing\n\n"
    "Choose a section below to get started 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Register user (if new) and show main menu."""
    async with get_session() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    """Return to main menu."""
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.message(F.text == "/mock")
async def cmd_mock(message: Message) -> None:
    """Weekly Mock MVP."""
    text = (
        "📝 <b>Weekly Mock Exam (MVP)</b>\n\n"
        "Welcome to your mini-mock! Here are your tasks:\n\n"
        "✍️ <b>Task 1: Writing</b>\n"
        "<i>Do you agree or disagree: People should read only those books that are about real events, real people, and established facts.</i>\n\n"
        "🎙 <b>Task 2: Speaking</b>\n"
        "<i>What is a skill you would like to learn and why?</i>\n"
        "👉 Record or write your answer later — speaking scoring will be added in the next step.\n\n"
        "<b>Summary:</b> Complete the writing task by going to the Writing menu. Speaking evaluation is coming soon!"
    )
    from app.bot.keyboards import back_to_menu_keyboard
    await message.answer(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
