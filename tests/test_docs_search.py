"""
Unit and integration tests for docs_search module and docs-search CLI command
"""

import json
from typer.testing import CliRunner
from godot_cli_connect.operations.docs_search import clean_bbcode, search_docs
from godot_cli_connect.cli import app

runner = CliRunner()


def test_clean_bbcode():
    raw = "This is [b]bold[/b] and [code]move_and_slide()[/code] with [param delta]."
    cleaned = clean_bbcode(raw)
    assert "**bold**" in cleaned
    assert "`move_and_slide()`" in cleaned
    assert "`delta`" in cleaned


def test_search_docs_fallback(tmp_path):
    res = search_docs("CharacterBody2D", project_path=str(tmp_path))
    assert res["status"] == "success"
    assert res["total"] > 0
    first = res["results"][0]
    assert first["name"] == "CharacterBody2D"
    assert first["code_example"] is not None
    assert "move_and_slide" in first["code_example"]


def test_search_docs_json_api(tmp_path):
    api_json = tmp_path / "extension_api.json"
    fake_api = {
        "classes": [
            {
                "name": "Area2D",
                "inherits": "CollisionObject2D",
                "brief_description": "2D Area for [b]collisions[/b].",
                "description": "Area2D node detects collisions.",
                "methods": [{"name": "get_overlapping_bodies"}],
                "signals": [{"name": "body_entered"}],
            }
        ]
    }
    api_json.write_text(json.dumps(fake_api))

    res = search_docs("Area2D", project_path=str(tmp_path))
    assert res["status"] == "success"
    assert res["results"][0]["name"] == "Area2D"
    assert "**collisions**" in res["results"][0]["brief_description"]


def test_cli_docs_search(tmp_path):
    res = runner.invoke(
        app, ["docs-search", "CharacterBody2D", "-p", str(tmp_path), "--json"]
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"name": "CharacterBody2D"' in res.stdout
