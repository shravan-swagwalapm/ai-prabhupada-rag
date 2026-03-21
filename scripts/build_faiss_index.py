#!/usr/bin/env python3
"""
Build FAISS IVF index from optimized embeddings
Phase 3 Part 2: 50-100x speedup with approximate nearest neighbor search
"""
import json
import numpy as np
import faiss
import time
from pathlib import Path
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings_optimized"
INDEX_DIR = PROJECT_ROOT / "faiss_indexes"

def build_faiss_index(nlist=100):
    """
    Build FAISS IVF100 index for fast approximate search

    Args:
        nlist: Number of clusters (100 = good balance of speed/accuracy)

    Returns:
        tuple: (index, metadata)
    """
    INDEX_DIR.mkdir(exist_ok=True)

    print("📦 Loading embeddings...")
    print("=" * 70)

    all_embeddings = []
    metadata = []
    total_files = 0

    embedding_files = list(EMBEDDINGS_DIR.glob("*_embeddings.json"))

    if not embedding_files:
        print("❌ No optimized embeddings found!")
        print(f"   Run: python3 scripts/optimize_embeddings.py")
        return None, None

    for emb_file in embedding_files:
        print(f"   Loading {emb_file.name}...")
        total_files += 1

        with open(emb_file) as f:
            data = json.load(f)

        scripture_name = data.get("scripture", emb_file.stem.replace("_embeddings", ""))

        for chunk in data["chunks"]:
            all_embeddings.append(chunk["embedding"])
            metadata.append({
                "scripture": scripture_name,
                "chunk_id": chunk.get("chunk_id", ""),
                "text": chunk["text"]
            })

    # Convert to numpy (already float32 and normalized)
    embeddings_matrix = np.array(all_embeddings, dtype=np.float32)
    dimension = embeddings_matrix.shape[1]

    print(f"\n✅ Loaded {len(all_embeddings):,} embeddings from {total_files} files")
    print(f"   Dimensions: {dimension}D")
    print(f"   Memory: {embeddings_matrix.nbytes / 1024 / 1024:.1f} MB")

    # Build FAISS IVF index
    print(f"\n{'='*70}")
    print(f"🏗️  Building FAISS IVF{nlist} index...")
    print(f"{'='*70}")
    start = time.time()

    # Create quantizer (for coarse search)
    quantizer = faiss.IndexFlatIP(dimension)  # Inner product (for normalized vectors)

    # Create IVF index (inverted file index)
    index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)

    print(f"   Training on {len(all_embeddings):,} vectors...")

    # Train the index (learns cluster centroids)
    index.train(embeddings_matrix)

    print(f"   ✅ Training complete")
    print(f"   Adding vectors to index...")

    # Add all vectors to the index
    index.add(embeddings_matrix)

    elapsed = time.time() - start
    print(f"   ✅ Index built in {elapsed:.1f}s")

    # Save index and metadata
    index_file = INDEX_DIR / "scripture_ivf100.index"
    metadata_file = INDEX_DIR / "metadata.json"

    print(f"\n💾 Saving index and metadata...")
    faiss.write_index(index, str(index_file))

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f)

    # Report sizes
    index_size = index_file.stat().st_size / 1024 / 1024
    metadata_size = metadata_file.stat().st_size / 1024 / 1024

    print(f"\n{'='*70}")
    print(f"✅ FAISS INDEX BUILD COMPLETE")
    print(f"{'='*70}")
    print(f"Index file:     {index_file}")
    print(f"Index size:     {index_size:.1f} MB")
    print(f"Metadata file:  {metadata_file}")
    print(f"Metadata size:  {metadata_size:.1f} MB")
    print(f"Total vectors:  {len(all_embeddings):,}")
    print(f"Clusters:       {nlist}")
    print(f"Build time:     {elapsed:.1f}s")
    print(f"{'='*70}")
    print(f"\n✅ Ready for fast search! Expected: 50-100x faster than brute-force")

    return index, metadata

if __name__ == "__main__":
    build_faiss_index(nlist=100)
