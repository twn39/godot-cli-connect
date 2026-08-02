"""
Unit tests for operations modules
"""

import subprocess

from godot_cli_connect.operations.checker import check_syntax
from godot_cli_connect.operations.inspector import inspect_project
from godot_cli_connect.operations.script_runner import run_test_script


def test_check_syntax_success(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="No errors", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = check_syntax(str(tmp_path))
    assert res["status"] == "success"


def test_inspect_project_no_file(tmp_path):
    res = inspect_project(str(tmp_path))
    assert res["status"] == "error"
    assert "No project.godot found" in res["message"]


def test_inspect_project_valid(tmp_path):
    godot_file = tmp_path / "project.godot"
    godot_file.write_text("""
config_version=5
[application]
config/name="Test Game"
run/main_scene="res://main.tscn"
""")
    res = inspect_project(str(tmp_path))
    assert res["status"] == "success"
    assert res["metadata"]["project_name"] == "Test Game"
    assert res["metadata"]["main_scene"] == "res://main.tscn"


def test_run_test_script(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="Test passed", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = run_test_script(str(tmp_path), "test.gd")
    assert res["status"] == "success"
    assert res["stdout"] == "Test passed"


def test_verify_import_status(tmp_path):
    from godot_cli_connect.operations.resources import verify_import_status

    valid_file = tmp_path / "valid.png.import"
    valid_file.write_text("[remap]\nvalid=true\n")
    invalid_file = tmp_path / "invalid.png.import"
    invalid_file.write_text("[remap]\nvalid=false\n")

    status = verify_import_status(str(tmp_path))
    assert status["total"] == 2
    assert status["valid_count"] == 1
    assert status["invalid_count"] == 1
    assert "invalid.png.import" in status["invalid"][0]


def test_reimport_assets_clean(monkeypatch, tmp_path):
    from godot_cli_connect.operations.resources import reimport_assets

    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    imported_dir = tmp_path / ".godot" / "imported"
    imported_dir.mkdir(parents=True)
    (imported_dir / "stale.ctex").touch()

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="Reimport ok", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = reimport_assets(str(tmp_path), clean=True)
    assert res["status"] == "success"
    assert res["clean"] is True
