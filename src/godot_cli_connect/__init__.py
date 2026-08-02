"""
godot-cli-connect package entry point
"""

from .core import (
    check_syntax,
    create_resource,
    dump_extension_api,
    export_project,
    get_project_logs,
    inspect_project,
    reimport_assets,
    run_test_script,
    take_screenshot,
)
from .exceptions import GodotCliError, GodotExecutionError, GodotNotFoundError
from .finder import find_godot_executable
from .models import OperationResult, as_result_dict, err, is_success, ok

__version__ = "0.1.0"

__all__ = [
    "GodotCliError",
    "GodotExecutionError",
    "GodotNotFoundError",
    "OperationResult",
    "as_result_dict",
    "check_syntax",
    "create_resource",
    "dump_extension_api",
    "err",
    "export_project",
    "find_godot_executable",
    "get_project_logs",
    "inspect_project",
    "is_success",
    "ok",
    "reimport_assets",
    "run_test_script",
    "take_screenshot",
]
