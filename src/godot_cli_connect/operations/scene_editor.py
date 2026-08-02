"""
Godot .tscn scene creation, node modification, property editing, and node deletion.

Policy layer: try headless engine mutation first, then offline .tscn text fallback.
GDScript templates live in ``scene_gdscript``; offline helpers in ``scene_tscn``;
path resolution in ``paths``; temp scripts in ``runner``.
"""

from __future__ import annotations

import os
import re
from typing import Any, Literal

from ..finder import find_godot_executable
from ..models import err, ok
from .paths import resolve_res_path
from .runner import run_godot_script
from .scene_gdscript import (
    script_add_node,
    script_attach_script,
    script_connect_signal,
    script_create_scene,
    script_disconnect_signal,
    script_edit_node,
    script_remove_node,
    script_rename_node,
    script_reparent_node,
)
from .scene_tscn import (
    add_node_to_scene_offline,
    attach_script_offline,
    connect_signal_offline,
    create_scene_offline,
    disconnect_signal_offline,
    edit_node_in_scene_offline,
    remove_node_from_scene_offline,
    rename_node_offline,
    reparent_node_offline,
)

# Dual-mode policy for scene mutations (CI can force offline for determinism).
EditMode = Literal["auto", "engine", "offline"]

# Re-export offline helpers for backward-compatible imports/tests
__all__ = [
    "EditMode",
    "add_node_to_scene",
    "attach_script",
    "add_node_to_scene_offline",
    "attach_script_offline",
    "connect_signal",
    "connect_signal_offline",
    "create_scene",
    "create_scene_offline",
    "disconnect_signal",
    "disconnect_signal_offline",
    "edit_node_in_scene",
    "edit_node_in_scene_offline",
    "inspect_signals",
    "remove_node_from_scene",
    "remove_node_from_scene_offline",
    "rename_node",
    "rename_node_offline",
    "reparent_node",
    "reparent_node_offline",
]


def _normalize_mode(mode: str | None) -> EditMode:
    if mode in ("auto", "engine", "offline"):
        return mode  # type: ignore[return-value]
    return "auto"


def _run_engine_script(
    project_path: str,
    script_source: str,
    success_marker: str,
    *,
    timeout: int = 20,
) -> bool:
    """Run a headless GDScript helper; return True when success marker is present."""
    godot_bin = find_godot_executable()
    res = run_godot_script(godot_bin, project_path, script_source, timeout=timeout)
    return success_marker in res.stdout


