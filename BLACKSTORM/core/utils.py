"""Core utility helpers for BLACKSTORM."""
from __future__ import annotations


def deep_merge(default, new):
    """Deep merge two dictionaries, preferring values from ``new``.

    Args:
        default (dict): Default dictionary values.
        new (dict): New dictionary values to merge in.

    Returns:
        dict: Merged dictionary.
    """
    if isinstance(default, dict) and isinstance(new, dict):
        result = default.copy()
        for key, value in new.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    return new if new is not None else default
