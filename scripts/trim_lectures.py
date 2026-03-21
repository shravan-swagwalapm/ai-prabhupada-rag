#!/usr/bin/env python3
"""
Trim Audio Lectures — Remove intros and Q&A sections
Removes first 5 minutes and last 5 minutes from Prabhupada's lecture recordings.
This isolates the core teaching content for higher-quality voice training.

Usage:
    python trim_lectures.py
    python trim_lectures.py --input-dir /path/to/lectures --output-dir /path/to/trimmed
"""

import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from pydub import AudioSegment

# Setup logging
LOG_DIR = Path("/Users/shravantickoo/ai-prabhupada-rag/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"trim_lectures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Trim configuration (milliseconds)
FULL_TRIM_MS = 5 * 60 * 1000      # 5 minutes = 300,000 ms
SHORT_TRIM_MS = 3 * 60 * 1000     # 3 minutes for shorter lectures
MIN_DURATION_MS = 12 * 60 * 1000  # 12 minutes minimum to trim
SHORT_THRESHOLD_MS = 15 * 60 * 1000  # 15 minutes — use shorter trim

DEFAULT_INPUT = Path("/Users/shravantickoo/Downloads/vedabase book transcripts/audio_lectures/bhagavad_gita")
DEFAULT_OUTPUT = Path("/Users/shravantickoo/Downloads/vedabase book transcripts/audio_lectures/trimmed_lectures")


def trim_single_file(input_path: Path, output_path: Path) -> dict:
    """
    Trim a single lecture file.

    Returns metadata dict with before/after durations and action taken.
    """
    try:
        audio = AudioSegment.from_mp3(input_path)
    except Exception as e:
        logger.error(f"Failed to load {input_path.name}: {e}")
        return {"file": input_path.name, "action": "error", "error": str(e)}

    original_duration_ms = len(audio)
    original_duration_min = original_duration_ms / 1000 / 60

    # Skip files shorter than 12 minutes
    if original_duration_ms < MIN_DURATION_MS:
        logger.warning(f"SKIP (too short: {original_duration_min:.1f}min): {input_path.name}")
        return {
            "file": input_path.name,
            "action": "skipped",
            "reason": f"Too short ({original_duration_min:.1f} min < 12 min)",
            "original_duration_min": round(original_duration_min, 1)
        }

    # Choose trim amount based on duration
    if original_duration_ms < SHORT_THRESHOLD_MS:
        # 12-15 min lectures: trim 3 min from each end
        trim_start = SHORT_TRIM_MS
        trim_end = SHORT_TRIM_MS
        trim_type = "short (3min each end)"
    else:
        # 15+ min lectures: trim 5 min from each end
        trim_start = FULL_TRIM_MS
        trim_end = FULL_TRIM_MS
        trim_type = "full (5min each end)"

    # Trim
    trimmed = audio[trim_start:-trim_end] if trim_end > 0 else audio[trim_start:]
    trimmed_duration_ms = len(trimmed)
    trimmed_duration_min = trimmed_duration_ms / 1000 / 60

    # Create output directory (preserving chapter structure)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export as MP3 192kbps
    trimmed.export(output_path, format="mp3", bitrate="192k")

    logger.info(
        f"TRIMMED ({trim_type}): {input_path.name} — "
        f"{original_duration_min:.1f}min → {trimmed_duration_min:.1f}min"
    )

    return {
        "file": input_path.name,
        "action": "trimmed",
        "trim_type": trim_type,
        "original_duration_min": round(original_duration_min, 1),
        "trimmed_duration_min": round(trimmed_duration_min, 1),
        "removed_min": round(original_duration_min - trimmed_duration_min, 1),
        "output": str(output_path)
    }


def trim_all_lectures(input_dir: Path, output_dir: Path):
    """
    Trim all MP3 lectures in directory, preserving chapter subdirectory structure.
    Idempotent: skips files that already exist in output.
    """
    logger.info(f"Trim Lectures — Starting")
    logger.info(f"{'='*70}")
    logger.info(f"Input:  {input_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"{'='*70}")

    # Find all MP3 files recursively
    mp3_files = sorted(input_dir.rglob("*.mp3"))

    if not mp3_files:
        logger.error(f"No MP3 files found in {input_dir}")
        return

    logger.info(f"Found {len(mp3_files)} MP3 files\n")

    results = {
        "started_at": datetime.now().isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "total_files": len(mp3_files),
        "trimmed": 0,
        "skipped_short": 0,
        "skipped_exists": 0,
        "errors": 0,
        "files": []
    }

    for i, mp3_path in enumerate(mp3_files, 1):
        # Preserve relative path (chapter_XX/filename.mp3)
        relative = mp3_path.relative_to(input_dir)
        output_path = output_dir / relative

        # Idempotent: skip if already trimmed
        if output_path.exists():
            logger.info(f"[{i}/{len(mp3_files)}] EXISTS (skipping): {relative}")
            results["skipped_exists"] += 1
            results["files"].append({
                "file": str(relative),
                "action": "skipped_exists"
            })
            continue

        logger.info(f"[{i}/{len(mp3_files)}] Processing: {relative}")

        file_result = trim_single_file(mp3_path, output_path)
        results["files"].append(file_result)

        if file_result["action"] == "trimmed":
            results["trimmed"] += 1
        elif file_result["action"] == "skipped":
            results["skipped_short"] += 1
        elif file_result["action"] == "error":
            results["errors"] += 1

    results["completed_at"] = datetime.now().isoformat()

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info(f"TRIM COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Total MP3 files:   {results['total_files']}")
    logger.info(f"Trimmed:           {results['trimmed']}")
    logger.info(f"Skipped (short):   {results['skipped_short']}")
    logger.info(f"Skipped (exists):  {results['skipped_exists']}")
    logger.info(f"Errors:            {results['errors']}")
    logger.info(f"{'='*70}")

    # Save results log
    results_file = output_dir / "trim_results.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to: {results_file}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Trim lecture audio — remove intros and Q&A")
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT),
        help="Directory containing lecture MP3s (with chapter_XX subdirectories)"
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT),
        help="Output directory for trimmed files"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return 1

    trim_all_lectures(input_dir, output_dir)
    return 0


if __name__ == "__main__":
    exit(main())
