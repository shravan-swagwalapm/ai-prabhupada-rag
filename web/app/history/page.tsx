"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { fetchHistory, getAudioUrl, type HistoryEntry } from "@/lib/api";
import RichAnswer from "@/components/RichAnswer";
import AudioPlayer from "@/components/AudioPlayer";

export default function HistoryPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/auth/");
    }
  }, [isAuthenticated, authLoading, router]);

  // Fetch history
  useEffect(() => {
    if (!isAuthenticated) return;

    (async () => {
      try {
        const data = await fetchHistory(50, 0);
        setEntries(data.entries);
        setTotal(data.total);
      } catch (err) {
        // Error handled by loading state — history will show empty
      } finally {
        setIsLoading(false);
      }
    })();
  }, [isAuthenticated]);

  if (authLoading) {
    return (
      <main className="relative z-10 min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-t-transparent rounded-full" style={{ borderColor: "var(--gold)" }} />
      </main>
    );
  }

  return (
    <main className="relative z-10 min-h-screen px-4 py-8 sm:py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => router.push("/")}
            className="p-2 rounded-lg transition-colors"
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(201, 168, 76, 0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "")}
            aria-label="Back"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: "var(--gold)" }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <h1 className="text-2xl font-serif" style={{ color: "var(--text-primary)" }}>Your Questions</h1>
          <span className="text-xs font-sans ml-auto" style={{ color: "var(--text-muted)" }}>
            {total} total
          </span>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center gap-3" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-serif italic">Loading your history...</span>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-20">
            <p className="font-sans" style={{ color: "var(--text-muted)" }}>
              You haven&apos;t asked any questions yet.
            </p>
            <button
              onClick={() => router.push("/")}
              className="mt-4 px-6 py-2 rounded-full text-white font-sans text-sm transition-colors"
              style={{ backgroundColor: "var(--gold)" }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--gold-bright)")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "var(--gold)")}
            >
              Ask your first question
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => {
              const isExpanded = expandedId === entry.id;
              const date = new Date(entry.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              });

              return (
                <div
                  key={entry.id}
                  className="rounded-xl border border-[var(--glass-border)] bg-[var(--card)] overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                    className="w-full text-left p-4 flex items-start gap-3"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-serif line-clamp-2" style={{ color: "var(--text-primary)" }}>
                        {entry.question}
                      </p>
                      <p className="text-xs font-sans mt-1" style={{ color: "var(--text-muted)" }}>
                        {date} &middot; {entry.answer_mode}
                      </p>
                    </div>
                    <svg
                      className={`w-4 h-4 shrink-0 mt-1 transition-transform ${
                        isExpanded ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      style={{ color: "var(--text-muted)" }}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-5 border-t border-[var(--glass-border)]">
                      <div className="pt-4">
                        <RichAnswer
                          text={entry.answer_text}
                          mode={entry.answer_mode === "voice" ? "voice" : "text"}
                        />
                      </div>
                      {entry.audio_id && (
                        <AudioPlayer audioId={entry.audio_id} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
