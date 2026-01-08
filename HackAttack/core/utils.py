"""Shared utility helpers for HackAttack."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger(__name__)


def load_json_file(path: str | Path) -> Optional[Any]:
    """Load JSON from disk and log useful diagnostics."""
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            logger.info("Loaded %s successfully", path)
            if isinstance(data, dict):
                logger.info("Keys in %s: %s", path.name, list(data.keys()))
            return data
    except Exception as exc:
        logger.error("Error loading %s: %s", path, exc)
        return None
