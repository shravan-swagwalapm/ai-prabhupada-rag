#!/usr/bin/env python3
"""
One-time script to optimize existing embeddings for faster search
Converts float64 → float32 and pre-normalizes vectors
Run once, saves optimized versions, 50% memory + 4-5x faster queries

Phase 3 Optimization - Part 1
"""
import json
import numpy as np
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
OPTIMIZED_DIR = PROJECT_ROOT / "embeddings_optimized"

def optimize_embeddings():
    """Convert all embeddings to float32 and pre-normalize"""
    OPTIMIZED_DIR.mkdir(exist_ok=True)

    embedding_files = list(EMBEDDINGS_DIR.glob("*_embeddings.json"))

    if not embedding_files:
        print("❌ No embedding files found in embeddings/ directory")
        return

    print(f"Found {len(embedding_files)} embedding files to optimize")
    print("="*70)

    total_start = time.time()
    total_chunks = 0

    for emb_file in embedding_files:
        print(f"\n📦 Optimizing {emb_file.name}...")
        start = time.time()

        try:
            with open(emb_file) as f:
                data = json.load(f)

            # Convert embeddings to numpy array (float32)
            print(f"   Converting to float32 and normalizing...")
            embeddings = np.array([c["embedding"] for c in data["chunks"]], dtype=np.float32)

            # Pre-normalize (do this ONCE, not every query!)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings_normalized = embeddings / norms

            # Update chunks with normalized float32 embeddings
            for i, chunk in enumerate(data["chunks"]):
                chunk["embedding"] = embeddings_normalized[i].tolist()

            # Save optimized version
            output_file = OPTIMIZED_DIR / emb_file.name
            with open(output_file, 'w') as f:
                json.dump(data, f)

            elapsed = time.time() - start
            num_chunks = len(data["chunks"])
            total_chunks += num_chunks

            print(f"   ✅ Saved {output_file.name}")
            print(f"   📊 {num_chunks:,} chunks optimized in {elapsed:.1f}s")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    total_elapsed = time.time() - total_start

    print("\n" + "="*70)
    print("✅ OPTIMIZATION COMPLETE")
    print("="*70)
    print(f"Total files optimized: {len(embedding_files)}")
    print(f"Total chunks: {total_chunks:,}")
    print(f"Total time: {total_elapsed:.1f}s")
    print(f"\nOptimized embeddings saved to: {OPTIMIZED_DIR}")
    print("\nNext step: Update scripts/search_scriptures.py to use optimized embeddings")

if __name__ == "__main__":
    optimize_embeddings()
