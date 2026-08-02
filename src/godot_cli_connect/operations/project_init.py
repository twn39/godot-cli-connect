"""
Godot project initialization module
"""

import os
import tempfile
from typing import Dict, Any, Optional
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd
from .scene_editor import create_scene


def init_project(
    project_path: str,
    project_name: Optional[str] = None,
    create_main_scene: bool = True,
    root_type: str = "Node2D",
) -> Dict[str, Any]:
    """Initializes a new empty Godot 4 project directory using Godot headless editor."""
    abs_project = os.path.abspath(project_path)
    os.makedirs(abs_project, exist_ok=True)

    folder_name = os.path.basename(abs_project.rstrip(os.sep)) or "GodotProject"
    actual_name = project_name if project_name else folder_name

    project_godot_path = os.path.join(abs_project, "project.godot")
    if not os.path.exists(project_godot_path):
        initial_content = f"""; Engine configuration file.
config_version=5

[application]

config/name="{actual_name}"
"""
        with open(project_godot_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

    # Optionally create main scene
    main_scene_created = False
    if create_main_scene:
        res = create_scene(
            project_path=abs_project,
            save_path="res://main.tscn",
            root_type=root_type,
            root_name="Main",
        )
        if res.get("status") == "success":
            main_scene_created = True
            # Set application/run/main_scene in project.godot
            with open(project_godot_path, "a", encoding="utf-8") as f:
                f.write('run/main_scene="res://main.tscn"\n')

    # Invoke Godot headless editor scan to complete initialization (.godot/ folder)
    mode = "offline"
    try:
        godot_bin = find_godot_executable()
        cmd = build_godot_cmd(
            godot_bin,
            project_path=abs_project,
            headless=True,
            extra_flags=["--editor", "--quit"],
        )
        res = run_godot_cmd(cmd, timeout=30)
        if res.returncode == 0:
            mode = "engine"
    except Exception:
        pass

    return {
        "status": "success",
        "mode": mode,
        "project_path": abs_project,
        "project_name": actual_name,
        "main_scene_created": main_scene_created,
        "message": f"Initialized Godot project successfully at {abs_project}",
    }
