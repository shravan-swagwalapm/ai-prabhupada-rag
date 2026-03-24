"use client";

import { useState, useEffect } from "react";

const SIZES = [
  { label: "Default", scale: 1 },
  { label: "Large", scale: 1.15 },
  { label: "Extra Large", scale: 1.3 },
];

const STORAGE_KEY = "prabhupada_font_scale";

export default function FontSizeToggle() {
  const [sizeIndex, setSizeIndex] = useState(0);

  // Restore saved preference
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const idx = parseInt(saved, 10);
      if (idx >= 0 && idx < SIZES.length) {
        setSizeIndex(idx);
        document.documentElement.style.fontSize = `${SIZES[idx].scale * 100}%`;
      }
    }
  }, []);

  const cycle = () => {
    const next = (sizeIndex + 1) % SIZES.length;
    setSizeIndex(next);
    localStorage.setItem(STORAGE_KEY, String(next));
    document.documentElement.style.fontSize = `${SIZES[next].scale * 100}%`;
  };

  return (
    <button
      onClick={cycle}
      className="flex items-center justify-center transition-all"
      style={{
        background: "rgba(255,255,255,0.65)",
        border: "1px solid var(--glass-border-hover)",
        borderRadius: 10,
        minHeight: 44,
        minWidth: 44,
        gap: 2,
      }}
      aria-label={`Font size: ${SIZES[sizeIndex].label}. Tap to increase.`}
      title={`Text size: ${SIZES[sizeIndex].label}`}
    >
      <span
        className="font-serif"
        style={{
          fontSize: 13,
          color: "var(--text-muted)",
          lineHeight: 1,
        }}
      >
        A
      </span>
      <span
        className="font-serif font-bold"
        style={{
          fontSize: 18,
          color: sizeIndex > 0 ? "var(--text-primary)" : "var(--text-secondary)",
          lineHeight: 1,
        }}
      >
        A
      </span>
    </button>
  );
}
