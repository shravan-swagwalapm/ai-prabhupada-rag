"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { checkAudioStatus, getAudioUrl } from "@/lib/api";

interface Props {
  audioId: string | null;
  /** Pre-created Audio element from user gesture (for mobile auto-play). */
  gestureAudio?: HTMLAudioElement | null;
}

type AudioState = "idle" | "generating" | "ready" | "playing" | "paused" | "error";

/** Backend status — tracks what the server reports separately from playback state. */
type BackendStatus = "pending" | "streaming" | "ready" | "error" | "unknown";

const POLL_TIMEOUT_MS = 5 * 60 * 1000;
const POLL_INITIAL_INTERVAL_MS = 1500;
const POLL_MAX_INTERVAL_MS = 10_000;
const SPEED_OPTIONS = [1, 1.25, 1.5, 0.75] as const;

/** Shared drag-to-scrub logic for progress bar and waveform */
function useScrub(
  audioRef: React.MutableRefObject<HTMLAudioElement | null>,
  duration: number,
  setProgress: (p: number) => void,
  scrubDisabled: boolean
) {
  const isDragging = useRef(false);
  const dragProgress = useRef(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const getPositionFromEvent = useCallback(
    (e: MouseEvent | TouchEvent) => {
      const container = containerRef.current;
      if (!container || duration <= 0) return null;
      const rect = container.getBoundingClientRect();
      const clientX = "touches" in e
        ? (e.touches[0]?.clientX ?? e.changedTouches?.[0]?.clientX ?? 0)
        : e.clientX;
      const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      return pct * duration;
    },
    [duration]
  );

  const onMove = useCallback(
    (e: MouseEvent | TouchEvent) => {
      if (!isDragging.current) return;
      const pos = getPositionFromEvent(e);
      if (pos !== null) {
        dragProgress.current = pos;
        setProgress(pos);
      }
    },
    [getPositionFromEvent, setProgress]
  );

  const onEnd = useCallback(() => {
    if (!isDragging.current) return;
    isDragging.current = false;
    const audio = audioRef.current;
    if (audio && isFinite(dragProgress.current) && dragProgress.current >= 0) {
      audio.currentTime = dragProgress.current;
    }
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onEnd);
    document.removeEventListener("touchmove", onMove);
    document.removeEventListener("touchend", onEnd);
  }, [audioRef, onMove]);

  const onStart = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (scrubDisabled || duration <= 0) return;
      isDragging.current = true;
      const nativeEvent = e.nativeEvent;
      const pos = getPositionFromEvent(nativeEvent as MouseEvent | TouchEvent);
      if (pos !== null) {
        dragProgress.current = pos;
        setProgress(pos);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onEnd);
      document.addEventListener("touchmove", onMove);
      document.addEventListener("touchend", onEnd);
    },
    [scrubDisabled, duration, getPositionFromEvent, onMove, onEnd, setProgress]
  );

  return { containerRef, onStart, isDragging };
}

