"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import QuestionInput from "@/components/QuestionInput";
import AnswerTabs from "@/components/AnswerTabs";
import QuotaBar from "@/components/QuotaBar";
import SubscribeGate from "@/components/SubscribeGate";
import ShareBar from "@/components/ShareBar";
import LotusWatermark from "@/components/LotusWatermark";
import WarmSkeleton from "@/components/WarmSkeleton";
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
      {/* Frosted glass header */}
      <header
        className="sticky top-0 z-50 w-full mb-8 sm:mb-12"
        style={{
          background: "rgba(250,246,239,0.85)",
          borderBottom: "1px solid var(--glass-border-hover)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
        }}
      >
        <div className="max-w-3xl mx-auto flex items-center justify-between px-5 py-3">
        {/* Logo / brand */}
        <div className="flex items-center gap-3">
          <div
            className="w-[38px] h-[38px] flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, #1A3A6B, #2A5298)",
              borderRadius: 12,
            }}
          >
            <span className="text-base">🙏</span>
          </div>
          <span
            className="text-lg font-bold font-serif"
            style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
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
            href="/history/"
            className="flex items-center justify-center transition-all"
            style={{
              background: "rgba(255,255,255,0.65)",
              border: "1px solid var(--glass-border-hover)",
              borderRadius: 10,
              minHeight: 44,
              minWidth: 44,
              color: "var(--text-secondary)",
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
            style={{ minHeight: 44, minWidth: 44, display: "flex", alignItems: "center", justifyContent: "center" }}
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
                  background: "linear-gradient(135deg, #1A3A6B, #2A5298)",
                  border: "2px solid var(--glass-border-hover)",
                }}
              >
                <span className="text-sm font-sans font-semibold" style={{ color: "#FAF6EF" }}>
                  {user?.name?.charAt(0)?.toUpperCase() || "?"}
                </span>
              </div>
            )}
          </button>
        </div>
        </div>
      </header>

      {/* Greeting */}
      <div className="relative text-center mb-10">
        {/* Arati glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "radial-gradient(ellipse 60% 40% at 50% 50%, rgba(201,168,76,0.08) 0%, transparent 70%)",
          }}
        />
        <LotusWatermark />
        <h1
          className="relative text-3xl sm:text-4xl font-serif font-bold leading-tight"
          style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
        >
          Hare Krishna{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.
        </h1>
        <p
          className="relative mt-3 text-lg font-sans max-w-md mx-auto"
          style={{ color: "var(--text-secondary)", fontWeight: 450, lineHeight: 1.75 }}
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

      {/* Text / Voice mode toggle — iOS segmented control */}
      <div className="mt-5 flex items-center justify-center">
        <div
          className="flex gap-1"
          style={{
            border: "1px solid var(--glass-border)",
            borderRadius: 14,
            background: "#FAF6EF",
            padding: "4px",
          }}
        >
          <button
            type="button"
            onClick={() => setVoiceEnabled(false)}
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
              className="ml-2 text-xs"
              style={{ color: !voiceEnabled ? "var(--text-secondary)" : "var(--text-ghost)" }}
            >
              {user?.text_quota ?? 0}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setVoiceEnabled(true)}
            className="flex items-center gap-2 px-5 py-2 text-sm font-sans font-semibold transition-all duration-200"
            style={{
              background: voiceEnabled ? "#FFFFFF" : "transparent",
              color: voiceEnabled ? "var(--text-primary)" : "var(--text-secondary)",
              boxShadow: voiceEnabled ? "0 1px 4px rgba(26,58,107,0.08)" : "none",
              borderRadius: 10,
              minHeight: 44,
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
            color: "var(--text-body)",
          }}
        >
          {streamError}
        </div>
      )}

      {/* Searching skeleton */}
      {isSearching && (
        <div className="w-full max-w-3xl mx-auto mt-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="relative w-4 h-4">
              <span
                className="absolute inset-0 rounded-full animate-ping"
                style={{ background: "rgba(26,58,107,0.2)" }}
              />
              <span
                className="relative block w-4 h-4 rounded-full"
                style={{ background: "rgba(26,58,107,0.4)" }}
              />
            </div>
            <span className="text-sm font-sans" style={{ color: "var(--text-secondary)" }}>
              Searching 14 sacred texts...
            </span>
          </div>
          <WarmSkeleton />
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
        question={currentQuestion}
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
        className="mt-auto pt-16 pb-6 text-center font-sans"
        style={{ color: "var(--text-ghost)", fontSize: "11px", letterSpacing: "0.04em" }}
      >
        Powered by FAISS + Claude Sonnet 4.5 + ElevenLabs
      </footer>
    </main>
  );
}
