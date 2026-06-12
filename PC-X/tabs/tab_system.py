"""System tab layout for PC-X."""

import getpass
import os
import platform
import socket
from datetime import datetime

import psutil
import subprocess
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFont


def setup_system_info_tab(module) -> None:
    """Set up the System Information tab."""
    system_tab = module.device_tabs["system"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("System Information")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    os_group = QGroupBox("Operating System")
    os_layout = QGridLayout(os_group)

    os_info = [
        ("OS", platform.system()),
        ("OS Version", platform.version()),
        ("OS Release", platform.release()),
        ("Architecture", platform.machine()),
        ("Hostname", socket.gethostname()),
        ("Python Version", platform.python_version()),
    ]

    for row, (label, value) in enumerate(os_info):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        os_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 10))
        os_layout.addWidget(value_label, row, 1)
        module.system_info_labels[label] = value_label

    content_layout.addWidget(os_group)

    user_group = QGroupBox("User Information")
    user_layout = QGridLayout(user_group)

    user_info = [
        ("Current User", getpass.getuser()),
        ("Home Directory", os.path.expanduser("~")),
        ("Current Directory", os.getcwd()),
    ]

    for row, (label, value) in enumerate(user_info):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        user_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 10))
        user_layout.addWidget(value_label, row, 1)

    content_layout.addWidget(user_group)

    boot_group = QGroupBox("System Uptime")
    boot_layout = QGridLayout(boot_group)

    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(uptime).split(".")[0]
    except Exception:
        boot_time = "Unknown"
        uptime_str = "Unknown"

    boot_info = [
        ("Boot Time", str(boot_time)),
        ("Uptime", uptime_str),
    ]

    for row, (label, value) in enumerate(boot_info):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        boot_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 10))
        boot_layout.addWidget(value_label, row, 1)
        module.system_info_labels[label] = value_label

    content_layout.addWidget(boot_group)

    stats_group = QGroupBox("System Stats")
    stats_layout = QGridLayout(stats_group)

    try:
        load1, load5, load15 = os.getloadavg()
        load_str = f"{load1:.2f}  {load5:.2f}  {load15:.2f}  (1m / 5m / 15m)"
    except Exception:
        load_str = "N/A"

    try:
        proc_count = len(psutil.pids())
    except Exception:
        proc_count = "N/A"

    try:
        pending_updates = "N/A"
        result = subprocess.run(
            ["apt-get", "-s", "upgrade"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            count = sum(
                1 for line in result.stdout.splitlines()
                if line.startswith("Inst ")
            )
            pending_updates = str(count)
    except Exception:
        pass

    stats_data = [
        ("Load Average", load_str),
        ("Running Processes", str(proc_count)),
        ("Pending Updates", pending_updates),
    ]

    for row, (label, value) in enumerate(stats_data):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        stats_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 10))
        value_label.setWordWrap(True)
        stats_layout.addWidget(value_label, row, 1)
        module.system_info_labels[label] = value_label

    content_layout.addWidget(stats_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(system_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
