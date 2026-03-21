#!/usr/bin/env python3
"""
Process ENTIRE Vedabase - All books
Systematic, cost-tracked processing
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime

# Paths
VEDABASE_DIR = Path.home() / "Downloads" / "vedabase book transcripts"
OUTPUT_DIR = Path.home() / "ai-prabhupada-rag" / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Progress tracking
PROGRESS_FILE = OUTPUT_DIR.parent / "processing_progress.json"


def clean_text(text: str) -> str:
    """Remove duplicate sections and footer text"""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip donation footer
        if any(skip in line for skip in ['Donate', 'Thanks to', 'supporting this site', 
                                          'Privacy policy', 'Default View', 'Advanced View',
                                          'Dual Language']):
            continue
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    text = re.sub(r'\n\n\n+', '\n\n', text)
    return text.strip()


def process_book_folder(folder_path: Path, book_name: str):
    """Process a single book folder"""
    all_text = []
    file_count = 0
    
    # Recursively find all .txt files
    txt_files = sorted(folder_path.rglob("*.txt"))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = clean_text(content)
            if content:  # Only add non-empty content
                all_text.append(content)
                file_count += 1
        except Exception as e:
            print(f"    ⚠️  Error reading {txt_file.name}: {e}")
    
    return "\n\n".join(all_text), file_count


def estimate_tokens_and_cost(text: str):
    """Estimate tokens and Voyage AI cost"""
    tokens = len(text) // 4  # Rough estimate
    cost = (tokens / 1_000_000) * 0.12  # Voyage-3-large pricing
    return tokens, cost


def process_all_books():
    """Process all books in Vedabase"""
    
    if not VEDABASE_DIR.exists():
        print(f"❌ Vedabase folder not found: {VEDABASE_DIR}")
        return
    
    print("="*70)
    print("COMPLETE VEDABASE PROCESSING")
    print("="*70)
    print(f"Source: {VEDABASE_DIR}")
    print(f"Output: {OUTPUT_DIR}\n")
    
    # Discover all book folders
    book_folders = [d for d in VEDABASE_DIR.iterdir() 
                   if d.is_dir() and not d.name.startswith('.')]
    
    print(f"Found {len(book_folders)} books to process:\n")
    
    total_tokens = 0
    total_cost = 0
    processed_books = []
    
    for i, book_folder in enumerate(sorted(book_folders), 1):
        book_code = book_folder.name
        print(f"\n[{i}/{len(book_folders)}] Processing: {book_code}")
        print("-" * 50)
        
        # Process the book
        book_text, file_count = process_book_folder(book_folder, book_code)
        
        if not book_text:
            print(f"  ⚠️  No text found, skipping")
            continue
        
        # Calculate stats
        tokens, cost = estimate_tokens_and_cost(book_text)
        total_tokens += tokens
        total_cost += cost
        
        # Save to file
        output_file = OUTPUT_DIR / f"{book_code}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(book_text)
        
        print(f"  ✓ Files processed: {file_count}")
        print(f"  ✓ Characters: {len(book_text):,}")
        print(f"  ✓ Est. tokens: {tokens:,}")
        print(f"  ✓ Est. cost: ${cost:.4f}")
        print(f"  ✓ Saved to: {output_file.name}")
        
        processed_books.append({
            "code": book_code,
            "files": file_count,
            "chars": len(book_text),
            "tokens": tokens,
            "cost": cost,
            "output_file": str(output_file)
        })
        
        # Save progress
        progress = {
            "timestamp": datetime.now().isoformat(),
            "total_books": len(book_folders),
            "processed": i,
            "books": processed_books,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        }
        
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    
    # Final summary
    print("\n" + "="*70)
    print("✅ PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nBooks processed: {len(processed_books)}")
    print(f"Total files: {sum(b['files'] for b in processed_books):,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total cost estimate: ${total_cost:.4f}")
    print(f"\nOutput folder: {OUTPUT_DIR}")
    
    return processed_books, total_tokens, total_cost


if __name__ == "__main__":
    process_all_books()
