"""Tests for get_project_logs operation."""

from godot_cli_connect.operations.logger import get_project_logs


def test_get_project_logs_no_project(tmp_path):
    res = get_project_logs(str(tmp_path))
    assert res["status"] == "error"
    assert "project.godot" in res.get("message", "").lower() or "No project" in res.get(
        "message", ""
    )


def test_get_project_logs_missing_log_file(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="LogGame"\n'
    )
    # Point userdata to an empty temp dir so godot.log is missing.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr("sys.platform", "linux")

    res = get_project_logs(str(tmp_path), lines=10)
    assert res["status"] == "error"
    assert "Log file not found" in res["message"]


def test_get_project_logs_success(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="LogGame"\n'
    )
    fake_home = tmp_path / "home"
    log_dir = fake_home / ".local/share/godot/app_userdata/LogGame/logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "godot.log"
    log_file.write_text(
        "INFO: boot\nWARNING: soft\nERROR: boom\nSCRIPT ERROR: fail\nOK line\n"
    )

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr("sys.platform", "linux")

    res = get_project_logs(str(tmp_path), lines=20)
    assert res["status"] == "success"
    assert res["total_lines_read"] == 5
    assert any("ERROR: boom" in e for e in res["errors"])
    assert any("WARNING: soft" in w for w in res["warnings"])
    assert res["logs"][-1] == "OK line"
