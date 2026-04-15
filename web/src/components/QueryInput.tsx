"use client";

import { KeyboardEvent, useRef, useState } from "react";

interface Props {
  onSubmit: (text: string, fileFilter?: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function QueryInput({ onSubmit, onStop, isStreaming, disabled }: Props) {
  const [text, setText] = useState("");
  const [fileFilter, setFileFilter] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSubmit() {
    const trimmed = text.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSubmit(trimmed, fileFilter.trim() || undefined);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
    }
  }

  const canSubmit = !!text.trim() && !isStreaming && !disabled;
  const hasFilter = !!fileFilter.trim();

  return (
    <div className="shrink-0 px-4 pb-4 pt-3" style={{ borderTop: "1px solid var(--border-2)" }}>

      {/* 파일 필터 입력 (토글) */}
      {filterOpen && (
        <div className="mb-2 flex items-center gap-2">
          <span className="text-xs shrink-0" style={{ color: "var(--text-muted)" }}>
            폴더/파일 필터
          </span>
          <input
            type="text"
            value={fileFilter}
            onChange={(e) => setFileFilter(e.target.value)}
            placeholder="예: 업무일지, 회의록, 프로젝트명…"
            className="flex-1 text-xs px-3 py-1.5 rounded-lg focus:outline-none"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
          />
          {hasFilter && (
            <button
              onClick={() => setFileFilter("")}
              className="text-xs shrink-0"
              style={{ color: "var(--text-dim)" }}
            >
              지우기
            </button>
          )}
        </div>
      )}

      {/* 입력창 */}
      <div
        className="flex items-end gap-2 rounded-2xl px-3 py-2"
        style={{
          background: "var(--bg-input)",
          border: `1px solid ${hasFilter ? "var(--accent)" : "var(--border)"}`,
        }}
      >
        {/* 필터 토글 버튼 */}
        <button
          onClick={() => setFilterOpen((o) => !o)}
          className="shrink-0 w-6 h-6 rounded-lg flex items-center justify-center mb-0.5 transition-colors"
          style={{
            color: filterOpen || hasFilter ? "var(--accent)" : "var(--text-dim)",
            background: filterOpen || hasFilter ? "var(--accent-dim)" : "transparent",
          }}
          title="폴더/파일 범위 지정"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <path d="M1 3h10M3 6h6M5 9h2" />
          </svg>
        </button>

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={
            disabled
              ? "인덱싱 중입니다. 잠시만 기다려 주세요…"
              : hasFilter
              ? `"${fileFilter}" 범위에서 검색…`
              : "질문을 입력하세요… (Shift+Enter 줄바꿈)"
          }
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm focus:outline-none max-h-[180px] overflow-y-auto leading-relaxed"
          style={{ color: "var(--text)" }}
        />

        {isStreaming ? (
          <button
            onClick={onStop}
            className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-colors mb-0.5"
            style={{ background: "#7f1d1d", color: "#fca5a5" }}
            title="생성 중지"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
              <rect x="1" y="1" width="10" height="10" rx="2" />
            </svg>
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all mb-0.5"
            style={{
              background: canSubmit ? "var(--accent-bg)" : "var(--bg-badge)",
              color: canSubmit ? "var(--accent)" : "var(--text-dim)",
            }}
            title="전송 (Enter)"
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 7.5H2M8 3l5 4.5-5 4.5" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
