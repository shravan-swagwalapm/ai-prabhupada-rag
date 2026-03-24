#!/usr/bin/env python3
"""
Seed FAQ answers — runs each FAQ question through FAISS + Claude once,
saves results to data/faq.json so they can be served instantly without
consuming credits.

Usage:
    python3 scripts/seed_faq.py
"""
import json
import os
import sys
from pathlib import Path

# Ensure scripts/ is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from search_scriptures_faiss import search_scriptures_faiss, load_faiss_index
from generate_answer import generate_answer

FAQ_QUESTIONS = [
    "What is the nature of the soul?",
    "How should one perform their duty?",
    "What is the purpose of human life?",
    "What should a person do when they get suicidal thoughts?",
    "How can someone be saved from addictions?",
]

TOP_K = 5
MODE = "concise"

OUTPUT = PROJECT_ROOT / "data" / "faq.json"


def main():
    print("Loading FAISS index...")
    index, metadata = load_faiss_index()
    if index is None:
        print("ERROR: FAISS index failed to load")
        sys.exit(1)
    print(f"FAISS loaded ({index.ntotal} vectors)")

    faq_entries = []

    for i, question in enumerate(FAQ_QUESTIONS, 1):
        print(f"\n[{i}/{len(FAQ_QUESTIONS)}] {question}")

        # Search
        print("  Searching...")
        results = list(search_scriptures_faiss(question, top_k=TOP_K))
        passages = [
            {
                "scripture": r["scripture"],
                "text": r["text"],
                "similarity": round(r["similarity"], 4),
                "chunk_id": r.get("chunk_id", ""),
            }
            for r in results
        ]
        print(f"  Found {len(passages)} passages")

        # Generate answer
        print("  Generating answer...")
        answer_text = generate_answer(question, results, mode=MODE)
        print(f"  Answer: {len(answer_text)} chars")

        faq_entries.append({
            "question": question,
            "answer_text": answer_text,
            "passages": passages,
        })

    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(faq_entries, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(faq_entries)} FAQ entries to {OUTPUT}")


if __name__ == "__main__":
    main()
