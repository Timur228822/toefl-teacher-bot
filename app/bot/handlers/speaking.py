"""
Speaking section handler.

Flow: prompt → voice → transcript → confirm / edit / re-record → scoring.
"""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import back_to_menu_keyboard, speaking_transcript_keyboard
from app.data.prompt_bank import get_daily_speaking_prompt, pick_speaking_prompt

logger = logging.getLogger(__name__)

router = Router(name="speaking")


class SpeakingState(StatesGroup):
    waiting_for_voice = State()
    confirm_transcript = State()
    editing_transcript = State()


def _build_prompt_text(prompt_str: str) -> str:
    """Build the display message for a given speaking prompt string."""
    return (
        "🎙 <b>Speaking Practice</b>\n\n"
        "Here is your prompt:\n"
        f"<i>{prompt_str}</i>\n\n"
        "💡 <b>How it works:</b>\n"
        "  1. Record a voice message (15-45 sec)\n"
        "  2. I will transcribe and score it\n\n"
        "👉 Please send your voice message now."
    )


def _transcript_message(transcript: str) -> str:
    return (
        f"📝 <b>Transcript:</b>\n\n{transcript}\n\n"
        "Choose an option below:"
    )


# ── helpers ──────────────────────────────────────────────────

async def _resolve_daily_prompt(telegram_id: int) -> dict:
    """Get today's speaking prompt, persisted in DB."""
    try:
        from app.db.session import get_session
        from app.db.crud import get_or_create_user

        async with get_session() as session:
            db_user = await get_or_create_user(session, telegram_id)
            user_id = db_user.id

        return await get_daily_speaking_prompt(user_id, telegram_id)
    except Exception as e:
        logger.warning("Daily prompt DB lookup failed, using random: %s", e)
        return pick_speaking_prompt(telegram_id)


# ── Entry point ──────────────────────────────────────────────

