from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console()
ROOT = Path(__file__).resolve().parents[2]


def serve(
    api_port: Annotated[int, typer.Option("--api-port")] = 8000,
    ui_port: Annotated[int, typer.Option("--ui-port")] = 3000,
    no_ui: Annotated[bool, typer.Option("--no-ui")] = False,
    dev: Annotated[bool, typer.Option("--dev")] = False,
):
    """Start the API server and web UI."""
    import signal

    procs = []

    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn", "api.main:app",
        "--host", "0.0.0.0", "--port", str(api_port),
    ]
    if dev:
        uvicorn_cmd.append("--reload")

    api_proc = subprocess.Popen(uvicorn_cmd, cwd=str(ROOT))
    procs.append(api_proc)
    console.print(f"[green]API server[/green]  -> http://localhost:{api_port}")
    console.print(f"[dim]Swagger UI[/dim]  -> http://localhost:{api_port}/docs")
    if dev:
        console.print(f"[yellow]--reload 활성화됨 (개발 모드)[/yellow]")

    if not no_ui:
        web_dir = ROOT / "web"
        if not web_dir.exists():
            console.print("[yellow]web/ directory not found, skipping UI[/yellow]")
        else:
            npm = "npm.cmd" if sys.platform == "win32" else "npm"
            web_proc = subprocess.Popen(
                [npm, "run", "dev", "--", "--port", str(ui_port)],
                cwd=str(web_dir),
            )
            procs.append(web_proc)
            console.print(f"[green]Web UI[/green]      -> http://localhost:{ui_port}")

    console.print("\n[yellow]Press Ctrl+C to stop all services[/yellow]")

    def shutdown(*_):
        for p in procs:
            p.terminate()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        for p in procs:
            p.wait()
    except (KeyboardInterrupt, SystemExit):
        for p in procs:
            p.terminate()
        console.print("[red]Services stopped.[/red]")
