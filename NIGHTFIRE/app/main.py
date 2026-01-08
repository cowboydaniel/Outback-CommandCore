#!/usr/bin/env python3
"""
NIGHTFIRE - Real-time Active Defense and Monitoring Tool
"""
import random
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from NIGHTFIRE.app import config
from NIGHTFIRE.core.base import NightfireCore
from NIGHTFIRE.ui.main_window import NightfireUI


def main() -> None:
    """Main entry point for NIGHTFIRE."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create UI and core logic
    ui = NightfireUI()
    nightfire = NightfireCore(ui.signal_emitter)
    ui.nightfire = nightfire

    # Connect UI buttons to nightfire methods
    ui.btn_start.clicked.connect(nightfire.start_monitoring)
    ui.btn_stop.clicked.connect(nightfire.stop_monitoring)

    # Show the main window
    ui.show()

    # Start with monitoring off
    ui.btn_start.setEnabled(True)
    ui.btn_stop.setEnabled(False)

    # Simulate some initial threats for demo
    def simulate_threats() -> None:
        for _ in range(3):
            threat = random.choice(config.DEMO_THREAT_TYPES)
            nightfire.detected_threats[threat] = nightfire.detected_threats.get(threat, 0) + 1
            ui.signal_emitter.alert_triggered.emit(
                threat,
                f"Detected {nightfire.detected_threats[threat]} occurrences"
            )

    # Schedule some demo threats
    QTimer.singleShot(config.DEMO_THREATS_DELAY_MS, simulate_threats)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
