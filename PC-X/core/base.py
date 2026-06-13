"""Shared base helpers for PC-X."""

from pathlib import Path
from typing import Tuple


def get_paths() -> Tuple[Path, Path]:
    """Return repository root and PC-X directory paths."""
    pcx_dir = Path(__file__).resolve().parents[1]
    root_dir = pcx_dir.parent
    return root_dir, pcx_dir


def ensure_logs_dir(root_dir: Path) -> Path:
    """Ensure the logs directory exists and return its path.

    When installed system-wide (root_dir not writable), falls back to
    ~/.local/share/pc-x/logs so the app can run without root privileges.
    """
    candidate = root_dir / "logs"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except PermissionError:
        fallback = Path.home() / ".local" / "share" / "pc-x" / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
