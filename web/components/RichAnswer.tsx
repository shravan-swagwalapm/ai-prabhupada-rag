"use client";

import React, { useMemo } from "react";

interface Props {
  text: string;
  mode?: "text" | "voice";
  isStreaming?: boolean;
}

// ─── Sanskrit Detection (Two-Tier) ───────────────────────────────

/**
 * TIER 1 — Exclusive Sanskrit vocabulary.
 * These words ONLY appear in actual Sanskrit transliteration, never in
 * casual English sentences about spirituality.
 */
const SANSKRIT_EXCLUSIVE = new Set([
  "shreyan", "svanushthitat", "nidhanam", "shreyah", "bhayavahah",
  "vigunah", "evadhikaras", "phaleshu", "kadachana", "phala",
  "sango", "stvakar", "hetur", "asaktah", "samachar", "acharan",
  "ahankara", "buddhi", "manas", "prakriti", "purusha", "shakti",
  "tattva", "vairagya", "viveka", "sattva", "rajas", "tamas",
  "vidya", "avidya", "paramatma", "jivatma", "achintya", "bhedabheda",
  "sambandha", "abhidheya", "prayojana", "svarupa", "vapu", "karmany",
  "karmanah", "dharmo", "dharmat", "dharme", "tvam", "sarvam", "idam",
  "jagat", "aham", "sarva", "papa", "punya", "loka", "kala", "mrityu",
  "janma", "bandha", "mukti", "dasa",
]);

/**
 * TIER 2 — Common proper nouns and terms used freely in English
 * spiritual writing. These are weak signals on their own.
 */
const SANSKRIT_COMMON = new Set([
  "krishna", "rama", "vishnu", "narayana", "govinda", "madhava", "hare",
  "shiva", "durga", "lakshmi", "radha", "chaitanya", "nityananda",
  "sri", "srila", "swami", "goswami", "prabhupada", "acharya",
  "bhagavad", "bhagavatam", "upanisad", "upanishad", "purana", "veda",
  "vedanta", "sutra", "mantra", "sloka", "shloka", "gita",
  "dharma", "karma", "yoga", "atma", "atman", "brahma", "brahman",
  "bhakti", "jnana", "guna", "gunas", "maya", "samsara", "moksha",
  "nirvana", "guru", "deva", "asura", "avatara", "lila", "prema",
  "seva", "nama", "rupa", "rasa", "bhava",
]);

/** Combined set for inline highlighting */
const ALL_SANSKRIT = new Set([...SANSKRIT_EXCLUSIVE, ...SANSKRIT_COMMON]);

/**
 * Common English function words — their presence is a strong negative
 * signal against Sanskrit verse detection. Real transliteration never
 * contains "the", "is", "in", etc.
 */
const ENGLISH_FUNCTION_WORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
  "in", "of", "to", "for", "with", "on", "at", "by", "from", "as",
  "this", "that", "these", "those", "it", "its", "he", "she", "they",
  "we", "you", "his", "her", "their", "our", "your", "my",
  "and", "but", "or", "so", "if", "then", "than", "not", "no",
  "do", "does", "did", "has", "have", "had", "will", "would", "can",
  "could", "should", "may", "might", "must", "about", "also", "very",
  "just", "even", "now", "how", "what", "when", "where", "who", "which",
  "there", "here", "because", "through", "after", "before", "between",
  "all", "each", "every", "any", "some", "most", "other", "into",
  "only", "over", "such", "like", "more", "than", "up", "out",
  "one", "two", "three", "four", "five", "gives", "says", "answer",
  "chapter", "verse", "explains", "according", "means", "says",
]);

/** Regex for common Sanskrit transliteration word endings */
const SANSKRIT_ENDINGS = /(?:am|ah|ena|asya|anam|aya|anti|ati|eti|isu|esu|anah|atah|avah|itah)$/i;

