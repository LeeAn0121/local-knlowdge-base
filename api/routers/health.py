from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from api.config import Settings, get_settings
from api.services.llm import list_models

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    # Check Ollama
    ollama_status = "ok"
    available_models: list[str] = []
    try:
        available_models = await list_models(settings.ollama_host)
    except Exception as e:
        ollama_status = f"error: {e}"

    # Check VectorDB
    vectordb_status = "ok"
    chunk_count = 0
    try:
        pipeline = getattr(request.app.state, "pipeline", None)
        if pipeline is None:
            vectordb_status = "initializing"
        elif not pipeline.store.is_ready():
            vectordb_status = "warming_up"
        else:
            store = pipeline.store
            chunk_count = store.count()
    except Exception as e:
        vectordb_status = f"error: {e}"

    return {
        "api": "ok",
        "ollama": ollama_status,
        "vectordb": vectordb_status,
        "ollama_models": available_models,
        "embed_model": settings.ollama_embed_model,
        "llm_model": settings.ollama_llm_model,
        "total_chunks": chunk_count,
    }


@router.get("/stats")
async def stats(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        return {
            "status": "initializing",
            "total_documents": 0,
            "total_chunks": 0,
            "embedding_model": settings.ollama_embed_model,
            "llm_model": settings.ollama_llm_model,
            "vector_dimensions": 768,
            "docs_path": str(settings.docs_path),
            "error": getattr(request.app.state, "pipeline_error", None),
        }
    if not pipeline.store.is_ready():
        return {
            "status": "warming_up",
            "total_documents": pipeline.tracker.total_files(),
            "total_chunks": 0,
            "embedding_model": settings.ollama_embed_model,
            "llm_model": settings.ollama_llm_model,
            "vector_dimensions": 768,
            "docs_path": str(settings.docs_path),
            "error": pipeline.store.last_error(),
        }

    store = pipeline.store
    tracker = pipeline.tracker
    return {
        "total_documents": tracker.total_files(),
        "total_chunks": store.count(),
        "embedding_model": settings.ollama_embed_model,
        "llm_model": settings.ollama_llm_model,
        "vector_dimensions": 768,
        "docs_path": str(settings.docs_path),
    }
