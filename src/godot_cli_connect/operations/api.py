"""
Godot Extension API dumping module
"""

import os
import shutil
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd


def dump_extension_api(output_path: str) -> dict[str, Any]:
    """Dumps complete Godot 4 Extension API schema to JSON file."""
    godot_bin = find_godot_executable()
    abs_output = os.path.abspath(output_path)

    cmd = build_godot_cmd(godot_bin, headless=True, extra_flags=["--dump-extension-api"])

    try:
        res = run_godot_cmd(cmd, timeout=30)
        if res.returncode == 0 and os.path.exists("extension_api.json"):
            shutil.move("extension_api.json", abs_output)
            return ok(api_json_path=abs_output)
        return err(
            res.stderr or "Failed to dump extension API",
            stderr=res.stderr,
        )
    except Exception as e:
        return err(str(e))
