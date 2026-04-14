from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def chat(
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    top_k: Annotated[int, typer.Option("--top-k", "-k")] = 5,
):
    """Start an interactive chat session with the knowledge base."""
    import asyncio
    asyncio.run(_chat_loop(model=model, top_k=top_k))


async def _chat_loop(model: Optional[str] = None, top_k: int = 5):
    from api.config import get_settings
    from api.services.context_builder import build_prompt, format_sources
    from api.services.llm import stream_chat
    from indexer.embedder import embed_query
    from vectordb.store import VectorStore

    settings = get_settings()
    llm_model = model or settings.ollama_llm_model
    store = VectorStore(settings.lancedb_path)
    history: list[dict[str, str]] = []

    console.print(Panel(
        f"[bold cyan]RAG Knowledge Base Chat[/bold cyan]\n"
        f"Model: [green]{llm_model}[/green] | Docs: [blue]{settings.docs_path}[/blue]\n"
        f"Type [bold]exit[/bold] or press Ctrl+C to quit.",
        border_style="cyan",
    ))

    while True:
        try:
            question = Prompt.ask("\n[bold blue]>[/bold blue]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if question.strip().lower() in ("exit", "quit", "q"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if not question.strip():
            continue

        with console.status("[cyan]Searching...[/cyan]"):
            vec = embed_query(question, model=settings.ollama_embed_model, ollama_host=settings.ollama_host)
            chunks = store.search(vec, top_k=top_k, min_score=settings.min_similarity_score)

        if not chunks:
            console.print("[yellow]No relevant context found.[/yellow]")
            continue

        messages = build_prompt(question, chunks, history)
        sources = format_sources(chunks)

        console.print()
        answer_parts = []
        async for token in stream_chat(messages, model=llm_model, ollama_host=settings.ollama_host):
            print(token, end="", flush=True)
            answer_parts.append(token)
        print()

        answer = "".join(answer_parts)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        # Keep last 10 turns
        if len(history) > 20:
            history = history[-20:]

        console.print()
        for s in sources:
            console.print(f"  [dim]↳ {s['file_path']} | {s['heading']} ({s['score']:.0%})[/dim]")
