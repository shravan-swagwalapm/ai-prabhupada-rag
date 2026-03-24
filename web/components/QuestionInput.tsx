"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  voiceQuotaExhausted?: boolean;
  children?: React.ReactNode;
}

const EXAMPLE_QUESTIONS = [
  "What is the nature of the soul?",
  "How should one perform their duty?",
  "What is the purpose of human life?",
  "What does Krishna say about karma?",
  "How to achieve peace of mind?",
];

export default function QuestionInput({
  onSubmit,
  isLoading,
  disabled,
  voiceQuotaExhausted = false,
  children,
}: Props) {
  const [question, setQuestion] = useState("");
  const [isListening, setIsListening] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  // Check for Web Speech API support
  const speechSupported =
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || isLoading || disabled) return;
    onSubmit(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleVoiceInput = () => {
    if (voiceQuotaExhausted) return;
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuestion(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          ref={inputRef}
          value={isListening ? "Listening..." : question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything…"
          rows={1}
          maxLength={500}
          disabled={isLoading || disabled || isListening}
          className="w-full resize-none disabled:opacity-50 transition-all font-serif"
          style={{
            background: "#FFFFFF",
            border: "1px solid var(--glass-border)",
            borderRadius: 22,
            boxShadow: "var(--shadow-search), inset 0 1px 0 rgba(255,255,255,0.9)",
            color: "var(--text-primary)",
            outline: "none",
            padding: "14px 80px 14px 22px",
            fontSize: 17,
            lineHeight: 1.5,
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--glass-border-hover)";
            e.currentTarget.style.boxShadow =
              "var(--shadow-search), 0 0 0 3px rgba(26,58,107,0.06)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--glass-border)";
            e.currentTarget.style.boxShadow =
              "var(--shadow-search), inset 0 1px 0 rgba(255,255,255,0.9)";
          }}
        />
        {/* Placeholder colour handled via inline style workaround in globals */}
        <div className="absolute right-4 bottom-4 flex items-center gap-2">
          {/* Mic button (only if browser supports Web Speech API) */}
          {speechSupported && (
            <button
              type="button"
              onClick={toggleVoiceInput}
              disabled={isLoading || disabled || voiceQuotaExhausted}
              title={voiceQuotaExhausted ? "Voice quota exhausted" : isListening ? "Stop listening" : "Voice input"}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl transition-all"
              style={{
                background: isListening
                  ? "var(--vermillion)"
                  : voiceQuotaExhausted
                  ? "rgba(194,77,44,0.08)"
                  : "rgba(26,58,107,0.04)",
                border: isListening
                  ? "1px solid var(--vermillion-bright)"
                  : voiceQuotaExhausted
                  ? "1px solid rgba(194,77,44,0.25)"
                  : "1px solid var(--glass-border-hover)",
                animation: isListening ? "pulse-ring 1.5s ease-in-out infinite" : undefined,
                opacity: voiceQuotaExhausted ? 0.4 : 1,
                cursor: voiceQuotaExhausted ? "not-allowed" : "pointer",
              }}
              aria-label={isListening ? "Stop listening" : "Voice input"}
            >
              <svg
                className="w-5 h-5"
                style={{ color: isListening ? "#fff" : voiceQuotaExhausted ? "var(--vermillion)" : "var(--gold-dim)" }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4M12 15a3 3 0 003-3V5a3 3 0 00-6 0v7a3 3 0 003 3z"
                />
              </svg>
            </button>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading || disabled || !question.trim()}
            className="flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              width: 48,
              height: 48,
              borderRadius: 16,
              background: "linear-gradient(135deg, var(--krishna-blue), var(--krishna-blue-light))",
              color: "var(--sanctum)",
              boxShadow: "0 2px 8px rgba(26,58,107,0.2)",
              border: "none",
            }}
            aria-label="Search"
          >
            {isLoading ? (
              <svg
                className="w-5 h-5 animate-spin"
                style={{ color: "var(--sanctum)" }}
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                style={{ color: "var(--sanctum)" }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
            )}
          </button>
        </div>
      </form>

      {/* Slot for toggle or other controls */}
      {children}

      {/* Example question cards */}
      <div className="mt-6 grid grid-cols-1 gap-3 max-w-xl mx-auto">
        {EXAMPLE_QUESTIONS.slice(0, 3).map((eq, i) => {
          const accents = ["var(--krishna-blue)", "var(--gold)", "var(--vermillion)"];
          return (
            <button
              key={eq}
              onClick={() => { setQuestion(eq); onSubmit(eq); }}
              disabled={isLoading || disabled}
              className="text-left transition-all duration-200 font-serif disabled:opacity-30"
              style={{
                background: "var(--bg-card-gradient)",
                border: "1px solid var(--glass-border)",
                borderLeft: `3.5px solid ${accents[i % 3]}`,
                borderRadius: 14,
                padding: "18px 20px",
                fontSize: 17,
                color: "var(--text-body)",
                minHeight: 56,
                boxShadow: "var(--shadow-card)",
              }}
            >
              {eq}
            </button>
          );
        })}
      </div>
    </div>
  );
}
