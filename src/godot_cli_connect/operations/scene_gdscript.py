"""
Headless GDScript templates for scene mutations.

All user-controlled strings are injected via Base64 to avoid quoting issues.
``scene_editor`` owns policy (engine vs offline); this module only builds scripts.
"""

from __future__ import annotations

import base64


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


_OWNER_RECURSIVE = """
func set_owner_recursive(node: Node, owner_node: Node) -> void:
    for child in node.get_children():
        if child != owner_node:
            child.owner = owner_node
        set_owner_recursive(child, owner_node)
"""


def script_create_scene(
    root_type: str,
    root_name: str,
    save_path: str,
    script_path: str | None = None,
) -> str:
    """Build GDScript that creates a PackedScene with optional root script."""
    b64_type = _b64(root_type)
    b64_name = _b64(root_name)
    b64_path = _b64(save_path)
    b64_script = _b64(script_path or "")
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_create_scene")

func run_create_scene() -> void:
    var r_type = Marshalls.base64_to_utf8("{b64_type}")
    var r_name = Marshalls.base64_to_utf8("{b64_name}")
    var s_path = Marshalls.base64_to_utf8("{b64_path}")
    var sc_path = Marshalls.base64_to_utf8("{b64_script}")

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

    if sc_path != "" and ResourceLoader.exists(sc_path):
        var sc_res = load(sc_path)
        if sc_res != null and sc_res is Script:
            root_obj.set_script(sc_res)

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


def script_add_node(
    scene_path: str,
    node_name: str,
    node_type: str,
    parent_path: str,
    script_path: str | None = None,
    properties_json: str = "{}",
) -> str:
    """Build GDScript that adds a child node to a PackedScene."""
    b64_scene = _b64(scene_path)
    b64_name = _b64(node_name)
    b64_type = _b64(node_type)
    b64_parent = _b64(parent_path)
    b64_script = _b64(script_path or "")
    b64_props = _b64(properties_json)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_add_node")
{_OWNER_RECURSIVE}
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


def script_edit_node(scene_path: str, node_path: str, properties_json: str = "{}") -> str:
    """Build GDScript that sets properties on a node in a PackedScene."""
    b64_scene = _b64(scene_path)
    b64_node = _b64(node_path)
    b64_props = _b64(properties_json)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_edit_node")
{_OWNER_RECURSIVE}
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


def script_remove_node(scene_path: str, node_path: str) -> str:
    """Build GDScript that removes a non-root node from a PackedScene."""
    b64_scene = _b64(scene_path)
    b64_node = _b64(node_path)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_remove_node")
{_OWNER_RECURSIVE}
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


