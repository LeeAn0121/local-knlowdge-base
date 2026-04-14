from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.config import Settings, get_settings
from indexer.pipeline import IndexPipeline, IndexStatus

router = APIRouter(prefix="/api/v1/index", tags=["index"])


class TriggerRequest(BaseModel):
    force_reindex: bool = False


class TriggerResponse(BaseModel):
    job_id: str
    status: str


class StatusResponse(BaseModel):
    status: str
    total_files: int
    processed_files: int
    current_file: str | None
    total_chunks: int
    error: str | None
    new_files: int
    modified_files: int
    deleted_files: int
    unchanged_files: int


def _get_pipeline(request: Request) -> IndexPipeline:
    return request.app.state.pipeline


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_index(
    body: TriggerRequest,
    pipeline: Annotated[IndexPipeline, Depends(_get_pipeline)],
):
    if pipeline.is_running():
        raise HTTPException(status_code=409, detail="Indexing already in progress")

    job_id = str(uuid.uuid4())[:8]
    pipeline.run_async(force=body.force_reindex)
    return TriggerResponse(job_id=job_id, status="started")


@router.get("/status", response_model=StatusResponse)
async def index_status(
    pipeline: Annotated[IndexPipeline, Depends(_get_pipeline)],
):
    p = pipeline.progress
    diff = p.last_diff
    return StatusResponse(
        status=p.status.value,
        total_files=p.total_files,
        processed_files=p.processed_files,
        current_file=p.current_file,
        total_chunks=pipeline.store.count(),
        error=p.error,
        new_files=len(diff.new) if diff else 0,
        modified_files=len(diff.modified) if diff else 0,
        deleted_files=len(diff.deleted) if diff else 0,
        unchanged_files=len(diff.unchanged) if diff else 0,
    )


@router.delete("/file")
async def delete_file(
    file_path: str,
    pipeline: Annotated[IndexPipeline, Depends(_get_pipeline)],
):
    deleted = pipeline.store.delete_by_file_path(file_path)
    pipeline.tracker.delete_record(file_path)
    return {"deleted_chunks": deleted, "file_path": file_path}
