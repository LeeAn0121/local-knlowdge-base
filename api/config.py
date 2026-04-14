from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2:3b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout: int = 120

    # Paths
    docs_path: Path = Path("./data/docs")
    lancedb_path: Path = Path("./data/lancedb")
    tracker_db_path: Path = Path("./data/index_tracker.db")

    # 인덱싱 제외 디렉토리 (쉼표 구분)
    exclude_dirs: str = ".obsidian,.trash,.git,.github,.vscode,__pycache__,node_modules,.templates,templates"

    @property
    def exclude_dirs_set(self) -> set[str]:
        return {d.strip() for d in self.exclude_dirs.split(",") if d.strip()}

    # Chunking
    chunk_max_chars: int = 2000
    chunk_overlap_chars: int = 200
    chunk_min_chars: int = 100

    # Retrieval
    default_top_k: int = 5
    min_similarity_score: float = 0.4

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
