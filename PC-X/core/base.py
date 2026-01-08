"""Shared base helpers for PC-X."""

from pathlib import Path
from typing import Tuple


def get_paths() -> Tuple[Path, Path]:
    """Return repository root and PC-X directory paths."""
    pcx_dir = Path(__file__).resolve().parents[1]
    root_dir = pcx_dir.parent
    return root_dir, pcx_dir


def ensure_logs_dir(root_dir: Path) -> Path:
    """Ensure the logs directory exists and return its path."""
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
