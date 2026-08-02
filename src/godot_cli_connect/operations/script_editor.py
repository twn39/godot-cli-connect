"""
GDScript file create / write / read helpers (filesystem-level, offline-friendly).
"""

from __future__ import annotations

import os
from typing import Any

from ..models import err, ok
from .paths import resolve_res_path
from .scene_editor import attach_script

DEFAULT_SCRIPT_TEMPLATE = """extends {extends}

# {title}


func _ready() -> void:
	pass


func _process(_delta: float) -> void:
	pass
"""


def create_script(
    project_path: str,
    script_path: str,
    *,
    extends: str = "Node",
    class_name: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a new GDScript file with a standard template."""
    abs_project, abs_script, res_path = resolve_res_path(project_path, script_path)
    if not res_path.endswith(".gd"):
        # allow user to omit extension
        abs_script = abs_script + ".gd"
        res_path = res_path + ".gd"

    if os.path.exists(abs_script) and not overwrite:
        return err(f"Script already exists: {res_path}", path=res_path)

    title = os.path.basename(abs_script)
    body = DEFAULT_SCRIPT_TEMPLATE.format(extends=extends, title=title)
    if class_name:
        # Godot 4 class_name goes after extends
        body = body.replace(
            f"extends {extends}\n",
            f"extends {extends}\nclass_name {class_name}\n",
            1,
        )

    try:
        os.makedirs(os.path.dirname(abs_script) or ".", exist_ok=True)
        with open(abs_script, "w", encoding="utf-8") as f:
            f.write(body)
        return ok(
            mode="offline",
            path=res_path,
            abs_path=abs_script,
            extends=extends,
            class_name=class_name,
            message=f"Created script {res_path}",
        )
    except Exception as e:
        return err(str(e))


def write_script(
    project_path: str,
    script_path: str,
    content: str,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Write full content to a GDScript file (create parent dirs as needed)."""
    abs_project, abs_script, res_path = resolve_res_path(project_path, script_path)
    if not res_path.endswith(".gd") and not abs_script.endswith(".gd"):
        abs_script = abs_script + ".gd"
        res_path = res_path + ".gd"

    if os.path.exists(abs_script) and not overwrite:
        return err(f"Script already exists: {res_path}", path=res_path)

    try:
        os.makedirs(os.path.dirname(abs_script) or ".", exist_ok=True)
        with open(abs_script, "w", encoding="utf-8") as f:
            f.write(content if content.endswith("\n") else content + "\n")
        return ok(
            mode="offline",
            path=res_path,
            abs_path=abs_script,
            bytes_written=len(content.encode("utf-8")),
            message=f"Wrote script {res_path}",
        )
    except Exception as e:
        return err(str(e))


def read_script(project_path: str, script_path: str) -> dict[str, Any]:
    """Read a GDScript file content."""
    _, abs_script, res_path = resolve_res_path(project_path, script_path)
    if not os.path.exists(abs_script) and not abs_script.endswith(".gd"):
        if os.path.exists(abs_script + ".gd"):
            abs_script = abs_script + ".gd"
            res_path = res_path + ".gd"
    if not os.path.exists(abs_script):
        return err(f"Script not found: {res_path}", path=res_path)
    try:
        with open(abs_script, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return ok(
            mode="offline",
            path=res_path,
            abs_path=abs_script,
            content=content,
            lines=content.count("\n") + (0 if content.endswith("\n") else 1),
        )
    except Exception as e:
        return err(str(e))


def attach_script_to_node(
    project_path: str,
    scene_path: str,
    node_path: str,
    script_path: str,
    *,
    mode: str = "auto",
) -> dict[str, Any]:
    """Attach an existing script file to a scene node."""
    return attach_script(
        project_path,
        scene_path,
        node_path,
        script_path,
        mode=mode,  # type: ignore[arg-type]
    )