def create_scene(
    project_path: str,
    save_path: str,
    root_type: str = "Node2D",
    root_name: str | None = None,
    script_path: str | None = None,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Creates a new Godot .tscn scene file with a specified root node type and optional script attachment."""
    abs_project, abs_save_path, res_save_path = resolve_res_path(project_path, save_path)
    actual_root_name = root_name if root_name else root_type
    mode = _normalize_mode(mode)
    payload = {
        "save_path": res_save_path,
        "root_name": actual_root_name,
        "root_type": root_type,
        "script_path": script_path,
    }

    if mode in ("auto", "engine"):
        try:
            helper = script_create_scene(root_type, actual_root_name, res_save_path, script_path)
            if _run_engine_script(abs_project, helper, "SCENE_CREATED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(
                    f"Engine create_scene failed for {res_save_path}",
                    **payload,
                )

    if mode in ("auto", "offline"):
        if create_scene_offline(abs_save_path, root_type, actual_root_name, script_path):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline create_scene failed for {res_save_path}", **payload)

    return err(f"Failed to create scene at {res_save_path}", **payload)


def add_node_to_scene(
    project_path: str,
    scene_path: str,
    node_name: str,
    node_type: str = "Node2D",
    parent_path: str = ".",
    script_path: str | None = None,
    properties_json: str = "{}",
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Adds a child node to an existing Godot .tscn scene file with owner hierarchy and script bindings."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    payload = {
        "scene_path": res_scene_path,
        "node_name": node_name,
        "node_type": node_type,
        "parent_path": parent_path,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_add_node(
                res_scene_path,
                node_name,
                node_type,
                parent_path,
                script_path,
                properties_json,
            )
            if _run_engine_script(abs_project, helper, "NODE_ADDED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(
                    f"Engine add_node failed for {node_name}",
                    **payload,
                )

    if mode in ("auto", "offline"):
        if add_node_to_scene_offline(
            abs_scene_path,
            node_name,
            node_type,
            parent_path,
            script_path,
            properties_json=properties_json,
        ):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline add_node failed for {node_name}", **payload)

    return err(f"Failed to add node {node_name} to scene {res_scene_path}", **payload)


def edit_node_in_scene(
    project_path: str,
    scene_path: str,
    node_path: str,
    properties_json: str = "{}",
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Edits properties of an existing node in a .tscn scene file."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    payload = {
        "scene_path": res_scene_path,
        "node_path": node_path,
        "properties": properties_json,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_edit_node(res_scene_path, node_path, properties_json)
            if _run_engine_script(abs_project, helper, "NODE_EDITED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine edit_node failed for {node_path}", **payload)

    if mode in ("auto", "offline"):
        if edit_node_in_scene_offline(abs_scene_path, node_path, properties_json):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline edit_node failed for {node_path}", **payload)

    return err(f"Failed to edit node {node_path} in scene {res_scene_path}", **payload)


def remove_node_from_scene(
    project_path: str,
    scene_path: str,
    node_path: str,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Removes a target child node synchronously from a .tscn scene file."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    payload = {"scene_path": res_scene_path, "removed_node": node_path}

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_remove_node(res_scene_path, node_path)
            if _run_engine_script(abs_project, helper, "NODE_REMOVED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine remove_node failed for {node_path}", **payload)

    if mode in ("auto", "offline"):
        if remove_node_from_scene_offline(abs_scene_path, node_path):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline remove_node failed for {node_path}", **payload)

    return err(f"Failed to remove node {node_path} from scene {res_scene_path}", **payload)


def connect_signal(
    project_path: str,
    scene_path: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
    deferred: bool = False,
    one_shot: bool = False,
    flags: int = 0,
    binds_json: str = "[]",
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Connects a signal between nodes in a .tscn scene file."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    total_flags = flags | (1 if deferred else 0) | (4 if one_shot else 0)
    payload = {
        "scene_path": res_scene_path,
        "from_node": from_node,
        "signal_name": signal_name,
        "to_node": to_node,
        "method_name": method_name,
        "flags": total_flags,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_connect_signal(
                res_scene_path,
                from_node,
                signal_name,
                to_node,
                method_name,
                total_flags,
                binds_json,
            )
            if _run_engine_script(abs_project, helper, "SIG_CONNECTED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine connect_signal failed for {signal_name}", **payload)

    if mode in ("auto", "offline"):
        if connect_signal_offline(
            abs_scene_path,
            from_node,
            signal_name,
            to_node,
            method_name,
            total_flags,
        ):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline connect_signal failed for {signal_name}", **payload)

    return err(
        f"Failed to connect signal {signal_name} from {from_node} to {to_node}.{method_name}",
        **payload,
    )


def disconnect_signal(
    project_path: str,
    scene_path: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Disconnects a signal between nodes in a .tscn scene file."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    payload = {
        "scene_path": res_scene_path,
        "from_node": from_node,
        "signal_name": signal_name,
        "to_node": to_node,
        "method_name": method_name,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_disconnect_signal(
                res_scene_path, from_node, signal_name, to_node, method_name
            )
            if _run_engine_script(abs_project, helper, "SIG_DISCONNECTED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine disconnect_signal failed for {signal_name}", **payload)

    if mode in ("auto", "offline"):
        if disconnect_signal_offline(abs_scene_path, from_node, signal_name, to_node, method_name):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline disconnect_signal failed for {signal_name}", **payload)

    return err(
        f"Failed to disconnect signal {signal_name} from {from_node} to {to_node}.{method_name}",
        **payload,
    )


def rename_node(
    project_path: str,
    scene_path: str,
    node_path: str,
    new_name: str,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Renames an existing node in a .tscn scene file with cascading path updates."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    old_leaf_name = os.path.basename(node_path.rstrip("/"))
    payload = {
        "scene_path": res_scene_path,
        "old_node_path": node_path,
        "new_name": new_name,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_rename_node(res_scene_path, node_path, new_name)
            if _run_engine_script(abs_project, helper, "NODE_RENAMED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine rename_node failed for {node_path}", **payload)

    if mode in ("auto", "offline"):
        if rename_node_offline(abs_scene_path, old_leaf_name, new_name):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline rename_node failed for {node_path}", **payload)

    return err(
        f"Failed to rename node {node_path} to {new_name} in scene {res_scene_path}",
        **payload,
    )


def reparent_node(
    project_path: str,
    scene_path: str,
    node_path: str,
    new_parent_path: str,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Reparents a node to a new parent in a .tscn scene file."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)
    leaf_node_name = os.path.basename(node_path.rstrip("/"))
    payload = {
        "scene_path": res_scene_path,
        "node_path": node_path,
        "new_parent_path": new_parent_path,
    }

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    if mode in ("auto", "engine"):
        try:
            helper = script_reparent_node(res_scene_path, node_path, new_parent_path)
            if _run_engine_script(abs_project, helper, "NODE_REPARENTED:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine reparent_node failed for {node_path}", **payload)

    if mode in ("auto", "offline"):
        if reparent_node_offline(abs_scene_path, leaf_node_name, new_parent_path):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline reparent_node failed for {node_path}", **payload)

    return err(
        f"Failed to reparent node {node_path} to {new_parent_path} in scene {res_scene_path}",
        **payload,
    )


def inspect_signals(
    project_path: str,
    scene_path: str,
) -> dict[str, Any]:
    """Inspects and returns all signal connections defined in a .tscn scene file."""
    _abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    connections = []
    try:
        with open(abs_scene_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("[connection "):
                    sig = re.search(r'signal="([^"]+)"', line_str)
                    from_n = re.search(r'from="([^"]+)"', line_str)
                    to_n = re.search(r'to="([^"]+)"', line_str)
                    mth = re.search(r'method="([^"]+)"', line_str)
                    flg = re.search(r"flags=(\d+)", line_str)

                    if sig and from_n and to_n and mth:
                        connections.append(
                            {
                                "signal": sig.group(1),
                                "from": from_n.group(1),
                                "to": to_n.group(1),
                                "method": mth.group(1),
                                "flags": int(flg.group(1)) if flg else 0,
                            }
                        )
    except Exception as e:
        return err(str(e))

    return ok(
        mode="offline",
        scene_path=res_scene_path,
        connections_count=len(connections),
        connections=connections,
    )


def attach_script(
    project_path: str,
    scene_path: str,
    node_path: str,
    script_path: str,
    *,
    mode: EditMode = "auto",
) -> dict[str, Any]:
    """Attach a GDScript resource path to a node in a scene (engine then offline)."""
    abs_project, abs_scene_path, res_scene_path = resolve_res_path(project_path, scene_path)
    mode = _normalize_mode(mode)

    if not os.path.exists(abs_scene_path):
        return err(f"Scene file not found at {abs_scene_path}")

    # Normalize script to res:// when possible
    if not script_path.startswith("res://"):
        _, _abs_script, res_script = resolve_res_path(project_path, script_path)
        script_res = res_script
    else:
        script_res = script_path

    payload = {
        "scene_path": res_scene_path,
        "node_path": node_path,
        "script_path": script_res,
    }

    if mode in ("auto", "engine"):
        try:
            helper = script_attach_script(res_scene_path, node_path, script_res)
            if _run_engine_script(abs_project, helper, "ATTACH_OK:ERR=0"):
                return ok(mode="engine", **payload)
        except Exception:
            if mode == "engine":
                return err(f"Engine attach_script failed for {node_path}", **payload)

    if mode in ("auto", "offline"):
        if attach_script_offline(abs_scene_path, node_path, script_res):
            return ok(mode="offline", **payload)
        if mode == "offline":
            return err(f"Offline attach_script failed for {node_path}", **payload)

    return err(
        f"Failed to attach script {script_res} to {node_path} in {res_scene_path}",
        **payload,
    )
