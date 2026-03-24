"use client";

interface Props {
  lines?: number;
  showVerse?: boolean;
}

const LINE_WIDTHS = ["100%", "88%", "75%", "55%"];

export default function WarmSkeleton({ lines = 4, showVerse = true }: Props) {
  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      {/* Answer skeleton */}
      <div
        className="rounded-xl p-6"
        style={{
          border: "1px solid #C4B89C",
          background: "var(--bg-card-gradient)",
          boxShadow: "0 2px 8px rgba(26,58,107,0.06), 0 1px 3px rgba(0,0,0,0.04)",
        }}
      >
        <div className="space-y-3">
          {Array.from({ length: lines }).map((_, i) => (
            <div
              key={i}
              className="warm-skeleton"
              style={{
                height: 13,
                width: LINE_WIDTHS[i % LINE_WIDTHS.length],
              }}
            />
          ))}
        </div>

        {/* Verse skeleton */}
        {showVerse && (
          <div
            className="mt-6 rounded-r-xl p-4"
            style={{
              borderLeft: "3px solid #EDE6D8",
              background: "rgba(201,168,76,0.02)",
            }}
          >
            <div className="space-y-2">
              <div className="warm-skeleton" style={{ height: 13, width: "70%" }} />
              <div className="warm-skeleton" style={{ height: 13, width: "55%" }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
