"""
Godot 4 official documentation search and GDScript code example retrieval module
"""

import os
import re
import json
from typing import Dict, Any, List
from .class_info import get_class_info

# Preset GDScript usage code snippets for common Godot 4 nodes
COMMON_NODE_SNIPPETS: Dict[str, str] = {
    "CharacterBody2D": """extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity += get_gravity() * delta

    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    var direction := Input.get_axis("ui_left", "ui_right")
    if direction:
        velocity.x = direction * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)

    move_and_slide()""",
    "Area2D": """extends Area2D

func _ready() -> void:
    body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        print("Player entered area!")""",
    "RayCast2D": """extends RayCast2D

func _process(_delta: float) -> void:
    if is_colliding():
        var collider = get_collider()
        var point = get_collision_point()
        print("Hit: ", collider.name, " at ", point)""",
    "Node2D": """extends Node2D

func _ready() -> void:
    position = Vector2(100, 200)
    rotation_degrees = 45.0""",
    "Control": """extends Control

func _ready() -> void:
    custom_minimum_size = Vector2(200, 100)""",
}


def clean_bbcode(text: str) -> str:
    """Removes or converts BBCode tags like [code], [b], [param] from Godot docstrings."""
    if not text:
        return ""
    text = re.sub(r"\[code\](.*?)\[/code\]", r"`\1`", text)
    text = re.sub(r"\[b\](.*?)\[/b\]", r"**\1**", text)
    text = re.sub(r"\[i\](.*?)\[/i\]", r"*\1*", text)
    text = re.sub(r"\[param (.*?)\]", r"`\1`", text)
    text = re.sub(r"\[method (.*?)\]", r"`\1()`", text)
    text = re.sub(r"\[member (.*?)\]", r"`\1`", text)
    text = re.sub(r"\[signal (.*?)\]", r"`\1`", text)
    text = re.sub(r"\[enum (.*?)\]", r"`\1`", text)
    text = re.sub(r"\[/?[a-zA-Z0-9_=]+\]", "", text)
    return text.strip()


def search_docs(query: str, project_path: str = ".", limit: int = 5) -> Dict[str, Any]:
    """
    Searches Godot 4 official class documentation and retrieves GDScript code examples.
    """
    query_clean = query.strip().lower()
    abs_project = os.path.abspath(project_path)
    api_json_path = os.path.join(abs_project, "extension_api.json")

    results: List[Dict[str, Any]] = []

    # 1. Try local extension_api.json if present
    if os.path.exists(api_json_path):
        try:
            with open(api_json_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            for c in data.get("classes", []):
                name = c.get("name", "")
                inherits = c.get("inherits", "Object")
                brief_desc = clean_bbcode(c.get("brief_description", ""))
                desc = clean_bbcode(c.get("description", ""))

                match_score = 0
                if query_clean == name.lower():
                    match_score += 100
                elif query_clean in name.lower():
                    match_score += 50
                elif query_clean in brief_desc.lower() or query_clean in desc.lower():
                    match_score += 20

                if match_score > 0:
                    methods = [
                        m.get("name")
                        for m in c.get("methods", [])
                        if not m.get("name", "").startswith("_")
                    ][:10]
                    signals_list = [s.get("name") for s in c.get("signals", [])][:5]

                    snippet = COMMON_NODE_SNIPPETS.get(name)

                    results.append(
                        {
                            "score": match_score,
                            "name": name,
                            "inherits": inherits,
                            "brief_description": brief_desc or f"Godot 4 {name} Class",
                            "docs_url": f"https://docs.godotengine.org/en/stable/classes/class_{name.lower()}.html",
                            "key_methods": methods,
                            "signals": signals_list,
                            "code_example": snippet,
                        }
                    )
        except Exception:
            pass

    # 2. Fallback to ClassDB targeted lookup if no cache results found
    if not results:
        exact_info = get_class_info(query, project_path=abs_project)
        if exact_info.get("status") == "success":
            c_info = exact_info.get("class_info", {})
            c_name = c_info.get("name", query)
            snippet = COMMON_NODE_SNIPPETS.get(c_name)

            results.append(
                {
                    "score": 100,
                    "name": c_name,
                    "inherits": c_info.get("inherits", "Object"),
                    "brief_description": f"Godot 4 {c_name} Class",
                    "docs_url": c_info.get(
                        "docs_url",
                        f"https://docs.godotengine.org/en/stable/classes/class_{c_name.lower()}.html",
                    ),
                    "key_methods": [m["name"] for m in c_info.get("methods", [])[:10]],
                    "signals": [s["name"] for s in c_info.get("signals", [])[:5]],
                    "code_example": snippet,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    final_results = results[:limit]

    return {
        "status": "success" if final_results else "not_found",
        "query": query,
        "total": len(final_results),
        "results": final_results,
    }
