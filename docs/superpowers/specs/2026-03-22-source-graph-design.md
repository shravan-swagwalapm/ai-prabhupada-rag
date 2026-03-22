# Scripture Source Graph — Design Spec

## Problem

PrabhupadaAI returns 5 scripture passages per query, but they're in a separate "Sources" tab that most devotees never click. The passages are the foundation of every answer — they should be visible, explorable, and persisted in history.

## Solution

Replace the Sources tab with an interactive **lotus card graph** that visualizes which scriptures the answer drew from. Each card is tappable to read the full passage. The center node opens a drawer with all sources as an accordion list. History entries persist and display the same graph.

## Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Goal | Visual overview with tap-to-read | Devotees want to quickly see where an answer came from, not build a knowledge graph |
| Placement | Replace Sources tab | Graph IS the sources view — no tab bloat |
| Card tap | Slide-up panel with full passage text | Proven mobile pattern (bottom sheet), graph stays visible above |
| Center tap | Right drawer with accordion cards | All sources stacked, one expandable at a time |
| Visual style | Lotus cards — radial mini-cards around golden center | Informational (book name, verse ref, match %), spiritual aesthetic |
| History | Full interactive graph (compact mode) | Consistent experience, true knowledge archive |
| Rendering | SVG + d3-force (~12KB) | Lightweight, CSS variable access, smart collision avoidance for 5 nodes |
| Performance | Zero impact on answer retrieval | All rendering is frontend-only from existing passage data |

## Component Architecture

```
page.tsx (existing)
  └── AnswerTabs.tsx (modified — 2 tabs: Answer | Sources)
        ├── [Answer tab] → AIAnswer + AudioPlayer (unchanged)
        └── [Sources tab] → SourceGraph.tsx (NEW — replaces ScriptureResults)
                              ├── Lotus card nodes (SVG)
                              ├── Center question node (golden, pulsing)
                              ├── Golden edge lines
                              ├── onCardTap(index) → SourceDetail
                              └── onCenterTap() → SourceDrawer
              SourceDetail.tsx (NEW — slide-up panel, single passage)
              SourceDrawer.tsx (NEW — right drawer, accordion cards)

history/page.tsx (modified)
  └── Per expanded entry:
        └── SourceGraph.tsx (compact=true)
              ├── SourceDetail.tsx
              └── SourceDrawer.tsx
```

### New Components

**SourceGraph.tsx** — SVG graph with d3-force layout
- Center node: golden radial gradient, pulsing ring animation, "view all" label. Tappable → opens SourceDrawer.
- Lotus cards: rectangular SVG `<g>` groups positioned by d3-force. Each shows scripture short name, verse reference, match %. Color-coded per scripture via `getScriptureColor()`. Tappable → opens SourceDetail.
- Edges: golden lines from center to each card, opacity proportional to similarity.
- d3-force simulation: `forceCenter`, `forceCollide`, `forceManyBody(-80)`, `forceLink`. Run 120 ticks synchronously on mount (<1ms for 5 nodes).
- `compact` prop for history view (smaller viewBox, smaller cards).
- Container: `<svg viewBox="0 0 400 300">`, scales responsively.

```typescript
interface SourceGraphProps {
  passages: Passage[];
  question: string;
  selectedIndex: number | null;
  onCardTap: (index: number) => void;
  onCenterTap: () => void;
  compact?: boolean;
}
```

**SourceDetail.tsx** — slide-up panel for a single passage
- Sticky header: scripture icon + full name (via `getScriptureName`) + close button (44px touch target).
- Relevance bar: gradient from vermillion to gold, with percentage label.
- Full passage text: `font-serif`, `line-height: 1.85`, `color: var(--text-body)`. No truncation. Scrollable container with max-height and thin golden scrollbar.
- Animation: `translateY(16px) → translateY(0)` + opacity fade, 0.3s ease-out.

```typescript
interface SourceDetailProps {
  passage: Passage | null;
  onClose: () => void;
}
```

**SourceDrawer.tsx** — right drawer with accordion cards
- Overlay: semi-transparent black, click-to-dismiss.
- Drawer: slides from right, `width: min(420px, 88vw)`, scrollable.
- Header: "All Sources" title + count subtitle + close button (44px).
- Accordion cards: collapsed = scripture badge + verse ref + match %. Expanded = full passage text with relevance bar. One card expandable at a time — tapping a new card collapses the previous.
- Reuses `getScriptureShort`, `getScriptureName`, `getScriptureIcon`, `getScriptureColor` from `scriptures.ts`.

```typescript
interface SourceDrawerProps {
  passages: Passage[];
  isOpen: boolean;
  onClose: () => void;
}
```

### Modified Components

**AnswerTabs.tsx**
- Add `question: string` to Props.
- Change Tab type from `"answer" | "references"` to `"answer" | "sources"`.
- Replace `<ScriptureResults>` with `<SourceGraph>` + `<SourceDetail>` + `<SourceDrawer>`.
- Manage state: `selectedPassageIndex: number | null`, `drawerOpen: boolean`.
- Reset state when passages change.

**page.tsx** — pass `question={currentQuestion}` to `<AnswerTabs>`.

