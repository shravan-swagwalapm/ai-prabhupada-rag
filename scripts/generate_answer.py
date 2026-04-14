#!/usr/bin/env python3
"""
Claude Answer Generation for AI Prabhupada RAG
Uses Anthropic Sonnet 4.5 to generate scripture-grounded answers in Prabhupada's teaching style.

Two modes:
  - concise: ~400 words (3-4 min audio at 120 wpm), optimized for voice synthesis (default for --voice)
  - full: 800-1200 words, detailed with verse references (default for --ai)

Usage as module:
    from generate_answer import generate_answer
    answer = generate_answer(question, passages, mode="concise")
"""

import logging
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# Model — configurable via env var so deployments can switch without code changes
ANSWER_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

# Voice response length targets (measured: ~120 words/minute of Prabhupada speech)
MINIMUM_VOICE_WORDS = 340  # Hard floor for retry logic (slightly under 3 min to allow tolerance)
WORDS_PER_MINUTE = 120.0   # Measured from 7 cached ElevenLabs recordings

# Input guards — prevent runaway API costs / context overflow
MAX_QUESTION_LENGTH = 500
MAX_PASSAGE_CHARS = 800     # Truncate each passage to this length
MAX_PASSAGES = 10           # Use at most this many passages for context

# Timeouts — don't hang indefinitely if Anthropic is slow
ANTHROPIC_TIMEOUT = 120.0   # 2 minutes; streaming extends this per-read


def estimate_audio_duration(text: str) -> float:
    """Estimate audio duration in minutes from text word count."""
    word_count = len(text.split())
    return word_count / WORDS_PER_MINUTE


# --- System prompts ---

SYSTEM_PROMPT_CONCISE = """You are Srila Prabhupada, the founder-acharya of ISKCON. You are giving a spoken lecture answering a devotee's question. This text will be converted to audio using your cloned voice, so write EXACTLY as you spoke.

HOW PRABHUPADA SPOKE — follow this pattern precisely:
- Short, declarative sentences. Never more than 15 words per sentence.
- Frequent repetition for emphasis: "The soul is eternal. Eternal. It does not die."
- Rhetorical questions then answering yourself: "So what is the soul? The soul is the real person within the body."
- Start answers with "So," or "My dear friend," or "You see," or "Now,"
- Use your signature phrases naturally: "This is the verdict of all Vedic literature." "This is not sentiment, this is fact." "So we must understand this point." "Is it not?" "You see?"
- Use simple analogies: the drop of ocean water, the bird in the cage, the dress and the person wearing it, the sun and sunshine, the finger and the body
- When citing verses, say: "In the Bhagavad Gita, chapter two, verse twenty, Krishna says..."
- For Sanskrit verses, write them phonetically in Roman letters, not in Devanagari. For example: "na jayate mriyate va kadachin"

CONTENT DEPTH — this is a three-minute spoken lecture, not a brief remark:
- Reference at least two scripture verses, cross-referencing them as Prabhupada did. For example, connect a Bhagavad Gita verse with a supporting Srimad Bhagavatam verse.
- Use at least two analogies to make the philosophy accessible.
- Give a purport-style explanation of the primary verse, unpacking it sentence by sentence.
- After the main explanation, circle back and re-emphasize the key point from a different angle, as Prabhupada always did in lectures.
- End with a practical daily-life application and the Hare Krishna maha-mantra.

WHAT TO NEVER DO — these break voice synthesis:
- Never use bullet points, headers, numbered lists, or markdown formatting
- Never use parentheses, brackets, semicolons, colons, or em-dashes
- Never use abbreviations like "BG" or "SB" — always write the full scripture name
- Never write numbers as digits — always spell them out: "two" not "2"
- Never use quotes around Sanskrit — just say it naturally as Prabhupada did

FORMAT:
- Write between 360 and 450 words. Do not write fewer than 360 words. This is critical because the audio must be at least three minutes long.
- One flowing spoken paragraph. No line breaks.
- Use periods and commas for natural speech rhythm. Periods create pauses. Commas create brief pauses.
- End with a practical instruction and the Hare Krishna mantra.

GROUNDING:
You will receive scripture passages. Base your answer on these. Cite the specific verse by full name."""

SYSTEM_PROMPT_FULL = """You are answering questions as Srila Prabhupada would — the founder-acharya of ISKCON and translator of the Bhagavad Gita As It Is.

STYLE:
- Speak in first person as a teacher addressing a student
- Use Prabhupada's characteristic phrases and teaching patterns
- Ground every point in specific scripture verses (cite chapter and verse)
- Use the analogies Prabhupada favored to make philosophy accessible
- Maintain warmth, authority, and clarity

FORMAT:
Provide a comprehensive answer with these sections:
1. **Primary Teaching** — The core answer with verse reference
2. **Purport** — Deeper explanation as Prabhupada would give in his purports
3. **Practical Application** — How to apply this teaching in daily life
4. **Related Verses** — Other relevant verses that support the teaching

Keep the full answer between 800-1200 words.

GROUNDING:
You will receive scripture passages from the RAG system. Base your answer on these passages. Cite specific verses (e.g., "In Bhagavad Gita 2.20, Lord Krishna says..."). If passages don't directly address the question, be transparent and share the closest relevant teaching."""


# --- Client singleton ---

_anthropic_client = None
_client_lock = __import__("threading").Lock()


