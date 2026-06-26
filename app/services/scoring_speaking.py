"""
Scoring service for TOEFL Speaking using local Ollama.

Evaluates a transcript against the displayed speaking prompt.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.llm import generate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a strict TOEFL Speaking rater. You evaluate a student's SPOKEN RESPONSE transcript against a specific Speaking prompt.

CRITICAL: You must evaluate whether the response ACTUALLY ANSWERS the displayed prompt.
Good English alone is NOT enough for a high score. The response must directly address the question.

Scoring guidelines (0-5 scale):

task_response — Does the transcript answer the specific prompt?
  - If the answer does not address the displayed prompt at all: max 1.5
  - If the answer is mostly off-topic: max 2.0
  - If the answer mentions the topic but does not answer "why" or give reasons: max 2.5
  - If no clear reason or example is provided: max 2.0
  - 4.0+ requires a clear direct answer to the prompt with relevant reasons and examples

delivery — Fluency and coherence markers visible in the transcript.
  NOTE: You only have the transcript text, not the audio. Evaluate based on:
  - Sentence completeness and flow
  - Hesitation markers (um, uh, like, you know) — many = lower score
  - False starts and self-corrections
  - Do NOT judge pronunciation or accent (you cannot hear the audio)
  - If transcript is mostly filler words or fragments: max 2.0

language — Grammar, vocabulary, and clarity.
  - If grammar errors make meaning hard to understand: max 2.0
  - Repetitive or very basic vocabulary: max 3.0
  - 4.0+ requires mostly accurate grammar and varied vocabulary

Overall score rules:
  - If the answer does not address the displayed prompt: overall max 2.0
  - If the answer is mostly off-topic: overall max 1.5
  - If the answer mentions the topic but does not explain "why": overall max 2.5
  - If transcript is very short (under 20 words) or mostly filler: overall max 2.0
  - If no clear reason/example is provided: overall max 2.5
  - 4.0+ requires clear answer, relevant reasons, organization, and mostly understandable language
  - Do NOT be generous. Most casual responses deserve 2.0-3.0.

Return ONLY valid JSON. No markdown backticks, no explanations outside the JSON object.

CRITICAL: The "issues" array MUST contain between 3 and 5 items.
Cover different categories (task_response, delivery, language, development, vocabulary).

Required JSON structure:
{
  "score": 0.0,
  "subs": {
    "delivery": 0.0,
    "language": 0.0,
    "task_response": 0.0
  },
  "issues": [
    { "type": "category", "example": "quote from transcript", "fix": "suggestion" }
  ],
  "model_answer": "A well-structured example response to the same prompt",
  "drills": ["drill 1", "drill 2", "drill 3"]
}
"""

_FALLBACK_PROMPT = """\
You returned invalid JSON previously.
Return strictly a valid JSON object matching this structure.
NO markdown (e.g. ```json). NO extra text. ONLY the JSON block.
{
  "score": 0.0,
  "subs": {"delivery": 0.0, "language": 0.0, "task_response": 0.0},
  "issues": [],
  "model_answer": "string",
  "drills": ["string"]
}
"""


def _clean_json(text: str) -> str:
    """Strip markdown code fences if present."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _apply_guardrails(result: dict[str, Any], transcript: str) -> dict[str, Any]:
    """Enforce hard score caps based on transcript quality."""
    word_count = len(transcript.split())
    score = float(result.get("score", 0.0))
    subs = result.get("subs", {})
    task_response = float(subs.get("task_response", 0.0))

    # Very short or filler-heavy transcript
    if word_count < 10 and score > 1.5:
        result["score"] = 1.5
    elif word_count < 20 and score > 2.0:
        result["score"] = min(score, 2.0)

    # If task_response is low, cap overall
    if task_response <= 2.0 and score > 2.5:
        result["score"] = 2.5
    if task_response <= 1.5 and score > 2.0:
        result["score"] = 2.0

    # Ensure issues list is valid and has 3-5 items
    issues = result.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    fallback_pool = [
        {
            "type": "task_response",
            "example": "Overall relevance to the prompt",
            "fix": "Make sure your answer directly addresses the question asked.",
        },
        {
            "type": "language",
            "example": "Overall language clarity",
            "fix": "Use clear, simple sentences and check subject-verb agreement.",
        },
        {
            "type": "development",
            "example": "Lack of supporting details",
            "fix": "Add a specific example or reason to support your main point.",
        },
        {
            "type": "delivery",
            "example": "Fluency and coherence",
            "fix": "Reduce filler words and practice speaking in complete sentences.",
        },
        {
            "type": "vocabulary",
            "example": "Repetitive word choice",
            "fix": "Use a wider range of vocabulary to express your ideas.",
        },
    ]

    while len(issues) < 3:
        existing_types = {i.get("type", "") for i in issues}
        added = False
        for fb in fallback_pool:
            if fb["type"] not in existing_types:
                issues.append(fb)
                added = True
                break
        if not added:
            issues.append(fallback_pool[0])

    if len(issues) > 5:
        issues = issues[:5]

    result["issues"] = issues

    # Ensure drills list exists
    if not isinstance(result.get("drills"), list) or len(result["drills"]) == 0:
        result["drills"] = [
            "Record yourself answering the prompt and listen back",
            "Practice stating your main point in the first sentence",
            "Use the OREO structure: Opinion, Reason, Example, Opinion restate",
        ]

    # Ensure model_answer exists
    if not result.get("model_answer"):
        result["model_answer"] = "(Model answer not available)"

    return result


async def evaluate_speaking(transcript: str, prompt: str) -> dict[str, Any]:
    """
    Evaluate the speaking transcript against the given prompt using Ollama.
    Returns structured scoring dict.
    """
    user_prompt = (
        f"Speaking Prompt (the question the student was asked):\n{prompt}\n\n"
        f"Student's Spoken Response Transcript:\n{transcript}"
    )

    try:
        response_text = await generate(
            system_prompt=_SYSTEM_PROMPT, user_prompt=user_prompt
        )

        try:
            result = json.loads(_clean_json(response_text))
            return _apply_guardrails(result, transcript)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse Ollama JSON for speaking. Retrying with fallback..."
            )
            retry_text = await generate(
                system_prompt=_FALLBACK_PROMPT, user_prompt=user_prompt
            )
            result = json.loads(_clean_json(retry_text))
            return _apply_guardrails(result, transcript)

    except RuntimeError:
        # Connection / timeout — re-raise for the handler to show a user-friendly error
        raise
    except Exception as e:
        logger.error(f"Error during speaking evaluation: {e}")
        return {}
