#!/usr/bin/env python3
"""
Voice Synthesizer — ElevenLabs integration for Prabhupada's voice
Converts text to speech using cloned Prabhupada voice via ElevenLabs SDK v1.x.

Usage as module:
    from voice_synthesizer import synthesize_speech, synthesize_and_play
    audio_path = synthesize_and_play("The soul is eternal...")
"""

import logging
import os
import shutil
import subprocess
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
AUDIO_DIR = PROJECT_ROOT / "audio_responses"
CONFIG_PATH = PROJECT_ROOT / "config" / "voice_config.json"

# Optional recordings mirror — configure via env var, not hardcoded path.
# Leave unset to skip auto-copy.
_RECORDINGS_DIR_ENV = os.getenv("PRABHUPADA_RECORDINGS_DIR", "").strip()
RECORDINGS_DIR = Path(_RECORDINGS_DIR_ENV) if _RECORDINGS_DIR_ENV else None

load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# Ensure scripts dir is on path so sanskrit_pronunciation can always be found
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# ElevenLabs limits
MAX_TEXT_CHARS = 5000        # ElevenLabs hard limit per request
ELEVENLABS_TIMEOUT = 180     # seconds — long audio can take time
ELEVENLABS_MAX_RETRIES = 3


def load_voice_config() -> dict:
    """Load and validate voice configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"voice_config.json not found at {CONFIG_PATH}\n"
            "Run: python save_voice_config.py <voice_id>"
        )
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    # Validate required fields
    if not config.get("voice_id"):
        raise ValueError(
            f"voice_id is missing or empty in {CONFIG_PATH}. "
            "Run: python save_voice_config.py <voice_id>"
        )

    return config


def get_elevenlabs_api_key() -> str:
    """Get ElevenLabs API key from environment."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in .env")
    return api_key


def _preprocess_text(text: str) -> str:
    """Validate length and preprocess text for voice synthesis."""
    if not text or not text.strip():
        raise ValueError("Text for synthesis cannot be empty")

    # Warn on long text; truncate at hard limit with clear logging
    if len(text) > MAX_TEXT_CHARS:
        logger.warning(
            "Text too long (%d chars), truncating to %d for ElevenLabs",
            len(text), MAX_TEXT_CHARS,
        )
        text = text[:MAX_TEXT_CHARS]

    # Preprocess Sanskrit diacriticals → ElevenLabs-friendly phonetics
    try:
        from sanskrit_pronunciation import preprocess_for_voice
        text = preprocess_for_voice(text)
    except ImportError:
        logger.warning("sanskrit_pronunciation not available; skipping preprocessing")

    return text


def _build_elevenlabs_payload(text: str, config: dict) -> dict:
    """Build the ElevenLabs API request payload from config."""
    settings = config.get("settings", {})
    return {
        "text": text,
        "model_id": config.get("model", "eleven_v3"),
        "voice_settings": {
            "stability": settings.get("stability", 0.5),
            "similarity_boost": settings.get("similarity_boost", 0.75),
            "style": settings.get("style", 0.3),
            "use_speaker_boost": settings.get("use_speaker_boost", True),
        },
    }


def synthesize_speech(text: str, output_path: Path = None) -> Path:
    """
    Synthesize speech from text using Prabhupada's cloned voice.
    Automatically preprocesses Sanskrit terms and diacriticals for pronunciation.
    Retries up to ELEVENLABS_MAX_RETRIES times on transient failures.

    Args:
        text: Text to synthesize (may contain Sanskrit, IAST, markdown)
        output_path: Optional specific output path. If None, auto-generates.

    Returns:
        Path to saved MP3 file

    Raises:
        ValueError: If text is empty or config is invalid
        requests.HTTPError: On non-retriable ElevenLabs API error
        RuntimeError: If all retries fail
    """
    text = _preprocess_text(text)
    config = load_voice_config()
    api_key = get_elevenlabs_api_key()

    voice_id = config["voice_id"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = _build_elevenlabs_payload(text, config)

    logger.info(
        "Synthesizing speech: %d chars, voice=%s, model=%s",
        len(text), voice_id[:8] + "...", config.get("model", "eleven_v3"),
    )

    last_error: Exception = RuntimeError("No attempts made")
    for attempt in range(ELEVENLABS_MAX_RETRIES):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=ELEVENLABS_TIMEOUT
            )
            response.raise_for_status()
            break  # Success

        except requests.exceptions.Timeout:
            last_error = TimeoutError(
                f"ElevenLabs timed out after {ELEVENLABS_TIMEOUT}s"
            )
            logger.warning(
                "Attempt %d/%d: ElevenLabs timeout",
                attempt + 1, ELEVENLABS_MAX_RETRIES,
            )
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status == 429:
                wait = 2 ** attempt
                logger.warning(
                    "ElevenLabs rate limited, retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, ELEVENLABS_MAX_RETRIES,
                )
                time.sleep(wait)
                last_error = e
                continue
            # Non-retriable: bad voice ID, invalid auth, bad payload, etc.
            logger.error("ElevenLabs HTTP %d error: %s", status, e)
            raise
        except Exception as e:
            last_error = e
            logger.warning("Attempt %d/%d failed: %s", attempt + 1, ELEVENLABS_MAX_RETRIES, e)

        if attempt < ELEVENLABS_MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(
            f"ElevenLabs synthesis failed after {ELEVENLABS_MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    # Determine output path
    if output_path is None:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = AUDIO_DIR / f"response_{timestamp}.mp3"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    file_size_kb = output_path.stat().st_size / 1024
    logger.info("Audio saved to %s (%.0f KB)", output_path, file_size_kb)

    # Optional: mirror to recordings folder (configured via env var, never hardcoded)
    if RECORDINGS_DIR is not None:
        try:
            RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(output_path), str(RECORDINGS_DIR / output_path.name))
            logger.debug("Audio mirrored to %s", RECORDINGS_DIR)
        except Exception as e:
            logger.debug("Could not mirror audio to recordings dir: %s", e)
            # Never fail synthesis because the copy failed

    return output_path


def synthesize_and_play(text: str) -> Path:
    """
    Synthesize speech and auto-play on macOS.

    Args:
        text: Text to synthesize

    Returns:
        Path to saved MP3 file
    """
    audio_path = synthesize_speech(text)

    file_size_kb = audio_path.stat().st_size / 1024
    print(f"Audio: {audio_path} ({file_size_kb:.0f} KB)")

    # Auto-play on macOS (non-blocking — runs in background)
    try:
        subprocess.Popen(
            ["afplay", str(audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Playing...")
    except FileNotFoundError:
        print(f"Play with: open \"{audio_path}\"")

    return audio_path


def synthesize_speech_streaming(text: str):
    """
    Stream audio bytes as they're generated.
    Useful for the web API to start sending audio before full generation.

    Args:
        text: Text to synthesize (may contain Sanskrit, IAST, markdown)

    Yields:
        bytes: Audio chunks

    Raises:
        ValueError: If text is empty
        RuntimeError: On repeated failures
    """
    text = _preprocess_text(text)
    config = load_voice_config()
    api_key = get_elevenlabs_api_key()

    voice_id = config["voice_id"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = _build_elevenlabs_payload(text, config)

    logger.info("Streaming synthesis: %d chars, voice=%s", len(text), voice_id[:8] + "...")

    try:
        with requests.post(
            url, headers=headers, json=payload, stream=True, timeout=ELEVENLABS_TIMEOUT
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
    except Exception as e:
        logger.error("Streaming synthesis failed: %s", e, exc_info=True)
        raise
