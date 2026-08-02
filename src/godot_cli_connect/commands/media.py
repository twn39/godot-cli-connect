"""CLI command group: media."""

from __future__ import annotations

import typer

from .. import cli_common as common
from ..core import (
    compare_screenshots,
    remove_background,
    remove_background_batch,
    take_screenshot,
)

console = common.console


def register(app: typer.Typer) -> None:
    """Register commands on the root Typer app."""

    @app.command("screenshot", rich_help_panel="Media / Assets")
    def cmd_screenshot(
        project: str = typer.Option(".", "--project", "-p", help="Path to Godot project directory"),
        output: str = typer.Option("screenshot.png", "--output", "-o", help="Output PNG file path"),
        frames: int = typer.Option(
            10, "--frames", "-f", help="Number of frames to process before capture"
        ),
        scene: str | None = typer.Option(
            None,
            "--scene",
            "-s",
            help="Scene to render (res://...tscn). Default: project main_scene",
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """Render and capture a screenshot of the main scene or a specified scene."""
        res = take_screenshot(project, output, wait_frames=frames, scene_path=scene)
        if common.handle_json_flag(res, json_output, exit_on_error=False):
            return

        if res["status"] == "success":
            console.print(
                f"[bold green]✔ Screenshot saved to:[/bold green] {res['screenshot_path']} "
                f"[dim](scene: {res.get('scene')})[/dim]"
            )
        else:
            console.print(
                f"[bold red]✖ Failed to capture screenshot:[/bold red] {res.get('message')}"
            )
            if res.get("stdout"):
                console.print(f"[dim]{res['stdout']}[/dim]")
            raise typer.Exit(code=1)

    @app.command("screenshot-diff", rich_help_panel="Media / Assets")
    def cmd_screenshot_diff(
        baseline: str = typer.Option(
            ..., "--baseline", "-b", help="Path to baseline screenshot PNG"
        ),
        current: str = typer.Option(..., "--current", "-c", help="Path to current screenshot PNG"),
        diff_output: str | None = typer.Option(
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
        if common.handle_json_flag(res, json_output, exit_on_error=True):
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

    @app.command("remove-bg", rich_help_panel="Media / Assets")
    @app.command("bg-remove", rich_help_panel="Media / Assets")
    def cmd_remove_bg(
        inputs: list[str] = typer.Argument(  # noqa: B008
            ..., help="Input image path(s) (png/jpg/webp) or directory for batch mode"
        ),
        output: str | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output RGBA PNG path (single file) or output directory (batch)",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            "-m",
            help="Path to BiRefNet_lite ONNX (default: ./BiRefNet_lite_fp16.onnx)",
        ),
        threshold: float | None = typer.Option(
            None,
            "--threshold",
            "-t",
            help="Optional hard alpha threshold 0..1 (default: soft matte)",
        ),
        erode: int = typer.Option(
            0,
            "--erode",
            "-e",
            help="Pixels (1-3) to erode/shrink alpha mask boundary to trim white fringe",
        ),
        decontaminate: bool = typer.Option(
            False,
            "--decontaminate",
            "-d",
            help="Clean background color bleed on edge pixels with pure foreground RGB",
        ),
        save_mask: bool = typer.Option(False, "--mask", help="Also save grayscale alpha mask PNG"),
        json_output: bool = typer.Option(
            False, "--json", help="Output raw JSON for LLM Agent parsing"
        ),
    ):
        """
        Remove image background for game assets using BiRefNet_lite (ONNX + OpenCV).

        Place ``BiRefNet_lite_fp16.onnx`` in the project root, or pass ``--model``.
        Supports single file, multiple files, or directory batch mode.
        """
        import os

        paths: list[str] = []
        for p in inputs:
            if os.path.isdir(p):
                dir_paths = [
                    os.path.join(p, f)
                    for f in sorted(os.listdir(p))
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
                ]
                paths.extend(dir_paths)
            else:
                paths.append(p)

        if not paths:
            common.print_fail(f"No image files found in inputs: {inputs}")

        if len(paths) == 1 and not os.path.isdir(inputs[0]):
            res = remove_background(
                paths[0],
                output,
                model_path=model,
                threshold=threshold,
                erode=erode,
                decontaminate=decontaminate,
                save_mask=save_mask,
            )
        else:
            res = remove_background_batch(
                paths,
                output_dir=output,
                model_path=model,
                threshold=threshold,
                erode=erode,
                decontaminate=decontaminate,
            )

        if common.handle_json_flag(res, json_output, exit_on_error=True):
            return
        if res["status"] == "success":
            if "succeeded" in res:
                common.print_ok(res.get("message", f"{res['succeeded']}/{res['total']} done"))
                for r in res.get("results", []):
                    if r.get("status") == "success":
                        console.print(f"  • {r.get('output_path')}")
            else:
                common.print_ok(res.get("message", f"Saved {res.get('output_path')}"))
                if res.get("mask_path"):
                    console.print(f"  [dim]mask: {res['mask_path']}[/dim]")
        else:
            common.print_fail(res.get("message", "remove-bg failed"))

    if __name__ == "__main__":
        app()
