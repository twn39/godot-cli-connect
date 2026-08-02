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


def verify_import_status(project_path: str, auto_fix_valid: bool = True) -> dict[str, Any]:
    """
    Scans all .import files in the project to verify import validity.
    If imported .ctex/.stex cache files exist in .godot/imported and auto_fix_valid is True,
    updates stale `valid=false` lines to `valid=true` in .import files.
    """
    abs_project = os.path.abspath(project_path)
    imported_dir = os.path.join(abs_project, ".godot", "imported")
    valid_list = []
    invalid_list = []

    for root, _, files in os.walk(abs_project):
        if ".godot" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith(".import"):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    rel_p = os.path.relpath(full_p, abs_project)

                    is_invalid = "valid=false" in content
                    if is_invalid and auto_fix_valid and os.path.isdir(imported_dir):
                        asset_stem = f[:-7]  # remove .import suffix
                        matching_ctex = [
                            cf for cf in os.listdir(imported_dir) if cf.startswith(asset_stem)
                        ]
                        if matching_ctex:
                            new_content = content.replace("valid=false", "valid=true")
                            with open(full_p, "w", encoding="utf-8") as fp:
                                fp.write(new_content)
                            is_invalid = False

                    if is_invalid:
                        invalid_list.append(rel_p)
                    else:
                        valid_list.append(rel_p)
                except Exception:
                    pass

    return {
        "total": len(valid_list) + len(invalid_list),
        "valid": valid_list,
        "invalid": invalid_list,
        "valid_count": len(valid_list),
        "invalid_count": len(invalid_list),
    }


def fix_invalid_import_files(project_path: str) -> int:
    """Fixes `valid=false` lines in .import files so Godot will re-evaluates and import them."""
    abs_project = os.path.abspath(project_path)
    fixed = 0
    for root, _, files in os.walk(abs_project):
        if ".godot" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith(".import"):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    if "valid=false" in content:
                        new_content = content.replace("valid=false\n", "").replace("valid=false", "")
                        with open(full_p, "w", encoding="utf-8") as fp:
                            fp.write(new_content)
                        fixed += 1
                except Exception:
                    pass
    return fixed


def reimport_assets(project_path: str, clean: bool = False) -> dict[str, Any]:
    """
    Forces Godot to scan filesystem and reimport new/modified assets.

    Args:
        project_path: Path to Godot project directory.
        clean: If True, purges ``.godot/imported`` cache before scanning for a clean rebuild.
    """
    import shutil
    from .runner import build_godot_cmd, run_godot_cmd

    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)
    imported_dir = os.path.join(abs_project, ".godot", "imported")

    # Fix invalid .import files before running editor scan
    fix_invalid_import_files(abs_project)

    if clean and os.path.isdir(imported_dir):
        try:
            shutil.rmtree(imported_dir)
        except Exception:
            pass

    cmd = build_godot_cmd(
        godot_bin,
        project_path=abs_project,
        headless=True,
        editor=True,
        quit_after=True,
    )

    try:
        res = run_godot_cmd(cmd, timeout=30)
        status_info = verify_import_status(abs_project)

        # If invalid imports exist and we haven't cleaned yet, attempt auto-recovery
        if status_info["invalid_count"] > 0 and not clean:
            fix_invalid_import_files(abs_project)
            if os.path.isdir(imported_dir):
                try:
                    shutil.rmtree(imported_dir)
                except Exception:
                    pass
            res = run_godot_cmd(cmd, timeout=30)
            status_info = verify_import_status(abs_project)

        if res.returncode == 0:
            return ok(
                message=(
                    f"Assets reimported ({status_info['valid_count']} valid"
                    + (f", {status_info['invalid_count']} invalid" if status_info['invalid_count'] else "")
                    + ")."
                ),
                project_path=abs_project,
                stdout=res.stdout,
                returncode=res.returncode,
                clean=clean,
                imported_total=status_info["total"],
                valid_count=status_info["valid_count"],
                invalid_count=status_info["invalid_count"],
                invalid_files=status_info["invalid"] if status_info["invalid_count"] else None,
                mode="engine",
            )
        return err(
            f"Reimport finished with return code {res.returncode}",
            status="failure",
            project_path=abs_project,
            stdout=res.stdout,
            returncode=res.returncode,
            invalid_files=status_info["invalid"],
        )
    except Exception as e:
        return err(str(e))
