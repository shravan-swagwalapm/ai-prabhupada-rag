"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { initGoogleSignIn } from "@/lib/auth";
import AratiDivider from "@/components/AratiDivider";

export default function AuthPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();
  const gsiInitialized = useRef(false);

  // If already logged in, redirect to home
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, router]);

  // Initialize Google Sign-In button
  useEffect(() => {
    if (isLoading || isAuthenticated || gsiInitialized.current) return;
    gsiInitialized.current = true;

    initGoogleSignIn("google-signin-btn", () => {
      router.replace("/");
    });
  }, [isLoading, isAuthenticated, router]);

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
    <main
      className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-12"
      style={{
        background:
          "radial-gradient(ellipse at center, rgba(201,168,76,0.04) 0%, transparent 70%), var(--sanctum)",
      }}
    >
      {/* Pulsing concentric rings */}
      <div className="relative flex items-center justify-center mb-8">
        {/* Outer ring — slowest */}
        <div
          className="absolute rounded-full"
          style={{
            width: 120,
            height: 120,
            border: "1px solid rgba(201,168,76,0.15)",
            animation: "pulse-ring 3s ease-in-out infinite",
            animationDelay: "0.6s",
          }}
        />
        {/* Middle ring */}
        <div
          className="absolute rounded-full"
          style={{
            width: 88,
            height: 88,
            border: "1px solid rgba(201,168,76,0.25)",
            animation: "pulse-ring 3s ease-in-out infinite",
            animationDelay: "0.3s",
          }}
        />
        {/* Inner ring */}
        <div
          className="absolute rounded-full"
          style={{
            width: 60,
            height: 60,
            border: "1px solid rgba(201,168,76,0.4)",
            animation: "pulse-ring 3s ease-in-out infinite",
          }}
        />
        {/* Center dot */}
        <div
          className="relative w-5 h-5 rounded-full"
          style={{
            background:
              "radial-gradient(circle, var(--gold-bright) 0%, var(--gold-dim) 100%)",
            boxShadow: "0 0 12px rgba(201,168,76,0.5)",
          }}
        />
      </div>

      {/* Title */}
      <h1
        className="font-serif font-semibold text-4xl text-center tracking-wide leading-tight"
        style={{ color: "var(--text-primary)" }}
      >
        Hare Kṛṣṇa
      </h1>

      {/* Arati divider */}
      <AratiDivider />

      {/* Scripture count badge */}
      <p
        className="text-xs tracking-widest uppercase"
        style={{ color: "var(--text-muted)" }}
      >
        161,724 sacred passages indexed
      </p>

      {/* Subtitle */}
      <p
        className="mt-3 text-sm text-center max-w-xs leading-relaxed"
        style={{ color: "var(--text-secondary)" }}
      >
        5 questions free · Voice answers included
      </p>

      {/* Google Sign-In button area */}
      <div className="mt-10 flex flex-col items-center gap-4">
        {/* Custom-styled wrapper that shows when GSI loads */}
        <div id="google-signin-btn" />

        {/* Themed CTA button (shown when no GOOGLE_CLIENT_ID, or as primary styled button) */}
        {!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
          <button
            onClick={async () => {
              try {
                await login("dev-token");
                router.replace("/");
              } catch {
                // silent in prod
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
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--gold-bright)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                "var(--gold)";
            }}
          >
            Sign In to Ask Prabhupada ✦
          </button>
        )}
      </div>

      {/* Footer */}
      <p
        className="mt-auto pt-12 text-xs text-center tracking-wider"
        style={{ color: "var(--text-ghost)" }}
      >
        Powered by 161,724 passages from Srila Prabhupada&apos;s complete works
      </p>
    </main>
  );
}
