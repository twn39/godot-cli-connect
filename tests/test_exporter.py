"""Tests for export_project operation."""

import subprocess

from godot_cli_connect.operations import exporter
from godot_cli_connect.operations.exporter import export_project


def test_export_project_success(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    out = tmp_path / "build" / "game.app"
    out.parent.mkdir(parents=True)

    def mock_stream(cmd, timeout=None, **kwargs):
        out.write_text("binary")
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="ok", stderr=""
        )

    monkeypatch.setattr(exporter, "run_godot_cmd_streaming", mock_stream)
    res = export_project(str(tmp_path), "Mac OSX", str(out), debug=False)
    assert res["status"] == "success"
    assert res["mode"] == "release"
    assert res["export_preset"] == "Mac OSX"
    assert res["output_path"] == str(out.resolve())


def test_export_project_failure(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    def mock_stream(cmd, timeout=None, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr="export failed"
        )

    monkeypatch.setattr(exporter, "run_godot_cmd_streaming", mock_stream)
    missing = tmp_path / "missing.bin"
    res = export_project(str(tmp_path), "Linux", str(missing), debug=True)
    assert res["status"] == "error"
    assert res["mode"] == "debug"
    assert "return code" in res["message"]


def test_export_project_godot_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("GODOT_PATH", raising=False)
    monkeypatch.setattr(
        "godot_cli_connect.operations.exporter.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    res = export_project(str(tmp_path), "Web", str(tmp_path / "out"))
    assert res["status"] == "error"
    assert "no godot" in res["message"]
