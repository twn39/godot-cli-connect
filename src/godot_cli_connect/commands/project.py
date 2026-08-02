"""CLI command group: project."""

from __future__ import annotations

import typer
from rich.panel import Panel

from .. import cli_common as common
from ..core import (
    add_autoload,
    add_input_action,
    check_syntax,
    create_resource,
    dump_extension_api,
    export_project,
    get_class_info,
    get_config_setting,
    get_project_logs,
    init_project,
    inspect_project,
    list_autoloads,
    list_export_presets,
    reimport_assets,
    remove_autoload,
    search_docs,
    set_config_setting,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("inspect", rich_help_panel="Project")
    def cmd_inspect(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Inspect Godot project metadata, configuration, and asset statistics."""
        res = inspect_project(project)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            meta = res["metadata"]
            stats = res["stats"]
            console.print(
                Panel(
                    f"[bold cyan]Project Name:[/bold cyan] {meta['project_name']}\n"
                    f"[bold cyan]Main Scene:[/bold cyan] {meta['main_scene'] or 'N/A'}\n"
                    f"[bold cyan]Godot Config Version:[/bold cyan] {meta['config_version'] or 'Unknown'}\n"
                    f"[bold cyan]Rendering Method:[/bold cyan] {meta['rendering_method'] or 'Default'}\n"
                    f"[bold cyan]GDScript Files:[/bold cyan] {stats['gd_scripts']} | [bold cyan]Scenes:[/bold cyan] {stats['scenes']} | [bold cyan]Resources:[/bold cyan] {stats['resources']}",
                    title="Godot Project Inspection",
                )
            )
        else:
            console.print(f"[bold red]✖ Inspection failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("check", rich_help_panel="Project")
    def cmd_check(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Check GDScript syntax and compilation errors without running the full editor GUI."""
        res = check_syntax(project)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print("[bold green]✔ No GDScript compile/syntax errors found.[/bold green]")
        else:
            console.print("[bold red]✖ Syntax/compile errors found:[/bold red]")
            for err in res.get("errors", []):
                console.print(f"  [red]• {err}[/red]")
            raise typer.Exit(code=1)

    @app.command("init-project", rich_help_panel="Project")
    def cmd_init_project(
        project_path: str = typer.Argument(..., help="Target directory path for the new project"),
        name: str | None = typer.Option(
            None, "--name", "-n", help="Display name of the project (default: directory name)"
        ),
        no_scene: bool = typer.Option(
            False, "--no-scene", help="Do not create a default main.tscn scene file"
        ),
        root_type: str = typer.Option(
            "Node2D", "--root-type", "-r", help="Root node type for the default main.tscn"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Initialize a new empty Godot 4 project directory with project.godot and .godot/ cache."""
        res = init_project(
            project_path=project_path,
            project_name=name,
            create_main_scene=not no_scene,
            root_type=root_type,
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Initialized Godot project ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['project_name']} ➔ [underline]{res['project_path']}[/underline]"
            )
        else:
            console.print(
                f"[bold red]✖ Project initialization failed:[/bold red] {res.get('message')}"
            )
            raise typer.Exit(code=1)

    @app.command("config-get", rich_help_panel="Project")
    def cmd_config_get(
        setting_path: str = typer.Argument(
            ..., help="Setting path (e.g. application/config/name or config/name)"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Read a project.godot setting value."""
        res = get_config_setting(project, setting_path)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            console.print(
                f"[bold green]{res['setting_path']}[/bold green] = [cyan]{res['value']}[/cyan] "
                f"[dim](raw: {res['raw']})[/dim]"
            )
        else:
            common.print_fail(res.get("message", "config-get failed"))

    @app.command("config-set", rich_help_panel="Project")
    def cmd_config_set(
        setting_path: str = typer.Argument(
            ..., help="Setting path in project.godot (e.g. application/config/name)"
        ),
        value: str = typer.Argument(
            ..., help="Value to set (auto-typed to int, float, bool, or str)"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Set a project setting persistently in project.godot."""
        res = set_config_setting(project, setting_path, value)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Config updated ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['setting_path']} = {res['value']}"
            )
        else:
            console.print(f"[bold red]✖ Config update failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("input-add", rich_help_panel="Project")
    def cmd_input_add(
        action_name: str = typer.Argument(..., help="InputMap action name (e.g. move_left, jump)"),
        key_name: str = typer.Option(
            "KEY_A", "--key", "-k", help="Key name (e.g. KEY_A, KEY_SPACE, KEY_W)"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        append: bool = typer.Option(
            True, "--append", help="Append key binding to existing action if present"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Add or update an InputMap action with key binding in project.godot."""
        res = add_input_action(project, action_name, key_name=key_name, append=append)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Input action bound ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['action_name']} ➔ {res['key_bound']}"
            )
        else:
            console.print(f"[bold red]✖ Input binding failed:[/bold red] {res.get('message')}")

    @app.command("autoload-add", rich_help_panel="Project")
    def cmd_autoload_add(
        name: str = typer.Argument(..., help="Autoload singleton name (e.g. GameState)"),
        script_path: str = typer.Argument(
            ..., help="Script path (e.g. res://autoload/game_state.gd)"
        ),
        disabled: bool = typer.Option(
            False, "--disabled", help="Register but leave autoload disabled"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Register an Autoload singleton in project.godot."""
        res = add_autoload(project, name, script_path, enabled=not disabled)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            common.print_ok(
                f"Autoload {res['autoload_name']} → {res['path']} (enabled={res['enabled']})"
            )
        else:
            common.print_fail(res.get("message", "autoload-add failed"))

    @app.command("autoload-remove", rich_help_panel="Project")
    def cmd_autoload_remove(
        name: str = typer.Argument(..., help="Autoload singleton name to remove"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Remove an Autoload singleton from project.godot."""
        res = remove_autoload(project, name)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            common.print_ok(f"Removed autoload {name}")
        else:
            common.print_fail(res.get("message", "autoload-remove failed"))

    @app.command("autoload-list", rich_help_panel="Project")
    def cmd_autoload_list(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """List Autoload singletons from project.godot."""
        res = list_autoloads(project)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            console.print(f"[bold cyan]Autoloads ({res['count']}):[/bold cyan]")
            for item in res["autoloads"]:
                flag = "on" if item["enabled"] else "off"
                console.print(
                    f"  • [green]{item['name']}[/green] → {item['path']} [dim]({flag})[/dim]"
                )
        else:
            common.print_fail(res.get("message", "autoload-list failed"))

    @app.command("export", rich_help_panel="Project")
    def cmd_export(
        preset: str = typer.Argument(
            ..., help="Export preset name (defined in export_presets.cfg)"
        ),
        output: str = typer.Argument(..., help="Target binary output file path"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        debug: bool = typer.Option(
            False, "--debug", help="Export in debug mode (default is release)"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Export Godot project build for a given preset in headless mode."""
        res = export_project(project, preset, output, debug=debug)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Project exported successfully ({res['mode']} mode):[/bold green] {res['output_path']}"
            )
        else:
            console.print(f"[bold red]✖ Export failed:[/bold red] {res.get('message')}")
            if res.get("stderr"):
                console.print(f"[red]{res['stderr']}[/red]")
            raise typer.Exit(code=1)

    @app.command("export-presets", rich_help_panel="Project")
    def cmd_export_presets(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """List export presets defined in export_presets.cfg."""
        res = list_export_presets(project)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            console.print(f"[bold cyan]Export presets ({res['count']}):[/bold cyan]")
            for p in res["presets"]:
                console.print(
                    f"  • [green]{p.get('name')}[/green] "
                    f"[dim]platform={p.get('platform')} path={p.get('export_path')}[/dim]"
                )
        else:
            common.print_fail(res.get("message", "export-presets failed"))

    @app.command("logs", rich_help_panel="Project")
    def cmd_logs(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        lines: int = typer.Option(
            50, "--lines", "-n", help="Number of recent log lines to retrieve"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Retrieve and display recent Godot execution and error logs."""
        res = get_project_logs(project, lines=lines)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print(
                f"[bold cyan]Log file:[/bold cyan] {res['log_file']} ({res['total_lines_read']} lines read)"
            )
            if res["errors"]:
                console.print(f"[bold red]Errors detected ({len(res['errors'])}):[/bold red]")
                for err in res["errors"]:
                    console.print(f"  [red]• {err}[/red]")
            else:
                console.print("[green]✔ No error signatures in recent log output.[/green]")

            console.print("\n[bold]Recent Logs:[/bold]")
            for line in res["logs"]:
                console.print(f"  {line}")
        else:
            console.print(f"[bold red]✖ Failed to read logs:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("dump-api", rich_help_panel="Project")
    def cmd_dump_api(
        output: str = typer.Option(
            "godot_api.json", "--output", "-o", help="Output JSON path for Extension API"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Dump Godot 4 Engine Extension API schema as JSON."""
        res = dump_extension_api(output)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Extension API dumped to:[/bold green] {res['api_json_path']}"
            )
        else:
            console.print(f"[bold red]✖ Failed to dump API schema:[/bold red] {res.get('stderr')}")
            raise typer.Exit(code=1)

    @app.command("class-info", rich_help_panel="Project")
    def cmd_class_info(
        class_name: str = typer.Argument(
            ..., help="Godot 4 Class Name (e.g. CharacterBody2D, StyleBoxFlat)"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Query targeted ClassDB API details (methods, properties, signals, inherits, docs URL)."""
        res = get_class_info(class_name, project_path=project)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success":
            info = res.get("class_info", {})
            console.print(
                Panel(
                    f"[bold cyan]Class:[/bold cyan] {info.get('name')}\n"
                    f"[bold cyan]Inherits:[/bold cyan] {info.get('inherits') or 'Object'}\n"
                    f"[bold cyan]Methods Count:[/bold cyan] {len(info.get('methods', []))}\n"
                    f"[bold cyan]Properties Count:[/bold cyan] {len(info.get('properties', []))}\n"
                    f"[bold cyan]Signals Count:[/bold cyan] {len(info.get('signals', []))}\n"
                    f"[bold cyan]Official Docs:[/bold cyan] {info.get('docs_url')}",
                    title=f"ClassDB Info: {class_name}",
                )
            )
        else:
            console.print(f"[bold red]✖ ClassDB lookup failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("docs-search", rich_help_panel="Project")
    def cmd_docs_search(
        query: str = typer.Argument(
            ..., help="Search query (e.g. CharacterBody2D, TileMap, collision)"
        ),
        limit: int = typer.Option(
            5, "--limit", "-l", help="Maximum number of search results to display"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Search Godot 4 official class documentation and retrieve GDScript code examples."""
        res = search_docs(query, project_path=project, limit=limit)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return

        if res["status"] == "success" and res.get("results"):
            console.print(
                f"[bold cyan]🔍 Found {res['total']} doc results for '{query}':[/bold cyan]\n"
            )
            for item in res["results"]:
                snippet_str = (
                    f"\n\n[bold yellow]GDScript Usage Example:[/bold yellow]\n[green]{item['code_example']}[/green]"
                    if item.get("code_example")
                    else ""
                )
                methods_str = ", ".join(item.get("key_methods", [])[:5]) or "None"
                console.print(
                    Panel(
                        f"[bold white]{item['brief_description']}[/bold white]\n"
                        f"[bold dim]Inherits: {item['inherits']}[/bold dim]\n"
                        f"[bold cyan]Docs Link:[/bold cyan] {item['docs_url']}\n"
                        f"[bold magenta]Key Methods:[/bold magenta] {methods_str}{snippet_str}",
                        title=f"Class: [bold yellow]{item['name']}[/bold yellow]",
                    )
                )
        else:
            console.print(
                f"[bold yellow]⚠ No documentation results found for '{query}'.[/bold yellow]"
            )
            raise typer.Exit(code=1)

    @app.command("create-resource", rich_help_panel="Project")
    def cmd_create_resource(
        type_name: str = typer.Argument(
            ..., help="Godot Resource Class Name (e.g. StyleBoxFlat, Theme)"
        ),
        save_path: str = typer.Argument(..., help="Resource save path (e.g. res://my_style.tres)"),
        properties: str = typer.Option(
            "{}",
            "--properties",
            "-props",
            help="JSON string of property key-values to apply",
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Instantiate a Godot Resource class, set properties, and save to a .tres file."""
        res = create_resource(project, type_name, save_path, properties)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print(f"[bold green]✔ Resource created:[/bold green] {res['save_path']}")
        else:
            console.print(f"[bold red]✖ Failed to create resource:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("reimport", rich_help_panel="Project")
    @app.command("import-assets", rich_help_panel="Project")
    def cmd_reimport(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        clean: bool = typer.Option(
            False, "--clean", "-c", help="Purge .godot/imported cache before reimport scan"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Force Godot to scan the project directory and reimport new or modified assets."""
        res = reimport_assets(project, clean=clean)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            msg = f"[bold green]✔ {res.get('message', 'Assets reimported successfully.')}[/bold green]"
            console.print(f"{msg} [underline]{res.get('project_path', project)}[/underline]")
            if res.get("invalid_count", 0) > 0:
                console.print(
                    f"  [bold yellow]⚠ Warning: {res['invalid_count']} import files marked invalid:[/bold yellow]"
                )
                for inv in res.get("invalid_files", []) or []:
                    console.print(f"    • {inv}")
        else:
            console.print(f"[bold red]✖ Asset reimport failed:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)

    @app.command("config-resolution", rich_help_panel="Project")
    @app.command("set-resolution", rich_help_panel="Project")
    def cmd_config_resolution(
        preset: str | None = typer.Option(
            None, "--preset", "-preset", help="Resolution preset: 720p, 1080p, 800x600, 1024x768, retro"
        ),
        width: int | None = typer.Option(None, "--width", "-w", help="Custom viewport width in pixels"),
        height: int | None = typer.Option(None, "--height", "-h", help="Custom viewport height in pixels"),
        stretch_mode: str = typer.Option(
            "canvas_items", "--stretch", "-s", help="Stretch mode: disabled, canvas_items, viewport"
        ),
        stretch_aspect: str = typer.Option(
            "keep", "--aspect", "-a", help="Stretch aspect ratio: ignore, keep, keep_width, keep_height, expand"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Set project display resolution and responsive stretch mode in project.godot."""
        from ..operations.config_editor import set_project_resolution

        res = set_project_resolution(
            project,
            width=width,
            height=height,
            preset=preset,
            stretch_mode=stretch_mode,
            stretch_aspect=stretch_aspect,
        )
        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            console.print(f"[bold green]✔ {res['message']}[/bold green]")
        else:
            console.print(f"[bold red]✖ Failed to set resolution:[/bold red] {res.get('message')}")
            raise typer.Exit(code=1)
