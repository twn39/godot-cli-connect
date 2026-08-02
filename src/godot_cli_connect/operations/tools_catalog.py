"""
Machine-readable catalog of CLI tools for LLM / MCP agents.
"""

from __future__ import annotations

from typing import Any

from ..models import ok

# Flat agent result envelope (canonical JSON contract).
RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["status"],
    "properties": {
        "status": {
            "type": "string",
            "description": (
                "success on ok; error / failure / syntax_errors_found / "
                "tests_failed / lint_errors_found / formatting_required / "
                "diff_detected / not_found on failure paths"
            ),
        },
        "message": {"type": "string"},
        "errors": {"type": "array", "items": {"type": "string"}},
        "mode": {
            "type": "string",
            "description": "engine|offline|static|cache|debug|release when applicable",
        },
    },
    "additionalProperties": True,
}

# CLI command aliases that map to a primary catalog tool name.
CLI_ALIASES: dict[str, str] = {
    "bg-remove": "remove-bg",
    "import-assets": "reimport",
}

# Keep in sync with Typer command surface (validated by tests + catalog_alignment).
TOOLS: list[dict[str, Any]] = [
    {
        "name": "info",
        "summary": "Detect Godot binary path, version, and capabilities",
        "json": True,
        "needs_project": False,
        "needs_godot": False,
        "offline_ok": True,
    },
    {
        "name": "tools-list",
        "summary": "List all CLI tools with agent-oriented metadata",
        "json": True,
        "needs_project": False,
        "needs_godot": False,
        "offline_ok": True,
    },
    {
        "name": "init-project",
        "summary": "Create a new Godot 4 project directory",
        "json": True,
        "needs_project": False,
        "needs_godot": False,
        "offline_ok": True,
    },
    {
        "name": "inspect",
        "summary": "Inspect project.godot metadata and asset stats",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "check",
        "summary": "GDScript syntax / compile check via headless Godot",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
        "offline_ok": False,
    },
    {
        "name": "format",
        "summary": "Format GDScript (gdformat or builtin fallback)",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "lint",
        "summary": "Lint GDScript (gdlint or builtin fallback)",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "create-scene",
        "summary": "Create a .tscn with root node (engine or offline)",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
        "modes": ["engine", "offline"],
    },
    {
        "name": "add-node",
        "summary": "Add a child node to a scene",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
        "modes": ["engine", "offline"],
    },
    {
        "name": "edit-node",
        "summary": "Set properties on a scene node",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
        "modes": ["engine", "offline"],
    },
    {
        "name": "remove-node",
        "summary": "Remove a node from a scene",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
        "modes": ["engine", "offline"],
    },
    {
        "name": "rename-node",
        "summary": "Rename a node with cascading path updates",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "reparent-node",
        "summary": "Move a node under a new parent",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "bind-signal",
        "summary": "Connect a signal between nodes",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "disconnect-signal",
        "summary": "Disconnect a signal",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "inspect-scene",
        "summary": "Inspect scene tree (static or --engine runtime)",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "inspect-signals",
        "summary": "List signal connections in a .tscn",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "script-create",
        "summary": "Create a GDScript file from template",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "script-write",
        "summary": "Write full content to a GDScript file",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "script-read",
        "summary": "Read a GDScript file",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "attach-script",
        "summary": "Attach a script resource to a scene node",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
        "modes": ["engine", "offline"],
    },
    {
        "name": "config-get",
        "summary": "Read a project.godot setting",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "config-set",
        "summary": "Set a project.godot setting",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "input-add",
        "summary": "Add InputMap action key binding",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "autoload-add",
        "summary": "Register an Autoload singleton",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "autoload-remove",
        "summary": "Remove an Autoload singleton",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "autoload-list",
        "summary": "List Autoload singletons",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "export",
        "summary": "Headless export with a named preset",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
        "offline_ok": False,
    },
    {
        "name": "export-presets",
        "summary": "List export presets from export_presets.cfg",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "logs",
        "summary": "Read recent Godot user-data logs",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "screenshot",
        "summary": "Capture PNG of main scene or --scene",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
        "offline_ok": False,
    },
    {
        "name": "screenshot-diff",
        "summary": "Compare two screenshots with threshold",
        "json": True,
        "needs_project": False,
        "offline_ok": True,
    },
    {
        "name": "run-test",
        "summary": "Run a headless GDScript test file",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
    },
    {
        "name": "test-gut",
        "summary": "Run GUT test suite and parse metrics",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
    },
    {
        "name": "eval",
        "summary": "Evaluate GDScript snippet or REPL",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
    },
    {
        "name": "dump-api",
        "summary": "Dump Godot Extension API JSON",
        "json": True,
        "needs_godot": True,
    },
    {
        "name": "class-info",
        "summary": "ClassDB reflection for a class name",
        "json": True,
        "needs_project": True,
    },
    {
        "name": "docs-search",
        "summary": "Search class docs / code snippets",
        "json": True,
        "needs_project": True,
        "offline_ok": True,
    },
    {
        "name": "create-resource",
        "summary": "Instantiate and save a Resource (.tres)",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
    },
    {
        "name": "reimport",
        "summary": "Force asset reimport scan",
        "json": True,
        "needs_project": True,
        "needs_godot": True,
    },
    {
        "name": "remove-bg",
        "summary": "Remove image background (BiRefNet_lite ONNX + OpenCV) for game sprites",
        "json": True,
        "needs_project": False,
        "needs_godot": False,
        "offline_ok": True,
        "requires_model": "BiRefNet_lite_fp16.onnx",
    },
]


