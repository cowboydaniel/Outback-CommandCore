"""Logs tab layout for NIGHTFIRE."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtGui import QFont

from NIGHTFIRE.ui.styles import app_styles


def setup_log_tab(ui) -> QWidget:
    """Set up the log tab."""
    log_tab = QWidget()
    layout = QVBoxLayout(log_tab)

    # Log display
    ui.log_display = QTextEdit()
    ui.log_display.setReadOnly(True)
    ui.log_display.setFont(QFont(app_styles.LOG_FONT_FAMILY))

    layout.addWidget(ui.log_display)

    return log_tab
