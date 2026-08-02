"""
Unit tests for project_init module and init-project CLI command
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.project_init import init_project

runner = CliRunner()


def test_init_project(tmp_path):
    proj_dir = tmp_path / "MyTestGame"
    res = init_project(
        project_path=str(proj_dir),
        project_name="My Test Game",
        create_main_scene=True,
    )

    assert res["status"] == "success"
    assert res["project_name"] == "My Test Game"
    assert (proj_dir / "project.godot").exists()
    assert (proj_dir / "main.tscn").exists()


def test_cli_init_project(tmp_path):
    proj_dir = tmp_path / "CliTestGame"
    res = runner.invoke(
        app,
        [
            "init-project",
            str(proj_dir),
            "-n",
            "CLI Game",
            "--json",
        ],
    )

    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert (proj_dir / "project.godot").exists()