**history/page.tsx**
- Parse `entry.passages_json` via `parsePassages()` helper.
- Render `<SourceGraph compact>` + `<SourceDetail>` + `<SourceDrawer>` in expanded entries.
- Manage `selectedHistoryPassage` and `historyDrawerOpen` state. Reset when `expandedId` changes.
- Graceful degradation for old entries: missing similarity defaults to 0.5, missing chunk_id handled by `getScriptureName`, truncated text displayed as-is.

## Data Flow

```
User asks question
  → SSE stream fires 'passages' event (BEFORE answer)
     Now includes chunk_id (backend fix)
  → React: setPassages(p) — already in page.tsx
  → User clicks "Sources" tab
     SourceGraph renders from passages props
     d3-force computes layout (<1ms)
  → User taps a card → SourceDetail slides up (full text, scrollable)
  → User taps center → SourceDrawer opens (accordion, one-at-a-time)
  → Stream completes → backend saves full passages_json to DB
  → History: fetches entries with passages_json → renders SourceGraph(compact)
```

No new API calls. No blocking. The graph consumes the same `passages` state that already exists.

## Backend Changes

Four surgical edits. No new endpoints, no new computation.

### 1. Store full passage data in `passages_json`

**File**: `api/main.py`, line 559 (POST) and ~line 717 (stream)

Currently truncates text to 200 chars and drops similarity + chunk_id:
```python
# BEFORE
passages_json = json_module.dumps([
    {"scripture": r.get("scripture", ""), "text": r.get("text", "")[:200]}
    for r in relevant_results
])
```

Store complete data:
```python
# AFTER
passages_json = json_module.dumps([
    {"scripture": r.get("scripture", ""), "text": r.get("text", ""),
     "similarity": round(r.get("similarity", 0.0), 4),
     "chunk_id": str(r.get("chunk_id", ""))}
    for r in relevant_results
])
```

~4KB per row for 5 passages — negligible for SQLite.

### 2. Add `chunk_id` to streaming SSE passages event

**File**: `api/main.py`, lines 635-642

Add `"chunk_id": str(r.get("chunk_id", ""))` to the passage dict.

### 3. Return `passages_json` in history

**File**: `api/database.py`, line 214 — add `passages_json` to SELECT.

**File**: `api/models.py`, line 36 — add `passages_json: Optional[str] = None` to HistoryEntry.

**File**: `api/main.py`, lines 364-372 — add `passages_json=e.get("passages_json")` to HistoryEntry constructor.

### 4. Return passages on cache hits

**File**: `api/main.py` — wherever semantic cache hits build a response, include the cached `passages_json`.

## Frontend Type Changes

**File**: `web/lib/api.ts`

```typescript
// Add to HistoryEntry interface
passages_json: string | null;

// New helper
export function parsePassages(json: string | null): Passage[] {
  if (!json) return [];
  try { return JSON.parse(json); } catch { return []; }
}
```

## CSS Additions

**File**: `web/app/globals.css`

```css
.graph-node-scripture {
  cursor: pointer;
  transition: filter 0.2s, transform 0.15s;
}
.graph-node-scripture:hover {
  filter: drop-shadow(0 0 6px rgba(201,168,76,0.3));
  transform: scale(1.04);
}
.graph-node-selected {
  filter: drop-shadow(0 0 12px rgba(201,168,76,0.5));
}
```

## Dependencies

- `d3-force` (~12KB gzipped) — force simulation for node positioning
- `@types/d3-force` (dev only) — TypeScript types

## Reused Utilities (no changes)

- `web/lib/scriptures.ts` — `getScriptureName`, `getScriptureShort`, `getScriptureIcon`, `getScriptureColor`
- `web/components/ScriptureResults.tsx` — reference for relevance bar pattern (component itself is replaced, not deleted yet)

## Files Summary

| File | Action | What |
|------|--------|------|
| `api/main.py` | modify | Store full passages_json, add chunk_id to SSE, history passthrough, cache passthrough |
| `api/database.py` | modify | Add passages_json to history SELECT |
| `api/models.py` | modify | Add passages_json to HistoryEntry |
| `web/lib/api.ts` | modify | Add passages_json to HistoryEntry type, add parsePassages helper |
| `web/components/SourceGraph.tsx` | create | SVG lotus card graph with d3-force |
| `web/components/SourceDetail.tsx` | create | Slide-up panel for single passage |
| `web/components/SourceDrawer.tsx` | create | Right drawer with accordion cards |
| `web/components/AnswerTabs.tsx` | modify | Replace ScriptureResults with SourceGraph + SourceDetail + SourceDrawer |
| `web/app/page.tsx` | modify | Pass question to AnswerTabs |
| `web/app/history/page.tsx` | modify | Show graph in expanded history entries |
| `web/app/globals.css` | modify | Graph node hover/selected styles |

## Verification

1. Ask a question → verify SSE passages include chunk_id
2. Click Sources tab → verify lotus card graph renders with correct colors and verse refs
3. Tap a card → detail panel slides up with full scrollable text
4. Tap center node → drawer opens with accordion cards, one-at-a-time expansion
5. Go to history → verify saved entry shows compact graph with working interactions
6. Check an old history entry → verify graceful degradation (no crash)
7. Test at 375px width → verify 44px touch targets, SVG scales, drawer fits
