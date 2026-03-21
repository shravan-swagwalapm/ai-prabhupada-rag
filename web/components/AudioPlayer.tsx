"use client";

import { useState, useEffect, useRef } from "react";
import { checkAudioStatus, getAudioUrl } from "@/lib/api";

interface Props {
  audioId: string | null;
}

type AudioState = "idle" | "generating" | "ready" | "playing" | "paused" | "error";

const POLL_TIMEOUT_MS = 5 * 60 * 1000;
const POLL_INTERVAL_MS = 1500;

export default function AudioPlayer({ audioId }: Props) {
  const [state, setState] = useState<AudioState>("idle");
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollStartRef = useRef<number>(0);
  const animFrameRef = useRef<number>(0);

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // Poll for audio readiness
  useEffect(() => {
    if (!audioId) {
      setState("idle");
      stopPolling();
      return;
    }

    setState("generating");
    pollStartRef.current = Date.now();

    const poll = async () => {
      if (Date.now() - pollStartRef.current > POLL_TIMEOUT_MS) {
        setState("error");
        stopPolling();
        return;
      }

      const status = await checkAudioStatus(audioId);
      if (status === null) return;

      if (status.status === "ready") {
        setState("ready");
        stopPolling();
      } else if (status.status === "error" || status.status === "not_found") {
        setState("error");
        stopPolling();
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => stopPolling();
  }, [audioId]);

  // Clean up audio + animation frame
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current = null;
      }
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [audioId]);

  const updateProgress = () => {
    const audio = audioRef.current;
    if (audio) {
      setProgress(audio.currentTime);
      setDuration(audio.duration || 0);
      // Use the audio element's actual paused state — NOT React state,
      // which would be stale inside this requestAnimationFrame callback.
      if (!audio.paused && !audio.ended) {
        animFrameRef.current = requestAnimationFrame(updateProgress);
      }
    }
  };

  const togglePlay = () => {
    if (!audioId || state === "generating" || state === "error") return;

    if (!audioRef.current) {
      const audio = new Audio(getAudioUrl(audioId));
      audio.onended = () => {
        setState("ready");
        setProgress(0);
      };
      audio.onerror = () => setState("error");
      audio.onloadedmetadata = () => setDuration(audio.duration);
      audioRef.current = audio;
    }

    if (state === "playing") {
      audioRef.current.pause();
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      setState("paused");
    } else {
      audioRef.current.play().catch(() => setState("error"));
      setState("playing");
      animFrameRef.current = requestAnimationFrame(updateProgress);
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  if (!audioId || state === "idle") return null;

  const progressPct = duration > 0 ? (progress / duration) * 100 : 0;

  return (
    <div className="w-full max-w-3xl mx-auto mt-0">
      <div
        className="flex items-center gap-4 p-4 rounded-xl shadow-sm"
        style={{
          border: "1px solid var(--glass-border)",
          background: "var(--card)",
        }}
      >
        {/* Play/Pause button — double-ring gold glow */}
        <div
          className="shrink-0"
          style={{
            boxShadow: state === "playing"
              ? "0 0 0 3px var(--gold-dim), 0 0 0 6px rgba(201,168,76,0.15)"
              : "none",
            borderRadius: "9999px",
            transition: "box-shadow 0.3s ease",
          }}
        >
          <button
            onClick={togglePlay}
            disabled={state === "generating" || state === "error"}
            className="flex items-center justify-center rounded-full transition-all disabled:cursor-not-allowed"
            style={{
              width: "44px",
              height: "44px",
              background: state === "generating" || state === "error"
                ? "rgba(201,168,76,0.12)"
                : "linear-gradient(135deg, var(--gold), var(--gold-dim))",
              opacity: state === "error" ? 0.4 : 1,
            }}
            aria-label={state === "playing" ? "Pause" : "Listen to Prabhupada"}
          >
            {state === "generating" ? (
              <svg
                className="w-4 h-4 animate-spin"
                style={{ color: "var(--gold)" }}
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : state === "playing" ? (
              <svg className="w-4 h-4" style={{ color: "var(--sanctum)" }} fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="w-4 h-4 ml-0.5" style={{ color: "var(--sanctum)" }} fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
        </div>

        {/* Info + progress */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <p className="font-sans text-xs font-medium truncate" style={{ color: "var(--text-secondary)" }}>
              {state === "generating" && "Generating Prabhupada's voice..."}
              {state === "ready" && "Listen to Prabhupada"}
              {state === "playing" && "Prabhupada is speaking..."}
              {state === "paused" && "Paused"}
              {state === "error" && "Voice not available"}
            </p>
            {duration > 0 && (
              <span
                className="text-[10px] font-sans shrink-0 ml-2"
                style={{
                  color: "var(--text-muted)",
                  fontVariantNumeric: "tabular-nums",
                  fontFamily: "monospace",
                }}
              >
                {formatTime(progress)} / {formatTime(duration)}
              </span>
            )}
          </div>

          {/* Progress bar — vermillion → gold gradient */}
          <div
            className="w-full h-1 rounded-full overflow-hidden"
            style={{ background: "rgba(201,168,76,0.1)" }}
          >
            <div
              className="h-full rounded-full transition-[width] duration-100"
              style={{
                width: `${progressPct}%`,
                background: "linear-gradient(to right, var(--vermillion), var(--gold))",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
