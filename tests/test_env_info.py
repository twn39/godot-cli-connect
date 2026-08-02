"""Tests for probe_godot_info."""

from godot_cli_connect.operations.env_info import probe_godot_info


def test_probe_godot_missing(monkeypatch):
    monkeypatch.delenv("GODOT_PATH", raising=False)
    monkeypatch.setattr(
        "godot_cli_connect.operations.env_info.find_godot_executable",
        lambda: (_ for _ in ()).throw(
            __import__(
                "godot_cli_connect.exceptions", fromlist=["GodotNotFoundError"]
            ).GodotNotFoundError("missing")
        ),
    )
    res = probe_godot_info()
    assert res["status"] == "error"
    assert res.get("godot_found") is False


def test_probe_godot_found(monkeypatch, tmp_path):
    fake = tmp_path / "godot"
    fake.write_text("#!/bin/sh\necho '4.3.stable.official'\n")
    fake.chmod(0o755)
    monkeypatch.setattr(
        "godot_cli_connect.operations.env_info.find_godot_executable",
        lambda: str(fake),
    )

    def mock_run(cmd, capture_output, text, timeout):
        class R:
            stdout = "4.3.stable.official\n"
            stderr = ""

        return R()

    monkeypatch.setattr(
        "godot_cli_connect.operations.env_info.subprocess.run", mock_run
    )
    res = probe_godot_info()
    assert res["status"] == "success"
    assert res["godot_found"] is True
    assert res["version_major"] == 4
    assert res["is_godot_4"] is True
