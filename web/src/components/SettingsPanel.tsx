"use client";

import { useEffect, useRef } from "react";
import { Settings } from "@/hooks/useSettings";
import { Theme } from "@/hooks/useTheme";

interface Props {
  open: boolean;
  onClose: () => void;
  theme: Theme;
  onThemeToggle: () => void;
  settings: Settings;
  onSettingsChange: (partial: Partial<Settings>) => void;
}

export function SettingsPanel({
  open,
  onClose,
  theme,
  onThemeToggle,
  settings,
  onSettingsChange,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("keydown", handleKey);
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        style={{ background: "rgba(0,0,0,0.3)" }}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className="fixed right-0 top-0 bottom-0 z-50 w-72 flex flex-col settings-panel"
        style={{
          background: "var(--bg-header)",
          borderLeft: "1px solid var(--border-subtle)",
          boxShadow: "-8px 0 24px var(--shadow)",
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 shrink-0"
          style={{ borderBottom: "1px solid var(--border-2)" }}
        >
          <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
            설정
          </span>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M2 2l10 10M12 2L2 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6">

          {/* Theme */}
          <Section title="테마">
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: "var(--text-2)" }}>
                {theme === "dark" ? "다크 모드" : "라이트 모드"}
              </span>
              <ThemeToggle theme={theme} onToggle={onThemeToggle} />
            </div>
          </Section>

          {/* Search */}
          <Section title="검색 설정">
            <div className="space-y-4">
              <SliderField
                label="검색 결과 수 (Top-K)"
                value={settings.topK}
                min={1}
                max={20}
                onChange={(v) => onSettingsChange({ topK: v })}
                format={(v) => `${v}개`}
              />
              <SliderField
                label="최소 유사도"
                value={settings.minScore}
                min={0.1}
                max={0.9}
                step={0.05}
                onChange={(v) => onSettingsChange({ minScore: v })}
                format={(v) => `${Math.round(v * 100)}%`}
              />
            </div>
          </Section>
        </div>

        {/* Footer */}
        <div
          className="px-5 py-3 text-xs shrink-0"
          style={{
            borderTop: "1px solid var(--border-2)",
            color: "var(--text-dim)",
          }}
        >
          설정은 자동 저장됩니다
        </div>
      </div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div
        className="text-xs font-medium uppercase tracking-wider"
        style={{ color: "var(--text-muted)" }}
      >
        {title}
      </div>
      {children}
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  format,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  format: (v: number) => string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm" style={{ color: "var(--text-2)" }}>
          {label}
        </span>
        <span
          className="text-xs font-mono px-2 py-0.5 rounded"
          style={{ background: "var(--bg-badge)", color: "var(--accent)" }}
        >
          {format(value)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{ accentColor: "var(--accent)" }}
      />
      <div
        className="flex justify-between text-xs"
        style={{ color: "var(--text-dim)" }}
      >
        <span>{format(min)}</span>
        <span>{format(max)}</span>
      </div>
    </div>
  );
}

function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  const isDark = theme === "dark";
  return (
    <button
      onClick={onToggle}
      className="relative w-12 h-6 rounded-full transition-colors duration-200"
      style={{ background: isDark ? "var(--accent-bg)" : "#d1d5db" }}
      aria-label="테마 전환"
    >
      <span
        className="absolute top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs transition-all duration-200"
        style={{
          background: "white",
          left: isDark ? "calc(100% - 22px)" : "2px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }}
      >
        {isDark ? "🌙" : "☀️"}
      </span>
    </button>
  );
}
