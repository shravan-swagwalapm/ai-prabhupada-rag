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
 * Get a color class for scripture badges (for visual differentiation).
 */
export function getScriptureColor(code: string): string {
  const colors: Record<string, string> = {
    bg: "text-amber-300 bg-amber-500/10 border-amber-500/20",
    sb: "text-orange-300 bg-orange-500/10 border-orange-500/20",
    cc: "text-rose-300 bg-rose-500/10 border-rose-500/20",
    nod: "text-pink-300 bg-pink-500/10 border-pink-500/20",
    noi: "text-fuchsia-300 bg-fuchsia-500/10 border-fuchsia-500/20",
    iso: "text-violet-300 bg-violet-500/10 border-violet-500/20",
    kb: "text-emerald-300 bg-emerald-500/10 border-emerald-500/20",
    letters: "text-sky-300 bg-sky-500/10 border-sky-500/20",
  };
  return colors[code.toLowerCase()] || "text-saffron-300 bg-saffron-500/10 border-saffron-500/20";
}
