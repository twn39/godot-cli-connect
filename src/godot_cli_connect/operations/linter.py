"""
GDScript code formatting and static linting module with multi-toolchain support
"""

import os
import re
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from .checker import check_syntax


def _find_formatter_tool() -> Optional[str]:
    for tool in ["gdstyle", "gdformat"]:
        found = shutil.which(tool)
        if found:
            return found
    return None


def _find_linter_tool() -> Optional[str]:
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


def builtin_lint_content(file_path: str, content: str) -> List[Dict[str, Any]]:
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

    for idx, line in enumerate(lines, start=1):
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
) -> Dict[str, Any]:
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
        return {
            "status": "success"
            if res.returncode == 0
            else "formatting_required"
            if check_only
            else "error",
            "tool_used": tool_name,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }

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
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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
        status = "success" if not files_needing_format else "formatting_required"
        message = (
            "All files formatted."
            if not files_needing_format
            else f"{len(files_needing_format)} files require formatting."
        )
    else:
        status = "success"
        message = f"Formatted {formatted_count} files."

    return {
        "status": status,
        "tool_used": "builtin",
        "message": message,
        "files_needing_format": files_needing_format,
        "scanned_files": len(target_files),
    }


def lint_gdscript(project_path: str, target: str = ".") -> Dict[str, Any]:
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
        for err in syntax_res.get("errors", []):
            diagnostics.append(
                {
                    "file": abs_project,
                    "line": 1,
                    "column": 1,
                    "severity": "error",
                    "code": "engine/syntax_error",
                    "message": err,
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
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                rel_path = os.path.relpath(file_path, abs_project)
                file_diags = builtin_lint_content(rel_path, content)
                diagnostics.extend(file_diags)
            except Exception:
                pass

    has_errors = any(d["severity"] == "error" for d in diagnostics)
    status = "lint_errors_found" if has_errors else "success"

    return {
        "status": status,
        "tool_used": tool_name,
        "total_diagnostics": len(diagnostics),
        "diagnostics": diagnostics,
    }
