from __future__ import annotations

from typing import AsyncGenerator

import ollama


async def stream_chat(
    messages: list[dict[str, str]],
    model: str,
    ollama_host: str,
) -> AsyncGenerator[str, None]:
    """Async generator that yields text tokens from Ollama streaming chat."""
    client = ollama.AsyncClient(host=ollama_host)
    async for part in await client.chat(
        model=model,
        messages=messages,
        stream=True,
    ):
        token = part.message.content or ""
        if token:
            yield token


async def chat(
    messages: list[dict[str, str]],
    model: str,
    ollama_host: str,
) -> str:
    """Non-streaming chat, returns full response."""
    client = ollama.AsyncClient(host=ollama_host)
    response = await client.chat(model=model, messages=messages, stream=False)
    return response.message.content or ""


async def list_models(ollama_host: str) -> list[str]:
    client = ollama.AsyncClient(host=ollama_host)
    try:
        result = await client.list()
        return [m.model for m in result.models]
    except Exception:
        return []
