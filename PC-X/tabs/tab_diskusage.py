"""Disk Usage tab for PC-X — top-N directory size bar chart + du browser."""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

BAR_COLORS = [
    "#3498db", "#e74c3c", "#2ecc71", "#e67e22", "#9b59b6",
    "#1abc9c", "#f39c12", "#d35400", "#27ae60", "#8e44ad",
]


class _BarChart(QWidget):
    """Simple horizontal bar chart for directory sizes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[tuple[str, int]] = []   # (label, bytes)
        self.setMinimumHeight(220)

    def set_data(self, rows: list[tuple[str, int]]):
        self._rows = rows
        self.update()

    def paintEvent(self, event):
        if not self._rows:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 220
        margin_right = 90
        bar_area = w - margin_left - margin_right
        if bar_area <= 0:
            return

        max_val = max(v for _, v in self._rows) or 1
        bar_h = max(12, min(28, (h - 20) // max(len(self._rows), 1) - 4))
        row_h = bar_h + 6
        total_h = row_h * len(self._rows) + 20

        p.fillRect(0, 0, w, h, self.palette().base().color())

        for i, (label, val) in enumerate(self._rows):
            y = 10 + i * row_h
            color = QColor(BAR_COLORS[i % len(BAR_COLORS)])

            # label
            p.setPen(self.palette().text().color())
            p.setFont(QFont("Arial", 9))
            lbl = label if len(label) <= 28 else "…" + label[-26:]
            p.drawText(4, y, margin_left - 8, bar_h, Qt.AlignVCenter | Qt.AlignRight, lbl)

            # bar
            bar_w = int(bar_area * val / max_val)
            p.fillRect(margin_left, y, bar_w, bar_h, color)

            # size label
            p.setPen(self.palette().text().color())
            p.drawText(margin_left + bar_w + 4, y, margin_right - 4, bar_h,
                       Qt.AlignVCenter | Qt.AlignLeft, _fmt(val))


class _Signals(QObject):
    loaded = Signal(list)   # list[(path_str, size_bytes)]


def _fmt(b: int) -> str:
    if b >= 1 << 30:
        return f"{b / (1 << 30):.1f} GB"
    if b >= 1 << 20:
        return f"{b / (1 << 20):.1f} MB"
    if b >= 1 << 10:
        return f"{b / (1 << 10):.1f} KB"
    return f"{b} B"


def _du_top(path: str, depth: int, count: int) -> list[tuple[str, int]]:
    try:
        r = subprocess.run(
            ["du", "-b", f"--max-depth={depth}", path],
            capture_output=True, text=True, timeout=60,
        )
        rows = []
        for line in r.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                try:
                    size = int(parts[0])
                    p = parts[1].strip()
                    if p != path:
                        rows.append((p, size))
                except ValueError:
                    pass
        rows.sort(key=lambda x: x[1], reverse=True)
        return rows[:count]
    except Exception as exc:
        return [(f"Error: {exc}", 0)]


def setup_diskusage_tab(module) -> None:
    tab = module.tools_tabs["disk usage"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tl = QHBoxLayout(toolbar)
    tl.setContentsMargins(0, 0, 0, 0)
    tl.setSpacing(8)

    tl.addWidget(QLabel("Path:"))
    path_edit = QLineEdit()
    path_edit.setText(str(Path.home()))
    path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tl.addWidget(path_edit)

    tl.addWidget(QLabel("Depth:"))
    depth_slider = QSlider(Qt.Horizontal)
    depth_slider.setRange(1, 4)
    depth_slider.setValue(1)
    depth_slider.setFixedWidth(80)
    depth_label = QLabel("1")
    depth_slider.valueChanged.connect(lambda v: depth_label.setText(str(v)))
    tl.addWidget(depth_slider)
    tl.addWidget(depth_label)

    tl.addWidget(QLabel("Top:"))
    count_slider = QSlider(Qt.Horizontal)
    count_slider.setRange(5, 30)
    count_slider.setValue(15)
    count_slider.setFixedWidth(80)
    count_label = QLabel("15")
    count_slider.valueChanged.connect(lambda v: count_label.setText(str(v)))
    tl.addWidget(count_slider)
    tl.addWidget(count_label)

    scan_btn = QPushButton("Scan")
    tl.addWidget(scan_btn)

    root.addWidget(toolbar)

    module._du_status = QLabel("Enter a path and click Scan.")
    module._du_status.setFont(QFont("Arial", 9))
    root.addWidget(module._du_status)

    # ── splitter: chart + table ───────────────────────────────────────────────
    splitter = QSplitter(Qt.Vertical)
    root.addWidget(splitter)

    chart = _BarChart()
    splitter.addWidget(chart)

    table = QTableWidget()
    table.setColumnCount(3)
    table.setHorizontalHeaderLabels(["Path", "Size", "% of shown"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    table.setColumnWidth(1, 90)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    table.setColumnWidth(2, 100)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setAlternatingRowColors(True)
    table.setFont(QFont("Arial", 9))
    splitter.addWidget(table)
    splitter.setSizes([260, 200])

    module._du_rows: list = []

    def _populate(rows: list[tuple[str, int]]):
        module._du_rows = rows
        chart.set_data([(os.path.basename(p) or p, s) for p, s in rows])

        total = sum(s for _, s in rows) or 1
        table.setRowCount(len(rows))
        for r, (path, size) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(path))
            size_item = QTableWidgetItem(_fmt(size))
            size_item.setData(Qt.UserRole, size)
            table.setItem(r, 1, size_item)
            pct = 100 * size / total
            table.setItem(r, 2, QTableWidgetItem(f"{pct:.1f}%"))
            table.setRowHeight(r, 22)

        module._du_status.setText(
            f"Scanned {len(rows)} entries — total shown: {_fmt(sum(s for _, s in rows))}"
        )
        scan_btn.setEnabled(True)

    def _scan():
        path = path_edit.text().strip()
        if not path or not os.path.isdir(path):
            module._du_status.setText("Invalid path.")
            return
        scan_btn.setEnabled(False)
        module._du_status.setText("Scanning…")
        table.setRowCount(0)
        depth = depth_slider.value()
        count = count_slider.value()
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.loaded.connect(_populate)
        threading.Thread(
            target=lambda: sig.loaded.emit(_du_top(path, depth, count)),
            daemon=True,
        ).start()

    scan_btn.clicked.connect(_scan)

    # double-click a row → drill into that directory
    def _drill_down(row, _col):
        if row < len(module._du_rows):
            p, _ = module._du_rows[row]
            if os.path.isdir(p):
                path_edit.setText(p)
                _scan()

    table.cellDoubleClicked.connect(_drill_down)
