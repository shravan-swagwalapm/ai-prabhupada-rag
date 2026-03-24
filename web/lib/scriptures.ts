/**
 * Scripture name mapping and utilities.
 * Maps abbreviated codes from FAISS metadata to full, devotee-friendly names.
 */

const SCRIPTURE_NAMES: Record<string, string> = {
  bg: "Bhagavad-gita As It Is",
  sb: "Srimad-Bhagavatam",
  cc: "Sri Chaitanya-charitamrita",
  tlc: "Teachings of Lord Chaitanya",
  tlk: "Teachings of Lord Kapila",
  tqk: "Teachings of Queen Kunti",
  nod: "The Nectar of Devotion",
  noi: "The Nectar of Instruction",
  iso: "Sri Isopanisad",
  kb: "Krishna Book",
  lob: "Light of the Bhagavata",
  pop: "The Path of Perfection",
  letters: "Srila Prabhupada's Letters",
};

const SCRIPTURE_SHORT: Record<string, string> = {
  bg: "Bhagavad-gita",
  sb: "Srimad-Bhagavatam",
  cc: "Chaitanya-charitamrita",
  tlc: "Teachings of Lord Chaitanya",
  tlk: "Teachings of Lord Kapila",
  tqk: "Teachings of Queen Kunti",
  nod: "Nectar of Devotion",
  noi: "Nectar of Instruction",
  iso: "Sri Isopanisad",
  kb: "Krishna Book",
  lob: "Light of the Bhagavata",
  pop: "Path of Perfection",
  letters: "Prabhupada's Letters",
};

const SCRIPTURE_ICONS: Record<string, string> = {
  bg: "📖",
  sb: "📜",
  cc: "🙏",
  tlc: "📚",
  tlk: "📚",
  tqk: "📚",
  nod: "🌸",
  noi: "🌸",
  iso: "📿",
  kb: "🦚",
  lob: "🌅",
  pop: "🧘",
  letters: "✉️",
};

/**
 * Get full scripture name from abbreviation.
 * Parses chunk_id for chapter/verse info when available.
 */
export function getScriptureName(code: string, chunkId?: string): string {
  const baseName = SCRIPTURE_NAMES[code.toLowerCase()] || code;

  if (!chunkId) return baseName;

  // Try to extract chapter/verse from chunk_id patterns like "bg_2_47" or "sb_1_2_6"
  const parts = chunkId.split("_");
  if (parts.length < 2) return baseName;

  const codeLC = code.toLowerCase();

  if (codeLC === "bg" && parts.length >= 3) {
    return `${baseName}, Chapter ${parts[1]}, Verse ${parts.slice(2).join(".")}`;
  }

  if (codeLC === "sb" && parts.length >= 4) {
    return `${baseName}, Canto ${parts[1]}, Chapter ${parts[2]}, Verse ${parts.slice(3).join(".")}`;
  }

  if (codeLC === "cc" && parts.length >= 4) {
    const lilas: Record<string, string> = { adi: "Adi-lila", madhya: "Madhya-lila", antya: "Antya-lila" };
    const lila = lilas[parts[1]] || parts[1];
    return `${baseName}, ${lila}, Chapter ${parts[2]}, Text ${parts.slice(3).join(".")}`;
  }

  if (codeLC === "letters" && parts.length >= 2) {
    return `${baseName} (${parts.slice(1).join(" ")})`;
  }

  return baseName;
}

/**
 * Get short scripture name (for compact display).
 */
export function getScriptureShort(code: string): string {
  return SCRIPTURE_SHORT[code.toLowerCase()] || code;
}

/**
 * Get scripture icon emoji.
 */
export function getScriptureIcon(code: string): string {
  return SCRIPTURE_ICONS[code.toLowerCase()] || "📖";
}

/**
 * Get relevance color based on match percentage.
 * Used by SourceDetail and SourceDrawer.
 */
export function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

/**
 * Get SVG-compatible color values for a scripture.
 * Unlike getScriptureColor() which returns Tailwind classes,
 * this returns raw rgba values for SVG fill/stroke attributes.
 */
export function getScriptureSVGColor(code: string): { fill: string; stroke: string; text: string } {
  const colors: Record<string, { fill: string; stroke: string; text: string }> = {
    bg: { fill: "rgba(251,191,36,0.06)", stroke: "rgba(251,191,36,0.25)", text: "rgba(251,191,36,0.9)" },
    sb: { fill: "rgba(249,115,22,0.06)", stroke: "rgba(249,115,22,0.25)", text: "rgba(249,115,22,0.9)" },
    cc: { fill: "rgba(244,63,94,0.06)", stroke: "rgba(244,63,94,0.25)", text: "rgba(244,63,94,0.9)" },
    nod: { fill: "rgba(236,72,153,0.06)", stroke: "rgba(236,72,153,0.25)", text: "rgba(236,72,153,0.9)" },
    noi: { fill: "rgba(217,70,239,0.06)", stroke: "rgba(217,70,239,0.25)", text: "rgba(217,70,239,0.9)" },
    iso: { fill: "rgba(139,92,246,0.06)", stroke: "rgba(139,92,246,0.25)", text: "rgba(139,92,246,0.9)" },
    kb: { fill: "rgba(52,211,153,0.06)", stroke: "rgba(52,211,153,0.25)", text: "rgba(52,211,153,0.9)" },
    tlc: { fill: "rgba(251,146,60,0.06)", stroke: "rgba(251,146,60,0.25)", text: "rgba(251,146,60,0.9)" },
    tlk: { fill: "rgba(163,230,53,0.06)", stroke: "rgba(163,230,53,0.25)", text: "rgba(163,230,53,0.9)" },
    tqk: { fill: "rgba(45,212,191,0.06)", stroke: "rgba(45,212,191,0.25)", text: "rgba(45,212,191,0.9)" },
    lob: { fill: "rgba(251,191,36,0.06)", stroke: "rgba(251,191,36,0.25)", text: "rgba(251,191,36,0.9)" },
    pop: { fill: "rgba(168,162,158,0.06)", stroke: "rgba(168,162,158,0.25)", text: "rgba(168,162,158,0.9)" },
    letters: { fill: "rgba(56,189,248,0.06)", stroke: "rgba(56,189,248,0.25)", text: "rgba(56,189,248,0.9)" },
  };
  return colors[code.toLowerCase()] || { fill: "rgba(201,168,76,0.06)", stroke: "rgba(201,168,76,0.25)", text: "rgba(201,168,76,0.9)" };
}
