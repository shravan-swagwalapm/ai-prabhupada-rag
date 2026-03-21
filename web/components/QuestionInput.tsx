"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  voiceQuotaExhausted?: boolean;
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
          placeholder="Ask a spiritual question…"
          rows={2}
          maxLength={500}
          disabled={isLoading || disabled || isListening}
          className="w-full px-6 py-5 pr-28 rounded-2xl resize-none disabled:opacity-50 transition-all font-serif text-xl"
          style={{
            background: "var(--altar)",
            border: "2px solid var(--glass-border)",
            color: "var(--text-primary)",
            outline: "none",
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--glass-border-hover)";
            e.currentTarget.style.boxShadow =
              "0 0 0 2px var(--gold-dim), 0 0 16px rgba(201,168,76,0.08)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--glass-border)";
            e.currentTarget.style.boxShadow = "none";
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
                  : "rgba(201,168,76,0.08)",
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
            className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-md"
            style={{
              background: "var(--gold)",
              color: "var(--sanctum)",
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

      {/* Example question pills */}
      <div className="mt-5 flex flex-wrap gap-2.5 justify-center">
        {EXAMPLE_QUESTIONS.map((eq) => (
          <button
            key={eq}
            onClick={() => {
              setQuestion(eq);
              onSubmit(eq);
            }}
            disabled={isLoading || disabled}
            className="px-4 py-2 text-sm rounded-full transition-all duration-200 font-sans disabled:opacity-30 min-h-[44px]"
            style={{
              background: "var(--glass)",
              border: "1px solid var(--gold-dim)",
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--gold)";
              e.currentTarget.style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--gold-dim)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            {eq}
          </button>
        ))}
      </div>
    </div>
  );
}
