#!/usr/bin/env python3
"""
Simple ISKCON Desire Tree Audio Scraper
Downloads Srila Prabhupada's Bhagavad Gita lectures

Usage:
    python scrape_iskcon_audio_simple.py
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
from datetime import datetime
from urllib.parse import quote
import re

def log_message(msg, log_file):
    """Log to console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(log_file, 'a') as f:
        f.write(full_msg + '\n')

def get_chapter_url(chapter_num):
    """Build URL for chapter"""
    base = "https://audio.iskcondesiretree.com"
    path = f"/01_-_Srila_Prabhupada/01_-_Lectures/01_-_English/01_-_Topic_wise/Bhagavad_Gita/Chapter-{chapter_num:02d}"
    encoded = quote(path, safe='/')
    return f"{base}/index.php?q=f&f={encoded}"

def extract_mp3_urls(html_content, base_url):
    """Extract all MP3 URLs from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    mp3_links = []

    # Find all links ending in .mp3
    for link in soup.find_all('a', href=re.compile(r'\.mp3$', re.IGNORECASE)):
        href = link.get('href', '')

        # Skip play links
        if 'index.php?q=m' in href:
            continue

        # Make absolute URL
        if href.startswith('/'):
            full_url = base_url + href
        else:
            full_url = base_url + '/' + href

        # Get title
        title_elem = link.find('font', {'size': '2'})
        title = title_elem.get_text(strip=True) if title_elem else Path(href).name

        mp3_links.append({
            'url': full_url,
            'title': title,
            'filename': Path(href).name
        })

    return mp3_links

def download_file(url, filepath, log_file):
    """Download a file"""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size_mb = filepath.stat().st_size / (1024 * 1024)
        return True, size_mb
    except Exception as e:
        log_message(f"❌ Download error: {str(e)}", log_file)
        return False, 0

def main():
    # Setup
    base_url = "https://audio.iskcondesiretree.com"
    output_dir = Path("/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/raw_lectures/bhagavad_gita")
    log_dir = Path("/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"simple_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    print("\n" + "="*70)
    print("🕉️  Simple ISKCON Audio Scraper")
    print("="*70)
    print(f"\nDownloading to: {output_dir}")
    print(f"Log file: {log_file}\n")

    total_downloaded = 0
    total_failed = 0
    total_size = 0

    # Download chapter by chapter
    for chapter in range(1, 19):  # Chapters 1-18
        log_message(f"\n{'='*60}", log_file)
        log_message(f"Chapter {chapter:02d}", log_file)
        log_message(f"{'='*60}", log_file)

        # Create chapter directory
        chapter_dir = output_dir / f"chapter_{chapter:02d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)

        # Get chapter page
        chapter_url = get_chapter_url(chapter)
        log_message(f"Fetching: {chapter_url}", log_file)

        try:
            response = requests.get(chapter_url, timeout=30)
            response.raise_for_status()

            # Extract MP3 URLs
            mp3_links = extract_mp3_urls(response.text, base_url)
            log_message(f"Found {len(mp3_links)} lectures", log_file)

            if not mp3_links:
                log_message("⚠️  No lectures found!", log_file)
                continue

            # Download each lecture
            for i, mp3 in enumerate(mp3_links, 1):
                filepath = chapter_dir / mp3['filename']

                # Skip if already downloaded
                if filepath.exists() and filepath.stat().st_size > 0:
                    log_message(f"[{i}/{len(mp3_links)}] ⏭️  Skip: {mp3['title']}", log_file)
                    continue

                log_message(f"[{i}/{len(mp3_links)}] 📥 {mp3['title']}", log_file)

                success, size_mb = download_file(mp3['url'], filepath, log_file)

                if success:
                    total_downloaded += 1
                    total_size += size_mb
                    log_message(f"   ✅ Downloaded ({size_mb:.2f} MB)", log_file)
                else:
                    total_failed += 1

                # Rate limiting
                time.sleep(2)

            log_message(f"✅ Chapter {chapter} complete", log_file)

            # Break between chapters
            if chapter < 18:
                time.sleep(5)

        except Exception as e:
            log_message(f"❌ Chapter {chapter} error: {str(e)}", log_file)
            total_failed += 1
            continue

    # Final summary
    log_message(f"\n{'='*70}", log_file)
    log_message(f"🎉 COMPLETE!", log_file)
    log_message(f"{'='*70}", log_file)
    log_message(f"Downloaded: {total_downloaded}", log_file)
    log_message(f"Failed: {total_failed}", log_file)
    log_message(f"Total size: {total_size:.2f} MB ({total_size/1024:.2f} GB)", log_file)
    log_message(f"{'='*70}\n", log_file)

    print(f"\n✅ Done! Check logs at: {log_file}")
    print(f"📁 Files at: {output_dir}\n")

if __name__ == "__main__":
    main()
