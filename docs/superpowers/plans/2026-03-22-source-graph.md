# Scripture Source Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Sources tab with an interactive lotus card graph that visualizes scripture sources, with tap-to-read detail panel, center-node accordion drawer, and full history persistence.

**Architecture:** SVG graph rendered by React with d3-force computing node positions. Three new components (SourceGraph, SourceDetail, SourceDrawer) replace ScriptureResults in AnswerTabs. Backend stores full passage data and returns it in history.

**Tech Stack:** React 19, Next.js 15, d3-force, SVG, FastAPI, SQLite

**Spec:** `docs/superpowers/specs/2026-03-22-source-graph-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `api/main.py` | modify | Store full passages_json, add chunk_id to SSE, history passthrough, cache passthrough |
| `api/database.py` | modify | Add passages_json to history SELECT |
| `api/models.py` | modify | Add passages_json to HistoryEntry model |
| `web/lib/api.ts` | modify | Add passages_json to HistoryEntry type, add parsePassages helper |
| `web/lib/scriptures.ts` | modify | Add getScriptureSVGColor() for SVG fill/stroke values |
| `web/components/SourceDetail.tsx` | create | Slide-up panel showing single passage with full scrollable text |
| `web/components/SourceDrawer.tsx` | create | Right drawer with accordion cards, one-at-a-time expansion |
| `web/components/SourceGraph.tsx` | create | SVG lotus card graph with d3-force layout |
| `web/components/AnswerTabs.tsx` | modify | Replace ScriptureResults with SourceGraph + SourceDetail + SourceDrawer |
| `web/app/page.tsx` | modify | Pass question prop to AnswerTabs |
| `web/app/history/page.tsx` | modify | Show interactive graph in expanded history entries |
| `web/app/globals.css` | modify | Graph node hover/selected styles |

---

### Task 1: Backend — Store Full Passage Data

**Files:**
- Modify: `api/main.py:559` (POST passages_json)
- Modify: `api/main.py:717-720` (stream passages_json)
- Modify: `api/main.py:635-642` (SSE passages event)
- Modify: `api/main.py:655-656` (stream cache hit)

- [ ] **Step 1: Fix POST passages_json storage (line 559)**

Change:
```python
passages_json = json_module.dumps([{"scripture": r.get("scripture", ""), "text": r.get("text", "")[:200]} for r in relevant_results])
```
To:
```python
passages_json = json_module.dumps([
    {"scripture": r.get("scripture", ""), "text": r.get("text", ""),
     "similarity": round(r.get("similarity", 0.0), 4),
     "chunk_id": str(r.get("chunk_id", ""))}
    for r in relevant_results
])
```

- [ ] **Step 2: Fix stream passages_json storage (lines 717-720)**

Change:
```python
passages_json = json_module.dumps([
    {"scripture": r.get("scripture", ""), "text": r.get("text", "")[:200]}
    for r in raw_results
])
```
To (use `raw_results` to match what the SSE passages event sends to the frontend):
```python
passages_json = json_module.dumps([
    {"scripture": r.get("scripture", ""), "text": r.get("text", ""),
     "similarity": round(r.get("similarity", 0.0), 4),
     "chunk_id": str(r.get("chunk_id", ""))}
    for r in raw_results
])
```

- [ ] **Step 3: Add chunk_id to SSE passages event (lines 635-642)**

Change:
```python
passages = [
    {
        "scripture": r.get("scripture", ""),
        "text": r.get("text", ""),
        "similarity": r.get("similarity", 0.0),
    }
    for r in raw_results
]
```
To:
```python
passages = [
    {
        "scripture": r.get("scripture", ""),
        "text": r.get("text", ""),
        "similarity": r.get("similarity", 0.0),
        "chunk_id": str(r.get("chunk_id", "")),
    }
    for r in raw_results
]
```

- [ ] **Step 4: Emit passages on stream cache hit (after line 655)**

After `if cached:` and the logger.info line, add:
```python
# Re-emit passages so the frontend graph renders on cache hits
cached_passages = json_module.loads(cached.get("passages_json", "[]"))
yield f"data: {json_module.dumps({'type': 'passages', 'data': cached_passages})}\n\n"
```

- [ ] **Step 5: Commit**

```bash
git add api/main.py
git commit -m "fix: store full passage data in passages_json, add chunk_id to SSE, emit passages on cache hit"
```

---

### Task 2: Backend — Expose Passages in History

**Files:**
- Modify: `api/models.py:30-36`
- Modify: `api/database.py:214-215`
- Modify: `api/main.py:364-372`

- [ ] **Step 1: Add passages_json to HistoryEntry model**

In `api/models.py`, add to the `HistoryEntry` class after `audio_id`:
```python
passages_json: Optional[str] = None
```

- [ ] **Step 2: Add passages_json to history SELECT query**

In `api/database.py`, line 215, change:
```sql
SELECT id, question, answer_text, answer_mode, audio_id, created_at
```
To:
```sql
SELECT id, question, answer_text, answer_mode, audio_id, passages_json, created_at
```

- [ ] **Step 3: Pass passages_json through in history endpoint**

In `api/main.py`, lines 364-372, add `passages_json=e.get("passages_json")` to the HistoryEntry constructor:
```python
entries = [
    HistoryEntry(
        id=e["id"],
        question=e["question"],
        answer_text=e["answer_text"],
        answer_mode=e["answer_mode"],
        audio_id=e.get("audio_id"),
        passages_json=e.get("passages_json"),
        created_at=e["created_at"],
    )
    for e in result["entries"]
]
```

- [ ] **Step 4: Commit**

```bash
git add api/models.py api/database.py api/main.py
git commit -m "feat: expose passages_json in history API response"
```

---

### Task 3: Frontend Types + Utilities

**Files:**
- Modify: `web/lib/api.ts:36-43`
- Modify: `web/lib/scriptures.ts`

- [ ] **Step 1: Add passages_json to HistoryEntry type**

In `web/lib/api.ts`, add to the `HistoryEntry` interface after `audio_id`:
```typescript
passages_json: string | null;
```

- [ ] **Step 2: Add parsePassages helper**

In `web/lib/api.ts`, after the `HistoryResponse` interface, add:
```typescript
/** Parse passages_json string from history entries into Passage[]. */
export function parsePassages(json: string | null): Passage[] {
  if (!json) return [];
  try {
    return JSON.parse(json);
  } catch {
    return [];
  }
}
```

- [ ] **Step 3: Add getScriptureSVGColor to scriptures.ts**

At the end of `web/lib/scriptures.ts`, add:
```typescript
/**
 * Get SVG-compatible color values for a scripture.
 * Unlike getScriptureColor() which returns Tailwind classes,
 * this returns raw rgba values for SVG fill/stroke attributes.
 */
