"""
Project inspection and metadata extraction module
"""

import os
from typing import Any

from ..models import err, ok


def inspect_project(project_path: str) -> dict[str, Any]:
    """Parses project.godot file and scans project directory for metadata."""
    abs_project = os.path.abspath(project_path)
    project_godot_path = os.path.join(abs_project, "project.godot")

    if not os.path.exists(project_godot_path):
        return err(f"No project.godot found at {abs_project}")

    meta: dict[str, Any] = {
        "project_name": os.path.basename(abs_project),
        "config_version": None,
        "main_scene": None,
        "rendering_method": None,
        "autoloads": {},
        "plugins": [],
    }

    current_section = "global"
    with open(project_godot_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue
            if "=" in line:
                k, v = [part.strip() for part in line.split("=", 1)]
                v_clean = v.strip('"')
                if current_section in ("global", "application"):
                    if k == "config_version":
                        meta["config_version"] = v_clean
                    elif k == "config/name":
                        meta["project_name"] = v_clean
                    elif k == "run/main_scene":
                        meta["main_scene"] = v_clean
                elif current_section == "application/run":
                    if k == "main_scene":
                        meta["main_scene"] = v_clean

                elif current_section == "rendering/renderer/rendering_method":
                    meta["rendering_method"] = v_clean
                elif current_section == "autoload":
                    meta["autoloads"][k] = v_clean
                elif current_section == "editor_plugins":
                    meta["plugins"].append(k)

    # Count project asset files
    gd_count = 0
    tscn_count = 0
    tres_count = 0
    for root, _, files in os.walk(abs_project):
        if ".godot" in root:
            continue
        for file in files:
            if file.endswith(".gd"):
                gd_count += 1
            elif file.endswith(".tscn"):
                tscn_count += 1
            elif file.endswith(".tres"):
                tres_count += 1

    return ok(
        mode="offline",
        project_path=abs_project,
        metadata=meta,
        stats={
            "gd_scripts": gd_count,
            "scenes": tscn_count,
            "resources": tres_count,
        },
    )
