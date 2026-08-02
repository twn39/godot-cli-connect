"""Offline edit/remove/properties for scene_tscn + scene_editor."""

from godot_cli_connect.operations.scene_editor import (
    add_node_to_scene,
    create_scene,
    edit_node_in_scene,
    remove_node_from_scene,
)
from godot_cli_connect.operations.scene_tscn import (
    edit_node_in_scene_offline,
    remove_node_from_scene_offline,
)


def test_add_node_with_properties_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("GODOT_PATH", raising=False)
    monkeypatch.setattr(
        "godot_cli_connect.operations.scene_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    scene = tmp_path / "main.tscn"
    create_scene(str(tmp_path), str(scene), root_type="Node2D", root_name="Root")
    res = add_node_to_scene(
        str(tmp_path),
        str(scene),
        node_name="Sprite",
        node_type="Sprite2D",
        parent_path=".",
        properties_json='{"visible": false, "z_index": 3}',
    )
    assert res["status"] == "success"
    assert res["mode"] == "offline"
    text = scene.read_text()
    assert "visible = false" in text
    assert "z_index = 3" in text


def test_edit_and_remove_offline_forced(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "godot_cli_connect.operations.scene_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    scene = tmp_path / "main.tscn"
    create_scene(str(tmp_path), str(scene), root_type="Node2D", root_name="Root")
    add_node_to_scene(
        str(tmp_path),
        str(scene),
        "Child",
        node_type="Node2D",
        parent_path=".",
    )
    edit = edit_node_in_scene(
        str(tmp_path), str(scene), "Child", properties_json='{"visible": false}'
    )
    assert edit["status"] == "success"
    assert edit["mode"] == "offline"
    assert "visible = false" in scene.read_text()

    rm = remove_node_from_scene(str(tmp_path), str(scene), "Child")
    assert rm["status"] == "success"
    assert rm["mode"] == "offline"
    assert 'name="Child"' not in scene.read_text()


def test_scene_tscn_helpers_direct(tmp_path):
    scene = tmp_path / "s.tscn"
    scene.write_text(
        '[gd_scene format=3]\n\n[node name="Root" type="Node2D"]\n\n'
        '[node name="A" type="Node2D" parent="."]\nposition = Vector2(1, 2)\n'
    )
    assert edit_node_in_scene_offline(
        str(scene), "A", '{"position": "Vector2(10, 20)", "visible": true}'
    )
    content = scene.read_text()
    assert "position = Vector2(10, 20)" in content
    assert "visible = true" in content
    assert remove_node_from_scene_offline(str(scene), "A")
    assert 'name="A"' not in scene.read_text()
