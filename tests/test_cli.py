"""
Integration tests for CLI interface using Typer CliRunner
"""

from typer.testing import CliRunner
from godot_cli_connect.cli import app

runner = CliRunner()


def test_cli_info_found(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    res = runner.invoke(app, ["info"])
    assert res.exit_code == 0
    assert "Godot Binary Found" in res.stdout


def test_cli_inspect_json(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""
config_version=5
[application]
config/name="Test Game"
""")
    res = runner.invoke(app, ["inspect", "-p", str(tmp_path), "--json"])
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"project_name": "Test Game"' in res.stdout
