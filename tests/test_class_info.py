"""
Unit and integration tests for class_info module and class-info CLI command
"""

import json

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.class_info import get_class_info_json

runner = CliRunner()


def test_get_class_info_json(tmp_path):
    api_json = tmp_path / "extension_api.json"
    fake_api = {
        "classes": [
            {
                "name": "CharacterBody2D",
                "inherits": "PhysicsBody2D",
                "methods": [{"name": "move_and_slide", "arguments": []}],
                "properties": [{"name": "velocity", "type": "Vector2"}],
                "signals": [],
            }
        ]
    }
    api_json.write_text(json.dumps(fake_api))

    info = get_class_info_json("CharacterBody2D", str(api_json))
    assert info is not None
    assert info["name"] == "CharacterBody2D"
    assert info["inherits"] == "PhysicsBody2D"
    assert len(info["methods"]) == 1
    assert info["methods"][0]["name"] == "move_and_slide"


def test_cli_class_info_json(tmp_path):
    api_json = tmp_path / "extension_api.json"
    fake_api = {
        "classes": [
            {
                "name": "Sprite2D",
                "inherits": "Node2D",
                "methods": [],
                "properties": [],
                "signals": [],
            }
        ]
    }
    api_json.write_text(json.dumps(fake_api))

    res = runner.invoke(app, ["class-info", "Sprite2D", "-p", str(tmp_path), "--json"])
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"name": "Sprite2D"' in res.stdout
