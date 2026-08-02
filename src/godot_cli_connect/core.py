"""
Core Operations Facade Module for Godot Engine Interactions
"""

from .operations.runner import run_godot_cmd as _run_godot_cmd
from .operations.checker import check_syntax
from .operations.screenshot import take_screenshot
from .operations.script_runner import run_test_script
from .operations.api import dump_extension_api
from .operations.resources import create_resource, reimport_assets
from .operations.inspector import inspect_project
from .operations.exporter import export_project
from .operations.logger import get_project_logs
from .operations.scene_inspector import inspect_scene
from .operations.evaluator import eval_code
from .operations.linter import format_gdscript, lint_gdscript
from .operations.class_info import get_class_info
from .operations.gut_runner import run_gut_tests
from .operations.config_editor import set_config_setting, add_input_action
from .operations.scene_editor import (
    create_scene,
    add_node_to_scene,
    edit_node_in_scene,
    remove_node_from_scene,
    connect_signal,
    disconnect_signal,
    rename_node,
    reparent_node,
    inspect_signals,
)
from .operations.docs_search import search_docs
from .operations.screenshot_diff import compare_screenshots
from .operations.project_init import init_project

__all__ = [
    "_run_godot_cmd",
    "check_syntax",
    "take_screenshot",
    "run_test_script",
    "dump_extension_api",
    "create_resource",
    "reimport_assets",
    "inspect_project",
    "export_project",
    "get_project_logs",
    "inspect_scene",
    "eval_code",
    "format_gdscript",
    "lint_gdscript",
    "get_class_info",
    "run_gut_tests",
    "set_config_setting",
    "add_input_action",
    "create_scene",
    "add_node_to_scene",
    "edit_node_in_scene",
    "remove_node_from_scene",
    "connect_signal",
    "disconnect_signal",
    "rename_node",
    "reparent_node",
    "inspect_signals",
    "search_docs",
    "compare_screenshots",
    "init_project",
]