export default function AudioPlayer({ audioId, gestureAudio }: Props) {
  const [state, setState] = useState<AudioState>("idle");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("unknown");
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speedIndex, setSpeedIndex] = useState(0);
  const [hoveringBar, setHoveringBar] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollStartRef = useRef<number>(0);
  const animFrameRef = useRef<number>(0);
  /** Ref to avoid stale closure of updateProgressLoop in rAF callbacks. */
  const updateProgressLoopRef = useRef<() => void>(() => {});
  /** Track whether we've already started auto-play for this audioId. */
  const autoPlayFiredRef = useRef<string | null>(null);
  /** Ref to current backend status — used in audio event handlers to avoid stale closures. */
  const backendStatusRef = useRef<BackendStatus>("unknown");

  const currentSpeed = SPEED_OPTIONS[speedIndex];

  // Keep ref in sync for use in audio event handler closures
  backendStatusRef.current = backendStatus;

  // Scrubbing is disabled when backend is still streaming (can't seek a live stream)
  const scrubDisabled = backendStatus === "streaming";

  const progressBar = useScrub(audioRef, duration, setProgress, scrubDisabled);
  const waveformBar = useScrub(audioRef, duration, setProgress, scrubDisabled);

  const stopPolling = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  /** Start playback using either the gesture-unlocked Audio or a new one. */
  const startStreaming = useCallback(
    (id: string) => {
      // Prevent double auto-play for same audioId
      if (autoPlayFiredRef.current === id) return;
      autoPlayFiredRef.current = id;

      // Reuse the gesture-unlocked Audio element if available, otherwise create new
      let audio: HTMLAudioElement;
      if (gestureAudio) {
        audio = gestureAudio;
      } else {
        audio = new Audio();
      }

      audio.src = getAudioUrl(id);
      audio.playbackRate = currentSpeed;

      audio.onended = () => {
        setState("ready");
        setProgress(0);
      };
      audio.onerror = () => {
        setState("error");
      };
      audio.onstalled = () => {
        // Only treat as error if backend also errored — brief stalls are normal during streaming
        if (backendStatusRef.current === "error") {
          setState("error");
        }
      };
      audio.onloadedmetadata = () => {
        if (isFinite(audio.duration) && audio.duration > 0) {
          setDuration(audio.duration);
        }
      };
      // Also listen for durationchange — fires when full file is buffered
      audio.ondurationchange = () => {
        if (isFinite(audio.duration) && audio.duration > 0) {
          setDuration(audio.duration);
        }
      };

      audioRef.current = audio;
      audio.play().catch(() => {
        // Auto-play blocked — fall back to manual play (ready state)
        setState("ready");
      });
      setState("playing");
      animFrameRef.current = requestAnimationFrame(() => updateProgressLoopRef.current());
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [gestureAudio, currentSpeed]
  );

  // Poll for audio readiness
  useEffect(() => {
    if (!audioId) {
      setState("idle");
      setBackendStatus("unknown");
      stopPolling();
      return;
    }

    setState("generating");
    setBackendStatus("pending");
    pollStartRef.current = Date.now();
    autoPlayFiredRef.current = null;
    let currentInterval = POLL_INITIAL_INTERVAL_MS;

    const schedulePoll = () => {
      timeoutRef.current = setTimeout(async () => {
        if (Date.now() - pollStartRef.current > POLL_TIMEOUT_MS) {
          setState("error");
          setBackendStatus("error");
          return;
        }

        const status = await checkAudioStatus(audioId);
        if (status === null) {
          schedulePoll();
          return;
        }

        if (status.status === "streaming") {
          setBackendStatus("streaming");
          // Auto-play as soon as streaming starts
          startStreaming(audioId);
          // Continue polling to detect transition to "ready"
          currentInterval = POLL_INITIAL_INTERVAL_MS;
          schedulePoll();
        } else if (status.status === "ready") {
          setBackendStatus("ready");
          // Auto-play if we haven't already (e.g., audio skipped "streaming" state)
          if (autoPlayFiredRef.current !== audioId) {
            startStreaming(audioId);
          }
        } else if (status.status === "error" || status.status === "not_found") {
          setBackendStatus("error");
          setState("error");
        } else {
          // pending or other — keep polling
          currentInterval = Math.min(currentInterval * 2, POLL_MAX_INTERVAL_MS);
          schedulePoll();
        }
      }, currentInterval);
    };

    // Immediate first check
    (async () => {
      const status = await checkAudioStatus(audioId);
      if (status?.status === "streaming") {
        setBackendStatus("streaming");
        startStreaming(audioId);
        schedulePoll();
        return;
      }
      if (status?.status === "ready") {
        setBackendStatus("ready");
        // Auto-play even when audio went straight to "ready" (skipped streaming)
        if (autoPlayFiredRef.current !== audioId) {
          startStreaming(audioId);
        } else {
          setState("ready");
        }
        return;
      }
      if (status?.status === "error" || status?.status === "not_found") {
        setBackendStatus("error");
        setState("error");
        return;
      }
      schedulePoll();
    })();

    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioId]);

  // Clean up audio + animation frame on audioId change
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

  const updateProgressLoop = () => {
    const audio = audioRef.current;
    if (audio && !progressBar.isDragging.current && !waveformBar.isDragging.current) {
      setProgress(audio.currentTime);
      if (isFinite(audio.duration) && audio.duration > 0) {
        setDuration(audio.duration);
      }
    }
    if (audio && !audio.paused && !audio.ended) {
      animFrameRef.current = requestAnimationFrame(() => updateProgressLoopRef.current());
    }
  };
  updateProgressLoopRef.current = updateProgressLoop;

  const togglePlay = () => {
    if (!audioId || state === "generating" || state === "error") return;

    if (!audioRef.current) {
      const audio = new Audio(getAudioUrl(audioId));
      audio.playbackRate = currentSpeed;
      audio.onended = () => {
        setState("ready");
        setProgress(0);
      };
      audio.onerror = () => setState("error");
      audio.onloadedmetadata = () => setDuration(audio.duration);
      audio.ondurationchange = () => {
        if (isFinite(audio.duration) && audio.duration > 0) {
          setDuration(audio.duration);
        }
      };
      audioRef.current = audio;
    }

    if (state === "playing") {
      audioRef.current.pause();
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      setState("paused");
    } else {
      audioRef.current.play().catch(() => {
        if (audioRef.current?.paused === false) {
          setState("error");
        }
      });
      setState("playing");
      animFrameRef.current = requestAnimationFrame(() => updateProgressLoopRef.current());
    }
  };

  const cycleSpeed = () => {
    const nextIndex = (speedIndex + 1) % SPEED_OPTIONS.length;
    setSpeedIndex(nextIndex);
    if (audioRef.current) {
      audioRef.current.playbackRate = SPEED_OPTIONS[nextIndex];
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  if (!audioId || state === "idle") return null;

  // Error state — graceful failure
  if (state === "error") {
    return (
      <div className="w-full max-w-3xl mx-auto mt-4">
        <div
          className="overflow-hidden px-5 py-4"
          role="alert"
          style={{
            background: "linear-gradient(135deg, var(--krishna-blue), var(--krishna-blue-dark))",
            borderRadius: 16,
          }}
        >
          <p
            className="font-sans text-sm text-center"
            style={{ color: "rgba(250,246,239,0.6)" }}
          >
            Voice unavailable — read the text answer below
          </p>
        </div>
      </div>
    );
  }

  const isStreaming = backendStatus === "streaming";
  const hasDuration = isFinite(duration) && duration > 0;
  const rawPct = hasDuration ? (progress / duration) * 100 : 0;
  const progressPct = isFinite(rawPct) ? Math.max(0, Math.min(100, rawPct)) : 0;

  // Cursor style: default when scrubbing disabled, pointer when allowed
  const scrubCursor = scrubDisabled ? "default" : (hasDuration ? "pointer" : "default");

  // Status label
  const statusLabel = (() => {
    if (state === "generating") return "Generating Prabhupada\u2019s voice...";
    if (state === "playing") return "Prabhupada is speaking...";
    if (state === "ready") return "Listen to Prabhupada";
    if (state === "paused") return "Paused";
    return "";
  })();

  return (
    <div className="w-full max-w-3xl mx-auto mt-4">
      <div
        className="overflow-hidden"
        style={{
          background: "linear-gradient(135deg, var(--krishna-blue), var(--krishna-blue-dark))",
          borderRadius: 16,
        }}
      >
        {/* Progress bar — draggable (when not streaming), thickens on hover */}
        <div
          ref={progressBar.containerRef}
          onMouseDown={progressBar.onStart}
          onTouchStart={progressBar.onStart}
          onMouseEnter={() => setHoveringBar(true)}
          onMouseLeave={() => { if (!progressBar.isDragging.current) setHoveringBar(false); }}
          style={{
            height: hoveringBar || progressBar.isDragging.current ? 8 : 3,
            background: "rgba(250,246,239,0.08)",
            cursor: scrubCursor,
            transition: "height 0.15s ease",
            position: "relative",
          }}
        >
          {/* Shimmer fill during streaming, gold fill when ready */}
          {state === "playing" && isStreaming ? (
            <div
              className="h-full audio-shimmer"
              style={{
                width: "100%",
                borderRadius: "0 2px 2px 0",
              }}
            />
          ) : (
            <div
              className="h-full"
              style={{
                width: `${progressPct}%`,
                background: "linear-gradient(to right, #C9A84C, #E0C068)",
                borderRadius: "0 2px 2px 0",
                transition: progressBar.isDragging.current ? "none" : "width 0.1s",
              }}
            />
          )}
          {/* Thumb — visible on hover, only when scrubbing is allowed */}
          {!scrubDisabled && (hoveringBar || progressBar.isDragging.current) && hasDuration && (
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: `${progressPct}%`,
                transform: "translate(-50%, -50%)",
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: "#E0C068",
                boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
                pointerEvents: "none",
              }}
            />
          )}
        </div>

        <div className="flex items-center gap-4 px-5 py-4">
          {/* Play button — gold circle */}
          <button
            onClick={togglePlay}
            disabled={state === "generating"}
            className="flex items-center justify-center rounded-full transition-all disabled:cursor-not-allowed shrink-0"
            style={{
              width: 48,
              height: 48,
              background: state === "generating"
                ? "rgba(201,168,76,0.15)"
                : "linear-gradient(135deg, #C9A84C, #E0C068)",
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
              <svg className="w-5 h-5" style={{ color: "var(--krishna-blue)" }} fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="w-5 h-5 ml-0.5" style={{ color: "var(--krishna-blue)" }} fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="font-sans text-sm font-semibold truncate" style={{ color: "rgba(250,246,239,0.9)" }}>
              {statusLabel}
            </p>
            {/* Waveform bars — draggable to seek (when not streaming) */}
            <div
              ref={waveformBar.containerRef}
              onMouseDown={waveformBar.onStart}
              onTouchStart={waveformBar.onStart}
              className="flex items-end gap-[2px] mt-2 h-4"
              style={{ cursor: scrubCursor }}
            >
              {Array.from({ length: 24 }).map((_, i) => {
                const played = hasDuration ? (i / 24) < (progress / duration) : false;
                // During streaming, show a subtle animated effect instead of static bars
                const streamingActive = state === "playing" && isStreaming;
                return (
                  <div
                    key={i}
                    style={{
                      width: 3,
                      height: `${30 + Math.sin(i * 0.8) * 60}%`,
                      borderRadius: 2,
                      background: streamingActive
                        ? "rgba(201,168,76,0.35)"
                        : played
                          ? "#C9A84C"
                          : "rgba(250,246,239,0.15)",
                      transition: waveformBar.isDragging.current ? "none" : "background 0.1s",
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Speed toggle */}
          <button
            onClick={cycleSpeed}
            className="shrink-0 rounded-md transition-colors"
            style={{
              minWidth: 44,
              minHeight: 44,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: currentSpeed === 1 ? "rgba(250,246,239,0.4)" : "#C9A84C",
              fontSize: 14,
              fontWeight: 700,
              fontFamily: "monospace",
              background: currentSpeed === 1 ? "transparent" : "rgba(201,168,76,0.1)",
              border: currentSpeed === 1 ? "1px solid rgba(250,246,239,0.15)" : "1px solid rgba(201,168,76,0.25)",
            }}
            aria-label={`Playback speed: ${currentSpeed}x. Tap to change.`}
          >
            {currentSpeed}x
          </button>

          {/* Time — elapsed only during streaming, elapsed / total when ready */}
          {(state === "playing" || state === "paused") && (
            <span
              className="text-sm font-sans shrink-0"
              style={{
                color: "rgba(250,246,239,0.4)",
                fontVariantNumeric: "tabular-nums",
                fontFamily: "monospace",
              }}
            >
              {formatTime(progress)}{hasDuration && !isStreaming ? ` / ${formatTime(duration)}` : ""}
            </span>
          )}
          {/* Show duration when ready but not yet playing */}
          {state === "ready" && hasDuration && (
            <span
              className="text-sm font-sans shrink-0"
              style={{
                color: "rgba(250,246,239,0.4)",
                fontVariantNumeric: "tabular-nums",
                fontFamily: "monospace",
              }}
            >
              {formatTime(duration)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
