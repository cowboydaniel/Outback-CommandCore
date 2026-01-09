"""Application entry point for CommandCoreCodex."""

import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QThread, QTimer, Signal

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Codex.app.config import DEFAULT_CONFIG
from Codex.app.gui import CommandCoreGUI
from Codex.ui.splash_screen import show_splash_screen


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading AI models...")
            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


def create_app() -> QApplication:
    """Create the Qt application instance."""
    return QApplication(sys.argv)


def main() -> int:
    """Run the CommandCoreCodex GUI."""
    app = create_app()

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
            window = CommandCoreGUI(config=DEFAULT_CONFIG)
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
