"""
Godot Resource instantiation and asset reimporting module
"""

import base64
import os
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import run_godot_script


def create_resource(
    project_path: str, resource_type: str, save_path: str, properties_json: str = "{}"
) -> dict[str, Any]:
    """Instantiates a Godot Resource class, applies properties safely via Base64, and saves to .tres."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    b64_type = base64.b64encode(resource_type.encode("utf-8")).decode("ascii")
    b64_save = base64.b64encode(save_path.encode("utf-8")).decode("ascii")
    b64_props = base64.b64encode(properties_json.encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_create")

func run_create() -> void:
    var res_type = Marshalls.base64_to_utf8("{b64_type}")
    var save_path = Marshalls.base64_to_utf8("{b64_save}")
    if not ClassDB.class_exists(res_type):
        print("RES_ERR:Class " + res_type + " does not exist.")
        quit(1)
        return

    var obj = ClassDB.instantiate(res_type)
    if obj == null or not (obj is Resource):
        print("RES_ERR:Failed to instantiate resource type " + res_type)
        quit(1)
        return

    var b64_json = "{b64_props}"
    var json_str = Marshalls.base64_to_utf8(b64_json)
    var props = JSON.parse_string(json_str)
    if props != null and props is Dictionary:
        for key in props.keys():
            obj.set(key, props[key])

    var dir_path = save_path.get_base_dir()
    if dir_path != "" and dir_path != "res://":
        DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))

    var err = ResourceSaver.save(obj, save_path)
    print("RES_SUCCESS:" + save_path + " ERR:" + str(err))
    quit()
"""

    try:
        res = run_godot_script(godot_bin, abs_project, helper_code, timeout=20)
        if res.returncode == 0 and "RES_SUCCESS" in res.stdout:
            return ok(
                message=f"Resource {resource_type} saved to {save_path}",
                save_path=save_path,
                mode="engine",
            )
        return err(res.stdout or res.stderr or "Failed to create resource")
    except Exception as e:
        return err(str(e))


def reimport_assets(project_path: str) -> dict[str, Any]:
    """Forces Godot to scan filesystem and reimport new/modified assets (PNG, SVG, WAV, etc.)."""
    from .runner import build_godot_cmd, run_godot_cmd

    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    cmd = build_godot_cmd(
        godot_bin,
        project_path=abs_project,
        headless=True,
        extra_flags=["--editor", "--quit"],
    )

    try:
        res = run_godot_cmd(cmd, timeout=30)
        if res.returncode == 0:
            return ok(
                message="Filesystem scanned and assets reimported successfully.",
                project_path=abs_project,
                stdout=res.stdout,
                returncode=res.returncode,
                mode="engine",
            )
        return err(
            f"Reimport finished with return code {res.returncode}",
            status="failure",
            project_path=abs_project,
            stdout=res.stdout,
            returncode=res.returncode,
        )
    except Exception as e:
        return err(str(e))
