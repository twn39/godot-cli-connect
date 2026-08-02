"""
Core Operations Facade Module for Godot Engine Interactions
"""

from .operations.api import dump_extension_api
from .operations.bg_remove import remove_background, remove_background_batch
from .operations.checker import check_syntax
from .operations.class_info import get_class_info
from .operations.config_editor import (
    add_autoload,
    add_input_action,
    get_config_setting,
    list_autoloads,
    remove_autoload,
    set_config_setting,
)
from .operations.docs_search import search_docs
from .operations.env_info import probe_godot_info
from .operations.evaluator import eval_code
from .operations.exporter import export_project, list_export_presets
from .operations.gut_runner import run_gut_tests
from .operations.inspector import inspect_project
from .operations.linter import format_gdscript, lint_gdscript
from .operations.logger import get_project_logs
from .operations.project_init import init_project
from .operations.resources import create_resource, reimport_assets
from .operations.runner import (
    run_godot_cmd,
    run_godot_cmd_streaming,
    run_godot_script,
)
from .operations.scene_editor import (
    add_node_to_scene,
    attach_script,
    connect_signal,
    create_scene,
    disconnect_signal,
    edit_node_in_scene,
    inspect_signals,
    remove_node_from_scene,
    rename_node,
    reparent_node,
)
from .operations.scene_inspector import inspect_scene
from .operations.screenshot import take_screenshot
from .operations.screenshot_diff import compare_screenshots
from .operations.script_editor import (
    attach_script_to_node,
    create_script,
    read_script,
    write_script,
)
from .operations.script_runner import run_test_script
from .operations.tools_catalog import list_tools

# Backward-compatible private alias used by older callers.
_run_godot_cmd = run_godot_cmd

__all__ = [
    "_run_godot_cmd",
    "run_godot_cmd",
    "run_godot_cmd_streaming",
    "run_godot_script",
    "add_autoload",
    "add_input_action",
    "add_node_to_scene",
    "attach_script",
    "attach_script_to_node",
    "check_syntax",
    "compare_screenshots",
    "connect_signal",
    "create_resource",
    "create_scene",
    "create_script",
    "disconnect_signal",
    "dump_extension_api",
    "edit_node_in_scene",
    "eval_code",
    "export_project",
    "format_gdscript",
    "get_class_info",
    "get_config_setting",
    "get_project_logs",
    "init_project",
    "inspect_project",
    "inspect_scene",
    "inspect_signals",
    "list_autoloads",
    "list_export_presets",
    "list_tools",
    "lint_gdscript",
    "probe_godot_info",
    "read_script",
    "reimport_assets",
    "remove_autoload",
    "remove_background",
    "remove_background_batch",
    "remove_node_from_scene",
    "rename_node",
    "reparent_node",
    "run_gut_tests",
    "run_test_script",
    "search_docs",
    "set_config_setting",
    "take_screenshot",
    "write_script",
]
