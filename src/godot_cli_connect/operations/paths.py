"""
Path helpers for Godot project / res:// resource resolution.
"""

from __future__ import annotations

import os


def resolve_res_path(project_path: str, resource_path: str) -> tuple[str, str, str]:
    """
    Resolve a project-relative, absolute, or res:// path.

    Returns:
        (abs_project, abs_resource_path, res_path)
        where res_path is always of the form ``res://...``.
    """
    abs_project = os.path.abspath(project_path)

    if resource_path.startswith("res://"):
        rel_path = resource_path[6:]
        abs_resource = os.path.join(abs_project, rel_path)
        res_path = resource_path
    elif os.path.isabs(resource_path):
        abs_resource = os.path.abspath(resource_path)
        try:
            res_path = f"res://{os.path.relpath(abs_resource, abs_project)}"
        except ValueError:
            res_path = f"res://{os.path.basename(abs_resource)}"
    else:
        abs_resource = os.path.abspath(os.path.join(abs_project, resource_path))
        res_path = f"res://{os.path.relpath(abs_resource, abs_project)}"

    return abs_project, abs_resource, res_path
