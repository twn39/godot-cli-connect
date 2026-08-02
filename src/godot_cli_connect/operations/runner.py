"""
Subprocess execution runner helper
"""

import subprocess
from typing import List

def run_godot_cmd(cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Helper function to execute Godot executable commands cleanly."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
