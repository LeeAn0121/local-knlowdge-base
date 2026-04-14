from __future__ import annotations

from pydantic import BaseModel


class Chunk(BaseModel):
    chunk_id: str
    file_path: str
    file_hash: str
    heading_breadcrumb: str
    heading_level: int
    chunk_index: int
    total_chunks_in_section: int
    text: str
    char_start: int
    char_end: int
    vector: list[float] = []

    def to_dict(self) -> dict:
        return self.model_dump()


class IndexRecord(BaseModel):
    file_path: str
    file_hash: str
    mtime: float
    chunk_count: int = 0


class IndexDiff(BaseModel):
    new: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    unchanged: list[str] = []

    @property
    def needs_processing(self) -> list[str]:
        return self.new + self.modified
