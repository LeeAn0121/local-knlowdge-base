from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def status():
    """Show knowledge base status and statistics."""
    import asyncio
    asyncio.run(_status())


async def _status():
    from api.config import get_settings
    from api.services.llm import list_models
    from vectordb.store import VectorStore
    from indexer.file_tracker import FileTracker

    settings = get_settings()

    store = VectorStore(settings.lancedb_path)
    tracker = FileTracker(settings.tracker_db_path)

    with console.status("Checking Ollama..."):
        models = await list_models(settings.ollama_host)

    table = Table(title="RAG Knowledge Base Status", show_header=False)
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Docs path", str(settings.docs_path))
    table.add_row("Total documents", str(tracker.total_files()))
    table.add_row("Total chunks", str(store.count()))
    table.add_row("Embed model", settings.ollama_embed_model)
    table.add_row("LLM model", settings.ollama_llm_model)
    table.add_row(
        "Ollama",
        f"[green]connected[/green] ({settings.ollama_host})" if models else "[red]not connected[/red]",
    )
    table.add_row("Available models", ", ".join(models) if models else "[red]none[/red]")
    table.add_row("LanceDB path", str(settings.lancedb_path))

    console.print(table)
