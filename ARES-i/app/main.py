from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import config
from ui.window import IOSToolsModule
from ui.splash_screen import show_splash_screen


def configure_logging() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()],
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationVersion(config.APP_VERSION)

    # Show splash screen
    splash = show_splash_screen()
    app.processEvents()

    # Create main window while splash is showing
    splash.update_status("Loading modules...")
    app.processEvents()

    window = IOSToolsModule()

    splash.update_status("Ready!")
    app.processEvents()

    # Close splash and show main window after animation completes
    def show_main():
        splash.close()
        window.show()

    QTimer.singleShot(5900, show_main)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
