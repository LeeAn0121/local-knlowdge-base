from __future__ import annotations

import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from api.config import get_settings
from api.routers import chat, health, index, search

DEBOUNCE_SECONDS = 5  # 연속 저장 대비 디바운스


class _MDChangeHandler(FileSystemEventHandler):
    """
    .md 파일 변경 감지 → 변경된 파일 목록 수집 → 디바운스 후 해당 파일만 재인덱싱.
    서버 재기동 없이 실시간으로 지식 베이스 업데이트.
    """

    def __init__(self, pipeline, docs_root: Path, exclude_dirs: set[str]):
        self._pipeline = pipeline
        self._docs_root = docs_root
        self._exclude_dirs = exclude_dirs
        self._changed: set[str] = set()
        self._deleted: set[str] = set()
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_created(self, event):
        self._handle(event.src_path, deleted=False)

    def on_modified(self, event):
        self._handle(event.src_path, deleted=False)

    def on_deleted(self, event):
        self._handle(event.src_path, deleted=True)

    def on_moved(self, event):
        # 이동: 원본은 삭제, 대상은 새 파일
        self._handle(event.src_path, deleted=True)
        self._handle(event.dest_path, deleted=False)

    def _handle(self, abs_path: str, deleted: bool) -> None:
        path = abs_path.replace("\\", "/")
        if not path.endswith(".md"):
            return
        if any(part in self._exclude_dirs for part in path.split("/")):
            return

        try:
            rel_path = str(Path(abs_path).relative_to(self._docs_root)).replace("\\", "/")
        except ValueError:
            return

        with self._lock:
            if deleted:
                self._deleted.add(rel_path)
                self._changed.discard(rel_path)
            else:
                self._changed.add(rel_path)
                self._deleted.discard(rel_path)

            # 디바운스: 타이머 리셋
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._trigger)
            self._timer.start()

    def _trigger(self):
        with self._lock:
            changed = list(self._changed)
            deleted = list(self._deleted)
            self._changed.clear()
            self._deleted.clear()

        if not changed and not deleted:
            return

        print(f"[감시] 변경 {len(changed)}개, 삭제 {len(deleted)}개 → 재인덱싱 시작")
        # run_files_async: 서버 재기동 없이 해당 파일만 즉시 재인덱싱
        self._pipeline.run_files_async(changed=changed, deleted=deleted)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # 디렉토리 생성
    settings.docs_path.mkdir(parents=True, exist_ok=True)
    settings.lancedb_path.mkdir(parents=True, exist_ok=True)
    settings.tracker_db_path.parent.mkdir(parents=True, exist_ok=True)

    app.state.pipeline = None
    app.state.retriever = None
    app.state.pipeline_ready = False
    app.state.pipeline_error = None

    # 파일 감시 — 서버 시작을 블로킹하지 않도록 백그라운드 스레드에서 초기화
    observer: Observer | None = None
    try:
        from api.services.retriever import Retriever
        from indexer.pipeline import IndexPipeline

        pipeline = IndexPipeline(
            docs_path=settings.docs_path,
            db_path=settings.lancedb_path,
            tracker_db_path=settings.tracker_db_path,
            embed_model=settings.ollama_embed_model,
            ollama_host=settings.ollama_host,
            chunk_max_chars=settings.chunk_max_chars,
            chunk_overlap_chars=settings.chunk_overlap_chars,
            chunk_min_chars=settings.chunk_min_chars,
            exclude_dirs=settings.exclude_dirs_set,
        )

        retriever = Retriever(
            store=pipeline.store,
            embed_model=settings.ollama_embed_model,
            ollama_host=settings.ollama_host,
            docs_path=settings.docs_path,
        )

        pipeline.warm_store_async()

        app.state.pipeline = pipeline
        app.state.retriever = retriever
        app.state.pipeline_ready = True

        def _start_watcher():
            nonlocal observer
            try:
                handler = _MDChangeHandler(pipeline, settings.docs_path, settings.exclude_dirs_set)
                obs = Observer()
                obs.schedule(handler, str(settings.docs_path), recursive=True)
                obs.start()
                observer = obs
                print(f"[감시] 시작: {settings.docs_path} (변경 감지 후 {DEBOUNCE_SECONDS}초 뒤 자동 재인덱싱)")
            except Exception as e:
                print(f"[감시] 시작 실패 (파일 감시 비활성화): {e}")

        watcher_thread = threading.Thread(target=_start_watcher, daemon=True)
        watcher_thread.start()
    except Exception as e:
        app.state.pipeline_error = str(e)
        print(f"[초기화] 실패: {e}")

    yield

    if observer is not None:
        observer.stop()
        observer.join()
        print("[감시] 종료")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="RAG 지식 베이스 API",
        description="Ollama 기반 로컬 AI 지식 베이스",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(search.router)
    app.include_router(index.router)
    app.include_router(health.router)

    return app


app = create_app()
