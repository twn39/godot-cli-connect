"""
Godot ClassDB targeted inspection module
"""

import base64
import json
import os
import tempfile
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd


def get_class_info_engine(class_name: str, project_path: str) -> dict[str, Any]:
    """Queries ClassDB in headless Godot runtime for class methods, properties, signals, and inheritance."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    b64_name = base64.b64encode(class_name.encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_query")

func run_query() -> void:
    var c_name = Marshalls.base64_to_utf8("{b64_name}")
    if not ClassDB.class_exists(c_name):
        print("CLASS_ERR:Class " + c_name + " does not exist in ClassDB")
        quit(1)
        return

    var parent_cls = ClassDB.get_parent_class(c_name)
    var methods = []
    for m in ClassDB.class_get_method_list(c_name, true):
        var m_name = str(m["name"])
        if not m_name.begins_with("_"):
            var args = []
            for a in m.get("args", []):
                args.append({{"name": str(a["name"]), "type": str(a["type"])}})
            methods.append({{
                "name": m_name,
                "args": args
            }})

    var properties = []
    for p in ClassDB.class_get_property_list(c_name, true):
        var p_name = str(p["name"])
        if not p_name.contains("."):
            properties.append({{
                "name": p_name,
                "type": str(p["type"])
            }})

    var signals_list = []
    for s in ClassDB.class_get_signal_list(c_name, true):
        signals_list.append({{
            "name": str(s["name"])
        }})

    var payload = {{
        "name": c_name,
        "inherits": parent_cls,
        "methods": methods,
        "properties": properties,
        "signals": signals_list,
        "docs_url": "https://docs.godotengine.org/en/stable/classes/class_" + c_name.to_lower() + ".html"
    }}

    print("CLASS_INFO_JSON:" + JSON.stringify(payload))
    quit()
"""

    with tempfile.NamedTemporaryFile(suffix=".gd", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(helper_code)
        temp_script_path = tf.name

    cmd = build_godot_cmd(
        godot_bin, project_path=abs_project, headless=True, script=temp_script_path
    )

    try:
        res = run_godot_cmd(cmd, timeout=20)
        for line in res.stdout.splitlines():
            if line.startswith("CLASS_INFO_JSON:"):
                raw_json = line[len("CLASS_INFO_JSON:") :].strip()
                data = json.loads(raw_json)
                return ok(mode="engine", class_info=data)
        return err(f"Class {class_name} not found or failed to query ClassDB")
    except Exception as e:
        return err(str(e))
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def get_class_info_json(class_name: str, api_json_path: str) -> dict[str, Any] | None:
    """Fast local lookup of class details from dumped extension_api.json."""
    if not os.path.exists(api_json_path):
        return None

    try:
        with open(api_json_path, encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        classes = data.get("classes", [])
        for c in classes:
            if c.get("name") == class_name:
                methods = []
                for m in c.get("methods", []):
                    m_name = m.get("name", "")
                    if not m_name.startswith("_"):
                        args = [
                            {"name": a.get("name"), "type": a.get("type")}
                            for a in m.get("arguments", [])
                        ]
                        methods.append({"name": m_name, "args": args})

                properties = [
                    {"name": p.get("name"), "type": p.get("type")} for p in c.get("properties", [])
                ]
                signals_list = [{"name": s.get("name")} for s in c.get("signals", [])]

                return {
                    "name": class_name,
                    "inherits": c.get("inherits", "Object"),
                    "methods": methods,
                    "properties": properties,
                    "signals": signals_list,
                    "docs_url": f"https://docs.godotengine.org/en/stable/classes/class_{class_name.lower()}.html",
                }
    except Exception:
        pass
    return None


def get_class_info(class_name: str, project_path: str = ".") -> dict[str, Any]:
    """Targeted ClassDB inspection query for Godot 4 classes."""
    abs_project = os.path.abspath(project_path)
    api_json_path = os.path.join(abs_project, "extension_api.json")

    # Try fast local lookup first
    cached_info = get_class_info_json(class_name, api_json_path)
    if cached_info:
        return ok(mode="cache", class_info=cached_info)

    # Fallback to runtime engine query
    return get_class_info_engine(class_name, abs_project)