/** Regex for diacritical marks used in IAST transliteration */
const DIACRITICAL_REGEX = /[āīūṛṝḷḹēōṃḥśṣṇṭḍñ]/;

/**
 * Tokenize a line into lowercase cleaned words for analysis.
 */
function tokenize(text: string): string[] {
  return text.toLowerCase().replace(/[.,;:!?"'"'()[\]{}—–-]/g, "").split(/\s+/).filter(Boolean);
}

/**
 * Count exclusive-tier Sanskrit words in a token list.
 */
function countExclusive(words: string[]): number {
  let count = 0;
  for (const w of words) {
    if (SANSKRIT_EXCLUSIVE.has(w) || SANSKRIT_ENDINGS.test(w)) count++;
  }
  return count;
}

/**
 * Count common-tier Sanskrit words in a token list.
 */
function countCommon(words: string[]): number {
  let count = 0;
  for (const w of words) {
    if (SANSKRIT_COMMON.has(w)) count++;
  }
  return count;
}

/**
 * Count English function words in a token list.
 */
function countEnglish(words: string[]): number {
  let count = 0;
  for (const w of words) {
    if (ENGLISH_FUNCTION_WORDS.has(w)) count++;
  }
  return count;
}

/**
 * Count how many words are recognizable Sanskrit (either tier).
 * Used for inline highlighting.
 */
function countSanskritWords(text: string): number {
  const words = tokenize(text);
  let count = 0;
  for (const w of words) {
    if (ALL_SANSKRIT.has(w) || SANSKRIT_ENDINGS.test(w)) count++;
  }
  return count;
}

/**
 * Detect if a line is a Sanskrit verse (transliteration).
 *
 * Two-tier approach:
 * - Diacriticals → always a verse
 * - Exclusive Sanskrit words are strong positive signals
 * - English function words are strong negative signals
 * - Common Sanskrit words (krishna, gita, etc.) are weak signals
 */
function isSanskritVerse(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed || trimmed.length < 10) return false;

  // Strong signal: IAST diacriticals present → always verse
  if (DIACRITICAL_REGEX.test(trimmed)) return true;

  const words = tokenize(trimmed);
  const wordCount = words.length;
  if (wordCount === 0) return false;

  const exclusiveCount = countExclusive(words);
  const commonCount = countCommon(words);
  const totalSanskrit = exclusiveCount + commonCount;
  const englishWords = countEnglish(words);

  // English function words are a strong negative signal:
  // real Sanskrit transliteration never contains "the", "is", "in", etc.
  if (englishWords >= 3) return false;
  if (englishWords >= 2 && exclusiveCount === 0) return false;

  // Exclusive terms are strong positive signals
  if (exclusiveCount >= 2) return true;
  if (exclusiveCount >= 1 && totalSanskrit >= 3 && wordCount <= 12) return true;

  // High density of ANY Sanskrit in a short line with NO English words
  if (englishWords === 0 && totalSanskrit >= 3 && wordCount <= 10) return true;
  if (englishWords === 0 && wordCount <= 12 && wordCount > 0 && totalSanskrit / wordCount > 0.7) return true;

  return false;
}

/**
 * Detect if a line is a verse reference.
 */
function isVerseReference(line: string): boolean {
  const trimmed = line.trim();
  return /^(Bhagavad|Srimad|Sri |BG|SB|CC|ISO|NOD|NOI|TLK|—\s*(Bhagavad|Srimad|Sri))/.test(trimmed)
    || /^—?\s*(Bhagavad|Srimad|Sri)/.test(trimmed);
}

/**
 * Detect if a line is an English translation of a preceding verse.
 * Translations are typically quoted English text that follows a Sanskrit verse.
 */
function isTranslation(line: string, prevBlock: Block | undefined): boolean {
  if (!prevBlock || prevBlock.type !== "verse") return false;
  const trimmed = line.trim();

  // Starts with a quote mark
  if (trimmed.startsWith('"') || trimmed.startsWith('\u201c')) {
    const words = tokenize(trimmed);
    const englishCount = countEnglish(words);
    // Primarily English content
    return englishCount >= 2;
  }

  return false;
}

// ─── Block Parser ─────────────────────────────────────────────────

type Block =
  | { type: "h1"; text: string }
  | { type: "h2"; text: string }
  | { type: "h3"; text: string }
  | { type: "verse"; text: string }
  | { type: "translation"; text: string }
  | { type: "verse-ref"; text: string }
  | { type: "quote"; text: string }
  | { type: "paragraph"; text: string }
  | { type: "mantra"; text: string }
  | { type: "bullet-list"; items: string[] }
  | { type: "verse-card"; lines: string[]; translation?: string; ref?: string };

function parseBlocks(text: string): Block[] {
  // Pre-process: ensure markdown headers start on their own lines.
  // The AI sometimes generates "...sentence. ## Header" inline.
  // Exclude # from the lookbehind to avoid splitting "##" into "#\n#".
  const preprocessed = text.replace(/([^\n#])(#{1,3} )/g, "$1\n$2");
  const lines = preprocessed.split("\n");
  const blocks: Block[] = [];
  let currentParagraph: string[] = [];
  let currentBullets: string[] = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const joined = currentParagraph.join(" ").trim();
      if (joined) {
        blocks.push({ type: "paragraph", text: joined });
      }
      currentParagraph = [];
    }
  };

  const flushBullets = () => {
    if (currentBullets.length > 0) {
      blocks.push({ type: "bullet-list", items: [...currentBullets] });
      currentBullets = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    // Empty line = paragraph break
    if (!trimmed) {
      flushParagraph();
      flushBullets();
      continue;
    }

    // Horizontal rules (---, ***, ___) — skip them (just section dividers)
    if (/^[-*_]{3,}$/.test(trimmed)) {
      flushParagraph();
      flushBullets();
      continue;
    }

    // Blockquote lines (> text) — treat as verse if Sanskrit, else as quote
    if (trimmed.startsWith("> ")) {
      flushParagraph();
      flushBullets();
      const inner = trimmed.slice(2).trim();
      if (isSanskritVerse(inner)) {
        blocks.push({ type: "verse", text: inner });
      } else {
        blocks.push({ type: "translation", text: inner.replace(/^[""\u201c]|[""\u201d]$/g, "") });
      }
      continue;
    }

    // Bullet list items (- or * or numbered)
    const bulletMatch = trimmed.match(/^[-*•]\s+(.+)/) || trimmed.match(/^\d+[.)]\s+(.+)/);
    if (bulletMatch) {
      flushParagraph();
      currentBullets.push(bulletMatch[1]);
      continue;
    } else if (currentBullets.length > 0) {
      flushBullets();
    }

    // Markdown headers
    if (trimmed.startsWith("### ")) {
      flushParagraph();
      blocks.push({ type: "h3", text: trimmed.slice(4).trim() });
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushParagraph();
      blocks.push({ type: "h2", text: trimmed.slice(3).trim() });
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushParagraph();
      blocks.push({ type: "h1", text: trimmed.slice(2).trim() });
      continue;
    }

    // Hare Krishna mantra detection
    if (/Hare Krishna.*Hare Krishna.*Krishna Krishna.*Hare Hare/i.test(trimmed)) {
      flushParagraph();
      blocks.push({ type: "mantra", text: trimmed });
      continue;
    }

    // Verse reference line
    if (isVerseReference(trimmed)) {
      flushParagraph();
      blocks.push({ type: "verse-ref", text: trimmed });
      continue;
    }

    // Translation detection: quoted English text right after a verse
    const lastBlock = blocks[blocks.length - 1];
    if (isTranslation(trimmed, lastBlock)) {
      flushParagraph();
      const cleanText = trimmed.replace(/^[""\u201c]|[""\u201d]$/g, "");
      blocks.push({ type: "translation", text: cleanText });
      continue;
    }

    // Quoted verse (starts with " and contains Sanskrit)
    if (trimmed.startsWith('"') && isSanskritVerse(trimmed)) {
      flushParagraph();
      blocks.push({ type: "quote", text: trimmed.replace(/^"|"$/g, "") });
      continue;
    }

    // Sanskrit verse line (standalone, not too long)
    if (isSanskritVerse(trimmed) && trimmed.length < 250) {
      flushParagraph();
      blocks.push({ type: "verse", text: trimmed });
      continue;
    }

    // Regular text
    currentParagraph.push(trimmed);
  }

  flushParagraph();
  flushBullets();
  return mergeVerseCards(blocks);
}

/**
 * Post-process blocks: merge consecutive verse, translation, verse-ref,
 * and quote blocks into unified "verse-card" blocks so they render as
 * a single visual unit.
 */
function mergeVerseCards(blocks: Block[]): Block[] {
  const merged: Block[] = [];
  let i = 0;

  while (i < blocks.length) {
    const block = blocks[i];

    // Start a card when we hit a verse or quote block
    if (block.type === "verse" || block.type === "quote") {
      const lines: string[] = [block.type === "quote" ? `\u201c${block.text}\u201d` : block.text];
      let translation: string | undefined;
      let ref: string | undefined;
      i++;

      // Consume consecutive verse/quote/translation/verse-ref blocks
      while (i < blocks.length) {
        const next = blocks[i];
        if (next.type === "verse" || next.type === "quote") {
          lines.push(next.type === "quote" ? `\u201c${next.text}\u201d` : next.text);
          i++;
        } else if (next.type === "translation" && !translation) {
          translation = next.text;
          i++;
        } else if (next.type === "verse-ref" && !ref) {
          ref = next.text;
          i++;
        } else {
          break;
        }
      }

      merged.push({ type: "verse-card", lines, translation, ref });
      continue;
    }

    // Standalone translation or ref that wasn't preceded by a verse —
    // wrap them in a card too so they always get the box treatment
    if (block.type === "translation") {
      merged.push({ type: "verse-card", lines: [], translation: block.text });
      i++;
      continue;
    }
    if (block.type === "verse-ref") {
      merged.push({ type: "verse-card", lines: [], ref: block.text });
      i++;
      continue;
    }

    merged.push(block);
    i++;
  }

  return merged;
}

// ─── Voice Mode Splitter ──────────────────────────────────────────

/**
 * For voice mode: split wall of text into readable paragraphs.
 */
function splitVoiceText(text: string): Block[] {
  // If it already has structure, parse normally
  if (text.includes("\n\n") || text.includes("# ") || text.includes("\n- ")) {
    return parseBlocks(text);
  }

  // Split into sentences
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  const blocks: Block[] = [];
  const SENTENCES_PER_PARAGRAPH = 3;

  let i = 0;
  while (i < sentences.length) {
    const sentence = sentences[i].trim();

    // Check if this sentence contains a Sanskrit verse
    if (isSanskritVerse(sentence) && sentence.length < 250) {
      blocks.push({ type: "verse", text: sentence });
      i++;
      continue;
    }

    // Check for Hare Krishna mantra
    if (/Hare Krishna.*Hare Krishna.*Krishna Krishna.*Hare Hare/i.test(sentence)) {
      blocks.push({ type: "mantra", text: sentence });
      i++;
      continue;
    }

    // Group 3 sentences into a paragraph
    const chunk = sentences.slice(i, i + SENTENCES_PER_PARAGRAPH).join(" ").trim();
    if (chunk) {
      blocks.push({ type: "paragraph", text: chunk });
    }
    i += SENTENCES_PER_PARAGRAPH;
  }

  return blocks;
}

// ─── Inline Sanskrit Highlighting ─────────────────────────────────

/**
 * Process inline markdown: **bold**, *italic*, and Sanskrit highlighting.
 * Handles nested patterns like **bold *italic* bold**.
 */
function renderInlineText(text: string): React.ReactNode {
  // First pass: split on markdown bold and italic markers
  const parts: React.ReactNode[] = [];
  let key = 0;

  // Regex: match **bold**, *italic* (but not ** inside **)
  // Process bold first, then italic within remaining segments
  const segments = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  for (const seg of segments) {
    if (!seg) continue;

    // Bold: **text**
    if (seg.startsWith("**") && seg.endsWith("**")) {
      const inner = seg.slice(2, -2);
      parts.push(
        <strong key={key++} className="font-semibold" style={{ color: "var(--text-primary)" }}>
          {inner}
        </strong>
      );
      continue;
    }

    // Italic: *text*
    if (seg.startsWith("*") && seg.endsWith("*") && seg.length > 2) {
      const inner = seg.slice(1, -1);
      parts.push(
        <em key={key++} className="italic" style={{ color: "var(--vermillion-bright)" }}>
          {inner}
        </em>
      );
      continue;
    }

    // Plain text — apply Sanskrit highlighting
    parts.push(<React.Fragment key={key++}>{highlightSanskrit(seg)}</React.Fragment>);
  }

  return parts.length > 0 ? parts : text;
}

/**
 * Detect Sanskrit phrases within English text and highlight them
 * in Vedabase red-brown italic. Requires 2+ consecutive Sanskrit words.
 */
function highlightSanskrit(text: string): React.ReactNode {
  const words = text.split(/(\s+)/); // preserve whitespace
  const result: React.ReactNode[] = [];
  let sanskritRun: string[] = [];
  let normalRun: string[] = [];
  let key = 0;

  const flushNormal = () => {
    if (normalRun.length > 0) {
      result.push(<span key={key++}>{normalRun.join("")}</span>);
      normalRun = [];
    }
  };

  const flushSanskrit = () => {
    if (sanskritRun.length > 0) {
      const joined = sanskritRun.join("");
      const sanskritWordCount = countSanskritWords(joined);
      if (sanskritWordCount >= 2) {
        flushNormal();
        result.push(
          <span key={key++} style={{ color: "var(--vermillion-bright)" }} className="italic font-medium">
            {joined}
          </span>
        );
      } else {
        normalRun.push(...sanskritRun);
      }
      sanskritRun = [];
    }
  };

  for (const token of words) {
    if (/^\s+$/.test(token)) {
      if (sanskritRun.length > 0) {
        sanskritRun.push(token);
      } else {
        normalRun.push(token);
      }
      continue;
    }

    const clean = token.replace(/[.,;:!?"'"'()[\]{}]/g, "").toLowerCase();
    const isSanskrit = ALL_SANSKRIT.has(clean) || SANSKRIT_ENDINGS.test(clean)
      || DIACRITICAL_REGEX.test(token);

    if (isSanskrit) {
      sanskritRun.push(token);
    } else {
      flushSanskrit();
      normalRun.push(token);
    }
  }

  flushSanskrit();
  flushNormal();

  return result.length > 0 ? result : text;
}

// ─── Component ────────────────────────────────────────────────────

export default function RichAnswer({ text, mode = "text", isStreaming }: Props) {
  const blocks = useMemo(() => {
    if (!text) return [];
    return mode === "voice" ? splitVoiceText(text) : parseBlocks(text);
  }, [text, mode]);

  if (!text && !isStreaming) return null;

  return (
    <div className={`rich-answer space-y-5 ${isStreaming ? "streaming-cursor" : ""}`}>
      {blocks.map((block, i) => {
        switch (block.type) {
          case "h1":
            return (
              <h2
                key={i}
                className="text-2xl font-serif pt-3 pb-2"
                style={{
                  color: "var(--text-primary)",
                  borderBottom: "1px solid #D4C9B8",
                  letterSpacing: "-0.02em",
                }}
              >
                {block.text}
              </h2>
            );
          case "h2":
            return (
              <h3
                key={i}
                className="text-xl font-serif pt-5 pb-1 flex items-center gap-3"
                style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
              >
                <span
                  className="w-1 h-6 rounded-full inline-block shrink-0"
                  style={{ background: "var(--gold-dim)" }}
                />
                {block.text}
              </h3>
            );
          case "h3":
            return (
              <h4
                key={i}
                className="text-lg font-serif pt-3 font-medium"
                style={{ color: "var(--text-body)", letterSpacing: "-0.02em" }}
              >
                {block.text}
              </h4>
            );
          case "verse-card":
            return (
              <div
                key={i}
                className="my-6 overflow-hidden"
                style={{
                  borderLeft: "3px solid #C9A84C",
                  background: "rgba(201,168,76,0.03)",
                  borderRadius: "0 12px 12px 0",
                  padding: "14px 18px",
                }}
              >
                <div className="space-y-3">
                  {block.lines.length > 0 && (
                    <div className="space-y-1">
                      {block.lines.map((line, j) => (
                        <p
                          key={j}
                          className="font-serif italic"
                          style={{ color: "#c75b39", fontSize: 15 }}
                        >
                          {line}
                        </p>
                      ))}
                    </div>
                  )}
                  {block.translation && (
                    <p
                      className="font-sans"
                      style={{
                        color: "#2C4A78",
                        fontWeight: 600,
                        fontSize: 14,
                        borderTop: block.lines.length > 0 ? "1px solid rgba(201,168,76,0.15)" : undefined,
                        paddingTop: block.lines.length > 0 ? "0.75rem" : undefined,
                      }}
                    >
                      &ldquo;{block.translation}&rdquo;
                    </p>
                  )}
                  {block.ref && (
                    <p
                      className="text-xs font-sans uppercase tracking-widest"
                      style={{ color: "#8B7332" }}
                    >
                      {block.ref}
                    </p>
                  )}
                </div>
              </div>
            );
          /* Legacy fallbacks — these shouldn't appear after mergeVerseCards,
             but keep them so the compiler doesn't complain */
          case "verse":
          case "translation":
          case "quote":
          case "verse-ref":
            return null;
          case "mantra":
            return (
              <div
                key={i}
                className="mantra-block my-6 py-5 px-8 rounded-xl text-center"
                style={{
                  background: "linear-gradient(to right, rgba(201,168,76,0.08), rgba(194,77,44,0.06), rgba(201,168,76,0.08))",
                  border: "1px solid rgba(201,168,76,0.2)",
                }}
              >
                <p
                  className="font-serif text-xl leading-loose tracking-wide"
                  style={{ color: "var(--text-primary)" }}
                >
                  {block.text}
                </p>
              </div>
            );
          case "bullet-list":
            return (
              <ul key={i} className="space-y-2 pl-2 my-3">
                {block.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-3">
                    <span
                      className="mt-2.5 w-1.5 h-1.5 rounded-full shrink-0"
                      style={{ background: "var(--gold-dim)" }}
                    />
                    <span
                      className="font-sans"
                      style={{ color: "var(--text-body)", fontSize: 18, fontWeight: 450, lineHeight: 1.75 }}
                    >
                      {renderInlineText(item)}
                    </span>
                  </li>
                ))}
              </ul>
            );
          case "paragraph":
            return (
              <p
                key={i}
                className="font-sans"
                style={{
                  color: "var(--text-body)",
                  fontSize: 18,
                  fontWeight: 450,
                  lineHeight: 1.75,
                  marginBottom: 18,
                }}
              >
                {renderInlineText(block.text)}
              </p>
            );
          default:
            return null;
        }
      })}
    </div>
  );
}
