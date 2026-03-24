"use client";

import { useState, useEffect } from "react";
import AIAnswer from "@/components/AIAnswer";
import AudioPlayer from "@/components/AudioPlayer";
import SourceGraph from "@/components/SourceGraph";
import SourceDetail from "@/components/SourceDetail";
import SourceDrawer from "@/components/SourceDrawer";
import type { Passage } from "@/lib/api";

interface Props {
  passages: Passage[];
  answer: string;
  isStreaming: boolean;
  audioId: string | null;
  voiceEnabled: boolean;
  isSearching: boolean;
  question: string;
}

type Tab = "answer" | "sources";

export default function AnswerTabs({
  passages,
  answer,
  isStreaming,
  audioId,
  voiceEnabled,
  isSearching,
  question,
}: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("answer");
  const [selectedPassageIndex, setSelectedPassageIndex] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Reset graph state when passages change (new query)
  useEffect(() => {
    setSelectedPassageIndex(null);
    setDrawerOpen(false);
  }, [passages]);

  const hasContent = passages.length > 0 || answer || isStreaming || isSearching;
  if (!hasContent) return null;

  const answerMode = voiceEnabled ? "voice" : "text";

  return (
    <div className="w-full max-w-3xl mx-auto mt-8">
      {/* Tab bar */}
      <div
        className="flex gap-0 mb-6 max-w-xs"
        style={{ borderBottom: "1px solid #D4C9B8" }}
      >
        <button
          onClick={() => setActiveTab("answer")}
          className="relative flex-1 px-4 py-2.5 text-sm transition-all duration-200"
          style={{
            fontFamily: "Georgia, serif",
            letterSpacing: "0.04em",
            color: activeTab === "answer" ? "var(--text-primary)" : "var(--text-muted)",
            background: "transparent",
            border: "none",
            minHeight: 44,
          }}
        >
          Answer
          {activeTab === "answer" && (
            <span
              className="absolute bottom-0 left-0 right-0 rounded-full"
              style={{ background: "#1A3A6B", height: "2.5px" }}
            />
          )}
        </button>
        <button
          onClick={() => setActiveTab("sources")}
          className="relative flex-1 px-4 py-2.5 text-sm transition-all duration-200"
          style={{
            fontFamily: "Georgia, serif",
            letterSpacing: "0.04em",
            color: activeTab === "sources" ? "var(--text-primary)" : "var(--text-muted)",
            background: "transparent",
            border: "none",
            minHeight: 44,
          }}
        >
          Sources{passages.length > 0 ? ` (${passages.length})` : ""}
          {activeTab === "sources" && (
            <span
              className="absolute bottom-0 left-0 right-0 rounded-full"
              style={{ background: "#1A3A6B", height: "2.5px" }}
            />
          )}
        </button>
      </div>

      {/* Tab content */}
      {activeTab === "answer" ? (
        <div className="space-y-4">
          <AIAnswer answer={answer} isStreaming={isStreaming} mode={answerMode} />
          {voiceEnabled && <AudioPlayer audioId={audioId} />}
        </div>
      ) : (
        <div>
          {isSearching ? (
            <div className="flex items-center gap-3 py-8" style={{ color: "var(--text-secondary)" }}>
              <div className="relative w-5 h-5">
                <span className="absolute inset-0 rounded-full animate-ping" style={{ background: "rgba(201,168,76,0.3)" }} />
                <span className="relative block w-5 h-5 rounded-full" style={{ background: "rgba(201,168,76,0.6)" }} />
              </div>
              <span className="font-serif italic">Searching 13 sacred texts...</span>
            </div>
          ) : (
            <>
              <SourceGraph
                passages={passages}
                question={question}
                selectedIndex={selectedPassageIndex}
                onCardTap={(i) => setSelectedPassageIndex(selectedPassageIndex === i ? null : i)}
                onCenterTap={() => setDrawerOpen(true)}
              />
              <SourceDetail
                passage={selectedPassageIndex !== null ? passages[selectedPassageIndex] : null}
                onClose={() => setSelectedPassageIndex(null)}
              />
              <SourceDrawer
                passages={passages}
                isOpen={drawerOpen}
                onClose={() => setDrawerOpen(false)}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}
