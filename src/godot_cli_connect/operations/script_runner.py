"""
GDScript test script execution module
"""

import os
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd


def run_test_script(project_path: str, script_path: str) -> dict[str, Any]:
    """Runs a test GDScript file in headless mode with timeout and parse error diagnostic parsing."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_script = os.path.abspath(script_path)

    cmd = build_godot_cmd(godot_bin, project_path=abs_project, headless=True, script=abs_script)

    try:
        res = run_godot_cmd(cmd, timeout=30)
        output = res.stdout or res.stderr
        parse_errors = [
            line for line in output.splitlines() if "SCRIPT ERROR" in line or "Parse Error" in line
        ]

        if res.returncode == 0 and not parse_errors:
            return ok(
                message="Test script executed successfully.",
                return_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
            )

        message = (
            f"GDScript parse/runtime error(s) detected: {parse_errors[0]}"
            if parse_errors
            else f"Script exited with non-zero code {res.returncode}"
        )
        payload: dict[str, Any] = {
            "return_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
        if parse_errors:
            payload["parse_errors"] = parse_errors
        return err(message, status="failure", **payload)
    except Exception as e:
        msg = str(e)
        if "timed out" in msg:
            msg += ". Make sure the test script calls quit() and does not hang on async/preload."
        return err(msg)
