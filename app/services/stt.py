"""
Speech-to-Text service using local faster-whisper.
"""

import os
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_model = None

def _get_model():
    global _model
    if _model is None:
        model_size = os.getenv("WHISPER_MODEL", "base")
        logger.info(f"Loading faster-whisper model '{model_size}'...")
        try:
            _model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info("Whisper model loaded successfully.")
        except ImportError:
            raise RuntimeError("faster-whisper is not installed. Please install it.")
        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            raise RuntimeError(f"Could not load faster-whisper model: {e}")
    return _model

def transcribe(file_path: str) -> str:
    """
    Transcribe audio file to text using faster-whisper.
    """
    model = _get_model()
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        # segments is a generator; iterating over it performs the transcription
        text = " ".join([segment.text for segment in segments]).strip()
        return text
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}")
