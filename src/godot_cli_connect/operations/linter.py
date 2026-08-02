"""
GDScript code formatting and static linting module with multi-toolchain support
"""

import os
import re
import shutil
import subprocess
from typing import Any

from ..models import err, ok
from .checker import check_syntax


def _find_formatter_tool() -> str | None:
    for tool in ["gdstyle", "gdformat"]:
        found = shutil.which(tool)
        if found:
            return found
    return None


def _find_linter_tool() -> str | None:
    for tool in ["gdstyle", "gdlint"]:
        found = shutil.which(tool)
        if found:
            return found
    return None


def builtin_format_content(content: str) -> str:
    """Builtin Python fallback formatter for GDScript according to Godot 4 style guide."""
    lines = content.splitlines()
    formatted_lines = []
    for line in lines:
        # Strip trailing whitespace
        stripped_line = line.rstrip()
        # Convert leading 4-space blocks to tabs (Godot 4 style guide preference)
        indent_len = len(stripped_line) - len(stripped_line.lstrip(" "))
        if indent_len > 0 and indent_len % 4 == 0:
            tabs = "\t" * (indent_len // 4)
            stripped_line = tabs + stripped_line.lstrip(" ")
        formatted_lines.append(stripped_line)

    result = "\n".join(formatted_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def builtin_lint_content(file_path: str, content: str) -> list[dict[str, Any]]:
    """Builtin Python fallback GDScript linter for naming conventions and style."""
    diagnostics = []
    lines = content.splitlines()

    func_re = re.compile(r"^\s*func\s+([a-zA-Z0-9_]+)\s*\(")
    const_re = re.compile(r"^\s*const\s+([a-zA-Z0-9_]+)\s*=")
    class_name_re = re.compile(r"^\s*class_name\s+([a-zA-Z0-9_]+)")

    def is_snake_case(s: str) -> bool:
        return s.startswith("_") or bool(re.match(r"^[a-z0-9_]+$", s))

    def is_pascal_case(s: str) -> bool:
        return bool(re.match(r"^[A-Z][a-zA-Z0-9]*$", s))

    def is_upper_snake_case(s: str) -> bool:
        return bool(re.match(r"^[A-Z0-9_]+$", s))

    py_type_str_re = re.compile(r"(?:\b:\s*|\b->\s*)str\b")
    py_type_dict_re = re.compile(r"(?:\b:\s*|\b->\s*)dict\b")
    py_type_list_re = re.compile(r"(?:\b:\s*|\b->\s*)list\b")

    yield_re = re.compile(r"\byield\s*\(")
    instance_re = re.compile(r"\.instance\s*\(")
    rand_range_re = re.compile(r"\brand_range\s*\(")
    godot3_export_re = re.compile(r"^\s*export(?:\([^)]*\))?\s+var\b")
    godot3_onready_re = re.compile(r"^\s*onready\s+var\b")

    none_re = re.compile(r"\bNone\b")
    capital_bool_re = re.compile(r"\b(True|False)\b")

    for idx, line in enumerate(lines, start=1):
        code_part = line.split("#")[0]

        # Line length check
        if len(line) > 120:
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "style/line_length",
                    "message": f"Line exceeds 120 characters ({len(line)} chars)",
                }
            )

        # Check Python-style type annotations
        if py_type_str_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "type/python_str_type",
                    "message": "Use 'String' instead of 'str' in GDScript 2.0 type annotations.",
                }
            )
        if py_type_dict_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "type/python_dict_type",
                    "message": "Use 'Dictionary' instead of 'dict' in GDScript 2.0 type annotations.",
                }
            )
        if py_type_list_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "type/python_list_type",
                    "message": "Use 'Array' instead of 'list' in GDScript 2.0 type annotations.",
                }
            )

        # Check Godot 3 -> 4 Deprecations
        if yield_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "error",
                    "code": "deprecated/yield",
                    "message": "'yield()' is deprecated in Godot 4, use 'await'.",
                }
            )
        if instance_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "error",
                    "code": "deprecated/instance",
                    "message": "'.instance()' is deprecated in Godot 4, use '.instantiate()'.",
                }
            )
        if rand_range_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "deprecated/rand_range",
                    "message": "'rand_range()' is deprecated in Godot 4, use 'randf_range()' or 'randi_range()'.",
                }
            )
        if godot3_export_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "deprecated/godot3_export",
                    "message": "Use '@export var' annotation in Godot 4.",
                }
            )
        if godot3_onready_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "deprecated/godot3_onready",
                    "message": "Use '@onready var' annotation in Godot 4.",
                }
            )

        # Check Python keywords/literals
        if none_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "syntax/python_none",
                    "message": "Use 'null' instead of 'None' in GDScript.",
                }
            )
        if capital_bool_re.search(code_part):
            diagnostics.append(
                {
                    "file": file_path,
                    "line": idx,
                    "column": 1,
                    "severity": "warning",
                    "code": "syntax/python_bool",
                    "message": "Use lowercase 'true' / 'false' in GDScript.",
                }
            )

        # Check func name
        f_match = func_re.search(line)
        if f_match:
            fn_name = f_match.group(1)
            if not is_snake_case(fn_name):
                diagnostics.append(
                    {
                        "file": file_path,
                        "line": idx,
                        "column": f_match.start(1) + 1,
                        "severity": "warning",
                        "code": "style/naming_convention",
                        "message": f"Function name '{fn_name}' should be snake_case",
                    }
                )

        # Check const name
        c_match = const_re.search(line)
        if c_match:
            cn_name = c_match.group(1)
            if not is_upper_snake_case(cn_name):
                diagnostics.append(
                    {
                        "file": file_path,
                        "line": idx,
                        "column": c_match.start(1) + 1,
                        "severity": "warning",
                        "code": "style/naming_convention",
                        "message": f"Constant name '{cn_name}' should be UPPER_SNAKE_CASE",
                    }
                )

        # Check class_name
        cls_match = class_name_re.search(line)
        if cls_match:
            cls_name = cls_match.group(1)
            if not is_pascal_case(cls_name):
                diagnostics.append(
                    {
                        "file": file_path,
                        "line": idx,
                        "column": cls_match.start(1) + 1,
                        "severity": "warning",
                        "code": "style/naming_convention",
                        "message": f"Class name '{cls_name}' should be PascalCase",
                    }
                )

    return diagnostics


