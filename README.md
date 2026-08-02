# godot-cli-connect

<p align="center">
  <b>A high-performance Python CLI connecting AI Agents with Godot Engine 4.x</b>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python Version"></a>
  <a href="https://godotengine.org"><img src="https://img.shields.io/badge/godot-4.x-blueviolet.svg" alt="Godot Engine"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/managed%20by-uv-de5b43.svg" alt="uv"></a>
  <a href="https://git-lfs.github.com"><img src="https://img.shields.io/badge/Git%20LFS-enabled-brightgreen.svg" alt="Git LFS"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

---

`godot-cli-connect` (or `godot-cli`) bridges LLM AI Agents (Claude Code, Antigravity, Cursor, Grok, Codex) and human developers with the **Godot Engine 4.x** runtime. It provides machine-readable CLI commands, robust text-based offline parsing fallbacks, GDScript 2.0 linting, visual testing, and AI-powered background removal.

## 🚀 Key Features

* **Dual-Mode Execution Architecture**:
  - **Engine Mode**: Invokes headless Godot binary for exact runtime execution, scene instantiation, and API reflection.
  - **Offline Fallback**: Direct text-based AST manipulation for `.tscn`, `.gd`, and `project.godot` files when Godot binary is absent.
* **AI Background Removal (BiRefNet_lite ONNX)**:
  - Built-in 109MB ONNX model managed via **Git LFS** and bundled directly inside Python Wheel packages.
  - Advanced fringe optimization: **Alpha Erosion** (`--erode`) and **Color Decontamination** (`--decontaminate`) to eliminate edge white halos on game sprites.
* **Machine-Readable Agent Contract**:
  - All commands support `--json` output formatted for reliable LLM tool-calling parsing.
* **Full Godot 4.x Tooling Ecosystem**:
  - Project management, scene graph editing, signal wiring, GDScript 2.0 linting/formatting, GUT unit test runner, visual screenshot diffing, and API documentation search.

---

## 📊 Command Matrix

| Category | Commands | Description |
|---|---|---|
| **Project & Media** | `info`, `tools-list`, `init-project`, `inspect`, `export`, `export-presets`, `logs`, `reimport` | Project management, asset reimporting, and export pipelines. |
| **Quality & Lint** | `check`, `format`, `lint` | GDScript 2.0 syntax checks, ruff formatting, and deprecation linting. |
| **Scene Graph** | `create-scene`, `add-node`, `edit-node`, `remove-node`, `rename-node`, `reparent-node`, `inspect-scene`, `inspect-signals`, `bind-signal`, `disconnect-signal`, `attach-script` | Full TSCN scene structure modification and signal binding. |
| **Scripting & Test** | `script-create`, `script-write`, `script-read`, `eval`, `run-test`, `test-gut` | GDScript CRUD, dynamic evaluation, and GUT test suite execution. |
| **Assets & ML** | `remove-bg` / `bg-remove`, `screenshot`, `screenshot-diff`, `create-resource`, `dump-api`, `class-info`, `docs-search` | AI background removal, screenshot capture/diffing, and Godot API inspection. |
| **Config & Autoload**| `config-get`, `config-set`, `config-resolution`, `input-add`, `autoload-add`, `autoload-remove`, `autoload-list` | `project.godot` settings, input map management, and singleton autoloads. |

---

## 📦 Installation & Setup

### Requirements
- Python `>= 3.12`
- [uv](https://github.com/astral-sh/uv) (recommended)
- [Git LFS](https://git-lfs.github.com) (for ONNX model tracking)
- Godot Engine `4.x` (optional, required for engine-mode execution)

### Install via uv

```bash
# Clone repository
git clone https://github.com/twn39/godot-cli-connect.git
cd godot-cli-connect

# Pull Git LFS model files
git lfs pull

# Synchronize dependencies
uv sync
```

### Global Editable Install

```bash
uv pip install -e .
```

### Environment Variables

```bash
# Set path to your Godot 4.x binary (if not on system PATH)
export GODOT_PATH="/Applications/Godot.app/Contents/MacOS/Godot"

# Subprocess timeout in seconds (default: 30)
export GODOT_CLI_TIMEOUT=60

# Optional custom BiRefNet ONNX model path
export BIREFNET_MODEL="/path/to/custom_model.onnx"
```

---

## 🤖 Agent Result Contract (JSON Interface)

Every command accepts `--json` for machine-readable tool invocation.

### Success Response

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "mode": "engine",
  "output_path": "res://scenes/player.tscn"
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Detailed description of error",
  "errors": ["Optional list of sub-errors"]
}
```

Python helpers available via `godot_cli_connect.models`: `ok()`, `err()`, `is_success()`, and `OperationResult`.

---

## 📖 Command Examples

### 1. Environment & Project Management

```bash
# Inspect environment & detected Godot binary
uv run godot-cli info --json

# Initialize a new Godot 4 project
uv run godot-cli init-project ./my_game --name "My Game"

# Reimport assets and fix invalid .import files
uv run godot-cli reimport --project ./my_game --clean
```

### 2. Scene Graph Modification (Offline & Engine Dual-Mode)

```bash
# Create 2D Character Scene
uv run godot-cli create-scene res://scenes/player.tscn --root CharacterBody2D --project .

# Add Sprite2D node with properties
uv run godot-cli add-node res://scenes/player.tscn --name Sprite --type Sprite2D --properties '{"visible":true}' --project .

# Connect signal
uv run godot-cli bind-signal res://scenes/ui.tscn --from Button --signal pressed --to . --method _on_pressed --project .
```

### 3. AI Background Removal (BiRefNet ONNX)

Remove background from game assets into transparent RGBA PNGs:

```bash
# Single image with fringe optimization (1px alpha erosion + color decontamination)
uv run godot-cli remove-bg ./hero.png -o ./hero_nobg.png -e 1 -d

# Batch process an entire directory of assets
uv run godot-cli remove-bg ./raw_assets/ -o ./sprites_nobg/ -e 1 -d

# Hard alpha thresholding
uv run godot-cli remove-bg ./item.png -t 0.5
```

### 4. Code Quality & Linting

```bash
# GDScript 2.0 linting (detects Godot 4 deprecations & invalid types)
uv run godot-cli lint . --project . --json

# Format GDScript files
uv run godot-cli format . --project .
```

### 5. Visual Testing & GUT

```bash
# Render scene screenshot
uv run godot-cli screenshot --project . --scene res://levels/level1.tscn --output level1.png

# Compare screenshot with baseline
uv run godot-cli screenshot-diff --baseline baseline.png --current level1.png --threshold 0.05

# Run GUT unit tests
uv run godot-cli test-gut --dir res://test --project .
```

---

## 🛠️ Development & Testing

```bash
# Install development dependencies
uv sync --group dev

# Run unit tests
uv run pytest

# Code linting
uv run ruff check .

# Rebuild codebase knowledge graph (for AI agents)
codegraph build . -e demo -e .pytest_cache -e .ruff_cache
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
