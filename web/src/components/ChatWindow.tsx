"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

const SUGGESTIONS = [
  "최근에 작성한 내용 요약해줘",
  "프로젝트 진행 상황을 정리해줘",
  "오늘 할 일 목록 있어?",
  "지난주 회의 내용 알려줘",
  "중요한 메모나 아이디어 있어?",
  "가장 많이 다룬 주제가 뭐야?",
];

interface Props {
  messages: Message[];
  onSuggestion: (text: string) => void;
}

export function ChatWindow({ messages, onSuggestion }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-8">
        <div className="text-center space-y-2">
          <div className="text-5xl mb-3">📚</div>
          <p className="font-semibold text-lg" style={{ color: "var(--text)" }}>
            무엇이든 물어보세요
          </p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            지식 베이스에서 관련 내용을 찾아 답변드립니다
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 w-full max-w-xl">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestion(s)}
              className="text-left text-sm px-4 py-3 rounded-xl transition-all"
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border)",
                color: "var(--text-2)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.color = "var(--text)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--text-2)";
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
