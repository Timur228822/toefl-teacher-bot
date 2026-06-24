"""
Daily Practice handler.

Provides daily practice prompts across all TOEFL skills.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards import back_to_menu_keyboard
from app.db.session import get_session
from app.db.crud import get_user_by_telegram_id, get_user_stats
from app.services.learning_engine import generate_daily_plan, get_next_activity

router = Router(name="daily_practice")


@router.callback_query(F.data == "menu:daily_practice")
async def cb_daily_practice(callback: CallbackQuery) -> None:
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            stats = await get_user_stats(session, user.id)
        else:
            stats = {"total_sessions": 0}

    plan = generate_daily_plan(stats)
    main_task = plan["main_task"]
    drill = plan["drill"]
    vocab = plan["vocab"]

    text = (
        "📚 <b>Your Daily Practice Plan (15-25 min)</b>\n\n"
        "Here is what we have for you today:\n\n"
        f"🎯 <b>Main Task:</b> {main_task['title']}\n"
        f"🔧 <b>Drill:</b> {drill['title']} - {drill['description']}\n"
        f"📖 <b>Vocabulary:</b> {', '.join(vocab)}\n\n"
        "Ready to start?"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Start Practice", callback_data="daily:start")],
            [InlineKeyboardButton(text="◀️ Back to Menu", callback_data="menu:main")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "daily:start")
async def cb_daily_start(callback: CallbackQuery) -> None:
    # MVP logic: we just get the first next_activity and route to it or show it.
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            stats = await get_user_stats(session, user.id)
        else:
            stats = {"total_sessions": 0}

    activity = get_next_activity(stats, current_step=0)
    
    if activity == "writing":
        # Redirect to writing module
        text = "🚀 Let's start with your Main Task: <b>Writing</b>.\n\nPlease go to the Writing section."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Go to Writing", callback_data="menu:writing")],
            [InlineKeyboardButton(text="◀️ Back to Menu", callback_data="menu:main")]
        ])
    else:
        text = f"🚀 Let's start with your Main Task: <b>{activity.capitalize()}</b>.\n\n(This module is under construction in this MVP)."
        keyboard = back_to_menu_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
