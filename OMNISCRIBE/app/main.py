#!/usr/bin/env python3
"""
OMNISCRIBE - Automation and Scripting Control Suite
"""
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QThread, QTimer, Signal

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from OMNISCRIBE.app.config import APP_VERSION, APP_NAME
from OMNISCRIBE.core.base import Omniscribe
from OMNISCRIBE.core.utils import create_sample_scripts
from OMNISCRIBE.ui.main_window import OmniscribeMainWindow
from OMNISCRIBE.ui.splash_screen import show_splash_screen


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading speech recognition models...")
            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


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

    splash_start_time = time.time()
    minimum_splash_duration = 5.9

    thread = QThread()
    worker = StartupWorker()
    worker.moveToThread(thread)

    worker.status.connect(splash.update_status)
    if hasattr(splash, "set_progress"):
        worker.progress.connect(splash.set_progress)

    main_window = None

    def show_main() -> None:
        elapsed = time.time() - splash_start_time
        remaining = max(0, minimum_splash_duration - elapsed)

        def finish_startup() -> None:
            nonlocal main_window
            if splash and splash.isVisible():
                splash.close()
            omni = Omniscribe()
            main_window = OmniscribeMainWindow(omni)
            create_sample_scripts(omni, main_window.script_tab)
            main_window.show()

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

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
