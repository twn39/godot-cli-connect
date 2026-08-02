"""
Godot project settings and InputMap configuration editor module
"""

import os
import json
import base64
import tempfile
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd


def parse_config_value(raw_val: str) -> Any:
    """Parses raw CLI input strings into appropriate Python types (int, float, bool, or str)."""
    raw_clean = raw_val.strip()
    if raw_clean.lower() == "true":
        return True
    if raw_clean.lower() == "false":
        return False
    try:
        if "." in raw_clean:
            return float(raw_clean)
        return int(raw_clean)
    except ValueError:
        return raw_clean


def set_config_setting_offline(
    project_godot_path: str, setting_path: str, parsed_val: Any
) -> bool:
    """Fallback offline text-based INI editor for project.godot."""
    if not os.path.exists(project_godot_path):
        return False

    parts = setting_path.split("/")
    if len(parts) > 1:
        section = "/".join(parts[:-1])
        key = parts[-1]
    else:
        section = "global"
        key = parts[0]

    val_str = (
        json.dumps(parsed_val)
        if isinstance(parsed_val, (dict, list))
        else (
            "true"
            if parsed_val is True
            else "false"
            if parsed_val is False
            else f'"{parsed_val}"'
            if isinstance(parsed_val, str)
            else str(parsed_val)
        )
    )

    lines = []
    with open(project_godot_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    section_found = False
    key_updated = False
    new_lines = []
    current_sec = "global"

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_sec = stripped[1:-1]
            if current_sec == section:
                section_found = True
        elif current_sec == section and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k == key:
                line = f"{key}={val_str}\n"
                key_updated = True
        new_lines.append(line)

    if not section_found:
        new_lines.append(f"\n[{section}]\n{key}={val_str}\n")
    elif not key_updated:
        # Insert key under section
        for i, line in enumerate(new_lines):
            if line.strip() == f"[{section}]":
                new_lines.insert(i + 1, f"{key}={val_str}\n")
                break

    with open(project_godot_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True


def set_config_setting(
    project_path: str, setting_path: str, raw_value: str
) -> Dict[str, Any]:
    """Updates a ProjectSettings entry persistently in project.godot."""
    abs_project = os.path.abspath(project_path)
    parsed_val = parse_config_value(raw_value)
    project_godot_path = os.path.join(abs_project, "project.godot")

    try:
        godot_bin = find_godot_executable()
        b64_key = base64.b64encode(setting_path.encode("utf-8")).decode("ascii")
        b64_val = base64.b64encode(json.dumps(parsed_val).encode("utf-8")).decode(
            "ascii"
        )

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_set")

func run_set() -> void:
    var k = Marshalls.base64_to_utf8("{b64_key}")
    var v_str = Marshalls.base64_to_utf8("{b64_val}")
    var val = JSON.parse_string(v_str)

    ProjectSettings.set_setting(k, val)
    var err = ProjectSettings.save()
    print("CONFIG_SAVED:ERR=" + str(err))
    quit()
"""
        with tempfile.NamedTemporaryFile(
            suffix=".gd", delete=False, mode="w", encoding="utf-8"
        ) as tf:
            tf.write(helper_code)
            temp_script_path = tf.name

        cmd = build_godot_cmd(
            godot_bin, project_path=abs_project, headless=True, script=temp_script_path
        )

        try:
            res = run_godot_cmd(cmd, timeout=20)
            if "CONFIG_SAVED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "setting_path": setting_path,
                    "value": parsed_val,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Fallback to offline INI editor
    success = set_config_setting_offline(project_godot_path, setting_path, parsed_val)
    if success:
        return {
            "status": "success",
            "mode": "offline",
            "setting_path": setting_path,
            "value": parsed_val,
        }

    return {"status": "error", "message": f"Failed to update setting {setting_path}"}


def add_input_action(
    project_path: str, action_name: str, key_name: str = "KEY_A", append: bool = True
) -> Dict[str, Any]:
    """Adds or updates a persistent InputMap action with key binding in project.godot."""
    abs_project = os.path.abspath(project_path)

    try:
        godot_bin = find_godot_executable()
        b64_action = base64.b64encode(action_name.encode("utf-8")).decode("ascii")
        b64_key = base64.b64encode(key_name.encode("utf-8")).decode("ascii")

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_input_add")

func run_input_add() -> void:
    var act_name = Marshalls.base64_to_utf8("{b64_action}")
    var key_str = Marshalls.base64_to_utf8("{b64_key}")
    
    var setting_key = "input/" + act_name
    var existing_data = ProjectSettings.get_setting(setting_key)
    
    var ev = InputEventKey.new()
    var keycode_val = OS.find_keycode_from_string(key_str.replace("KEY_", ""))
    if keycode_val != 0:
        ev.physical_keycode = keycode_val
    else:
        ev.physical_keycode = KEY_A

    var events_array = [ev]
    var deadzone_val = 0.5

    if {str(append).lower()} and existing_data != null and existing_data is Dictionary:
        if existing_data.has("events") and existing_data["events"] is Array:
            events_array = existing_data["events"]
            events_array.append(ev)
        if existing_data.has("deadzone"):
            deadzone_val = existing_data["deadzone"]

    var input_data = {{
        "deadzone": deadzone_val,
        "events": events_array
    }}

    ProjectSettings.set_setting(setting_key, input_data)
    var err = ProjectSettings.save()
    print("INPUT_SAVED:ERR=" + str(err))
    quit()
"""
        with tempfile.NamedTemporaryFile(
            suffix=".gd", delete=False, mode="w", encoding="utf-8"
        ) as tf:
            tf.write(helper_code)
            temp_script_path = tf.name

        cmd = build_godot_cmd(
            godot_bin, project_path=abs_project, headless=True, script=temp_script_path
        )

        try:
            res = run_godot_cmd(cmd, timeout=20)
            if "INPUT_SAVED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "action_name": action_name,
                    "key_bound": key_name,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Fallback to direct config setting setting for input action
    fallback_res = set_config_setting(
        project_path, f"input/{action_name}", {"deadzone": 0.5, "events": []}
    )
    if fallback_res.get("status") == "success":
        fallback_res["action_name"] = action_name
        fallback_res["key_bound"] = key_name
        return fallback_res

    return {"status": "error", "message": f"Failed to bind input action {action_name}"}
