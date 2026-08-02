"""CLI command group: scene."""

from __future__ import annotations

import typer
from rich.tree import Tree

from .. import cli_common as common
from ..core import (
    add_node_to_scene,
    connect_signal,
    create_scene,
    disconnect_signal,
    edit_node_in_scene,
    inspect_scene,
    inspect_signals,
    remove_node_from_scene,
    rename_node,
    reparent_node,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("inspect-scene", rich_help_panel="Scene")
    def cmd_inspect_scene(
        scene_path: str = typer.Argument(..., help="Path to Godot scene file (.tscn)"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        engine: bool = typer.Option(
            False,
            "--engine",
            help="Use headless Godot engine instantiation for runtime inspection",
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Inspect and visualize Godot .tscn scene file node hierarchy, scripts, and signals."""
        res = inspect_scene(project, scene_path, use_engine=engine)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            root = res.get("root_node")
            if root:
                tree = Tree(
                    f"[bold magenta]📦 Scene:[/bold magenta] [underline]{res['scene_path']}[/underline] ([dim]mode: {res['mode']}[/dim])"
                )
                common.build_rich_tree(root, tree)
                console.print(tree)
            else:
                console.print("[yellow]Scene has no root node.[/yellow]")
        else:
            console.print(f"[bold red]✖ Scene inspection failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("create-scene", rich_help_panel="Scene")
    def cmd_create_scene(
        save_path: str = typer.Argument(
            ..., help="Target scene save path (e.g. res://scenes/player.tscn)"
        ),
        root_type: str = typer.Option(
            "Node2D",
            "--root",
            "-r",
            help="Root node Class Name (e.g. Node2D, CharacterBody2D, Control)",
        ),
        name: str | None = typer.Option(
            None, "--name", "-n", help="Optional custom name for root node"
        ),
        script: str | None = typer.Option(
            None,
            "--script",
            "-s",
            help="Optional script file path to attach to root node (e.g. res://main.gd)",
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
        """Create a new Godot .tscn scene file with a specified root node and optional script."""
        res = create_scene(
            project,
            save_path,
            root_type=root_type,
            root_name=name,
            script_path=script,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            script_info = f" [script: {res['script_path']}]" if res.get("script_path") else ""
            console.print(
                f"[bold green]✔ Scene created ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['save_path']} (root: {res['root_name']} [{res['root_type']}]{script_info})"
            )
        else:
            console.print(f"[bold red]✖ Scene creation failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("add-node", rich_help_panel="Scene")
    def cmd_add_node(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        node_name: str = typer.Option(..., "--name", "-n", help="Name of the new node to add"),
        node_type: str = typer.Option(
            "Node2D",
            "--type",
            "-t",
            help="Class Name of the new node (e.g. Sprite2D, CollisionShape2D)",
        ),
        parent: str = typer.Option(
            ".",
            "--parent",
            "-parent",
            help="Parent node path relative to root (e.g. '.' or 'Player/Hands')",
        ),
        script: str | None = typer.Option(
            None,
            "--script",
            "-s",
            help="Optional script file path to attach (e.g. res://scripts/gun.gd)",
        ),
        properties: str = typer.Option(
            "{}",
            "--properties",
            "-props",
            help="JSON string of initial properties to apply",
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
        """Add a child node to an existing Godot .tscn scene file."""
        res = add_node_to_scene(
            project,
            scene_path,
            node_name,
            node_type=node_type,
            parent_path=parent,
            script_path=script,
            properties_json=properties,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Node added to scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['node_name']} ({res['node_type']}) ➔ {res['scene_path']} under '{res['parent_path']}'"
            )
        else:
            console.print(f"[bold red]✖ Add node failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("edit-node", rich_help_panel="Scene")
    def cmd_edit_node(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        node: str = typer.Option(
            ...,
            "--node",
            "-n",
            help="Node path in scene relative to root (e.g. '.' or 'Player/Sprite2D')",
        ),
        properties: str = typer.Option(
            "{}", "--properties", "-props", help="JSON string of properties to set"
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
        """Edit properties of an existing node in a .tscn scene file."""
        res = edit_node_in_scene(
            project,
            scene_path,
            node,
            properties_json=properties,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Node edited in scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['node_path']} ➔ {res['scene_path']}"
            )
        else:
            console.print(f"[bold red]✖ Edit node failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("remove-node", rich_help_panel="Scene")
    def cmd_remove_node(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        node: str = typer.Option(
            ..., "--node", "-n", help="Target node path to remove (e.g. 'Player/Sprite2D')"
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
        """Remove a child node synchronously from a .tscn scene file."""
        res = remove_node_from_scene(project, scene_path, node, mode=mode)  # type: ignore[arg-type]
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Node removed from scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['removed_node']} ➔ {res['scene_path']}"
            )
        else:
            console.print(f"[bold red]✖ Remove node failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("rename-node", rich_help_panel="Scene")
    def cmd_rename_node(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        node: str = typer.Option(
            ..., "--node", "-n", help="Target node path to rename (e.g. 'Button')"
        ),
        new_name: str = typer.Option(
            ..., "--new-name", "-new", help="New name for the target node (e.g. 'SubmitButton')"
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
        """Rename an existing node in a .tscn scene file with cascading path updates."""
        res = rename_node(project, scene_path, node, new_name, mode=mode)  # type: ignore[arg-type]
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Node renamed ([dim]mode: {res['mode']}[/dim]):[/bold green] {node} ➔ {new_name}"
            )
        else:
            console.print(f"[bold red]✖ Rename node failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("reparent-node", rich_help_panel="Scene")
    def cmd_reparent_node(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        node: str = typer.Option(
            ..., "--node", "-n", help="Target node path to reparent (e.g. 'Button')"
        ),
        new_parent: str = typer.Option(
            ..., "--new-parent", "-np", help="New parent node path (e.g. 'UIContainer')"
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
        """Move/reparent a node to a new parent node in a .tscn scene tree."""
        res = reparent_node(
            project,
            scene_path,
            node,
            new_parent,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Node reparented ([dim]mode: {res['mode']}[/dim]):[/bold green] {node} ➔ {new_parent}"
            )
        else:
            console.print(f"[bold red]✖ Reparent node failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("bind-signal", rich_help_panel="Scene")
    def cmd_bind_signal(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        from_node: str = typer.Option(
            ..., "--from", "-f", help="Source node emitting the signal (e.g. 'Button')"
        ),
        signal: str = typer.Option(..., "--signal", "-s", help="Signal name (e.g. 'pressed')"),
        to_node: str = typer.Option(
            ".", "--to", "-t", help="Target node receiving the signal (default: root '.')"
        ),
        method: str = typer.Option(
            ..., "--method", "-m", help="Target handler method name (e.g. '_on_button_pressed')"
        ),
        deferred: bool = typer.Option(
            False, "--deferred", help="Defer signal emission to idle frame (flags=1)"
        ),
        one_shot: bool = typer.Option(
            False, "--one-shot", help="Automatically disconnect after first emission (flags=4)"
        ),
        flags: int = typer.Option(0, "--flags", help="Custom bitmask ConnectFlags integer"),
        binds: str = typer.Option(
            "[]", "--binds", help="JSON array of extra bound arguments (e.g. '[\"arg1\", 100]')"
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
        """Bind/connect a GDScript signal from a source node to a target node method."""
        res = connect_signal(
            project,
            scene_path,
            from_node,
            signal,
            to_node,
            method,
            deferred=deferred,
            one_shot=one_shot,
            flags=flags,
            binds_json=binds,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Signal connected ([dim]mode: {res['mode']}[/dim]):[/bold green] {from_node}.{signal} ➔ {to_node}.{method}()"
            )
        else:
            console.print(f"[bold red]✖ Signal connection failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("disconnect-signal", rich_help_panel="Scene")
    def cmd_disconnect_signal(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        from_node: str = typer.Option(
            ..., "--from", "-f", help="Source node emitting the signal (e.g. 'Button')"
        ),
        signal: str = typer.Option(..., "--signal", "-s", help="Signal name (e.g. 'pressed')"),
        to_node: str = typer.Option(
            ".", "--to", "-t", help="Target node receiving the signal (default: root '.')"
        ),
        method: str = typer.Option(
            ..., "--method", "-m", help="Target handler method name (e.g. '_on_button_pressed')"
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
        """Disconnect an existing signal connection between nodes in a scene."""
        res = disconnect_signal(
            project,
            scene_path,
            from_node,
            signal,
            to_node,
            method,
            mode=mode,  # type: ignore[arg-type]
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Signal disconnected ([dim]mode: {res['mode']}[/dim]):[/bold green] {from_node}.{signal} ➔ {to_node}.{method}()"
            )
        else:
            console.print(
                f"[bold red]✖ Signal disconnection failed:[/bold red] {res.get('message')}"
            )
            raise typer.Exit(code=1)

    @app.command("inspect-signals", rich_help_panel="Scene")
    def cmd_inspect_signals(
        scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Inspect and list all signal connections defined in a .tscn scene file."""
        res = inspect_signals(project, scene_path)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            conns = res.get("connections", [])
            console.print(
                f"[bold magenta]⚡ Signal Connections in:[/bold magenta] {res['scene_path']} [dim]({res['connections_count']} total)[/dim]"
            )
            for c in conns:
                flags_str = f" [dim](flags={c['flags']})[/dim]" if c.get("flags") else ""
                console.print(
                    f"  • [green]{c['from']}[/green].[bold cyan]{c['signal']}[/bold cyan] ➔ [yellow]{c['to']}[/yellow].[bold method]{c['method']}[/bold method](){flags_str}"
                )
        else:
            console.print(f"[bold red]✖ Inspect signals failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)
