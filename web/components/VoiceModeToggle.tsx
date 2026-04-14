"use client";

interface Props {
  voiceEnabled: boolean;
  onToggle: (enabled: boolean) => void;
  disabled?: boolean;
  textQuota: number;
  voiceQuota: number;
  voiceQuotaExhausted?: boolean;
}

export default function VoiceModeToggle({
  voiceEnabled,
  onToggle,
  disabled = false,
  textQuota,
  voiceQuota,
  voiceQuotaExhausted = false,
}: Props) {
  return (
    <div
      className="w-full max-w-3xl mx-auto mt-5 flex flex-col items-center gap-2.5"
      style={{
        opacity: disabled ? 0.5 : 1,
        transition: "opacity 0.2s ease",
      }}
    >
      {/* Teaser label — only visible when Voice mode is selected */}
      {voiceEnabled && (
        <span
          id="voice-mode-label"
          className="text-sm font-serif"
          style={{
            color: "var(--gold-dim)",
            letterSpacing: "0.02em",
            fontStyle: "italic",
          }}
        >
          Hear Prabhupada&apos;s voice
        </span>
      )}

      {/* Segmented control */}
      <div
        role="radiogroup"
        aria-labelledby={voiceEnabled ? "voice-mode-label" : undefined}
        aria-label={!voiceEnabled ? "Answer mode" : undefined}
        className="flex gap-1"
        style={{
          border: "1px solid var(--glass-border)",
          borderRadius: 14,
          background: "var(--sanctum)",
          padding: "4px",
        }}
      >
        <button
          type="button"
          onClick={() => onToggle(false)}
          role="radio"
          aria-checked={!voiceEnabled}
          disabled={disabled}
          className="px-5 py-2 text-sm font-sans font-semibold transition-all duration-200"
          style={{
            background: !voiceEnabled ? "#FFFFFF" : "transparent",
            color: !voiceEnabled ? "var(--text-primary)" : "var(--text-secondary)",
            boxShadow: !voiceEnabled ? "0 1px 4px rgba(26,58,107,0.08)" : "none",
            borderRadius: 10,
            minHeight: 44,
          }}
        >
          Text
          <span
            className="ml-2 text-sm"
            style={{ color: !voiceEnabled ? "var(--text-secondary)" : "var(--text-ghost)" }}
          >
            {textQuota}
          </span>
        </button>
        <button
          type="button"
          onClick={() => onToggle(true)}
          role="radio"
          aria-checked={voiceEnabled}
          disabled={disabled || voiceQuotaExhausted}
          className="flex items-center gap-2 px-5 py-2 text-sm font-sans font-semibold transition-all duration-200"
          style={{
            background: voiceEnabled ? "#FFFFFF" : "transparent",
            color: voiceEnabled ? "var(--text-primary)" : "var(--text-secondary)",
            boxShadow: voiceEnabled ? "0 1px 4px rgba(26,58,107,0.08)" : "none",
            borderRadius: 10,
            minHeight: 44,
            opacity: voiceQuotaExhausted ? 0.4 : 1,
            cursor: voiceQuotaExhausted ? "not-allowed" : "pointer",
          }}
        >
          {/* Speaker icon with sound waves */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 5L6 9H2v6h4l5 4V5z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.54 8.46a5 5 0 010 7.07"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19.07 4.93a10 10 0 010 14.14"
            />
          </svg>
          Voice
          <span
            className="text-sm"
            style={{ color: voiceEnabled ? "var(--text-secondary)" : "var(--text-ghost)" }}
          >
            {voiceQuota}
          </span>
        </button>
      </div>
    </div>
  );
}
