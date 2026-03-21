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
    <div className="flex items-center gap-3 text-xs font-display tracking-wide">
      <span
        style={{
          color: textExhausted ? "var(--vermillion)" : "var(--tulsi)",
        }}
      >
        {textQuota} of {textMax} questions
      </span>
      <span style={{ color: "var(--text-ghost)" }}>·</span>
      <span
        style={{
          color: voiceExhausted ? "var(--vermillion)" : "var(--tulsi)",
        }}
      >
        {voiceQuota} of {voiceMax} voice
      </span>
    </div>
  );
}
