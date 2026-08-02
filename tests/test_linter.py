"""
Unit and integration tests for linter module, format, and lint CLI commands
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.linter import (
    builtin_format_content,
    builtin_lint_content,
    format_gdscript,
    lint_gdscript,
)

runner = CliRunner()

SAMPLE_UNFORMATTED_SCRIPT = """extends Node

func BadFunctionName():  
    var x = 1
    return x
"""

SAMPLE_CLEAN_SCRIPT = """extends Node

class_name PlayerController

const MAX_SPEED = 100

func move_player():
\treturn true
"""


def test_builtin_format_content():
    formatted = builtin_format_content("func test():   \n    var a = 1  ")
    assert "func test():\n" in formatted
    assert "\tvar a = 1" in formatted
    assert formatted.endswith("\n")


def test_builtin_lint_content():
    content = """extends Node
class_name bad_class_name
const bad_const = 10
func BadFunc():
    pass
"""
    diags = builtin_lint_content("test.gd", content)
    codes = [d["code"] for d in diags]
    assert "style/naming_convention" in codes
    assert len(diags) >= 3


def test_format_gdscript(tmp_path):
    gd_file = tmp_path / "test.gd"
    gd_file.write_text(SAMPLE_UNFORMATTED_SCRIPT)

    res_check = format_gdscript(str(tmp_path), target=str(gd_file), check_only=True)
    assert res_check["status"] == "formatting_required"

    res_format = format_gdscript(str(tmp_path), target=str(gd_file), check_only=False)
    assert res_format["status"] == "success"


def test_lint_gdscript(tmp_path):
    gd_file = tmp_path / "test.gd"
    gd_file.write_text(SAMPLE_CLEAN_SCRIPT)

    res = lint_gdscript(str(tmp_path), target=str(gd_file))
    assert "diagnostics" in res
    assert "tool_used" in res


def test_cli_format_check(tmp_path):
    gd_file = tmp_path / "test.gd"
    gd_file.write_text(SAMPLE_UNFORMATTED_SCRIPT)

    res = runner.invoke(
        app, ["format", str(gd_file), "-p", str(tmp_path), "--check", "--json"]
    )
    assert '"status": "formatting_required"' in res.stdout


def test_cli_lint(tmp_path):
    gd_file = tmp_path / "test.gd"
    gd_file.write_text(SAMPLE_CLEAN_SCRIPT)

    res = runner.invoke(app, ["lint", str(gd_file), "-p", str(tmp_path), "--json"])
    assert '"tool_used":' in res.stdout


def test_builtin_lint_python_types_and_deprecations():
    bad_code = """extends Node

var val: str = "hello"
var data: dict = {}
var items: list = []

func _ready() -> void:
    var n = None
    var ok = True
    yield(get_tree(), "idle_frame")
    var scene = load("res://test.tscn").instance()
    var r = rand_range(0.0, 1.0)
    export var count: int = 5
    onready var label: Label = $Label
"""
    diags = builtin_lint_content("bad_script.gd", bad_code)
    codes = [d["code"] for d in diags]
    assert "type/python_str_type" in codes
    assert "type/python_dict_type" in codes
    assert "type/python_list_type" in codes
    assert "syntax/python_none" in codes
    assert "syntax/python_bool" in codes
    assert "deprecated/yield" in codes
    assert "deprecated/instance" in codes
    assert "deprecated/rand_range" in codes
    assert "deprecated/godot3_export" in codes
    assert "deprecated/godot3_onready" in codes
