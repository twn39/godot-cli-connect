"""
Godot .tscn scene file inspection and hierarchy parsing module
"""

import base64
import os
import re
import tempfile
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd
from .tscn_common import (
    SECTION_RE,
    empty_node_shell,
    parse_groups_attr,
    parse_section_attrs,
)


def parse_attrs(attr_str: str) -> dict[str, str]:
    """Parse section-header attributes (public alias for tests / callers)."""
    return parse_section_attrs(attr_str)


def parse_tscn_text(
    tscn_content: str, project_path: str, max_depth: int = 3, current_depth: int = 0
) -> dict[str, Any]:
    """
    Parses a Godot 4 .tscn text file content into a structured node hierarchy graph.
    Supports ext_resources, sub_resources, signal connections, and recursive sub-scene expansion.
    """
    ext_resources: dict[str, dict[str, str]] = {}
    sub_resources: dict[str, dict[str, str]] = {}
    nodes: list[dict[str, Any]] = []
    connections: list[dict[str, str]] = []

    lines = tscn_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith(";"):
            i += 1
            continue

        sec_match = SECTION_RE.match(line)
        if sec_match:
            sec_type = sec_match.group(1)
            sec_attrs_str = sec_match.group(2)
            attrs = parse_section_attrs(sec_attrs_str)

            if sec_type == "ext_resource":
                res_id = attrs.get("id")
                if res_id:
                    ext_resources[res_id] = {
                        "type": attrs.get("type", "Resource"),
                        "path": attrs.get("path", ""),
                    }
            elif sec_type == "sub_resource":
                res_id = attrs.get("id")
                if res_id:
                    sub_resources[res_id] = {"type": attrs.get("type", "Resource")}
            elif sec_type == "node":
                node_data: dict[str, Any] = empty_node_shell(attrs)
                node_data["groups"] = parse_groups_attr(sec_attrs_str)

                # Read node property lines until next section or EOF
                i += 1
                while i < len(lines):
                    sub_line = lines[i].strip()
                    if not sub_line or sub_line.startswith(";"):
                        i += 1
                        continue
                    if SECTION_RE.match(sub_line):
                        i -= 1  # Backtrack for outer loop
                        break
                    if "=" in sub_line:
                        pk, pv = [p.strip() for p in sub_line.split("=", 1)]
                        pv_clean = pv.strip('"')
                        if pk == "script":
                            # Match ExtResource("id")
                            ext_ref = re.search(r'ExtResource\("?([^"\)]+)"?\)', pv)
                            if ext_ref:
                                ref_id = ext_ref.group(1)
                                if ref_id in ext_resources:
                                    node_data["script_path"] = ext_resources[ref_id]["path"]
                        else:
                            node_data["properties"][pk] = pv_clean
                    i += 1

                nodes.append(node_data)

            elif sec_type == "connection":
                connections.append(
                    {
                        "signal": attrs.get("signal", ""),
                        "from": attrs.get("from", ""),
                        "to": attrs.get("to", ""),
                        "method": attrs.get("method", ""),
                    }
                )

        i += 1

    # Map connections to node objects
    node_by_path: dict[str, dict[str, Any]] = {}

    # Identify Root node (first node without parent or parent=".")
    root_node: dict[str, Any] | None = None

    for node in nodes:
        parent = node["parent"]
        if parent is None:
            node_path = "."
            root_node = node
        elif parent == ".":
            node_path = node["name"]
        else:
            node_path = f"{parent}/{node['name']}"

        node["node_path"] = node_path
        node_by_path[node_path] = node

    # Attach signals
    for conn in connections:
        from_path = conn["from"]
        if from_path in node_by_path:
            node_by_path[from_path]["connections"].append(conn)
        elif root_node and from_path == ".":
            root_node["connections"].append(conn)

    # Build multi-branch tree
    tree_root: dict[str, Any] | None = None

    for node in nodes:
        parent = node["parent"]
        if parent is None:
            tree_root = node
        elif parent == ".":
            if tree_root:
                tree_root["children"].append(node)
        else:
            if parent in node_by_path:
                node_by_path[parent]["children"].append(node)
            elif tree_root:
                tree_root["children"].append(node)

    # Handle sub-scene recursive expansion if instance_id present
    if current_depth < max_depth:
        for node in nodes:
            inst_id = node.get("instance_id")
            if inst_id:
                # Match ExtResource("id")
                ext_ref = re.search(r'ExtResource\("?([^"\)]+)"?\)', inst_id)
                if ext_ref:
                    ref_id = ext_ref.group(1)
                    if ref_id in ext_resources and ext_resources[ref_id]["path"].endswith(".tscn"):
                        sub_scene_rel = ext_resources[ref_id]["path"].replace("res://", "")
                        sub_scene_abs = os.path.join(project_path, sub_scene_rel)
                        if os.path.exists(sub_scene_abs):
                            try:
                                with open(
                                    sub_scene_abs,
                                    encoding="utf-8",
                                    errors="ignore",
                                ) as sf:
                                    sub_parsed = parse_tscn_text(
                                        sf.read(),
                                        project_path,
                                        max_depth,
                                        current_depth + 1,
                                    )
                                    if sub_parsed.get("root_node"):
                                        sub_root = sub_parsed["root_node"]
                                        node["instance_source"] = ext_resources[ref_id]["path"]
                                        # Merge sub-scene children into current node
                                        for child in sub_root.get("children", []):
                                            child["is_instantiated_child"] = True
                                            node["children"].append(child)
                            except Exception:
                                pass

    return ok(
        root_node=tree_root,
        ext_resources=ext_resources,
        sub_resources=sub_resources,
        total_nodes=len(nodes),
        connections_count=len(connections),
    )


