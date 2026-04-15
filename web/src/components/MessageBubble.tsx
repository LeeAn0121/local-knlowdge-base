"use client";

import { useEffect, useRef } from "react";
import { marked } from "marked";
import { Message } from "@/lib/types";
import { SourceCard } from "./SourceCard";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const htmlRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isUser && htmlRef.current) {
      htmlRef.current.innerHTML = marked.parse(message.content) as string;
    }
  }, [message.content, isUser]);

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[78%] text-sm px-4 py-3 rounded-2xl rounded-tr-sm leading-relaxed"
          style={{
            background: "var(--user-bg)",
            color: "var(--user-text)",
            border: "1px solid var(--user-border)",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-3">
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 mt-0.5"
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          color: "var(--text-muted)",
        }}
      >
        AI
      </div>

      <div className="max-w-[85%] space-y-3 min-w-0">
        {/* Answer bubble */}
        <div
          className="text-sm px-4 py-3 rounded-2xl rounded-tl-sm"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
        >
          {message.content ? (
            <>
              <div ref={htmlRef} className="prose prose-sm max-w-none" />
              {message.isStreaming && <span className="streaming-cursor" />}
            </>
          ) : (
            <span className="text-sm" style={{ color: "var(--text-muted)" }}>
              답변 생성 중<span className="streaming-cursor" />
            </span>
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && !message.isStreaming && (
          <div className="space-y-1.5">
            <div className="text-xs font-medium px-1" style={{ color: "var(--text-dim)" }}>
              참고 문서 {message.sources.length}개
            </div>
            {message.sources.map((s, i) => (
              <SourceCard key={i} source={s} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
