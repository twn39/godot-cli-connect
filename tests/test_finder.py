"""
Unit tests for finder module
"""

import os

import pytest

from godot_cli_connect.exceptions import GodotNotFoundError
from godot_cli_connect.finder import find_godot_executable


def test_find_godot_executable_env(monkeypatch, tmp_path):
    fake_godot = tmp_path / "fake_godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))
    assert find_godot_executable() == str(fake_godot)


def test_find_godot_executable_not_found(monkeypatch):
    monkeypatch.delenv("GODOT_PATH", raising=False)
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    monkeypatch.setattr("shutil.which", lambda cmd: None)

    with pytest.raises(GodotNotFoundError):
        find_godot_executable()
