"""
Subprocess execution runner helper
"""

import os
import subprocess
from typing import List, Optional
from ..exceptions import GodotTimeoutError

DEFAULT_TIMEOUT = int(os.environ.get("GODOT_CLI_TIMEOUT", "30"))


def build_godot_cmd(
    godot_bin: str,
    project_path: Optional[str] = None,
    headless: bool = True,
    editor: bool = False,
    quit_after: bool = False,
    script: Optional[str] = None,
    extra_flags: Optional[List[str]] = None,
) -> List[str]:
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


def run_godot_cmd(
    cmd: List[str], timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    """Helper function to execute Godot executable commands cleanly with timeout management."""
    eff_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=eff_timeout)
    except subprocess.TimeoutExpired as e:
        raise GodotTimeoutError(
            f"Godot command timed out after {eff_timeout} seconds: {' '.join(cmd)}"
        ) from e
