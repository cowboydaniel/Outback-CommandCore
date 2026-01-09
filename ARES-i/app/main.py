from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QThread, QTimer, Signal

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import config
from ui.window import IOSToolsModule
from ui.splash_screen import show_splash_screen


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading modules...")
            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            logging.exception("Startup failed")
            self.failed.emit(str(exc))


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

    splash_start_time = time.time()
    minimum_splash_duration = 5.9

    thread = QThread()
    worker = StartupWorker()
    worker.moveToThread(thread)

    worker.status.connect(splash.update_status)
    if hasattr(splash, "set_progress"):
        worker.progress.connect(splash.set_progress)

    main_windows = []

    def show_main() -> None:
        elapsed = time.time() - splash_start_time
        remaining = max(0, minimum_splash_duration - elapsed)

        def finish_startup() -> None:
            nonlocal main_window
            if splash and splash.isVisible():
                splash.close()
            window = IOSToolsModule()
            main_windows.append(window)
            window.show()

        QTimer.singleShot(int(remaining * 1000), finish_startup)

    def handle_error(message: str) -> None:
        if splash and splash.isVisible():
            splash.update_status(f"Error: {message}")
        QTimer.singleShot(2000, app.quit)

    worker.finished.connect(show_main)
    worker.failed.connect(handle_error)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.started.connect(worker.run)
    thread.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
