"""
Shared low-level helpers for Godot 4 .tscn text parsing and mutation.

Used by both offline mutators (``scene_tscn``) and static inspectors
(``scene_inspector``) so section/attribute handling stays consistent.
"""

from __future__ import annotations

import re
from typing import Any

# Section header: [node name="X" type="Y"] etc.
SECTION_RE = re.compile(r"^\[([a-zA-Z0-9_]+)\s*(.*)\]$")
# Attribute pairs on section headers.
ATTR_RE = re.compile(r'([a-zA-Z0-9_]+)\s*=\s*("(?:[^"\\]|\\.)*"|\S+)')
NODE_NAME_RE = re.compile(r'name="([^"]+)"')
NODE_PARENT_RE = re.compile(r'parent="([^"]+)"')


def parse_section_attrs(attr_str: str) -> dict[str, str]:
    """Parse ``key=value`` pairs from a .tscn section header attribute string."""
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(attr_str):
        key = match.group(1)
        val = match.group(2).strip('"')
        attrs[key] = val
    return attrs


def node_header_name(line: str) -> str | None:
    """Extract ``name="..."`` from a ``[node ...]`` header line."""
    match = NODE_NAME_RE.search(line)
    return match.group(1) if match else None


def node_header_parent(line: str) -> str | None:
    """Extract ``parent="..."`` from a ``[node ...]`` header line."""
    match = NODE_PARENT_RE.search(line)
    return match.group(1) if match else None


def split_node_blocks(lines: list[str]) -> list[tuple[int, int, str | None]]:
    """
    Return list of ``(start_idx, end_idx_exclusive, node_name)`` for each ``[node]`` block.

    Non-node preamble is not included.
    """
    blocks: list[tuple[int, int, str | None]] = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith("[node "):
            name = node_header_name(lines[i])
            start = i
            i += 1
            while i < n and not lines[i].lstrip().startswith("["):
                i += 1
            blocks.append((start, i, name))
        else:
            i += 1
    return blocks


def is_section_line(line: str) -> bool:
    """True when ``line`` is a Godot text-resource section header."""
    return bool(SECTION_RE.match(line.strip()))


def parse_groups_attr(attr_str: str) -> list[str]:
    """Parse optional ``groups=[...]`` from a node header attribute string."""
    groups_match = re.search(r"groups\s*=\s*\[(.*?)\]", attr_str)
    if not groups_match:
        return []
    raw_groups = groups_match.group(1)
    return [g.strip(' "') for g in raw_groups.split(",") if g.strip()]


def empty_node_shell(attrs: dict[str, str]) -> dict[str, Any]:
    """Build a standard node dict used by static scene inspectors."""
    return {
        "name": attrs.get("name", "Node"),
        "type": attrs.get("type", "Node"),
        "parent": attrs.get("parent"),
        "instance_id": attrs.get("instance"),
        "script_path": None,
        "groups": [],
        "properties": {},
        "children": [],
        "connections": [],
    }
