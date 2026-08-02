"""
Unit tests for runner module
"""

import subprocess
import pytest
from godot_cli_connect.operations.runner import build_godot_cmd, run_godot_cmd
from godot_cli_connect.exceptions import GodotTimeoutError


def test_build_godot_cmd_default():
    cmd = build_godot_cmd("/bin/godot")
    assert cmd == ["/bin/godot", "--headless"]


def test_build_godot_cmd_full():
    cmd = build_godot_cmd(
        "/bin/godot",
        project_path="/my/project",
        headless=True,
        editor=True,
        quit_after=True,
        script="main.gd",
        extra_flags=["--debug"],
    )
    assert "/bin/godot" in cmd
    assert "--path" in cmd
    assert "/my/project" in cmd
    assert "--headless" in cmd
    assert "--editor" in cmd
    assert "--quit" in cmd
    assert "-s" in cmd
    assert "--debug" in cmd


def test_run_godot_cmd_timeout(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    monkeypatch.setattr(subprocess, "run", mock_run)
    with pytest.raises(GodotTimeoutError):
        run_godot_cmd(["godot", "--headless"], timeout=5)