@router.callback_query(F.data == "menu:speaking")
async def cb_speaking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    chosen = await _resolve_daily_prompt(callback.from_user.id)
    prompt_str = chosen["prompt"]
    await state.update_data(prompt=prompt_str)
    await state.set_state(SpeakingState.waiting_for_voice)
    await callback.message.edit_text(
        _build_prompt_text(prompt_str),
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


def _format_score(result: dict) -> str:
    """Format scoring result into a Telegram-friendly message."""
    score = result.get("score", "?")
    subs = result.get("subs", {})
    if not isinstance(subs, dict):
        subs = {}
    issues = result.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    model_answer = result.get("model_answer", "")
    drills = result.get("drills", [])
    if not isinstance(drills, list):
        drills = []

    lines = [
        f"🎙 <b>Speaking Score: {score} / 5.0</b>\n",
        "<b>Subscores:</b>",
        f"  • Task Response: {subs.get('task_response', '?')}",
        f"  • Delivery: {subs.get('delivery', '?')}",
        f"  • Language: {subs.get('language', '?')}",
    ]

    if issues:
        lines.append("\n<b>Key Issues:</b>")
        for i, issue in enumerate(issues[:5], 1):
            if not isinstance(issue, dict):
                issue = {"type": "general", "example": str(issue), "fix": ""}
            itype = issue.get("type", "")
            example = issue.get("example", "")
            fix = issue.get("fix", "")
            lines.append(f"  {i}. <b>[{itype}]</b> \"{example}\"")
            if fix:
                lines.append(f"     → {fix}")

    if model_answer:
        lines.append(f"\n<b>Model Answer:</b>\n<i>{model_answer}</i>")

    if drills:
        lines.append("\n<b>Recommended Drills:</b>")
        for d in drills[:5]:
            lines.append(f"  • {d}")

    return "\n".join(lines)


# ── Entry point ──────────────────────────────────────────────

@router.callback_query(F.data == "menu:speaking")
async def cb_speaking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    chosen = pick_speaking_prompt(callback.from_user.id)
    prompt_str = chosen["prompt"]
    await state.update_data(prompt=prompt_str)
    await state.set_state(SpeakingState.waiting_for_voice)
    await callback.message.edit_text(
        _build_prompt_text(prompt_str),
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Voice → transcript ───────────────────────────────────────

@router.message(SpeakingState.waiting_for_voice)
async def process_voice(message: Message, state: FSMContext) -> None:
    if not message.voice:
        await message.answer(
            "Please send a <b>voice message</b> 🎙.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    wait_msg = await message.answer(
        "⏳ Downloading and transcribing your voice...", parse_mode="HTML"
    )

    from app.services.stt import transcribe

    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    file_path = os.path.join(
        tmp_dir, f"voice_{message.from_user.id}_{message.message_id}.ogg"
    )

    try:
        await message.bot.download(message.voice, destination=file_path)
        transcript = await asyncio.to_thread(transcribe, file_path)

        await state.update_data(transcript=transcript)
        await state.set_state(SpeakingState.confirm_transcript)

        await wait_msg.edit_text(
            _transcript_message(transcript),
            reply_markup=speaking_transcript_keyboard(),
            parse_mode="HTML",
        )
    except RuntimeError as e:
        await wait_msg.edit_text(
            f"❌ <b>Error:</b> {e}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        await state.clear()
    except Exception as e:
        await wait_msg.edit_text(
            f"❌ <b>Error processing voice:</b> {e}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        await state.clear()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ── ✅ Use this transcript → score ───────────────────────────

@router.callback_query(SpeakingState.confirm_transcript, F.data == "spk:use")
async def cb_use_transcript(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    transcript = data.get("transcript", "")
    prompt = data.get("prompt", "")

    await callback.message.edit_text(
        "⏳ <b>Scoring your response...</b>", parse_mode="HTML"
    )
    await callback.answer()

    from app.services.scoring_speaking import evaluate_speaking

    try:
        result = await evaluate_speaking(transcript, prompt)

        if not result:
            await callback.message.edit_text(
                "❌ <b>Could not generate a score.</b>\n\n"
                "Your transcript has been confirmed.\n"
                "Please try again later.",
                reply_markup=back_to_menu_keyboard(),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                _format_score(result),
                reply_markup=back_to_menu_keyboard(),
                parse_mode="HTML",
            )
    except RuntimeError as e:
        logger.error(f"Speaking scoring error: {e}")
        await callback.message.edit_text(
            f"❌ <b>Scoring error:</b> {e}\n\n"
            "Your transcript has been confirmed, but scoring failed.\n"
            "Make sure Ollama is running.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Unexpected speaking scoring error: {e}")
        await callback.message.edit_text(
            "❌ <b>Unexpected error during scoring.</b>\n\n"
            "Your transcript has been confirmed.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
    finally:
        await state.clear()


# ── ✏️ Edit transcript ───────────────────────────────────────

@router.callback_query(SpeakingState.confirm_transcript, F.data == "spk:edit")
async def cb_edit_transcript(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SpeakingState.editing_transcript)
    await callback.message.edit_text(
        "✏️ Please send your corrected transcript as a <b>text message</b>.",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SpeakingState.editing_transcript)
async def process_edited_transcript(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "Please send a <b>text message</b> with the corrected transcript.",
            parse_mode="HTML",
        )
        return

    new_transcript = message.text.strip()
    await state.update_data(transcript=new_transcript)
    await state.set_state(SpeakingState.confirm_transcript)

    await message.answer(
        f"✅ <b>Transcript updated:</b>\n\n{new_transcript}",
        reply_markup=speaking_transcript_keyboard(),
        parse_mode="HTML",
    )


# ── 🔁 Record again ─────────────────────────────────────────

@router.callback_query(SpeakingState.confirm_transcript, F.data == "spk:again")
async def cb_record_again(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    prompt_str = data.get("prompt", "")
    await state.set_state(SpeakingState.waiting_for_voice)
    await callback.message.edit_text(
        "🔁 Let's try again!\n\n" + _build_prompt_text(prompt_str),
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
