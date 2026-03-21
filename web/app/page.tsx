"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import QuestionInput from "@/components/QuestionInput";
import AnswerTabs from "@/components/AnswerTabs";
import QuotaBar from "@/components/QuotaBar";
import SubscribeGate from "@/components/SubscribeGate";
import ShareBar from "@/components/ShareBar";
import { queryStream, type Passage } from "@/lib/api";

export default function Home() {
  const { user, isAuthenticated, isLoading: authLoading, refreshUser, logout } = useAuth();
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const [passages, setPassages] = useState<Passage[]>([]);
  const [answer, setAnswer] = useState("");
  const [audioId, setAudioId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState("");

  // Subscribe gate state
  const [showQuotaWall, setShowQuotaWall] = useState(false);
  const [quotaWallType, setQuotaWallType] = useState<"text" | "voice">("text");

  const cleanupStreamRef = useRef<(() => void) | null>(null);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/auth/");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = useCallback(
    (question: string) => {
      // Cancel any in-flight stream
      if (cleanupStreamRef.current) {
        cleanupStreamRef.current();
        cleanupStreamRef.current = null;
      }

      // Reset state
      setIsLoading(true);
      setIsSearching(true);
      setIsStreaming(false);
      setStreamError(null);
      setPassages([]);
      setAnswer("");
      setAudioId(null);
      setCurrentQuestion(question);

      const cleanup = queryStream(
        question,
        {
          onPassages: (p) => {
            setPassages(p);
            setIsSearching(false);
            setIsStreaming(true);
          },
          onAnswerChunk: (chunk) => {
            setAnswer((prev) => prev + chunk);
          },
          onAudioId: (id) => {
            setAudioId(id);
          },
          onDone: () => {
            setIsLoading(false);
            setIsStreaming(false);
            cleanupStreamRef.current = null;
            // Refresh user to get updated quota counts
            refreshUser();
          },
          onError: (err) => {
            setStreamError(err);
            setIsLoading(false);
            setIsSearching(false);
            setIsStreaming(false);
            cleanupStreamRef.current = null;
          },
          onQuotaExhausted: (quotaType) => {
            setIsLoading(false);
            setIsSearching(false);
            setQuotaWallType((quotaType === "voice" ? "voice" : "text") as "text" | "voice");
            setShowQuotaWall(true);
          },
          onNoMatch: (message: string) => {
            setAnswer(message);
            setPassages([]);
            setIsStreaming(false);
          },
        },
        { includeVoice: voiceEnabled }
      );

      cleanupStreamRef.current = cleanup;
    },
    [voiceEnabled, refreshUser]
  );

  // Show loading spinner while checking auth
  if (authLoading) {
    return (
      <main
        className="relative z-10 min-h-screen flex items-center justify-center"
        style={{ background: "var(--sanctum)" }}
      >
        <div
          className="animate-spin w-8 h-8 rounded-full border-2 border-t-transparent"
          style={{ borderColor: "var(--gold)", borderTopColor: "transparent" }}
        />
      </main>
    );
  }

  // Check if quota is fully exhausted for disabling input
  const textExhausted = (user?.text_quota ?? 0) <= 0;
  const voiceExhausted = (user?.voice_quota ?? 0) <= 0;
  const currentModeExhausted = voiceEnabled ? voiceExhausted : textExhausted;

  return (
    <main
      className="relative z-10 min-h-screen flex flex-col items-center px-4 py-8 sm:py-12"
      style={{ background: "var(--sanctum)" }}
    >
      {/* Glass header */}
      <div
        className="w-full max-w-3xl mx-auto flex items-center justify-between mb-8 sm:mb-12 px-5 py-3 rounded-2xl"
        style={{
          background: "var(--glass)",
          border: "1px solid var(--glass-border)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
        }}
      >
        {/* Logo / brand */}
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.08))",
              border: "1px solid var(--glass-border-hover)",
            }}
          >
            <span className="text-base">🙏</span>
          </div>
          <span
            className="text-lg font-serif tracking-wide"
            style={{ color: "var(--text-primary)" }}
          >
            AI Prabhupada
          </span>
        </div>

        {/* Right side: quota + history + avatar */}
        <div className="flex items-center gap-3">
          {user && (
            <QuotaBar
              textQuota={user.text_quota}
              voiceQuota={user.voice_quota}
            />
          )}
          <a
            href="/history"
            className="p-2.5 rounded-xl transition-all min-h-[44px] min-w-[44px] flex items-center justify-center"
            style={{
              border: "1px solid transparent",
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = "rgba(201,168,76,0.06)";
              (e.currentTarget as HTMLElement).style.borderColor = "var(--glass-border-hover)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
              (e.currentTarget as HTMLElement).style.borderColor = "transparent";
            }}
            aria-label="History"
            title="Your questions"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </a>
          <button
            onClick={logout}
            className="rounded-full cursor-pointer transition-opacity hover:opacity-80"
            aria-label="Sign out"
            title="Sign out"
          >
            {user?.photo_url ? (
              <img
                src={user.photo_url}
                alt={user.name}
                className="w-9 h-9 rounded-full shadow-sm"
                style={{ border: "2px solid var(--glass-border-hover)" }}
              />
            ) : (
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center"
                style={{
                  background: "linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.08))",
                  border: "2px solid var(--glass-border-hover)",
                }}
              >
                <span className="text-sm font-sans font-semibold" style={{ color: "var(--text-primary)" }}>
                  {user?.name?.charAt(0)?.toUpperCase() || "?"}
                </span>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Greeting */}
      <div className="text-center mb-10">
        <h1
          className="text-3xl sm:text-4xl font-serif font-semibold tracking-wide leading-tight"
          style={{ color: "var(--text-primary)" }}
        >
          Hare Krishna{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.
        </h1>
        <p
          className="mt-3 text-base font-sans max-w-md mx-auto"
          style={{ color: "var(--text-secondary)" }}
        >
          What would you like to ask Srila Prabhupada?
        </p>
      </div>

      {/* Search input */}
      <QuestionInput
        onSubmit={handleSubmit}
        isLoading={isLoading}
        disabled={currentModeExhausted}
        voiceQuotaExhausted={voiceExhausted}
      />

      {/* Text / Voice mode toggle */}
      <div className="mt-5 flex items-center justify-center">
        <div
          className="flex gap-1 p-1.5 rounded-full"
          style={{
            background: "var(--card)",
            border: "1px solid var(--glass-border)",
          }}
        >
          <button
            type="button"
            onClick={() => setVoiceEnabled(false)}
            className="px-5 py-2 rounded-full text-sm font-sans font-semibold transition-all duration-200 min-h-[44px]"
            style={{
              background: !voiceEnabled ? "rgba(201,168,76,0.15)" : "transparent",
              color: !voiceEnabled ? "var(--text-primary)" : "var(--text-muted)",
              border: !voiceEnabled ? "1px solid var(--glass-border-hover)" : "1px solid transparent",
              boxShadow: !voiceEnabled ? "0 2px 8px rgba(0,0,0,0.2)" : "none",
            }}
          >
            Text
            <span
              className="ml-2 text-xs"
              style={{ color: !voiceEnabled ? "var(--text-secondary)" : "var(--text-ghost)" }}
            >
              {user?.text_quota ?? 0}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setVoiceEnabled(true)}
            className="flex items-center gap-2 px-5 py-2 rounded-full text-sm font-sans font-semibold transition-all duration-200 min-h-[44px]"
            style={{
              background: voiceEnabled ? "rgba(201,168,76,0.15)" : "transparent",
              color: voiceEnabled ? "var(--text-primary)" : "var(--text-muted)",
              border: voiceEnabled ? "1px solid var(--glass-border-hover)" : "1px solid transparent",
              boxShadow: voiceEnabled ? "0 2px 8px rgba(0,0,0,0.2)" : "none",
            }}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4M12 15a3 3 0 003-3V5a3 3 0 00-6 0v7a3 3 0 003 3z" />
            </svg>
            Voice
            <span
              className="text-xs"
              style={{ color: voiceEnabled ? "var(--text-secondary)" : "var(--text-ghost)" }}
            >
              {user?.voice_quota ?? 0}
            </span>
          </button>
        </div>
      </div>

      {/* Error banner */}
      {streamError && (
        <div
          className="w-full max-w-3xl mx-auto mt-4 px-4 py-3 rounded-lg text-sm font-sans"
          style={{
            background: "rgba(194,77,44,0.1)",
            border: "1px solid rgba(194,77,44,0.3)",
            color: "var(--vermillion-bright)",
          }}
        >
          {streamError}
        </div>
      )}

      {/* Results with tabs */}
      <AnswerTabs
        passages={passages}
        answer={answer}
        isStreaming={isStreaming}
        audioId={audioId}
        voiceEnabled={voiceEnabled}
        isSearching={isSearching}
      />

      {/* ShareBar — only show when answer is complete */}
      {answer && !isStreaming && (
        <div
          className="w-full max-w-3xl mx-auto mt-2 rounded-xl overflow-hidden"
          style={{
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
          }}
        >
          <ShareBar answerText={answer} question={currentQuestion} />
        </div>
      )}

      {/* Subscribe Gate Modal */}
      {showQuotaWall && (
        <SubscribeGate
          quotaType={quotaWallType}
          userEmail={user?.email ?? ""}
          textUsed={5 - (user?.text_quota ?? 0)}
          voiceUsed={2 - (user?.voice_quota ?? 0)}
          onSubmit={() => setShowQuotaWall(false)}
          onDismiss={() => setShowQuotaWall(false)}
        />
      )}

      {/* Footer */}
      <footer
        className="mt-auto pt-16 pb-6 text-center text-xs font-sans tracking-wide"
        style={{ color: "var(--text-ghost)" }}
      >
        Powered by FAISS + Claude Sonnet 4.5 + ElevenLabs
      </footer>
    </main>
  );
}
