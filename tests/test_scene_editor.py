"""
Unit and integration tests for scene_editor module and create-scene / add-node CLI commands
"""

from typer.testing import CliRunner
from godot_cli_connect.operations.scene_editor import create_scene, add_node_to_scene
from godot_cli_connect.cli import app

runner = CliRunner()


def test_create_scene_offline(tmp_path):
    scene_file = tmp_path / "player.tscn"
    res = create_scene(
        str(tmp_path), str(scene_file), root_type="CharacterBody2D", root_name="Player"
    )

    assert res["status"] == "success"
    assert res["root_name"] == "Player"
    assert res["root_type"] == "CharacterBody2D"
    assert scene_file.exists()

    content = scene_file.read_text()
    assert 'name="Player"' in content
    assert 'type="CharacterBody2D"' in content


def test_add_node_to_scene_offline(tmp_path):
    scene_file = tmp_path / "player.tscn"
    create_scene(
        str(tmp_path), str(scene_file), root_type="CharacterBody2D", root_name="Player"
    )

    res = add_node_to_scene(
        str(tmp_path),
        str(scene_file),
        node_name="Sprite2D",
        node_type="Sprite2D",
        parent_path=".",
    )
    assert res["status"] == "success"
    assert res["node_name"] == "Sprite2D"

    content = scene_file.read_text()
    assert 'name="Sprite2D"' in content


def test_cli_create_scene(tmp_path):
    res = runner.invoke(
        app,
        [
            "create-scene",
            "res://enemy.tscn",
            "-r",
            "Node2D",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout


def test_cli_add_node(tmp_path):
    scene_file = tmp_path / "enemy.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Node2D")

    res = runner.invoke(
        app,
        [
            "add-node",
            str(scene_file),
            "-n",
            "Gun",
            "-t",
            "Node2D",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"node_name": "Gun"' in res.stdout
