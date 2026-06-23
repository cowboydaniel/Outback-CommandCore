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
    # Splash is a QMainWindow; closing it before the real window appears
    # must not trigger quitOnLastWindowClosed and kill the app.
    app.setQuitOnLastWindowClosed(False)

    # Show splash screen
    splash = show_splash_screen()
    app.processEvents()
    splash.update_status("Loading modules...")

    main_windows = []
    _live_refs = []

    def finish_startup() -> None:
        # SplashScreen is a QMainWindow, not QSplashScreen - it has no
        # .finish() method, so close it directly.
        if splash and splash.isVisible():
            splash.close()

        window = IOSToolsModule()
        main_windows.append(window)
        window.destroyed.connect(app.quit)
        window.show()
        _live_refs.clear()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(finish_startup)
    _live_refs.append(timer)
    timer.start(5900)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
