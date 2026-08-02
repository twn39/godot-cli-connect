"""
Headless project export build module
"""

from __future__ import annotations

import os
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd_streaming


def export_project(
    project_path: str, preset: str, output_path: str, debug: bool = False
) -> dict[str, Any]:
    """Exports the Godot project for a given export preset in headless mode."""
    try:
        godot_bin = find_godot_executable()
    except Exception as e:
        return err(str(e))

    abs_project = os.path.abspath(project_path)
    abs_output = os.path.abspath(output_path)
    export_flag = "--export-debug" if debug else "--export-release"
    export_mode = "debug" if debug else "release"

    cmd = build_godot_cmd(
        godot_bin,
        project_path=abs_project,
        headless=True,
        extra_flags=[export_flag, preset, abs_output],
    )

    try:
        res = run_godot_cmd_streaming(cmd, timeout=120)
        if os.path.exists(abs_output) or res.returncode == 0:
            return ok(
                message=f"Successfully exported project to {abs_output}",
                export_preset=preset,
                output_path=abs_output,
                mode=export_mode,
            )
        return err(
            f"Export failed with return code {res.returncode}",
            stdout=res.stdout,
            stderr=res.stderr,
            mode=export_mode,
        )
    except Exception as e:
        return err(str(e), mode=export_mode)


def list_export_presets(project_path: str) -> dict[str, Any]:
    """Parse export_presets.cfg and list named export presets (offline)."""
    abs_project = os.path.abspath(project_path)
    cfg_path = os.path.join(abs_project, "export_presets.cfg")
    if not os.path.exists(cfg_path):
        return err(
            f"No export_presets.cfg found at {abs_project}",
            project_path=abs_project,
            presets=[],
            count=0,
        )

    presets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    try:
        with open(cfg_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith(";"):
                    continue
                if stripped.startswith("[preset."):
                    if current and "name" in current:
                        presets.append(current)
                    current = {"section": stripped.strip("[]")}
                    continue
                if current is not None and "=" in stripped:
                    k, v = stripped.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"')
                    if k in {
                        "name",
                        "platform",
                        "runnable",
                        "dedicated_server",
                        "export_filter",
                        "export_path",
                    }:
                        if v in ("true", "false"):
                            current[k] = v == "true"
                        else:
                            current[k] = v
        if current and "name" in current:
            presets.append(current)
        return ok(
            mode="offline",
            project_path=abs_project,
            count=len(presets),
            presets=presets,
            config_path=cfg_path,
        )
    except Exception as e:
        return err(str(e), presets=[], count=0)
