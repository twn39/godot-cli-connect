# godot-cli-connect

A high-performance Python CLI built with **Typer** and managed by **uv**, enabling AI Agents (Claude Code, Codex, Antigravity, Grok) to interact with **Godot Engine 4.x** headlessly.

## Features

| Area | Commands |
|---|---|
| Project | `info`, `tools-list`, `init-project`, `inspect`, `export`, `export-presets`, `logs`, `reimport` / `import-assets` |
| Quality | `check`, `format`, `lint` |
| Scenes | `create-scene`, `add-node`, `edit-node`, `remove-node`, `rename-node`, `reparent-node`, `inspect-scene`, `inspect-signals`, `bind-signal`, `disconnect-signal`, `attach-script` |
| Scripts | `script-create`, `script-write`, `script-read`, `eval`, `run-test`, `test-gut` |
| Assets / API | `create-resource`, `screenshot` (`--scene`), `screenshot-diff`, `remove-bg` / `bg-remove`, `dump-api`, `class-info`, `docs-search` |
| Config | `config-get`, `config-set`, `input-add`, `autoload-add`, `autoload-remove`, `autoload-list` |

Most commands accept **`--json`** for machine-readable output (preferred by LLM tool callers).

Many scene/config operations use a **dual mode** strategy:

1. **engine** — headless Godot process when a binary is available  
2. **offline** — text-based `.tscn` / `project.godot` fallback when Godot is missing  

Successful JSON payloads often include `"mode": "engine" | "offline"`.

## Installation & Setup

```bash
cd /path/to/godot-cli-connect
uv sync
```

Optional global editable install:

```bash
uv pip install -e .
```

Set the Godot binary if it is not on `PATH`:

```bash
export GODOT_PATH="/Applications/Godot.app/Contents/MacOS/Godot"
# optional: subprocess timeout seconds (default 30)
export GODOT_CLI_TIMEOUT=60
```

## Agent result contract

Operations return a **flat JSON object**:

```json
{
  "status": "success",
  "message": "optional human summary",
  "mode": "engine",
  "...": "command-specific fields"
}
```

On failure:

```json
{
  "status": "error",
  "message": "what went wrong",
  "errors": ["optional list"]
}
```

Python helpers: `godot_cli_connect.models.ok`, `err`, `is_success`, `OperationResult`.

Non-zero process exit code is used when a command fails (and for `--json` when `status != success`, except a few diagnostic commands that always print JSON first).

## Command reference

Run `uv run godot-cli --help` or `uv run godot-cli <command> --help` for full flags.

### Environment & project

```bash
uv run godot-cli info --json
uv run godot-cli tools-list --json
uv run godot-cli init-project ./my_game --name "My Game"
uv run godot-cli inspect --project /path/to/project --json
uv run godot-cli export-presets --project /path/to/project --json
uv run godot-cli export "Mac OSX" ./build/game.app --project /path/to/project
uv run godot-cli logs --project /path/to/project --lines 50
uv run godot-cli reimport --project /path/to/project
```

### Quality

```bash
uv run godot-cli check --project /path/to/project --json
uv run godot-cli format . --project /path/to/project
uv run godot-cli lint . --project /path/to/project --json
```

### Scenes (offline-capable)

```bash
uv run godot-cli create-scene res://scenes/player.tscn --root CharacterBody2D --project .
uv run godot-cli add-node res://scenes/player.tscn --name Sprite --type Sprite2D --properties '{"visible":true}' --project .
uv run godot-cli edit-node res://scenes/player.tscn --node Sprite --properties '{"modulate":"Color(1,0,0,1)"}' --project .
uv run godot-cli remove-node res://scenes/player.tscn --node Sprite --project .
uv run godot-cli rename-node res://scenes/player.tscn --node Sprite --new-name Icon --project .
uv run godot-cli reparent-node res://scenes/player.tscn --node Icon --new-parent Player --project .
uv run godot-cli bind-signal res://ui.tscn --from Button --signal pressed --to . --method _on_pressed --project .
uv run godot-cli attach-script res://scenes/player.tscn --script res://scripts/player.gd --node . --project .
uv run godot-cli inspect-scene res://main.tscn --project . --json
uv run godot-cli inspect-signals res://main.tscn --project . --json
```

### Scripts (filesystem, offline)

```bash
uv run godot-cli script-create res://scripts/player.gd --extends CharacterBody2D --class-name Player --project .
uv run godot-cli script-write res://scripts/player.gd --content 'extends Node\nfunc _ready():\n\tpass\n' --project .
uv run godot-cli script-read res://scripts/player.gd --project . --json
```

### Scripting, API, screenshots

```bash
uv run godot-cli eval "1+1" --project . --json
uv run godot-cli run-test res://tests/test_game.gd --project .
uv run godot-cli test-gut --dir res://test --project .
uv run godot-cli dump-api --output godot_api.json
uv run godot-cli class-info CharacterBody2D --json
uv run godot-cli docs-search TileMap --limit 5 --json
uv run godot-cli screenshot --project . --output preview.png
uv run godot-cli screenshot --project . --scene res://levels/level1.tscn --output level1.png
uv run godot-cli screenshot-diff --baseline a.png --current b.png --threshold 0.05
```

### Background removal (BiRefNet_lite ONNX)

Place the model at project root as `BiRefNet_lite_fp16.onnx` (or set `BIREFNET_MODEL` / `--model`).

```bash
# Single image → transparent PNG for Godot sprites
uv run godot-cli remove-bg ./sprite.png -o ./sprite_nobg.png
uv run godot-cli remove-bg ./sprite.png --mask --json

# Batch a folder of assets
uv run godot-cli remove-bg ./raw_assets -o ./sprites_nobg

# Custom model path
uv run godot-cli remove-bg ./hero.jpg -m ./BiRefNet_lite_fp16.onnx -t 0.5
```

Uses **onnxruntime** + **OpenCV** (ImageNet preprocess, 1024×1024, soft alpha matte).

### Config & Autoload

```bash
uv run godot-cli config-get application/config/name --project . --json
uv run godot-cli config-set application/config/name "My Game" --project .
uv run godot-cli input-add jump --key KEY_SPACE --project .
uv run godot-cli autoload-add GameState res://autoload/game_state.gd --project .
uv run godot-cli autoload-list --project . --json
uv run godot-cli autoload-remove GameState --project .
```

## Development

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check src tests
```

Knowledge graph (for agents):

```bash
codegraph build . -e demo -e .pytest_cache -e .ruff_cache
```

See [`.codegraph/README.md`](.codegraph/README.md) for architecture notes.
