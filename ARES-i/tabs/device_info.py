from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QGridLayout, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QPushButton


def setup_device_info_tab(window) -> None:
    """Set up the device info tab."""
    layout = window.device_layout

    connection_frame = QGroupBox("Device Connection")
    connection_layout = QVBoxLayout(connection_frame)

    conn_buttons_frame = QHBoxLayout()

    window.connect_button = QPushButton("Connect iPhone")
    window.connect_button.clicked.connect(window.connect_device)
    conn_buttons_frame.addWidget(window.connect_button)

    window.refresh_button = QPushButton("Refresh Devices")
    window.refresh_button.clicked.connect(window.refresh_device_list)
    conn_buttons_frame.addWidget(window.refresh_button)

    conn_buttons_frame.addStretch()

    connection_layout.addLayout(conn_buttons_frame)

    instructions = QLabel(
        "1. Make sure your iPhone is unlocked\n"
        "2. Connect your iPhone via USB cable\n"
        "3. On your iPhone, tap 'Trust' when prompted\n"
        "4. Click 'Connect iPhone' above"
    )
    connection_layout.addWidget(instructions)

    layout.addWidget(connection_frame)

    info_frame = QGroupBox("Device Information")
    info_layout = QGridLayout(info_frame)

    window.info_fields = {}
    basic_fields = ["Model", "Manufacturer", "iOS Version", "Serial Number", "UDID", "Battery Level"]

    for i, field in enumerate(basic_fields):
        label = QLabel(f"{field}:")
        label.setStyleSheet("font-weight: bold;")
        value = QLabel("N/A")
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        info_layout.addWidget(label, i, 0)
        info_layout.addWidget(value, i, 1)

        window.info_fields[field] = value

    debug_label = QLabel("Debug Information")
    debug_label.setStyleSheet("font-weight: bold;")
    info_layout.addWidget(debug_label, len(basic_fields) + 1, 0, 1, 2)

    window.debug_text = QTextEdit()
    window.debug_text.setReadOnly(True)
    window.debug_text.setMaximumHeight(100)
    info_layout.addWidget(window.debug_text, len(basic_fields) + 2, 0, 1, 2)

    layout.addWidget(info_frame)
    layout.addStretch()
