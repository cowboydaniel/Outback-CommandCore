"""Shared base classes for BLACKSTORM tabs and widgets."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget


class BaseTab(QWidget):
    """Base class for BLACKSTORM tabs."""

    def set_settings(self, settings):
        """Receive settings from the main application."""
        _ = settings
