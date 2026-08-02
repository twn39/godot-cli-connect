"""
Offscreen screenshot capture module
"""

from __future__ import annotations

import base64
import os
import sys
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd, temporary_godot_script


def take_screenshot(
    project_path: str,
    output_path: str,
    wait_frames: int = 10,
    scene_path: str | None = None,
) -> dict[str, Any]:
    """
    Capture a screenshot of the main scene or an explicit scene path.

    Args:
        scene_path: Optional ``res://...tscn`` (or project-relative path).
            When omitted, uses ``application/run/main_scene``.
    """
    try:
        godot_bin = find_godot_executable()
    except Exception as e:
        return err(str(e))

    abs_project = os.path.abspath(project_path)
    abs_output = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    b64_output = base64.b64encode(abs_output.encode("utf-8")).decode("ascii")
    scene_res = scene_path or ""
    if scene_res and not scene_res.startswith("res://"):
        # project-relative -> res://
        scene_res = f"res://{scene_res.lstrip('./')}"
    b64_scene = base64.b64encode(scene_res.encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_capture")

func run_capture() -> void:
    var save_path = Marshalls.base64_to_utf8("{b64_output}")
    var forced_scene = Marshalls.base64_to_utf8("{b64_scene}")
    var main_scene_path = forced_scene
    if main_scene_path == "":
        main_scene_path = ProjectSettings.get_setting("application/run/main_scene")

    var vp = root.get_viewport()
    var w = ProjectSettings.get_setting("display/window/size/viewport_width")
    var h = ProjectSettings.get_setting("display/window/size/viewport_height")
    if w != null and h != null:
        vp.size = Vector2i(int(w), int(h))

    if main_scene_path and ResourceLoader.exists(main_scene_path):
        var scn = load(main_scene_path).instantiate()
        root.add_child(scn)
    else:
        print("SCREENSHOT_ERR:Scene not found: " + str(main_scene_path))
        quit(1)
        return

    for i in range({wait_frames}):
        await process_frame
    await RenderingServer.frame_post_draw
    var img = vp.get_texture().get_image()
    img.save_png(save_path)
    print("SCREENSHOT_SAVED:" + save_path)
    quit()
"""

    extra_flags: list[str] = []
    if sys.platform != "darwin":
        extra_flags.extend(["--display-driver", "offscreen"])

    try:
        # headless=False: need a (possibly offscreen) window for viewport capture.
        with temporary_godot_script(helper_code) as temp_script_path:
            cmd = build_godot_cmd(
                godot_bin,
                project_path=abs_project,
                headless=False,
                script=temp_script_path,
                extra_flags=extra_flags,
            )
            res = run_godot_cmd(cmd, timeout=30)

        if os.path.exists(abs_output):
            return ok(
                screenshot_path=abs_output,
                scene=scene_res or "main_scene",
                message=f"Screenshot saved successfully to {abs_output}",
            )
        return err(
            "Screenshot file was not generated.",
            stdout=res.stdout,
            stderr=res.stderr,
            scene=scene_res or "main_scene",
        )
    except Exception as e:
        return err(str(e))
