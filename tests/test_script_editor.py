"""Tests for GDScript create/write/read/attach."""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.scene_editor import create_scene
from godot_cli_connect.operations.script_editor import (
    attach_script_to_node,
    create_script,
    read_script,
    write_script,
)

runner = CliRunner()


def test_create_write_read_script(tmp_path):
    res = create_script(
        str(tmp_path),
        "res://scripts/player.gd",
        extends="CharacterBody2D",
        class_name="Player",
    )
    assert res["status"] == "success"
    assert (tmp_path / "scripts" / "player.gd").exists()
    text = (tmp_path / "scripts" / "player.gd").read_text()
    assert "extends CharacterBody2D" in text
    assert "class_name Player" in text

    w = write_script(
        str(tmp_path),
        "res://scripts/player.gd",
        "extends Node\nfunc _ready():\n\tpass\n",
    )
    assert w["status"] == "success"
    r = read_script(str(tmp_path), "res://scripts/player.gd")
    assert r["status"] == "success"
    assert "extends Node" in r["content"]


def test_attach_script_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "godot_cli_connect.operations.scene_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    scene = tmp_path / "main.tscn"
    create_scene(str(tmp_path), str(scene), root_type="Node2D", root_name="Root")
    create_script(str(tmp_path), "res://main.gd", extends="Node2D")
    res = attach_script_to_node(
        str(tmp_path), str(scene), ".", "res://main.gd"
    )
    assert res["status"] == "success"
    assert res["mode"] == "offline"
    assert "ExtResource" in scene.read_text()
    assert "script =" in scene.read_text()


def test_cli_script_create(tmp_path):
    result = runner.invoke(
        app,
        [
            "script-create",
            "res://a.gd",
            "-e",
            "Node2D",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout
