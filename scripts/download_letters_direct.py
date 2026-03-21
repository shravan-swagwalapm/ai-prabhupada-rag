#!/usr/bin/env python3
"""
Direct Letters Downloader - Downloads letters by discovering from first 330 pages
Skips the lengthy pagination check, goes straight to downloading
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', 'beautifulsoup4'])
    import requests
    from bs4 import BeautifulSoup


class DirectLettersDownloader:
    def __init__(self, max_workers=5):
        self.base_url = "https://vedabase.io"
        self.letters_url = f"{self.base_url}/en/library/letters/"
        self.max_workers = max_workers
        self.delay_between_batches = 0.5

        self.output_dir = Path.home() / "Downloads/vedabase book transcripts/letters"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.progress_lock = Lock()
        self.sessions = {}

        self.progress_file = Path.home() / "ai-prabhupada-rag/metadata/letters_progress.json"
        self.progress_file.parent.mkdir(exist_ok=True, parents=True)

        self.load_progress()

    def get_session(self):
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
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
                if isinstance(self.progress.get('fetched_urls'), list):
                    self.progress['fetched_urls'] = set(self.progress['fetched_urls'])
        else:
            self.progress = {
                'started': datetime.now().isoformat(),
                'total_discovered': 0,
                'total_fetched': 0,
                'fetched_urls': set(),
                'errors': []
            }

    def save_progress(self):
        with self.progress_lock:
            self.progress['last_updated'] = datetime.now().isoformat()
            progress_copy = self.progress.copy()
            progress_copy['fetched_urls'] = list(self.progress['fetched_urls'])

            with open(self.progress_file, 'w') as f:
                json.dump(progress_copy, f, indent=2)

    def fetch_url(self, url, timeout=20):
        try:
            session = self.get_session()
            response = session.get(url, timeout=timeout)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except Exception:
            return None

    def quick_discover(self, max_pages=330):
        """Quick discovery of first 330 pages (where all letters are)"""
        print("🔍 Quick Discovery (pages 1-330)...")
        print("━" * 70)

        all_letters = []

        for page in range(1, max_pages + 1):
            url = f"{self.letters_url}?page={page}"
            soup = self.fetch_url(url)

            if not soup:
                continue

            letter_links = soup.find_all('a', href=re.compile(r'/en/library/letters/letter-to-'))

            page_letters = []
            for link in letter_links:
                letter_url = link.get('href')
                if letter_url.startswith('/'):
                    letter_url = self.base_url + letter_url

                if letter_url not in [l['url'] for l in all_letters]:
                    letter_title = link.get_text().strip()
                    page_letters.append({
                        'url': letter_url,
                        'title': letter_title
                    })

            all_letters.extend(page_letters)

            if page % 50 == 0:
                print(f"   Page {page}: {len(all_letters):,} letters discovered")

            time.sleep(0.3)

        print("━" * 70)
        print(f"✅ Discovery complete: {len(all_letters):,} letters\n")

        return all_letters

    def extract_letter_data(self, soup, url):
        try:
            title_elem = soup.find('title')
            title = title_elem.get_text() if title_elem else "Unknown"

            recipient_match = re.search(r'/letter-to-([^/]+)/?$', url)
            recipient = recipient_match.group(1).replace('-', ' ').title() if recipient_match else "Unknown"

            text = soup.get_text()

            date_patterns = [
                r'(\w+ \d+(?:st|nd|rd|th)?,? \d{4})',
                r'(\d+ \w+ \d{4})',
            ]

            date_str = None
            year = 'unknown'

            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    date_str = date_match.group(1)
                    year_match = re.search(r'\d{4}', date_str)
                    if year_match:
                        year = year_match.group()
                    break

            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {
                'recipient': recipient,
                'date': date_str,
                'year': year,
                'title': title,
                'content': content,
                'url': url
            }
        except Exception:
            return None

    def fetch_letter(self, letter_info):
        url = letter_info['url']

        if url in self.progress.get('fetched_urls', set()):
            return None

        soup = self.fetch_url(url)
        if not soup:
            return None

        metadata = self.extract_letter_data(soup, url)
        return metadata

    def save_letter(self, letter_data):
        year = letter_data.get('year', 'unknown')
        year_dir = self.output_dir / year
        year_dir.mkdir(exist_ok=True, parents=True)

        url_slug = letter_data['url'].split('/')[-2]
        filename = f"{url_slug}.txt"
        filepath = year_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"LETTER TO: {letter_data['recipient']}\n")
            f.write(f"DATE: {letter_data.get('date', 'Unknown')}\n")
            f.write(f"URL: {letter_data['url']}\n")
            f.write("=" * 70 + "\n\n")
            f.write(letter_data['content'])

        return filepath

    def download_parallel(self, letters):
        print(f"📥 Downloading {len(letters):,} letters ({self.max_workers} workers)...")
        print("━" * 70)

        letters_to_fetch = [
            l for l in letters
            if l['url'] not in self.progress.get('fetched_urls', set())
        ]

        if not letters_to_fetch:
            print("✅ All letters already downloaded!")
            return

        print(f"   Remaining: {len(letters_to_fetch):,}/{len(letters):,}")
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
                        self.save_letter(letter_data)

                        with self.progress_lock:
                            self.progress['fetched_urls'].add(letter_info['url'])
                            self.progress['total_fetched'] = len(self.progress['fetched_urls'])

                        downloaded += 1

                        if downloaded % 50 == 0:
                            elapsed = time.time() - start_time
                            rate = downloaded / elapsed if elapsed > 0 else 0
                            remaining = len(letters_to_fetch) - downloaded
                            eta_seconds = remaining / rate if rate > 0 else 0
                            eta_mins = int(eta_seconds / 60)

                            percent = (downloaded / len(letters_to_fetch)) * 100
                            print(f"   📊 {downloaded:,}/{len(letters_to_fetch):,} ({percent:.1f}%) | "
                                  f"{rate:.1f}/sec | ETA: {eta_mins}m", flush=True)

                            self.save_progress()
                            print(f"   💾 Checkpoint saved", flush=True)

                except Exception as e:
                    print(f"   ❌ Error: {letter_info['url'][:50]}...", flush=True)

        self.save_progress()

        elapsed = time.time() - start_time
        print()
        print("━" * 70)
        print(f"✅ Downloaded {downloaded:,} letters in {elapsed/60:.1f} minutes")
        print(f"   Rate: {downloaded/elapsed:.2f} letters/sec")

    def create_combined_file(self):
        print("\n📄 Creating combined file...")

        combined_file = self.output_dir.parent / "letters.txt"

        all_letters = []
        for year_dir in sorted(self.output_dir.iterdir()):
            if year_dir.is_dir():
                for letter_file in sorted(year_dir.glob("*.txt")):
                    with open(letter_file, 'r', encoding='utf-8') as f:
                        all_letters.append(f.read())

        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write('\n\n' + ('='*70 + '\n\n').join(all_letters))

        size_mb = combined_file.stat().st_size / (1024 * 1024)
        print(f"✅ Combined: {combined_file}")
        print(f"   Size: {size_mb:.2f} MB | Letters: {len(all_letters):,}")

    def run(self):
        print("━" * 70)
        print("📧 DIRECT LETTERS DOWNLOADER")
        print("━" * 70)
        print()

        # Quick discovery (330 pages)
        letters = self.quick_discover(max_pages=330)

        # Download
        self.download_parallel(letters)

        # Create combined file
        self.create_combined_file()

        print()
        print("━" * 70)
        print("✅ COMPLETE!")
        print("━" * 70)
        print(f"\nLetters: {self.output_dir}")
        print(f"Combined: {self.output_dir.parent / 'letters.txt'}")


if __name__ == "__main__":
    downloader = DirectLettersDownloader(max_workers=5)
    downloader.run()
