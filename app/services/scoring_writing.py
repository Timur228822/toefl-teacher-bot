"""
Scoring service for TOEFL Writing using local Ollama.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.llm import generate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert TOEFL evaluator.
You will evaluate the user's essay based on the provided TOEFL Writing Prompt.
Return ONLY valid JSON. No markdown backticks, no explanations outside the JSON object.

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
                
            return json.loads(cleaned.strip())
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
                
            return json.loads(cleaned_retry.strip())
            
    except RuntimeError as e:
        # Re-raise to be handled by the bot handler (e.g., connection errors, timeout)
        raise e
    except Exception as e:
        logger.error(f"Error during writing evaluation: {e}")
        return {}
