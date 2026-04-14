const API_BASE = "/api";

/** Maximum question length enforced both client-side and server-side. */
export const MAX_QUESTION_LENGTH = 500;

export interface Passage {
  scripture: string;
  text: string;
  similarity?: number;
  chunk_id?: string;
}

export interface QueryResponse {
  question: string;
  passages: Passage[];
  ai_answer: string | null;
  audio_id: string | null;
  search_method: string;
  cached?: boolean;
}

export interface AudioStatus {
  audio_id: string;
  status: "pending" | "streaming" | "ready" | "error" | "not_found" | "unavailable";
  bytes_ready?: number;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  photo_url: string | null;
  text_quota: number;
  voice_quota: number;
}

export interface HistoryEntry {
  id: string;
  question: string;
  answer_text: string;
  answer_mode: string;
  audio_id: string | null;
  passages_json: string | null;
  created_at: string;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
  total: number;
}

/** Parse passages_json string from history entries into Passage[]. */
export function parsePassages(json: string | null): Passage[] {
  if (!json) return [];
  try {
    return JSON.parse(json);
  } catch {
    return [];
  }
}

/** Thrown when user's quota is exhausted (HTTP 402). */
export class QuotaExhaustedError extends Error {
  quota_type: string;
  remaining: number;

  constructor(quota_type: string, remaining: number) {
    super(`Your ${quota_type} quota is exhausted`);
    this.name = "QuotaExhaustedError";
    this.quota_type = quota_type;
    this.remaining = remaining;
  }
}

// ── Auth helpers ─────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("prabhupada_token");
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

function handleAuthError(status: number): void {
  if (status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("prabhupada_token");
    localStorage.removeItem("prabhupada_user");
    window.location.href = "/auth/";
  }
}

async function handleQuotaError(res: Response): Promise<never> {
  const body = await res.json().catch(() => ({}));
  throw new QuotaExhaustedError(
    body.quota_type || "text",
    body.remaining ?? 0
  );
}

// ── User API ─────────────────────────────────────────────────────────────────

export async function fetchUser(): Promise<UserInfo> {
  const res = await fetch(`${API_BASE}/user`, {
    headers: authHeaders(),
  });

  if (res.status === 401) {
    handleAuthError(401);
    throw new Error("Not authenticated");
  }
  if (!res.ok) throw new Error("Failed to fetch user");

  return res.json();
}

export async function fetchHistory(
  limit: number = 20,
  offset: number = 0
): Promise<HistoryResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await fetch(`${API_BASE}/history?${params}`, {
    headers: authHeaders(),
  });

  if (res.status === 401) {
    handleAuthError(401);
    throw new Error("Not authenticated");
  }
  if (!res.ok) throw new Error("Failed to fetch history");

  return res.json();
}

export async function submitWaitlist(email: string): Promise<void> {
  const res = await fetch(`${API_BASE}/waitlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ email }),
  });

  if (res.status === 401) {
    handleAuthError(401);
    throw new Error("Not authenticated");
  }
  if (!res.ok) throw new Error("Failed to submit to waitlist");
}

// ── Query API ────────────────────────────────────────────────────────────────

/**
 * POST /api/query — non-streaming query with auth.
 */
export async function queryScriptures(
  question: string,
  options: { includeAi?: boolean; includeVoice?: boolean; topK?: number } = {}
): Promise<QueryResponse> {
  if (!question.trim()) {
    throw new Error("Question cannot be empty");
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    throw new Error(`Question too long (max ${MAX_QUESTION_LENGTH} characters)`);
  }

  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      question: question.trim(),
      top_k: options.topK ?? 5,
      include_ai: options.includeAi ?? true,
      include_voice: options.includeVoice ?? false,
    }),
  });

  if (res.status === 401) {
    handleAuthError(401);
    throw new Error("Not authenticated");
  }
  if (res.status === 402) {
    return handleQuotaError(res);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      // ignore
    }
    throw new Error(`Query failed (${res.status}): ${detail}`);
  }

  return res.json();
}

/**
 * GET /api/query/stream — SSE streaming with auth headers.
 *
 * Uses fetch + ReadableStream instead of EventSource (which can't send headers).
 * Returns a cleanup function to abort the stream.
 */
export interface QueryStreamCallbacks {
  onPassages?: (passages: Passage[]) => void;
  onAnswerChunk?: (chunk: string) => void;
  onAudioId?: (audioId: string) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
  onQuotaExhausted?: (quotaType: string) => void;
  onNoMatch?: (message: string) => void;
}

export function queryStream(
  question: string,
  callbacks: QueryStreamCallbacks,
  options: { includeVoice?: boolean } = {}
): () => void {
  // Client-side guard
  if (!question.trim()) {
    callbacks.onError?.("Question cannot be empty");
    return () => {};
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    callbacks.onError?.(
      `Question too long (max ${MAX_QUESTION_LENGTH} characters)`
    );
    return () => {};
  }

  const params = new URLSearchParams({
    question: question.trim(),
    top_k: '5',  // locked — do not expose to callers
  });
  if (options.includeVoice) {
    params.set("include_voice", "true");
  }

  const url = `${API_BASE}/query/stream?${params.toString()}`;
  const controller = new AbortController();

  // Use fetch with auth headers (EventSource can't set headers)
  (async () => {
    try {
      const res = await fetch(url, {
        headers: authHeaders(),
        signal: controller.signal,
      });

      if (res.status === 401) {
        handleAuthError(401);
        return;
      }

      if (res.status === 402) {
        const body = await res.json().catch(() => ({}));
        callbacks.onQuotaExhausted?.(body.quota_type || "text");
        return;
      }

      if (!res.ok) {
        callbacks.onError?.(`Server error (${res.status})`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError?.("Stream not available");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let doneFired = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE lines
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6);
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            switch (data.type) {
              case "passages":
                callbacks.onPassages?.(data.data as Passage[]);
                break;
              case "answer_chunk":
                callbacks.onAnswerChunk?.(data.data as string);
                break;
              case "audio_id":
                callbacks.onAudioId?.(data.data as string);
                break;
              case "audio_status":
                // Voice unavailable (circuit breaker open)
                break;
              case "done":
                if (!doneFired) {
                  doneFired = true;
                  callbacks.onDone?.();
                }
                break;
              case "no_match":
                callbacks.onNoMatch?.(data.message);
                break;
              case "error":
                callbacks.onError?.(data.message || "Server error");
                break;
            }
          } catch {
            // Ignore malformed JSON
          }
        }
      }

      // If stream ended without a 'done' event, still notify completion
      if (!doneFired) {
        callbacks.onDone?.();
      }
    } catch (err: any) {
      if (err.name === "AbortError") return; // Intentional cancel
      callbacks.onError?.("Connection to server lost. Please try again.");
    }
  })();

  return () => controller.abort();
}

/**
 * Poll audio generation status.
 */
export async function checkAudioStatus(
  audioId: string
): Promise<AudioStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/audio/${audioId}/status`);
    if (!res.ok) {
      if (res.status === 404) {
        return { audio_id: audioId, status: "not_found" };
      }
      return null;
    }
    return res.json() as Promise<AudioStatus>;
  } catch {
    return null;
  }
}

/**
 * Get audio URL for playback.
 */
export function getAudioUrl(audioId: string): string {
  return `${API_BASE}/audio/${audioId}`;
}
