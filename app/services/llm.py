"""
Ollama LLM client using aiohttp.
"""

import aiohttp
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate(system_prompt: str, user_prompt: str) -> str:
    """
    Generate a response from Ollama.
    """
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.1,
            "seed": 42
        }
    }
    
    timeout = aiohttp.ClientTimeout(total=120)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("response", "").strip()
    except aiohttp.ClientConnectorError as e:
        error_msg = f"Failed to connect to Ollama at {settings.ollama_base_url}. Is it running? Error: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except asyncio.TimeoutError as e:
        error_msg = "Request to Ollama timed out after 120 seconds."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except aiohttp.ClientResponseError as e:
        error_msg = f"Ollama API returned an error: {e.status} {e.message}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"An unexpected error occurred while communicating with Ollama: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
