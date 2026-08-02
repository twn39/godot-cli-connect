"""CLI command registration package."""

from __future__ import annotations

import typer

from . import media, meta, project, quality, scene, scripts


def register_all(app: typer.Typer) -> None:
    """Register all command groups on the root Typer application."""
    meta.register(app)
    project.register(app)
    scene.register(app)
    scripts.register(app)
    quality.register(app)
    media.register(app)
