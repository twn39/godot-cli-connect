"""
Subprocess execution runner helper
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from ..exceptions import GodotTimeoutError

DEFAULT_TIMEOUT = int(os.environ.get("GODOT_CLI_TIMEOUT", "30"))

LineCallback = Callable[[str], None]


def build_godot_cmd(
    godot_bin: str,
    project_path: str | None = None,
    headless: bool = True,
    editor: bool = False,
    quit_after: bool = False,
    script: str | None = None,
    extra_flags: list[str] | None = None,
) -> list[str]:
    """Builds a standardized Godot 4 command-line argument list."""
    cmd = [godot_bin]
    if project_path:
        cmd.extend(["--path", os.path.abspath(project_path)])
    if headless:
        cmd.append("--headless")
    if editor:
        cmd.append("--editor")
    if quit_after:
        cmd.append("--quit")
    if script:
        cmd.extend(["-s", os.path.abspath(script)])
    if extra_flags:
        cmd.extend(extra_flags)
    return cmd


def run_godot_cmd(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    """Helper function to execute Godot executable commands cleanly with timeout management."""
    eff_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=eff_timeout)
    except subprocess.TimeoutExpired as e:
        raise GodotTimeoutError(
            f"Godot command timed out after {eff_timeout} seconds: {' '.join(cmd)}"
        ) from e


def run_godot_cmd_streaming(
    cmd: list[str],
    timeout: int | None = None,
    *,
    on_stdout_line: LineCallback | None = None,
    on_stderr_line: LineCallback | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a Godot command while streaming stdout/stderr line-by-line.

    Useful for long jobs (export, GUT). Still returns a CompletedProcess with
    full captured output for callers that also need the full buffers.
    """
    eff_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError:
        # Match subprocess.run behaviour for permission / missing binary errors.
        raise

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _pump(stream, chunks: list[str], callback: LineCallback | None) -> None:
        if stream is None:
            return
        for line in stream:
            chunks.append(line)
            if callback is not None:
                callback(line.rstrip("\n"))

    t_out = threading.Thread(
        target=_pump, args=(proc.stdout, stdout_chunks, on_stdout_line), daemon=True
    )
    t_err = threading.Thread(
        target=_pump, args=(proc.stderr, stderr_chunks, on_stderr_line), daemon=True
    )
    t_out.start()
    t_err.start()

    deadline = time.monotonic() + eff_timeout
    while proc.poll() is None:
        if time.monotonic() > deadline:
            proc.kill()
            t_out.join(timeout=1)
            t_err.join(timeout=1)
            raise GodotTimeoutError(
                f"Godot command timed out after {eff_timeout} seconds: {' '.join(cmd)}"
            )
        time.sleep(0.05)

    t_out.join(timeout=5)
    t_err.join(timeout=5)
    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
    )


@contextmanager
def temporary_godot_script(source: str, suffix: str = ".gd") -> Iterator[str]:
    """
    Write a temporary GDScript file and always delete it when the block exits.

    Yields the absolute path of the temporary script.
    """
    path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, mode="w", encoding="utf-8"
        ) as tf:
            tf.write(source)
            path = tf.name
        yield path
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def run_godot_script(
    godot_bin: str,
    project_path: str,
    script_source: str,
    *,
    timeout: int = 20,
) -> subprocess.CompletedProcess:
    """
    Write ``script_source`` to a temp .gd file, run it headless under ``project_path``,
    and clean up the temp file.
    """
    with temporary_godot_script(script_source) as script_path:
        cmd = build_godot_cmd(
            godot_bin,
            project_path=project_path,
            headless=True,
            script=script_path,
        )
        return run_godot_cmd(cmd, timeout=timeout)
