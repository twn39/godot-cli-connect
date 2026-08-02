"""Tests for streaming Godot command runner helpers."""

from __future__ import annotations

import sys

from godot_cli_connect.operations.runner import run_godot_cmd_streaming


def test_run_godot_cmd_streaming_captures_and_callbacks():
    lines: list[str] = []
    cmd = [sys.executable, "-c", "print('hello'); print('world')"]
    res = run_godot_cmd_streaming(
        cmd,
        timeout=10,
        on_stdout_line=lines.append,
    )
    assert res.returncode == 0
    assert "hello" in res.stdout
    assert "world" in res.stdout
    assert lines == ["hello", "world"]


def test_run_godot_cmd_streaming_stderr():
    errs: list[str] = []
    cmd = [
        sys.executable,
        "-c",
        "import sys; print('e1', file=sys.stderr); print('e2', file=sys.stderr)",
    ]
    res = run_godot_cmd_streaming(
        cmd,
        timeout=10,
        on_stderr_line=errs.append,
    )
    assert res.returncode == 0
    assert "e1" in res.stderr
    assert errs == ["e1", "e2"]
