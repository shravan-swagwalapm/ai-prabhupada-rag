"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { initGoogleSignIn } from "@/lib/auth";
import AratiDivider from "@/components/AratiDivider";

// ─── Scripture Data ──────────────────────────────────────────────────────────

const SCRIPTURES = [
  { code: "BG", name: "Bhagavad-gita As It Is", count: "6,292" },
  { code: "SB", name: "Srimad-Bhagavatam", count: "93,645" },
  { code: "CC", name: "Caitanya-caritamrta", count: "26,600" },
  { code: "TLC", name: "Teachings of Lord Caitanya", count: "2,629" },
  { code: "KB", name: "Krishna Book", count: "7,009" },
  { code: "NOD", name: "Nectar of Devotion", count: "3,552" },
  { code: "TLK", name: "Teachings of Lord Kapila", count: "1,750" },
  { code: "TQK", name: "Teachings of Queen Kunti", count: "1,538" },
  { code: "POP", name: "Perfection of Yoga", count: "1,013" },
  { code: "ISO", name: "Sri Isopanisad", count: "370" },
  { code: "LOB", name: "Light of Bhagavata", count: "354" },
  { code: "NOI", name: "Nectar of Instruction", count: "303" },
  { code: "Letters", name: "Prabhupada\u2019s Letters", count: "12,090" },
  { code: "Talks", name: "Recorded Conversations", count: "4,348" },
];

const EXAMPLE_QUESTIONS = [
  "What happens to the soul after death?",
  "How do I deal with anxiety and stress at work?",
  "How can I start practicing bhakti yoga in daily life?",
  "What does Krishna say about balancing family and spiritual life?",
];

// ─── Component ───────────────────────────────────────────────────────────────

