"use client";

import RichAnswer from "@/components/RichAnswer";

interface Props {
  answer: string;
  isStreaming: boolean;
  mode?: "text" | "voice";
}

export default function AIAnswer({ answer, isStreaming, mode = "text" }: Props) {
  if (!answer && !isStreaming) return null;

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div
        className="p-6 sm:p-8 rounded-2xl"
        style={{
          border: "1px solid var(--glass-border)",
          background: "var(--card)",
          boxShadow: "var(--shadow-strong)",
        }}
      >
        {!answer && isStreaming ? (
          <div className="flex items-center gap-3" style={{ color: "var(--text-secondary)" }}>
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
            <span className="font-serif italic">Prabhupada is contemplating...</span>
          </div>
        ) : (
          <RichAnswer text={answer} mode={mode} isStreaming={isStreaming} />
        )}
      </div>
    </div>
  );
}
