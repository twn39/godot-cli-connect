"""
Godot Extension API dumping module
"""

import os
import shutil
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd

def dump_extension_api(output_path: str) -> Dict[str, Any]:
    """Dumps complete Godot 4 Extension API schema to JSON file."""
    godot_bin = find_godot_executable()
    abs_output = os.path.abspath(output_path)
    
    cmd = [
        godot_bin,
        "--headless",
        "--dump-extension-api"
    ]
    
    try:
        res = run_godot_cmd(cmd, timeout=30)
        if res.returncode == 0 and os.path.exists("extension_api.json"):
            shutil.move("extension_api.json", abs_output)
            return {"status": "success", "api_json_path": abs_output}
        return {"status": "error", "stderr": res.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}
