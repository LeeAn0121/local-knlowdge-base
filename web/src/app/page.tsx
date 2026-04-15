"use client";

import { useState } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { IndexStatus } from "@/components/IndexStatus";
import { IndexingOverlay } from "@/components/IndexingOverlay";
import { QueryInput } from "@/components/QueryInput";
import { SettingsPanel } from "@/components/SettingsPanel";
import { useChat } from "@/hooks/useChat";
import { useIndexStatus } from "@/hooks/useIndexStatus";
import { useSettings } from "@/hooks/useSettings";
import { useTheme } from "@/hooks/useTheme";

export default function Home() {
  const { messages, status, submit, stop, clear } = useChat();
  const { status: indexStatus } = useIndexStatus(2000);
  const { theme, toggle } = useTheme();
  const { settings, update: updateSettings } = useSettings();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isStreaming = status === "streaming";
  const isIndexing = indexStatus?.status === "running";

  function handleSubmit(text: string, fileFilter?: string) {
    submit(text, settings.topK, settings.minScore, fileFilter);
  }

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--bg)" }}>
      {isIndexing && indexStatus && <IndexingOverlay status={indexStatus} />}

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        theme={theme}
        onThemeToggle={toggle}
        settings={settings}
        onSettingsChange={updateSettings}
      />

      {/* Header */}
      <header
        className="shrink-0 flex items-center justify-between px-5 py-3"
        style={{
          background: "var(--bg-header)",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-sm"
            style={{ background: "var(--accent-dim)", border: "1px solid var(--border)" }}
          >
            📚
          </div>
          <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
            지식 베이스
          </span>
        </div>

        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              onClick={clear}
              className="text-xs transition-colors"
              style={{ color: "var(--text-dim)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-dim)")}
            >
              초기화
            </button>
          )}
          <IndexStatus />
          {/* Settings button */}
          <button
            onClick={() => setSettingsOpen(true)}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors"
            style={{
              background: settingsOpen ? "var(--bg-surface)" : "transparent",
              color: "var(--text-muted)",
              border: "1px solid transparent",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--bg-surface)";
              e.currentTarget.style.borderColor = "var(--border)";
            }}
            onMouseLeave={(e) => {
              if (!settingsOpen) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.borderColor = "transparent";
              }
            }}
            title="설정"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <circle cx="7" cy="7" r="2" />
              <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13M2.93 2.93l1.06 1.06M10.01 10.01l1.06 1.06M2.93 11.07l1.06-1.06M10.01 3.99l1.06-1.06" />
            </svg>
          </button>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden max-w-3xl w-full mx-auto">
        <ChatWindow messages={messages} onSuggestion={handleSubmit} />
        <QueryInput
          onSubmit={handleSubmit}
          onStop={stop}
          isStreaming={isStreaming}
          disabled={isIndexing}
        />
      </div>
    </div>
  );
}