def script_connect_signal(
    scene_path: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
    total_flags: int,
    binds_json: str = "[]",
) -> str:
    """Build GDScript that connects a persistent signal between nodes."""
    b64_scene = _b64(scene_path)
    b64_from = _b64(from_node)
    b64_signal = _b64(signal_name)
    b64_to = _b64(to_node)
    b64_method = _b64(method_name)
    b64_binds = _b64(binds_json)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_connect_signal")
{_OWNER_RECURSIVE}
func run_connect_signal() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var f_node = Marshalls.base64_to_utf8("{b64_from}")
    var sig_name = Marshalls.base64_to_utf8("{b64_signal}")
    var t_node = Marshalls.base64_to_utf8("{b64_to}")
    var m_name = Marshalls.base64_to_utf8("{b64_method}")
    var raw_binds = Marshalls.base64_to_utf8("{b64_binds}")

    if not ResourceLoader.exists(scn_path):
        print("SIG_CONN_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("SIG_CONN_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    var src_node = inst if (f_node == "." or f_node == "") else inst.get_node_or_null(f_node)
    var tgt_node = inst if (t_node == "." or t_node == "") else inst.get_node_or_null(t_node)

    if src_node == null:
        print("SIG_CONN_ERR:Source node not found " + f_node)
        quit(1)
        return

    if tgt_node == null:
        print("SIG_CONN_ERR:Target node not found " + t_node)
        quit(1)
        return

    var callable_obj = Callable(tgt_node, m_name)
    var parsed_binds = JSON.parse_string(raw_binds)
    if parsed_binds != null and parsed_binds is Array and parsed_binds.size() > 0:
        callable_obj = callable_obj.bindv(parsed_binds)

    var connect_flags = 2 | {total_flags} # 2 == CONNECT_PERSIST
    var err = src_node.connect(sig_name, callable_obj, connect_flags)
    if err != OK and err != ERR_INVALID_PARAMETER:
        print("SIG_CONN_ERR:Connect failed with code " + str(err))
        quit(1)
        return

    set_owner_recursive(inst, inst)
    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("SIG_CONN_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("SIG_CONNECTED:ERR=" + str(save_err))
    quit()
"""


def script_disconnect_signal(
    scene_path: str,
    from_node: str,
    signal_name: str,
    to_node: str,
    method_name: str,
) -> str:
    """Build GDScript that disconnects a signal between nodes."""
    b64_scene = _b64(scene_path)
    b64_from = _b64(from_node)
    b64_signal = _b64(signal_name)
    b64_to = _b64(to_node)
    b64_method = _b64(method_name)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_disconnect_signal")
{_OWNER_RECURSIVE}
func run_disconnect_signal() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var f_node = Marshalls.base64_to_utf8("{b64_from}")
    var sig_name = Marshalls.base64_to_utf8("{b64_signal}")
    var t_node = Marshalls.base64_to_utf8("{b64_to}")
    var m_name = Marshalls.base64_to_utf8("{b64_method}")

    if not ResourceLoader.exists(scn_path):
        print("SIG_DISC_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("SIG_DISC_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    var src_node = inst if (f_node == "." or f_node == "") else inst.get_node_or_null(f_node)
    var tgt_node = inst if (t_node == "." or t_node == "") else inst.get_node_or_null(t_node)

    if src_node != null and tgt_node != null:
        var callable_obj = Callable(tgt_node, m_name)
        if src_node.is_connected(sig_name, callable_obj):
            src_node.disconnect(sig_name, callable_obj)

    set_owner_recursive(inst, inst)
    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("SIG_DISC_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("SIG_DISCONNECTED:ERR=" + str(save_err))
    quit()
"""


def script_rename_node(scene_path: str, node_path: str, new_name: str) -> str:
    """Build GDScript that renames a node in a PackedScene."""
    b64_scene = _b64(scene_path)
    b64_node = _b64(node_path)
    b64_new = _b64(new_name)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_rename_node")
{_OWNER_RECURSIVE}
func run_rename_node() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_path = Marshalls.base64_to_utf8("{b64_node}")
    var n_new = Marshalls.base64_to_utf8("{b64_new}")

    if not ResourceLoader.exists(scn_path):
        print("NODE_RENAME_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("NODE_RENAME_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    var target_node = inst if (n_path == "." or n_path == "") else inst.get_node_or_null(n_path)

    if target_node == null:
        print("NODE_RENAME_ERR:Target node not found " + n_path)
        quit(1)
        return

    target_node.name = n_new
    set_owner_recursive(inst, inst)

    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("NODE_RENAME_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("NODE_RENAMED:ERR=" + str(save_err))
    quit()
"""


def script_reparent_node(scene_path: str, node_path: str, new_parent_path: str) -> str:
    """Build GDScript that reparents a node in a PackedScene."""
    b64_scene = _b64(scene_path)
    b64_node = _b64(node_path)
    b64_parent = _b64(new_parent_path)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_reparent_node")
{_OWNER_RECURSIVE}
func run_reparent_node() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_path = Marshalls.base64_to_utf8("{b64_node}")
    var p_path = Marshalls.base64_to_utf8("{b64_parent}")

    if not ResourceLoader.exists(scn_path):
        print("NODE_REPARENT_ERR:Scene does not exist " + scn_path)
        quit(1)
        return

    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("NODE_REPARENT_ERR:Resource is not PackedScene " + scn_path)
        quit(1)
        return

    var inst = scn_res.instantiate()
    var target_node = inst.get_node_or_null(n_path)
    var parent_node = inst if (p_path == "." or p_path == "") else inst.get_node_or_null(p_path)

    if target_node == null:
        print("NODE_REPARENT_ERR:Target node not found " + n_path)
        quit(1)
        return

    if parent_node == null:
        print("NODE_REPARENT_ERR:New parent node not found " + p_path)
        quit(1)
        return

    target_node.reparent(parent_node)
    set_owner_recursive(inst, inst)

    var packed = PackedScene.new()
    var pack_err = packed.pack(inst)
    if pack_err != OK:
        print("NODE_REPARENT_ERR:Pack error " + str(pack_err))
        quit(1)
        return

    var save_err = ResourceSaver.save(packed, scn_path)
    print("NODE_REPARENTED:ERR=" + str(save_err))
    quit()
"""


def script_attach_script(scene_path: str, node_path: str, script_path: str) -> str:
    """Build GDScript that attaches a Script resource to a node."""
    b64_scene = _b64(scene_path)
    b64_node = _b64(node_path)
    b64_script = _b64(script_path)
    return f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_attach")
{_OWNER_RECURSIVE}
func run_attach() -> void:
    var scn_path = Marshalls.base64_to_utf8("{b64_scene}")
    var n_path = Marshalls.base64_to_utf8("{b64_node}")
    var s_path = Marshalls.base64_to_utf8("{b64_script}")

    if not ResourceLoader.exists(scn_path):
        print("ATTACH_ERR:Scene missing")
        quit(1)
        return
    var scn_res = load(scn_path)
    if not (scn_res is PackedScene):
        print("ATTACH_ERR:Not PackedScene")
        quit(1)
        return
    var inst = scn_res.instantiate()
    var target = inst if (n_path == "." or n_path == "") else inst.get_node_or_null(n_path)
    if target == null:
        print("ATTACH_ERR:Node not found")
        quit(1)
        return
    if not ResourceLoader.exists(s_path):
        print("ATTACH_ERR:Script missing")
        quit(1)
        return
    var scr = load(s_path)
    if scr == null or not (scr is Script):
        print("ATTACH_ERR:Bad script")
        quit(1)
        return
    target.set_script(scr)
    set_owner_recursive(inst, inst)
    var packed = PackedScene.new()
    if packed.pack(inst) != OK:
        print("ATTACH_ERR:Pack")
        quit(1)
        return
    var err = ResourceSaver.save(packed, scn_path)
    print("ATTACH_OK:ERR=" + str(err))
    quit()
"""
