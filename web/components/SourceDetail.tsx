"use client";

import type { Passage } from "@/lib/api";
import { getScriptureName, getScriptureIcon } from "@/lib/scriptures";

interface SourceDetailProps {
  passage: Passage | null;
  onClose: () => void;
}

function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

export default function SourceDetail({ passage, onClose }: SourceDetailProps) {
  if (!passage) return null;

  const fullName = getScriptureName(passage.scripture, passage.chunk_id);
  const icon = getScriptureIcon(passage.scripture);
  const matchPct = (passage.similarity || 0.5) * 100;
  const relevanceColor = getRelevanceColor(matchPct);

  return (
    <div
      className="w-full mt-4 rounded-xl overflow-hidden"
      style={{
        border: "1px solid var(--glass-border)",
        background: "var(--card)",
        animation: "fadeInUp 0.3s ease-out",
      }}
    >
      <div className="max-h-[450px] overflow-y-auto" style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(201,168,76,0.2) transparent" }}>
        {/* Sticky header */}
        <div
          className="flex items-center justify-between px-5 py-4 sticky top-0 z-10"
          style={{
            borderBottom: "1px solid var(--glass-border)",
            background: "var(--card)",
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-lg shrink-0">{icon}</span>
            <div className="min-w-0">
              <p className="text-sm font-serif font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                {fullName.split(",")[0]}
              </p>
              {fullName.includes(",") && (
                <p className="text-xs font-sans truncate" style={{ color: "var(--text-muted)" }}>
                  {fullName.substring(fullName.indexOf(",") + 2)}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-11 h-11 min-w-[44px] flex items-center justify-center rounded-lg transition-colors"
            style={{ border: "1px solid var(--glass-border)", color: "var(--text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--glass-border-hover)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; e.currentTarget.style.color = "var(--text-muted)"; }}
            aria-label="Close source detail"
          >
            ✕
          </button>
        </div>

        {/* Relevance bar */}
        <div className="flex items-center gap-2 px-5 py-2">
          <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: "rgba(201,168,76,0.1)" }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(100, matchPct)}%`,
                background: `linear-gradient(to right, var(--vermillion), ${relevanceColor})`,
              }}
            />
          </div>
          <span className="text-xs font-sans font-semibold" style={{ color: relevanceColor }}>
            {matchPct.toFixed(0)}%
          </span>
        </div>

        {/* Full passage text — no truncation */}
        <div className="px-5 pb-6">
          <p className="font-serif" style={{ fontSize: 16, lineHeight: "1.75", color: "var(--text-body)" }}>
            {passage.text}
          </p>
        </div>
      </div>
    </div>
  );
}
