#!/usr/bin/env python3
"""
Process Vedabase book transcripts into clean text files for embedding
"""
import os
import re
from pathlib import Path

# Paths
VEDABASE_DIR = Path.home() / "Downloads" / "vedabase book transcripts"
OUTPUT_DIR = Path.home() / "ai-prabhupada-rag" / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Books to process (Phase 1: Bhagavad Gita only)
BOOKS = {
    "bg": {
        "name": "Bhagavad Gita As It Is",
        "folder": "bg",
        "chapters": 18,
        "priority": 1
    },
    "sb": {
        "name": "Srimad Bhagavatam",
        "folder": "sb",
        "cantos": [1, 2, 10],  # Start with these
        "priority": 2
    },
    "iso": {
        "name": "Sri Isopanisad",
        "folder": "iso",
        "priority": 3
    },
    "noi": {
        "name": "Nectar of Instruction",
        "folder": "noi",
        "priority": 3
    }
}


def clean_text(text: str) -> str:
    """Remove duplicate sections and footer text"""
    # Split by the header
    lines = text.split('\n')
    
    # Find the translation section (appears once)
    cleaned_lines = []
    seen_sections = set()
    current_section = None
    
    for line in lines:
        # Skip donation footer
        if 'Donate' in line or 'Thanks to' in line or 'supporting this site' in line:
            continue
        
        # Skip duplicate headers
        if 'Default View' in line or 'Advanced View' in line or 'Dual Language' in line:
            continue
        
        # Skip repeated devanagari
        if line.startswith('कर्मण्य') or line.startswith('मा '):
            if 'devanagari' in seen_sections:
                continue
            seen_sections.add('devanagari')
        
        cleaned_lines.append(line)
    
    # Join and remove excessive whitespace
    text = '\n'.join(cleaned_lines)
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()


def process_bhagavad_gita(include_purports=True):
    """Process all Bhagavad Gita chapters"""
    bg_dir = VEDABASE_DIR / "bg"
    
    if not bg_dir.exists():
        print(f"❌ Bhagavad Gita folder not found: {bg_dir}")
        return None
    
    print("Processing Bhagavad Gita...")
    all_text = []
    total_verses = 0
    
    for chapter_num in range(1, 19):  # 18 chapters
        chapter_dir = bg_dir / f"chapter_{chapter_num:02d}"
        
        if not chapter_dir.exists():
            print(f"  ⚠️  Chapter {chapter_num} not found")
            continue
        
        chapter_verses = []
        verse_files = sorted(chapter_dir.glob("v*.txt"))
        
        for verse_file in verse_files:
            with open(verse_file, 'r', encoding='utf-8') as f:
                verse_text = f.read()
            
            # Clean the text
            verse_text = clean_text(verse_text)
            
            # Extract just verse text and translation (optionally purport)
            if not include_purports:
                # Find translation section
                if 'Translation' in verse_text:
                    start = verse_text.find('Translation')
                    end = verse_text.find('Purport') if 'Purport' in verse_text else len(verse_text)
                    verse_text = verse_text[start:end]
            
            chapter_verses.append(verse_text)
            total_verses += 1
        
        if chapter_verses:
            chapter_text = f"\n\n{'='*60}\nCHAPTER {chapter_num}\n{'='*60}\n\n"
            chapter_text += "\n\n".join(chapter_verses)
            all_text.append(chapter_text)
            print(f"  ✓ Chapter {chapter_num}: {len(verse_files)} verses")
    
    # Combine all chapters
    full_text = "\n\n".join(all_text)
    
    # Estimate tokens and cost
    tokens = len(full_text) // 4  # Rough estimate
    cost = (tokens / 1_000_000) * 0.12
    
    print(f"\n📊 Bhagavad Gita Stats:")
    print(f"   Total verses: {total_verses}")
    print(f"   Total characters: {len(full_text):,}")
    print(f"   Estimated tokens: {tokens:,}")
    print(f"   Estimated cost: ${cost:.4f}")
    
    # Save to file
    output_file = OUTPUT_DIR / ("bhagavad_gita_complete.txt" if include_purports else "bhagavad_gita_verses_only.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print(f"   ✓ Saved to: {output_file}")
    
    return output_file, tokens, cost


def main():
    """Main processing pipeline"""
    print("="*70)
    print("VEDABASE TRANSCRIPT PROCESSOR")
    print("="*70)
    print(f"\nSource: {VEDABASE_DIR}")
    print(f"Output: {OUTPUT_DIR}\n")
    
    # Check if vedabase folder exists
    if not VEDABASE_DIR.exists():
        print(f"❌ Vedabase folder not found!")
        print(f"   Expected: {VEDABASE_DIR}")
        return
    
    print("Available books:")
    for code, info in BOOKS.items():
        folder = VEDABASE_DIR / info["folder"]
        status = "✓" if folder.exists() else "✗"
        print(f"  {status} {code}: {info['name']}")
    
    print("\n" + "="*70)
    print("PHASE 1: Bhagavad Gita")
    print("="*70)
    
    # Ask user what to include
    print("\nProcessing options:")
    print("  1. Verses + Translations only (~50K tokens, ~$0.01)")
    print("  2. Verses + Translations + Purports (~400K tokens, ~$0.05)")
    print()
    
    choice = input("Choose option (1 or 2, or ENTER for option 1): ").strip()
    include_purports = (choice == "2")
    
    # Process Bhagavad Gita
    result = process_bhagavad_gita(include_purports=include_purports)
    
    if result:
        output_file, tokens, cost = result
        print(f"\n{'='*70}")
        print("✅ COMPLETE!")
        print("="*70)
        print(f"\nNext steps:")
        print(f"  1. Review the file: {output_file}")
        print(f"  2. Run embedding: python3 scripts/embed_scriptures.py")
        print(f"  3. Estimated cost: ${cost:.4f}")
    else:
        print("\n❌ Processing failed")


if __name__ == "__main__":
    main()
