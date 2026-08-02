"""
godot-cli-connect package entry point
"""

from .finder import find_godot_executable
from .exceptions import GodotCliError, GodotNotFoundError, GodotExecutionError
from .core import (
    check_syntax,
    take_screenshot,
    run_test_script,
    dump_extension_api,
    create_resource,
    reimport_assets,
    inspect_project,
    export_project,
    get_project_logs,
)

__version__ = "0.1.0"

__all__ = [
    "find_godot_executable",
    "GodotCliError",
    "GodotNotFoundError",
    "GodotExecutionError",
    "check_syntax",
    "take_screenshot",
    "run_test_script",
    "dump_extension_api",
    "create_resource",
    "reimport_assets",
    "inspect_project",
    "export_project",
    "get_project_logs",
]
