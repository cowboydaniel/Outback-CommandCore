"""Core monitoring logic for NIGHTFIRE."""
from typing import Dict
import random

from PySide6.QtCore import QTimer

from NIGHTFIRE.app import config
from NIGHTFIRE.core.utils import setup_logging
from NIGHTFIRE.ui.components.signal_emitter import SignalEmitter


class NightfireCore:
    def __init__(self, signal_emitter: SignalEmitter) -> None:
        self.running = False
        self.logger = setup_logging()
        self.alert_thresholds = dict(config.ALERT_THRESHOLDS)
        self.detected_threats: Dict[str, int] = {}
        self.signal_emitter = signal_emitter
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_threats)

    def start_monitoring(self) -> None:
        """Start the monitoring service."""
        self.running = True
        self.timer.start(config.CHECK_INTERVAL_MS)
        self.signal_emitter.log_message.emit("INFO", "NIGHTFIRE monitoring service started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring service."""
        self.running = False
        self.timer.stop()
        self.signal_emitter.log_message.emit("INFO", "NIGHTFIRE monitoring service stopped")

    def check_for_threats(self) -> None:
        """Simulate checking for threats."""
        if not self.running:
            return

        # Simulate random threats for demo purposes
        if random.random() > 0.7:  # 30% chance of a threat
            threat = random.choice(config.THREAT_TYPES)
            self.detected_threats[threat] = self.detected_threats.get(threat, 0) + 1
            self.signal_emitter.alert_triggered.emit(
                threat,
                f"Detected {self.detected_threats[threat]} occurrences",
            )
            self._check_thresholds()

    def _check_thresholds(self) -> None:
        """Check if any threat thresholds have been exceeded."""
        for threat_type, count in self.detected_threats.items():
            if count >= self.alert_thresholds.get(threat_type, float("inf")):
                self._trigger_alert(threat_type, count)

    def _trigger_alert(self, threat_type: str, count: int) -> None:
        """Trigger an alert for a detected threat."""
        message = (
            f"{threat_type} detected {count} times "
            f"(threshold: {self.alert_thresholds.get(threat_type)})"
        )
        self.signal_emitter.alert_triggered.emit("THRESHOLD_EXCEEDED", message)
        self.signal_emitter.log_message.emit("WARNING", f"Alert: {message}")
