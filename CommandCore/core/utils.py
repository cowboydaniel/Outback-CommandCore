"""
Utility helpers for CommandCore.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return a UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()
