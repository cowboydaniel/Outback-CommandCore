from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QScrollArea, QVBoxLayout, QWidget


def setup_tools_tab(window) -> None:
    """Set up the tools tab with scrollable categories."""
    tools_layout = window.tools_layout
    tools_layout.setContentsMargins(0, 0, 0, 0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(15)

    grid_layout = QGridLayout()
    grid_layout.setContentsMargins(0, 0, 0, 0)
    grid_layout.setSpacing(15)

    tool_categories = [
        ("Device Control", window._add_device_control_widgets, 0, 0),
        ("App Management", window._add_app_management_widgets, 0, 1),
        ("System Tools", window._add_system_tools_widgets, 1, 0),
        ("iOS Tools", window._add_ios_tools_widgets, 1, 1),
        ("Debugging", window._add_debugging_widgets, 2, 0),
        ("File Operations", window._add_file_operations_widgets, 2, 1),
        ("Security", window._add_security_widgets, 3, 0),
        ("Automation", window._add_automation_widgets, 3, 1),
        ("Advanced Tests", window._add_advanced_tests_widgets, 4, 0),
    ]

    for title, method, row, col in tool_categories:
        group_box = QGroupBox(title)
        group_box.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin-top: 12px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            """
        )

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 20, 10, 10)
        content_layout.setSpacing(8)

        method(content_layout)

        group_box.setLayout(content_layout)
        grid_layout.addWidget(group_box, row, col)

    scroll_layout.addLayout(grid_layout)
    scroll_layout.addStretch()

    scroll_area.setWidget(scroll_content)

    tools_layout.addWidget(scroll_area)
