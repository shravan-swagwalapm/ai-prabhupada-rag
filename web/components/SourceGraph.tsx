"use client";

import { useMemo } from "react";
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
import { getScriptureShort, getScriptureSVGColor } from "@/lib/scriptures";

interface SourceGraphProps {
  passages: Passage[];
  question: string;
  selectedIndex: number | null;
  onCardTap: (index: number) => void;
  onCenterTap: () => void;
  compact?: boolean;
  instanceId?: string;
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
  instanceId = "main",
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
          <radialGradient id={`sgGlow-${instanceId}`}>
            <stop offset="0%" stopColor="rgba(201,168,76,0.3)" />
            <stop offset="100%" stopColor="rgba(201,168,76,0)" />
          </radialGradient>
          <radialGradient id={`sgSolid-${instanceId}`}>
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
        <circle cx={cx} cy={cy} r={compact ? 35 : 45} fill={`url(#sgGlow-${instanceId})`} />

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
          const abbrev = p.scripture.toUpperCase();
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
              aria-label={`${shortName}, ${matchPct}% match`}
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
                {abbrev}
              </text>
              <text
                x={pos.x}
                y={pos.y + 2}
                textAnchor="middle"
                fill="rgba(255,255,255,0.35)"
                fontSize={subFontSize}
                fontFamily="Georgia, serif"
              >
                {shortName.length > 14 ? shortName.slice(0, 12) + "…" : shortName}
              </text>
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
          <circle cx={cx} cy={cy} r={compact ? 11 : 14} fill={`url(#sgSolid-${instanceId})`} />
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
