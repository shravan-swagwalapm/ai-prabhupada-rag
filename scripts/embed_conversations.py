#!/usr/bin/env python3
"""
Embed Prabhupada Conversations — Resume-safe, parallel-friendly

Usage:
    python3 scripts/embed_conversations.py --years 1967 1971 --output conversations_embeddings_a.json
    python3 scripts/embed_conversations.py --years 1972 1974 --output conversations_embeddings_b.json
    python3 scripts/embed_conversations.py --years 1975 1977 --output conversations_embeddings_c.json

Output goes to: embeddings_optimized/{output}
Progress saved to: embeddings_optimized/{output}.progress.json
"""

import os
import re
import json
import time
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY not found in .env")

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
EMBEDDING_MODEL = "voyage-3-large"
BATCH_SIZE = 50          # chunks per API call
CHECKPOINT_EVERY = 5     # save progress every N months
MAX_WORDS_PER_CHUNK = 400
OVERLAP_SENTENCES = 2

PROJECT_ROOT = Path(__file__).parent.parent
CONVERSATIONS_DIR = Path("/Users/shravantickoo/Downloads/vedabase book transcripts/conversations")
OUTPUT_DIR = PROJECT_ROOT / "embeddings_optimized"
OUTPUT_DIR.mkdir(exist_ok=True)

MONTHS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]


# ─── Text processing ────────────────────────────────────────────────

def parse_conversations_from_file(txt_path: Path, year: int, month: str) -> list:
    """
    Parse a month .txt file into individual conversation blocks.
    Each conversation starts with a 6-digit ID like 750401mw.may
    """
    text = txt_path.read_text(encoding="utf-8")
    
    # Pattern: 6-digit date code + 2-letter type + .location (e.g. 750401mw.may)
    conv_id_pattern = re.compile(r'^[0-9]{6}[A-Z]{2,4}\.[A-Z]{2,4}$', re.MULTILINE | re.IGNORECASE)
    
    lines = text.split("\n")
    conversations = []
    current_id = f"{year}_{month}_main"
    current_title = ""
    current_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect conversation ID line
        if re.match(r'^[0-9]{6}[A-Za-z]{2,4}\.[A-Za-z]{2,4}$', line):
            # Save previous conversation
            if current_lines:
                text_block = "\n".join(current_lines).strip()
                if len(text_block) > 100:
                    conversations.append({
                        "conv_id": current_id,
                        "title": current_title,
                        "year": year,
                        "month": month,
                        "text": text_block
                    })
            current_id = line
            current_title = ""
            current_lines = []
            # Next few lines often have the title/date/location
            for j in range(i+1, min(i+5, len(lines))):
                t = lines[j].strip()
                if t and t not in ["—", "–", "-"]:
                    current_title += t + " "
        else:
            # Skip header boilerplate at top of file
            if line.startswith("=== Prabhupada") or line.startswith("Source:") or line.startswith("Scraped:"):
                i += 1
                continue
            if line:
                current_lines.append(line)
        i += 1
    
    # Save last conversation
    if current_lines:
        text_block = "\n".join(current_lines).strip()
        if len(text_block) > 100:
            conversations.append({
                "conv_id": current_id,
                "title": current_title.strip(),
                "year": year,
                "month": month,
                "text": text_block
            })
    
    return conversations


def chunk_conversation(conv: dict) -> list:
    """Split a conversation into overlapping word chunks with metadata prefix."""
    text = conv["text"]
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    chunks = []
    current = []
    current_words = 0
    
    for sent in sentences:
        words = len(sent.split())
        if current_words + words > MAX_WORDS_PER_CHUNK and current:
            chunk_text = " ".join(current)
            # Prepend metadata context
            meta = f"[Conversations, {conv['year']} {conv['month'].upper()}, {conv['conv_id']}] "
            chunks.append({
                "conv_id": conv["conv_id"],
                "year": conv["year"],
                "month": conv["month"],
                "text": meta + chunk_text
            })
            # Overlap: keep last N sentences
            current = current[-OVERLAP_SENTENCES:] if len(current) > OVERLAP_SENTENCES else current
            current_words = sum(len(s.split()) for s in current)
        
        current.append(sent)
        current_words += words
    
    if current:
        chunk_text = " ".join(current)
        meta = f"[Conversations, {conv['year']} {conv['month'].upper()}, {conv['conv_id']}] "
        chunks.append({
            "conv_id": conv["conv_id"],
            "year": conv["year"],
            "month": conv["month"],
            "text": meta + chunk_text
        })
    
    return chunks


# ─── Voyage AI ──────────────────────────────────────────────────────

