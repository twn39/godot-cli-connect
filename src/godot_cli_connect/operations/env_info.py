"""
Environment / Godot binary capability probing.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from ..exceptions import GodotNotFoundError
from ..finder import find_godot_executable
from ..models import err, ok


def probe_godot_info() -> dict[str, Any]:
    """
    Locate Godot binary and probe version / basic capabilities.

    Does not require a project path.
    """
    try:
        godot_bin = find_godot_executable()
    except GodotNotFoundError as e:
        return err(
            str(e),
            godot_found=False,
            godot_path=None,
            version=None,
            version_major=None,
        )
    except Exception as e:
        return err(str(e), godot_found=False)

    version_raw = None
    version_major = None
    version_minor = None
    is_godot4 = None
    try:
        proc = subprocess.run(
            [godot_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_raw = (proc.stdout or proc.stderr or "").strip().splitlines()
        version_raw = version_raw[0] if version_raw else ""
        # e.g. "4.3.stable.official.xxxxx" or "4.2.1.stable"
        m = re.match(r"(\d+)\.(\d+)", version_raw)
        if m:
            version_major = int(m.group(1))
            version_minor = int(m.group(2))
            is_godot4 = version_major >= 4
    except Exception as e:
        version_raw = f"probe_failed: {e}"

    return ok(
        godot_found=True,
        godot_path=godot_bin,
        version=version_raw,
        version_major=version_major,
        version_minor=version_minor,
        is_godot_4=is_godot4,
        headless_supported=True,
        godot_path_env=os.environ.get("GODOT_PATH"),
        timeout_default=int(os.environ.get("GODOT_CLI_TIMEOUT", "30")),
        message=f"Godot binary found: {godot_bin}",
    )
