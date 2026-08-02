"""
Unit and integration tests for config_editor module and config-set / input-add CLI commands
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.config_editor import (
    add_input_action,
    parse_config_value,
    set_config_setting,
)

runner = CliRunner()


def test_parse_config_value():
    assert parse_config_value("1280") == 1280
    assert parse_config_value("3.14") == 3.14
    assert parse_config_value("true") is True
    assert parse_config_value("false") is False
    assert parse_config_value("My Game") == "My Game"


def test_set_config_setting_offline(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""config_version=5

[application]
config/name="Old Name"
""")

    res = set_config_setting(str(tmp_path), "application/config/name", "New Game Name")
    assert res["status"] == "success"

    updated_text = godot_file.read_text()
    assert 'config/name="New Game Name"' in updated_text


def test_add_input_action(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""config_version=5\n""")

    res = add_input_action(str(tmp_path), "move_left", key_name="KEY_A")
    assert res["status"] == "success"
    assert res["action_name"] == "move_left"


def test_cli_config_set(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""config_version=5\n""")

    res = runner.invoke(
        app,
        [
            "config-set",
            "application/config/name",
            "Awesome Game",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout


    res = runner.invoke(
        app, ["input-add", "jump", "-k", "KEY_SPACE", "-p", str(tmp_path), "--json"]
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"action_name": "jump"' in res.stdout


def test_set_project_resolution(tmp_path):
    from godot_cli_connect.operations.config_editor import set_project_resolution

    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""config_version=5\n""")

    res = set_project_resolution(str(tmp_path), preset="720p", stretch_mode="canvas_items", stretch_aspect="keep")
    assert res["status"] == "success"
    assert res["viewport_width"] == 1280
    assert res["viewport_height"] == 720

    content = godot_file.read_text()
    assert "viewport_width=1280.0" in content
    assert "viewport_height=720.0" in content
    assert 'mode="canvas_items"' in content


def test_cli_config_resolution(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""config_version=5\n""")

    res = runner.invoke(
        app,
        ["config-resolution", "--preset", "1080p", "-p", str(tmp_path), "--json"],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"viewport_width": 1920' in res.stdout
