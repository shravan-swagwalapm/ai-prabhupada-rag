#!/usr/bin/env python3
"""
PrabhupadaAI Demo Player — Play pre-recorded answers without running the RAG pipeline.

For live demos: skip the 30-second pipeline and play cached Prabhupada voice answers instantly.
Reads from question_index.json and plays MP3s via macOS afplay.

Usage:
    python3 scripts/demo_player.py                  # Interactive menu
    python3 scripts/demo_player.py 7                # Play recording #7 directly
    python3 scripts/demo_player.py karma            # Search by keyword and play best match
    python3 scripts/demo_player.py --list           # Just list all available recordings
    python3 scripts/demo_player.py --stop           # Stop any currently playing audio
"""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

# Recordings index location
INDEX_PATH = Path.home() / "Downloads" / "vedabase book transcripts" / "ai prabhupada recordings" / "question_index.json"


def load_index() -> dict:
    """Load the question index."""
    if not INDEX_PATH.exists():
        print(f"Error: question_index.json not found at {INDEX_PATH}")
        sys.exit(1)
    with open(INDEX_PATH, 'r') as f:
        return json.load(f)


def stop_playback():
    """Stop any currently playing afplay process."""
    os.system("killall afplay 2>/dev/null")


def play_recording(recording_dir: str, entry: dict):
    """Play a recording and show metadata."""
    filepath = Path(recording_dir) / entry['file']

    if not filepath.exists():
        print(f"\n  File not found: {filepath}")
        return

    # Stop any existing playback
    stop_playback()

    # Display what's playing
    print()
    print("  " + "=" * 64)
    print(f"  Q: {entry['question']}")
    print("  " + "-" * 64)
    print(f"  Duration: {entry['duration_approx']}  |  Relevance: {entry['top_relevance']:.1%}")
    print(f"  Sources: {', '.join(entry.get('primary_sources', [])[:2])}")
    if entry.get('key_verses'):
        print(f"  Verses: {', '.join(entry['key_verses'][:3])}")
    print("  " + "=" * 64)
    print(f"\n  Playing Prabhupada's voice...  (Ctrl+C to stop)\n")

    try:
        # Play audio — blocks until complete or interrupted
        subprocess.run(["afplay", str(filepath)], check=True)
        print("  Playback complete.\n")
    except KeyboardInterrupt:
        stop_playback()
        print("\n  Stopped.\n")
    except FileNotFoundError:
        print("  Error: afplay not found. Open the file manually:")
        print(f"  open \"{filepath}\"\n")


def keyword_search(questions: list, query: str) -> list:
    """Search questions by keyword match. Returns matching entries sorted by relevance."""
    query_lower = query.lower().strip()
    scored = []

    for entry in questions:
        score = 0
        # Check keywords
        for kw in entry.get('keywords', []):
            if query_lower in kw.lower():
                score += 2
        # Check question text
        if query_lower in entry['question'].lower():
            score += 3
        # Check primary sources
        for src in entry.get('primary_sources', []):
            if query_lower in src.lower():
                score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def print_menu(questions: list):
    """Print the numbered question menu."""
    print()
    print("  " + "=" * 64)
    print("  PrabhupadaAI Demo Player")
    print("  " + "=" * 64)
    print()

    for entry in questions:
        # Truncate long questions for display
        q = entry['question']
        if len(q) > 70:
            q = q[:67] + "..."
        print(f"  [{entry['id']:>2}]  {q}")
        print(f"       {entry['duration_approx']}  |  {entry['file']}")
        print()

    print("  " + "-" * 64)
    print("  Enter a number to play, a keyword to search, or 'q' to quit.")
    print("  " + "-" * 64)


def interactive_mode(data: dict):
    """Run the interactive menu loop."""
    questions = data['questions']
    recording_dir = data['recordings_dir']

    print_menu(questions)

    while True:
        try:
            choice = input("\n  > ").strip()
        except (KeyboardInterrupt, EOFError):
            stop_playback()
            print("\n")
            break

        if not choice:
            continue

        if choice.lower() in ('q', 'quit', 'exit'):
            stop_playback()
            break

        if choice.lower() == 'list':
            print_menu(questions)
            continue

        if choice.lower() == 'stop':
            stop_playback()
            print("  Stopped playback.")
            continue

        # Try as a number first
        try:
            num = int(choice)
            matches = [e for e in questions if e['id'] == num]
            if matches:
                play_recording(recording_dir, matches[0])
                continue
            else:
                print(f"  No recording #{num}. Available: 1-{len(questions)}")
                continue
        except ValueError:
            pass

        # Keyword search
        results = keyword_search(questions, choice)
        if not results:
            print(f"  No matches for '{choice}'. Try another keyword.")
            continue

        if len(results) == 1:
            play_recording(recording_dir, results[0])
        else:
            print(f"\n  Found {len(results)} matches for '{choice}':\n")
            for entry in results:
                q = entry['question']
                if len(q) > 60:
                    q = q[:57] + "..."
                print(f"  [{entry['id']:>2}]  {q}")
            print("\n  Enter a number to play.")


def main():
    data = load_index()
    questions = data['questions']
    recording_dir = data['recordings_dir']

    # Handle --stop flag
    if len(sys.argv) > 1 and sys.argv[1] == '--stop':
        stop_playback()
        print("  Stopped all playback.")
        return

    # Handle --list flag
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        print_menu(questions)
        return

    # Handle direct number argument: python3 demo_player.py 7
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            num = int(arg)
            matches = [e for e in questions if e['id'] == num]
            if matches:
                play_recording(recording_dir, matches[0])
                return
            else:
                print(f"  No recording #{num}. Available: 1-{len(questions)}")
                return
        except ValueError:
            pass

        # Handle keyword argument: python3 demo_player.py karma
        results = keyword_search(questions, arg)
        if results:
            play_recording(recording_dir, results[0])
            return
        else:
            print(f"  No matches for '{arg}'.")
            return

    # No arguments — interactive mode
    interactive_mode(data)


if __name__ == "__main__":
    main()
