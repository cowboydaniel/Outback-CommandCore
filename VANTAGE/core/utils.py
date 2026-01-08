"""Shared helpers for VANTAGE core components."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time with timezone info."""

    return datetime.now(timezone.utc)
