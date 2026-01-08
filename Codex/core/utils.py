"""Cross-cutting utilities for CommandCoreCodex."""

from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory for the Codex package."""
    return Path(__file__).resolve().parents[1]
