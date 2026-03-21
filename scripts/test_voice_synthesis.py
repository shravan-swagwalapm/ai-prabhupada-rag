#!/usr/bin/env python3
"""
Test ElevenLabs Voice Synthesis — SDK v1.x
Tests the cloned Prabhupada voice with sample texts across 4 categories.

Usage:
    python test_voice_synthesis.py                # Single default test
    python test_voice_synthesis.py --suite         # Run all 4 test categories
    python test_voice_synthesis.py --suite --play  # Run all 4 + auto-play each
    python test_voice_synthesis.py --text "custom text"
    python test_voice_synthesis.py --play          # Auto-play on macOS

Test Categories (--suite):
    1. Pure English     — baseline, no Sanskrit
    2. Light Sanskrit   — common terms (all in dictionary)
    3. Heavy Sanskrit   — dictionary + IAST fallback
    4. Verse Quotation  — verse ref normalization

Requirements:
    - ELEVENLABS_API_KEY in .env file
    - config/voice_config.json with voice_id saved
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "voice_config.json"
TESTS_DIR = PROJECT_ROOT / "tests"

# Add scripts/ to path for preprocessor
sys.path.insert(0, str(Path(__file__).parent))
from sanskrit_pronunciation import preprocess_for_voice

# ---------------------------------------------------------------------------
# Test texts — 4 categories matching real Claude RAG output
# ---------------------------------------------------------------------------
# These represent what ElevenLabs will ACTUALLY receive after preprocessing.
# The preprocessor has already converted all Sanskrit terms.

TEST_SUITE = {
    "1_pure_english": {
        "label": "Pure English (baseline)",
        "description": "No Sanskrit terms. Should sound perfect.",
        "text": (
            "So my dear friend, the purpose of human life is to understand God. "
            "This is not sentiment. This is the verdict of all Vedic literature. "
            "We are not these bodies. We are eternal spirit souls. And our "
            "business is to serve the Supreme Lord. This is the perfection of "
            "life. Hare Krishna."
        ),
        "listen_for": [
            "Natural English cadence",
            "Warm, conversational Prabhupada tone",
            "Clear enunciation of 'Hare Krishna'",
        ],
    },
    "2_light_sanskrit": {
        "label": "Light Sanskrit (common terms)",
        "description": "Common terms all handled by dictionary.",
        "text": (
            "Krishna says in Bhagavad Geeta, chapter two, verse twenty. "
            "The soul is never born and never dies. This aatmaa is eternal. "
            "Through bhakti yoga, one can realize this truth. The guru "
            "teaches us how to surrender to Krishna. This is dharma."
        ),
        "listen_for": [
            "Does 'aatmaa' sound like 'atma'?",
            "Does 'Geeta' sound natural?",
            "Does 'bhakti yoga' flow smoothly?",
        ],
    },
    "3_heavy_sanskrit": {
        "label": "Heavy Sanskrit (dictionary + IAST fallback)",
        "description": "Tests both dictionary lookups and character-level IAST conversion.",
        "text": (
            "So the process is gyaana yoga combined with bhakti yoga. "
            "The jeeva, trapped in samsaara, must approach a bona fide guru. "
            "Through shaastra and saadhu sanga, one develops shraddhaa. "
            "Then by chanting the mahaa mantra, Hare Krishna Hare Krishna "
            "Krishna Krishna Hare Hare, the aatmaa becomes purified."
        ),
        "listen_for": [
            "Does 'gyaana' sound like 'gyana/jnana'?",
            "Does 'samsaara' flow naturally?",
            "Does the Hare Krishna mantra sound right?",
        ],
    },
    "4_verse_quotation": {
        "label": "Verse Quotation (verse ref normalization)",
        "description": "Tests verse references converted to spoken form.",
        "text": (
            "In the Bhagavad Geeta, chapter nine, verse twenty-six, "
            "Krishna says. If one offers Me with love and devotion a leaf, "
            "a flower, fruit or water, I will accept it. You see? Krishna "
            "is not asking for anything expensive. Simply offer with bhakti. "
            "This is the secret of karma yoga."
        ),
        "listen_for": [
            "Do verse references sound natural (not robotic)?",
            "Does 'chapter nine, verse twenty-six' flow?",
            "Is the transition from reference to quote smooth?",
        ],
    },
}


def load_voice_config():
    """Load voice configuration from config/voice_config.json."""
    if not CONFIG_PATH.exists():
        print(f"Error: voice_config.json not found at {CONFIG_PATH}")
        print(f"Run: python save_voice_config.py <voice_id>")
        return None

    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def _synthesize_one(client, voice_id, model_id, voice_settings, text, output_file):
    """Generate audio for a single text. Returns (output_path, size_kb) or None."""
    audio_iterator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        voice_settings=voice_settings,
    )
    audio_bytes = b"".join(audio_iterator)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'wb') as f:
        f.write(audio_bytes)

    return output_file, output_file.stat().st_size / 1024


def test_voice_synthesis(custom_text=None, auto_play=False):
    """
    Test voice synthesis with a single text (default or custom).

    Args:
        custom_text: Optional custom text to synthesize
        auto_play: Whether to auto-play on macOS

    Returns:
        Path to generated audio file, or None on failure
    """
    print(f"\n🎙️  Testing Prabhupada Voice Synthesis (SDK v1.x)")
    print(f"{'='*60}\n")

    # Load environment
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in .env")
        print("Add: ELEVENLABS_API_KEY=your_key_here")
        return None

    # Load voice config
    config = load_voice_config()
    if not config:
        return None

    voice_id = config['voice_id']
    model_id = config.get('model', 'eleven_multilingual_v2')
    settings = config.get('settings', {})

    print(f"Voice: {config.get('voice_name', 'Unknown')} ({voice_id})")
    print(f"Model: {model_id}")
    print(f"Settings: stability={settings.get('stability', 0.5)}, "
          f"similarity={settings.get('similarity_boost', 0.75)}\n")

    # Select text
    if custom_text:
        test_text = custom_text
    else:
        test_text = (
            "The soul is never born and never dies. "
            "It is unborn, eternal, ever-existing, and primeval. "
            "The soul is not slain when the body is slain. "
            "This is described in the Bhagavad Gita, Chapter Two, Verse Twenty."
        )

    preview = test_text[:100] + ('...' if len(test_text) > 100 else '')
    print(f"Text: \"{preview}\"\n")

    # Initialize ElevenLabs client (SDK v1.x)
    try:
        from elevenlabs import ElevenLabs
        from elevenlabs.types import VoiceSettings
    except ImportError:
        print("Error: elevenlabs package not installed or wrong version")
        print("Install: pip3 install elevenlabs>=1.0.0")
        return None

    client = ElevenLabs(api_key=api_key)

    # Build voice settings
    voice_settings = VoiceSettings(
        stability=settings.get('stability', 0.5),
        similarity_boost=settings.get('similarity_boost', 0.75),
        style=settings.get('style', 0.3),
        use_speaker_boost=settings.get('use_speaker_boost', True)
    )

    # Generate audio
    try:
        print("Generating audio...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = TESTS_DIR / f"prabhupada_voice_test_{timestamp}.mp3"

        path, size_kb = _synthesize_one(
            client, voice_id, model_id, voice_settings, test_text, output_file
        )
        est_duration = len(test_text.split()) * 0.5

        print(f"\n✅ Audio generated!")
        print(f"{'='*60}")
        print(f"File:     {path}")
        print(f"Size:     {size_kb:.1f} KB")
        print(f"Duration: ~{est_duration:.0f}s (estimated)")
        print(f"{'='*60}\n")

        # Auto-play on macOS
        if auto_play and os.system("which afplay > /dev/null 2>&1") == 0:
            print("Playing audio...")
            os.system(f'afplay "{path}"')
            print("Playback complete.\n")

        print("Quality checklist:")
        print("   1. Does it sound like Srila Prabhupada?")
        print("   2. Is pronunciation clear?")
        print("   3. Is the tone appropriate for spiritual teachings?")
        print(f"\nTo play: afplay \"{path}\"")

        return path

    except Exception as e:
        print(f"Error generating audio: {e}")
        print("\nTroubleshooting:")
        print("   - Check ELEVENLABS_API_KEY is valid")
        print("   - Verify voice_id exists in your ElevenLabs account")
        print("   - Ensure you have API credits")
        return None


def test_voice_suite(auto_play=False):
    """
    Run the full 4-category test suite.
    Generates one MP3 per category and provides a listening guide.

    Args:
        auto_play: Whether to auto-play each test on macOS

    Returns:
        List of generated file paths, or empty list on failure
    """
    print(f"\n🎙️  Prabhupada Voice — Full Test Suite")
    print(f"{'='*60}")
    print(f"4 categories | preprocessed text | ElevenLabs v3\n")

    # Load environment
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in .env")
        return []

    config = load_voice_config()
    if not config:
        return []

    voice_id = config['voice_id']
    model_id = config.get('model', 'eleven_multilingual_v2')
    settings = config.get('settings', {})

    print(f"Voice: {config.get('voice_name', 'Unknown')} ({voice_id})")
    print(f"Model: {model_id}")
    print(f"Settings: stability={settings.get('stability', 0.5)}, "
          f"similarity={settings.get('similarity_boost', 0.75)}, "
          f"style={settings.get('style', 0.3)}\n")

    try:
        from elevenlabs import ElevenLabs
        from elevenlabs.types import VoiceSettings
    except ImportError:
        print("Error: elevenlabs not installed. Run: pip3 install elevenlabs>=1.0.0")
        return []

    client = ElevenLabs(api_key=api_key)

    voice_settings = VoiceSettings(
        stability=settings.get('stability', 0.5),
        similarity_boost=settings.get('similarity_boost', 0.75),
        style=settings.get('style', 0.3),
        use_speaker_boost=settings.get('use_speaker_boost', True),
    )

    # Create session directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = TESTS_DIR / f"voice_suite_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    for test_key, test in TEST_SUITE.items():
        print(f"\n--- Test: {test['label']} ---")
        print(f"    {test['description']}")
        print(f"    Text: \"{test['text'][:80]}...\"")

        output_file = session_dir / f"{test_key}.mp3"

        try:
            print(f"    Generating...", end=" ", flush=True)
            path, size_kb = _synthesize_one(
                client, voice_id, model_id, voice_settings,
                test['text'], output_file,
            )
            est_duration = len(test['text'].split()) * 0.5
            print(f"OK ({size_kb:.0f} KB, ~{est_duration:.0f}s)")
            generated.append(path)

            # Auto-play
            if auto_play and os.system("which afplay > /dev/null 2>&1") == 0:
                print(f"    Playing...")
                os.system(f'afplay "{path}"')

        except Exception as e:
            print(f"FAILED ({e})")

    # Save session metadata
    session_meta = {
        "timestamp": timestamp,
        "voice_id": voice_id,
        "model": model_id,
        "settings": settings,
        "tests": {k: {"label": v["label"], "text": v["text"]} for k, v in TEST_SUITE.items()},
        "results": [str(p) for p in generated],
    }
    with open(session_dir / "test_session.json", 'w') as f:
        json.dump(session_meta, f, indent=2)

    # Print results and listening guide
    print(f"\n{'='*60}")
    print(f"Suite complete! {len(generated)}/{len(TEST_SUITE)} tests passed.")
    print(f"Files saved to: {session_dir}")
    print(f"{'='*60}")

    print(f"\nListening Guide:")
    print(f"{'─'*60}")
    for test_key, test in TEST_SUITE.items():
        path = session_dir / f"{test_key}.mp3"
        exists = path.exists()
        status = "ready" if exists else "MISSING"
        print(f"\n  [{status}] {test['label']}")
        if exists:
            print(f"  afplay \"{path}\"")
        print(f"  Listen for:")
        for item in test["listen_for"]:
            print(f"    - {item}")

    print(f"\n{'─'*60}")
    print(f"After listening, if tuning is needed:")
    print(f"  python tune_voice_settings.py")
    print(f"  # Generates 4 presets x 2 texts = 8 files for A/B comparison")

    return generated


def main():
    parser = argparse.ArgumentParser(description='Test Prabhupada voice synthesis')
    parser.add_argument('--text', help='Custom text to synthesize', default=None)
    parser.add_argument('--play', action='store_true', help='Auto-play audio on macOS')
    parser.add_argument('--suite', action='store_true',
                        help='Run full 4-category test suite')

    args = parser.parse_args()

    if args.suite:
        results = test_voice_suite(auto_play=args.play)
        return 0 if results else 1
    else:
        result = test_voice_synthesis(custom_text=args.text, auto_play=args.play)
        return 0 if result else 1


if __name__ == "__main__":
    exit(main())
