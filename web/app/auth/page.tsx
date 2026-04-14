"use client";

import { useEffect, useRef, useState } from "react";
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

const GSI_FALLBACK_DELAY_MS = 5000;

// ─── Component ───────────────────────────────────────────────────────────────

export default function AuthPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();
  const gsiInitialized = useRef(false);
  const [showGsiFallback, setShowGsiFallback] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isLoading || isAuthenticated || gsiInitialized.current) return;
    gsiInitialized.current = true;
    initGoogleSignIn("google-signin-btn-hero", () => {
      window.location.href = "/";
    });
    initGoogleSignIn("google-signin-btn-bottom", () => {
      window.location.href = "/";
    });

    // If GSI button hasn't rendered after 5s, show fallback help
    const fallbackTimer = setTimeout(() => {
      const heroBtn = document.getElementById("google-signin-btn-hero");
      if (heroBtn && !heroBtn.querySelector("iframe")) {
        setShowGsiFallback(true);
      }
    }, GSI_FALLBACK_DELAY_MS);
    return () => clearTimeout(fallbackTimer);
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
      <section className="min-h-screen flex flex-col items-center justify-center px-4 py-6 sm:py-12 sm:pb-28 relative">
        {/* Background glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(26,58,107,0.03) 0%, transparent 70%)",
          }}
        />

        {/* Walking Prabhupada — Gemini illustration */}
        <div className="relative flex items-center justify-center mb-4 sm:mb-6">
          {/* Golden aura behind the figure */}
          <div
            className="absolute prabhupada-aura rounded-full"
            style={{
              width: 280,
              height: 280,
              background: "radial-gradient(circle, rgba(201,168,76,0.12) 0%, rgba(201,168,76,0.03) 50%, transparent 70%)",
            }}
          />
          <picture>
            <source srcSet="/prabhupada-walking.webp" type="image/webp" />
            <img
              src="/prabhupada-walking.png"
              alt="Srila Prabhupada on his morning walk"
              className="relative"
              width={169}
              height={260}
              style={{ height: 260, width: "auto" }}
            />
          </picture>
        </div>

        {/* Title */}
        <h1
          className="font-serif font-bold text-4xl sm:text-5xl text-center leading-tight"
          style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
        >
          Prabhupada AI
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

        {/* Hero CTA */}
        <div className="mt-5 sm:mt-8 flex flex-col items-center gap-3">
          <div id="google-signin-btn-hero" />

          {showGsiFallback && (
            <p
              aria-live="polite"
              className="text-sm text-center max-w-xs leading-relaxed"
              style={{ color: "var(--text-muted)" }}
            >
              Having trouble signing in? Try opening this page in Chrome,
              or update Safari to the latest version.
            </p>
          )}

          {!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
            <button
              onClick={async () => {
                try {
                  await login("dev-token");
                  router.replace("/");
                } catch { /* silent */ }
              }}
              className="rounded-full transition-all"
              style={{
                background: "var(--gold)",
                color: "var(--sanctum)",
                minHeight: 44,
                paddingLeft: "2rem",
                paddingRight: "2rem",
                fontSize: "0.875rem",
                fontWeight: 600,
                letterSpacing: "0.05em",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "var(--gold-bright)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "var(--gold)"; }}
            >
              Sign In to Ask Prabhupada
            </button>
          )}

          <p className="text-xs" style={{ color: "var(--text-ghost)" }}>
            7 questions free · No credit card
          </p>
        </div>

        {/* Scroll hint — hidden on small screens to avoid overlap */}
        <div
          className="absolute bottom-8 hidden sm:flex flex-col items-center gap-2"
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
          className="font-serif font-bold text-2xl sm:text-3xl text-center mb-12"
          style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
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
                e.currentTarget.style.borderColor = "var(--glass-border-hover)";
                e.currentTarget.style.background = "rgba(255,255,255,0.8)";
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
                className="font-serif font-bold text-lg mb-2"
                style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
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
          className="font-serif font-bold text-2xl sm:text-3xl text-center mb-3"
          style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
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
                e.currentTarget.style.borderColor = "var(--glass-border-hover)";
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
          className="font-serif font-bold text-2xl sm:text-3xl text-center mb-12"
          style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
        >
          What would you ask Prabhupada?
        </h2>

        <div className="space-y-4">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <div
              key={i}
              className="rounded-xl transition-all duration-200"
              style={{
                background: "var(--bg-card-gradient)",
                border: "1px solid var(--glass-border)",
                borderLeft: "3.5px solid var(--vermillion)",
                borderRadius: 14,
                padding: "18px 20px",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--glass-border-hover)";
                e.currentTarget.style.borderLeftColor = "var(--vermillion-bright)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--glass-border)";
                e.currentTarget.style.borderLeftColor = "var(--vermillion)";
              }}
            >
              <p
                className="font-serif text-lg leading-relaxed"
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
              className="font-serif font-bold text-xl sm:text-2xl mb-3"
              style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}
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
                background: "var(--glass)",
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
                className="text-xs font-mono shrink-0"
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
              border: "1px solid rgba(26,58,107,0.2)",
              background: "linear-gradient(135deg, var(--krishna-blue), var(--krishna-blue-dark))",
              borderRadius: 16,
              boxShadow: "0 4px 24px rgba(26,58,107,0.2)",
            }}
          >
            <h3
              className="font-serif font-bold text-2xl mb-1"
              style={{ color: "var(--sanctum)", letterSpacing: "-0.02em" }}
            >
              Prabhupada AI
            </h3>

            <AratiDivider />

            <p
              className="text-sm mb-2"
              style={{ color: "rgba(250,246,239,0.85)" }}
            >
              7 questions free · 5 text + 2 voice
            </p>

            <p
              className="text-xs mb-6"
              style={{ color: "rgba(250,246,239,0.5)" }}
            >
              No credit card required
            </p>

            {/* Google Sign-In */}
            <div className="flex flex-col items-center gap-4">
              <div id="google-signin-btn-bottom" />

              {showGsiFallback && (
                <p
                  aria-live="polite"
                  className="text-sm text-center max-w-xs leading-relaxed"
                  style={{ color: "rgba(250,246,239,0.65)" }}
                >
                  Having trouble signing in? Try opening this page in Chrome,
                  or update Safari to the latest version.
                </p>
              )}

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
      <footer className="px-4 pt-16 pb-6 text-center">
        <p
          className="font-sans"
          style={{ color: "var(--text-muted)", fontSize: "13px", letterSpacing: "0.04em" }}
        >
          Powered by 161,724 passages from Srila Prabhupada&apos;s complete works
        </p>
      </footer>
    </main>
  );
}
