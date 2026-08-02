"""
Godot .tscn scene creation, node modification, property editing, and node deletion module
"""

import base64
import os
import tempfile
from typing import Any, Dict, Optional

from ..finder import find_godot_executable
from .runner import build_godot_cmd, run_godot_cmd


def create_scene_offline(abs_scene: str, root_type: str, root_name: str) -> bool:
    """Fallback offline text-based .tscn creator."""
    try:
        dir_path = os.path.dirname(abs_scene)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        content = f"""[gd_scene format=3]

[node name="{root_name}" type="{root_type}"]
"""
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def create_scene(
    project_path: str,
    save_path: str,
    root_type: str = "Node2D",
    root_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new Godot .tscn scene file with a specified root node type."""
    abs_project = os.path.abspath(project_path)
    if save_path.startswith("res://"):
        rel_path = save_path[6:]
        abs_save_path = os.path.join(abs_project, rel_path)
        res_save_path = save_path
    elif os.path.isabs(save_path):
        abs_save_path = os.path.abspath(save_path)
        try:
            res_save_path = f"res://{os.path.relpath(abs_save_path, abs_project)}"
        except ValueError:
            res_save_path = f"res://{os.path.basename(abs_save_path)}"
    else:
        abs_save_path = os.path.abspath(os.path.join(abs_project, save_path))
        res_save_path = f"res://{os.path.relpath(abs_save_path, abs_project)}"

    actual_root_name = root_name if root_name else root_type

    try:
        godot_bin = find_godot_executable()
        b64_type = base64.b64encode(root_type.encode("utf-8")).decode("ascii")
        b64_name = base64.b64encode(actual_root_name.encode("utf-8")).decode("ascii")
        b64_path = base64.b64encode(res_save_path.encode("utf-8")).decode("ascii")

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_create_scene")

func run_create_scene() -> void:
    var r_type = Marshalls.base64_to_utf8("{b64_type}")
    var r_name = Marshalls.base64_to_utf8("{b64_name}")
    var s_path = Marshalls.base64_to_utf8("{b64_path}")

    if not ClassDB.class_exists(r_type):
        print("SCENE_CREATE_ERR:Class " + r_type + " does not exist")
        quit(1)
        return

    var root_obj = ClassDB.instantiate(r_type)
    if root_obj == null or not (root_obj is Node):
        print("SCENE_CREATE_ERR:Failed to instantiate root node " + r_type)
        quit(1)
        return

    root_obj.name = r_name

    var dir_dir = s_path.get_base_dir()
    if dir_dir != "" and dir_dir != "res://":
        DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_dir))

    var packed = PackedScene.new()
    var pack_err = packed.pack(root_obj)
    if pack_err != OK:
        print("SCENE_CREATE_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, s_path)
    print("SCENE_CREATED:ERR=" + str(save_err))
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
            if "SCENE_CREATED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "save_path": res_save_path,
                    "root_name": actual_root_name,
                    "root_type": root_type,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Offline fallback
    if create_scene_offline(abs_save_path, root_type, actual_root_name):
        return {
            "status": "success",
            "mode": "offline",
            "save_path": res_save_path,
            "root_name": actual_root_name,
            "root_type": root_type,
        }

    return {"status": "error", "message": f"Failed to create scene at {res_save_path}"}


def add_node_to_scene_offline(
    abs_scene: str,
    node_name: str,
    node_type: str,
    parent_path: str,
    script_path: Optional[str],
) -> bool:
    """Fallback offline text-based .tscn node adder."""
    if not os.path.exists(abs_scene):
        return False

    try:
        with open(abs_scene, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        ext_insert_idx = -1
        script_id = None

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[ext_resource"):
                ext_insert_idx = idx

        if script_path:
            script_id = "1_script"
            ext_line = (
                f'[ext_resource type="Script" path="{script_path}" id="{script_id}"]\n'
            )
            if ext_insert_idx != -1:
                lines.insert(ext_insert_idx + 1, ext_line)
            else:
                lines.insert(1, ext_line)

        node_line = (
            f'[node name="{node_name}" type="{node_type}" parent="{parent_path}"]\n'
        )
        if script_id:
            node_line += f'script = ExtResource("{script_id}")\n'

        lines.append(f"\n{node_line}")
        with open(abs_scene, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False


def add_node_to_scene(
    project_path: str,
    scene_path: str,
    node_name: str,
    node_type: str = "Node2D",
    parent_path: str = ".",
    script_path: Optional[str] = None,
    properties_json: str = "{}",
) -> Dict[str, Any]:
    """Adds a child node to an existing Godot .tscn scene file with owner hierarchy and script bindings."""
    abs_project = os.path.abspath(project_path)
    if scene_path.startswith("res://"):
        rel_path = scene_path[6:]
        abs_scene_path = os.path.join(abs_project, rel_path)
        res_scene_path = scene_path
    elif os.path.isabs(scene_path):
        abs_scene_path = os.path.abspath(scene_path)
        try:
            res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"
        except ValueError:
            res_scene_path = f"res://{os.path.basename(abs_scene_path)}"
    else:
        abs_scene_path = os.path.abspath(os.path.join(abs_project, scene_path))
        res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"

    if not os.path.exists(abs_scene_path):
        return {
            "status": "error",
            "message": f"Scene file not found at {abs_scene_path}",
        }

    try:
        godot_bin = find_godot_executable()
        b64_scene = base64.b64encode(res_scene_path.encode("utf-8")).decode("ascii")
        b64_name = base64.b64encode(node_name.encode("utf-8")).decode("ascii")
        b64_type = base64.b64encode(node_type.encode("utf-8")).decode("ascii")
        b64_parent = base64.b64encode(parent_path.encode("utf-8")).decode("ascii")
        b64_script = base64.b64encode((script_path or "").encode("utf-8")).decode(
            "ascii"
        )
        b64_props = base64.b64encode(properties_json.encode("utf-8")).decode("ascii")

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_add_node")

func set_owner_recursive(node: Node, owner_node: Node) -> void:
    for child in node.get_children():
        if child != owner_node:
            child.owner = owner_node
        set_owner_recursive(child, owner_node)

func run_add_node() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_name = Marshalls.base64_to_utf8("{b64_name}")
    var n_type = Marshalls.base64_to_utf8("{b64_type}")
    var p_path = Marshalls.base64_to_utf8("{b64_parent}")
    var s_path = Marshalls.base64_to_utf8("{b64_script}")
    var raw_props = Marshalls.base64_to_utf8("{b64_props}")

    if not ResourceLoader.exists(scn_path):
        print("NODE_ADD_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("NODE_ADD_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    if inst == null:
        print("NODE_ADD_ERR:Failed to instantiate scene " + scn_path)
        quit(1)
        return

    var parent_node = inst
    if p_path != "." and p_path != "":
        parent_node = inst.get_node_or_null(p_path)
        if parent_node == null:
            print("NODE_ADD_ERR:Parent node not found " + p_path)
            quit(1)
            return

    if not ClassDB.class_exists(n_type):
        print("NODE_ADD_ERR:Class " + n_type + " does not exist")
        quit(1)
        return

    var new_child = ClassDB.instantiate(n_type)
    if new_child == null or not (new_child is Node):
        print("NODE_ADD_ERR:Failed to instantiate node type " + n_type)
        quit(1)
        return

    new_child.name = n_name

    if s_path != "" and ResourceLoader.exists(s_path):
        var scr = load(s_path)
        if scr is Script:
            new_child.set_script(scr)

    var parsed_props = JSON.parse_string(raw_props)
    if parsed_props != null and parsed_props is Dictionary:
        for k in parsed_props.keys():
            var v_val = parsed_props[k]
            if v_val is String:
                var parsed_v = str_to_var(v_val)
                if parsed_v != null:
                    v_val = parsed_v
            new_child.set(k, v_val)

    parent_node.add_child(new_child)
    set_owner_recursive(inst, inst)

    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("NODE_ADD_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("NODE_ADDED:ERR=" + str(save_err))
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
            if "NODE_ADDED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "scene_path": res_scene_path,
                    "node_name": node_name,
                    "node_type": node_type,
                    "parent_path": parent_path,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    # Offline fallback
    if add_node_to_scene_offline(
        abs_scene_path, node_name, node_type, parent_path, script_path
    ):
        return {
            "status": "success",
            "mode": "offline",
            "scene_path": res_scene_path,
            "node_name": node_name,
            "node_type": node_type,
            "parent_path": parent_path,
        }

    return {
        "status": "error",
        "message": f"Failed to add node {node_name} to scene {res_scene_path}",
    }


def edit_node_in_scene(
    project_path: str,
    scene_path: str,
    node_path: str,
    properties_json: str = "{}",
) -> Dict[str, Any]:
    """Edits properties of an existing node in a .tscn scene file."""
    abs_project = os.path.abspath(project_path)
    if scene_path.startswith("res://"):
        rel_path = scene_path[6:]
        abs_scene_path = os.path.join(abs_project, rel_path)
        res_scene_path = scene_path
    elif os.path.isabs(scene_path):
        abs_scene_path = os.path.abspath(scene_path)
        try:
            res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"
        except ValueError:
            res_scene_path = f"res://{os.path.basename(abs_scene_path)}"
    else:
        abs_scene_path = os.path.abspath(os.path.join(abs_project, scene_path))
        res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"

    if not os.path.exists(abs_scene_path):
        return {
            "status": "error",
            "message": f"Scene file not found at {abs_scene_path}",
        }

    try:
        godot_bin = find_godot_executable()
        b64_scene = base64.b64encode(res_scene_path.encode("utf-8")).decode("ascii")
        b64_node = base64.b64encode(node_path.encode("utf-8")).decode("ascii")
        b64_props = base64.b64encode(properties_json.encode("utf-8")).decode("ascii")

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_edit_node")

func set_owner_recursive(node: Node, owner_node: Node) -> void:
    for child in node.get_children():
        if child != owner_node:
            child.owner = owner_node
        set_owner_recursive(child, owner_node)

func run_edit_node() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_path = Marshalls.base64_to_utf8("{b64_node}")
    var raw_props = Marshalls.base64_to_utf8("{b64_props}")

    if not ResourceLoader.exists(scn_path):
        print("NODE_EDIT_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("NODE_EDIT_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    var target_node = inst
    if n_path != "." and n_path != "":
        target_node = inst.get_node_or_null(n_path)
        if target_node == null:
            print("NODE_EDIT_ERR:Target node not found " + n_path)
            quit(1)
            return

    var parsed_props = JSON.parse_string(raw_props)
    if parsed_props != null and parsed_props is Dictionary:
        for k in parsed_props.keys():
            var v_val = parsed_props[k]
            if v_val is String:
                var parsed_v = str_to_var(v_val)
                if parsed_v != null:
                    v_val = parsed_v
            target_node.set(k, v_val)

    set_owner_recursive(inst, inst)
    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("NODE_EDIT_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("NODE_EDITED:ERR=" + str(save_err))
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
            if "NODE_EDITED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "scene_path": res_scene_path,
                    "node_path": node_path,
                    "properties": properties_json,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    return {
        "status": "error",
        "message": f"Failed to edit node {node_path} in scene {res_scene_path}",
    }


def remove_node_from_scene(
    project_path: str,
    scene_path: str,
    node_path: str,
) -> Dict[str, Any]:
    """Removes a target child node synchronously from a .tscn scene file."""
    abs_project = os.path.abspath(project_path)
    if scene_path.startswith("res://"):
        rel_path = scene_path[6:]
        abs_scene_path = os.path.join(abs_project, rel_path)
        res_scene_path = scene_path
    elif os.path.isabs(scene_path):
        abs_scene_path = os.path.abspath(scene_path)
        try:
            res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"
        except ValueError:
            res_scene_path = f"res://{os.path.basename(abs_scene_path)}"
    else:
        abs_scene_path = os.path.abspath(os.path.join(abs_project, scene_path))
        res_scene_path = f"res://{os.path.relpath(abs_scene_path, abs_project)}"

    if not os.path.exists(abs_scene_path):
        return {
            "status": "error",
            "message": f"Scene file not found at {abs_scene_path}",
        }

    try:
        godot_bin = find_godot_executable()
        b64_scene = base64.b64encode(res_scene_path.encode("utf-8")).decode("ascii")
        b64_node = base64.b64encode(node_path.encode("utf-8")).decode("ascii")

        helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_remove_node")

func set_owner_recursive(node: Node, owner_node: Node) -> void:
    for child in node.get_children():
        if child != owner_node:
            child.owner = owner_node
        set_owner_recursive(child, owner_node)

func run_remove_node() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_path = Marshalls.base64_to_utf8("{b64_node}")

    if not ResourceLoader.exists(scn_path):
        print("NODE_RM_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("NODE_RM_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    if n_path == "." or n_path == "":
        print("NODE_RM_ERR:Cannot remove root node")
        quit(1)
        return

    var target_node = inst.get_node_or_null(n_path)
    if target_node == null:
        print("NODE_RM_ERR:Target node not found " + n_path)
        quit(1)
        return

    var parent_node = target_node.get_parent()
    if parent_node != null:
        parent_node.remove_child(target_node)
        target_node.free()

    set_owner_recursive(inst, inst)
    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("NODE_RM_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("NODE_REMOVED:ERR=" + str(save_err))
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
            if "NODE_REMOVED:ERR=0" in res.stdout:
                return {
                    "status": "success",
                    "mode": "engine",
                    "scene_path": res_scene_path,
                    "removed_node": node_path,
                }
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
    except Exception:
        pass

    return {
        "status": "error",
        "message": f"Failed to remove node {node_path} from scene {res_scene_path}",
    }
