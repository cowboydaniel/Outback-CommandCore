#!/usr/bin/env python3
"""
NIGHTFIRE - Real-time Active Defense and Monitoring Tool
"""
import random
import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QThread, QTimer, Signal

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from NIGHTFIRE.app import config
from NIGHTFIRE.core.base import NightfireCore
from NIGHTFIRE.ui.main_window import NightfireUI
from NIGHTFIRE.ui.splash_screen import show_splash_screen


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Initializing defense systems...")
            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


def main() -> None:
    """Main entry point for NIGHTFIRE."""
    app = QApplication(sys.argv)

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

    main_windows = []
    nightfire = None

    def show_main() -> None:
        elapsed = time.time() - splash_start_time
        remaining = max(0, minimum_splash_duration - elapsed)

        def finish_startup() -> None:
            nonlocal nightfire
            if splash and splash.isVisible():
                splash.close()
            window = NightfireUI()
            nightfire = NightfireCore(window.signal_emitter)
            window.nightfire = nightfire

            # Connect UI buttons to nightfire methods
            window.btn_start.clicked.connect(nightfire.start_monitoring)
            window.btn_stop.clicked.connect(nightfire.stop_monitoring)

            # Start with monitoring off
            window.btn_start.setEnabled(True)
            window.btn_stop.setEnabled(False)
            main_windows.append(window)
            window.show()

            # Simulate some initial threats for demo
            def simulate_threats() -> None:
                for _ in range(3):
                    threat = random.choice(config.DEMO_THREAT_TYPES)
                    nightfire.detected_threats[threat] = nightfire.detected_threats.get(threat, 0) + 1
                    window.signal_emitter.alert_triggered.emit(
                        threat,
                        f"Detected {nightfire.detected_threats[threat]} occurrences"
                    )

            # Schedule some demo threats
            QTimer.singleShot(config.DEMO_THREATS_DELAY_MS, simulate_threats)

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
