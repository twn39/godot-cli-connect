"""
GDScript syntax and compilation error checking module
"""

import os
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd


def check_syntax(project_path: str) -> dict[str, Any]:
    """Checks GDScript syntax and compilation errors without running the full editor GUI."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    cmd = build_godot_cmd(
        godot_bin, project_path=abs_project, headless=True, editor=True, quit_after=True
    )

    try:
        res = run_godot_cmd(cmd, timeout=30)
        stderr_lines = [
            line
            for line in res.stderr.splitlines()
            if any(tok in line for tok in ["ERROR", "Parse Error", "Compile Error"])
        ]
        stdout_lines = [
            line
            for line in res.stdout.splitlines()
            if any(tok in line for tok in ["ERROR", "Parse Error", "Compile Error"])
        ]

        errors = stderr_lines + stdout_lines
        if not errors:
            return ok(message="No GDScript compile/syntax errors found.")
        return err(
            "GDScript compile/syntax errors found",
            status="syntax_errors_found",
            errors=errors,
        )
    except Exception as e:
        return err(str(e))
