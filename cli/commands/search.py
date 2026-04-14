from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    top_k: Annotated[int, typer.Option("--top-k", "-k")] = 10,
    min_score: Annotated[float, typer.Option("--min-score")] = 0.4,
    as_json: Annotated[bool, typer.Option("--json")] = False,
):
    """Search the knowledge base without LLM generation."""
    from api.config import get_settings
    from indexer.embedder import embed_query
    from vectordb.store import VectorStore

    settings = get_settings()

    with console.status("Searching..."):
        vec = embed_query(query, model=settings.ollama_embed_model, ollama_host=settings.ollama_host)
        store = VectorStore(settings.lancedb_path)
        results = store.search(vec, top_k=top_k, min_score=min_score)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    if as_json:
        console.print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Search: {query!r}", show_lines=True)
    table.add_column("#", style="dim", max_width=4)
    table.add_column("Score", style="green", max_width=7)
    table.add_column("File", style="cyan", max_width=35)
    table.add_column("Heading", style="blue", max_width=30)
    table.add_column("Excerpt", max_width=50)

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{r['score']:.2f}",
            r.get("file_path", ""),
            r.get("heading_breadcrumb", ""),
            r.get("text", "")[:120] + "...",
        )

    console.print(table)
