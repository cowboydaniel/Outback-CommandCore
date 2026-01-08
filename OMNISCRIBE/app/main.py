#!/usr/bin/env python3
"""
OMNISCRIBE - Automation and Scripting Control Suite
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from OMNISCRIBE.app.config import APP_VERSION, APP_NAME
from OMNISCRIBE.core.base import Omniscribe
from OMNISCRIBE.core.utils import create_sample_scripts
from OMNISCRIBE.ui.main_window import OmniscribeMainWindow


def main() -> None:
    """Main entry point for OMNISCRIBE."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set application style
    app.setStyle('Fusion')

    # Create Omniscribe instance
    omni = Omniscribe()

    # Create and show the main window
    ui = OmniscribeMainWindow(omni)
    ui.show()

    # Add some sample scripts if none exist
    create_sample_scripts(omni, ui.script_tab)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
