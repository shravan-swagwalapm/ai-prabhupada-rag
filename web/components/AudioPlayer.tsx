"use client";

import { useState, useEffect, useRef } from "react";
import { checkAudioStatus, getAudioUrl } from "@/lib/api";

interface Props {
  audioId: string | null;
}

type AudioState = "idle" | "generating" | "ready" | "playing" | "paused" | "error";

const POLL_TIMEOUT_MS = 5 * 60 * 1000;
const POLL_INITIAL_INTERVAL_MS = 1500;
const POLL_MAX_INTERVAL_MS = 10_000;

export default function AudioPlayer({ audioId }: Props) {
  const [state, setState] = useState<AudioState>("idle");
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollStartRef = useRef<number>(0);
  const animFrameRef = useRef<number>(0);

  const stopPolling = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
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
    let currentInterval = POLL_INITIAL_INTERVAL_MS;

    const schedulePoll = () => {
      timeoutRef.current = setTimeout(async () => {
        if (Date.now() - pollStartRef.current > POLL_TIMEOUT_MS) {
          setState("error");
          return;
        }

        const status = await checkAudioStatus(audioId);
        if (status === null) {
          schedulePoll();
          return;
        }

        if (status.status === "ready") {
          setState("ready");
        } else if (status.status === "error" || status.status === "not_found") {
          setState("error");
        } else {
          // Exponential backoff: double interval up to max
          currentInterval = Math.min(currentInterval * 2, POLL_MAX_INTERVAL_MS);
          schedulePoll();
        }
      }, currentInterval);
    };

    // First poll immediately
    (async () => {
      const status = await checkAudioStatus(audioId);
      if (status?.status === "ready") { setState("ready"); return; }
      if (status?.status === "error" || status?.status === "not_found") { setState("error"); return; }
      schedulePoll();
    })();

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
    <div className="w-full max-w-3xl mx-auto mt-4">
      <div
        className="overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #1A3A6B, #15305A)",
          borderRadius: 16,
        }}
      >
        {/* Spotify progress line at top — 3px */}
        <div style={{ height: 3, background: "rgba(250,246,239,0.08)" }}>
          <div
            className="h-full transition-[width] duration-100"
            style={{
              width: `${progressPct}%`,
              background: "linear-gradient(to right, #C9A84C, #E0C068)",
              borderRadius: "0 2px 2px 0",
            }}
          />
        </div>

        <div className="flex items-center gap-4 px-5 py-4">
          {/* Play button — gold circle */}
          <button
            onClick={togglePlay}
            disabled={state === "generating" || state === "error"}
            className="flex items-center justify-center rounded-full transition-all disabled:cursor-not-allowed shrink-0"
            style={{
              width: 48,
              height: 48,
              background: state === "generating" || state === "error"
                ? "rgba(201,168,76,0.15)"
                : "linear-gradient(135deg, #C9A84C, #E0C068)",
              opacity: state === "error" ? 0.4 : 1,
              boxShadow: state === "playing" ? "0 4px 12px rgba(201,168,76,0.25)" : "none",
            }}
            aria-label={state === "playing" ? "Pause" : "Listen to Prabhupada"}
          >
            {state === "generating" ? (
              <svg className="w-5 h-5 animate-spin" style={{ color: "#C9A84C" }} fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : state === "playing" ? (
              <svg className="w-5 h-5" style={{ color: "#1A3A6B" }} fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="w-5 h-5 ml-0.5" style={{ color: "#1A3A6B" }} fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="font-sans text-[13px] font-semibold truncate" style={{ color: "rgba(250,246,239,0.9)" }}>
              {state === "generating" && "Generating Prabhupada\u2019s voice..."}
              {state === "ready" && "Listen to Prabhupada"}
              {state === "playing" && "Prabhupada is speaking..."}
              {state === "paused" && "Paused"}
              {state === "error" && "Voice unavailable"}
            </p>
            {/* Waveform bars */}
            <div className="flex items-end gap-[2px] mt-2 h-4">
              {Array.from({ length: 24 }).map((_, i) => {
                const played = duration > 0 ? (i / 24) < (progress / duration) : false;
                return (
                  <div
                    key={i}
                    style={{
                      width: 3,
                      height: `${30 + Math.sin(i * 0.8) * 60}%`,
                      borderRadius: 2,
                      background: played ? "#C9A84C" : "rgba(250,246,239,0.15)",
                      transition: "background 0.1s",
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Time */}
          {duration > 0 && (
            <span
              className="text-[11px] font-sans shrink-0"
              style={{
                color: "rgba(250,246,239,0.4)",
                fontVariantNumeric: "tabular-nums",
                fontFamily: "monospace",
              }}
            >
              {formatTime(progress)} / {formatTime(duration)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
