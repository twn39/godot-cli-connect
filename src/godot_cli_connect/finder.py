"""
Godot Executable Finder Module
"""

import os
import shutil

from .exceptions import GodotNotFoundError


def find_godot_executable() -> str:
    """Finds the Godot 4 executable binary on macOS, Linux, or Windows."""
    env_path = os.environ.get("GODOT_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # Common macOS paths
    mac_paths = [
        "/Applications/Godot.app/Contents/MacOS/Godot",
        "/Applications/Godot_4.app/Contents/MacOS/Godot",
    ]
    for p in mac_paths:
        if os.path.exists(p):
            return p

    # Standard system PATH search
    for cmd in ["godot", "godot4", "godot.exe"]:
        found = shutil.which(cmd)
        if found:
            return found

    raise GodotNotFoundError(
        "Godot 4 executable not found. Please set the GODOT_PATH environment variable."
    )
