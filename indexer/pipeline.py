"""Orchestrates the full indexing pipeline."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from indexer.chunker import chunk_file_from_path
from indexer.embedder import embed_texts
from indexer.file_tracker import DEFAULT_EXCLUDE_DIRS, FileTracker
from indexer.models import IndexDiff
from vectordb.store import VectorStore


class IndexStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class IndexProgress:
    status: IndexStatus = IndexStatus.IDLE
    total_files: int = 0
    processed_files: int = 0
    current_file: str | None = None
    total_chunks: int = 0
    error: str | None = None
    last_diff: IndexDiff | None = None


class IndexPipeline:
    def __init__(
        self,
        docs_path: str | Path,
        db_path: str | Path,
        tracker_db_path: str | Path,
        embed_model: str,
        ollama_host: str = "http://localhost:11434",
        chunk_max_chars: int = 2000,
        chunk_overlap_chars: int = 200,
        chunk_min_chars: int = 100,
        batch_size: int = 64,
        exclude_dirs: set[str] | None = None,
    ):
        self.docs_path = Path(docs_path)
        self.embed_model = embed_model
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else DEFAULT_EXCLUDE_DIRS
        self.ollama_host = ollama_host
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self.chunk_min_chars = chunk_min_chars
        self.batch_size = batch_size

        self._store = VectorStore(db_path)
        self._tracker = FileTracker(tracker_db_path)
        self._progress = IndexProgress()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    @property
    def progress(self) -> IndexProgress:
        with self._lock:
            return IndexProgress(
                status=self._progress.status,
                total_files=self._progress.total_files,
                processed_files=self._progress.processed_files,
                current_file=self._progress.current_file,
                total_chunks=self._progress.total_chunks,
                error=self._progress.error,
                last_diff=self._progress.last_diff,
            )

    @property
    def store(self) -> VectorStore:
        return self._store

    def warm_store_async(self) -> None:
        self._store.warmup_async()

    @property
    def tracker(self) -> FileTracker:
        return self._tracker

    def is_running(self) -> bool:
        return self._progress.status == IndexStatus.RUNNING

    # ------------------------------------------------------------------ 핵심: 파일 처리

    def _process_files(self, files_to_process: list[str], deleted: list[str]) -> None:
        """
        지정된 파일 목록만 처리. compute_diff 없이 바로 인덱싱.
        watcher에서 변경된 파일만 넘겨줄 때 사용 (전체 스캔 없음).
        """
        # 삭제된 파일 제거
        for rel_path in deleted:
            self._store.delete_by_file_path(rel_path)
            self._tracker.delete_record(rel_path)

        if not files_to_process:
            return

        # 파일별 청크 수집 (배치 임베딩을 위해 모두 모음)
        all_chunks = []
        file_chunk_map: dict[str, int] = {}  # rel_path → chunk 개수

        for i, rel_path in enumerate(files_to_process):
            abs_path = self.docs_path / rel_path.replace("/", "\\")

            with self._lock:
                self._progress.current_file = rel_path
                self._progress.processed_files = i

            try:
                file_hash = self._tracker.hash_file(abs_path)
                chunks = chunk_file_from_path(
                    path=abs_path,
                    file_hash=file_hash,
                    docs_root=self.docs_path,
                    max_chars=self.chunk_max_chars,
                    overlap_chars=self.chunk_overlap_chars,
                    min_chars=self.chunk_min_chars,
                )
                file_chunk_map[rel_path] = len(chunks)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[인덱서] 청킹 오류 {rel_path}: {e}")
                file_chunk_map[rel_path] = 0

        # 배치 임베딩 (파일별이 아닌 전체 청크를 한번에)
        # 헤딩 컨텍스트를 임베딩 텍스트에 포함 → 의미 검색 품질 향상
        if all_chunks:
            texts = [
                f"{c.heading_breadcrumb}\n\n{c.text}"
                if c.heading_breadcrumb and c.heading_breadcrumb != "(intro)"
                else c.text
                for c in all_chunks
            ]
            try:
                vectors = embed_texts(
                    texts,
                    model=self.embed_model,
                    ollama_host=self.ollama_host,
                    batch_size=self.batch_size,
                )
            except Exception as e:
                print(f"[인덱서] 임베딩 오류: {e}")
                return

            # 기존 청크 삭제 후 새 청크 upsert
            processed_files = {c.file_path for c in all_chunks}
            for fp in processed_files:
                self._store.delete_by_file_path(fp)

            records = [
                {**chunk.to_dict(), "vector": vec}
                for chunk, vec in zip(all_chunks, vectors)
            ]
            self._store.upsert_chunks(records)

        # tracker 업데이트
        for rel_path in files_to_process:
            abs_path = self.docs_path / rel_path.replace("/", "\\")
            if abs_path.exists():
                self._tracker.update_record(rel_path, abs_path, file_chunk_map.get(rel_path, 0))

    # ------------------------------------------------------------------ 전체 인덱싱

    def run(
        self,
        force: bool = False,
        on_progress: Callable[[IndexProgress], None] | None = None,
    ) -> IndexProgress:
        """전체 인덱싱 (compute_diff로 변경 파일 탐지 후 처리)."""
        with self._lock:
            if self._progress.status == IndexStatus.RUNNING:
                raise RuntimeError("이미 인덱싱 중입니다")
            self._progress = IndexProgress(status=IndexStatus.RUNNING)

        try:
            diff = self._tracker.compute_diff(self.docs_path, exclude_dirs=self.exclude_dirs)
            if force:
                all_files = diff.new + diff.modified + diff.unchanged
                diff.new = all_files
                diff.modified = []
                diff.unchanged = []

            with self._lock:
                self._progress.last_diff = diff
                self._progress.total_files = len(diff.needs_processing)

            self._process_files(diff.needs_processing, diff.deleted)

            total = self._store.count()
            with self._lock:
                self._progress.status = IndexStatus.IDLE
                self._progress.current_file = None
                self._progress.processed_files = len(diff.needs_processing)
                self._progress.total_chunks = total

            self._store.rebuild_index()
            print(f"[인덱서] 완료: {len(diff.needs_processing)}개 파일, 총 {total}개 청크")

        except Exception as e:
            with self._lock:
                self._progress.status = IndexStatus.ERROR
                self._progress.error = str(e)
            print(f"[인덱서] 오류: {e}")

        return self.progress

    # ------------------------------------------------------------------ 파일 지정 인덱싱 (watcher용)

    def run_files(self, changed: list[str], deleted: list[str] | None = None) -> IndexProgress:
        """
        특정 파일만 재인덱싱. compute_diff 전체 스캔 없이 즉시 처리.
        watcher가 변경된 파일 경로를 직접 넘겨줄 때 사용.
        """
        with self._lock:
            if self._progress.status == IndexStatus.RUNNING:
                return self.progress
            self._progress = IndexProgress(
                status=IndexStatus.RUNNING,
                total_files=len(changed),
            )

        try:
            self._process_files(changed, deleted or [])

            total = self._store.count()
            with self._lock:
                self._progress.status = IndexStatus.IDLE
                self._progress.current_file = None
                self._progress.processed_files = len(changed)
                self._progress.total_chunks = total

            print(f"[인덱서] 파일 업데이트: {len(changed)}개, 총 {total}개 청크")

        except Exception as e:
            with self._lock:
                self._progress.status = IndexStatus.ERROR
                self._progress.error = str(e)
            print(f"[인덱서] 오류: {e}")

        return self.progress

    # ------------------------------------------------------------------ 비동기 실행

    def run_async(self, force: bool = False) -> None:
        """백그라운드 스레드에서 전체 인덱싱."""
        if self.is_running():
            return
        self._thread = threading.Thread(target=self.run, args=(force,), daemon=True)
        self._thread.start()

    def run_files_async(self, changed: list[str], deleted: list[str] | None = None) -> None:
        """백그라운드 스레드에서 파일 지정 인덱싱 (재기동 불필요)."""
        if self.is_running():
            return
        self._thread = threading.Thread(
            target=self.run_files, args=(changed, deleted), daemon=True
        )
        self._thread.start()
