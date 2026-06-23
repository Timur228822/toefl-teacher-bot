"""
Settings handler.

Lets users configure proficiency level, daily goal, target score,
and notification preferences.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard, level_keyboard, settings_keyboard
from app.db.crud import get_user_by_telegram_id, get_user_settings
from app.db.models import ProficiencyLevel
from app.db.session import get_session

router = Router(name="settings")


@router.callback_query(F.data == "menu:settings")
async def cb_settings_menu(callback: CallbackQuery) -> None:
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

        user_settings = await get_user_settings(session, user.id)

    level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
    current_level = user_settings.proficiency_level.value if user_settings else "intermediate"
    daily_goal = user_settings.daily_goal if user_settings else 3
    target_score = user_settings.target_score if user_settings else 100
    notify = "✅ On" if (user_settings and user_settings.notify_enabled) else "❌ Off"

    text = (
        "⚙️ <b>Settings</b>\n\n"
        f"🎯 Level: {level_emoji.get(current_level, '🟡')} <b>{current_level.capitalize()}</b>\n"
        f"📅 Daily goal: <b>{daily_goal} sessions</b>\n"
        f"🏆 Target score: <b>{target_score}</b>\n"
        f"🔔 Notifications: <b>{notify}</b>\n\n"
        "Tap a setting to change it:"
    )
    await callback.message.edit_text(text, reply_markup=settings_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings:level")
async def cb_settings_level(callback: CallbackQuery) -> None:
    text = (
        "🎯 <b>Proficiency Level</b>\n\n"
        "Select your current TOEFL proficiency level.\n"
        "This affects the difficulty of practice materials."
    )
    await callback.message.edit_text(text, reply_markup=level_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("level:"))
async def cb_set_level(callback: CallbackQuery) -> None:
    level_str = callback.data.split(":")[1]
    try:
        new_level = ProficiencyLevel(level_str)
    except ValueError:
        await callback.answer("Invalid level.", show_alert=True)
        return

    async with get_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user is None:
            await callback.answer("User not found.", show_alert=True)
            return
        user_settings = await get_user_settings(session, user.id)
        if user_settings:
            user_settings.proficiency_level = new_level

    level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
    await callback.message.edit_text(
        f"✅ Level updated to {level_emoji.get(level_str, '')} <b>{level_str.capitalize()}</b>!\n\n"
        "Practice content will be adjusted accordingly.",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings:daily_goal")
async def cb_settings_daily_goal(callback: CallbackQuery) -> None:
    text = (
        "📅 <b>Daily Goal</b>\n\n"
        "Your current daily goal determines how many practice sessions "
        "are recommended each day.\n\n"
        "🔄 <i>Send a number (1-10) to update your daily goal.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings:target_score")
async def cb_settings_target_score(callback: CallbackQuery) -> None:
    text = (
        "🏆 <b>Target Score</b>\n\n"
        "Set your target TOEFL iBT total score (0-120).\n"
        "This helps me tailor your practice plan.\n\n"
        "🔄 <i>Send a number (60-120) to set your target.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings:notifications")
async def cb_settings_notifications(callback: CallbackQuery) -> None:
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user is None:
            await callback.answer("User not found.", show_alert=True)
            return
        user_settings = await get_user_settings(session, user.id)
        if user_settings:
            user_settings.notify_enabled = not user_settings.notify_enabled
            new_state = user_settings.notify_enabled
        else:
            new_state = False

    status = "✅ Enabled" if new_state else "❌ Disabled"
    await callback.message.edit_text(
        f"🔔 Notifications: <b>{status}</b>",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
