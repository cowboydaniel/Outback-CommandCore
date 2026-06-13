"""Log Viewer tab for PC-X — journald + syslog browser with live tail."""

from __future__ import annotations

import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

LOG_SOURCES = [
    ("System journal (all)",  ["journalctl", "-n", "{lines}", "--no-pager", "--output=short-iso"]),
    ("Kernel (dmesg)",        ["journalctl", "-k", "-n", "{lines}", "--no-pager", "--output=short-iso"]),
    ("Auth log",              ["journalctl", "-u", "ssh", "-u", "sudo", "-n", "{lines}", "--no-pager", "--output=short-iso"]),
    ("Syslog file",           ["tail", "-n", "{lines}", "/var/log/syslog"]),
    ("Apt history",           ["tail", "-n", "{lines}", "/var/log/apt/history.log"]),
]

LEVEL_COLORS = {
    "emerg":   "#ff0000",
    "alert":   "#ff4500",
    "crit":    "#ff6347",
    "err":     "#e74c3c",
    "error":   "#e74c3c",
    "warning": "#e67e22",
    "warn":    "#e67e22",
    "notice":  "#3498db",
    "info":    "#2ecc71",
    "debug":   "#95a5a6",
}


class _Signals(QObject):
    lines_ready = Signal(list)


def _fetch_log(source_args: list, lines: int) -> list:
    args = [a.replace("{lines}", str(lines)) for a in source_args]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return (r.stdout + r.stderr).splitlines()
    except Exception as exc:
        return [f"Error fetching log: {exc}"]


def setup_logs_tab(module) -> None:
    tab = module.mgmt_tabs["logs"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tl = QHBoxLayout(toolbar)
    tl.setContentsMargins(0, 0, 0, 0)
    tl.setSpacing(8)

    source_cb = QComboBox()
    for label, _ in LOG_SOURCES:
        source_cb.addItem(label)
    source_cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tl.addWidget(source_cb)

    tl.addWidget(QLabel("Lines:"))
    lines_spin = QSpinBox()
    lines_spin.setRange(50, 5000)
    lines_spin.setValue(200)
    lines_spin.setSingleStep(50)
    tl.addWidget(lines_spin)

    refresh_btn = QPushButton("Load")
    tl.addWidget(refresh_btn)

    live_chk = QCheckBox("Live tail (5 s)")
    tl.addWidget(live_chk)

    root.addWidget(toolbar)

    # ── filter bar ────────────────────────────────────────────────────────────
    filter_bar = QFrame()
    fl = QHBoxLayout(filter_bar)
    fl.setContentsMargins(0, 0, 0, 0)
    fl.setSpacing(8)

    filter_edit = QLineEdit()
    filter_edit.setPlaceholderText("Filter (case-insensitive substring)…")
    filter_edit.setClearButtonEnabled(True)
    filter_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    fl.addWidget(filter_edit)

    highlight_edit = QLineEdit()
    highlight_edit.setPlaceholderText("Highlight keyword…")
    highlight_edit.setClearButtonEnabled(True)
    highlight_edit.setFixedWidth(180)
    fl.addWidget(highlight_edit)

    root.addWidget(filter_bar)

    # ── log display ───────────────────────────────────────────────────────────
    log_view = QTextEdit()
    log_view.setReadOnly(True)
    log_view.setFont(QFont("Courier", 9))
    log_view.setLineWrapMode(QTextEdit.NoWrap)
    log_view.setPlaceholderText("Select a source and click Load.")
    root.addWidget(log_view)

    module._log_raw_lines: list = []

    def _level_color(line: str) -> str | None:
        ll = line.lower()
        for kw, color in LEVEL_COLORS.items():
            if kw in ll:
                return color
        return None

    def _render(lines: list):
        module._log_raw_lines = lines
        filter_text = filter_edit.text().lower()
        highlight = highlight_edit.text().lower()

        log_view.clear()
        cursor = log_view.textCursor()

        for line in lines:
            if filter_text and filter_text not in line.lower():
                continue
            fmt = cursor.charFormat()
            color = _level_color(line)
            if color:
                fmt.setForeground(QColor(color))
            else:
                fmt.setForeground(log_view.palette().text().color())
            if highlight and highlight in line.lower():
                fmt.setBackground(QColor("#4a3800"))
            else:
                fmt.setBackground(log_view.palette().base().color())
            cursor.setCharFormat(fmt)
            cursor.insertText(line + "\n")

        log_view.moveCursor(QTextCursor.End)

    def _load():
        refresh_btn.setEnabled(False)
        idx = source_cb.currentIndex()
        _, args = LOG_SOURCES[idx]
        lines = lines_spin.value()
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.lines_ready.connect(lambda ls: (_render(ls), refresh_btn.setEnabled(True)))
        threading.Thread(
            target=lambda: sig.lines_ready.emit(_fetch_log(args, lines)),
            daemon=True,
        ).start()

    refresh_btn.clicked.connect(_load)
    filter_edit.textChanged.connect(lambda _: _render(module._log_raw_lines))
    highlight_edit.textChanged.connect(lambda _: _render(module._log_raw_lines))
    source_cb.currentIndexChanged.connect(lambda _: _load())

    # ── live tail timer ───────────────────────────────────────────────────────
    module._log_live_timer = QTimer()
    module._log_live_timer.setInterval(5000)
    module._log_live_timer.timeout.connect(_load)

    def _toggle_live(state):
        if state:
            module._log_live_timer.start()
        else:
            module._log_live_timer.stop()

    live_chk.stateChanged.connect(_toggle_live)

    _load()
