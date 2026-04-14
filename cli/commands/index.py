from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from api.config import get_settings
from indexer.pipeline import IndexPipeline, IndexProgress

app = typer.Typer(help="Index markdown documents")
console = Console()


def _make_pipeline(docs_path: Optional[Path] = None) -> IndexPipeline:
    settings = get_settings()
    return IndexPipeline(
        docs_path=docs_path or settings.docs_path,
        db_path=settings.lancedb_path,
        tracker_db_path=settings.tracker_db_path,
        embed_model=settings.ollama_embed_model,
        ollama_host=settings.ollama_host,
        chunk_max_chars=settings.chunk_max_chars,
        chunk_overlap_chars=settings.chunk_overlap_chars,
        chunk_min_chars=settings.chunk_min_chars,
    )


@app.callback(invoke_without_command=True)
def index(
    ctx: typer.Context,
    docs_path: Annotated[Optional[Path], typer.Option("--docs-path", "-d", help="Directory containing .md files")] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Re-index all files")] = False,
    watch: Annotated[bool, typer.Option("--watch", "-w", help="Watch for changes")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """Index markdown documents into the knowledge base."""
    if ctx.invoked_subcommand is not None:
        return

    pipeline = _make_pipeline(docs_path)
    settings = get_settings()
    effective_docs = docs_path or settings.docs_path

    if not effective_docs.exists():
        console.print(f"[red]Docs path does not exist: {effective_docs}[/red]")
        raise typer.Exit(1)

    _run_index(pipeline, force=force, verbose=verbose)

    if watch:
        _watch_loop(pipeline, effective_docs, verbose=verbose)


def _run_index(pipeline: IndexPipeline, force: bool = False, verbose: bool = False) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)

        def on_progress(p: IndexProgress):
            if p.total_files > 0:
                progress.update(
                    task,
                    total=p.total_files,
                    completed=p.processed_files,
                    description=f"[cyan]{p.current_file or 'Processing...'}",
                )

        result = pipeline.run(force=force, on_progress=on_progress)

    if result.error:
        console.print(f"[red]Error: {result.error}[/red]")
        return

    diff = result.last_diff
    table = Table(title="Indexing Complete", show_header=False)
    table.add_row("Total chunks", str(result.total_chunks))
    if diff:
        table.add_row("New files", f"[green]{len(diff.new)}[/green]")
        table.add_row("Modified files", f"[yellow]{len(diff.modified)}[/yellow]")
        table.add_row("Deleted files", f"[red]{len(diff.deleted)}[/red]")
        table.add_row("Unchanged files", str(len(diff.unchanged)))
    console.print(table)

    if verbose and diff:
        for f in diff.new:
            console.print(f"  [green]+[/green] {f}")
        for f in diff.modified:
            console.print(f"  [yellow]~[/yellow] {f}")
        for f in diff.deleted:
            console.print(f"  [red]-[/red] {f}")


def _watch_loop(pipeline: IndexPipeline, docs_path: Path, verbose: bool = False) -> None:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    import time

    console.print(f"[cyan]Watching {docs_path} for changes... (Ctrl+C to stop)[/cyan]")

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            if not event.is_directory and str(event.src_path).endswith(".md"):
                console.print(f"[yellow]Change detected: {event.src_path}[/yellow]")
                if not pipeline.is_running():
                    _run_index(pipeline, verbose=verbose)

    observer = Observer()
    observer.schedule(Handler(), str(docs_path), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
