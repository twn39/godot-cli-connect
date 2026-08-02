"""CLI command group: scripts."""

from __future__ import annotations

import typer

from .. import cli_common as common
from ..core import (
    attach_script_to_node,
    create_script,
    read_script,
    write_script,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("script-create", rich_help_panel="Scripts")
    def cmd_script_create(
        path: str = typer.Argument(..., help="Script path (e.g. res://scripts/player.gd)"),
        extends: str = typer.Option(
            "Node", "--extends", "-e", help="Base class for the script template"
        ),
        class_name: str | None = typer.Option(
            None, "--class-name", "-c", help="Optional class_name declaration"
        ),
        overwrite: bool = typer.Option(
            False, "--overwrite", help="Overwrite if the file already exists"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Create a new GDScript file from a standard template."""
        res = create_script(
            project, path, extends=extends, class_name=class_name, overwrite=overwrite
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            common.print_ok(f"Script created: {res['path']} (extends {res['extends']})")
        else:
            common.print_fail(res.get("message", "script-create failed"))

    @app.command("script-write", rich_help_panel="Scripts")
    def cmd_script_write(
        path: str = typer.Argument(..., help="Script path (e.g. res://scripts/player.gd)"),
        content: str = typer.Option(
            ...,
            "--content",
            "-c",
            help="Full GDScript source to write (use \\n for newlines in shells)",
        ),
        no_overwrite: bool = typer.Option(
            False, "--no-overwrite", help="Fail if the file already exists"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Write full content to a GDScript file (creates parent directories)."""
        # Allow shell-friendly escaped newlines
        text = content.replace("\\n", "\n")
        res = write_script(project, path, text, overwrite=not no_overwrite)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            common.print_ok(f"Script written: {res['path']}")
        else:
            common.print_fail(res.get("message", "script-write failed"))

    @app.command("script-read", rich_help_panel="Scripts")
    def cmd_script_read(
        path: str = typer.Argument(..., help="Script path (e.g. res://scripts/player.gd)"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Read a GDScript file and print its content."""
        res = read_script(project, path)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            console.print(f"[bold cyan]{res['path']}[/bold cyan] ({res['lines']} lines)")
            console.print(res["content"])
        else:
            common.print_fail(res.get("message", "script-read failed"))

    @app.command("attach-script", rich_help_panel="Scripts")
    def cmd_attach_script(
        scene_path: str = typer.Argument(..., help="Path to target scene (.tscn)"),
        script_path: str = typer.Option(
            ..., "--script", "-s", help="Script path (e.g. res://scripts/player.gd)"
        ),
        node: str = typer.Option(
            ".", "--node", "-n", help="Node path relative to root (default: root '.')"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        mode: str = typer.Option(
            "auto",
            "--mode",
            help="Scene edit mode: auto (engine then offline), engine, or offline",
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Attach a GDScript resource to a node in a scene (engine or offline)."""
        res = attach_script_to_node(
            project,
            scene_path,
            node,
            script_path,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            common.print_ok(
                f"Attached {res['script_path']} → {res['node_path']} in {res['scene_path']} "
                f"(mode: {res['mode']})"
            )
        else:
            common.print_fail(res.get("message", "attach-script failed"))
