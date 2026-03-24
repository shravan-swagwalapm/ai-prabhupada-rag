"use client";

/**
 * Stylized line-art of Srila Prabhupada on his morning walk — SIDE PROFILE.
 * Walking to the right with cane, flowing saffron robes, shaved head, glasses.
 * Gold (#C9A84C) strokes on transparent background.
 * Two variants: "hero" (full walking figure) and "logo" (head profile in circle).
 *
 * NOTE: Uses hardcoded hex colors (not CSS vars) because var() is unreliable
 * inside SVG presentation attributes and gradient stops.
 */

const GOLD = "#C9A84C";
const GOLD_DIM = "#8B7332";

interface Props {
  variant?: "hero" | "logo";
  className?: string;
}

export default function PrabhupadaWalkingSVG({ variant = "hero", className = "" }: Props) {
  if (variant === "logo") {
    // Side-profile head in a circle
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
        {/* Gold ring */}
        <circle cx="32" cy="32" r="30" stroke={GOLD} strokeWidth="2" fill="none" />

        {/* Side-profile head facing right */}
        {/* Back of skull */}
        <path
          d="M22 30 Q20 18 27 12 Q33 8 38 14"
          stroke={GOLD} strokeWidth="1.6" fill="none" strokeLinecap="round"
        />
        {/* Top of head to forehead */}
        <path
          d="M38 14 Q42 18 42 24"
          stroke={GOLD} strokeWidth="1.6" fill="none" strokeLinecap="round"
        />
        {/* Forehead → nose (prominent) */}
        <path
          d="M42 24 L42 28 L46 32 L43 34"
          stroke={GOLD} strokeWidth="1.6" fill="none" strokeLinecap="round"
        />
        {/* Lips → chin → jaw */}
        <path
          d="M43 34 L42 36 Q39 40 34 42 Q28 42 24 38 L22 30"
          stroke={GOLD} strokeWidth="1.6" fill="none" strokeLinecap="round"
        />

        {/* Tilak */}
        <path d="M40 15 L39 23" stroke={GOLD} strokeWidth="1" fill="none" opacity="0.45" strokeLinecap="round" />

        {/* Sikha curling back */}
        <path d="M25 13 Q22 8 23 5" stroke={GOLD} strokeWidth="1.1" fill="none" strokeLinecap="round" />

        {/* Glasses — single lens in profile */}
        <circle cx="41" cy="27" r="3.2" stroke={GOLD_DIM} strokeWidth="0.9" fill="none" />
        {/* Temple arm */}
        <path d="M38 27 Q30 26 24 28" stroke={GOLD_DIM} strokeWidth="0.7" fill="none" />

        {/* Ear */}
        <path d="M23 27 Q21 30 23 33" stroke={GOLD} strokeWidth="0.8" fill="none" />

        {/* Neck + shoulder hint */}
        <path d="M30 42 L28 50" stroke={GOLD} strokeWidth="1.2" fill="none" />
        <path d="M36 42 L40 50" stroke={GOLD} strokeWidth="1.2" fill="none" />
        <path d="M18 56 Q28 48 40 50 Q46 52 48 56" stroke={GOLD} strokeWidth="1.3" fill="none" />

        {/* Robe drape */}
        <path d="M18 56 L16 62" stroke={GOLD} strokeWidth="1" fill="none" />
        <path d="M48 56 L50 62" stroke={GOLD} strokeWidth="1" fill="none" />
      </svg>
    );
  }

  // Hero variant — SIDE-PROFILE walking figure, facing right
  // Narrow body (side view), pronounced walking stride, robe flowing back
  return (
    <svg
      viewBox="0 0 160 320"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ height: 180, width: "auto" }}
      role="img"
      aria-label="Srila Prabhupada on his morning walk"
    >
      <defs>
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

        {/* ── HEAD (side profile, facing right) ── */}
        {/* Back of skull */}
        <path
          d="M52 44 Q48 24 58 14 Q66 6 74 14 Q80 20 80 30"
          stroke="url(#walk-fade)" strokeWidth="2.2" fill="none"
        />
        {/* Forehead → prominent nose → lips → chin */}
        <path
          d="M80 30 L81 38 L88 44 L84 48 L83 50 Q78 56 70 58"
          stroke="url(#walk-fade)" strokeWidth="2.2" fill="none"
        />
        {/* Jawline wrapping back */}
        <path
          d="M70 58 Q60 58 54 50 L52 44"
          stroke="url(#walk-fade)" strokeWidth="2.2" fill="none"
        />

        {/* Tilak */}
        <path d="M76 16 L74 28" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.4" />

        {/* Sikha curling back from crown */}
        <path d="M56 16 Q50 8 52 2" stroke="url(#walk-fade)" strokeWidth="1.4" fill="none" />

        {/* Glasses — one lens visible in profile */}
        <ellipse cx="79" cy="36" rx="5.5" ry="4.5" stroke="url(#walk-fade-dim)" strokeWidth="1.1" fill="none" />
        {/* Temple arm running back */}
        <path d="M74 36 Q62 34 54 38" stroke={GOLD_DIM} strokeWidth="0.8" fill="none" />

        {/* Ear */}
        <path d="M53 36 Q50 40 53 44" stroke={GOLD} strokeWidth="1" fill="none" />

        {/* ── NECK (slight forward lean — walking posture) ── */}
        <path d="M64 58 L62 70" stroke={GOLD} strokeWidth="1.6" fill="none" />
        <path d="M72 58 L76 70" stroke={GOLD} strokeWidth="1.6" fill="none" />

        {/* ── TORSO — narrow side view, leaning forward (walking) ── */}
        {/* Back line — curves forward showing walking lean */}
        <path
          d="M56 76 Q50 110 46 150 Q42 190 38 225"
          stroke="url(#walk-fade)" strokeWidth="2" fill="none"
        />
        {/* Front line */}
        <path
          d="M82 76 Q82 110 80 150 Q78 190 76 225"
          stroke="url(#walk-fade)" strokeWidth="2" fill="none"
        />

        {/* Shoulder line (narrow, side view) */}
        <path d="M56 76 Q64 70 76 70 Q80 72 82 76" stroke={GOLD} strokeWidth="1.8" fill="none" />

        {/* Chadar draped — flowing behind and billowing */}
        <path
          d="M56 76 Q44 86 34 108 Q24 136 20 170"
          stroke={GOLD} strokeWidth="1.6" fill="none" opacity="0.55"
        />
        <path
          d="M20 170 Q18 200 22 230 Q24 245 20 260"
          stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.35"
        />
        {/* Second chadar fold */}
        <path
          d="M58 80 Q48 92 40 115 Q32 145 28 178"
          stroke={GOLD} strokeWidth="0.8" fill="none" opacity="0.25"
        />

        {/* Robe fold lines */}
        <path d="M54 100 Q66 98 80 100" stroke={GOLD} strokeWidth="0.6" fill="none" opacity="0.25" />
        <path d="M50 135 Q64 132 80 135" stroke={GOLD} strokeWidth="0.6" fill="none" opacity="0.2" />
        <path d="M46 170 Q62 166 78 170" stroke={GOLD} strokeWidth="0.6" fill="none" opacity="0.18" />
        <path d="M42 205 Q58 200 76 205" stroke={GOLD} strokeWidth="0.6" fill="none" opacity="0.15" />

        {/* ── RIGHT ARM — forward, holding cane ── */}
        <path d="M82 76 Q92 92 96 108 Q98 116 96 120" stroke={GOLD} strokeWidth="1.6" fill="none" />
        {/* Hand gripping cane */}
        <path d="M96 120 Q94 124 97 126" stroke={GOLD} strokeWidth="1.1" fill="none" />

        {/* ── WALKING CANE — angled well forward ── */}
        <line x1="96" y1="122" x2="128" y2="292" stroke="url(#walk-fade)" strokeWidth="2.5" />
        {/* Curved handle */}
        <path d="M94 116 Q98 112 101 116" stroke={GOLD} strokeWidth="1.4" fill="none" />

        {/* ── LEFT ARM — behind body, relaxed swing ── */}
        <path d="M56 76 Q48 92 44 108" stroke={GOLD} strokeWidth="1.4" fill="none" opacity="0.6" />
        <path d="M44 108 Q42 112 44 114" stroke={GOLD} strokeWidth="0.9" fill="none" opacity="0.5" />

        {/* ── DHOTI BOTTOM — flowing scalloped edge ── */}
        <path d="M38 225 Q48 238 58 228" stroke={GOLD} strokeWidth="1.2" fill="none" opacity="0.5" />
        <path d="M66 228 Q72 236 76 230" stroke={GOLD} strokeWidth="1.2" fill="none" opacity="0.45" />
        {/* Flowing dhoti tail billowing behind */}
        <path d="M38 225 Q30 234 24 250 Q20 260 18 272" stroke={GOLD} strokeWidth="1.1" fill="none" opacity="0.3" />

        {/* ── LEGS — wide walking stride ── */}
        {/* Front leg — stepping well forward (right) */}
        <path d="M66 228 Q82 255 100 278" stroke="url(#walk-fade)" strokeWidth="1.8" fill="none" />
        {/* Front foot / sandal */}
        <path d="M100 278 Q105 282 110 280" stroke={GOLD} strokeWidth="1.3" fill="none" opacity="0.5" />

        {/* Back leg — pushing off well behind (left) */}
        <path d="M50 228 Q38 258 28 280" stroke="url(#walk-fade)" strokeWidth="1.6" fill="none" />
        {/* Back foot */}
        <path d="M28 280 Q24 284 20 282" stroke={GOLD} strokeWidth="1.2" fill="none" opacity="0.4" />

      </g>

      {/* Ground shadow — elongated, matching wide stride */}
      <ellipse cx="68" cy="292" rx="52" ry="3.5" fill={GOLD} opacity="0.06" />
    </svg>
  );
}
