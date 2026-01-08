"""Benchmarks tab layout for PC-X."""

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


def setup_benchmarks_tab(module) -> None:
    """Set up the Benchmarks tab."""
    benchmarks_tab = module.tools_tabs["benchmarks"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("System Benchmarks")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    disk_group = QGroupBox("Disk Speed Test")
    disk_layout = QVBoxLayout(disk_group)

    disk_info = QLabel("Test sequential read/write speeds of your storage devices.")
    disk_layout.addWidget(disk_info)

    module.disk_results = QTextEdit()
    module.disk_results.setReadOnly(True)
    module.disk_results.setMaximumHeight(150)
    disk_layout.addWidget(module.disk_results)

    disk_btn = QPushButton("Run Disk Benchmark")
    disk_btn.clicked.connect(module.run_disk_speed_test)
    disk_layout.addWidget(disk_btn)

    content_layout.addWidget(disk_group)

    cpu_group = QGroupBox("CPU Benchmark")
    cpu_layout = QVBoxLayout(cpu_group)

    cpu_info = QLabel("Test CPU performance with multi-threaded workloads.")
    cpu_layout.addWidget(cpu_info)

    module.cpu_results = QTextEdit()
    module.cpu_results.setReadOnly(True)
    module.cpu_results.setMaximumHeight(150)
    cpu_layout.addWidget(module.cpu_results)

    cpu_btn = QPushButton("Run CPU Benchmark")
    cpu_btn.clicked.connect(module.run_cpu_benchmark)
    cpu_layout.addWidget(cpu_btn)

    content_layout.addWidget(cpu_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(benchmarks_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
