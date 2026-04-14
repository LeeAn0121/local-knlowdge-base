from __future__ import annotations

import json
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from api.config import get_settings
from api.services.context_builder import build_prompt, format_sources
from indexer.embedder import embed_query
from vectordb.store import VectorStore

console = Console()


def query(
    question: Annotated[str, typer.Argument(help="Your question")],
    top_k: Annotated[int, typer.Option("--top-k", "-k")] = 5,
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    show_context: Annotated[bool, typer.Option("--show-context")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
    no_stream: Annotated[bool, typer.Option("--no-stream")] = False,
):
    """Ask a question and get an answer from the knowledge base."""
    import asyncio
    asyncio.run(_query(question, top_k=top_k, model=model, show_context=show_context, as_json=as_json, stream=not no_stream))


async def _query(
    question: str,
    top_k: int = 5,
    model: Optional[str] = None,
    show_context: bool = False,
    as_json: bool = False,
    stream: bool = True,
):
    settings = get_settings()
    llm_model = model or settings.ollama_llm_model

    with console.status("Searching knowledge base..."):
        vec = embed_query(question, model=settings.ollama_embed_model, ollama_host=settings.ollama_host)
        store = VectorStore(settings.lancedb_path)
        chunks = store.search(vec, top_k=top_k, min_score=settings.min_similarity_score)

    if not chunks:
        console.print("[yellow]No relevant documents found.[/yellow]")
        return

    if show_context:
        table = Table(title="Retrieved Context", show_lines=True)
        table.add_column("Source", style="cyan", max_width=40)
        table.add_column("Score", style="green", max_width=8)
        table.add_column("Excerpt", max_width=60)
        for c in chunks:
            table.add_row(
                f"{c['file_path']}\n{c['heading_breadcrumb']}",
                f"{c['score']:.2f}",
                c["text"][:150] + "...",
            )
        console.print(table)

    messages = build_prompt(question, chunks)
    sources = format_sources(chunks)

    from api.services.llm import chat, stream_chat

    if as_json:
        answer = await chat(messages, model=llm_model, ollama_host=settings.ollama_host)
        result = {"answer": answer, "sources": sources, "model": llm_model}
        console.print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print()
    console.print(Panel(f"[bold]{question}[/bold]", title="Question", border_style="blue"))
    console.print()

    if stream:
        answer_parts = []
        with console.status("Generating answer..."):
            pass
        async for token in stream_chat(messages, model=llm_model, ollama_host=settings.ollama_host):
            print(token, end="", flush=True)
            answer_parts.append(token)
        print()
    else:
        with console.status("Generating answer..."):
            answer = await chat(messages, model=llm_model, ollama_host=settings.ollama_host)
        console.print(Markdown(answer))

    console.print()
    console.print("[bold]Sources:[/bold]")
    for s in sources:
        console.print(f"  [cyan]{s['file_path']}[/cyan] | {s['heading']} ([green]{s['score']:.0%}[/green])")
