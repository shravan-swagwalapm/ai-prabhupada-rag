#!/usr/bin/env python3
"""
Merge Audio Clips for ElevenLabs Voice Training
Combines trimmed Prabhupada lecture clips into a single 3-hour training MP3.

Changes from v1:
- Default input: trimmed_lectures/ (not edited_clips/)
- Export format: MP3 192kbps (not WAV) — 250MB vs 1.9GB for 3 hours
- Target: 3.0 hours (ElevenLabs sweet spot for quality)
- Shuffles files across chapters for voice variety
- Adds 0.5s silence between clips for natural separation

Usage:
    python merge_audio_for_training.py
    python merge_audio_for_training.py --target-hours 3.0 --output custom_output.mp3
"""

import os
import json
import random
import argparse
from pathlib import Path
from datetime import datetime
from pydub import AudioSegment
from pydub.effects import normalize

DEFAULT_INPUT = "/Users/shravantickoo/Downloads/vedabase book transcripts/audio_lectures/trimmed_lectures"
DEFAULT_OUTPUT = "/Users/shravantickoo/Downloads/vedabase book transcripts/audio_lectures/training/prabhupada_training_3hr.mp3"


class AudioMerger:
    def __init__(self, input_dir, output_file, target_hours=3.0, shuffle=True):
        """
        Initialize audio merger.

        Args:
            input_dir: Directory containing trimmed audio clips
            output_file: Path for output training file
            target_hours: Target duration in hours (default: 3.0)
            shuffle: Whether to shuffle files across chapters (default: True)
        """
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.target_hours = target_hours
        self.target_ms = int(target_hours * 60 * 60 * 1000)
        self.shuffle = shuffle

        # 0.5 second silence between clips
        self.silence_gap = AudioSegment.silent(duration=500)

        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "target_hours": target_hours,
            "shuffled": shuffle,
            "format": "mp3",
            "bitrate": "192k",
            "source_clips": [],
            "total_duration_hours": 0,
            "total_clips": 0,
            "clips_used": 0
        }

    def get_audio_files(self):
        """Get all MP3 files from input directory (recursively across chapters)."""
        audio_files = sorted(self.input_dir.rglob("*.mp3"))

        # Also check for WAV files (in case user has edited clips)
        audio_files.extend(sorted(self.input_dir.rglob("*.wav")))

        if self.shuffle:
            random.seed(42)  # Reproducible shuffle
            random.shuffle(audio_files)
        else:
            audio_files.sort()

        return audio_files

    def merge_audio_clips(self):
        """Merge audio clips into single training file."""
        print(f"\n🎵 Audio Merge for Voice Training")
        print(f"{'='*60}")
        print(f"Input:   {self.input_dir}")
        print(f"Output:  {self.output_file}")
        print(f"Target:  {self.target_hours} hours")
        print(f"Format:  MP3 192kbps")
        print(f"Shuffle: {'Yes (seed=42)' if self.shuffle else 'No'}")
        print(f"{'='*60}\n")

        audio_files = self.get_audio_files()

        if not audio_files:
            print(f"No audio files found in {self.input_dir}")
            print("   Run trim_lectures.py first to generate trimmed files.")
            return False

        print(f"Found {len(audio_files)} audio clips")
        self.metadata['total_clips'] = len(audio_files)

        combined = AudioSegment.empty()
        current_duration_ms = 0

        for i, audio_file in enumerate(audio_files, 1):
            if current_duration_ms >= self.target_ms:
                print(f"\n✅ Reached target duration of {self.target_hours} hours")
                break

            try:
                print(f"[{i}/{len(audio_files)}] Loading: {audio_file.name}")

                # Load based on extension
                ext = audio_file.suffix.lower()
                if ext == '.mp3':
                    segment = AudioSegment.from_mp3(audio_file)
                elif ext == '.wav':
                    segment = AudioSegment.from_wav(audio_file)
                else:
                    segment = AudioSegment.from_file(audio_file)

                segment_duration_sec = len(segment) / 1000
                print(f"    Duration: {segment_duration_sec:.1f}s")

                # Add silence gap between clips (skip for first clip)
                if len(combined) > 0:
                    combined += self.silence_gap

                combined += segment
                current_duration_ms += len(segment) + 500  # Include gap

                self.metadata['source_clips'].append({
                    "filename": str(audio_file.relative_to(self.input_dir)),
                    "duration_seconds": round(segment_duration_sec, 1),
                    "file_size_mb": round(audio_file.stat().st_size / (1024 * 1024), 2)
                })
                self.metadata['clips_used'] += 1

            except Exception as e:
                print(f"    ⚠️  Error loading {audio_file.name}: {e}")
                continue

        if len(combined) == 0:
            print("\nNo audio could be loaded")
            return False

        final_duration_hours = len(combined) / (1000 * 60 * 60)
        self.metadata['total_duration_hours'] = round(final_duration_hours, 2)

        print(f"\n{'='*60}")
        print(f"Merged {self.metadata['clips_used']} clips")
        print(f"Total duration: {final_duration_hours:.2f} hours ({len(combined)/1000/60:.1f} min)")
        print(f"{'='*60}\n")

        # Normalize audio levels
        print("Normalizing audio levels...")
        combined = normalize(combined)

        # Create output directory
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Export as MP3 192kbps
        print(f"Exporting to: {self.output_file}")
        print("   Format: MP3 192kbps (ElevenLabs compatible)")
        combined.export(
            self.output_file,
            format="mp3",
            bitrate="192k"
        )

        output_size_mb = self.output_file.stat().st_size / (1024 * 1024)
        print(f"   File size: {output_size_mb:.1f} MB")

        # Save metadata
        metadata_file = self.output_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        print(f"Metadata saved to: {metadata_file}")

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Audio merge complete!")
        print(f"{'='*60}")
        print(f"File:     {self.output_file}")
        print(f"Duration: {final_duration_hours:.2f} hours")
        print(f"Clips:    {self.metadata['clips_used']}/{self.metadata['total_clips']}")
        print(f"Size:     {output_size_mb:.1f} MB")

        if final_duration_hours < 2.0:
            print(f"\n⚠️  Duration ({final_duration_hours:.2f}h) < 2 hours recommended minimum")
        elif final_duration_hours > 3.5:
            print(f"\n⚠️  Duration ({final_duration_hours:.2f}h) > 3.5 hours — may exceed ElevenLabs limit")

        print(f"\nNext steps:")
        print(f"   1. Listen to {self.output_file} to verify quality")
        print(f"   2. Upload to ElevenLabs: https://elevenlabs.io/voice-lab")
        print(f"   3. Create voice profile 'Srila Prabhupada'")
        print(f"   4. Copy voice_id and run: python save_voice_config.py <voice_id>")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Merge trimmed audio clips for ElevenLabs voice training'
    )
    parser.add_argument(
        '--input-dir',
        default=DEFAULT_INPUT,
        help='Directory with trimmed audio clips'
    )
    parser.add_argument(
        '--output',
        default=DEFAULT_OUTPUT,
        help='Output file path (MP3)'
    )
    parser.add_argument(
        '--target-hours',
        type=float,
        default=3.0,
        help='Target duration in hours (default: 3.0)'
    )
    parser.add_argument(
        '--no-shuffle',
        action='store_true',
        help='Disable file shuffling (merge in order instead)'
    )

    args = parser.parse_args()

    merger = AudioMerger(
        input_dir=args.input_dir,
        output_file=args.output,
        target_hours=args.target_hours,
        shuffle=not args.no_shuffle
    )

    success = merger.merge_audio_clips()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
