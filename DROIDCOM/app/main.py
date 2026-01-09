"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys

import time

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, QThread, QTimer, Signal

if __package__:
    from . import AndroidToolsModule
    from .config import APP_VERSION
    from ..ui.splash_screen import show_splash_screen
else:
    module_root = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(module_root))
    from DROIDCOM.app import AndroidToolsModule
    from DROIDCOM.app.config import APP_VERSION
    from DROIDCOM.ui.splash_screen import show_splash_screen


def main():
    """Main entry point for the application"""
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setApplicationVersion(APP_VERSION)

    # Show splash screen
    splash = show_splash_screen()
    qt_app.processEvents()

    class StartupWorker(QObject):
        status = Signal(str)
        progress = Signal(int)
        finished = Signal(object)
        failed = Signal(str)

        def run(self) -> None:
            try:
                self.status.emit("Scanning for devices...")
                window = QtWidgets.QWidget()
                window.setWindowTitle("DROIDCOM - Android Device Management")
                # Ensure window has minimize, maximize and close buttons
                window.setWindowFlags(
                    QtCore.Qt.Window |
                    QtCore.Qt.WindowMinimizeButtonHint |
                    QtCore.Qt.WindowMaximizeButtonHint |
                    QtCore.Qt.WindowCloseButtonHint
                )
                # Set a smaller default size that fits most screens
                window.resize(800, 600)  # Wider but shorter
                window.setMinimumSize(800, 400)  # Set minimum size

                # Set window icon
                icon_path = Path(__file__).resolve().parents[2] / 'icons' / 'droidcom.png'
                if icon_path.exists():
                    window.setWindowIcon(QIcon(str(icon_path)))

                layout = QtWidgets.QVBoxLayout(window)
                app = AndroidToolsModule(window)
                layout.addWidget(app)

                self.status.emit("Ready!")
                self.finished.emit(window)
            except Exception as exc:
                self.failed.emit(str(exc))

    splash_start_time = time.time()
    minimum_splash_duration = 5.9

    thread = QThread()
    worker = StartupWorker()
    worker.moveToThread(thread)

    worker.status.connect(splash.update_status)
    if hasattr(splash, "set_progress"):
        worker.progress.connect(splash.set_progress)

    def show_main(window: QtWidgets.QWidget) -> None:
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
        QTimer.singleShot(2000, qt_app.quit)

    worker.finished.connect(show_main)
    worker.failed.connect(handle_error)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.started.connect(worker.run)
    thread.start()

    qt_app.exec()


# For testing the module independently
if __name__ == "__main__":
    main()
