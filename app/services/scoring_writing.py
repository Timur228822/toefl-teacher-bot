"""
Scoring service for TOEFL Writing using local Ollama.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.llm import generate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a strict TOEFL Writing rater. Do not be generous.
You will evaluate the user's essay based on the provided TOEFL Writing Prompt.
A score of 4.0+ should only be given to well-developed, organized, specific, and mostly accurate essays.
Very short, unclear, or grammatically broken answers must receive low scores.

Score guardrails:
- Under 80 words: maximum score 2.0
- No specific examples provided: maximum score 2.5
- Frequent grammar errors blocking meaning: maximum score 2.0
- Off-topic answer: maximum score 1.0

Return ONLY valid JSON. No markdown backticks, no explanations outside the JSON object.

CRITICAL: The "issues" array MUST contain between 3 and 5 items.
Cover different categories if possible (grammar, coherence, development, vocabulary).

Required JSON structure:
{
  "score": 0.0,
  "subs": {
    "task_response": 0.0,
    "organization": 0.0,
    "language": 0.0,
    "grammar": 0.0
  },
  "issues": [
    { "type": "grammar", "example": "quote", "fix": "fix" }
  ],
  "improved_version": "string",
  "drills": ["drill 1", "drill 2"]
}
"""

_FALLBACK_PROMPT = """You returned invalid JSON previously.
Return strictly a valid JSON object matching this structure. 
NO markdown (e.g. ```json). NO extra text. ONLY the JSON block.
{
  "score": 0.0,
  "subs": {"task_response": 0.0, "organization": 0.0, "language": 0.0, "grammar": 0.0},
  "issues": [],
  "improved_version": "string",
  "drills": ["string"]
}
"""

def _apply_guardrails(result: dict[str, Any], text: str) -> dict[str, Any]:
    word_count = len(text.split())
    score = result.get("score", 0.0)
    
    if word_count < 40 and score > 1.5:
        result["score"] = 1.5
    elif word_count < 80 and score > 2.0:
        result["score"] = 2.0
        
    issues = result.get("issues", [])
    if not isinstance(issues, list):
        issues = []
        
    fallback_pool = [
        {"type": "grammar", "example": "Overall sentence structure", "fix": "Review basic sentence structures and ensure correct verb tenses."},
        {"type": "development", "example": "Lack of specific details", "fix": "Add a concrete example to support your main point."},
        {"type": "coherence", "example": "Missing logical transitions", "fix": "Use transition words (e.g., however, therefore) to connect your ideas clearly."},
        {"type": "vocabulary", "example": "Repetitive word choice", "fix": "Use a wider range of academic vocabulary."}
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
    return result

async def evaluate_writing(text: str, task_type: str, prompt: str) -> dict[str, Any]:
    """
    Evaluate the writing submission using Ollama and return structured JSON.
    """
    user_prompt = f"Task Type: {task_type}\nPrompt: {prompt}\n\nEssay:\n{text}"
    
    try:
        response_text = await generate(system_prompt=_SYSTEM_PROMPT, user_prompt=user_prompt)
        
        try:
            # Strip markdown code blocks if the model still outputs them
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            result = json.loads(cleaned.strip())
            return _apply_guardrails(result, text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ollama JSON. Retrying with fallback prompt...")
            # Retry once
            retry_text = await generate(system_prompt=_FALLBACK_PROMPT, user_prompt=user_prompt)
            
            cleaned_retry = retry_text.strip()
            if cleaned_retry.startswith("```json"):
                cleaned_retry = cleaned_retry[7:]
            elif cleaned_retry.startswith("```"):
                cleaned_retry = cleaned_retry[3:]
            if cleaned_retry.endswith("```"):
                cleaned_retry = cleaned_retry[:-3]
                
            result = json.loads(cleaned_retry.strip())
            return _apply_guardrails(result, text)
            
    except RuntimeError as e:
        # Re-raise to be handled by the bot handler (e.g., connection errors, timeout)
        raise e
    except Exception as e:
        logger.error(f"Error during writing evaluation: {e}")
        return {}