def catalog_tool_names() -> set[str]:
    """Primary tool names declared in the static catalog."""
    return {t["name"] for t in TOOLS}


def cli_registered_command_names() -> set[str]:
    """Command names currently registered on the Typer app (including aliases)."""
    from ..cli import app

    return {cmd.name for cmd in app.registered_commands if cmd.name}


def catalog_alignment() -> dict[str, Any]:
    """
    Compare TOOLS catalog to live Typer commands.

    Catalog entries are primary names; CLI may also expose aliases listed in
    ``CLI_ALIASES``. Returns missing/extra sets for tests and diagnostics.
    """
    catalog = catalog_tool_names()
    cli_names = cli_registered_command_names()
    # Expand catalog with known aliases for comparison against CLI.
    catalog_with_aliases = set(catalog) | set(CLI_ALIASES)
    # Map CLI aliases back: every CLI name should be a catalog name or alias key.
    primary_from_cli = {CLI_ALIASES.get(name, name) for name in cli_names}

    missing_in_cli = sorted(catalog - cli_names)
    extra_in_cli = sorted(cli_names - catalog_with_aliases)
    missing_in_catalog = sorted(primary_from_cli - catalog)
    aligned = not missing_in_cli and not extra_in_cli and not missing_in_catalog
    return {
        "aligned": aligned,
        "catalog_count": len(catalog),
        "cli_count": len(cli_names),
        "missing_in_cli": missing_in_cli,
        "extra_in_cli": extra_in_cli,
        "missing_in_catalog": missing_in_catalog,
        "aliases": dict(CLI_ALIASES),
    }


def list_tools() -> dict[str, Any]:
    """Return the agent tool catalog plus result schema and alignment status."""
    alignment = catalog_alignment()
    return ok(
        tool_count=len(TOOLS),
        tools=TOOLS,
        aliases=dict(CLI_ALIASES),
        result_contract={
            "success": {"status": "success", "optional": ["message", "mode", "..."]},
            "error": {
                "status": "error|failure|…",
                "message": "string",
                "optional": ["errors"],
            },
            "schema": RESULT_SCHEMA,
        },
        catalog_alignment=alignment,
        notes=[
            "Prefer --json on every command for machine parsing.",
            "Scene and config ops often support offline mode without a Godot binary.",
            "mode field: engine|offline for dual-mode ops; export uses debug|release.",
            "Public operations return flat dicts via ok()/err() (see result_contract.schema).",
        ],
    )
