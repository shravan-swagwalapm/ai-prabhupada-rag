#!/usr/bin/env python3
"""
Live Progress Monitor for ISKCON Audio Scraper
Shows real-time progress with progress bars

Usage:
    python monitor_scraping_progress.py
"""

import os
import time
from pathlib import Path
from datetime import datetime
import sys

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_terminal_width():
    """Get terminal width for progress bar"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def progress_bar(current, total, width=50, label="Progress"):
    """Generate a progress bar"""
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100

    filled = int(width * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)

    return f"{label}: [{bar}] {current}/{total} ({percentage:.1f}%)"

def count_files(base_dir):
    """Count MP3 files per chapter and total"""
    base_path = Path(base_dir)

    chapter_counts = {}
    total_files = 0
    total_size = 0

    for chapter_num in range(1, 19):
        chapter_dir = base_path / f"chapter_{chapter_num:02d}"
        if chapter_dir.exists():
            mp3_files = list(chapter_dir.glob("*.mp3"))
            count = len(mp3_files)
            size = sum(f.stat().st_size for f in mp3_files)

            chapter_counts[chapter_num] = {
                'count': count,
                'size': size
            }
            total_files += count
            total_size += size
        else:
            chapter_counts[chapter_num] = {'count': 0, 'size': 0}

    return chapter_counts, total_files, total_size

def get_current_chapter_from_log(log_dir):
    """Get current chapter being processed from log file"""
    log_path = Path(log_dir)

    # Find most recent log file
    log_files = sorted(log_path.glob("simple_scrape_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        return None

    # Read last few lines
    with open(log_files[0], 'r') as f:
        lines = f.readlines()

        # Look for chapter number in recent lines
        for line in reversed(lines[-50:]):
            if "Chapter" in line and "=" in line:
                try:
                    # Extract chapter number
                    import re
                    match = re.search(r'Chapter\s+(\d+)', line)
                    if match:
                        return int(match.group(1))
                except:
                    pass

    return None

def format_size(bytes_size):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"

def monitor_progress():
    """Main monitoring loop"""
    base_dir = "/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/raw_lectures/bhagavad_gita"
    log_dir = "/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/logs"

    total_chapters = 18
    estimated_total_lectures = 450  # Rough estimate

    start_time = time.time()

    print("\n🕉️  ISKCON Audio Scraper - Live Progress Monitor")
    print("="*70)
    print("\nPress Ctrl+C to exit (scraping will continue in background)\n")

    try:
        while True:
            clear_screen()

            # Header
            print("\n" + "="*70)
            print("🕉️  ISKCON AUDIO SCRAPER - LIVE PROGRESS")
            print("="*70)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70 + "\n")

            # Get stats
            chapter_counts, total_files, total_size = count_files(base_dir)
            current_chapter = get_current_chapter_from_log(log_dir)

            # Calculate chapters completed (those with files)
            chapters_completed = sum(1 for c in chapter_counts.values() if c['count'] > 0)

            # Overall progress
            print("📊 OVERALL PROGRESS")
            print("-" * 70)
            print(progress_bar(chapters_completed, total_chapters, 50, "Chapters"))
            print(progress_bar(total_files, estimated_total_lectures, 50, "Lectures "))
            print()

            # Stats
            print("📈 STATISTICS")
            print("-" * 70)
            print(f"   Total Files Downloaded: {total_files}")
            print(f"   Total Size: {format_size(total_size)}")
            print(f"   Chapters Complete: {chapters_completed}/{total_chapters}")
            if current_chapter:
                print(f"   Currently Processing: Chapter {current_chapter:02d}")
            print()

            # Chapter breakdown
            print("📚 CHAPTER BREAKDOWN")
            print("-" * 70)

            # Show in rows of 6
            for row_start in range(0, 18, 6):
                row_chapters = range(row_start + 1, min(row_start + 7, 19))

                for ch in row_chapters:
                    count = chapter_counts[ch]['count']
                    status = "✅" if count > 0 else "⏳"
                    current_marker = "📍" if ch == current_chapter else "  "
                    print(f"   {current_marker} Ch{ch:02d}: {status} {count:3d} files", end="  ")
                print()

            print()

            # Recent activity (from log)
            print("📋 RECENT ACTIVITY")
            print("-" * 70)

            log_files = sorted(Path(log_dir).glob("simple_scrape_*.log"),
                             key=lambda x: x.stat().st_mtime, reverse=True)

            if log_files:
                with open(log_files[0], 'r') as f:
                    lines = f.readlines()
                    # Show last 5 non-empty lines
                    recent = [l.strip() for l in lines[-8:] if l.strip() and not l.strip().startswith('=')]
                    for line in recent[-5:]:
                        # Truncate long lines
                        if len(line) > 68:
                            line = line[:65] + "..."
                        print(f"   {line}")

            print()
            print("="*70)
            print("⏸️  Press Ctrl+C to exit monitor (scraping continues)")
            print("="*70)

            # Wait before refresh
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n✅ Progress monitor stopped.")
        print("📥 Scraping continues in background.")
        print(f"📁 Files: {base_dir}")
        print(f"📊 Total downloaded so far: {total_files} files ({format_size(total_size)})\n")

if __name__ == "__main__":
    monitor_progress()
