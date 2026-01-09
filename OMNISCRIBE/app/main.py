#!/usr/bin/env python3
"""
OMNISCRIBE - Automation and Scripting Control Suite
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from OMNISCRIBE.app.config import APP_VERSION, APP_NAME
from OMNISCRIBE.core.base import Omniscribe
from OMNISCRIBE.core.utils import create_sample_scripts
from OMNISCRIBE.ui.main_window import OmniscribeMainWindow
from OMNISCRIBE.ui.splash_screen import show_splash_screen


def main() -> None:
    """Main entry point for OMNISCRIBE."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set application style
    app.setStyle('Fusion')

    # Show splash screen
    splash = show_splash_screen()
    app.processEvents()

    splash.update_status("Loading speech recognition models...")
    app.processEvents()

    # Create Omniscribe instance
    omni = Omniscribe()

    # Create the main window
    ui = OmniscribeMainWindow(omni)

    # Add some sample scripts if none exist
    create_sample_scripts(omni, ui.script_tab)

    splash.update_status("Ready!")
    app.processEvents()

    # Close splash and show main window after animation completes
    def show_main():
        splash.close()
        ui.show()

    QTimer.singleShot(5900, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
