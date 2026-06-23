"""
Ollama LLM client.

Thin async wrapper around the Ollama HTTP API for generating
TOEFL content: prompts, feedback, scoring.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(timeout=120.0, connect=10.0)


async def generate(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Send a prompt to Ollama and return the generated text.

    Args:
        prompt: User/task prompt.
        system: Optional system prompt for role-setting.
        model: Override default model from config.
        temperature: Sampling temperature.
        max_tokens: Max tokens in response.

    Returns:
        Generated text string.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        httpx.ConnectError: If Ollama is unreachable.
    """
    url = f"{settings.ollama_base_url}/api/generate"
    payload: dict[str, Any] = {
        "model": model or settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        logger.debug("Ollama request: model=%s, prompt_len=%d", payload["model"], len(prompt))
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    text: str = data.get("response", "")
    logger.debug("Ollama response: len=%d", len(text))
    return text.strip()


async def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Multi-turn chat completion via Ollama /api/chat.

    Args:
        messages: List of {"role": "system"|"user"|"assistant", "content": "..."}.
        model: Override default model.
        temperature: Sampling temperature.

    Returns:
        Assistant's reply text.
    """
    url = f"{settings.ollama_base_url}/api/chat"
    payload: dict[str, Any] = {
        "model": model or settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data.get("message", {}).get("content", "").strip()


async def is_available() -> bool:
    """Health-check: returns True if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(settings.ollama_base_url)
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
