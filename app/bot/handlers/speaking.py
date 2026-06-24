"""
Speaking section handler.

Manages speaking practice prompts and (future) voice-message evaluation.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import back_to_menu_keyboard

router = Router(name="speaking")

class SpeakingState(StatesGroup):
    waiting_for_voice = State()


@router.callback_query(F.data == "menu:speaking")
async def cb_speaking(callback: CallbackQuery, state: FSMContext) -> None:
    text = (
        "🎙 <b>Speaking Practice</b>\n\n"
        "Here is your prompt:\n"
        "<i>What is a skill you would like to learn and why?</i>\n\n"
        "💡 <b>How it works:</b>\n"
        "  1. Record a voice message (15-45 sec)\n"
        "  2. I will transcribe it for you\n"
        "  (Scoring will be added soon!)\n\n"
        "👉 Please send your voice message now."
    )
    await state.set_state(SpeakingState.waiting_for_voice)
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(SpeakingState.waiting_for_voice)
async def process_voice(message: Message, state: FSMContext) -> None:
    if not message.voice:
        await message.answer("Please send a voice message 🎙.", reply_markup=back_to_menu_keyboard())
        return

    wait_msg = await message.answer("⏳ Downloading and transcribing your voice...", parse_mode="HTML")

    import os
    import asyncio
    from app.services.stt import transcribe

    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    file_path = os.path.join(tmp_dir, f"voice_{message.from_user.id}_{message.message_id}.ogg")

    try:
        await message.bot.download(message.voice, destination=file_path)
        
        # Run transcription in a thread since it's blocking
        transcript = await asyncio.to_thread(transcribe, file_path)
        
        await wait_msg.edit_text(
            f"📝 <b>Transcript:</b>\n\n{transcript}\n\n"
            f"<i>(Speaking scoring will be added in the next step)</i>",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except RuntimeError as e:
        await wait_msg.edit_text(f"❌ <b>Error:</b> {e}", reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    except Exception as e:
        await wait_msg.edit_text(f"❌ <b>Error processing voice:</b> {e}", reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    await state.clear()
