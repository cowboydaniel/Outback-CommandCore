from __future__ import annotations

from PySide6.QtCore import QObject, Signal as PySideSignal
from PySide6.QtWidgets import QMainWindow


class SignalEmitter(QObject):
    update_signal = PySideSignal(str)

    def __init__(self) -> None:
        super().__init__()

    def update_status(self, message: str) -> None:
        self.update_signal.emit(message)


class BaseWindow(QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
