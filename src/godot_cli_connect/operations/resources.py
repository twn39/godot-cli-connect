"""
Godot Resource instantiation and asset reimporting module
"""

import os
import tempfile
import base64
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd

def create_resource(project_path: str, resource_type: str, save_path: str, properties_json: str = "{}") -> Dict[str, Any]:
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
    with tempfile.NamedTemporaryFile(suffix=".gd", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(helper_code)
        temp_script_path = tf.name

    cmd = build_godot_cmd(godot_bin, project_path=abs_project, headless=True, script=temp_script_path)

    try:
        res = run_godot_cmd(cmd, timeout=20)
        if res.returncode == 0 and "RES_SUCCESS" in res.stdout:
            return {"status": "success", "save_path": save_path, "message": f"Resource {resource_type} saved to {save_path}"}
        return {"status": "error", "message": res.stdout or res.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

def reimport_assets(project_path: str) -> Dict[str, Any]:
    """Forces Godot to scan filesystem and reimport new/modified assets."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    cmd = build_godot_cmd(godot_bin, project_path=abs_project, headless=True, editor=True, quit_after=True)

    try:
        res = run_godot_cmd(cmd, timeout=30)
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "message": "Filesystem scanned and reimported.",
            "stdout": res.stdout
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

