#!/usr/bin/env python3
"""
Detect Missing Sanskrit Terms — Find words the preprocessor misses.

Runs text through preprocess_for_voice() and checks if any IAST
diacritical characters survive. Reports the missed words so you
can add them to SANSKRIT_TERMS in sanskrit_pronunciation.py.

Usage:
    python detect_missing_sanskrit.py
    python detect_missing_sanskrit.py --text "Kṛṣṇa says in the śāstra..."
    python detect_missing_sanskrit.py --file answer.txt
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from sanskrit_pronunciation import preprocess_for_voice

# All IAST diacritical characters that should NOT survive preprocessing
_lower = set("āīūṛṝṣśṭḍṇṁḥñṅ")
IAST_CHARS = _lower | {c.upper() for c in _lower if c.upper() != c}


def find_missed_terms(text: str) -> list[dict]:
    """
    Find words that still contain IAST diacriticals after preprocessing.

    Args:
        text: Raw text (before preprocessing)

    Returns:
        List of dicts with 'word', 'position', and 'remaining_chars'
    """
    processed = preprocess_for_voice(text)
    missed = []

    for i, word in enumerate(processed.split()):
        remaining = [c for c in word if c in IAST_CHARS]
        if remaining:
            missed.append({
                "word": word,
                "position": i,
                "remaining_chars": remaining,
            })

    return missed


def analyze_text(text: str, label: str = "Input"):
    """Analyze text and print results."""
    print(f"\n--- {label} ---")
    print(f"Original ({len(text)} chars): {text[:120]}{'...' if len(text) > 120 else ''}")

    processed = preprocess_for_voice(text)
    print(f"Processed: {processed[:120]}{'...' if len(processed) > 120 else ''}")

    missed = find_missed_terms(text)

    if missed:
        print(f"\nMISSED TERMS ({len(missed)}):")
        for m in missed:
            chars = ", ".join(m["remaining_chars"])
            print(f"  '{m['word']}' — remaining IAST chars: {chars}")
        print(f"\nSuggested additions to SANSKRIT_TERMS:")
        for m in missed:
            clean = m["word"]
            for c in m["remaining_chars"]:
                # Show what the IAST fallback would produce
                pass
            print(f'    "{m["word"]}": "<phonetic_spelling>",')
    else:
        print("All IAST characters converted successfully.")

    return missed


# Sample texts representing real Claude RAG answers
SAMPLE_ANSWERS = [
    (
        "Soul Query",
        "So what is the soul? The soul is the real person within the body. "
        "In the Bhagavad-gītā, chapter two, verse twenty, Kṛṣṇa explains: "
        "na jāyate mriyate vā kadāchin. The ātmā is never born. "
        "The jīva changes bodies through saṁsāra. The Paramātmā witnesses."
    ),
    (
        "Karma Yoga",
        "Kṛṣṇa says perform niṣkāma-karma. Without desire for fruits. "
        "Ordinary karma binds the jīva to saṁsāra. But karma-yoga liberates. "
        "Arjuna was a kṣatriya. Dedicate the fruits of your yajña to Kṛṣṇa."
    ),
    (
        "Who is Krishna",
        "Kṛṣṇa is the Supreme Personality of Godhead. Bhagavān. "
        "In the Śrīmad-Bhāgavatam: kṛṣṇas tu bhagavān svayam. "
        "All avatāras come from Him. Rāma, Nṛsiṁha, Varāha. "
        "Brahmā, Śiva, Viṣṇu are subordinate. Kṛṣṇa is param brahman."
    ),
    (
        "Devotional Process",
        "The process begins with śraddhā. Then sādhu-saṅga. Then bhajana-kriyā. "
        "Then anartha-nivṛtti. Then niṣṭhā. Then ruci. Then āsakti. "
        "Then bhāva. Then prema. This is the path of bhakti described "
        "by Śrīla Rūpa Gosvāmī in the Bhakti-rasāmṛta-sindhu."
    ),
]


def main():
    parser = argparse.ArgumentParser(description="Detect missed Sanskrit terms")
    parser.add_argument("--text", help="Custom text to analyze")
    parser.add_argument("--file", help="File containing text to analyze")
    args = parser.parse_args()

    all_missed = []

    if args.text:
        missed = analyze_text(args.text, "Custom Input")
        all_missed.extend(missed)
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {path}")
            return 1
        text = path.read_text()
        missed = analyze_text(text, path.name)
        all_missed.extend(missed)
    else:
        print("Sanskrit Preprocessor Gap Analysis")
        print("=" * 60)
        print(f"Testing {len(SAMPLE_ANSWERS)} sample Claude answers...\n")

        for label, text in SAMPLE_ANSWERS:
            missed = analyze_text(text, label)
            all_missed.extend(missed)

    # Summary
    print(f"\n{'=' * 60}")
    if all_missed:
        unique = {m["word"] for m in all_missed}
        print(f"TOTAL: {len(unique)} unique missed terms across all samples")
        print("Action: Add these to SANSKRIT_TERMS in sanskrit_pronunciation.py")
    else:
        print("RESULT: All Sanskrit terms handled correctly!")
        print("The preprocessor caught every IAST character.")

    return 1 if all_missed else 0


if __name__ == "__main__":
    exit(main())
