from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit


def setup_log_console_tab(window) -> None:
    """Set up the log console tab."""
    layout = window.log_layout

    controls_layout = QHBoxLayout()

    clear_btn = QPushButton("Clear Log")
    clear_btn.clicked.connect(lambda: window.log_text.clear())
    controls_layout.addWidget(clear_btn)

    save_btn = QPushButton("Save Log...")
    save_btn.clicked.connect(window.save_log)
    controls_layout.addWidget(save_btn)

    controls_layout.addStretch()

    layout.addLayout(controls_layout)

    window.log_text = QTextEdit()
    window.log_text.setReadOnly(True)
    window.log_text.setFont(QFont("Monospace", 10))

    layout.addWidget(window.log_text)

    window.log_message("Log console initialized")
