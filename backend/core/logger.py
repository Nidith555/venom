"""
Venom Logger
============
Rich-based logging configuration with the Venom symbiote aesthetic.
Black-and-white colour palette, menacing prefix, and structured log levels.
"""

from __future__ import annotations

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.text import Text

# ── Venom colour theme ────────────────────────────────────────────────────────
VENOM_THEME = Theme(
    {
        "logging.level.debug": "dim white",
        "logging.level.info": "bold white",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold red on white",
        "venom.prefix": "bold white",
        "venom.accent": "white",
        "venom.muted": "dim white",
        "venom.danger": "bold red",
    }
)

# Shared Rich console used by the logger and other modules.
console = Console(theme=VENOM_THEME, stderr=True)


class VenomRichHandler(RichHandler):
    """
    Custom Rich log handler that prepends the symbiote glyph to every record.
    """

    SYMBIOTE_PREFIX = "◈ VENOM"

    def render_message(self, record: logging.LogRecord, message: str) -> Text:  # type: ignore[override]
        text = Text()
        text.append(f"[{self.SYMBIOTE_PREFIX}] ", style="venom.prefix")
        text.append(message, style="venom.accent")
        return text


def get_logger(
    name: str = "venom",
    level: int = logging.INFO,
    rich_tracebacks: bool = True,
) -> logging.Logger:
    """
    Return (or create) a named logger configured with the Venom aesthetic.

    Parameters
    ----------
    name:
        Logger name, e.g. ``"venom.engine"``.
    level:
        Logging level (default ``logging.INFO``).
    rich_tracebacks:
        Whether to enable Rich-rendered tracebacks in log output.

    Returns
    -------
    logging.Logger
    """
    log = logging.getLogger(name)

    # Avoid adding duplicate handlers when called multiple times.
    if log.handlers:
        return log

    handler = VenomRichHandler(
        console=console,
        rich_tracebacks=rich_tracebacks,
        show_time=True,
        show_path=False,
        markup=False,
    )
    handler.setLevel(level)

    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root Venom logger."""
    get_logger("venom", level=level)


# Module-level root Venom logger — other modules can import this directly.
logger: logging.Logger = get_logger("venom")
