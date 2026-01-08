"""Qt signal definitions for the NIGHTFIRE UI."""
from PySide6.QtCore import QObject, Signal


class SignalEmitter(QObject):
    alert_triggered = Signal(str, str)  # alert_type, message
    log_message = Signal(str, str)      # level, message
