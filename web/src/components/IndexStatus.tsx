"use client";

import { useEffect, useRef, useState } from "react";
import { triggerIndex } from "@/lib/api";
import { useIndexStatus } from "@/hooks/useIndexStatus";

export function IndexStatus() {
  const { status, error } = useIndexStatus(3000);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  if (error) {
    return (
      <div className="flex items-center gap-1.5 text-xs" style={{ color: "#ef4444" }}>
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
        API 오프라인
      </div>
    );
  }

  if (!status) return null;

  const isRunning = status.status === "running";
  const isError = status.status === "error";
  const pct =
    status.total_files > 0
      ? Math.round((status.processed_files / status.total_files) * 100)
      : 0;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs transition-colors"
        style={{ color: "var(--text-dim)" }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-dim)")}
      >
        {isRunning ? (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse inline-block" />
            인덱싱 {pct}%
          </>
        ) : isError ? (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
            오류
          </>
        ) : (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
            {status.total_chunks.toLocaleString()}청크
          </>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-7 z-50 rounded-xl text-sm w-60 overflow-hidden"
          style={{
            background: "var(--bg-header)",
            border: "1px solid var(--border)",
            boxShadow: "0 8px 24px var(--shadow)",
          }}
        >
          <div className="px-4 py-2.5" style={{ borderBottom: "1px solid var(--border-2)" }}>
            <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
              인덱스 상태
            </span>
          </div>

          <div className="px-4 py-3 space-y-2">
            <Row label="상태" value={isRunning ? "인덱싱 중" : isError ? "오류" : "정상"} />
            <Row label="파일" value={`${status.total_files.toLocaleString()}개`} />
            <Row label="청크" value={`${status.total_chunks.toLocaleString()}개`} />
            {isRunning && (
              <div className="pt-1">
                <div className="w-full rounded-full h-1 overflow-hidden" style={{ background: "var(--border)" }}>
                  <div
                    className="h-1 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, background: "var(--accent)" }}
                  />
                </div>
                {status.current_file && (
                  <div className="text-xs mt-1.5 truncate font-mono" style={{ color: "var(--text-dim)" }}>
                    {status.current_file}
                  </div>
                )}
              </div>
            )}
            {isError && status.error && (
              <div className="text-xs" style={{ color: "#ef4444" }}>{status.error}</div>
            )}
          </div>

          <div className="px-3 py-2.5 flex gap-2" style={{ borderTop: "1px solid var(--border-2)" }}>
            <ActionBtn label="재인덱싱" onClick={() => { triggerIndex(false); setOpen(false); }} disabled={isRunning} />
            <ActionBtn label="전체 재인덱싱" onClick={() => { triggerIndex(true); setOpen(false); }} disabled={isRunning} />
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span style={{ color: "var(--text-dim)" }}>{label}</span>
      <span style={{ color: "var(--text-2)" }}>{value}</span>
    </div>
  );
}

function ActionBtn({ label, onClick, disabled }: { label: string; onClick: () => void; disabled: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex-1 text-xs py-1.5 rounded-lg transition-colors disabled:opacity-30"
      style={{
        background: "var(--bg-surface)",
        color: "var(--text-muted)",
        border: "1px solid var(--border)",
      }}
      onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.background = "var(--bg-surface-2)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "var(--bg-surface)"; }}
    >
      {label}
    </button>
  );
}
