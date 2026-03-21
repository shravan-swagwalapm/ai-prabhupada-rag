#!/usr/bin/env python3
"""
RAG Query for Vedabase — with AI answers and voice synthesis

Usage:
    python rag_query.py "What is the soul?"              # Scripture search only
    python rag_query.py "What is the soul?" --ai          # + Claude AI answer (full)
    python rag_query.py "What is the soul?" --voice       # + AI answer + Prabhupada voice
    python rag_query.py --stats                           # View cache statistics

Pipeline:
    Question → FAISS Search (0.3s) → [Claude Sonnet 4.5 answer] → [ElevenLabs voice]
"""
import logging
import sys
import argparse
from pathlib import Path

# Configure logging for CLI usage — INFO level, clean format
logging.basicConfig(
    level=logging.WARNING,  # Keep CLI output clean; scripts use print for UX
    format="%(levelname)s %(name)s: %(message)s",
)

MAX_QUERY_LENGTH = 1000  # Guard against absurdly long CLI inputs

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

# Try FAISS first (Phase 3), fallback to optimized brute-force (Phase 1)
try:
    from search_scriptures_faiss import search_scriptures_faiss_cached as search_func
    from search_scriptures import print_cache_stats
    SEARCH_METHOD = "FAISS (Phase 3)"
except (ImportError, Exception) as e:
    print(f"⚠️  FAISS not available ({e}), using brute-force")
    from search_scriptures import search_scriptures_cached as search_func
    from search_scriptures import print_cache_stats
    SEARCH_METHOD = "Brute-force (Phase 1+2)"


def run_query(query: str, use_ai: bool = False, use_voice: bool = False, top_k: int = 5):
    """
    Run the full RAG pipeline.

    Args:
        query: User's spiritual question
        use_ai: Whether to generate Claude AI answer
        use_voice: Whether to synthesize voice (implies use_ai)
        top_k: Number of scripture passages to retrieve
    """
    # Input validation
    if not query or not query.strip():
        print("Error: query cannot be empty.")
        return 1

    query = query.strip()
    if len(query) > MAX_QUERY_LENGTH:
        print(f"Error: query too long ({len(query)} chars, max {MAX_QUERY_LENGTH}).")
        return 1

    if top_k < 1 or top_k > 50:
        print("Error: --top-k must be between 1 and 50.")
        return 1

    # Voice mode requires AI answer
    if use_voice:
        use_ai = True

    print(f"🔍 Search: {SEARCH_METHOD}")

    # Step 1: FAISS search
    results = list(search_func(query, top_k=top_k))

    print(f"\nQuery: {query}\n")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    # Display scripture passages
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['scripture']} (relevance: {result['similarity']:.3f})")
        print("-" * 80)
        print(result['text'][:500])
        print()

    # Step 2: AI answer generation
    if use_ai:
        print("=" * 80)
        mode = "concise" if use_voice else "full"
        print(f"\n🤖 Generating answer (Sonnet 4.5, {mode} mode)...\n")

        try:
            from generate_answer import generate_answer_streaming

            answer_text = ""
            for chunk in generate_answer_streaming(query, results, mode=mode):
                print(chunk, end="", flush=True)
                answer_text += chunk
            print("\n")

        except Exception as e:
            print(f"\nError generating AI answer: {e}")
            print("Check that ANTHROPIC_API_KEY is set in .env")
            return

        # Step 3: Voice synthesis
        if use_voice:
            print("=" * 80)
            print("\n🎙️  Synthesizing Prabhupada's voice...\n")

            try:
                from voice_synthesizer import synthesize_and_play
                audio_path = synthesize_and_play(answer_text)
                if audio_path:
                    print(f"\nAudio saved: {audio_path}")
            except ImportError:
                print("Error: voice_synthesizer.py not found")
                print("Voice synthesis requires ElevenLabs setup (Task 3)")
            except Exception as e:
                print(f"Error synthesizing voice: {e}")
                print("Check ELEVENLABS_API_KEY and voice_config.json")


def main():
    parser = argparse.ArgumentParser(
        description="AI Prabhupada — Scripture search with AI answers and voice"
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Your spiritual question"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate AI answer using Claude Sonnet 4.5"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Synthesize answer in Prabhupada's voice (implies --ai)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="View embedding cache statistics"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of scripture passages to retrieve (default: 5)"
    )

    args = parser.parse_args()

    if args.stats:
        print_cache_stats()
        return 0

    if not args.query:
        parser.print_help()
        return 1

    query = " ".join(args.query)
    run_query(query, use_ai=args.ai, use_voice=args.voice, top_k=args.top_k)
    return 0


if __name__ == "__main__":
    exit(main())
