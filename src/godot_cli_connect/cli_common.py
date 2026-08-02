"""
Shared CLI presentation helpers for godot-cli-connect.

All Typer command modules should use these helpers instead of reimplementing
JSON/human output and success checks.
"""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.tree import Tree

from .models import as_result_dict, is_success

console = Console()


def emit_json(res: Any, *, exit_on_error: bool = True) -> None:
    """Print structured JSON for agents; optionally non-zero exit on failure."""
    console.print_json(data=as_result_dict(res))
    if exit_on_error and not is_success(res):
        raise typer.Exit(code=1)


def print_ok(message: str) -> None:
    """Print a human-readable success line."""
    console.print(f"[bold green]✔ {message}[/bold green]")


def print_fail(message: str, *, details: str | None = None) -> None:
    """Print a human-readable failure and exit with code 1."""
    console.print(f"[bold red]✖ {message}[/bold red]")
    if details:
        console.print(f"[red]{details}[/red]")
    raise typer.Exit(code=1)


def handle_json_flag(res: Any, json_output: bool, *, exit_on_error: bool = True) -> bool:
    """If --json was set, emit JSON and return True so the command can return early."""
    if not json_output:
        return False
    emit_json(res, exit_on_error=exit_on_error)
    return True


def build_rich_tree(node: dict, parent_tree: Tree) -> None:
    """Recursively attach scene node data onto a Rich Tree."""
    name = node.get("name", "Node")
    type_name = node.get("type", "Node")
    script = node.get("script_path")
    groups = node.get("groups", [])
    conns = node.get("connections", [])

    label = f"[bold green]{name}[/bold green] [cyan]({type_name})[/cyan]"
    if script:
        label += f" [yellow]📜 {script}[/yellow]"
    if groups:
        label += f" [magenta]🏷️ {groups}[/magenta]"

    branch = parent_tree.add(label)

    for conn in conns:
        branch.add(
            f"[bold red]⚡ {conn.get('signal')} ➔ "
            f"{conn.get('to')}.{conn.get('method')}()[/bold red]"
        )

    for child in node.get("children", []):
        build_rich_tree(child, branch)