def format_gdscript(
    project_path: str, target: str = ".", check_only: bool = False
) -> dict[str, Any]:
    """Formats GDScript files in the project or target path using external tools or builtin fallback."""
    abs_project = os.path.abspath(project_path)
    if target.startswith("res://"):
        rel_target = target.replace("res://", "")
        abs_target = os.path.join(abs_project, rel_target)
    else:
        abs_target = os.path.abspath(target)
        if not abs_target.startswith(abs_project):
            abs_target = os.path.join(abs_project, target)

    tool_path = _find_formatter_tool()
    if tool_path:
        tool_name = os.path.basename(tool_path)
        cmd = [tool_path]
        if check_only:
            cmd.append("--check")
        cmd.append(abs_target)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return ok(
                tool_used=tool_name,
                stdout=res.stdout,
                stderr=res.stderr,
            )
        if check_only:
            return err(
                "Formatting required",
                status="formatting_required",
                tool_used=tool_name,
                stdout=res.stdout,
                stderr=res.stderr,
            )
        return err(
            res.stderr or res.stdout or "Formatter failed",
            tool_used=tool_name,
            stdout=res.stdout,
            stderr=res.stderr,
        )

    # Builtin Python fallback formatter
    target_files = []
    if os.path.isfile(abs_target) and abs_target.endswith(".gd"):
        target_files.append(abs_target)
    elif os.path.isdir(abs_target):
        for root, _, files in os.walk(abs_target):
            if ".godot" in root:
                continue
            for file in files:
                if file.endswith(".gd"):
                    target_files.append(os.path.join(root, file))

    files_needing_format = []
    formatted_count = 0

    for file_path in target_files:
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            formatted = builtin_format_content(content)
            if content != formatted:
                rel_path = os.path.relpath(file_path, abs_project)
                files_needing_format.append(rel_path)
                if not check_only:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(formatted)
                    formatted_count += 1
        except Exception:
            pass

    if check_only:
        if not files_needing_format:
            return ok(
                message="All files formatted.",
                tool_used="builtin",
                files_needing_format=files_needing_format,
                scanned_files=len(target_files),
            )
        return err(
            f"{len(files_needing_format)} files require formatting.",
            status="formatting_required",
            tool_used="builtin",
            files_needing_format=files_needing_format,
            scanned_files=len(target_files),
        )

    return ok(
        message=f"Formatted {formatted_count} files.",
        tool_used="builtin",
        files_needing_format=files_needing_format,
        scanned_files=len(target_files),
    )


def lint_gdscript(project_path: str, target: str = ".") -> dict[str, Any]:
    """Runs static linting and engine syntax analysis across GDScript files."""
    abs_project = os.path.abspath(project_path)
    if target.startswith("res://"):
        rel_target = target.replace("res://", "")
        abs_target = os.path.join(abs_project, rel_target)
    else:
        abs_target = os.path.abspath(target)
        if not abs_target.startswith(abs_project):
            abs_target = os.path.join(abs_project, target)

    diagnostics = []

    # Step 1: Engine Syntax Check
    syntax_res = check_syntax(abs_project)
    if syntax_res.get("status") == "syntax_errors_found":
        for syntax_err in syntax_res.get("errors", []):
            diagnostics.append(
                {
                    "file": abs_project,
                    "line": 1,
                    "column": 1,
                    "severity": "error",
                    "code": "engine/syntax_error",
                    "message": syntax_err,
                }
            )

    # Step 2: Tool or Builtin Static Linting
    tool_path = _find_linter_tool()
    tool_name = "builtin"
    if tool_path:
        tool_name = os.path.basename(tool_path)
        cmd = [tool_path, abs_target]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            for line in res.stdout.splitlines():
                diagnostics.append(
                    {
                        "file": abs_target,
                        "line": 1,
                        "column": 1,
                        "severity": "warning",
                        "code": f"{tool_name}/lint",
                        "message": line.strip(),
                    }
                )
    else:
        target_files = []
        if os.path.isfile(abs_target) and abs_target.endswith(".gd"):
            target_files.append(abs_target)
        elif os.path.isdir(abs_target):
            for root, _, files in os.walk(abs_target):
                if ".godot" in root:
                    continue
                for file in files:
                    if file.endswith(".gd"):
                        target_files.append(os.path.join(root, file))

        for file_path in target_files:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                rel_path = os.path.relpath(file_path, abs_project)
                file_diags = builtin_lint_content(rel_path, content)
                diagnostics.extend(file_diags)
            except Exception:
                pass

    has_errors = any(d["severity"] == "error" for d in diagnostics)
    payload = {
        "tool_used": tool_name,
        "total_diagnostics": len(diagnostics),
        "diagnostics": diagnostics,
    }
    if has_errors:
        return err(
            "Lint errors found",
            status="lint_errors_found",
            **payload,
        )
    return ok(**payload)
