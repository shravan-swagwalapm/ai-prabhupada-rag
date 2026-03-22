"use client";

import { useState, useEffect } from "react";
import type { Passage } from "@/lib/api";
import { getScriptureName, getScriptureShort, getScriptureIcon } from "@/lib/scriptures";
import { getScriptureSVGColor } from "@/lib/scriptures";

interface SourceDrawerProps {
  passages: Passage[];
  isOpen: boolean;
  onClose: () => void;
}

function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

export default function SourceDrawer({ passages, isOpen, onClose }: SourceDrawerProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Reset expanded card when drawer opens/closes
  useEffect(() => {
    if (!isOpen) setExpandedIndex(null);
  }, [isOpen]);

  const toggleAccordion = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  // Count unique scriptures
  const uniqueScriptures = new Set(passages.map((p) => p.scripture)).size;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-[100] transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.6)",
          opacity: isOpen ? 1 : 0,
          pointerEvents: isOpen ? "auto" : "none",
        }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 bottom-0 z-[101] overflow-y-auto transition-transform duration-300 ease-out"
        style={{
          width: "min(420px, 88vw)",
          background: "var(--sanctum, #0f0c08)",
          borderLeft: "1px solid var(--glass-border)",
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
          scrollbarWidth: "thin",
          scrollbarColor: "rgba(201,168,76,0.2) transparent",
          padding: "24px 20px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-11 h-11 flex items-center justify-center rounded-lg transition-colors"
          style={{ border: "1px solid var(--glass-border)", color: "var(--text-muted)" }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--glass-border-hover)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; }}
          aria-label="Close sources drawer"
        >
          ✕
        </button>

        {/* Header */}
        <p className="text-sm font-serif" style={{ color: "var(--gold)", letterSpacing: "0.06em" }}>
          All Sources
        </p>
        <p className="text-[11px] font-sans mb-5" style={{ color: "var(--text-muted)" }}>
          {passages.length} passages from {uniqueScriptures} scripture{uniqueScriptures !== 1 ? "s" : ""}
        </p>

        {/* Accordion cards */}
        <div className="space-y-2.5">
          {passages.map((p, i) => {
            const isExpanded = expandedIndex === i;
            const shortName = getScriptureShort(p.scripture);
            const fullName = getScriptureName(p.scripture, p.chunk_id);
            const icon = getScriptureIcon(p.scripture);
            const svgColor = getScriptureSVGColor(p.scripture);
            const matchPct = (p.similarity || 0.5) * 100;
            const relevanceColor = getRelevanceColor(matchPct);

            return (
              <div
                key={`${p.scripture}-${p.chunk_id || i}`}
                className="rounded-xl overflow-hidden transition-colors"
                style={{
                  border: `1px solid ${isExpanded ? "var(--glass-border-hover)" : "var(--glass-border)"}`,
                  background: "var(--card)",
                }}
              >
                {/* Header — always visible */}
                <button
                  onClick={() => toggleAccordion(i)}
                  className="w-full text-left px-4 py-3.5 flex items-center justify-between"
                  aria-expanded={isExpanded}
                  aria-controls={`drawer-passage-${i}`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-base shrink-0">{icon}</span>
                    <div className="min-w-0">
                      <span
                        className="inline-block px-2 py-0.5 rounded-md text-[11px] font-sans font-medium"
                        style={{
                          color: svgColor.text,
                          background: svgColor.fill,
                          border: `1px solid ${svgColor.stroke}`,
                        }}
                      >
                        {shortName}
                      </span>
                      {fullName !== shortName && (
                        <p className="text-[10px] font-sans mt-1 truncate" style={{ color: "var(--text-muted)" }}>
                          {fullName.substring(fullName.indexOf(",") + 2)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-sans font-semibold" style={{ color: "var(--gold-dim)" }}>
                      {matchPct.toFixed(0)}%
                    </span>
                    <span
                      className="text-[10px] transition-transform duration-200"
                      style={{
                        color: "var(--text-muted)",
                        transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                      }}
                    >
                      ▼
                    </span>
                  </div>
                </button>

                {/* Body — expandable */}
                <div
                  id={`drawer-passage-${i}`}
                  className="overflow-hidden transition-all duration-300 ease-out"
                  style={{ maxHeight: isExpanded ? "500px" : "0" }}
                >
                  <div className="px-4 pb-4" style={{ borderTop: "1px solid var(--glass-border)" }}>
                    {/* Relevance bar */}
                    <div className="flex items-center gap-2 py-2.5">
                      <div className="w-14 h-1 rounded-full overflow-hidden" style={{ background: "rgba(201,168,76,0.1)" }}>
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(100, matchPct)}%`,
                            background: `linear-gradient(to right, var(--vermillion), ${relevanceColor})`,
                          }}
                        />
                      </div>
                      <span className="text-[10px] font-sans font-semibold" style={{ color: relevanceColor }}>
                        {matchPct.toFixed(0)}% relevance
                      </span>
                    </div>

                    {/* Full passage text */}
                    <p className="font-serif text-[13px]" style={{ lineHeight: "1.8", color: "var(--text-body)" }}>
                      {p.text}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
