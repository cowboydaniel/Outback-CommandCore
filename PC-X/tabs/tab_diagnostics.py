"""Diagnostics tab layout for PC-X."""

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFont


def setup_diagnostics_tab(module) -> None:
    """Set up the Diagnostics tab."""
    diagnostics_tab = module.tools_tabs["diagnostics"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("System Diagnostics")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    quick_group = QGroupBox("Quick System Check")
    quick_layout = QVBoxLayout(quick_group)

    quick_info = QLabel("Run a quick diagnostic check on your system.")
    quick_layout.addWidget(quick_info)

    module.diag_results = QTextEdit()
    module.diag_results.setReadOnly(True)
    module.diag_results.setMaximumHeight(250)
    quick_layout.addWidget(module.diag_results)

    quick_btn = QPushButton("Run Quick Diagnostics")
    quick_btn.clicked.connect(module.run_quick_diagnostics)
    quick_layout.addWidget(quick_btn)

    content_layout.addWidget(quick_group)

    logs_group = QGroupBox("System Logs")
    logs_layout = QVBoxLayout(logs_group)

    module.log_text_widget = QTextEdit()
    module.log_text_widget.setReadOnly(True)
    module.log_text_widget.setMaximumHeight(200)
    logs_layout.addWidget(module.log_text_widget)

    logs_btn = QPushButton("View Recent Logs")
    logs_btn.clicked.connect(module.view_system_logs)
    logs_layout.addWidget(logs_btn)

    content_layout.addWidget(logs_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(diagnostics_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
