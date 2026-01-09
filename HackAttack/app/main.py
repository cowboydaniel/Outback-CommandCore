"""Main entry point for the HackAttack GUI application."""

from __future__ import annotations

import importlib.util
import logging
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from HackAttack.app.config import LOGGING_CONFIG, application_title
from HackAttack.tabs import get_tab_definitions
from HackAttack.ui.themes import APP_STYLESHEET

logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

if importlib.util.find_spec("PySide6") is None:
    message = (
        "Error: PySide6 is required. Install dependencies with "
        "`pip install -r HackAttack/requirements.txt` (see HackAttack/README.md)."
    )
    logger.error(message)
    print(message)
    sys.exit(1)

from PySide6.QtGui import QFont
from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from HackAttack.ui.splash_screen import show_splash_screen


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading penetration testing modules...")
            window = HackAttackGUI()
            self.status.emit("Ready!")
            self.finished.emit(window)
        except Exception as exc:
            logger.error("Startup failed: %s", exc, exc_info=True)
            self.failed.emit(str(exc))


class HackAttackGUI(QMainWindow):
    """Primary GUI window for HackAttack."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(application_title())
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(APP_STYLESHEET)

        self.tab_definitions = get_tab_definitions()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.create_sidebar()
        self.create_main_content()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_sidebar(self) -> None:
        """Create the sidebar navigation."""
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(280)
        self.sidebar.setMaximumWidth(300)
        self.sidebar.setWordWrap(True)

        self.sidebar.addItems([tab.title for tab in self.tab_definitions])
        self.sidebar.currentRowChanged.connect(self.change_page)
        self.main_layout.addWidget(self.sidebar)

    def create_main_content(self) -> None:
        """Create the main content area with stacked widgets."""
        self.stacked_widget = QStackedWidget()

        for tab in self.tab_definitions:
            try:
                page = tab.builder(tab.title, tab.description, tab.icon)
            except Exception as exc:
                logger.error("Failed to build tab '%s': %s", tab.title, exc, exc_info=True)
                page = QWidget()
            self.stacked_widget.addWidget(page)

        self.main_layout.addWidget(self.stacked_widget, 1)

    def change_page(self, index: int) -> None:
        """Change the current page based on sidebar selection."""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            current_item = self.sidebar.currentItem()
            if current_item is not None:
                self.status_bar.showMessage(f"Switched to: {current_item.text()}")


def main() -> int:
    """Launch the HackAttack GUI."""
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setFont(QFont("Segoe UI", 10))

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

        def show_main(window: HackAttackGUI) -> None:
            elapsed = time.time() - splash_start_time
            remaining = max(0, minimum_splash_duration - elapsed)

            def finish_startup() -> None:
                if splash and splash.isVisible():
                    splash.close()
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
    except Exception as exc:
        logger.error("Application error: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
