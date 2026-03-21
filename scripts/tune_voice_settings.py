#!/usr/bin/env python3
"""
Voice Settings Tuning — Generate test audio with different ElevenLabs settings
Creates 4 audio files with different stability/similarity/style combinations
for A/B comparison to find the best Prabhupada voice settings.

Usage:
    python tune_voice_settings.py
    python tune_voice_settings.py --text "Custom text to test"

Requires: voice_config.json with valid voice_id
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "voice_config.json"
TUNING_DIR = PROJECT_ROOT / "tests" / "voice_tuning"

load_dotenv(PROJECT_ROOT / ".env")

# 4 test presets — each emphasizes different qualities
PRESETS = {
    "baseline": {
        "label": "Baseline (balanced)",
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.30,
        "use_speaker_boost": True,
    },
    "expressive": {
        "label": "Expressive (more animated)",
        "stability": 0.40,
        "similarity_boost": 0.85,
        "style": 0.20,
        "use_speaker_boost": True,
    },
    "stable": {
        "label": "Stable (consistent tone)",
        "stability": 0.55,
        "similarity_boost": 0.75,
        "style": 0.40,
        "use_speaker_boost": True,
    },
    "high_fidelity": {
        "label": "High Fidelity (max similarity)",
        "stability": 0.45,
        "similarity_boost": 0.90,
        "style": 0.25,
        "use_speaker_boost": True,
    },
}

# Test texts — one English, one with Sanskrit
TEST_TEXTS = {
    "english": (
        "My dear student, this is very important to understand. "
        "You are not this body. You are the eternal spirit soul. "
        "The body is changing at every moment, but the soul remains the same. "
        "Just like you are the same person from childhood, but your body has completely changed. "
        "So we must understand this distinction between the body and the soul. "
        "This is the beginning of spiritual knowledge."
    ),
    "mixed": (
        "In the Bhagavad Geeta, chapter two, verse twenty, Krishna says very clearly. "
        "The soul is never born and never dies. Na jayate mriyate va kadachin. "
        "It is unborn, eternal, ever-existing, and primeval. "
        "Nityaha shashvato ayam puranaha. Na hanyate hanyamane sharire. "
        "The soul is not slain when the body is slain. "
        "This is the verdict of all Vedic literature."
    ),
}


def generate_tuning_samples(custom_text=None):
    """Generate test audio with each preset."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in .env")
        return

    if not CONFIG_PATH.exists():
        print(f"Error: voice_config.json not found at {CONFIG_PATH}")
        print("Run: python save_voice_config.py <voice_id>")
        return

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    voice_id = config['voice_id']
    model_id = config.get('model', 'eleven_multilingual_v2')

    try:
        from elevenlabs import ElevenLabs
        from elevenlabs.types import VoiceSettings
    except ImportError:
        print("Error: elevenlabs not installed. Run: pip3 install elevenlabs>=1.0.0")
        return

    client = ElevenLabs(api_key=api_key)

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = TUNING_DIR / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)

    # Determine texts to test
    if custom_text:
        texts = {"custom": custom_text}
    else:
        texts = TEST_TEXTS

    print(f"\nVoice Settings Tuning Session")
    print(f"{'='*60}")
    print(f"Voice: {config.get('voice_name', 'Unknown')} ({voice_id})")
    print(f"Model: {model_id}")
    print(f"Output: {session_dir}")
    print(f"Presets: {len(PRESETS)}")
    print(f"Texts: {len(texts)}")
    print(f"Total files: {len(PRESETS) * len(texts)}")
    print(f"{'='*60}\n")

    results = []

    for preset_name, preset in PRESETS.items():
        print(f"\n--- Preset: {preset['label']} ---")
        print(f"    stability={preset['stability']}, similarity={preset['similarity_boost']}, style={preset['style']}")

        voice_settings = VoiceSettings(
            stability=preset['stability'],
            similarity_boost=preset['similarity_boost'],
            style=preset['style'],
            use_speaker_boost=preset['use_speaker_boost'],
        )

        for text_name, text in texts.items():
            filename = f"{preset_name}_{text_name}.mp3"
            output_path = session_dir / filename

            try:
                print(f"    Generating: {filename}...", end=" ", flush=True)

                audio_iterator = client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id=model_id,
                    voice_settings=voice_settings,
                )

                audio_bytes = b"".join(audio_iterator)

                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)

                size_kb = output_path.stat().st_size / 1024
                print(f"OK ({size_kb:.0f} KB)")

                results.append({
                    "preset": preset_name,
                    "text_type": text_name,
                    "file": filename,
                    "size_kb": round(size_kb, 1),
                    "settings": {k: v for k, v in preset.items() if k != "label"},
                })

            except Exception as e:
                print(f"FAILED ({e})")

    # Save session metadata
    meta = {
        "timestamp": timestamp,
        "voice_id": voice_id,
        "model": model_id,
        "presets": PRESETS,
        "texts": texts,
        "results": results,
    }
    with open(session_dir / "tuning_session.json", 'w') as f:
        json.dump(meta, f, indent=2)

    # Print comparison guide
    print(f"\n{'='*60}")
    print(f"Tuning session complete! {len(results)} files generated.")
    print(f"{'='*60}")
    print(f"\nFiles saved to: {session_dir}")
    print(f"\nListening guide:")
    print(f"  1. Play each preset for the SAME text type")
    print(f"  2. Compare: which sounds most like Prabhupada?")
    print(f"  3. Note which preset handles Sanskrit best")
    print(f"\nQuick play (macOS):")
    for r in results:
        print(f"  afplay \"{session_dir / r['file']}\"")

    print(f"\nAfter choosing the best preset, update voice_config.json:")
    print(f"  python save_voice_config.py <voice_id>")
    print(f"  Then edit config/voice_config.json settings to match your pick.")


def apply_preset(preset_name: str):
    """Apply a tuning preset to voice_config.json."""
    if preset_name not in PRESETS:
        print(f"Unknown preset: {preset_name}")
        print(f"Available: {', '.join(PRESETS.keys())}")
        return

    if not CONFIG_PATH.exists():
        print("Error: voice_config.json not found")
        return

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    preset = PRESETS[preset_name]
    config['settings'] = {
        "stability": preset['stability'],
        "similarity_boost": preset['similarity_boost'],
        "style": preset['style'],
        "use_speaker_boost": preset['use_speaker_boost'],
    }
    config['tuning_preset'] = preset_name

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Applied preset '{preset_name}' to voice_config.json")
    print(f"  stability={preset['stability']}, similarity={preset['similarity_boost']}, style={preset['style']}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Tune Prabhupada voice settings')
    parser.add_argument('--text', help='Custom text to test', default=None)
    parser.add_argument('--apply', help='Apply a preset to voice_config.json', default=None)

    args = parser.parse_args()

    if args.apply:
        apply_preset(args.apply)
    else:
        generate_tuning_samples(custom_text=args.text)


if __name__ == "__main__":
    main()
