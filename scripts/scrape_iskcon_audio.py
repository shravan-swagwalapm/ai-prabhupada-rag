#!/usr/bin/env python3
"""
ISKCON Desire Tree Audio Scraper (Improved)
Downloads Srila Prabhupada's Bhagavad Gita lectures from audio.iskcondesiretree.com

Usage:
    python scrape_iskcon_audio.py
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
from datetime import datetime
from urllib.parse import urljoin, quote, unquote
import re
import sys

class ISKCONAudioScraper:
    def __init__(self, output_dir, max_workers=3):
        """
        Initialize ISKCON audio scraper

        Args:
            output_dir: Base directory for downloaded audio files
            max_workers: Number of parallel download threads (default: 3 for respectful scraping)
        """
        self.base_url = "https://audio.iskcondesiretree.com"
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Progress tracking
        self.progress_file = Path("/Users/shravantickoo/ai-prabhupada-rag/metadata/iskcon_audio_progress.json")
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress = self.load_progress()

        # Logs
        self.log_dir = Path("/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log(self, message):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def load_progress(self):
        """Load progress from JSON file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "downloaded": {},  # URL -> filepath mapping
            "failed": [],
            "total_size_mb": 0,
            "last_updated": None,
            "chapters_completed": []
        }

    def save_progress(self):
        """Save progress to JSON file"""
        self.progress["last_updated"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def build_chapter_url(self, chapter_num):
        """Build URL for a specific Bhagavad Gita chapter"""
        chapter_str = f"Chapter-{chapter_num:02d}"
        path = f"/01_-_Srila_Prabhupada/01_-_Lectures/01_-_English/01_-_Topic_wise/Bhagavad_Gita/{chapter_str}"
        # URL encode the path
        encoded_path = quote(path, safe='/')
        return f"{self.base_url}/index.php?q=f&f={encoded_path}"

    def fetch_page(self, url, retry=3):
        """Fetch webpage with retry logic"""
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                self.log(f"Attempt {attempt + 1}/{retry} failed for {url}: {e}")
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def parse_file_size(self, size_text):
        """Parse file size from text like '4.02 MB · MP3'"""
        match = re.search(r'([\d.]+)\s*(MB|KB|GB)', size_text, re.IGNORECASE)
        if match:
            size = float(match.group(1))
            unit = match.group(2).upper()

            # Convert to MB
            if unit == 'KB':
                size = size / 1024
            elif unit == 'GB':
                size = size * 1024

            return size
        return 0

    def extract_mp3_links(self, chapter_url, chapter_num):
        """
        Extract MP3 download links and metadata from chapter page

        Returns:
            list: List of dictionaries with MP3 metadata
        """
        self.log(f"\n{'='*60}")
        self.log(f"Fetching Chapter {chapter_num:02d}: {chapter_url}")
        self.log(f"{'='*60}")

        try:
            response = self.fetch_page(chapter_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            lectures = []

            # Find all table rows that contain MP3 files
            # Look for <a> tags with href ending in .mp3
            mp3_links = soup.find_all('a', href=re.compile(r'\.mp3$', re.IGNORECASE))

            for link in mp3_links:
                try:
                    href = link.get('href')
                    if not href:
                        continue

                    # Skip the play links (those with index.php?q=m&m=)
                    if 'index.php?q=m' in href:
                        continue

                    # Make absolute URL
                    if href.startswith('/'):
                        mp3_url = f"{self.base_url}{href}"
                    else:
                        mp3_url = urljoin(self.base_url, href)

                    # Extract title from link text
                    title_elem = link.find('font', {'size': '2'})
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        title = link.get_text(strip=True) or Path(href).stem

                    # Find the parent table row to get file size
                    parent_row = link.find_parent('table')
                    file_size = "Unknown"
                    size_mb = 0

                    if parent_row:
                        # Look for file size in the same table
                        size_elem = parent_row.find('font', string=re.compile(r'MB|KB|GB', re.IGNORECASE))
                        if size_elem:
                            file_size = size_elem.get_text(strip=True)
                            size_mb = self.parse_file_size(file_size)

                    # Extract date and location from title
                    # Format: "SP BG 01-01 London 1973-07-07 The Material World..."
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
                    location_match = re.search(r'(London|Los Angeles|New York|Bombay|Vrindavan|Mayapur|Paris|Melbourne|Tokyo|Moscow)', title, re.IGNORECASE)

                    verse_match = re.search(r'BG\s+([\d-]+)', title)

                    lecture_data = {
                        "url": mp3_url,
                        "title": title,
                        "chapter": chapter_num,
                        "verse": verse_match.group(1) if verse_match else None,
                        "file_size": file_size,
                        "size_mb": size_mb,
                        "date": date_match.group(1) if date_match else None,
                        "location": location_match.group(1) if location_match else None,
                        "filename": Path(href).name
                    }

                    lectures.append(lecture_data)

                except Exception as e:
                    self.log(f"Error processing link: {e}")
                    continue

            self.log(f"Found {len(lectures)} lectures in Chapter {chapter_num:02d}")

            # Log sample lectures for verification
            if lectures:
                self.log(f"\nSample lectures:")
                for i, lec in enumerate(lectures[:3], 1):
                    self.log(f"  {i}. {lec['title']} ({lec['file_size']})")

            return lectures

        except Exception as e:
            self.log(f"❌ Error fetching chapter {chapter_num}: {e}")
            return []

    def download_lecture(self, lecture_data, chapter_dir):
        """
        Download a single lecture MP3 file

        Args:
            lecture_data: Dictionary with lecture metadata
            chapter_dir: Directory to save the lecture

        Returns:
            bool: True if successful, False otherwise
        """
        url = lecture_data['url']

        # Check if already downloaded
        if url in self.progress['downloaded']:
            filepath = Path(self.progress['downloaded'][url])
            if filepath.exists() and filepath.stat().st_size > 0:
                self.log(f"⏭️  Skipping (already downloaded): {lecture_data['title']}")
                return True

        try:
            # Use original filename from URL
            filename = lecture_data['filename']
            filepath = chapter_dir / filename

            # Download with progress
            self.log(f"📥 Downloading: {lecture_data['title']}")
            self.log(f"   Size: {lecture_data['file_size']}")

            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Show progress for large files
                        if total_size > 0 and downloaded % (1024 * 1024) == 0:  # Every 1MB
                            progress_pct = (downloaded / total_size) * 100
                            self.log(f"   Progress: {progress_pct:.1f}%")

            # Save metadata alongside audio file
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(lecture_data, f, indent=2)

            # Update progress
            actual_size_mb = filepath.stat().st_size / (1024 * 1024)
            self.progress['downloaded'][url] = str(filepath)
            self.progress['total_size_mb'] += actual_size_mb
            self.save_progress()

            self.log(f"✅ Downloaded: {filename} ({actual_size_mb:.2f} MB)")
            return True

        except Exception as e:
            self.log(f"❌ Failed to download {lecture_data['title']}: {e}")
            self.progress['failed'].append({
                "url": url,
                "title": lecture_data['title'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.save_progress()
            return False

    def scrape_chapter(self, chapter_num):
        """Scrape all lectures from a specific chapter"""
        self.log(f"\n{'='*70}")
        self.log(f"🕉️  CHAPTER {chapter_num:02d} - Starting Download")
        self.log(f"{'='*70}")

        # Create chapter directory
        chapter_dir = self.output_dir / f"chapter_{chapter_num:02d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)

        # Get chapter URL
        chapter_url = self.build_chapter_url(chapter_num)

        # Extract all MP3 links
        lectures = self.extract_mp3_links(chapter_url, chapter_num)

        if not lectures:
            self.log(f"⚠️  No lectures found for Chapter {chapter_num:02d}")
            return 0, 0

        self.log(f"\n📋 Total lectures to download: {len(lectures)}")

        # Download lectures
        successful = 0
        failed = 0

        for i, lecture in enumerate(lectures, 1):
            self.log(f"\n[{i}/{len(lectures)}] Processing: {lecture['title']}")

            if self.download_lecture(lecture, chapter_dir):
                successful += 1
            else:
                failed += 1

            # Rate limiting: wait 2 seconds between downloads
            if i < len(lectures):
                time.sleep(2)

        # Mark chapter as completed
        if chapter_num not in self.progress['chapters_completed']:
            self.progress['chapters_completed'].append(chapter_num)
            self.save_progress()

        self.log(f"\n{'='*70}")
        self.log(f"✅ Chapter {chapter_num:02d} Complete!")
        self.log(f"   Successful: {successful}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {(successful/(successful+failed)*100):.1f}%")
        self.log(f"{'='*70}")

        return successful, failed

    def scrape_all_chapters(self, start_chapter=1, end_chapter=18):
        """Scrape all Bhagavad Gita chapters"""
        self.log(f"\n{'='*70}")
        self.log(f"🕉️  ISKCON DESIRE TREE AUDIO SCRAPER")
        self.log(f"{'='*70}")
        self.log(f"📖 Target: Bhagavad Gita Chapters {start_chapter}-{end_chapter}")
        self.log(f"📁 Output: {self.output_dir}")
        self.log(f"⚙️  Workers: {self.max_workers} (sequential for stability)")
        self.log(f"{'='*70}\n")

        start_time = time.time()
        total_successful = 0
        total_failed = 0

        # Sequential scraping (more respectful to server)
        for chapter in range(start_chapter, end_chapter + 1):
            try:
                successful, failed = self.scrape_chapter(chapter)
                total_successful += successful
                total_failed += failed

                # Break between chapters
                if chapter < end_chapter:
                    self.log(f"\n⏸️  Waiting 5 seconds before next chapter...")
                    time.sleep(5)

            except Exception as e:
                self.log(f"❌ Error scraping chapter {chapter}: {e}")
                total_failed += 1
                continue

        # Final summary
        elapsed = time.time() - start_time
        self.log(f"\n{'='*70}")
        self.log(f"🎉 SCRAPING COMPLETE!")
        self.log(f"{'='*70}")
        self.log(f"📊 Statistics:")
        self.log(f"   Total downloads: {total_successful}")
        self.log(f"   Total failures: {total_failed}")
        self.log(f"   Success rate: {(total_successful/(total_successful+total_failed)*100):.1f}%")
        self.log(f"   Total size: {self.progress['total_size_mb']:.2f} MB")
        self.log(f"   Chapters completed: {len(self.progress['chapters_completed'])}/18")
        self.log(f"   Time elapsed: {elapsed/60:.1f} minutes")
        self.log(f"{'='*70}")
        self.log(f"\n📁 Files saved to: {self.output_dir}")
        self.log(f"📊 Progress tracked in: {self.progress_file}")
        self.log(f"📋 Log file: {self.log_file}")

        return total_successful, total_failed


def main():
    """Main entry point"""
    output_dir = Path("/Users/shravantickoo/Downloads/vedabase-complete/audio_lectures/raw_lectures/bhagavad_gita")

    scraper = ISKCONAudioScraper(output_dir, max_workers=3)

    print("\n" + "="*70)
    print("🕉️  Srila Prabhupada Audio Scraper")
    print("="*70)
    print("\nThis will download all Bhagavad Gita lectures (Chapters 1-18)")
    print("from ISKCON Desire Tree.")
    print(f"\nEstimated time: 2-4 hours")
    print(f"Expected: 50-100 lectures (~10-20 hours of audio)")
    print("\nPress Ctrl+C to stop at any time. Progress is saved!")
    print("="*70 + "\n")

    try:
        # Scrape all 18 chapters
        successful, failed = scraper.scrape_all_chapters(start_chapter=1, end_chapter=18)

        if successful > 0:
            print("\n✅ Scraping complete!")
            print(f"\n📁 Audio files: {output_dir}")
            print(f"📊 Progress: {scraper.progress_file}")
            print(f"📋 Logs: {scraper.log_file}")

            print("\n🎯 Next steps:")
            print("   1. Check the downloaded files in the output directory")
            print("   2. Start editing in Audacity to remove non-Prabhupada sections")
            print("   3. Run: python3 scripts/merge_audio_for_training.py")
        else:
            print("\n❌ No files were downloaded successfully.")
            print("   Check the log file for details.")

    except KeyboardInterrupt:
        print("\n\n⏸️  Scraping interrupted by user.")
        print("✅ Progress has been saved!")
        print(f"📊 Resume by running the script again.")
        print(f"   Already downloaded files will be skipped.\n")
        return 1


if __name__ == "__main__":
    exit(main())
