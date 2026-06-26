"""
Reusable InlineKeyboardMarkup & ReplyKeyboardMarkup factories.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with 6 feature buttons (2 × 3 grid)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Diagnostics", callback_data="menu:diagnostics"),
                InlineKeyboardButton(text="📚 Daily Practice", callback_data="menu:daily_practice"),
            ],
            [
                InlineKeyboardButton(text="🎙 Speaking", callback_data="menu:speaking"),
                InlineKeyboardButton(text="✍️ Writing", callback_data="menu:writing"),
            ],
            [
                InlineKeyboardButton(text="📊 Stats", callback_data="menu:stats"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings"),
            ],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Single 'Back to menu' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Back to Menu", callback_data="menu:main")]
        ]
    )


def speaking_transcript_keyboard() -> InlineKeyboardMarkup:
    """Transcript confirmation / edit buttons for Speaking."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Use this transcript", callback_data="spk:use")],
            [InlineKeyboardButton(text="✏️ Edit transcript", callback_data="spk:edit")],
            [InlineKeyboardButton(text="🔁 Record again", callback_data="spk:again")],
            [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="menu:main")],
        ]
    )


def diagnostics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Reading", callback_data="diag:reading"),
                InlineKeyboardButton(text="🎧 Listening", callback_data="diag:listening"),
            ],
            [
                InlineKeyboardButton(text="🎙 Speaking", callback_data="diag:speaking"),
                InlineKeyboardButton(text="✍️ Writing", callback_data="diag:writing"),
            ],
            [InlineKeyboardButton(text="◀️ Back to Menu", callback_data="menu:main")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Proficiency Level", callback_data="settings:level")],
            [InlineKeyboardButton(text="📅 Daily Goal", callback_data="settings:daily_goal")],
            [InlineKeyboardButton(text="🏆 Target Score", callback_data="settings:target_score")],
            [InlineKeyboardButton(text="🔔 Notifications", callback_data="settings:notifications")],
            [InlineKeyboardButton(text="◀️ Back to Menu", callback_data="menu:main")],
        ]
    )


def level_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Beginner", callback_data="level:beginner")],
            [InlineKeyboardButton(text="🟡 Intermediate", callback_data="level:intermediate")],
            [InlineKeyboardButton(text="🔴 Advanced", callback_data="level:advanced")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="menu:settings")],
        ]
    )
