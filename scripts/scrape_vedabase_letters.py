#!/usr/bin/env python3
"""
Vedabase Letters Scraper - Parallel download of all Prabhupada letters
Uses threading for faster downloads with controlled concurrency
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing dependencies. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', 'beautifulsoup4'])
    import requests
    from bs4 import BeautifulSoup


class VedabaseLettersScraper:
    def __init__(self, max_workers=5):
        self.base_url = "https://vedabase.io"
        self.letters_url = f"{self.base_url}/en/library/letters/"
        self.max_workers = max_workers
        self.delay_between_batches = 0.5

        # Output directory
        self.output_dir = Path.home() / "Downloads/vedabase book transcripts/letters"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Thread-safe locks
        self.progress_lock = Lock()
        self.sessions = {}

        # Progress tracking
        self.progress_file = Path.home() / "ai-prabhupada-rag/metadata/letters_progress.json"
        self.progress_file.parent.mkdir(exist_ok=True, parents=True)

        self.load_progress()

    def get_session(self):
        """Get or create session for current thread"""
        import threading
        thread_id = threading.get_ident()

        if thread_id not in self.sessions:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            self.sessions[thread_id] = session

        return self.sessions[thread_id]

    def load_progress(self):
        """Load scraping progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                'started': datetime.now().isoformat(),
                'total_discovered': 0,
                'total_fetched': 0,
                'fetched_urls': set(),
                'errors': [],
                'years_completed': []
            }

        # Convert fetched_urls to set if it's a list
        if isinstance(self.progress.get('fetched_urls'), list):
            self.progress['fetched_urls'] = set(self.progress['fetched_urls'])

    def save_progress(self):
        """Save current progress (thread-safe)"""
        with self.progress_lock:
            self.progress['last_updated'] = datetime.now().isoformat()
            # Convert set to list for JSON serialization
            progress_copy = self.progress.copy()
            progress_copy['fetched_urls'] = list(self.progress['fetched_urls'])

            with open(self.progress_file, 'w') as f:
                json.dump(progress_copy, f, indent=2)

    def log_error(self, message):
        """Log error message"""
        print(f"❌ {message}", flush=True)
        with self.progress_lock:
            self.progress['errors'].append({
                'time': datetime.now().isoformat(),
                'message': message
            })

    def fetch_url(self, url, timeout=20):
        """Fetch and parse a URL"""
        try:
            session = self.get_session()
            response = session.get(url, timeout=timeout)

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                self.log_error(f"HTTP {response.status_code} for {url}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            return soup

        except Exception as e:
            self.log_error(f"Error fetching {url}: {e}")
            return None

    def discover_all_letters(self):
        """Phase 1: Discover all letter URLs from pagination"""
        print("🔍 Phase 1: Discovering all letters...")
        print("━" * 70)

        all_letters = []
        page = 1

        while True:
            url = f"{self.letters_url}?page={page}"
            soup = self.fetch_url(url)

            if not soup:
                break

            # Find all letter links
            # Look for links that match the pattern /en/library/letters/letter-to-
            letter_links = soup.find_all('a', href=re.compile(r'/en/library/letters/letter-to-'))

            if not letter_links:
                print(f"   📄 Page {page}: No more letters found")
                break

            page_letters = []
            for link in letter_links:
                letter_url = link.get('href')
                if letter_url.startswith('/'):
                    letter_url = self.base_url + letter_url

                # Avoid duplicates
                if letter_url not in [l['url'] for l in all_letters]:
                    letter_title = link.get_text().strip()
                    page_letters.append({
                        'url': letter_url,
                        'title': letter_title,
                        'page': page
                    })

            all_letters.extend(page_letters)
            print(f"   📄 Page {page}: Found {len(page_letters)} letters (total: {len(all_letters)})", flush=True)

            page += 1
            time.sleep(self.delay_between_batches)  # Be polite

        self.progress['total_discovered'] = len(all_letters)
        self.save_progress()

        print("━" * 70)
        print(f"✅ Discovery complete: {len(all_letters)} letters found\n")

        return all_letters

    def extract_letter_metadata(self, soup, url):
        """Parse letter HTML to extract metadata and content"""
        try:
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text() if title_elem else "Unknown"

            # Extract recipient from URL
            recipient_match = re.search(r'/letter-to-([^/]+)/?$', url)
            recipient = recipient_match.group(1).replace('-', ' ').title() if recipient_match else "Unknown"

            # Extract date - look for patterns like "July 12th 1947" or "12 July 1947"
            text = soup.get_text()

            # Try multiple date patterns
            date_patterns = [
                r'(\w+ \d+(?:st|nd|rd|th)?,? \d{4})',  # July 12th, 1947
                r'(\d+ \w+ \d{4})',  # 12 July 1947
            ]

            date_str = None
            year = 'unknown'
            location = None

            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    date_str = date_match.group(1)
                    year_match = re.search(r'\d{4}', date_str)
                    if year_match:
                        year = year_match.group()
                    break

            # Try to extract location (often follows or precedes date)
            location_match = re.search(r'(?:Date|Location|Place):\s*([A-Z][a-zA-Z\s]+)', text)
            if location_match:
                location = location_match.group(1).strip()

            # Extract main content
            # Remove scripts, styles, nav, headers, footers
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Get text content
            content = soup.get_text(separator='\n', strip=True)

            return {
                'recipient': recipient,
                'date': date_str,
                'year': year,
                'location': location,
                'title': title,
                'content': content,
                'url': url
            }

        except Exception as e:
            self.log_error(f"Error extracting metadata from {url}: {e}")
            return None

    def fetch_letter(self, letter_info):
        """Fetch single letter content"""
        url = letter_info['url']

        # Check if already fetched
        if url in self.progress.get('fetched_urls', set()):
            return None

        soup = self.fetch_url(url)
        if not soup:
            return None

        metadata = self.extract_letter_metadata(soup, url)
        if not metadata:
            return None

        return metadata

    def save_letter(self, letter_data):
        """Save letter to appropriate year folder"""
        year = letter_data.get('year', 'unknown')
        year_dir = self.output_dir / year
        year_dir.mkdir(exist_ok=True, parents=True)

        # Generate filename from URL
        url_slug = letter_data['url'].split('/')[-2]
        filename = f"{url_slug}.txt"
        filepath = year_dir / filename

        # Write letter file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"LETTER TO: {letter_data['recipient']}\n")
            f.write(f"DATE: {letter_data.get('date', 'Unknown')}\n")
            f.write(f"LOCATION: {letter_data.get('location', 'Unknown')}\n")
            f.write(f"URL: {letter_data['url']}\n")
            f.write("=" * 70 + "\n\n")
            f.write(letter_data['content'])

        return filepath

    def download_letters_parallel(self, letters):
        """Phase 2: Download letters using ThreadPoolExecutor"""
        print(f"📥 Phase 2: Parallel download ({self.max_workers} workers)...")
        print("━" * 70)

        # Filter out already fetched
        letters_to_fetch = [
            l for l in letters
            if l['url'] not in self.progress.get('fetched_urls', set())
        ]

        if not letters_to_fetch:
            print("✅ All letters already downloaded!")
            return

        print(f"   Letters to download: {len(letters_to_fetch)}/{len(letters)}")
        print()

        downloaded = 0
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_letter = {
                executor.submit(self.fetch_letter, letter): letter
                for letter in letters_to_fetch
            }

            for future in as_completed(future_to_letter):
                letter_info = future_to_letter[future]

                try:
                    letter_data = future.result()

                    if letter_data:
                        filepath = self.save_letter(letter_data)

                        # Update progress
                        with self.progress_lock:
                            self.progress['fetched_urls'].add(letter_info['url'])
                            self.progress['total_fetched'] = len(self.progress['fetched_urls'])

                        downloaded += 1

                        # Progress indicator
                        if downloaded % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = downloaded / elapsed if elapsed > 0 else 0
                            remaining = len(letters_to_fetch) - downloaded
                            eta_seconds = remaining / rate if rate > 0 else 0
                            eta_mins = int(eta_seconds / 60)

                            percent = (downloaded / len(letters_to_fetch)) * 100
                            print(f"   📊 Progress: {downloaded}/{len(letters_to_fetch)} ({percent:.1f}%) | "
                                  f"Rate: {rate:.1f} letters/sec | ETA: {eta_mins}m", flush=True)

                        # Save progress checkpoint every 50 letters
                        if downloaded % 50 == 0:
                            self.save_progress()
                            print(f"   💾 Checkpoint saved ({downloaded} letters)", flush=True)

                except Exception as e:
                    self.log_error(f"Error processing {letter_info['url']}: {e}")

        # Final save
        self.save_progress()

        elapsed = time.time() - start_time
        print()
        print("━" * 70)
        print(f"✅ Download complete!")
        print(f"   Downloaded: {downloaded} new letters")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Average: {downloaded/elapsed:.2f} letters/sec")

    def create_combined_file(self):
        """Create combined letters.txt file for embedding"""
        print("\n📄 Creating combined letters.txt file...")

        combined_file = self.output_dir.parent / "letters.txt"

        all_letters = []
        for year_dir in sorted(self.output_dir.iterdir()):
            if year_dir.is_dir():
                for letter_file in sorted(year_dir.glob("*.txt")):
                    with open(letter_file, 'r', encoding='utf-8') as f:
                        all_letters.append(f.read())

        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write('\n\n' + '='*70 + '\n\n'.join(all_letters))

        size_mb = combined_file.stat().st_size / (1024 * 1024)
        print(f"✅ Combined file created: {combined_file}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Letters: {len(all_letters)}")

        return combined_file

    def generate_statistics(self):
        """Generate final statistics"""
        print("\n📊 FINAL STATISTICS")
        print("━" * 70)

        year_counts = {}
        total_size = 0

        for year_dir in sorted(self.output_dir.iterdir()):
            if year_dir.is_dir() and year_dir.name.replace('_', '').isdigit():
                letter_files = list(year_dir.glob("*.txt"))
                count = len(letter_files)
                year_counts[year_dir.name] = count

                for f in letter_files:
                    total_size += f.stat().st_size

        print(f"Total letters: {sum(year_counts.values()):,}")
        print(f"Total size: {total_size / (1024*1024):.2f} MB")
        print(f"Year range: {min(year_counts.keys())} - {max(year_counts.keys())}")
        print()
        print("Top 5 years by letter count:")
        for year, count in sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {year}: {count:,} letters")

        print("━" * 70)

        # Estimate embedding cost
        tokens_estimate = (total_size * 0.25)  # 1 byte ≈ 0.25 tokens
        cost_estimate = (tokens_estimate / 1_000_000) * 0.18

        print(f"\n💰 Embedding Cost Estimate:")
        print(f"   Estimated tokens: {int(tokens_estimate):,}")
        print(f"   Estimated cost: ${cost_estimate:.4f}")

    def run(self):
        """Main execution: discover + download in parallel"""
        print("━" * 70)
        print("📧 VEDABASE LETTERS SCRAPER - Parallel Download")
        print("━" * 70)
        print()

        # Phase 1: Discover
        letters = self.discover_all_letters()

        if not letters:
            print("❌ No letters discovered!")
            return

        # Phase 2: Download
        self.download_letters_parallel(letters)

        # Phase 3: Post-processing
        self.create_combined_file()
        self.generate_statistics()

        print()
        print("━" * 70)
        print("✅ ALL DONE!")
        print("━" * 70)
        print(f"\nLetters saved to: {self.output_dir}")
        print(f"Combined file: {self.output_dir.parent / 'letters.txt'}")
        print(f"Progress file: {self.progress_file}")
        print()
        print("Ready for embedding tomorrow! 🚀")


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Interrupted by user. Progress has been saved.")
    print("Run the script again to resume from checkpoint.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    scraper = VedabaseLettersScraper(max_workers=5)
    scraper.run()
