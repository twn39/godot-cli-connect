"""
Headless project export build module
"""

import os
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd

def export_project(project_path: str, preset: str, output_path: str, debug: bool = False) -> Dict[str, Any]:
    """Exports the Godot project for a given export preset in headless mode."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_output = os.path.abspath(output_path)

    export_flag = "--export-debug" if debug else "--export-release"
    
    cmd = [
        godot_bin,
        "--path", abs_project,
        "--headless",
        export_flag,
        preset,
        abs_output
    ]

    try:
        res = run_godot_cmd(cmd, timeout=120)
        if os.path.exists(abs_output) or res.returncode == 0:
            return {
                "status": "success",
                "export_preset": preset,
                "output_path": abs_output,
                "mode": "debug" if debug else "release",
                "message": f"Successfully exported project to {abs_output}"
            }
        return {
            "status": "error",
            "message": f"Export failed with return code {res.returncode}",
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
