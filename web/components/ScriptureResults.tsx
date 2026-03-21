"use client";

import type { Passage } from "@/lib/api";
import {
  getScriptureName,
  getScriptureShort,
  getScriptureIcon,
  getScriptureColor,
} from "@/lib/scriptures";

interface Props {
  passages: Passage[];
  isLoading: boolean;
}

function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

export default function ScriptureResults({ passages, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="w-full max-w-3xl mx-auto">
        <div className="flex items-center gap-3 py-8" style={{ color: "var(--text-secondary)" }}>
          <div className="relative w-5 h-5">
            <span
              className="absolute inset-0 rounded-full animate-ping"
              style={{ background: "rgba(201,168,76,0.3)" }}
            />
            <span
              className="relative block w-5 h-5 rounded-full"
              style={{ background: "rgba(201,168,76,0.6)" }}
            />
          </div>
          <span className="font-serif italic">Searching 13 sacred texts...</span>
        </div>
      </div>
    );
  }

  if (passages.length === 0) return null;

  // Calculate top relevance for header
  const topRelevance = Math.max(...passages.map((p) => p.similarity * 100));

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Section header */}
      <p
        className="text-xs font-sans font-medium mb-4 tracking-wider uppercase"
        style={{ color: "var(--text-muted)" }}
      >
        Sources ({passages.length}) — Top relevance:{" "}
        <span style={{ color: getRelevanceColor(topRelevance) }}>
          {topRelevance.toFixed(1)}%
        </span>
      </p>

      <div className="space-y-4">
        {passages.map((p, i) => {
          const fullName = getScriptureName(p.scripture, p.chunk_id);
          const shortName = getScriptureShort(p.scripture);
          const icon = getScriptureIcon(p.scripture);
          const colorClass = getScriptureColor(p.scripture);
          const matchPct = p.similarity * 100;
          const matchPercent = matchPct.toFixed(0);
          const relevanceColor = getRelevanceColor(matchPct);

          return (
            <div
              key={`${p.scripture}-${p.chunk_id || i}`}
              className="group p-5 rounded-xl transition-all duration-200"
              style={{
                border: "1px solid var(--glass-border)",
                background: "var(--card)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.borderColor = "var(--glass-border-hover)";
                (e.currentTarget as HTMLElement).style.background = "var(--card-hover)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.borderColor = "var(--glass-border)";
                (e.currentTarget as HTMLElement).style.background = "var(--card)";
              }}
            >
              {/* Header row */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-lg shrink-0">{icon}</span>
                  <div className="min-w-0">
                    <span className={`inline-block px-2.5 py-0.5 rounded-md text-xs font-sans font-medium border ${colorClass}`}>
                      {shortName}
                    </span>
                    {fullName !== shortName && (
                      <p className="text-[11px] font-sans mt-1 truncate" style={{ color: "var(--text-muted)" }}>
                        {fullName}
                      </p>
                    )}
                  </div>
                </div>

                {/* Relevance percentage — color-coded */}
                <div className="flex items-center gap-1.5 shrink-0">
                  <div
                    className="w-12 h-1.5 rounded-full overflow-hidden"
                    style={{ background: "rgba(201,168,76,0.1)" }}
                  >
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, Number(matchPercent))}%`,
                        background: `linear-gradient(to right, var(--vermillion), ${relevanceColor})`,
                      }}
                    />
                  </div>
                  <span
                    className="text-[10px] font-sans font-semibold w-7 text-right"
                    style={{ color: relevanceColor }}
                  >
                    {matchPercent}%
                  </span>
                </div>
              </div>

              {/* Scripture text */}
              <p
                className="font-serif text-sm leading-[1.75]"
                style={{ color: "var(--text-body)" }}
              >
                {p.text.length > 500 ? p.text.slice(0, 500) + "..." : p.text}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
