from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.config import Settings, get_settings
from api.services.context_builder import build_prompt, format_sources
from api.services.llm import chat, stream_chat
from api.services.retriever import Retriever

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    top_k: int = 5
    model: str | None = None


class Source(BaseModel):
    file_path: str
    heading: str
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    model: str


def _get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    retriever: Annotated[Retriever, Depends(_get_retriever)],
):
    model = body.model or settings.ollama_llm_model
    loop = asyncio.get_event_loop()
    chunks = await loop.run_in_executor(None, lambda: retriever.search(body.message, top_k=body.top_k, min_score=settings.min_similarity_score))
    messages = build_prompt(body.message, chunks, body.history or None)
    answer = await chat(messages, model=model, ollama_host=settings.ollama_host)
    sources = format_sources(chunks)
    return ChatResponse(answer=answer, sources=sources, model=model)


@router.get("/chat/stream")
async def chat_stream(
    request: Request,
    message: str = Query(..., description="User question"),
    top_k: int = Query(8),
    min_score: float = Query(None),
    file_filter: str | None = Query(None, description="file_path 포함 키워드 필터"),
    model: str | None = Query(None),
    settings: Settings = Depends(get_settings),
    retriever: Retriever = Depends(_get_retriever),
):
    llm_model = model or settings.ollama_llm_model
    effective_min_score = min_score if min_score is not None else settings.min_similarity_score
    loop = asyncio.get_event_loop()
    chunks = await loop.run_in_executor(
        None,
        lambda: retriever.search(
            message,
            top_k=top_k,
            min_score=effective_min_score,
            file_path_filter=file_filter,
        ),
    )
    messages = build_prompt(message, chunks, None)
    sources = format_sources(chunks)

    async def event_generator():
        try:
            async for token in stream_chat(messages, model=llm_model, ollama_host=settings.ollama_host):
                if await request.is_disconnected():
                    break
                yield {"data": json.dumps({"type": "token", "content": token})}

            yield {"data": json.dumps({"type": "sources", "sources": sources})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception as e:
            yield {"data": json.dumps({"type": "error", "message": str(e)})}

    return EventSourceResponse(event_generator())
