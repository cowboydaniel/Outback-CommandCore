"""
System Status tab for the CommandCore Launcher.
"""
import platform
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


def _try_psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        return None


class StatCard(QFrame):
    def __init__(self, title, value="—", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet("""
            #statCard {
                background-color: #3A3A3A;
                border: 1px solid #4A4A4A;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #ECF0F1; font-size: 20px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(value)


class InfoRow(QWidget):
    def __init__(self, label, value, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #B0B0B0; font-size: 13px;")
        lbl.setFixedWidth(160)

        val = QLabel(value)
        val.setStyleSheet("color: #ECF0F1; font-size: 13px;")
        val.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(val, 1)


class SectionHeader(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #ECF0F1; font-size: 15px; font-weight: bold; margin-top: 8px;")


class SystemStatusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._psutil = _try_psutil()
        self._init_ui()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        title = QLabel("System Status")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ECF0F1;")
        subtitle = QLabel("Live system resource and hardware overview")
        subtitle.setStyleSheet("font-size: 14px; color: #B0B0B0;")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        # Live metric cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        self.cpu_card = StatCard("CPU Usage")
        self.mem_card = StatCard("Memory Usage")
        self.disk_card = StatCard("Disk Usage")
        for card in (self.cpu_card, self.mem_card, self.disk_card):
            cards_layout.addWidget(card)
        outer.addLayout(cards_layout)

        # Scrollable info section
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # Platform info
        info_layout.addWidget(SectionHeader("System Information"))
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #4A4A4A;")
        info_layout.addWidget(sep)

        uname = platform.uname()
        rows = [
            ("OS", f"{uname.system} {uname.release}"),
            ("Version", uname.version[:80] + ("…" if len(uname.version) > 80 else "")),
            ("Machine", uname.machine),
            ("Processor", uname.processor or "—"),
            ("Hostname", uname.node),
            ("Python", platform.python_version()),
        ]
        for label, value in rows:
            info_layout.addWidget(InfoRow(label, value))

        # CPU info
        info_layout.addWidget(SectionHeader("CPU"))
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #4A4A4A;")
        info_layout.addWidget(sep2)

        if self._psutil:
            cpu_count_logical = self._psutil.cpu_count(logical=True)
            cpu_count_physical = self._psutil.cpu_count(logical=False)
            cpu_freq = self._psutil.cpu_freq()
            freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "—"
            info_layout.addWidget(InfoRow("Physical cores", str(cpu_count_physical or "—")))
            info_layout.addWidget(InfoRow("Logical cores", str(cpu_count_logical or "—")))
            info_layout.addWidget(InfoRow("Frequency", freq_str))
        else:
            info_layout.addWidget(InfoRow("Cores", str(os.cpu_count() or "—")))

        info_layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

    def _refresh(self):
        ps = self._psutil
        if ps:
            cpu_pct = ps.cpu_percent(interval=None)
            mem = ps.virtual_memory()
            disk = ps.disk_usage('/')
            self.cpu_card.set_value(f"{cpu_pct:.1f}%")
            self.mem_card.set_value(f"{mem.percent:.1f}%")
            self.disk_card.set_value(f"{disk.percent:.1f}%")
        else:
            self.cpu_card.set_value("N/A")
            self.mem_card.set_value("N/A")
            self.disk_card.set_value("N/A")