def get_anthropic_client():
    """
    Initialize and return the Anthropic client as a module-level singleton.
    Thread-safe. The anthropic.Anthropic client is itself thread-safe (connection pool).
    """
    global _anthropic_client

    if _anthropic_client is not None:
        return _anthropic_client

    with _client_lock:
        # Double-checked locking
        if _anthropic_client is not None:
            return _anthropic_client

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in .env\n"
                "Add: ANTHROPIC_API_KEY=your_key_here"
            )

        try:
            import anthropic
            _anthropic_client = anthropic.Anthropic(
                api_key=api_key,
                timeout=ANTHROPIC_TIMEOUT,
                default_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
            )
            logger.info("Anthropic client initialized (model: %s)", ANSWER_MODEL)
            return _anthropic_client
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip3 install 'anthropic>=0.40.0'"
            )


# --- Helpers ---

def _validate_inputs(question: str, passages: list) -> None:
    """Raise ValueError on invalid inputs before making any API calls."""
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Question too long: {len(question)} chars (max {MAX_QUESTION_LENGTH})"
        )
    if not isinstance(passages, (list, tuple)):
        raise ValueError("Passages must be a list")


def format_passages_for_context(passages: list) -> str:
    """
    Format RAG passages into context string for Claude.
    Applies per-passage truncation and a passage count cap to stay within
    Claude's context budget.
    """
    context_parts = []
    for i, p in enumerate(passages[:MAX_PASSAGES], 1):
        scripture = p.get("scripture", "Unknown")
        similarity = p.get("similarity", 0)
        text = p.get("text", "")[:MAX_PASSAGE_CHARS]  # Truncate long passages
        context_parts.append(
            f"[Passage {i}] {scripture} (relevance: {similarity:.1%})\n{text}"
        )
    return "\n\n".join(context_parts)


def _build_user_message(question: str, passages: list) -> str:
    context = format_passages_for_context(passages)
    return (
        f"Scripture passages from the Vedic library:\n\n{context}\n\n"
        f"---\n\nQuestion: {question}"
    )


# --- Public API ---

def generate_answer(question: str, passages: list, mode: str = "concise") -> str:
    """
    Generate an answer using Claude.

    Args:
        question: User's spiritual question (max 500 chars)
        passages: List of RAG result dicts with 'scripture', 'text', 'similarity' keys
        mode: "concise" (~400 words / 3-4 min audio, for voice) or "full" (800-1200 words)

    Returns:
        Generated answer text

    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If all API attempts fail
    """
    _validate_inputs(question, passages)

    client = get_anthropic_client()
    system_prompt = SYSTEM_PROMPT_CONCISE if mode == "concise" else SYSTEM_PROMPT_FULL
    user_message = _build_user_message(question, passages)

    logger.info("Generating %s answer for: '%s...'", mode, question[:60])
    start = time.time()

    try:
        response = client.messages.create(
            model=ANSWER_MODEL,
            max_tokens=2048 if mode == "full" else 1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as e:
        logger.error("Anthropic API call failed: %s", e, exc_info=True)
        raise

    answer = response.content[0].text
    elapsed = time.time() - start
    word_count = len(answer.split())
    logger.info("Answer generated in %.1fs (%d words)", elapsed, word_count)

    # Word count validation with single retry for concise (voice) mode
    if mode == "concise" and word_count < MINIMUM_VOICE_WORDS:
        logger.warning(
            "Answer too short for voice (%d words < %d minimum), retrying...",
            word_count, MINIMUM_VOICE_WORDS,
        )
        retry_message = (
            f"{user_message}\n\n"
            "IMPORTANT: Your previous response was too short for voice synthesis. "
            f"You must write at least 360 words. Write a full three-minute spoken lecture. "
            "Include two scripture cross-references, two analogies, a purport explanation, "
            "and a practical application. Do not stop early."
        )
        try:
            response = client.messages.create(
                model=ANSWER_MODEL,
                max_tokens=1024,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": retry_message}],
            )
            answer = response.content[0].text
            logger.info("Retry answer: %d words", len(answer.split()))
        except Exception as e:
            logger.error("Retry failed, using original short answer: %s", e)
            # Fall through — return the shorter answer rather than raising

    return answer


def generate_answer_streaming(question: str, passages: list, mode: str = "concise"):
    """
    Stream an answer using Claude.
    Yields text chunks as they arrive — useful for real-time display.

    Note: Streaming mode cannot retry for word count since chunks are already
    yielded. The prompt targets 360-450 words (~3-4 min audio) but no validation.

    Args:
        question: User's spiritual question
        passages: List of RAG result dicts
        mode: "concise" (~400 words / 3-4 min audio) or "full"

    Yields:
        str: Text chunks as they stream in

    Raises:
        ValueError: If inputs are invalid
    """
    _validate_inputs(question, passages)

    client = get_anthropic_client()
    system_prompt = SYSTEM_PROMPT_CONCISE if mode == "concise" else SYSTEM_PROMPT_FULL
    user_message = _build_user_message(question, passages)

    logger.info("Streaming %s answer for: '%s...'", mode, question[:60])

    try:
        with client.messages.stream(
            model=ANSWER_MODEL,
            max_tokens=2048 if mode == "full" else 1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error("Streaming answer failed: %s", e, exc_info=True)
        raise
