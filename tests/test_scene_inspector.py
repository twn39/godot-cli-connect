"""
Unit and integration tests for scene_inspector module
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.scene_inspector import inspect_scene, parse_tscn_text

runner = CliRunner()

SAMPLE_TSCN = """[gd_scene load_steps=3 format=3 uid="uid://sample123"]

[ext_resource type="Script" path="res://player.gd" id="1_player"]
[ext_resource type="PackedScene" path="res://weapon.tscn" id="2_weapon"]

[node name="Main" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="." groups=["players", "allies"]]
script = ExtResource("1_player")

[node name="Sprite2D" type="Sprite2D" parent="Player"]

[node name="Weapon" parent="Player" instance=ExtResource("2_weapon")]

[connection signal="body_entered" from="Player" to="." method="_on_player_body_entered"]
"""

SAMPLE_WEAPON_TSCN = """[gd_scene load_steps=1 format=3]

[node name="Weapon" type="Node2D"]

[node name="BulletPoint" type="Marker2D" parent="."]
"""


def test_parse_tscn_text(tmp_path):
    # Write weapon sub-scene
    weapon_path = tmp_path / "weapon.tscn"
    weapon_path.write_text(SAMPLE_WEAPON_TSCN)

    res = parse_tscn_text(SAMPLE_TSCN, str(tmp_path))
    assert res["status"] == "success"
    root = res["root_node"]
    assert root["name"] == "Main"
    assert root["type"] == "Node2D"
    assert len(root["children"]) == 1

    player = root["children"][0]
    assert player["name"] == "Player"
    assert player["type"] == "CharacterBody2D"
    assert player["script_path"] == "res://player.gd"
    assert "players" in player["groups"]
    assert len(player["connections"]) == 1
    assert player["connections"][0]["signal"] == "body_entered"
    assert player["connections"][0]["method"] == "_on_player_body_entered"

    # Check children of Player (Sprite2D + Weapon containing BulletPoint)
    child_names = [c["name"] for c in player["children"]]
    assert "Sprite2D" in child_names
    assert "Weapon" in child_names

    weapon_node = [c for c in player["children"] if c["name"] == "Weapon"][0]
    sub_child_names = [c["name"] for c in weapon_node["children"]]
    assert "BulletPoint" in sub_child_names


def test_inspect_scene_file_not_found(tmp_path):
    res = inspect_scene(str(tmp_path), "non_existent.tscn")
    assert res["status"] == "error"
    assert "Scene file not found" in res["message"]


def test_cli_inspect_scene_cmd(tmp_path):
    scene_file = tmp_path / "main.tscn"
    scene_file.write_text(SAMPLE_TSCN)

    res = runner.invoke(
        app, ["inspect-scene", str(scene_file), "-p", str(tmp_path), "--json"]
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"name": "Main"' in res.stdout
    assert '"script_path": "res://player.gd"' in res.stdout
