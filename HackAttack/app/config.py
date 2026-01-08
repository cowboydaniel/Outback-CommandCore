"""Centralized configuration for the HackAttack GUI application."""

from __future__ import annotations

import logging
from typing import Dict

APP_NAME = "Hack Attack"
APP_VERSION = "0.1.0"
APP_TAGLINE = "Professional Security Testing Suite"
APP_DESCRIPTION = "Enterprise-Grade Security Testing and Ethical Hacking Platform"
APP_AUTHOR = "Hack Attack Team"
APP_AUTHOR_EMAIL = "security@hackattack.example"

PROJECT_URLS: Dict[str, str] = {
    "Bug Tracker": "https://github.com/hack-attack/security-platform/issues",
    "Documentation": "https://hack-attack.readthedocs.io/",
    "Source Code": "https://github.com/hack-attack/security-platform",
}

LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%H:%M:%S",
}


def application_title() -> str:
    """Return the window title for the GUI."""
    return f"{APP_NAME} - {APP_TAGLINE}"
