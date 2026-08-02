"""
Typer CLI Application Module for godot-cli-connect.

Command implementations live under ``godot_cli_connect.commands`` and are
registered onto the root app below.
"""

from __future__ import annotations

import typer

from .cli_common import (
    build_rich_tree,
    console,
    emit_json,
    handle_json_flag,
    print_fail,
    print_ok,
)
from .commands import register_all

app = typer.Typer(
    name="godot-cli",
    help=(
        "CLI Bridge Tool connecting AI Agents (Claude Code, Codex, Antigravity) "
        "with Godot Engine 4.x"
    ),
    add_completion=False,
)

register_all(app)

# Re-export helpers for tests and external importers that historically used
# ``godot_cli_connect.cli``.
__all__ = [
    "app",
    "build_rich_tree",
    "console",
    "emit_json",
    "handle_json_flag",
    "print_fail",
    "print_ok",
]


if __name__ == "__main__":
    app()
