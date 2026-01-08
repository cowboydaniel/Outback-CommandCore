"""Application configuration values for BLACKSTORM."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_TITLE = "BLACKSTORM - Secure Data Erasure & Forensic Suite"
WINDOW_MIN_SIZE = (1280, 800)

REPO_ROOT = Path(__file__).resolve().parents[2]
ICON_PATH = REPO_ROOT / "icons" / "blackstorm.png"

CONFIG_DIR = os.path.expanduser("~/.config/blackstorm")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Noto Sans"
DEFAULT_FONT_SIZE = 10

DEFAULT_SETTINGS = {
    "window_geometry": None,
    "window_state": None,
    "recent_files": [],
    "ui_theme": "dark",
    "font": {
        "family": DEFAULT_FONT_FAMILY,
        "size": DEFAULT_FONT_SIZE,
    },
    "show_statusbar": True,
    "show_toolbar": True,
    "language": "English",
    "save_location": "",
    "auto_update": True,
    "wipe_method": "DoD 5220.22-M (3-pass)",
    "verify_wipe": True,
}
