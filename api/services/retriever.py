from __future__ import annotations

import re
from typing import Any

from indexer.embedder import embed_query
from vectordb.store import VectorStore

# 광범위한 쿼리 감지 패턴 (전체/모든/다 + 요약/정리/알려)
_BROAD_PATTERNS = re.compile(
    r"(전체|모든|모두|다\s|전부|전반|종합|통틀어)",
    re.IGNORECASE,
)
_BROAD_TOP_K_MULTIPLIER = 4  # 일반 top_k의 4배 확장


class Retriever:
    def __init__(self, store: VectorStore, embed_model: str, ollama_host: str):
        self._store = store
        self._embed_model = embed_model
        self._ollama_host = ollama_host

    def search(
        self,
        query: str,
        top_k: int = 8,
        min_score: float = 0.2,
        file_path_filter: str | None = None,
    ) -> list[dict[str, Any]]:
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
