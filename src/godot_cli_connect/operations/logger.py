"""
Godot runtime log analysis module
"""

from __future__ import annotations

import os
import sys
from typing import Any

from ..models import err, ok
from .inspector import inspect_project


def get_project_logs(project_path: str, lines: int = 50) -> dict[str, Any]:
    """Retrieves recent logs from the Godot application user data directory."""
    inspect_res = inspect_project(project_path)
    if inspect_res.get("status") != "success":
        return inspect_res

    proj_name = inspect_res["metadata"]["project_name"]
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in proj_name)

    if sys.platform == "darwin":
        log_dir = os.path.expanduser(
            f"~/Library/Application Support/Godot/app_userdata/{safe_name}/logs"
        )
    elif sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        log_dir = os.path.join(app_data, "Godot", "app_userdata", safe_name, "logs")
    else:
        log_dir = os.path.expanduser(f"~/.local/share/godot/app_userdata/{safe_name}/logs")

    godot_log_file = os.path.join(log_dir, "godot.log")
    if not os.path.exists(godot_log_file):
        return err(
            f"Log file not found at {godot_log_file}. "
            "Ensure the project has been run at least once.",
            log_dir=log_dir,
        )

    try:
        with open(godot_log_file, encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            recent_lines = [line_str.rstrip() for line_str in all_lines[-lines:]]

        errors = [
            line_str
            for line_str in recent_lines
            if "ERROR" in line_str or "CRITICAL" in line_str or "SCRIPT ERROR" in line_str
        ]
        warnings = [line_str for line_str in recent_lines if "WARNING" in line_str]

        return ok(
            log_file=godot_log_file,
            total_lines_read=len(recent_lines),
            errors=errors,
            warnings=warnings,
            logs=recent_lines,
        )
    except Exception as e:
        return err(str(e))
