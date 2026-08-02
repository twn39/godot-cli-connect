"""CLI command group: meta."""

from __future__ import annotations

import typer
from rich.panel import Panel

from .. import cli_common as common
from ..core import (
    list_tools,
    probe_godot_info,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("info", rich_help_panel="Meta")
    def info(
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Detect Godot binary path, version string, and basic capabilities."""
        res = probe_godot_info()
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res.get("status") != "success":
            common.print_fail(res.get("message", "Godot not found"))
        console.print(
            Panel(
                f"[bold green]Godot Binary Found:[/bold green] {res.get('godot_path')}\n"
                f"[bold cyan]Version:[/bold cyan] {res.get('version') or 'unknown'}\n"
                f"[bold cyan]Godot 4.x:[/bold cyan] {res.get('is_godot_4')}\n"
                f"[bold cyan]GODOT_PATH env:[/bold cyan] {res.get('godot_path_env') or '(not set)'}\n"
                f"[bold cyan]Default timeout:[/bold cyan] {res.get('timeout_default')}s",
                title="Godot CLI Connect",
            )
        )

    @app.command("tools-list", rich_help_panel="Meta")
    def cmd_tools_list(
        json_output: bool = typer.Option(
            True, "--json/--no-json", help="Output raw JSON (default: on for agents)"
        ),
    ):
        """List all CLI tools with agent-oriented metadata and result contract."""
        res = list_tools()
        if json_output:
            common.emit_json(res, exit_on_error=False)
            return
        console.print(f"[bold cyan]Tools ({res['tool_count']}):[/bold cyan]")
        for t in res["tools"]:
            console.print(f"  • [green]{t['name']}[/green] — {t['summary']}")
