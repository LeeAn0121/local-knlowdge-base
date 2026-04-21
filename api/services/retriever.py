from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# 광범위한 쿼리 감지 패턴 (전체/모든/다 + 요약/정리/알려)
_BROAD_PATTERNS = re.compile(
    r"(전체|모든|모두|다\s|전부|전반|종합|통틀어)",
    re.IGNORECASE,
)
_BROAD_TOP_K_MULTIPLIER = 4  # 일반 top_k의 4배 확장


class Retriever:
    def __init__(self, store: Any, embed_model: str, ollama_host: str, docs_path: str | Path | None = None):
        self._store = store
        self._embed_model = embed_model
        self._ollama_host = ollama_host
        self._docs_path = Path(docs_path) if docs_path is not None else None

    def search(
        self,
        query: str,
        top_k: int = 8,
        min_score: float = 0.2,
        file_path_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        if hasattr(self._store, "is_ready") and not self._store.is_ready():
            return self._filesystem_search(query, top_k=top_k, file_path_filter=file_path_filter)

        from indexer.embedder import embed_query

        # 광범위한 쿼리면 더 많은 청크 검색
        effective_top_k = top_k
        if _BROAD_PATTERNS.search(query):
            effective_top_k = min(top_k * _BROAD_TOP_K_MULTIPLIER, 50)

        vec = embed_query(query, model=self._embed_model, ollama_host=self._ollama_host)
        return self._store.search(
            vec,
            top_k=effective_top_k,
            min_score=min_score,
            file_path_filter=file_path_filter,
        )

    def _filesystem_search(
        self,
        query: str,
        top_k: int = 8,
        file_path_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._docs_path is None or not self._docs_path.exists():
            return []

        tokens = self._make_tokens(query)
        candidates: list[dict[str, Any]] = []

        for path in self._docs_path.rglob("*.md"):
            rel_path = str(path.relative_to(self._docs_path)).replace("\\", "/")
            rel_lower = rel_path.lower()

            if file_path_filter and file_path_filter.lower() not in rel_lower:
                continue

            score = 0
            for token in tokens:
                if token in rel_lower:
                    score += 5

            if score == 0 and not any(k in query for k in ("업무일지", "일지", "주간보고")):
                continue

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8-sig")
            except Exception:
                continue

            text_lower = text.lower()
            for token in tokens:
                if token in text_lower:
                    score += 2

            if score <= 0:
                continue

            excerpt = self._best_excerpt(text, tokens)
            candidates.append(
                {
                    "file_path": rel_path,
                    "heading_breadcrumb": "(fallback)",
                    "text": excerpt,
                    "score": min(0.99, 0.3 + (score * 0.05)),
                }
            )

        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[:top_k]

    def _make_tokens(self, query: str) -> list[str]:
        q = query.lower()
        tokens = set(re.findall(r"[0-9a-z가-힣:/-]+", q))

        for month, day in re.findall(r"(\d{1,2})\s*/\s*(\d{1,2})", q):
            mm = int(month)
            dd = int(day)
            tokens.add(f"{mm}/{dd}")
            tokens.add(f"{mm:02d}-{dd:02d}")
            tokens.add(f"2026-{mm:02d}-{dd:02d}")

        return [t for t in tokens if len(t) >= 2]

    def _best_excerpt(self, text: str, tokens: list[str]) -> str:
        for line in text.splitlines():
            line_lower = line.lower()
            if any(token in line_lower for token in tokens):
                return line.strip()[:300]
        compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
        return compact[:300]
