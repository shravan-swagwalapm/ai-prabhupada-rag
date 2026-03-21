#!/usr/bin/env python3
"""
Verify FAISS quality vs brute-force
Expected: 95-99% overlap in top-5 results
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from search_scriptures import search_scriptures
from search_scriptures_faiss import search_scriptures_faiss

TEST_QUERIES = [
    "what does krsna say about the nature of the soul?",
    "how to practice karma yoga?",
    "what is bhakti yoga?",
    "what is dharma?",
    "how to control the mind?"
]

def compare_results(query: str):
    """Compare FAISS vs brute-force top-5 results"""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    # Run both searches
    brute_results = search_scriptures(query, top_k=5)
    faiss_results = search_scriptures_faiss(query, top_k=5)

    # Extract chunk IDs
    brute_ids = set(r['chunk_id'] for r in brute_results)
    faiss_ids = set(r['chunk_id'] for r in faiss_results)

    # Calculate overlap
    overlap = len(brute_ids & faiss_ids)
    overlap_pct = (overlap / 5) * 100

    print(f"\nBrute-force top-5:")
    for i, r in enumerate(brute_results[:3], 1):
        print(f"  {i}. [{r['scripture']}] {r['similarity']:.3f} - {r['text'][:60]}...")

    print(f"\nFAISS top-5:")
    for i, r in enumerate(faiss_results[:3], 1):
        print(f"  {i}. [{r['scripture']}] {r['similarity']:.3f} - {r['text'][:60]}...")

    print(f"\n📊 Overlap: {overlap}/5 ({overlap_pct:.0f}%)")

    return overlap_pct


def main():
    """Run quality verification"""
    print("🧪 FAISS Quality Verification")
    print("=" * 70)
    print("Comparing FAISS vs brute-force search")
    print("Expected: 95-99% overlap in top-5 results")
    print("=" * 70)

    overlaps = []

    for query in TEST_QUERIES:
        overlap = compare_results(query)
        overlaps.append(overlap)

    avg = sum(overlaps) / len(overlaps)

    print(f"\n{'='*70}")
    print(f"QUALITY SUMMARY")
    print(f"{'='*70}")
    print(f"Average overlap: {avg:.1f}%")
    print(f"Min overlap:     {min(overlaps):.0f}%")
    print(f"Max overlap:     {max(overlaps):.0f}%")
    print(f"{'='*70}")

    if avg >= 95:
        print(f"✅ PASS: {avg:.1f}% overlap ≥ 95% (excellent quality)")
    elif avg >= 80:
        print(f"⚠️  ACCEPTABLE: {avg:.1f}% overlap ≥ 80% (good quality)")
    else:
        print(f"❌ FAIL: {avg:.1f}% overlap < 80% (poor quality)")

    print()


if __name__ == "__main__":
    main()