def embed_batch(texts: list, retries: int = 3) -> list:
    headers = {
        "Authorization": f"Bearer {VOYAGE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": [t[:6000] for t in texts],  # safety truncation
        "model": EMBEDDING_MODEL
    }
    for attempt in range(retries):
        try:
            resp = requests.post(VOYAGE_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            return [item["embedding"] for item in resp.json()["data"]]
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    ⚠️  API error (attempt {attempt+1}): {e} — retrying in {wait}s")
                time.sleep(wait)
            else:
                raise


# ─── Progress tracking ──────────────────────────────────────────────

def load_progress(progress_file: Path) -> dict:
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    return {"completed_months": [], "total_chunks": 0}


def save_progress(progress_file: Path, progress: dict):
    tmp = progress_file.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(progress, f, indent=2)
    tmp.replace(progress_file)


def save_embeddings(output_file: Path, all_chunks: list, complete: bool = False):
    """Atomic save — write to .tmp then rename."""
    data = {
        "scripture": "conversations",
        "model": EMBEDDING_MODEL,
        "total_chunks": len(all_chunks),
        "complete": complete,
        "chunks": all_chunks
    }
    tmp = output_file.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f)
    tmp.replace(output_file)


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs=2, type=int, required=True, metavar=("START", "END"))
    parser.add_argument("--output", type=str, required=True, help="Output filename (e.g. conversations_embeddings_a.json)")
    args = parser.parse_args()

    year_start, year_end = args.years
    output_file = OUTPUT_DIR / args.output
    progress_file = OUTPUT_DIR / (args.output + ".progress.json")

    print(f"🕉️  Conversations Embedding Pipeline")
    print(f"📅 Years: {year_start}–{year_end}")
    print(f"📁 Output: {output_file}")
    print(f"🔑 Model: {EMBEDDING_MODEL}\n")

    # Load progress + existing chunks
    progress = load_progress(progress_file)
    completed_months = set(progress["completed_months"])

    all_chunks = []
    if output_file.exists():
        try:
            with open(output_file) as f:
                existing = json.load(f)
            all_chunks = existing.get("chunks", [])
            print(f"  🔄 Resuming: {len(all_chunks)} chunks already embedded\n")
        except Exception:
            all_chunks = []

    months_done = 0

    for year in range(year_start, year_end + 1):
        for month in MONTHS:
            key = f"{year}/{month}"
            txt_path = CONVERSATIONS_DIR / str(year) / f"conversations_{year}_{month}.txt"

            if not txt_path.exists():
                continue

            if key in completed_months:
                print(f"  ✅ {key} — already embedded, skipping")
                continue

            print(f"  📖 {key} ({txt_path.stat().st_size // 1024}KB)...", flush=True)

            # Parse into conversations
            conversations = parse_conversations_from_file(txt_path, year, month)
            if not conversations:
                print(f"    ⚠️  No conversations parsed")
                completed_months.add(key)
                continue

            # Chunk all conversations in this month
            month_chunks = []
            for conv in conversations:
                month_chunks.extend(chunk_conversation(conv))

            print(f"    → {len(conversations)} conversations, {len(month_chunks)} chunks", flush=True)

            # Embed in batches
            month_embedded = []
            for i in range(0, len(month_chunks), BATCH_SIZE):
                batch = month_chunks[i:i + BATCH_SIZE]
                texts = [c["text"] for c in batch]

                embeddings = embed_batch(texts)

                for j, (chunk, emb) in enumerate(zip(batch, embeddings)):
                    month_embedded.append({
                        "chunk_id": f"{chunk['conv_id']}_{i+j}",
                        "year": chunk["year"],
                        "month": chunk["month"],
                        "conv_id": chunk["conv_id"],
                        "text": chunk["text"],
                        "embedding": emb
                    })

                time.sleep(0.3)  # gentle rate limiting

            all_chunks.extend(month_embedded)
            completed_months.add(key)
            months_done += 1

            print(f"    ✅ {len(month_embedded)} chunks embedded (total: {len(all_chunks)})")

            # Checkpoint every N months
            if months_done % CHECKPOINT_EVERY == 0:
                save_embeddings(output_file, all_chunks, complete=False)
                progress["completed_months"] = list(completed_months)
                progress["total_chunks"] = len(all_chunks)
                save_progress(progress_file, progress)
                print(f"  💾 Checkpoint saved")

    # Final save
    save_embeddings(output_file, all_chunks, complete=True)
    progress["completed_months"] = list(completed_months)
    progress["total_chunks"] = len(all_chunks)
    save_progress(progress_file, progress)

    print(f"\n🎉 Done — {len(all_chunks)} total chunks → {output_file.name}")


if __name__ == "__main__":
    main()
