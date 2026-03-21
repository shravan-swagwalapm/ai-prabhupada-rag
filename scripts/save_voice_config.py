#!/usr/bin/env python3
"""
Save ElevenLabs Voice Configuration
Saves voice_id from ElevenLabs to config/voice_config.json

Usage:
    python save_voice_config.py <voice_id>

Example:
    python save_voice_config.py pqHfZKP75CvOlQylNhV4
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def save_voice_config(voice_id, training_hours=2.5):
    """
    Save ElevenLabs voice configuration

    Args:
        voice_id: Voice ID from ElevenLabs
        training_hours: Hours of training audio used

    Returns:
        dict: Saved configuration
    """
    config_path = Path("/Users/shravantickoo/ai-prabhupada-rag/config/voice_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)

    voice_config = {
        "voice_id": voice_id,
        "voice_name": "Srila Prabhupada",
        "model": "eleven_multilingual_v2",  # Supports Sanskrit/Hindi
        "settings": {
            "stability": 0.5,  # Balance between consistency and expressiveness
            "similarity_boost": 0.75,  # High similarity to training voice
            "style": 0.3,  # Subtle style preservation
            "use_speaker_boost": True  # Enhance voice clarity
        },
        "created_at": datetime.now().isoformat(),
        "training_hours": training_hours,
        "source": "ISKCON Desire Tree - Bhagavad Gita lectures",
        "description": "Authentic voice of A.C. Bhaktivedanta Swami Prabhupada",
        "notes": [
            "Voice trained on manually curated Prabhupada-only audio",
            "Source: Bhagavad Gita lecture series",
            "Manually edited to remove other speakers",
            "High quality for spiritual teachings"
        ]
    }

    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(voice_config, f, indent=2)

    print(f"\n✅ Voice configuration saved!")
    print(f"{'='*60}")
    print(f"📁 Config file: {config_path}")
    print(f"🎙️  Voice ID: {voice_id}")
    print(f"📝 Voice name: Srila Prabhupada")
    print(f"⏱️  Training duration: {training_hours} hours")
    print(f"{'='*60}\n")

    print("📤 Next steps:")
    print("   1. Test the voice: python test_voice_synthesis.py")
    print("   2. Integrate with RAG system")
    print("   3. Query with voice output enabled\n")

    return voice_config


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("❌ Error: voice_id required")
        print("\nUsage:")
        print("   python save_voice_config.py <voice_id>")
        print("\nExample:")
        print("   python save_voice_config.py pqHfZKP75CvOlQylNhV4")
        print("\nHow to get voice_id:")
        print("   1. Go to https://elevenlabs.io/voice-lab")
        print("   2. Upload your training audio")
        print("   3. Create voice profile")
        print("   4. Copy the voice_id from the dashboard")
        return 1

    voice_id = sys.argv[1].strip()

    # Optional: training hours parameter
    training_hours = 2.5
    if len(sys.argv) >= 3:
        try:
            training_hours = float(sys.argv[2])
        except ValueError:
            print(f"⚠️  Invalid training_hours value, using default: 2.5")

    # Validate voice_id format (basic check)
    if len(voice_id) < 10 or ' ' in voice_id:
        print(f"⚠️  Warning: voice_id '{voice_id}' looks unusual")
        print("   Proceeding anyway — verify on ElevenLabs dashboard if synthesis fails")

    # Save configuration
    save_voice_config(voice_id, training_hours)

    return 0


if __name__ == "__main__":
    exit(main())
