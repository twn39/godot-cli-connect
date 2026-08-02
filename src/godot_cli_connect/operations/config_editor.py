"""
Godot project settings and InputMap configuration editor module
"""

import base64
import json
import os
import tempfile
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .config_ini import (
    parse_config_value,
    parse_project_godot,
    set_config_setting_offline,
    split_setting_path,
)
from .runner import build_godot_cmd, run_godot_cmd

# Re-export offline helpers for callers/tests that import from this module.
__all__ = [
    "add_autoload",
    "add_input_action",
    "get_config_setting",
    "list_autoloads",
    "parse_config_value",
    "remove_autoload",
    "set_config_setting",
    "set_config_setting_offline",
]


def set_config_setting(project_path: str, setting_path: str, raw_value: str) -> dict[str, Any]:
    """Updates a ProjectSettings entry persistently in project.godot."""
    abs_project = os.path.abspath(project_path)
    parsed_val = parse_config_value(raw_value)
    project_godot_path = os.path.join(abs_project, "project.godot")

    try:
        godot_bin = find_godot_executable()
        b64_key = base64.b64encode(setting_path.encode("utf-8")).decode("ascii")
        b64_val = base64.b64encode(json.dumps(parsed_val).encode("utf-8")).decode("ascii")

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
                return ok(
                    mode="engine",
                    setting_path=setting_path,
                    value=parsed_val,
                )
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Fallback to offline INI editor
    success = set_config_setting_offline(project_godot_path, setting_path, parsed_val)
    if success:
        return ok(
            mode="offline",
            setting_path=setting_path,
            value=parsed_val,
        )

    return err(f"Failed to update setting {setting_path}")


def add_input_action(
    project_path: str, action_name: str, key_name: str = "KEY_A", append: bool = True
) -> dict[str, Any]:
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
                return ok(
                    mode="engine",
                    action_name=action_name,
                    key_bound=key_name,
                )
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Fallback to direct config setting for input action
    fallback_res = set_config_setting(
        project_path, f"input/{action_name}", '{"deadzone": 0.5, "events": []}'
    )
    if fallback_res.get("status") == "success":
        fallback_res["action_name"] = action_name
        fallback_res["key_bound"] = key_name
        return fallback_res

    return err(f"Failed to bind input action {action_name}")


def get_config_setting(project_path: str, setting_path: str) -> dict[str, Any]:
    """Read a single project.godot setting (offline INI parse)."""
    abs_project = os.path.abspath(project_path)
    project_godot_path = os.path.join(abs_project, "project.godot")
    if not os.path.exists(project_godot_path):
        return err(f"No project.godot found at {abs_project}")

    section, key = split_setting_path(setting_path)

    sections = parse_project_godot(project_godot_path)
    raw = None
    used_section = section
    if section in sections and key in sections[section]:
        raw = sections[section][key]
    elif "application" in sections and setting_path in sections["application"]:
        # rare: full path as key
        raw = sections["application"][setting_path]
        used_section = "application"
        key = setting_path
    elif section != "application" and "application" in sections:
        # allow config/name without application/ prefix
        if setting_path in sections["application"]:
            raw = sections["application"][setting_path]
            used_section = "application"
            key = setting_path

    if raw is None:
        return err(
            f"Setting not found: {setting_path}",
            setting_path=setting_path,
        )

    # Strip surrounding quotes for display
    display = raw
    if len(display) >= 2 and display[0] == '"' and display[-1] == '"':
        display = display[1:-1]
    parsed: Any = display
    if display.lower() == "true":
        parsed = True
    elif display.lower() == "false":
        parsed = False
    else:
        try:
            if "." in display:
                parsed = float(display)
            else:
                parsed = int(display)
        except ValueError:
            parsed = display

    return ok(
        mode="offline",
        setting_path=setting_path,
        section=used_section,
        key=key,
        raw=raw,
        value=parsed,
    )


def add_autoload(
    project_path: str,
    name: str,
    script_path: str,
    *,
    enabled: bool = True,
) -> dict[str, Any]:
    """
    Register an Autoload singleton in project.godot.

    Godot stores: name="*res://path.gd" (leading * means enabled).
    """
    abs_project = os.path.abspath(project_path)
    project_godot = os.path.join(abs_project, "project.godot")
    if not os.path.exists(project_godot):
        return err(f"No project.godot found at {abs_project}")

    res_path = script_path
    if not res_path.startswith("res://"):
        try:
            res_path = f"res://{os.path.relpath(os.path.abspath(os.path.join(abs_project, script_path)), abs_project)}"
        except ValueError:
            res_path = f"res://{os.path.basename(script_path)}"

    # set_config_setting_offline string-quotes values; store *path for enabled autoloads
    raw_for_offline = f"*{res_path}" if enabled else res_path
    wrote = set_config_setting_offline(project_godot, f"autoload/{name}", raw_for_offline)
    if wrote:
        return ok(
            mode="offline",
            autoload_name=name,
            path=res_path,
            enabled=enabled,
        )
    return err(f"Failed to add autoload {name}")


def remove_autoload(project_path: str, name: str) -> dict[str, Any]:
    """Remove an Autoload entry from project.godot."""
    abs_project = os.path.abspath(project_path)
    project_godot = os.path.join(abs_project, "project.godot")
    if not os.path.exists(project_godot):
        return err(f"No project.godot found at {abs_project}")
    try:
        with open(project_godot, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        current = "global"
        new_lines = []
        removed = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                current = stripped[1:-1]
                new_lines.append(line)
                continue
            if current == "autoload" and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k == name:
                    removed = True
                    continue
            new_lines.append(line)
        if not removed:
            return err(
                f"Autoload not found: {name}",
                autoload_name=name,
            )
        with open(project_godot, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return ok(
            mode="offline",
            autoload_name=name,
            message=f"Removed autoload {name}",
        )
    except Exception as e:
        return err(str(e))


def list_autoloads(project_path: str) -> dict[str, Any]:
    """List Autoload singletons from project.godot."""
    abs_project = os.path.abspath(project_path)
    project_godot = os.path.join(abs_project, "project.godot")
    if not os.path.exists(project_godot):
        return err(f"No project.godot found at {abs_project}")
    sections = parse_project_godot(project_godot)
    autos = sections.get("autoload", {})
    items = []
    for name, raw in autos.items():
        val = raw.strip().strip('"')
        enabled = val.startswith("*")
        path = val[1:] if enabled else val
        items.append({"name": name, "path": path, "enabled": enabled, "raw": raw})
    return ok(
        mode="offline",
        count=len(items),
        autoloads=items,
    )