export function getScriptureSVGColor(code: string): { fill: string; stroke: string; text: string } {
  const colors: Record<string, { fill: string; stroke: string; text: string }> = {
    bg: { fill: "rgba(251,191,36,0.06)", stroke: "rgba(251,191,36,0.25)", text: "rgba(251,191,36,0.9)" },
    sb: { fill: "rgba(249,115,22,0.06)", stroke: "rgba(249,115,22,0.25)", text: "rgba(249,115,22,0.9)" },
    cc: { fill: "rgba(244,63,94,0.06)", stroke: "rgba(244,63,94,0.25)", text: "rgba(244,63,94,0.9)" },
    nod: { fill: "rgba(236,72,153,0.06)", stroke: "rgba(236,72,153,0.25)", text: "rgba(236,72,153,0.9)" },
    noi: { fill: "rgba(217,70,239,0.06)", stroke: "rgba(217,70,239,0.25)", text: "rgba(217,70,239,0.9)" },
    iso: { fill: "rgba(139,92,246,0.06)", stroke: "rgba(139,92,246,0.25)", text: "rgba(139,92,246,0.9)" },
    kb: { fill: "rgba(52,211,153,0.06)", stroke: "rgba(52,211,153,0.25)", text: "rgba(52,211,153,0.9)" },
    tlc: { fill: "rgba(251,146,60,0.06)", stroke: "rgba(251,146,60,0.25)", text: "rgba(251,146,60,0.9)" },
    tlk: { fill: "rgba(163,230,53,0.06)", stroke: "rgba(163,230,53,0.25)", text: "rgba(163,230,53,0.9)" },
    tqk: { fill: "rgba(45,212,191,0.06)", stroke: "rgba(45,212,191,0.25)", text: "rgba(45,212,191,0.9)" },
    lob: { fill: "rgba(251,191,36,0.06)", stroke: "rgba(251,191,36,0.25)", text: "rgba(251,191,36,0.9)" },
    pop: { fill: "rgba(168,162,158,0.06)", stroke: "rgba(168,162,158,0.25)", text: "rgba(168,162,158,0.9)" },
    letters: { fill: "rgba(56,189,248,0.06)", stroke: "rgba(56,189,248,0.25)", text: "rgba(56,189,248,0.9)" },
  };
  return colors[code.toLowerCase()] || { fill: "rgba(201,168,76,0.06)", stroke: "rgba(201,168,76,0.25)", text: "rgba(201,168,76,0.9)" };
}
```

- [ ] **Step 4: Install d3-force**

```bash
cd web && npm install d3-force && npm install -D @types/d3-force
```

- [ ] **Step 5: Commit**

```bash
git add web/lib/api.ts web/lib/scriptures.ts web/package.json web/package-lock.json
git commit -m "feat: add parsePassages helper, getScriptureSVGColor, install d3-force"
```

---

### Task 4: Create SourceDetail Component

**Files:**
- Create: `web/components/SourceDetail.tsx`

- [ ] **Step 1: Create SourceDetail.tsx**

```typescript
"use client";

