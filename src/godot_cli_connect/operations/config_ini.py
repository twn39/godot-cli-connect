"""
Offline project.godot INI parse/mutate helpers.

Shared by config_editor and any other operation that touches project.godot
without launching Godot.
"""

from __future__ import annotations

import json
import os
from typing import Any


def parse_config_value(raw_val: str) -> Any:
    """Parse raw CLI input strings into int, float, bool, or str."""
    raw_clean = raw_val.strip()
    while (
        (raw_clean.startswith('"') and raw_clean.endswith('"'))
        or (raw_clean.startswith("'") and raw_clean.endswith("'"))
    ) and len(raw_clean) >= 2:
        raw_clean = raw_clean[1:-1].strip()

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


def parse_project_godot(project_godot_path: str) -> dict[str, dict[str, str]]:
    """Parse project.godot into section -> {key: raw_value_string}."""
    sections: dict[str, dict[str, str]] = {"global": {}}
    current = "global"
    if not os.path.exists(project_godot_path):
        return sections
    with open(project_godot_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                current = stripped[1:-1]
                sections.setdefault(current, {})
                continue
            if "=" in stripped:
                k, v = stripped.split("=", 1)
                sections.setdefault(current, {})[k.strip()] = v.strip()
    return sections


def format_ini_value(parsed_val: Any) -> str:
    """Serialize a Python value into project.godot INI value text."""
    if isinstance(parsed_val, (dict, list)):
        return json.dumps(parsed_val)
    if parsed_val is True:
        return "true"
    if parsed_val is False:
        return "false"
    if isinstance(parsed_val, str):
        return f'"{parsed_val}"'
    return str(parsed_val)


def set_config_setting_offline(project_godot_path: str, setting_path: str, parsed_val: Any) -> bool:
    """Fallback offline text-based INI editor for project.godot."""
    if not os.path.exists(project_godot_path):
        return False

    # Godot convention: first path segment is the INI section, rest is the key
    # e.g. application/config/name -> [application] config/name=...
    parts = setting_path.split("/")
    if len(parts) > 1:
        section = parts[0]
        key = "/".join(parts[1:])
    else:
        section = "global"
        key = parts[0]

    val_str = format_ini_value(parsed_val)

    with open(project_godot_path, encoding="utf-8", errors="ignore") as f:
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
        for i, line in enumerate(new_lines):
            if line.strip() == f"[{section}]":
                new_lines.insert(i + 1, f"{key}={val_str}\n")
                break

    with open(project_godot_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True


def split_setting_path(setting_path: str) -> tuple[str, str]:
    """Split ``section/key/...`` into INI ``(section, key)``."""
    parts = setting_path.split("/")
    if len(parts) > 1:
        return parts[0], "/".join(parts[1:])
    return "global", parts[0]
