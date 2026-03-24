"use client";

/**
 * Stylized line-art of Srila Prabhupada on his morning walk.
 * Gold (#C9A84C) strokes on transparent background.
 * Two variants: "hero" (full walking figure) and "logo" (head portrait in circle).
 *
 * NOTE: Uses hardcoded hex colors (not CSS vars) because var() is unreliable
 * inside SVG presentation attributes and gradient stops.
 */

const GOLD = "#C9A84C";
const GOLD_DIM = "#8B7332";
const GOLD_FAINT = "rgba(201,168,76,0.35)";

interface Props {
  variant?: "hero" | "logo";
  className?: string;
}

export default function PrabhupadaWalkingSVG({ variant = "hero", className = "" }: Props) {
  if (variant === "logo") {
    return (
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        style={{ width: 38, height: 38 }}
        role="img"
        aria-label="Prabhupada AI"
      >
        {/* Gold ring border */}
        <circle cx="32" cy="32" r="30" stroke={GOLD} strokeWidth="2" fill="none" />

        {/* Head */}
        <ellipse cx="32" cy="24" rx="9" ry="10" stroke={GOLD} strokeWidth="1.6" fill="none" />

        {/* Tilak */}
        <path d="M32 17 L30.8 22 L33.2 22 Z" fill={GOLD} opacity="0.5" />

        {/* Sikha */}
        <path d="M32 14 Q34 10 33 7" stroke={GOLD} strokeWidth="1.2" fill="none" strokeLinecap="round" />

        {/* Glasses */}
        <circle cx="29" cy="24" r="2.8" stroke={GOLD_DIM} strokeWidth="0.9" fill="none" />
        <circle cx="36" cy="24" r="2.8" stroke={GOLD_DIM} strokeWidth="0.9" fill="none" />
        <line x1="31.8" y1="24" x2="33.2" y2="24" stroke={GOLD_DIM} strokeWidth="0.7" />

        {/* Shoulders / robe neckline */}
        <path d="M22 44 Q27 37 32 35 Q37 37 42 44" stroke={GOLD} strokeWidth="1.5" fill="none" />

        {/* Robe drape lines */}
        <path d="M22 44 L19 60" stroke={GOLD} strokeWidth="1.3" fill="none" />
        <path d="M42 44 L45 60" stroke={GOLD} strokeWidth="1.3" fill="none" />
        <path d="M32 35 L32 56" stroke={GOLD} strokeWidth="0.7" fill="none" opacity="0.3" />
      </svg>
    );
  }

  // Hero variant — full walking figure
  return (
    <svg
      viewBox="0 0 200 300"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ height: 180, width: "auto" }}
      role="img"
      aria-label="Srila Prabhupada on his morning walk"
    >
      <defs>
        {/* Vertical fade for feet */}
        <linearGradient id="walk-fade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={GOLD} stopOpacity="1" />
          <stop offset="80%" stopColor={GOLD} stopOpacity="0.9" />
          <stop offset="100%" stopColor={GOLD} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="walk-fade-dim" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={GOLD_DIM} stopOpacity="1" />
          <stop offset="80%" stopColor={GOLD_DIM} stopOpacity="0.9" />
          <stop offset="100%" stopColor={GOLD_DIM} stopOpacity="0" />
        </linearGradient>
      </defs>

      <g strokeLinecap="round" strokeLinejoin="round">
        {/* ── Head ── */}
        <ellipse cx="100" cy="35" rx="15" ry="17" stroke="url(#walk-fade)" strokeWidth="2.2" fill="none" />

        {/* Tilak */}
        <path d="M100 22 L98 30 L102 30 Z" fill={GOLD} opacity="0.4" />

        {/* Sikha (tuft) */}
        <path d="M100 18 Q103 12 101 6" stroke="url(#walk-fade)" strokeWidth="1.5" fill="none" />

        {/* Glasses */}
        <ellipse cx="95" cy="34" rx="4.5" ry="4" stroke="url(#walk-fade-dim)" strokeWidth="1.1" fill="none" />
        <ellipse cx="107" cy="34" rx="4.5" ry="4" stroke="url(#walk-fade-dim)" strokeWidth="1.1" fill="none" />
        <line x1="99.5" y1="34" x2="102.5" y2="34" stroke={GOLD_DIM} strokeWidth="0.8" />
        {/* Ear hooks */}
        <path d="M90.5 34 Q88 33 87 36" stroke={GOLD_DIM} strokeWidth="0.7" fill="none" />
        <path d="M111.5 34 Q114 33 115 36" stroke={GOLD_DIM} strokeWidth="0.7" fill="none" />

        {/* Nose hint */}
        <path d="M100 33 Q98 37 100 39" stroke={GOLD} strokeWidth="0.8" fill="none" />

        {/* ── Neck ── */}
        <line x1="95" y1="51" x2="93" y2="62" stroke={GOLD} strokeWidth="1.6" />
        <line x1="105" y1="51" x2="107" y2="62" stroke={GOLD} strokeWidth="1.6" />

        {/* ── Shoulders ── */}
        <path d="M72 72 Q92 62 100 64 Q108 62 128 72" stroke={GOLD} strokeWidth="2" fill="none" />

        {/* ── Chadar (shawl) — left drape ── */}
        <path d="M72 72 Q70 110 73 155 Q75 190 72 230" stroke="url(#walk-fade)" strokeWidth="2" fill="none" />
        {/* Inner fold */}
        <path d="M77 76 Q75 120 78 165 Q79 200 77 240" stroke={GOLD} strokeWidth="1" fill="none" opacity="0.35" />

        {/* ── Right side of robe ── */}
        <path d="M128 72 Q130 110 127 155 Q125 200 128 245" stroke="url(#walk-fade)" strokeWidth="2" fill="none" />

        {/* ── Central fold ── */}
        <path d="M100 64 Q99 130 101 200 Q102 240 100 270" stroke={GOLD} strokeWidth="0.8" fill="none" opacity="0.2" />

        {/* ── Horizontal dhoti folds ── */}
        <path d="M76 120 Q100 116 124 120" stroke={GOLD} strokeWidth="0.7" fill="none" opacity="0.3" />
        <path d="M74 160 Q100 155 126 160" stroke={GOLD} strokeWidth="0.7" fill="none" opacity="0.25" />
        <path d="M73 200 Q100 195 127 200" stroke={GOLD} strokeWidth="0.7" fill="none" opacity="0.2" />

        {/* ── Walking cane (right hand) ── */}
        <line x1="130" y1="82" x2="142" y2="275" stroke="url(#walk-fade)" strokeWidth="2.5" />
        {/* Cane handle */}
        <path d="M129 78 Q132 74 135 78 Q136 80 133 84" stroke={GOLD} strokeWidth="1.5" fill="none" />

        {/* ── Right arm (holding cane) ── */}
        <path d="M128 72 Q133 78 130 82" stroke={GOLD} strokeWidth="1.6" fill="none" />

        {/* ── Left arm (relaxed) ── */}
        <path d="M72 72 Q64 92 60 110 Q58 118 62 122" stroke={GOLD} strokeWidth="1.6" fill="none" />
        {/* Left hand */}
        <path d="M62 122 Q60 126 63 128" stroke={GOLD} strokeWidth="1.1" fill="none" />

        {/* ── Legs (mid-stride) ── */}
        {/* Left leg forward */}
        <path d="M90 235 Q85 255 78 278" stroke="url(#walk-fade)" strokeWidth="1.6" fill="none" />
        <path d="M78 278 Q74 282 71 281" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.4" />

        {/* Right leg back */}
        <path d="M110 235 Q115 255 122 273" stroke="url(#walk-fade)" strokeWidth="1.6" fill="none" />
        <path d="M122 273 Q126 277 129 276" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.4" />

        {/* ── Dhoti bottom edge ── */}
        <path d="M72 230 Q80 242 90 235" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.5" />
        <path d="M110 235 Q120 242 128 245" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.5" />
      </g>

      {/* Ground shadow */}
      <ellipse cx="102" cy="288" rx="38" ry="4" fill={GOLD} opacity="0.06" />
    </svg>
  );
}
