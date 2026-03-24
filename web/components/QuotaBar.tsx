"use client";

interface Props {
  textQuota: number;
  voiceQuota: number;
  textMax?: number;
  voiceMax?: number;
}

export default function QuotaBar({
  textQuota,
  voiceQuota,
  textMax = 5,
  voiceMax = 2,
}: Props) {
  const textExhausted = textQuota <= 0;
  const voiceExhausted = voiceQuota <= 0;

  return (
    <div className="flex items-center gap-1.5 text-xs font-sans font-medium whitespace-nowrap">
      <span
        style={{
          color: textExhausted ? "var(--vermillion)" : "var(--tulsi)",
        }}
      >
        {textQuota}/{textMax}
      </span>
      <span style={{ color: "var(--text-ghost)" }}>·</span>
      <span
        style={{
          color: voiceExhausted ? "var(--vermillion)" : "var(--tulsi)",
        }}
      >
        {voiceQuota}/{voiceMax}
        <svg className="inline-block w-3 h-3 ml-0.5 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4M12 15a3 3 0 003-3V5a3 3 0 00-6 0v7a3 3 0 003 3z" />
        </svg>
      </span>
    </div>
  );
}