def inspect_scene_engine(project_path: str, scene_path: str) -> dict[str, Any]:
    """Runs a headless Godot process to inspect instantiated scene node hierarchy and runtime info."""
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    b64_scene = base64.b64encode(scene_path.encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_inspect")

func run_inspect() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    if not ResourceLoader.exists(scn_path):
        print("SCENE_ERR:Scene resource does not exist: " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("SCENE_ERR:Resource is not PackedScene: " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    if inst == null:
        print("SCENE_ERR:Failed to instantiate scene: " + scn_path)
        quit(1)
        return

    var tree_dict = serialize_node(inst)
    print("SCENE_TREE_JSON:" + JSON.stringify(tree_dict))
    quit()

func serialize_node(node: Node) -> Dictionary:
    var data = {{
        "name": node.name,
        "type": node.get_class(),
        "script_path": "",
        "groups": [],
        "children": []
    }}
    
    var scr = node.get_script()
    if scr != null and scr is Script:
        data["script_path"] = scr.resource_path

    var grps = node.get_groups()
    for g in grps:
        var g_str = str(g)
        if not g_str.begins_with("_"):
            data["groups"].append(g_str)

    for i in range(node.get_child_count()):
        data["children"].append(serialize_node(node.get_child(i)))

    return data
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
            if line.startswith("SCENE_TREE_JSON:"):
                import json

                raw_json = line[len("SCENE_TREE_JSON:") :].strip()
                parsed_root = json.loads(raw_json)
                return ok(
                    mode="engine",
                    scene_path=scene_path,
                    root_node=parsed_root,
                )
        return err(res.stdout or res.stderr or "Failed to inspect scene via engine")
    except Exception as e:
        return err(str(e))
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def inspect_scene(
    project_path: str, scene_path: str, use_engine: bool = False, max_depth: int = 3
) -> dict[str, Any]:
    """
    Main entry point to inspect Godot .tscn files.
    Defaults to fast zero-dependency static parsing, with optional engine runtime fallback.
    """
    abs_project = os.path.abspath(project_path)

    # Resolve scene path
    if scene_path.startswith("res://"):
        rel_scene = scene_path.replace("res://", "")
        abs_scene = os.path.join(abs_project, rel_scene)
    else:
        abs_scene = os.path.abspath(scene_path)
        if not abs_scene.startswith(abs_project):
            abs_scene = os.path.join(abs_project, scene_path)

    if not os.path.exists(abs_scene):
        return err(f"Scene file not found at {abs_scene}")

    if use_engine:
        res_scene_path = (
            scene_path
            if scene_path.startswith("res://")
            else f"res://{os.path.relpath(abs_scene, abs_project)}"
        )
        return inspect_scene_engine(abs_project, res_scene_path)

    try:
        with open(abs_scene, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        parsed = parse_tscn_text(content, abs_project, max_depth=max_depth)
        parsed["mode"] = "static"
        parsed["scene_path"] = scene_path
        return parsed
    except Exception as e:
        return err(str(e))
