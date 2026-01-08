"""UI builder for the Logs tab."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
)


def setup_logs_tab(gui) -> None:
    """Set up the Logs tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    gui.log_display = QPlainTextEdit()
    gui.log_display.setReadOnly(True)
    gui.log_display.setPlaceholderText("Log messages will appear here...")

    btn_layout = QHBoxLayout()
    save_logs_btn = QPushButton("Save Logs")
    clear_logs_btn = QPushButton("Clear Logs")

    save_logs_btn.clicked.connect(gui.save_logs)
    clear_logs_btn.clicked.connect(gui.clear_logs)

    btn_layout.addWidget(save_logs_btn)
    btn_layout.addWidget(clear_logs_btn)
    btn_layout.addStretch()

    layout.addWidget(gui.log_display)
    layout.addLayout(btn_layout)

    gui.tab_widget.addTab(tab, "Logs")
