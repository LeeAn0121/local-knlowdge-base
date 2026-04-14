from __future__ import annotations

from datetime import datetime
from typing import Any


def build_prompt(
    question: str,
    chunks: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """
    Build the messages list for Ollama chat API.
    Returns [system, ...history, user] messages.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        breadcrumb = chunk.get("heading_breadcrumb", "")
        file_path = chunk.get("file_path", "")
        text = chunk.get("text", "")
        # Include heading as a header in the chunk body for better LLM comprehension
        heading_line = f"### {breadcrumb}\n" if breadcrumb and breadcrumb != "(intro)" else ""
        context_parts.append(
            f"[Source {i}: {file_path}]\n{heading_line}{text}"
        )

    context_str = "\n\n---\n\n".join(context_parts)

    today = datetime.now().strftime("%Y년 %m월 %d일 (%A)").replace(
        "Monday", "월요일").replace("Tuesday", "화요일").replace(
        "Wednesday", "수요일").replace("Thursday", "목요일").replace(
        "Friday", "금요일").replace("Saturday", "토요일").replace(
        "Sunday", "일요일")

    system_prompt = (
        f"오늘 날짜: {today}\n\n"
        "당신은 한국어 지식 베이스 어시스턴트입니다.\n\n"
        "## 답변 규칙\n"
        "- 반드시 한국어로만 답변하세요.\n"
        "- 컨텍스트를 기반으로 답변하되, 작은 빈틈은 일반 지식으로 보완해도 됩니다.\n"
        "- 컨텍스트에 없는 내용은 명확히 '관련 문서에서 찾을 수 없습니다'라고 하세요.\n\n"
        "## 출력 형식\n"
        "- 마크다운을 적극 활용하세요 (헤딩, 목록, 굵게 등).\n"
        "- 여러 항목은 반드시 bullet list (`-`) 또는 numbered list로 정리하세요.\n"
        "- 날짜/항목별로 나뉘는 내용은 `### 날짜` 형식의 소제목을 사용하세요.\n"
        "- 불필요한 반복이나 장황한 서두 없이 핵심만 간결하게 작성하세요.\n"
        "- 출처 인용 시 `[Source N]` 형식을 사용하세요.\n\n"
        f"=== 컨텍스트 ===\n{context_str}\n=== 컨텍스트 끝 ==="
    )

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": question})
    return messages


def format_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format retrieved chunks into source citation objects."""
    sources = []
    seen = set()
    for chunk in chunks:
        key = (chunk.get("file_path", ""), chunk.get("heading_breadcrumb", ""))
        if key in seen:
            continue
        seen.add(key)
        text = chunk.get("text", "")
        sources.append({
            "file_path": chunk.get("file_path", ""),
            "heading": chunk.get("heading_breadcrumb", ""),
            "excerpt": text[:200] + ("..." if len(text) > 200 else ""),
            "score": chunk.get("score", 0.0),
        })
    return sources
