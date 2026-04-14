from __future__ import annotations

from typing import Annotated

import ollama
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
        store = request.app.state.pipeline.store
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
    store = request.app.state.pipeline.store
    tracker = request.app.state.pipeline.tracker
    return {
        "total_documents": tracker.total_files(),
        "total_chunks": store.count(),
        "embedding_model": settings.ollama_embed_model,
        "llm_model": settings.ollama_llm_model,
        "vector_dimensions": 768,
        "docs_path": str(settings.docs_path),
    }
