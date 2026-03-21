#!/usr/bin/env python3
"""
Merge partial conversation embedding files (a, b, c) into one
and trigger FAISS rebuild.

Run after all 3 embedding agents complete:
    python3 scripts/merge_conversation_embeddings.py
"""

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "embeddings_optimized"
FINAL_FILE = OUTPUT_DIR / "conversations_embeddings.json"
PART_FILES = [
    OUTPUT_DIR / "conversations_embeddings_a.json",
    OUTPUT_DIR / "conversations_embeddings_b.json",
    OUTPUT_DIR / "conversations_embeddings_c.json",
]


def main():
    print("🕉️  Merging conversation embeddings...\n")

    all_chunks = []
    for part in PART_FILES:
        if not part.exists():
            print(f"  ⚠️  Missing: {part.name} — skipping")
            continue
        with open(part) as f:
            data = json.load(f)
        chunks = data.get("chunks", [])
        complete = data.get("complete", False)
        print(f"  {'✅' if complete else '⚠️ INCOMPLETE'} {part.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("\n❌ No chunks to merge!")
        return

    # Re-index chunk IDs
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = i

    merged = {
        "scripture": "conversations",
        "model": "voyage-3-large",
        "total_chunks": len(all_chunks),
        "complete": True,
        "chunks": all_chunks
    }

    tmp = FINAL_FILE.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(merged, f)
    tmp.replace(FINAL_FILE)

    print(f"\n✅ Merged {len(all_chunks)} chunks → {FINAL_FILE.name}")
    print("\n🔨 Rebuilding FAISS index...")

    result = subprocess.run(
        ["python3", "scripts/build_faiss_index.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=False
    )

    if result.returncode == 0:
        print("\n✅ FAISS index rebuilt successfully!")
        print("🕉️  Conversations are now searchable in the RAG system.")
    else:
        print("\n❌ FAISS rebuild failed. Check output above.")

    # Clean up part files
    print("\n🧹 Cleaning up part files...")
    for part in PART_FILES:
        if part.exists():
            part.unlink()
            print(f"  Deleted {part.name}")
    for f in OUTPUT_DIR.glob("*.progress.json"):
        f.unlink()
        print(f"  Deleted {f.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
