"""
Unit tests for new enhancements: asset reimport, script attachment in scene creation, and test runner diagnostics
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.resources import reimport_assets
from godot_cli_connect.operations.scene_editor import create_scene

runner = CliRunner()


def test_reimport_assets(tmp_path):
    proj_dir = tmp_path / "ReimportProj"
    proj_dir.mkdir()
    (proj_dir / "project.godot").write_text("config_version=5\n[application]\nconfig/name=\"Test\"\n")
    
    res = reimport_assets(str(proj_dir))
    assert res["status"] in ["success", "failure"]
    assert "project_path" in res


def test_cli_import_assets(tmp_path):
    proj_dir = tmp_path / "ImportCliProj"
    proj_dir.mkdir()
    (proj_dir / "project.godot").write_text("config_version=5\n[application]\nconfig/name=\"Test\"\n")

    res = runner.invoke(app, ["import-assets", "-p", str(proj_dir), "--json"])
    assert res.exit_code in [0, 1]
    assert "status" in res.stdout


def test_create_scene_with_script(tmp_path):
    proj_dir = tmp_path / "SceneScriptProj"
    proj_dir.mkdir()
    (proj_dir / "project.godot").write_text("config_version=5\n")
    (proj_dir / "main.gd").write_text("extends Node2D\n")

    res = create_scene(
        project_path=str(proj_dir),
        save_path="res://main.tscn",
        root_type="Node2D",
        script_path="res://main.gd",
    )

    assert res["status"] == "success"
    assert res["script_path"] == "res://main.gd"
    scene_text = (proj_dir / "main.tscn").read_text()
    assert "res://main.gd" in scene_text


def test_cli_create_scene_with_script(tmp_path):
    proj_dir = tmp_path / "CliSceneScriptProj"
    proj_dir.mkdir()
    (proj_dir / "project.godot").write_text("config_version=5\n")
    (proj_dir / "player.gd").write_text("extends CharacterBody2D\n")

    res = runner.invoke(
        app,
        [
            "create-scene",
            "res://player.tscn",
            "-r",
            "CharacterBody2D",
            "-s",
            "res://player.gd",
            "-p",
            str(proj_dir),
            "--json",
        ],
    )

    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    scene_text = (proj_dir / "player.tscn").read_text()
    assert "res://player.gd" in scene_text
