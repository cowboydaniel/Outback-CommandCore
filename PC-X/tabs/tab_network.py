"""Network tab layout for PC-X."""

import logging

import psutil
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFont


def setup_network_tab(module) -> None:
    """Set up the Network tab with interface and speed information."""
    network_tab = module.device_tabs["network"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("Network Information")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    interfaces_group = QGroupBox("Network Interfaces")
    interfaces_layout = QVBoxLayout(interfaces_group)

    try:
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        for iface, addrs in net_if_addrs.items():
            iface_frame = QGroupBox(iface)
            iface_layout = QGridLayout(iface_frame)

            row = 0
            for addr in addrs:
                if addr.family.name == "AF_INET":
                    label = QLabel("IPv4 Address:")
                    label.setFont(QFont("Arial", 9, QFont.Bold))
                    iface_layout.addWidget(label, row, 0)
                    iface_layout.addWidget(QLabel(addr.address), row, 1)
                    row += 1
                elif addr.family.name == "AF_INET6":
                    label = QLabel("IPv6 Address:")
                    label.setFont(QFont("Arial", 9, QFont.Bold))
                    iface_layout.addWidget(label, row, 0)
                    iface_layout.addWidget(QLabel(addr.address[:30] + "..."), row, 1)
                    row += 1
                elif addr.family.name == "AF_PACKET":
                    label = QLabel("MAC Address:")
                    label.setFont(QFont("Arial", 9, QFont.Bold))
                    iface_layout.addWidget(label, row, 0)
                    iface_layout.addWidget(QLabel(addr.address), row, 1)
                    row += 1

            if iface in net_if_stats:
                stats = net_if_stats[iface]
                label = QLabel("Status:")
                label.setFont(QFont("Arial", 9, QFont.Bold))
                iface_layout.addWidget(label, row, 0)
                status = "Up" if stats.isup else "Down"
                iface_layout.addWidget(QLabel(status), row, 1)
                row += 1

                label = QLabel("Speed:")
                label.setFont(QFont("Arial", 9, QFont.Bold))
                iface_layout.addWidget(label, row, 0)
                speed = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"
                iface_layout.addWidget(QLabel(speed), row, 1)

            interfaces_layout.addWidget(iface_frame)
    except Exception as exc:
        logging.error("Error getting network info: %s", exc)
        interfaces_layout.addWidget(QLabel(f"Error: {exc}"))

    content_layout.addWidget(interfaces_group)

    speed_group = QGroupBox("Internet Speed Test")
    speed_layout = QVBoxLayout(speed_group)

    results_frame = QFrame()
    results_layout = QGridLayout(results_frame)

    results_layout.addWidget(QLabel("Server:"), 0, 0)
    module.server_label = QLabel("Not tested")
    results_layout.addWidget(module.server_label, 0, 1)

    results_layout.addWidget(QLabel("Download:"), 1, 0)
    module.download_speed = QLabel("--")
    module.download_speed.setFont(QFont("Arial", 14, QFont.Bold))
    results_layout.addWidget(module.download_speed, 1, 1)

    results_layout.addWidget(QLabel("Upload:"), 2, 0)
    module.upload_speed = QLabel("--")
    module.upload_speed.setFont(QFont("Arial", 14, QFont.Bold))
    results_layout.addWidget(module.upload_speed, 2, 1)

    results_layout.addWidget(QLabel("Ping:"), 3, 0)
    module.ping_label = QLabel("--")
    results_layout.addWidget(module.ping_label, 3, 1)

    speed_layout.addWidget(results_frame)

    module.speed_progress = QProgressBar()
    module.speed_progress.setValue(0)
    speed_layout.addWidget(module.speed_progress)

    module.phase_label = QLabel("Click 'Start Speed Test' to begin")
    speed_layout.addWidget(module.phase_label)

    module.test_button = QPushButton("Start Speed Test")
    module.test_button.clicked.connect(module.run_speed_test)
    speed_layout.addWidget(module.test_button)

    content_layout.addWidget(speed_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(network_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
