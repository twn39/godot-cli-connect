"""
Typer CLI Application Module for godot-cli-connect
"""

import json
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
)
from .finder import find_godot_executable


app = typer.Typer(
    name="godot-cli",
    help="CLI Bridge Tool connecting AI Agents (Claude Code, Codex, Antigravity) with Godot Engine 4.x",
    add_completion=False
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
        branch.add(f"[bold red]⚡ {conn.get('signal')} ➔ {conn.get('to')}.{conn.get('method')}()[/bold red]")
        
    for child in node.get("children", []):
        _build_rich_tree(child, branch)


@app.command("inspect-scene")
def cmd_inspect_scene(
    scene_path: str = typer.Argument(..., help="Path to Godot scene file (.tscn)"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    engine: bool = typer.Option(False, "--engine", help="Use headless Godot engine instantiation for runtime inspection"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Inspect and visualize Godot .tscn scene file node hierarchy, scripts, and signals."""
    res = inspect_scene(project, scene_path, use_engine=engine)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        root = res.get("root_node")
        if root:
            tree = Tree(f"[bold magenta]📦 Scene:[/bold magenta] [underline]{res['scene_path']}[/underline] ([dim]mode: {res['mode']}[/dim])")
            _build_rich_tree(root, tree)
            console.print(tree)
        else:
            console.print("[yellow]Scene has no root node.[/yellow]")
    else:
        console.print(f"[bold red]✖ Scene inspection failed:[/bold red] {res.get('message')}")
        raise typer.Exit(code=1)


@app.command("info")
def info():
    """Prints detected Godot binary path and environment info."""
    try:
        godot_bin = find_godot_executable()
        console.print(Panel(f"[bold green]Godot Binary Found:[/bold green] {godot_bin}", title="Godot CLI Connect"))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command("check")
def cmd_check(
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Check GDScript syntax and compilation errors without running the full editor GUI."""
    res = check_syntax(project)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print("[bold green]✔ No GDScript compile/syntax errors found.[/bold green]")
    else:
        console.print("[bold red]✖ Syntax/compile errors found:[/bold red]")
        for err in res.get("errors", []):
            console.print(f"  [red]• {err}[/red]")
        raise typer.Exit(code=1)

@app.command("inspect")
def cmd_inspect(
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Inspect Godot project metadata, configuration, and asset statistics."""
    res = inspect_project(project)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        meta = res["metadata"]
        stats = res["stats"]
        console.print(Panel(
            f"[bold cyan]Project Name:[/bold cyan] {meta['project_name']}\n"
            f"[bold cyan]Main Scene:[/bold cyan] {meta['main_scene'] or 'N/A'}\n"
            f"[bold cyan]Godot Config Version:[/bold cyan] {meta['config_version'] or 'Unknown'}\n"
            f"[bold cyan]Rendering Method:[/bold cyan] {meta['rendering_method'] or 'Default'}\n"
            f"[bold cyan]GDScript Files:[/bold cyan] {stats['gd_scripts']} | [bold cyan]Scenes:[/bold cyan] {stats['scenes']} | [bold cyan]Resources:[/bold cyan] {stats['resources']}",
            title="Godot Project Inspection"
        ))
    else:
        console.print(f"[bold red]✖ Inspection failed:[/bold red] {res.get('message')}")
        raise typer.Exit(code=1)

@app.command("screenshot")
def cmd_screenshot(
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    output: str = typer.Option("screenshot.png", "--output", "-o", help="Output PNG file path"),
    frames: int = typer.Option(10, "--frames", "-f", help="Number of frames to process before capture"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Render and capture a screenshot of the main scene in background/offscreen mode."""
    res = take_screenshot(project, output, wait_frames=frames)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Screenshot saved to:[/bold green] {res['screenshot_path']}")
    else:
        console.print(f"[bold red]✖ Failed to capture screenshot:[/bold red] {res.get('message')}")
        if res.get("stdout"):
            console.print(f"[dim]{res['stdout']}[/dim]")
        raise typer.Exit(code=1)

@app.command("run-test")
def cmd_run_test(
    script: str = typer.Argument(..., help="Path to test GDScript file"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Run a GDScript test file in headless mode."""
    res = run_test_script(project, script)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Test script completed successfully.[/bold green]")
        if res.get("stdout"):
            console.print(res["stdout"])
    else:
        console.print(f"[bold red]✖ Test script failed with exit code {res['return_code']}.[/bold red]")
        if res.get("stderr"):
            console.print(f"[red]{res['stderr']}[/red]")
        raise typer.Exit(code=1)

@app.command("export")
def cmd_export(
    preset: str = typer.Argument(..., help="Export preset name (defined in export_presets.cfg)"),
    output: str = typer.Argument(..., help="Target binary output file path"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    debug: bool = typer.Option(False, "--debug", help="Export in debug mode (default is release)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Export Godot project build for a given preset in headless mode."""
    res = export_project(project, preset, output, debug=debug)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Project exported successfully ({res['mode']} mode):[/bold green] {res['output_path']}")
    else:
        console.print(f"[bold red]✖ Export failed:[/bold red] {res.get('message')}")
        if res.get("stderr"):
            console.print(f"[red]{res['stderr']}[/red]")
        raise typer.Exit(code=1)

@app.command("logs")
def cmd_logs(
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of recent log lines to retrieve"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Retrieve and display recent Godot execution and error logs."""
    res = get_project_logs(project, lines=lines)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold cyan]Log file:[/bold cyan] {res['log_file']} ({res['total_lines_read']} lines read)")
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

@app.command("dump-api")
def cmd_dump_api(
    output: str = typer.Option("godot_api.json", "--output", "-o", help="Output JSON path for Extension API"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Dump Godot 4 Engine Extension API schema as JSON."""
    res = dump_extension_api(output)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Extension API dumped to:[/bold green] {res['api_json_path']}")
    else:
        console.print(f"[bold red]✖ Failed to dump API schema:[/bold red] {res.get('stderr')}")
        raise typer.Exit(code=1)

@app.command("create-resource")
def cmd_create_resource(
    type_name: str = typer.Argument(..., help="Godot Resource Class Name (e.g. StyleBoxFlat, Theme)"),
    save_path: str = typer.Argument(..., help="Resource save path (e.g. res://my_style.tres)"),
    properties: str = typer.Option("{}", "--properties", "-props", help="JSON string of property key-values to apply"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Instantiate a Godot Resource class, set properties, and save to a .tres file."""
    res = create_resource(project, type_name, save_path, properties)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Resource created:[/bold green] {res['save_path']}")
    else:
        console.print(f"[bold red]✖ Failed to create resource:[/bold red] {res.get('message')}")
        raise typer.Exit(code=1)

@app.command("reimport")
def cmd_reimport(
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Force Godot to scan the project directory and reimport new or modified assets."""
    res = reimport_assets(project)
    if json_output:
        console.print_json(data=res)
        return

@app.command("eval")
def cmd_eval(
    code: Optional[str] = typer.Argument(None, help="GDScript code snippet or expression to evaluate"),
    vars_json: str = typer.Option("{}", "--vars", "-v", help="JSON string of variable bindings (e.g. '{\"x\": 10}')"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    repl: bool = typer.Option(False, "--repl", help="Start interactive REPL terminal session"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Dynamically evaluate GDScript expressions/code snippets or start REPL session."""
    if repl:
        console.print("[bold magenta]Godot GDScript REPL Terminal[/bold magenta] (type [bold cyan]'exit'[/bold cyan] or [bold cyan]'quit'[/bold cyan] to exit)")
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
                        console.print(f"[bold cyan]⇒ Result:[/bold cyan] {res['result']}")
                    for stdout_line in res.get("stdout", []):
                        console.print(f"[dim]{stdout_line}[/dim]")
                else:
                    console.print(f"[bold red]✖ Eval Error:[/bold red] {res.get('message')}")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Exiting REPL.[/dim]")
                break
        return

    if not code:
        console.print("[bold red]✖ Error:[/bold red] Please provide code to evaluate or use --repl for interactive session.")
        raise typer.Exit(code=1)

    res = eval_code(project, code, vars_json=vars_json)
    if json_output:
        console.print_json(data=res)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Evaluation completed ({res['mode']} mode):[/bold green]")
        if res.get("result") is not None:
            console.print(Panel(f"[bold cyan]Result:[/bold cyan] {res['result']}", title="GDScript Eval"))
        if res.get("stdout"):
            console.print("[bold]Stdout:[/bold]")
@app.command("format")
def cmd_format(
    target: str = typer.Argument(".", help="Target GDScript file or directory to format"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    check: bool = typer.Option(False, "--check", help="Check formatting without modifying files on disk"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
):
    """Format GDScript files according to Godot 4 style guidelines."""
    res = format_gdscript(project, target=target, check_only=check)
    if json_output:
        console.print_json(data=res)
        if res["status"] != "success":
            raise typer.Exit(code=1)
        return

    if res["status"] == "success":
        console.print(f"[bold green]✔ Formatting completed ([dim]tool: {res['tool_used']}[/dim]):[/bold green] {res.get('message', '')}")
    else:
        console.print(f"[bold yellow]⚠ Formatting required ([dim]tool: {res['tool_used']}[/dim]):[/bold yellow]")
        for f in res.get("files_needing_format", []):
            console.print(f"  [yellow]• {f}[/yellow]")
        raise typer.Exit(code=1)


@app.command("lint")
def cmd_lint(
    target: str = typer.Argument(".", help="Target GDScript file or directory to lint"),
    project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON for LLM Agent parsing")
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
        console.print(f"[bold green]✔ No lint errors or style warnings found ([dim]tool: {res['tool_used']}[/dim]).[/bold green]")
    else:
        console.print(f"[bold yellow]Diagnostics ({len(diags)} items found, [dim]tool: {res['tool_used']}[/dim]):[/bold yellow]")
        for d in diags:
            color = "red" if d["severity"] == "error" else "yellow"
            console.print(f"  [{color}]• [{d['severity'].upper()}] {d['file']}:{d['line']}:{d['column']} ({d['code']}) - {d['message']}[/{color}]")
        if res["status"] != "success":
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