export default function AuthPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();
  const gsiInitialized = useRef(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isLoading || isAuthenticated || gsiInitialized.current) return;
    gsiInitialized.current = true;
    initGoogleSignIn("google-signin-btn", () => {
      window.location.href = "/";
    });
    // Also init the bottom CTA button
    initGoogleSignIn("google-signin-btn-bottom", () => {
      window.location.href = "/";
    });
  }, [isLoading, isAuthenticated]);

  if (isLoading) {
    return (
      <main
        className="relative z-10 min-h-screen flex items-center justify-center"
        style={{ background: "var(--sanctum)" }}
      >
        <div
          className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: "var(--gold) transparent var(--gold) var(--gold)" }}
        />
      </main>
    );
  }

  return (
    <main className="relative z-10" style={{ background: "var(--sanctum)" }}>
      {/* ── Section 1: Hero ────────────────────────────────────────── */}
      <section className="min-h-screen flex flex-col items-center justify-center px-4 py-12 relative">
        {/* Background glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(201,168,76,0.04) 0%, transparent 70%)",
          }}
        />

        {/* Pulsing rings */}
        <div className="relative flex items-center justify-center mb-8">
          <div
            className="absolute rounded-full"
            style={{
              width: 120, height: 120,
              border: "1px solid rgba(201,168,76,0.15)",
              animation: "pulse-ring 3s ease-in-out infinite",
              animationDelay: "0.6s",
            }}
          />
          <div
            className="absolute rounded-full"
            style={{
              width: 88, height: 88,
              border: "1px solid rgba(201,168,76,0.25)",
              animation: "pulse-ring 3s ease-in-out infinite",
              animationDelay: "0.3s",
            }}
          />
          <div
            className="absolute rounded-full"
            style={{
              width: 60, height: 60,
              border: "1px solid rgba(201,168,76,0.4)",
              animation: "pulse-ring 3s ease-in-out infinite",
            }}
          />
          <div
            className="relative w-5 h-5 rounded-full"
            style={{
              background: "radial-gradient(circle, var(--gold-bright) 0%, var(--gold-dim) 100%)",
              boxShadow: "0 0 12px rgba(201,168,76,0.5)",
            }}
          />
        </div>

        {/* Title */}
        <h1
          className="font-serif font-semibold text-4xl sm:text-5xl text-center tracking-wide leading-tight"
          style={{ color: "var(--text-primary)" }}
        >
          Hare Kṛṣṇa
        </h1>

        <AratiDivider />

        {/* Tagline */}
        <p
          className="text-lg sm:text-xl text-center max-w-md leading-relaxed font-serif"
          style={{ color: "var(--text-body)" }}
        >
          Ask Srila Prabhupada anything.
          <br />
          Hear him answer in his own voice.
        </p>

        <p
          className="mt-3 text-xs tracking-widest uppercase"
          style={{ color: "var(--text-muted)" }}
        >
          Powered by AI · Grounded in scripture
        </p>

        {/* Scroll hint */}
        <div
          className="absolute bottom-8 flex flex-col items-center gap-2"
          style={{ animation: "bounce-hint 2s ease-in-out infinite" }}
        >
          <p className="text-xs tracking-wider" style={{ color: "var(--text-ghost)" }}>
            Discover more
          </p>
          <svg
            width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.5"
            style={{ color: "var(--gold-dim)" }}
          >
            <path d="M7 10l5 5 5-5" />
          </svg>
        </div>
      </section>

      {/* ── Section 2: How It Works ────────────────────────────────── */}
      <section className="px-4 py-20 max-w-4xl mx-auto">
        <h2
          className="font-serif text-2xl sm:text-3xl text-center mb-12"
          style={{ color: "var(--text-primary)" }}
        >
          How it works
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            {
              step: "1",
              icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
              ),
              title: "Ask any question",
              desc: "About life, dharma, relationships, purpose \u2014 in plain English",
            },
            {
              step: "2",
              icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
                  <path d="M8 7h8M8 11h5" />
                </svg>
              ),
              title: "Scripture search",
              desc: "AI searches 161,724 passages across 14 sacred texts in under a second",
            },
            {
              step: "3",
              icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
                  <path d="M19 10v2a7 7 0 01-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              ),
              title: "Prabhupada answers",
              desc: "Read the answer with verse references, or hear it in Prabhupada\u2019s own voice",
            },
          ].map((item) => (
            <div
              key={item.step}
              className="rounded-xl p-6 text-center transition-all duration-300"
              style={{
                border: "1px solid var(--glass-border)",
                background: "var(--glass)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(201,168,76,0.2)";
                e.currentTarget.style.background = "rgba(22,16,9,0.8)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--glass-border)";
                e.currentTarget.style.background = "var(--glass)";
              }}
            >
              <div
                className="text-xs font-sans tracking-widest uppercase mb-4"
                style={{ color: "var(--gold-dim)" }}
              >
                Step {item.step}
              </div>
              <div className="flex justify-center mb-4" style={{ color: "var(--gold)" }}>
                {item.icon}
              </div>
              <h3
                className="font-serif text-lg mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                {item.title}
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Section 3: Scripture Coverage ───────────────────────────── */}
      <section className="px-4 py-20 max-w-4xl mx-auto">
        <h2
          className="font-serif text-2xl sm:text-3xl text-center mb-3"
          style={{ color: "var(--text-primary)" }}
        >
          Every word Prabhupada wrote.
          <br />
          Searchable in seconds.
        </h2>
        <p
          className="text-sm text-center mb-12 tracking-wide"
          style={{ color: "var(--text-muted)" }}
        >
          The complete library — indexed and ready
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {SCRIPTURES.map((s) => (
            <div
              key={s.code}
              className="rounded-lg p-4 transition-all duration-200"
              style={{
                border: "1px solid var(--glass-border)",
                background: "var(--glass)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(201,168,76,0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--glass-border)";
              }}
            >
              <span
                className="text-xs font-sans font-semibold tracking-widest uppercase block mb-1"
                style={{ color: "var(--gold)" }}
              >
                {s.code}
              </span>
              <span
                className="text-sm font-serif block leading-snug"
                style={{ color: "var(--text-body)" }}
              >
                {s.name}
              </span>
              <span
                className="text-xs mt-1 block"
                style={{ color: "var(--text-muted)" }}
              >
                {s.count} passages
              </span>
            </div>
          ))}
        </div>

        {/* Total badge */}
        <div className="flex justify-center mt-8">
          <div
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs tracking-wider uppercase"
            style={{
              border: "1px solid rgba(201,168,76,0.2)",
              color: "var(--gold)",
              background: "rgba(201,168,76,0.04)",
            }}
          >
            <span>161,724 passages</span>
            <span style={{ color: "var(--text-ghost)" }}>·</span>
            <span>14 sources</span>
            <span style={{ color: "var(--text-ghost)" }}>·</span>
            <span>One search</span>
          </div>
        </div>
      </section>

      {/* ── Section 4: Example Questions ────────────────────────────── */}
      <section className="px-4 py-20 max-w-2xl mx-auto">
        <h2
          className="font-serif text-2xl sm:text-3xl text-center mb-12"
          style={{ color: "var(--text-primary)" }}
        >
          What would you ask Prabhupada?
        </h2>

        <div className="space-y-4">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <div
              key={i}
              className="rounded-xl px-6 py-5 transition-all duration-200"
              style={{
                borderLeft: "3px solid rgba(224,112,80,0.4)",
                background: "linear-gradient(to right, rgba(22,16,9,0.8), rgba(28,21,14,0.3))",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderLeftColor = "var(--vermillion-bright)";
                e.currentTarget.style.background = "linear-gradient(to right, rgba(22,16,9,0.95), rgba(28,21,14,0.5))";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderLeftColor = "rgba(224,112,80,0.4)";
                e.currentTarget.style.background = "linear-gradient(to right, rgba(22,16,9,0.8), rgba(28,21,14,0.3))";
              }}
            >
              <p
                className="font-serif italic text-lg leading-relaxed"
                style={{ color: "var(--text-body)" }}
              >
                &ldquo;{q}&rdquo;
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Section 5: Voice Feature + CTA ──────────────────────────── */}
      <section className="px-4 py-20 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
          {/* Left: Voice feature */}
          <div className="text-center md:text-left">
            {/* Waveform illustration */}
            <div className="flex items-end justify-center md:justify-start gap-1.5 mb-6">
              {[14, 24, 18, 32, 22, 28, 16, 26, 20, 30, 14, 22, 18].map((h, i) => (
                <div
                  key={i}
                  className="rounded-full"
                  style={{
                    width: 3,
                    height: h,
                    background: `linear-gradient(to top, var(--vermillion), var(--gold))`,
                    opacity: 0.6 + (i % 3) * 0.15,
                    animation: `arati-flicker ${1.5 + (i % 4) * 0.3}s ease-in-out infinite alternate`,
                    animationDelay: `${i * 0.1}s`,
                  }}
                />
              ))}
            </div>

            <h3
              className="font-serif text-xl sm:text-2xl mb-3"
              style={{ color: "var(--text-primary)" }}
            >
              Hear Prabhupada&apos;s voice
            </h3>
            <p
              className="text-sm leading-relaxed mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              AI-cloned from original recordings using ElevenLabs.
              Every answer can be heard in Srila Prabhupada&apos;s
              own speaking style — as if he were personally
              answering your question.
            </p>

            {/* Mini player mock */}
            <div
              className="inline-flex items-center gap-3 px-4 py-3 rounded-xl"
              style={{
                border: "1px solid var(--glass-border)",
                background: "var(--card)",
              }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                style={{
                  background: "linear-gradient(135deg, var(--gold), var(--gold-dim))",
                }}
              >
                <svg className="w-3.5 h-3.5 ml-0.5" style={{ color: "var(--sanctum)" }} fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-sans" style={{ color: "var(--text-secondary)" }}>
                  Prabhupada is speaking...
                </p>
                <div
                  className="w-32 h-1 rounded-full mt-1.5 overflow-hidden"
                  style={{ background: "rgba(201,168,76,0.1)" }}
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: "35%",
                      background: "linear-gradient(to right, var(--vermillion), var(--gold))",
                    }}
                  />
                </div>
              </div>
              <span
                className="text-[10px] font-mono shrink-0"
                style={{ color: "var(--text-muted)" }}
              >
                1:24 / 4:02
              </span>
            </div>
          </div>

          {/* Right: CTA */}
          <div
            className="rounded-2xl p-8 text-center"
            style={{
              border: "1px solid rgba(201,168,76,0.15)",
              background: "linear-gradient(135deg, rgba(22,16,9,0.9), rgba(28,21,14,0.6))",
              boxShadow: "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(201,168,76,0.06)",
            }}
          >
            <h3
              className="font-serif text-2xl mb-1"
              style={{ color: "var(--text-primary)" }}
            >
              Hare Kṛṣṇa
            </h3>

            <AratiDivider />

            <p
              className="text-sm mb-2"
              style={{ color: "var(--text-body)" }}
            >
              5 questions free · 2 voice answers included
            </p>

            <p
              className="text-xs mb-6"
              style={{ color: "var(--text-muted)" }}
            >
              No credit card required
            </p>

            {/* Google Sign-In */}
            <div className="flex flex-col items-center gap-4">
              <div id="google-signin-btn-bottom" />

              {!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
                <button
                  onClick={async () => {
                    try {
                      await login("dev-token");
                      router.replace("/");
                    } catch {
                      // silent
                    }
                  }}
                  className="font-display tracking-wider rounded-full transition-all"
                  style={{
                    background: "var(--gold)",
                    color: "var(--sanctum)",
                    minHeight: 44,
                    paddingLeft: "2rem",
                    paddingRight: "2rem",
                    fontSize: "0.875rem",
                    fontWeight: 600,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--gold-bright)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "var(--gold)";
                  }}
                >
                  Sign In to Ask Prabhupada
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="px-4 py-8 text-center">
        <p
          className="text-xs tracking-wider"
          style={{ color: "var(--text-ghost)" }}
        >
          Powered by 161,724 passages from Srila Prabhupada&apos;s complete works
        </p>
      </footer>
    </main>
  );
}
