from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.services.retriever import Retriever

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    min_score: float = 0.2


class SearchResult(BaseModel):
    chunk_text: str
    file_path: str
    heading: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


def _get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    retriever: Annotated[Retriever, Depends(_get_retriever)],
):
    chunks = retriever.search(body.query, top_k=body.top_k, min_score=body.min_score)
    results = [
        SearchResult(
            chunk_text=c.get("text", ""),
            file_path=c.get("file_path", ""),
            heading=c.get("heading_breadcrumb", ""),
            score=c.get("score", 0.0),
        )
        for c in chunks
    ]
    return SearchResponse(results=results, total=len(results))
