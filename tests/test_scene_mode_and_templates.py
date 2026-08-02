"""Tests for scene EditMode policy and GDScript template builders."""

from __future__ import annotations

from godot_cli_connect.operations.scene_editor import create_scene
from godot_cli_connect.operations.scene_gdscript import (
    script_add_node,
    script_create_scene,
)


def test_force_offline_mode(tmp_path, monkeypatch):
    """mode=offline must not require a Godot binary."""
    monkeypatch.delenv("GODOT_PATH", raising=False)
    monkeypatch.setattr(
        "godot_cli_connect.operations.scene_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("godot should not be called")),
    )
    scene = tmp_path / "main.tscn"
    res = create_scene(
        str(tmp_path),
        str(scene),
        root_type="Node2D",
        root_name="Root",
        mode="offline",
    )
    assert res["status"] == "success"
    assert res["mode"] == "offline"
    assert scene.exists()


def test_force_engine_mode_fails_without_godot(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "godot_cli_connect.operations.scene_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    res = create_scene(
        str(tmp_path),
        str(tmp_path / "x.tscn"),
        root_type="Node2D",
        mode="engine",
    )
    assert res["status"] == "error"
    assert "Engine create_scene failed" in res["message"] or "no godot" in res.get("message", "")


def test_gdscript_templates_embed_b64_payloads():
    src = script_create_scene("Node2D", "Root", "res://main.tscn", None)
    assert "extends SceneTree" in src
    assert "SCENE_CREATED" in src
    assert "Marshalls.base64_to_utf8" in src

    add = script_add_node(
        "res://main.tscn",
        "Child",
        "Sprite2D",
        ".",
        None,
        '{"modulate":"Color(1,0,0,1)"}',
    )
    assert "NODE_ADDED" in add
    assert "set_owner_recursive" in add