import type { Passage } from "@/lib/api";
import { getScriptureName, getScriptureIcon } from "@/lib/scriptures";

interface SourceDetailProps {
  passage: Passage | null;
  onClose: () => void;
}

function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

export default function SourceDetail({ passage, onClose }: SourceDetailProps) {
  if (!passage) return null;

  const fullName = getScriptureName(passage.scripture, passage.chunk_id);
  const icon = getScriptureIcon(passage.scripture);
  const matchPct = (passage.similarity || 0.5) * 100;
  const relevanceColor = getRelevanceColor(matchPct);

  return (
    <div
      className="w-full mt-4 rounded-xl overflow-hidden"
      style={{
        border: "1px solid var(--glass-border)",
        background: "var(--card)",
        animation: "fadeInUp 0.3s ease-out",
      }}
    >
      <div className="max-h-[450px] overflow-y-auto" style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(201,168,76,0.2) transparent" }}>
        {/* Sticky header */}
        <div
          className="flex items-center justify-between px-5 py-4 sticky top-0 z-10"
          style={{
            borderBottom: "1px solid var(--glass-border)",
            background: "var(--card)",
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-lg shrink-0">{icon}</span>
            <div className="min-w-0">
              <p className="text-sm font-serif font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                {fullName.split(",")[0]}
              </p>
              {fullName.includes(",") && (
                <p className="text-[11px] font-sans truncate" style={{ color: "var(--text-muted)" }}>
                  {fullName.substring(fullName.indexOf(",") + 2)}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-11 h-11 min-w-[44px] flex items-center justify-center rounded-lg transition-colors"
            style={{ border: "1px solid var(--glass-border)", color: "var(--text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--glass-border-hover)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; e.currentTarget.style.color = "var(--text-muted)"; }}
            aria-label="Close source detail"
          >
            ✕
          </button>
        </div>

        {/* Relevance bar */}
        <div className="flex items-center gap-2 px-5 py-2">
          <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: "rgba(201,168,76,0.1)" }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(100, matchPct)}%`,
                background: `linear-gradient(to right, var(--vermillion), ${relevanceColor})`,
              }}
            />
          </div>
          <span className="text-[11px] font-sans font-semibold" style={{ color: relevanceColor }}>
            {matchPct.toFixed(0)}%
          </span>
        </div>

        {/* Full passage text — no truncation */}
        <div className="px-5 pb-6">
          <p className="font-serif text-sm" style={{ lineHeight: "1.85", color: "var(--text-body)" }}>
            {passage.text}
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/SourceDetail.tsx
git commit -m "feat: create SourceDetail slide-up panel component"
```

---

### Task 5: Create SourceDrawer Component

**Files:**
- Create: `web/components/SourceDrawer.tsx`

- [ ] **Step 1: Create SourceDrawer.tsx**

```typescript
"use client";

import { useState, useEffect } from "react";
import type { Passage } from "@/lib/api";
import { getScriptureName, getScriptureShort, getScriptureIcon } from "@/lib/scriptures";
import { getScriptureSVGColor } from "@/lib/scriptures";

interface SourceDrawerProps {
  passages: Passage[];
  isOpen: boolean;
  onClose: () => void;
}

function getRelevanceColor(pct: number): string {
  if (pct >= 70) return "var(--tulsi)";
  if (pct >= 50) return "var(--gold)";
  return "var(--text-muted)";
}

export default function SourceDrawer({ passages, isOpen, onClose }: SourceDrawerProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Reset expanded card when drawer opens/closes
  useEffect(() => {
    if (!isOpen) setExpandedIndex(null);
  }, [isOpen]);

  const toggleAccordion = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  // Count unique scriptures
  const uniqueScriptures = new Set(passages.map((p) => p.scripture)).size;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-[100] transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.6)",
          opacity: isOpen ? 1 : 0,
          pointerEvents: isOpen ? "all" : "none",
        }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 bottom-0 z-[101] overflow-y-auto transition-transform duration-300 ease-out"
        style={{
          width: "min(420px, 88vw)",
          background: "var(--sanctum, #0f0c08)",
          borderLeft: "1px solid var(--glass-border)",
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
          scrollbarWidth: "thin",
          scrollbarColor: "rgba(201,168,76,0.2) transparent",
          padding: "24px 20px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-11 h-11 flex items-center justify-center rounded-lg transition-colors"
          style={{ border: "1px solid var(--glass-border)", color: "var(--text-muted)" }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--glass-border-hover)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; }}
          aria-label="Close sources drawer"
        >
          ✕
        </button>

        {/* Header */}
        <p className="text-sm font-serif" style={{ color: "var(--gold)", letterSpacing: "0.06em" }}>
          All Sources
        </p>
        <p className="text-[11px] font-sans mb-5" style={{ color: "var(--text-muted)" }}>
          {passages.length} passages from {uniqueScriptures} scripture{uniqueScriptures !== 1 ? "s" : ""}
        </p>

        {/* Accordion cards */}
        <div className="space-y-2.5">
          {passages.map((p, i) => {
            const isExpanded = expandedIndex === i;
            const shortName = getScriptureShort(p.scripture);
            const fullName = getScriptureName(p.scripture, p.chunk_id);
            const icon = getScriptureIcon(p.scripture);
            const svgColor = getScriptureSVGColor(p.scripture);
            const matchPct = (p.similarity || 0.5) * 100;
            const relevanceColor = getRelevanceColor(matchPct);

            return (
              <div
                key={`${p.scripture}-${p.chunk_id || i}`}
                className="rounded-xl overflow-hidden transition-colors"
                style={{
                  border: `1px solid ${isExpanded ? "var(--glass-border-hover)" : "var(--glass-border)"}`,
                  background: "var(--card)",
                }}
              >
                {/* Header — always visible */}
                <button
                  onClick={() => toggleAccordion(i)}
                  className="w-full text-left px-4 py-3.5 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-base shrink-0">{icon}</span>
                    <div className="min-w-0">
                      <span
                        className="inline-block px-2 py-0.5 rounded-md text-[11px] font-sans font-medium"
                        style={{
                          color: svgColor.text,
                          background: svgColor.fill,
                          border: `1px solid ${svgColor.stroke}`,
                        }}
                      >
                        {shortName}
                      </span>
                      {fullName !== shortName && (
                        <p className="text-[10px] font-sans mt-1 truncate" style={{ color: "var(--text-muted)" }}>
                          {fullName.substring(fullName.indexOf(",") + 2)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-sans font-semibold" style={{ color: "var(--gold-dim)" }}>
                      {matchPct.toFixed(0)}%
                    </span>
                    <span
                      className="text-[10px] transition-transform duration-200"
                      style={{
                        color: "var(--text-muted)",
                        transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                      }}
                    >
                      ▼
                    </span>
                  </div>
                </button>

                {/* Body — expandable */}
                <div
                  className="overflow-hidden transition-all duration-300 ease-out"
                  style={{ maxHeight: isExpanded ? "500px" : "0" }}
                >
                  <div className="px-4 pb-4" style={{ borderTop: "1px solid var(--glass-border)" }}>
                    {/* Relevance bar */}
                    <div className="flex items-center gap-2 py-2.5">
                      <div className="w-14 h-1 rounded-full overflow-hidden" style={{ background: "rgba(201,168,76,0.1)" }}>
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(100, matchPct)}%`,
                            background: `linear-gradient(to right, var(--vermillion), ${relevanceColor})`,
                          }}
                        />
                      </div>
                      <span className="text-[10px] font-sans font-semibold" style={{ color: relevanceColor }}>
                        {matchPct.toFixed(0)}% relevance
                      </span>
                    </div>

                    {/* Full passage text */}
                    <p className="font-serif text-[13px]" style={{ lineHeight: "1.8", color: "var(--text-body)" }}>
                      {p.text}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/SourceDrawer.tsx
git commit -m "feat: create SourceDrawer accordion component"
```

---

### Task 6: Create SourceGraph Component

**Files:**
- Create: `web/components/SourceGraph.tsx`

This is the core component. It uses d3-force to compute positions for lotus card nodes arranged around a golden center node.

- [ ] **Step 1: Create SourceGraph.tsx**

```typescript
"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  forceSimulation,
  forceCenter,
  forceCollide,
  forceManyBody,
  forceLink,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import type { Passage } from "@/lib/api";
import { getScriptureShort, getScriptureName, getScriptureSVGColor } from "@/lib/scriptures";

interface SourceGraphProps {
  passages: Passage[];
  question: string;
  selectedIndex: number | null;
  onCardTap: (index: number) => void;
  onCenterTap: () => void;
  compact?: boolean;
}

interface GraphNode extends SimulationNodeDatum {
  id: string;
  type: "center" | "passage";
  passageIndex?: number;
}

const CARD_W = 100;
const CARD_H = 58;
const COMPACT_SCALE = 0.8;

export default function SourceGraph({
  passages,
  question,
  selectedIndex,
  onCardTap,
  onCenterTap,
  compact = false,
}: SourceGraphProps) {
  const viewW = compact ? 320 : 400;
  const viewH = compact ? 240 : 300;
  const scale = compact ? COMPACT_SCALE : 1;
  const cardW = CARD_W * scale;
  const cardH = CARD_H * scale;

  // Compute positions via d3-force (synchronous, runs once per passage set)
  const nodePositions = useMemo(() => {
    if (passages.length === 0) return [];

    const centerNode: GraphNode = { id: "center", type: "center", x: viewW / 2, y: viewH / 2 };
    const passageNodes: GraphNode[] = passages.map((_, i) => ({
      id: `p-${i}`,
      type: "passage" as const,
      passageIndex: i,
      // Start positions spread radially
      x: viewW / 2 + Math.cos((2 * Math.PI * i) / passages.length - Math.PI / 2) * (viewW * 0.3),
      y: viewH / 2 + Math.sin((2 * Math.PI * i) / passages.length - Math.PI / 2) * (viewH * 0.3),
    }));

    const nodes = [centerNode, ...passageNodes];
    const links: SimulationLinkDatum<GraphNode>[] = passageNodes.map((pn) => ({
      source: centerNode,
      target: pn,
    }));

    const sim = forceSimulation(nodes)
      .force("center", forceCenter(viewW / 2, viewH / 2).strength(0.1))
      .force("collide", forceCollide<GraphNode>((d) => (d.type === "center" ? 20 : Math.max(cardW, cardH) * 0.6)))
      .force("charge", forceManyBody().strength(-80))
      .force("link", forceLink(links).distance(viewW * 0.28).strength(0.5))
      .stop();

    // Run synchronously
    for (let i = 0; i < 120; i++) sim.tick();

    // Clamp positions to keep cards within viewBox with padding
    const pad = 8;
    for (const node of passageNodes) {
      node.x = Math.max(pad + cardW / 2, Math.min(viewW - pad - cardW / 2, node.x!));
      node.y = Math.max(pad + cardH / 2, Math.min(viewH - pad - cardH / 2, node.y!));
    }

    return passageNodes.map((n) => ({ x: n.x!, y: n.y! }));
  }, [passages, viewW, viewH, cardW, cardH]);

  if (passages.length === 0) return null;

  const cx = viewW / 2;
  const cy = viewH / 2;
  const fontSize = compact ? 8 : 10;
  const subFontSize = compact ? 6.5 : 8;
  const pctFontSize = compact ? 7.5 : 9;

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${viewW} ${viewH}`}
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-auto"
        style={{ maxWidth: compact ? 320 : 420 }}
      >
        <defs>
          <radialGradient id="sourceGraphCenterGlow">
            <stop offset="0%" stopColor="rgba(201,168,76,0.3)" />
            <stop offset="100%" stopColor="rgba(201,168,76,0)" />
          </radialGradient>
          <radialGradient id="sourceGraphCenterSolid">
            <stop offset="0%" stopColor="rgba(201,168,76,0.9)" />
            <stop offset="100%" stopColor="rgba(201,168,76,0.5)" />
          </radialGradient>
        </defs>

        {/* Edge lines */}
        {nodePositions.map((pos, i) => (
          <line
            key={`edge-${i}`}
            x1={cx}
            y1={cy}
            x2={pos.x}
            y2={pos.y}
            stroke="rgba(201,168,76,0.15)"
            strokeWidth={selectedIndex === i ? 1.5 : 1}
            style={{
              opacity: selectedIndex === i ? 1 : 0.6 + (passages[i]?.similarity || 0.5) * 0.4,
            }}
          />
        ))}

        {/* Center glow */}
        <circle cx={cx} cy={cy} r={compact ? 35 : 45} fill="url(#sourceGraphCenterGlow)" />

        {/* Center pulse ring */}
        <circle
          cx={cx}
          cy={cy}
          r={compact ? 18 : 22}
          fill="none"
          stroke="rgba(201,168,76,0.2)"
          strokeWidth={0.5}
          className="animate-pulse"
        />

        {/* Lotus cards */}
        {nodePositions.map((pos, i) => {
          const p = passages[i];
          if (!p) return null;
          const svgColor = getScriptureSVGColor(p.scripture);
          const shortName = getScriptureShort(p.scripture);
          const fullName = getScriptureName(p.scripture, p.chunk_id);
          const verseRef = fullName.includes(",") ? fullName.substring(fullName.indexOf(",") + 2) : "";
          const matchPct = ((p.similarity || 0.5) * 100).toFixed(0);
          const isSelected = selectedIndex === i;

          return (
            <g
              key={`card-${i}`}
              className="graph-node-scripture"
              style={isSelected ? { filter: "drop-shadow(0 0 12px rgba(201,168,76,0.5))" } : undefined}
              onClick={() => onCardTap(i)}
              role="button"
              tabIndex={0}
              aria-label={`${shortName}: ${verseRef || "passage"}, ${matchPct}% match`}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onCardTap(i); }}
            >
              <rect
                x={pos.x - cardW / 2}
                y={pos.y - cardH / 2}
                width={cardW}
                height={cardH}
                rx={8}
                fill={svgColor.fill}
                stroke={isSelected ? "rgba(201,168,76,0.6)" : svgColor.stroke}
                strokeWidth={isSelected ? 1.5 : 0.7}
              />
              <text
                x={pos.x}
                y={pos.y - cardH / 6}
                textAnchor="middle"
                fill={svgColor.text}
                fontSize={fontSize}
                fontFamily="Georgia, serif"
                fontWeight="bold"
              >
                {shortName.length > 16 ? shortName.slice(0, 14) + "…" : shortName}
              </text>
              {verseRef && (
                <text
                  x={pos.x}
                  y={pos.y + 2}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.35)"
                  fontSize={subFontSize}
                  fontFamily="Georgia, serif"
                >
                  {verseRef.length > 20 ? verseRef.slice(0, 18) + "…" : verseRef}
                </text>
              )}
              <text
                x={pos.x}
                y={pos.y + cardH / 3}
                textAnchor="middle"
                fill="rgba(201,168,76,0.7)"
                fontSize={pctFontSize}
                fontFamily="-apple-system, sans-serif"
                fontWeight="600"
              >
                {matchPct}%
              </text>
            </g>
          );
        })}

        {/* Center node (tappable) */}
        <g
          style={{ cursor: "pointer" }}
          onClick={onCenterTap}
          role="button"
          tabIndex={0}
          aria-label="View all sources"
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onCenterTap(); }}
        >
          <circle cx={cx} cy={cy} r={compact ? 11 : 14} fill="url(#sourceGraphCenterSolid)" />
          <circle cx={cx} cy={cy} r={compact ? 6 : 8} fill="rgba(201,168,76,0.9)" />
          <text
            x={cx}
            y={cy + (compact ? 20 : 25)}
            textAnchor="middle"
            fill="rgba(201,168,76,0.4)"
            fontSize={compact ? 6 : 7}
            fontFamily="-apple-system, sans-serif"
          >
            view all
          </text>
        </g>
      </svg>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/SourceGraph.tsx
git commit -m "feat: create SourceGraph lotus card component with d3-force layout"
```

---

### Task 7: Wire Components into AnswerTabs

**Files:**
- Modify: `web/components/AnswerTabs.tsx`

- [ ] **Step 1: Replace ScriptureResults with new graph components**

Replace the entire file content of `web/components/AnswerTabs.tsx`:

```typescript
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
        style={{ borderBottom: "1px solid var(--glass-border)" }}
      >
        <button
          onClick={() => setActiveTab("answer")}
          className="relative flex-1 px-4 py-2.5 text-sm transition-all duration-200"
          style={{
            fontFamily: "var(--font-display, 'Cinzel', serif)",
            letterSpacing: "0.04em",
            color: activeTab === "answer" ? "var(--text-primary)" : "var(--text-muted)",
            background: "transparent",
            border: "none",
          }}
        >
          Answer
          {activeTab === "answer" && (
            <span
              className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full"
              style={{ background: "linear-gradient(to right, var(--gold-dim), var(--gold), var(--gold-dim))" }}
            />
          )}
        </button>
        <button
          onClick={() => setActiveTab("sources")}
          className="relative flex-1 px-4 py-2.5 text-sm transition-all duration-200"
          style={{
            fontFamily: "var(--font-display, 'Cinzel', serif)",
            letterSpacing: "0.04em",
            color: activeTab === "sources" ? "var(--text-primary)" : "var(--text-muted)",
            background: "transparent",
            border: "none",
          }}
        >
          Sources{passages.length > 0 ? ` (${passages.length})` : ""}
          {activeTab === "sources" && (
            <span
              className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full"
              style={{ background: "linear-gradient(to right, var(--gold-dim), var(--gold), var(--gold-dim))" }}
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
```

- [ ] **Step 2: Pass question prop from page.tsx**

In `web/app/page.tsx`, find the `<AnswerTabs` component and add `question={currentQuestion}`:

```typescript
<AnswerTabs
  passages={passages}
  answer={answer}
  isStreaming={isStreaming}
  audioId={audioId}
  voiceEnabled={voiceEnabled}
  isSearching={isSearching}
  question={currentQuestion}
/>
```

- [ ] **Step 3: Commit**

```bash
git add web/components/AnswerTabs.tsx web/app/page.tsx
git commit -m "feat: wire SourceGraph + SourceDetail + SourceDrawer into AnswerTabs"
```

---

### Task 8: Add CSS for Graph Nodes

**Files:**
- Modify: `web/app/globals.css`

- [ ] **Step 1: Add graph node styles**

Add to the end of `web/app/globals.css`:

```css
/* Source graph — node interactions */
.graph-node-scripture {
  cursor: pointer;
  transition: filter 0.2s, transform 0.15s;
}
.graph-node-scripture:hover {
  filter: drop-shadow(0 0 6px rgba(201, 168, 76, 0.3));
  transform: scale(1.04);
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/globals.css
git commit -m "style: add graph node hover styles"
```

---

### Task 9: History Integration

**Files:**
- Modify: `web/app/history/page.tsx`

- [ ] **Step 1: Add graph to expanded history entries**

Add imports at top of `web/app/history/page.tsx`:
```typescript
import { parsePassages } from "@/lib/api";
import SourceGraph from "@/components/SourceGraph";
import SourceDetail from "@/components/SourceDetail";
import SourceDrawer from "@/components/SourceDrawer";
```

Add state for graph interaction inside the `HistoryPage` component, after the `expandedId` state:
```typescript
const [selectedHistoryPassage, setSelectedHistoryPassage] = useState<number | null>(null);
const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
```

Add a reset effect when expandedId changes:
```typescript
useEffect(() => {
  setSelectedHistoryPassage(null);
  setHistoryDrawerOpen(false);
}, [expandedId]);
```

In the expanded section (after `<AudioPlayer>`, around line 148), add:
```typescript
{(() => {
  const historyPassages = parsePassages(entry.passages_json);
  if (historyPassages.length === 0) return null;
  return (
    <div className="mt-4">
      <SourceGraph
        passages={historyPassages}
        question={entry.question}
        selectedIndex={selectedHistoryPassage}
        onCardTap={(i) => setSelectedHistoryPassage(selectedHistoryPassage === i ? null : i)}
        onCenterTap={() => setHistoryDrawerOpen(true)}
        compact
      />
      <SourceDetail
        passage={selectedHistoryPassage !== null ? historyPassages[selectedHistoryPassage] : null}
        onClose={() => setSelectedHistoryPassage(null)}
      />
      <SourceDrawer
        passages={historyPassages}
        isOpen={historyDrawerOpen}
        onClose={() => setHistoryDrawerOpen(false)}
      />
    </div>
  );
})()}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/history/page.tsx
git commit -m "feat: show source graph in history expanded entries"
```

---

### Task 10: End-to-End Verification

- [ ] **Step 1: Start backend**

```bash
cd ~/ai-prabhupada-rag && uvicorn api.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```bash
cd ~/ai-prabhupada-rag/web && npm run dev
```

- [ ] **Step 3: Verify SSE includes chunk_id**

Open browser DevTools Network tab, ask a question, filter for `stream`. Check the `passages` SSE event includes `chunk_id` in each passage.

- [ ] **Step 4: Verify graph renders**

Click the "Sources" tab. Confirm:
- Lotus cards appear with correct scripture names, verse refs, and match %
- Cards are color-coded per scripture
- Golden center node pulses
- "view all" label visible below center

- [ ] **Step 5: Verify card tap → detail panel**

Tap a scripture card. Confirm:
- Detail panel slides up below the graph
- Shows full passage text (no truncation), scrollable
- Header shows scripture icon + name + verse ref
- Relevance bar with correct percentage
- Close button works
- Tapping another card swaps the detail

- [ ] **Step 6: Verify center tap → drawer**

Tap the golden center node. Confirm:
- Drawer slides in from right with overlay
- Shows "All Sources" header with count
- Each card is collapsed (badge + ref + %)
- Tapping a card expands it with full text
- Tapping another card collapses the previous (one at a time)
- Overlay click dismisses drawer

- [ ] **Step 7: Verify history**

Go to history page. Expand a saved entry. Confirm:
- Compact source graph renders below the answer
- Card tap and center tap work identically to main page
- Old entries (pre-migration) render gracefully with no crash

- [ ] **Step 8: Verify mobile (375px)**

Resize browser to 375px width. Confirm:
- SVG scales properly
- Cards remain tappable (touch targets)
- Detail panel full width
- Drawer width = 88vw, scrollable
