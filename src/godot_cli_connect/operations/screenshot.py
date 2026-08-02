"""
Offscreen screenshot capture module
"""

import os
import sys
import tempfile
import base64
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd


def take_screenshot(
    project_path: str, output_path: str, wait_frames: int = 10
) -> Dict[str, Any]:
    """Captures a screenshot of the project or main scene using offscreen rendering."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    abs_output = os.path.abspath(output_path)

    b64_output = base64.b64encode(abs_output.encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_capture")

func run_capture() -> void:
    var save_path = Marshalls.base64_to_utf8("{b64_output}")
    var main_scene_path = ProjectSettings.get_setting("application/run/main_scene")

    var vp = root.get_viewport()
    var w = ProjectSettings.get_setting("display/window/size/viewport_width")
    var h = ProjectSettings.get_setting("display/window/size/viewport_height")
    if w != null and h != null:
        vp.size = Vector2i(int(w), int(h))

    if main_scene_path and ResourceLoader.exists(main_scene_path):
        var scn = load(main_scene_path).instantiate()
        root.add_child(scn)

    for i in range({wait_frames}):
        await process_frame
    await RenderingServer.frame_post_draw
    var img = vp.get_texture().get_image()
    img.save_png(save_path)
    print("SCREENSHOT_SAVED:" + save_path)
    quit()
"""

    with tempfile.NamedTemporaryFile(
        suffix=".gd", delete=False, mode="w", encoding="utf-8"
    ) as tf:
        tf.write(helper_code)
        temp_script_path = tf.name

    extra_flags = []
    if sys.platform != "darwin":
        extra_flags.extend(["--display-driver", "offscreen"])

    cmd = build_godot_cmd(
        godot_bin,
        project_path=abs_project,
        headless=False,
        script=temp_script_path,
        extra_flags=extra_flags,
    )

    try:
        res = run_godot_cmd(cmd, timeout=20)
        if os.path.exists(abs_output):
            return {
                "status": "success",
                "screenshot_path": abs_output,
                "message": f"Screenshot saved successfully to {abs_output}",
            }
        return {
            "status": "error",
            "message": "Screenshot file was not generated.",
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
