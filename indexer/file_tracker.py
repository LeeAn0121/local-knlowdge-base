"""SQLite-based file change tracker for incremental indexing."""
from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from indexer.models import IndexDiff, IndexRecord

# Obsidian 및 일반적으로 제외할 디렉토리
DEFAULT_EXCLUDE_DIRS: set[str] = {
    ".obsidian",
    ".trash",
    ".git",
    ".github",
    ".vscode",
    "__pycache__",
    "node_modules",
    ".templates",
    "templates",
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS file_records (
    file_path   TEXT PRIMARY KEY,
    file_hash   TEXT NOT NULL,
    mtime       REAL NOT NULL,
    indexed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER DEFAULT 0
);
"""


class FileTracker:
    def __init__(self, db_path: str | Path):
        self._db_path = str(db_path)
        with self._conn() as conn:
            conn.execute(CREATE_TABLE_SQL)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------ hash

    @staticmethod
    def hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------ diff

    def compute_diff(
        self,
        docs_root: Path,
        exclude_dirs: set[str] | None = None,
    ) -> IndexDiff:
        """
        Scan docs_root for .md files and compare against stored records.
        Returns categorized diff (new, modified, deleted, unchanged).
        """
        if exclude_dirs is None:
            exclude_dirs = DEFAULT_EXCLUDE_DIRS

        md_files = {
            str(p.relative_to(docs_root)).replace("\\", "/"): p
            for p in docs_root.rglob("*.md")
            if not any(part in exclude_dirs for part in p.parts)
        }

        with self._conn() as conn:
            stored: dict[str, IndexRecord] = {}
            for row in conn.execute("SELECT * FROM file_records"):
                stored[row["file_path"]] = IndexRecord(
                    file_path=row["file_path"],
                    file_hash=row["file_hash"],
                    mtime=row["mtime"],
                    chunk_count=row["chunk_count"] or 0,
                )

        diff = IndexDiff()

        for rel_path, abs_path in md_files.items():
            mtime = os.path.getmtime(abs_path)
            if rel_path not in stored:
                diff.new.append(rel_path)
            else:
                rec = stored[rel_path]
                if abs(mtime - rec.mtime) < 0.01:
                    diff.unchanged.append(rel_path)
                else:
                    # mtime changed — verify with hash
                    current_hash = self.hash_file(abs_path)
                    if current_hash != rec.file_hash:
                        diff.modified.append(rel_path)
                    else:
                        diff.unchanged.append(rel_path)

        for rel_path in stored:
            if rel_path not in md_files:
                diff.deleted.append(rel_path)

        return diff

    # ------------------------------------------------------------------ update

    def update_record(self, rel_path: str, abs_path: Path, chunk_count: int) -> None:
        file_hash = self.hash_file(abs_path)
        mtime = os.path.getmtime(abs_path)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO file_records (file_path, file_hash, mtime, chunk_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_hash=excluded.file_hash,
                    mtime=excluded.mtime,
                    chunk_count=excluded.chunk_count,
                    indexed_at=CURRENT_TIMESTAMP
                """,
                (rel_path, file_hash, mtime, chunk_count),
            )

    def delete_record(self, rel_path: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM file_records WHERE file_path = ?", (rel_path,))

    def get_record(self, rel_path: str) -> IndexRecord | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM file_records WHERE file_path = ?", (rel_path,)
            ).fetchone()
            if row is None:
                return None
            return IndexRecord(
                file_path=row["file_path"],
                file_hash=row["file_hash"],
                mtime=row["mtime"],
                chunk_count=row["chunk_count"] or 0,
            )

    def total_files(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM file_records").fetchone()[0]

    def total_chunks(self) -> int:
        with self._conn() as conn:
            result = conn.execute("SELECT SUM(chunk_count) FROM file_records").fetchone()[0]
            return result or 0
