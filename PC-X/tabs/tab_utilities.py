"""Utilities tab layout for PC-X."""

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


def setup_utilities_tab(module) -> None:
    """Set up the Utilities tab."""
    utilities_tab = module.tools_tabs["utilities"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("System Utilities")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    cleanup_group = QGroupBox("Disk Analysis & Cleanup")
    cleanup_layout = QVBoxLayout(cleanup_group)

    cleanup_info = QLabel("Analyze disk usage and remove unnecessary files to free space.")
    cleanup_layout.addWidget(cleanup_info)

    analyze_btn = QPushButton("Analyze Disk Space")
    analyze_btn.clicked.connect(module.analyze_disk_space)
    cleanup_layout.addWidget(analyze_btn)

    tmp_btn = QPushButton("Clear /tmp Files (older than 1 day)")
    tmp_btn.clicked.connect(module.clear_tmp_files)
    cleanup_layout.addWidget(tmp_btn)

    apt_btn = QPushButton("Clean APT Cache")
    apt_btn.clicked.connect(module.clear_apt_cache)
    cleanup_layout.addWidget(apt_btn)

    content_layout.addWidget(cleanup_group)

    log_group = QGroupBox("Activity Log")
    log_layout = QVBoxLayout(log_group)

    module.utils_log = QTextEdit()
    module.utils_log.setReadOnly(True)
    module.utils_log.setMaximumHeight(200)
    log_layout.addWidget(module.utils_log)

    content_layout.addWidget(log_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(utilities_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
