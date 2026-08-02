"""
Typer CLI Application Module for godot-cli-connect
"""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel

from rich.tree import Tree
from .core import (
    check_syntax,
    take_screenshot,
    run_test_script,
    dump_extension_api,
    create_resource,
    reimport_assets,
    inspect_project,
    export_project,
    get_project_logs,
    inspect_scene,
    eval_code,
    format_gdscript,
    lint_gdscript,
    get_class_info,
    run_gut_tests,
    set_config_setting,
    add_input_action,
    create_scene,
    add_node_to_scene,
    edit_node_in_scene,
    remove_node_from_scene,
    search_docs,
    compare_screenshots,
)
from .finder import find_godot_executable


app = typer.Typer(
    name="godot-cli",
    help="CLI Bridge Tool connecting AI Agents (Claude Code, Codex, Antigravity) with Godot Engine 4.x",
    add_completion=False,
)
console = Console()


def _build_rich_tree(node: dict, parent_tree: Tree):
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
            f"[bold red]⚡ {conn.get('signal')} ➔ {conn.get('to')}.{conn.get('method')}()[/bold red]"
        )

    for child in node.get("children", []):
        _build_rich_tree(child, branch)


@app.command("inspect-scene")
def cmd_inspect_scene(
    scene_path: str = typer.Argument(..., help="Path to Godot scene file (.tscn)"),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
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
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        root = res.get("root_node")
        if root:
            tree = Tree(
                f"[bold magenta]📦 Scene:[/bold magenta] [underline]{res['scene_path']}[/underline] ([dim]mode: {res['mode']}[/dim])"
            )
            _build_rich_tree(root, tree)
            console.print(tree)
        else:
            console.print("[yellow]Scene has no root node.[/yellow]")
    else:
        console.print(
            f"[bold red]✖ Scene inspection failed:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("info")
def info():
    """Prints detected Godot binary path and environment info."""
    try:
        godot_bin = find_godot_executable()
        console.print(
            Panel(
                f"[bold green]Godot Binary Found:[/bold green] {godot_bin}",
                title="Godot CLI Connect",
            )
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("check")
def cmd_check(
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Check GDScript syntax and compilation errors without running the full editor GUI."""
    res = check_syntax(project)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            "[bold green]✔ No GDScript compile/syntax errors found.[/bold green]"
        )
    else:
        console.print("[bold red]✖ Syntax/compile errors found:[/bold red]")
        for err in res.get("errors", []):
            console.print(f"  [red]• {err}[/red]")
        raise typer.Exit(code=1)


@app.command("inspect")
def cmd_inspect(
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Inspect Godot project metadata, configuration, and asset statistics."""
    res = inspect_project(project)
    if json_output:
        console.print_json(data=res)
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


@app.command("screenshot")
def cmd_screenshot(
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    output: str = typer.Option(
        "screenshot.png", "--output", "-o", help="Output PNG file path"
    ),
    frames: int = typer.Option(
        10, "--frames", "-f", help="Number of frames to process before capture"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Render and capture a screenshot of the main scene in background/offscreen mode."""
    res = take_screenshot(project, output, wait_frames=frames)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Screenshot saved to:[/bold green] {res['screenshot_path']}"
        )
    else:
        console.print(
            f"[bold red]✖ Failed to capture screenshot:[/bold red] {res.get('message')}"
        )
        if res.get("stdout"):
            console.print(f"[dim]{res['stdout']}[/dim]")
        raise typer.Exit(code=1)


@app.command("run-test")
def cmd_run_test(
    script: str = typer.Argument(..., help="Path to test GDScript file"),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Run a GDScript test file in headless mode."""
    res = run_test_script(project, script)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print("[bold green]✔ Test script completed successfully.[/bold green]")
        if res.get("stdout"):
            console.print(res["stdout"])
    else:
        console.print(
            f"[bold red]✖ Test script failed with exit code {res['return_code']}.[/bold red]"
        )
        if res.get("stderr"):
            console.print(f"[red]{res['stderr']}[/red]")
        raise typer.Exit(code=1)


@app.command("export")
def cmd_export(
    preset: str = typer.Argument(
        ..., help="Export preset name (defined in export_presets.cfg)"
    ),
    output: str = typer.Argument(..., help="Target binary output file path"),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Export in debug mode (default is release)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Export Godot project build for a given preset in headless mode."""
    res = export_project(project, preset, output, debug=debug)
    if json_output:
        console.print_json(data=res)
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


@app.command("logs")
def cmd_logs(
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    lines: int = typer.Option(
        50, "--lines", "-n", help="Number of recent log lines to retrieve"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Retrieve and display recent Godot execution and error logs."""
    res = get_project_logs(project, lines=lines)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            f"[bold cyan]Log file:[/bold cyan] {res['log_file']} ({res['total_lines_read']} lines read)"
        )
        if res["errors"]:
            console.print(
                f"[bold red]Errors detected ({len(res['errors'])}):[/bold red]"
            )
            for err in res["errors"]:
                console.print(f"  [red]• {err}[/red]")
        else:
            console.print("[green]✔ No error signatures in recent log output.[/green]")

        console.print("\n[bold]Recent Logs:[/bold]")
        for line in res["logs"]:
            console.print(f"  {line}")
    else:
        console.print(
            f"[bold red]✖ Failed to read logs:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("dump-api")
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
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Extension API dumped to:[/bold green] {res['api_json_path']}"
        )
    else:
        console.print(
            f"[bold red]✖ Failed to dump API schema:[/bold red] {res.get('stderr')}"
        )
        raise typer.Exit(code=1)


@app.command("create-resource")
def cmd_create_resource(
    type_name: str = typer.Argument(
        ..., help="Godot Resource Class Name (e.g. StyleBoxFlat, Theme)"
    ),
    save_path: str = typer.Argument(
        ..., help="Resource save path (e.g. res://my_style.tres)"
    ),
    properties: str = typer.Option(
        "{}",
        "--properties",
        "-props",
        help="JSON string of property key-values to apply",
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Instantiate a Godot Resource class, set properties, and save to a .tres file."""
    res = create_resource(project, type_name, save_path, properties)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Resource created:[/bold green] {res['save_path']}"
        )
    else:
        console.print(
            f"[bold red]✖ Failed to create resource:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("reimport")
def cmd_reimport(
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Force Godot to scan the project directory and reimport new or modified assets."""
    res = reimport_assets(project)
    if json_output:
        console.print_json(data=res)
        return


@app.command("eval")
def cmd_eval(
    code: Optional[str] = typer.Argument(
        None, help="GDScript code snippet or expression to evaluate"
    ),
    vars_json: str = typer.Option(
        "{}",
        "--vars",
        "-v",
        help="JSON string of variable bindings (e.g. '{\"x\": 10}')",
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    repl: bool = typer.Option(
        False, "--repl", help="Start interactive REPL terminal session"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Dynamically evaluate GDScript expressions/code snippets or start REPL session."""
    if repl:
        console.print(
            "[bold magenta]Godot GDScript REPL Terminal[/bold magenta] (type [bold cyan]'exit'[/bold cyan] or [bold cyan]'quit'[/bold cyan] to exit)"
        )
        while True:
            try:
                line = console.input("[bold green]gdscript>[/bold green] ")
                if not line.strip():
                    continue
                if line.strip().lower() in ["exit", "quit"]:
                    console.print("[dim]Exiting REPL.[/dim]")
                    break
                res = eval_code(project, line, vars_json=vars_json)
                if res["status"] == "success":
                    if res.get("result") is not None:
                        console.print(
                            f"[bold cyan]⇒ Result:[/bold cyan] {res['result']}"
                        )
                    for stdout_line in res.get("stdout", []):
                        console.print(f"[dim]{stdout_line}[/dim]")
                else:
                    console.print(
                        f"[bold red]✖ Eval Error:[/bold red] {res.get('message')}"
                    )
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Exiting REPL.[/dim]")
                break
        return

    if not code:
        console.print(
            "[bold red]✖ Error:[/bold red] Please provide code to evaluate or use --repl for interactive session."
        )
        raise typer.Exit(code=1)

    res = eval_code(project, code, vars_json=vars_json)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Evaluation completed ({res['mode']} mode):[/bold green]"
        )
        if res.get("result") is not None:
            console.print(
                Panel(
                    f"[bold cyan]Result:[/bold cyan] {res['result']}",
                    title="GDScript Eval",
                )
            )
        if res.get("stdout"):
            console.print("[bold]Stdout:[/bold]")


@app.command("format")
def cmd_format(
    target: str = typer.Argument(
        ".", help="Target GDScript file or directory to format"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    check: bool = typer.Option(
        False, "--check", help="Check formatting without modifying files on disk"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Format GDScript files according to Godot 4 style guidelines."""
    res = format_gdscript(project, target=target, check_only=check)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Formatting completed ([dim]tool: {res['tool_used']}[/dim]):[/bold green] {res.get('message', '')}"
        )
    else:
        console.print(
            f"[bold yellow]⚠ Formatting required ([dim]tool: {res['tool_used']}[/dim]):[/bold yellow]"
        )
        for f in res.get("files_needing_format", []):
            console.print(f"  [yellow]• {f}[/yellow]")
        raise typer.Exit(code=1)


@app.command("lint")
def cmd_lint(
    target: str = typer.Argument(".", help="Target GDScript file or directory to lint"),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Run static linting analysis and engine compile checks across GDScript files."""
    res = lint_gdscript(project, target=target)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    diags = res.get("diagnostics", [])
    if res["status"] == "success" and not diags:
        console.print(
            f"[bold green]✔ No lint errors or style warnings found ([dim]tool: {res['tool_used']}[/dim]).[/bold green]"
        )
    else:
        console.print(
            f"[bold yellow]Diagnostics ({len(diags)} items found, [dim]tool: {res['tool_used']}[/dim]):[/bold yellow]"
        )
        for d in diags:
            color = "red" if d["severity"] == "error" else "yellow"
            console.print(
                f"  [{color}]• [{d['severity'].upper()}] {d['file']}:{d['line']}:{d['column']} ({d['code']}) - {d['message']}[/{color}]"
            )


@app.command("class-info")
def cmd_class_info(
    class_name: str = typer.Argument(
        ..., help="Godot 4 Class Name (e.g. CharacterBody2D, StyleBoxFlat)"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Query targeted ClassDB API details (methods, properties, signals, inherits, docs URL)."""
    res = get_class_info(class_name, project_path=project)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
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
        console.print(
            f"[bold red]✖ ClassDB lookup failed:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("test-gut")
def cmd_test_gut(
    test_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory containing GUT test scripts (e.g. res://test)",
    ),
    script: Optional[str] = typer.Option(
        None, "--script", "-s", help="Specific test script file to execute"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Run GUT (Godot Unit Testing) suites and parse test metrics."""
    res = run_gut_tests(project, test_dir=test_dir, select_script=script)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        summary = res.get("summary", {})
        console.print(
            f"[bold green]✔ GUT tests completed successfully:[/bold green] Passed: {summary.get('passed', 0)}, Total: {summary.get('total', 0)}"
        )
    else:
        summary = res.get("summary", {})
        console.print(
            f"[bold red]✖ GUT tests failed:[/bold red] Failed: {summary.get('failed', 0)}, Passed: {summary.get('passed', 0)}, Total: {summary.get('total', 0)}"
        )
        for fail in summary.get("failures", []):
            console.print(
                f"  [red]• {fail.get('test_name')}: {fail.get('message')}[/red]"
            )


@app.command("config-set")
def cmd_config_set(
    setting_path: str = typer.Argument(
        ..., help="Setting path in project.godot (e.g. application/config/name)"
    ),
    value: str = typer.Argument(
        ..., help="Value to set (auto-typed to int, float, bool, or str)"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Set a project setting persistently in project.godot."""
    res = set_config_setting(project, setting_path, value)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Config updated ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['setting_path']} = {res['value']}"
        )
    else:
        console.print(
            f"[bold red]✖ Config update failed:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("input-add")
def cmd_input_add(
    action_name: str = typer.Argument(
        ..., help="InputMap action name (e.g. move_left, jump)"
    ),
    key_name: str = typer.Option(
        "KEY_A", "--key", "-k", help="Key name (e.g. KEY_A, KEY_SPACE, KEY_W)"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    append: bool = typer.Option(
        True, "--append", help="Append key binding to existing action if present"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Add or update an InputMap action with key binding in project.godot."""
    res = add_input_action(project, action_name, key_name=key_name, append=append)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Input action bound ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['action_name']} ➔ {res['key_bound']}"
        )
    else:
        console.print(
            f"[bold red]✖ Input binding failed:[/bold red] {res.get('message')}"
        )


@app.command("create-scene")
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
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Optional custom name for root node"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Create a new Godot .tscn scene file with a specified root node."""
    res = create_scene(project, save_path, root_type=root_type, root_name=name)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Scene created ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['save_path']} (root: {res['root_name']} [{res['root_type']}])"
        )
    else:
        console.print(
            f"[bold red]✖ Scene creation failed:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("add-node")
def cmd_add_node(
    scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
    node_name: str = typer.Option(
        ..., "--name", "-n", help="Name of the new node to add"
    ),
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
    script: Optional[str] = typer.Option(
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
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
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
    )
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Node added to scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['node_name']} ({res['node_type']}) ➔ {res['scene_path']} under '{res['parent_path']}'"
        )
    else:
        console.print(f"[bold red]✖ Add node failed:[/bold red] {res.get('message')}")
        raise typer.Exit(code=1)


@app.command("docs-search")
def cmd_docs_search(
    query: str = typer.Argument(
        ..., help="Search query (e.g. CharacterBody2D, TileMap, collision)"
    ),
    limit: int = typer.Option(
        5, "--limit", "-l", help="Maximum number of search results to display"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Search Godot 4 official class documentation and retrieve GDScript code examples."""
    res = search_docs(query, project_path=project, limit=limit)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
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


@app.command("edit-node")
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
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Edit properties of an existing node in a .tscn scene file."""
    res = edit_node_in_scene(project, scene_path, node, properties_json=properties)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Node edited in scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['node_path']} ➔ {res['scene_path']}"
        )
    else:
        console.print(f"[bold red]✖ Edit node failed:[/bold red] {res.get('message')}")
        raise typer.Exit(code=1)


@app.command("remove-node")
def cmd_remove_node(
    scene_path: str = typer.Argument(..., help="Path to target scene file (.tscn)"),
    node: str = typer.Option(
        ..., "--node", "-n", help="Target node path to remove (e.g. 'Player/Sprite2D')"
    ),
    project: str = typer.Option(
        ".", "--project", "-p", help="Path to Godot project directory"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Remove a child node synchronously from a .tscn scene file."""
    res = remove_node_from_scene(project, scene_path, node)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Node removed from scene ([dim]mode: {res['mode']}[/dim]):[/bold green] {res['removed_node']} ➔ {res['scene_path']}"
        )
    else:
        console.print(
            f"[bold red]✖ Remove node failed:[/bold red] {res.get('message')}"
        )
        raise typer.Exit(code=1)


@app.command("screenshot-diff")
def cmd_screenshot_diff(
    baseline: str = typer.Option(
        ..., "--baseline", "-b", help="Path to baseline screenshot PNG"
    ),
    current: str = typer.Option(
        ..., "--current", "-c", help="Path to current screenshot PNG"
    ),
    diff_output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Optional path to save red highlight diff mask PNG"
    ),
    threshold: float = typer.Option(
        0.05,
        "--threshold",
        "-t",
        help="Max allowed pixel difference ratio (e.g. 0.05 for 5%)",
    ),
    tolerance: int = typer.Option(
        10, "--tolerance", "-tol", help="Per-channel color difference tolerance (0-255)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON for LLM Agent parsing"
    ),
):
    """Compare two offscreen screenshots and compute visual diff percentage with red highlight overlay."""
    res = compare_screenshots(
        baseline,
        current,
        diff_output_path=diff_output,
        threshold=threshold,
        tolerance=tolerance,
    )
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(
            f"[bold green]✔ Screenshot diff passed:[/bold green] Diff: {res['diff_percentage'] * 100:.2f}% <= Threshold: {threshold * 100:.2f}%"
        )
        if res.get("diff_output_path"):
            console.print(f"  [dim]Diff mask saved to: {res['diff_output_path']}[/dim]")
    else:
        diff_pct = res.get("diff_percentage", 0.0) * 100
        console.print(
            f"[bold red]✖ Screenshot visual diff failed ([dim]{res.get('message', 'Diff exceeds threshold')}[/dim]):[/bold red] Diff: {diff_pct:.2f}% > Threshold: {threshold * 100:.2f}%"
        )
        if res.get("diff_output_path"):
            console.print(
                f"  [red]Highlight diff mask saved to: {res['diff_output_path']}[/red]"
            )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
