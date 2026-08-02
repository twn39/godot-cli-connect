"""
Unit and integration tests for evaluator module and eval CLI command
"""

import subprocess

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.evaluator import eval_code

runner = CliRunner()


def test_eval_code_expression_success(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    mock_stdout = """EVAL_MODE:expression
EVAL_RESULT:5
"""

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=mock_stdout, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = eval_code(str(tmp_path), "Vector2(0, 0).distance_to(Vector2(3, 4))")

    assert res["status"] == "success"
    assert res["mode"] == "expression"
    assert res["result"] == 5


def test_eval_code_with_vars(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    mock_stdout = """EVAL_MODE:expression
EVAL_RESULT:30
"""

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=mock_stdout, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = eval_code(str(tmp_path), "x * y + 10", vars_json='{"x": 5, "y": 4}')

    assert res["status"] == "success"
    assert res["result"] == 30


def test_cli_eval_cmd_json(monkeypatch, tmp_path):
    fake_godot = tmp_path / "godot"
    fake_godot.touch()
    monkeypatch.setenv("GODOT_PATH", str(fake_godot))

    mock_stdout = """EVAL_MODE:expression
EVAL_RESULT:"Hello World"
"""

    def mock_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=mock_stdout, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = runner.invoke(
        app, ["eval", "str('Hello World')", "-p", str(tmp_path), "--json"]
    )

    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"result": "Hello World"' in res.stdout
