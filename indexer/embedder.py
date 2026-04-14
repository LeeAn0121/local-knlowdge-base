"""Ollama 임베딩 (배치 처리, 클라이언트 재사용)."""
from __future__ import annotations

import time
from typing import Generator

import ollama

from vectordb.schema import VECTOR_DIM

DEFAULT_BATCH_SIZE = 64   # 32 → 64: Ollama 처리량에 맞게 증가
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# 클라이언트 캐시: host별 재사용 (매 호출마다 새 객체 생성 방지)
_client_cache: dict[str, ollama.Client] = {}


def _get_client(host: str) -> ollama.Client:
    if host not in _client_cache:
        _client_cache[host] = ollama.Client(host=host)
    return _client_cache[host]


def embed_texts(
    texts: list[str],
    model: str,
    ollama_host: str = "http://localhost:11434",
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[list[float]]:
    """
    텍스트 목록을 배치로 임베딩. float32 벡터 리스트 반환.
    클라이언트 재사용 + 재시도 로직 포함.
    """
    if not texts:
        return []

    client = _get_client(ollama_host)
    vectors: list[list[float]] = []

    for batch in _batches(texts, batch_size):
        for attempt in range(MAX_RETRIES):
            try:
                response = client.embed(model=model, input=batch)
                batch_vectors = response.embeddings
                for vec in batch_vectors:
                    if len(vec) != VECTOR_DIM:
                        raise ValueError(
                            f"벡터 차원 불일치: 예상 {VECTOR_DIM}, 실제 {len(vec)}. "
                            f"임베딩 모델 '{model}' 확인 필요."
                        )
                vectors.extend(batch_vectors)
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY * (attempt + 1)
                    print(f"[임베딩] 재시도 {attempt + 1}/{MAX_RETRIES} ({wait}초 후): {e}")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"임베딩 실패 ({MAX_RETRIES}회 시도): {e}") from e

    return vectors


def embed_query(
    text: str,
    model: str,
    ollama_host: str = "http://localhost:11434",
) -> list[float]:
    """단일 쿼리 임베딩."""
    return embed_texts([text], model=model, ollama_host=ollama_host)[0]


def _batches(items: list, size: int) -> Generator[list, None, None]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
