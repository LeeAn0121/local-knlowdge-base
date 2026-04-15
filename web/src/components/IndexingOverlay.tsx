"use client";

import { IndexStatus } from "@/lib/types";

interface Props {
  status: IndexStatus;
}

export function IndexingOverlay({ status }: Props) {
  const pct =
    status.total_files > 0
      ? Math.round((status.processed_files / status.total_files) * 100)
      : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center"
      style={{ background: "var(--overlay)", backdropFilter: "blur(6px)" }}
    >
      <div className="flex flex-col items-center gap-6 max-w-sm w-full px-8">
        <div className="relative w-10 h-10">
          <div className="absolute inset-0 rounded-full border-2" style={{ borderColor: "var(--border)" }} />
          <div
            className="absolute inset-0 rounded-full border-2 border-t-transparent animate-spin"
            style={{ borderColor: "var(--accent) transparent transparent transparent" }}
          />
        </div>

        <div className="text-center space-y-1">
          <div className="font-semibold text-sm" style={{ color: "var(--text)" }}>
            인덱싱 중
          </div>
          <div className="text-sm" style={{ color: "var(--text-muted)" }}>
            잠시만 기다려 주세요
          </div>
        </div>

        {status.total_files > 0 && (
          <div className="w-full space-y-2">
            <div className="w-full rounded-full h-1 overflow-hidden" style={{ background: "var(--border)" }}>
              <div
                className="h-1 rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, background: "var(--accent)" }}
              />
            </div>
            <div className="flex justify-between text-xs" style={{ color: "var(--text-dim)" }}>
              <span>{status.processed_files.toLocaleString()} / {status.total_files.toLocaleString()} 파일</span>
              <span>{pct}%</span>
            </div>
          </div>
        )}

        {status.current_file && (
          <div className="w-full text-xs font-mono truncate text-center" style={{ color: "var(--text-dim)" }}>
            {status.current_file}
          </div>
        )}
      </div>
    </div>
  );
}
