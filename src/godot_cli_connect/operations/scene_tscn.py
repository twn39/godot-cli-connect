"""
Offline text-based .tscn manipulation (no Godot binary required).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from .tscn_common import (
    node_header_parent as _node_header_parent,
)
from .tscn_common import (
    split_node_blocks as _split_node_blocks,
)


def format_tscn_value(value: Any) -> str:
    """Serialize a Python value into Godot .tscn property syntax."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if value is None:
        return '""'
    if isinstance(value, str):
        # Pass through Godot constructor / enum-like literals.
        if re.match(
            r"^(Vector[23]i?|Color|Rect2|Transform2D|Transform3D|NodePath|"
            r"Packed(String|Int32|Float32|Vector2|Color)Array|ExtResource|"
            r"SubResource)\s*\(",
            value,
        ):
            return value
        if value in {"true", "false"} or re.fullmatch(r"-?\d+(\.\d+)?", value):
            return value
        return json.dumps(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return json.dumps(str(value))


def _parse_properties_json(properties_json: str | None) -> dict[str, Any]:
    if not properties_json or properties_json.strip() in ("", "{}"):
        return {}
    try:
        data = json.loads(properties_json)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def create_scene_offline(
    abs_scene: str,
    root_type: str,
    root_name: str,
    script_path: str | None = None,
) -> bool:
    """Fallback offline text-based .tscn creator with script support."""
    try:
        dir_path = os.path.dirname(abs_scene)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        if script_path:
            content = f"""[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="{script_path}" id="1_script"]

[node name="{root_name}" type="{root_type}"]
script = ExtResource("1_script")
"""
        else:
            content = f"""[gd_scene format=3]

[node name="{root_name}" type="{root_type}"]
"""
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def add_node_to_scene_offline(
    abs_scene: str,
    node_name: str,
    node_type: str,
    parent_path: str,
    script_path: str | None,
    properties_json: str | None = None,
) -> bool:
    """Fallback offline text-based .tscn node adder with optional property lines."""
    if not os.path.exists(abs_scene):
        return False

    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        ext_insert_idx = -1
        script_id = None
        existing_ids: set[str] = set()

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[ext_resource"):
                ext_insert_idx = idx
                mid = re.search(r'id="([^"]+)"', stripped)
                if mid:
                    existing_ids.add(mid.group(1))

        if script_path:
            # Avoid duplicate ext_resource for same path when possible.
            found_existing = None
            for line in lines:
                if line.strip().startswith("[ext_resource") and f'path="{script_path}"' in line:
                    mid = re.search(r'id="([^"]+)"', line)
                    if mid:
                        found_existing = mid.group(1)
                        break
            if found_existing:
                script_id = found_existing
            else:
                n = 1
                while f"{n}_script" in existing_ids:
                    n += 1
                script_id = f"{n}_script"
                ext_line = f'[ext_resource type="Script" path="{script_path}" id="{script_id}"]\n'
                if ext_insert_idx != -1:
                    lines.insert(ext_insert_idx + 1, ext_line)
                else:
                    lines.insert(1, ext_line)

        props = _parse_properties_json(properties_json)
        node_block = f'[node name="{node_name}" type="{node_type}" parent="{parent_path}"]\n'
        if script_id:
            node_block += f'script = ExtResource("{script_id}")\n'
        for key, val in props.items():
            if key == "script":
                continue
            node_block += f"{key} = {format_tscn_value(val)}\n"

        lines.append(f"\n{node_block}")
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False


def edit_node_in_scene_offline(
    abs_scene: str,
    node_path: str,
    properties_json: str = "{}",
) -> bool:
    """Update property lines under a node section (matched by leaf name)."""
    if not os.path.exists(abs_scene):
        return False
    props = _parse_properties_json(properties_json)
    if not props:
        return True

    leaf = os.path.basename(node_path.rstrip("/")) or node_path
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        blocks = _split_node_blocks(lines)
        target: tuple[int, int] | None = None
        for start, end, name in blocks:
            if name == leaf:
                target = (start, end)
                break
        if target is None:
            return False

        start, end = target
        header = lines[start]
        body = lines[start + 1 : end]

        # Map existing property keys -> line index in body
        key_to_idx: dict[str, int] = {}
        for i, line in enumerate(body):
            stripped = line.strip()
            if not stripped or stripped.startswith("[") or stripped.startswith(";"):
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                key_to_idx[k] = i

        for key, val in props.items():
            rendered = f"{key} = {format_tscn_value(val)}\n"
            if key in key_to_idx:
                body[key_to_idx[key]] = rendered
            else:
                body.append(rendered)

        new_lines = lines[:start] + [header] + body + lines[end:]
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def remove_node_from_scene_offline(abs_scene: str, node_path: str) -> bool:
    """
    Remove a node block (by leaf name) plus simple child nodes and connections
    that reference it.
    """
    if not os.path.exists(abs_scene):
        return False
    if node_path in (".", "", "/"):
        return False  # never remove root via offline path

    leaf = os.path.basename(node_path.rstrip("/")) or node_path
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        blocks = _split_node_blocks(lines)
        if not blocks:
            return False

        # Root is first node block without parent= typically
        names_to_remove: set[str] = {leaf}
        # Children whose parent is the leaf or starts with leaf/
        changed = True
        while changed:
            changed = False
            for start, _end, name in blocks:
                if name is None or name in names_to_remove:
                    continue
                header = lines[start]
                parent = _node_header_parent(header)
                if parent is None:
                    continue
                if parent == leaf or parent.startswith(f"{leaf}/") or parent.endswith(f"/{leaf}"):
                    names_to_remove.add(name)
                    changed = True
                # parent path segments containing leaf as final component
                if parent.split("/")[-1] == leaf:
                    names_to_remove.add(name)
                    changed = True

        remove_ranges: list[tuple[int, int]] = []
        for start, end, name in blocks:
            if name in names_to_remove:
                remove_ranges.append((start, end))

        if not remove_ranges:
            return False

        skip = set()
        for start, end in remove_ranges:
            skip.update(range(start, end))

        new_lines: list[str] = []
        for i, line in enumerate(lines):
            if i in skip:
                continue
            stripped = line.strip()
            if stripped.startswith("[connection "):
                # Drop connections involving removed nodes
                drop = False
                for nm in names_to_remove:
                    if (
                        f'from="{nm}"' in stripped
                        or f'to="{nm}"' in stripped
                        or f'from="{nm}/' in stripped
                        or f'to="{nm}/' in stripped
                    ):
                        drop = True
                        break
                if drop:
                    continue
            new_lines.append(line)

        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def attach_script_offline(
    abs_scene: str,
    node_path: str,
    script_path: str,
) -> bool:
    """Attach a Script ext_resource to a node offline."""
    if not os.path.exists(abs_scene):
        return False
    leaf = os.path.basename(node_path.rstrip("/")) if node_path not in (".", "") else None
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Ensure ext_resource
        script_id = None
        ext_insert_idx = -1
        existing_ids: set[str] = set()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[ext_resource"):
                ext_insert_idx = idx
                mid = re.search(r'id="([^"]+)"', stripped)
                if mid:
                    existing_ids.add(mid.group(1))
                if f'path="{script_path}"' in stripped:
                    mid = re.search(r'id="([^"]+)"', stripped)
                    if mid:
                        script_id = mid.group(1)

        if script_id is None:
            n = 1
            while f"{n}_script" in existing_ids:
                n += 1
            script_id = f"{n}_script"
            ext_line = f'[ext_resource type="Script" path="{script_path}" id="{script_id}"]\n'
            if ext_insert_idx != -1:
                lines.insert(ext_insert_idx + 1, ext_line)
            else:
                # after [gd_scene ...]
                lines.insert(1, ext_line)

        blocks = _split_node_blocks(lines)
        target = None
        for start, end, name in blocks:
            if leaf is None:
                # root = first node
                target = (start, end)
                break
            if name == leaf:
                target = (start, end)
                break
        if target is None:
            return False

        start, end = target
        header = lines[start]
        body = lines[start + 1 : end]
        script_line = f'script = ExtResource("{script_id}")\n'
        found = False
        for i, line in enumerate(body):
            if line.strip().startswith("script "):
                body[i] = script_line
                found = True
                break
        if not found:
            body.insert(0, script_line)

        new_lines = lines[:start] + [header] + body + lines[end:]
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def connect_signal_offline(
    abs_scene: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
    flags: int = 0,
) -> bool:
    """Fallback offline text-based .tscn signal connection adder."""
    if not os.path.exists(abs_scene):
        return False
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        conn_str = (
            f'signal="{signal_name}" from="{from_node}" to="{to_node}" method="{method_name}"'
        )
        for line in lines:
            if line.strip().startswith("[connection") and conn_str in line:
                return True  # Already connected

        flags_attr = f" flags={flags}" if flags else ""
        conn_line = f"[connection {conn_str}{flags_attr}]\n"
        lines.append(f"\n{conn_line}")

        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False


def disconnect_signal_offline(
    abs_scene: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
) -> bool:
    """Fallback offline text-based .tscn signal disconnection remover."""
    if not os.path.exists(abs_scene):
        return False
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        conn_match = (
            f'signal="{signal_name}" from="{from_node}" to="{to_node}" method="{method_name}"'
        )
        new_lines = [
            line
            for line in lines
            if not (line.strip().startswith("[connection") and conn_match in line)
        ]

        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def rename_node_offline(abs_scene: str, old_name: str, new_name: str) -> bool:
    """Fallback offline text-based .tscn node renamer with cascading path updates."""
    if not os.path.exists(abs_scene):
        return False
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            s_line = line
            if s_line.startswith("[node "):
                s_line = s_line.replace(f'name="{old_name}"', f'name="{new_name}"')
                s_line = s_line.replace(f'parent="{old_name}"', f'parent="{new_name}"')
                s_line = s_line.replace(f'parent="{old_name}/', f'parent="{new_name}/')
            elif s_line.startswith("[connection "):
                s_line = s_line.replace(f'from="{old_name}"', f'from="{new_name}"')
                s_line = s_line.replace(f'from="{old_name}/', f'from="{new_name}/')
                s_line = s_line.replace(f'to="{old_name}"', f'to="{new_name}"')
                s_line = s_line.replace(f'to="{old_name}/', f'to="{new_name}/')
            new_lines.append(s_line)

        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def reparent_node_offline(abs_scene: str, node_name: str, new_parent: str) -> bool:
    """Fallback offline text-based .tscn node reparenter."""
    if not os.path.exists(abs_scene):
        return False
    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            s_line = line
            if s_line.startswith("[node ") and f'name="{node_name}"' in s_line:
                if 'parent="' in s_line:
                    s_line = re.sub(r'parent="[^"]*"', f'parent="{new_parent}"', s_line)
                else:
                    s_line = s_line.rstrip("]\n") + f' parent="{new_parent}"]\n'
            new_lines.append(s_line)

        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False
