"""CLI command group: quality."""

from __future__ import annotations

import typer
from rich.panel import Panel

from .. import cli_common as common
from ..core import (
    eval_code,
    format_gdscript,
    lint_gdscript,
    run_gut_tests,
    run_test_script,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("format", rich_help_panel="Quality")
    def cmd_format(
        target: str = typer.Argument(".", help="Target GDScript file or directory to format"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        check: bool = typer.Option(
            False, "--check", help="Check formatting without modifying files on disk"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Format GDScript files according to Godot 4 style guidelines."""
        res = format_gdscript(project, target=target, check_only=check)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
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

    @app.command("lint", rich_help_panel="Quality")
    def cmd_lint(
        target: str = typer.Argument(".", help="Target GDScript file or directory to lint"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Run static linting analysis and engine compile checks across GDScript files."""
        res = lint_gdscript(project, target=target)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
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

    @app.command("run-test", rich_help_panel="Quality")
    def cmd_run_test(
        script: str = typer.Argument(..., help="Path to test GDScript file"),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Run a GDScript test file in headless mode."""
        res = run_test_script(project, script)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
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

    @app.command("test-gut", rich_help_panel="Quality")
    def cmd_test_gut(
        test_dir: str | None = typer.Option(
            None,
            "--dir",
            "-d",
            help="Directory containing GUT test scripts (e.g. res://test)",
        ),
        script: str | None = typer.Option(
            None, "--script", "-s", help="Specific test script file to execute"
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Run GUT (Godot Unit Testing) suites and parse test metrics."""
        res = run_gut_tests(project, test_dir=test_dir, select_script=script)
        if common.handle_json_flag(res, json_output, exit_on_error=True):
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
                console.print(f"  [red]• {fail.get('test_name')}: {fail.get('message')}[/red]")

    @app.command("eval", rich_help_panel="Quality")
    def cmd_eval(
        code: str | None = typer.Argument(
            None, help="GDScript code snippet or expression to evaluate"
        ),
        vars_json: str = typer.Option(
            "{}",
            "--vars",
            "-v",
            help="JSON string of variable bindings (e.g. '{\"x\": 10}')",
        ),
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        repl: bool = typer.Option(False, "--repl", help="Start interactive REPL terminal session"),
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
            console.print(
                "[bold red]✖ Error:[/bold red] Please provide code to evaluate or use --repl for interactive session."
            )
            raise typer.Exit(code=1)

        res = eval_code(project, code, vars_json=vars_json)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            common.print_ok(f"Evaluation completed ({res.get('mode', 'engine')} mode):")
            if res.get("result") is not None:
                console.print(
                    Panel(
                        f"[bold cyan]Result:[/bold cyan] {res['result']}",
                        title="GDScript Eval",
                    )
                )
            if res.get("stdout"):
                console.print("[bold]Stdout:[/bold]")
                for line in (
                    res["stdout"]
                    if isinstance(res["stdout"], list)
                    else str(res["stdout"]).splitlines()
                ):
                    console.print(f"  {line}")
        else:
            common.print_fail(f"Evaluation failed: {res.get('message')}")
