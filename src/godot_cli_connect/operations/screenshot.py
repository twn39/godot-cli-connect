"""
Offscreen screenshot capture module
"""

import os
import sys
import tempfile
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd

def take_screenshot(project_path: str, output_path: str, wait_frames: int = 10) -> Dict[str, Any]:
    """Captures a screenshot of the project or main scene using offscreen rendering."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_output = os.path.abspath(output_path)
    
    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_capture")

func run_capture() -> void:
    var main_scene_path = ProjectSettings.get_setting("application/run/main_scene")
    if main_scene_path and ResourceLoader.exists(main_scene_path):
        var scn = load(main_scene_path).instantiate()
        root.add_child(scn)
    for i in range({wait_frames}):
        await process_frame
    await RenderingServer.frame_post_draw
    var img = root.get_viewport().get_texture().get_image()
    img.save_png("{abs_output}")
    print("SCREENSHOT_SAVED:{abs_output}")
    quit()
"""
    
    temp_script_path = os.path.join(tempfile.gettempdir(), "_temp_godot_screenshot.gd")
    with open(temp_script_path, "w", encoding="utf-8") as f:
        f.write(helper_code)

    cmd = [
        godot_bin,
        "--path", abs_project,
        "-s", temp_script_path
    ]
    if sys.platform != "darwin":
        cmd.extend(["--display-driver", "offscreen"])

    try:
        res = run_godot_cmd(cmd, timeout=20)
        if os.path.exists(abs_output):
            return {
                "status": "success",
                "screenshot_path": abs_output,
                "message": f"Screenshot saved successfully to {abs_output}"
            }
        return {
            "status": "error",
            "message": "Screenshot file was not generated.",
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
