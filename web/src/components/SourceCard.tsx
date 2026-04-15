"use client";

import { useState } from "react";
import { Source } from "@/lib/types";

interface Props {
  source: Source;
  index: number;
}

function fileName(path: string): string {
  return path.split("/").pop()?.replace(/\.md$/, "") ?? path;
}

function dirPath(path: string): string {
  const parts = path.split("/");
  return parts.length > 1 ? parts.slice(0, -1).join("/") : "";
}

export function SourceCard({ source, index }: Props) {
  const [expanded, setExpanded] = useState(false);

  const score = source.score;
  const scoreStyle =
    score >= 0.55
      ? { bg: "rgba(16,185,129,0.1)", text: "#34d399", border: "rgba(16,185,129,0.2)" }
      : score >= 0.35
      ? { bg: "rgba(251,191,36,0.1)", text: "#fbbf24", border: "rgba(251,191,36,0.2)" }
      : { bg: "rgba(251,146,60,0.1)", text: "#fb923c", border: "rgba(251,146,60,0.2)" };

  const dir = dirPath(source.file_path);

  return (
    <div
      className="rounded-xl text-sm overflow-hidden"
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="flex items-center gap-2 px-3 py-2.5">
        {/* Index badge */}
        <span
          className="shrink-0 w-5 h-5 rounded-md flex items-center justify-center text-xs font-medium"
          style={{ background: "var(--bg-badge)", color: "var(--text-muted)" }}
        >
          {index}
        </span>

        {/* File info */}
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate" style={{ color: "var(--text)" }}>
            {fileName(source.file_path)}
          </div>
          {dir && (
            <div className="text-xs truncate mt-0.5" style={{ color: "var(--text-dim)" }}>
              {dir}
            </div>
          )}
          {source.heading && source.heading !== "(intro)" && (
            <div className="text-xs truncate mt-0.5" style={{ color: "var(--accent)" }}>
              § {source.heading}
            </div>
          )}
        </div>

        {/* Score */}
        <span
          className="shrink-0 text-xs px-2 py-0.5 rounded-md font-medium"
          style={{
            background: scoreStyle.bg,
            color: scoreStyle.text,
            border: `1px solid ${scoreStyle.border}`,
          }}
        >
          {Math.round(score * 100)}%
        </span>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded((e) => !e)}
          className="shrink-0 transition-colors"
          style={{ color: "var(--text-dim)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-dim)")}
          title={expanded ? "접기" : "내용 보기"}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.15s" }}
          >
            <path d="M3 5l4 4 4-4" />
          </svg>
        </button>
      </div>

      {expanded && source.excerpt && (
        <div
          className="px-3 pb-3 pt-2.5 text-xs font-mono leading-relaxed whitespace-pre-wrap"
          style={{
            color: "var(--text-muted)",
            borderTop: "1px solid var(--border-2)",
          }}
        >
          {source.excerpt}
        </div>
      )}
    </div>
  );
}
