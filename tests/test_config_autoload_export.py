"""Tests for config-get, autoload, export-presets."""

from godot_cli_connect.operations.config_editor import (
    add_autoload,
    get_config_setting,
    list_autoloads,
    remove_autoload,
    set_config_setting,
)
from godot_cli_connect.operations.exporter import list_export_presets
from godot_cli_connect.operations.tools_catalog import list_tools


def test_config_get_and_set(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "godot_cli_connect.operations.config_editor.find_godot_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("no godot")),
    )
    (tmp_path / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="Demo"\n'
    )
    g = get_config_setting(str(tmp_path), "application/config/name")
    assert g["status"] == "success"
    assert g["value"] == "Demo"

    s = set_config_setting(str(tmp_path), "application/config/name", "NewName")
    assert s["status"] == "success"
    g2 = get_config_setting(str(tmp_path), "config/name")
    assert g2["status"] == "success"
    assert g2["value"] == "NewName"


def test_autoload_lifecycle(tmp_path):
    (tmp_path / "project.godot").write_text("config_version=5\n")
    (tmp_path / "autoload").mkdir()
    (tmp_path / "autoload" / "gs.gd").write_text("extends Node\n")

    add = add_autoload(str(tmp_path), "GameState", "res://autoload/gs.gd")
    assert add["status"] == "success"
    listed = list_autoloads(str(tmp_path))
    assert listed["count"] == 1
    assert listed["autoloads"][0]["name"] == "GameState"
    assert listed["autoloads"][0]["enabled"] is True

    rm = remove_autoload(str(tmp_path), "GameState")
    assert rm["status"] == "success"
    assert list_autoloads(str(tmp_path))["count"] == 0


def test_list_export_presets(tmp_path):
    (tmp_path / "export_presets.cfg").write_text(
        """
[preset.0]
name="Mac OSX"
platform="macOS"
runnable=true
export_path="build/game.zip"

[preset.1]
name="Web"
platform="Web"
runnable=false
export_path="build/web"
"""
    )
    res = list_export_presets(str(tmp_path))
    assert res["status"] == "success"
    assert res["count"] == 2
    names = {p["name"] for p in res["presets"]}
    assert names == {"Mac OSX", "Web"}


def test_list_tools():
    res = list_tools()
    assert res["status"] == "success"
    assert res["tool_count"] >= 30
    names = {t["name"] for t in res["tools"]}
    assert "script-create" in names
    assert "tools-list" in names
    assert "autoload-add" in names
