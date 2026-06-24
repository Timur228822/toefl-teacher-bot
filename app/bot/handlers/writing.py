"""
Writing section handler.

Manages writing practice: independent & integrated essay prompts,
AI-powered feedback via Ollama.
"""

from __future__ import annotations

import json
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import back_to_menu_keyboard
from app.db.crud import create_practice_session
from app.db.models import SkillType
from app.db.session import get_session
from app.services.scoring_writing import evaluate_writing

router = Router(name="writing")


class WritingState(StatesGroup):
    waiting_for_essay = State()


# A simple default prompt to show the user
DEFAULT_PROMPT = "Do you agree or disagree with the following statement: Technology has made our lives more complicated. Use specific reasons and examples to support your answer."


@router.callback_query(F.data == "menu:writing")
async def cb_writing(callback: CallbackQuery, state: FSMContext) -> None:
    text = (
        "✍️ <b>Writing Practice</b>\n\n"
        "TOEFL Writing has 2 tasks:\n"
        "  • <b>Integrated</b> — read a passage, listen to a lecture, "
        "write a summary (20 min, 150-225 words)\n"
        "  • <b>Academic Discussion</b> — contribute to an online "
        "discussion (10 min, 100+ words)\n\n"
        f"📝 <b>Today's Prompt:</b>\n<i>{DEFAULT_PROMPT}</i>\n\n"
        "💡 <b>How it works:</b>\n"
        "  Type your essay right here in the chat and send it to me.\n"
        "  I'll evaluate it using AI."
    )
    await state.set_state(WritingState.waiting_for_essay)
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(WritingState.waiting_for_essay)
async def process_essay(message: Message, state: FSMContext) -> None:
    user_text = message.text
    if not user_text:
        await message.answer("Please send text only.")
        return

    if len(user_text.split()) < 10:
        await message.answer("Your essay is too short to score. Please try to write at least 50 words.", reply_markup=back_to_menu_keyboard())
        return

    wait_msg = await message.answer("⏳ Evaluating your essay using Ollama. This might take a minute...", parse_mode="HTML")
    
    try:
        result = await evaluate_writing(text=user_text, task_type="Independent/Academic Discussion", prompt=DEFAULT_PROMPT)
    except RuntimeError as e:
        await wait_msg.edit_text(f"❌ <b>Error:</b> Ollama is not reachable or timed out.\n\n<code>{e}</code>", reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
        await state.clear()
        return

    if not result:
        await wait_msg.edit_text("❌ Failed to parse Ollama response. Please try again.", reply_markup=back_to_menu_keyboard())
        await state.clear()
        return

    # Save to DB
    score = result.get("score", 0.0)
    async with get_session() as session:
        from app.db.crud import get_user_by_telegram_id, log_error
        db_user = await get_user_by_telegram_id(session, message.from_user.id)
        if db_user:
            await create_practice_session(
                session=session,
                user_id=db_user.id,
                skill=SkillType.WRITING,
                prompt_text=DEFAULT_PROMPT,
                user_answer=user_text,
                feedback=json.dumps(result, ensure_ascii=False),
                score=score
            )
            
            issues = result.get("issues", [])
            for issue in issues:
                await log_error(
                    session,
                    user_id=db_user.id,
                    source_type="writing",
                    error_type=issue.get("type", "unknown"),
                    example=issue.get("example", ""),
                    fix=issue.get("fix", "")
                )
            await session.commit()

    # Format result for user
    subs = result.get("subs", {})
    issues = result.get("issues", [])
    
    response_text = f"🎯 <b>Writing Score: {score}/5.0</b>\n\n"
    response_text += f"📊 <b>Subscores:</b>\n"
    response_text += f"• Task Response: {subs.get('task_response', 0)}/5\n"
    response_text += f"• Organization: {subs.get('organization', 0)}/5\n"
    response_text += f"• Language Use: {subs.get('language', 0)}/5\n"
    response_text += f"• Grammar: {subs.get('grammar', 0)}/5\n\n"
    
    if issues:
        response_text += "⚠️ <b>Key Issues:</b>\n"
        for i, issue in enumerate(issues[:5], 1):
            response_text += f"{i}. [{issue.get('type')}] <i>{issue.get('example')}</i>\n   👉 Fix: {issue.get('fix')}\n"
        response_text += "\n"
        
    drills = result.get("drills", [])
    if drills:
        response_text += "💡 <b>Recommended Drills:</b>\n"
        for drill in drills:
            response_text += f"• {drill}\n"

    await wait_msg.edit_text(response_text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await state.clear()
