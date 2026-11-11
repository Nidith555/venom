"""
Venom CLI & Server Entry Point
==============================
Command line interface powered by Typer and Rich.
Commands:
  serve  - Launch the Venom FastAPI and WebSocket server
  chat   - Interactive terminal chat with the symbiote
  status - Verify model connectivity and system health
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure backend root is always in Python's search path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.config import VenomConfig
from core.logger import setup_logging
from engine.engine_factory import create_engine
from agent.venom_agent import VenomAgent
from api.app import create_app

app = typer.Typer(
    name="venom",
    help="🕷️ VENOM — Marvel Symbiote-Themed AI Assistant",
    no_args_is_help=True,
)
console = Console()

VENOM_ASCII = r"""[bold white]
  ██    ██ ███████ ███    ██  ██████  ███    ███
  ██    ██ ██      ████   ██ ██    ██ ████  ████
  ██    ██ █████   ██ ██  ██ ██    ██ ██ ████ ██
   ██  ██  ██      ██  ██ ██ ██    ██ ██  ██  ██
    ████   ███████ ██   ████  ██████  ██      ██
[/bold white][bold green]
            -- WE ARE VENOM --
[/bold green]"""


def print_banner():
    console.print(VENOM_ASCII)


@app.command()
def serve(
    host: str = typer.Option(None, "--host", "-h", help="Bind host address"),
    port: int = typer.Option(None, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Auto-reload on code change"),
):
    """Launch the Venom AI Assistant API and WebSocket Server."""
    setup_logging()
    print_banner()

    cfg = VenomConfig()
    bind_host = host or cfg.host
    bind_port = port or int(os.environ.get("PORT", cfg.port))

    console.print(
        Panel(
            f"[bold white]Symbiotic Kernel Active[/bold white]\n"
            f"[cyan]Engine:[/cyan] {cfg.engine} | [cyan]Model:[/cyan] {cfg.model}\n"
            f"[magenta]Voice (ElevenLabs):[/magenta] {cfg.elevenlabs_voice_id} (cgSgspJ2msm6clMCkdW9)\n"
            f"[green]Endpoint:[/green] http://{bind_host}:{bind_port}\n"
            f"[green]WebSocket:[/green] ws://{bind_host}:{bind_port}/ws/chat\n"
            f"[green]API Docs:[/green] http://{bind_host}:{bind_port}/docs",
            border_style="bold white",
            title="🕷️ VENOM CORE",
        )
    )

    fastapi_app = create_app(cfg)
    uvicorn.run(fastapi_app, host=bind_host, port=bind_port, log_level="info")


@app.command()
def status():
    """Check connectivity to the symbiote inference engine."""
    setup_logging()
    print_banner()

    cfg = VenomConfig()
    engine = create_engine(cfg)

    async def _check():
        with console.status("[bold green]Probing symbiotic neural link...", spinner="dots"):
            healthy = await engine.health_check()
            if healthy:
                res = engine.get_models()
                models = await res if hasattr(res, "__await__") else res
            else:
                models = []

        if healthy:
            console.print("[bold green]✔ Host and Symbiote in Sync. System Alive.[/bold green]")
            console.print(f"[bold]Active Engine:[/bold] {cfg.engine}")
            console.print(f"[bold]Default Model:[/bold] {cfg.model}")
            console.print(f"[bold]Available Models:[/bold] {', '.join(models) if models else 'None reported'}")
        else:
            console.print("[bold red]✖ Symbiotic connection failed.[/bold red]")
            console.print(f"Verify that [cyan]{cfg.engine}[/cyan] is running at [cyan]{cfg.ollama_url}[/cyan].")

    asyncio.run(_check())


@app.command()
def chat():
    """Interactive command-line chat session with Venom."""
    setup_logging()
    print_banner()

    cfg = VenomConfig()
    engine = create_engine(cfg)
    agent = VenomAgent(config=cfg, engine=engine)

    console.print("[dim]Type 'exit' or 'quit' to sever the bond.[/dim]\n")

    async def _interactive_loop():
        while True:
            try:
                user_input = console.input("[bold white]HOST > [/bold white]").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    console.print("[bold green]The bond is suspended... for now.[/bold green]")
                    break

                console.print("[bold green]VENOM > [/bold green]", end="")
                async for chunk in agent.chat(user_input, stream=True):
                    console.print(chunk, end="")
                console.print("\n")

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold green]Bond severed.[/bold green]")
                break

    asyncio.run(_interactive_loop())


if __name__ == "__main__":
    app()
