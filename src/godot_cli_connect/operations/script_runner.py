"""
GDScript test script execution module
"""

import os
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd

def run_test_script(project_path: str, script_path: str) -> Dict[str, Any]:
    """Runs a test GDScript file in headless mode."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_script = os.path.abspath(script_path)

    cmd = [
        godot_bin,
        "--path", abs_project,
        "--headless",
        "-s", abs_script
    ]

    try:
        res = run_godot_cmd(cmd, timeout=30)
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "return_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
