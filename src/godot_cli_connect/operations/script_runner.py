"""
GDScript test script execution module
"""

import os
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd


def run_test_script(project_path: str, script_path: str) -> Dict[str, Any]:
    """Runs a test GDScript file in headless mode with timeout and parse error diagnostic parsing."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_script = os.path.abspath(script_path)

    cmd = build_godot_cmd(
        godot_bin, project_path=abs_project, headless=True, script=abs_script
    )

    try:
        res = run_godot_cmd(cmd, timeout=30)
        output = res.stdout or res.stderr
        parse_errors = [
            line for line in output.splitlines() if "SCRIPT ERROR" in line or "Parse Error" in line
        ]
        
        status = "success" if res.returncode == 0 and not parse_errors else "failure"
        result: Dict[str, Any] = {
            "status": status,
            "return_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
        if parse_errors:
            result["parse_errors"] = parse_errors
            result["message"] = f"GDScript parse/runtime error(s) detected: {parse_errors[0]}"
        elif res.returncode != 0:
            result["message"] = f"Script exited with non-zero code {res.returncode}"
        else:
            result["message"] = "Test script executed successfully."
        return result
    except Exception as e:
        msg = str(e)
        if "timed out" in msg:
            msg += ". Make sure the test script calls quit() and does not hang on async/preload."
        return {"status": "error", "message": msg}

