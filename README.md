# godot-cli-connect

A high-performance Python CLI tool built with **Typer** and managed by **uv**, enabling AI Agents (Claude Code, Codex, Antigravity) to interact seamlessly with **Godot Engine 4.x**.

## Features

- 📸 **`godot-cli screenshot`**: Render and capture offscreen/background screenshots of Godot scenes.
- 🔍 **`godot-cli check`**: Rapid GDScript syntax and compile error checking.
- 📊 **`godot-cli inspect`**: Extract Godot project metadata, configuration, and script/scene stats.
- 📦 **`godot-cli export`**: Headless export build runner for defined export presets.
- 📜 **`godot-cli logs`**: Retrieve and analyze engine and runtime execution logs.
- 🧪 **`godot-cli run-test`**: Run unit test GDScripts in headless mode and capture execution logs.
- 🛠️ **`godot-cli create-resource`**: Instantiate Godot resources, set properties via JSON, and save `.tres`.
- 🔄 **`godot-cli reimport`**: Force Godot engine to rescan and reimport project assets.
- 📄 **`godot-cli dump-api`**: Export complete Godot 4 Extension API JSON for AI Agents to inspect engine APIs.
- 🤖 **`--json` Flag**: Formats output as structured JSON for easy parsing by LLM tool callers.

## Installation & Setup

Managed with **[uv](https://github.com/astral-sh/uv)**:

```bash
cd /Users/2342184/programs/godot-cli-connect
uv sync
```

Or install globally into your environment:

```bash
uv pip install -e .
```

## Command Usage Examples

### 1. Inspect Godot Project Metadata
```bash
uv run godot-cli inspect --project /path/to/godot/project
```

### 2. Check GDScript Syntax Errors
```bash
uv run godot-cli check --project /path/to/godot/project --json
```

### 3. Capture Offscreen Frame Screenshot
```bash
uv run godot-cli screenshot --project /path/to/godot/project --output preview.png
```

### 4. Read Engine Log Output
```bash
uv run godot-cli logs --project /path/to/godot/project --lines 50
```

### 5. Export Build
```bash
uv run godot-cli export "Mac OSX" ./build/my_game.app --project /path/to/godot/project
```

### 6. Run Headless Test Script
```bash
uv run godot-cli run-test res://tests/test_game.gd --project /path/to/godot/project
```

### 7. Dump Extension API JSON
```bash
uv run godot-cli dump-api --output godot_api.json
```
