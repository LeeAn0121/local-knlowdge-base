"use client";

import { useCallback, useRef, useState } from "react";
import { buildStreamUrl } from "@/lib/api";
import { Message, Source } from "@/lib/types";

type Status = "idle" | "streaming" | "error";

let msgCounter = 0;
const uid = () => String(++msgCounter);

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const esRef = useRef<EventSource | null>(null);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setStatus("idle");
    setMessages((prev) =>
      prev.map((m, i) =>
        i === prev.length - 1 && m.role === "assistant"
          ? { ...m, isStreaming: false }
          : m
      )
    );
  }, []);

  const submit = useCallback(
    (question: string, topK = 8, minScore = 0.2, fileFilter?: string) => {
      if (status === "streaming") return;

      const userMsg: Message = { id: uid(), role: "user", content: question };
      const assistantId = uid();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setStatus("streaming");

      const es = new EventSource(buildStreamUrl(question, topK, minScore, fileFilter));
      esRef.current = es;

      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);

          if (data.type === "token") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + data.content }
                  : m
              )
            );
          } else if (data.type === "sources") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, sources: data.sources as Source[] }
                  : m
              )
            );
          } else if (data.type === "done") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, isStreaming: false } : m
              )
            );
            setStatus("idle");
            es.close();
            esRef.current = null;
          } else if (data.type === "error") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: `오류: ${data.message}`, isStreaming: false }
                  : m
              )
            );
            setStatus("error");
            es.close();
          }
        } catch {
          // ignore parse errors
        }
      };

      es.onerror = () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content || "연결 오류가 발생했습니다.", isStreaming: false }
              : m
          )
        );
        setStatus("error");
        es.close();
        esRef.current = null;
      };
    },
    [status]
  );

  const clear = useCallback(() => {
    stop();
    setMessages([]);
    setStatus("idle");
  }, [stop]);

  return { messages, status, submit, stop, clear };
}
