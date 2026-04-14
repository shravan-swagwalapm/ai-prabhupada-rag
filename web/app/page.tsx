"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import QuestionInput from "@/components/QuestionInput";
import AnswerTabs from "@/components/AnswerTabs";
import AudioPlayer from "@/components/AudioPlayer";
import VoiceModeToggle from "@/components/VoiceModeToggle";
import FontSizeToggle from "@/components/FontSizeToggle";
import SubscribeGate from "@/components/SubscribeGate";
import ShareBar from "@/components/ShareBar";
import LotusWatermark from "@/components/LotusWatermark";
import WarmSkeleton from "@/components/WarmSkeleton";
import { queryStream, type Passage } from "@/lib/api";

// Must match api/database.py DEFAULT_TEXT_QUOTA / DEFAULT_VOICE_QUOTA
const DEFAULT_TEXT_QUOTA = 5;
const DEFAULT_VOICE_QUOTA = 2;

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
  /** Pre-created Audio element from user gesture — preserves mobile auto-play context. */
  const gestureAudioRef = useRef<HTMLAudioElement | null>(null);

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

      // Clean up previous gesture Audio before creating a new one
      if (gestureAudioRef.current) {
        gestureAudioRef.current.pause();
        gestureAudioRef.current.src = "";
      }
      // Create silent Audio element during user gesture to preserve mobile auto-play context.
      // Browsers allow audio.play() later if the Audio was created in a user-initiated event handler.
      gestureAudioRef.current = voiceEnabled ? new Audio() : null;

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
            setIsLoading(false);
            setIsSearching(false);
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
        <div className="flex items-center gap-2.5">
          <picture>
            <source srcSet="/prabhupada-walking.webp" type="image/webp" />
            <img
              src="/prabhupada-walking.png"
              alt="Prabhupada AI"
              className="shrink-0"
              width={24}
              height={38}
              style={{ height: 38, width: "auto", objectFit: "contain" }}
            />
          </picture>
          <span
            className="text-lg font-bold font-serif"
            style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
          >
            Prabhupada AI
          </span>
        </div>

        {/* Right side: font size + history + avatar */}
        <div className="flex items-center gap-2">
          <FontSizeToggle />
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
                  background: "linear-gradient(135deg, var(--krishna-blue), var(--krishna-blue-light))",
                  border: "2px solid var(--glass-border-hover)",
                }}
              >
                <span className="text-sm font-sans font-semibold" style={{ color: "var(--sanctum)" }}>
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
          Hare Krsna{user?.name ? `, ${user.name.split(" ")[0].charAt(0).toUpperCase()}${user.name.split(" ")[0].slice(1)}` : ""}.
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

      {/* Text / Voice mode toggle */}
      <VoiceModeToggle
        voiceEnabled={voiceEnabled}
        onToggle={setVoiceEnabled}
        disabled={isStreaming}
        textQuota={user?.text_quota ?? 0}
        voiceQuota={user?.voice_quota ?? 0}
        voiceQuotaExhausted={voiceExhausted}
      />

      {/* Error banner */}
      {streamError && (
        <div
          className="w-full max-w-3xl mx-auto mt-4 px-4 py-3 rounded-lg text-sm font-sans flex items-center justify-between gap-3"
          style={{
            background: "rgba(194,77,44,0.1)",
            border: "1px solid rgba(194,77,44,0.3)",
            color: "var(--text-body)",
          }}
        >
          <span>{streamError}</span>
          <button
            onClick={() => setStreamError(null)}
            className="shrink-0 w-6 h-6 flex items-center justify-center rounded-full transition-colors"
            style={{ color: "var(--text-muted)" }}
            aria-label="Dismiss error"
          >
            ✕
          </button>
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

      {/* Audio player — above answer, only when voice mode produced audio */}
      {voiceEnabled && <AudioPlayer audioId={audioId} gestureAudio={gestureAudioRef.current} />}

      {/* Results with tabs */}
      <AnswerTabs
        passages={passages}
        answer={answer}
        isStreaming={isStreaming}
        isSearching={isSearching}
        question={currentQuestion}
        voiceEnabled={voiceEnabled}
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
          textUsed={DEFAULT_TEXT_QUOTA - (user?.text_quota ?? 0)}
          voiceUsed={DEFAULT_VOICE_QUOTA - (user?.voice_quota ?? 0)}
          onSubmit={() => setShowQuotaWall(false)}
          onDismiss={() => setShowQuotaWall(false)}
        />
      )}

      {/* Footer */}
      <footer
        className="mt-auto pt-16 pb-6 text-center font-sans"
        style={{ color: "var(--text-muted)", fontSize: "14px", letterSpacing: "0.04em" }}
      >
        Powered by FAISS + Claude Sonnet 4.5 + ElevenLabs
      </footer>
    </main>
  );
}
