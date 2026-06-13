"""Service Manager tab for PC-X — systemd service control."""

from __future__ import annotations

import logging
import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QComboBox,
)


class _Signals(QObject):
    loaded = Signal(list)
    output = Signal(str)
    done = Signal(int)


def _load_services(filter_state: str) -> list:
    rows = []
    try:
        cmd = [
            "systemctl", "list-units", "--type=service",
            "--all", "--no-pager", "--plain", "--no-legend",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        for line in result.stdout.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 4:
                continue
            unit, load, active, sub = parts[0], parts[1], parts[2], parts[3]
            desc = parts[4].strip() if len(parts) > 4 else ""
            if filter_state == "running" and active != "active":
                continue
            if filter_state == "inactive" and active == "active":
                continue
            rows.append((unit, active, sub, load, desc))
    except Exception as exc:
        logging.warning("systemctl list-units failed: %s", exc)
    return rows


def _run_systemctl(args: list) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["systemctl", *args],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def setup_services_tab(module) -> None:
    tab = module.mgmt_tabs["services"]
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tb = QHBoxLayout(toolbar)
    tb.setContentsMargins(0, 0, 0, 0)
    tb.setSpacing(6)

    search = QLineEdit()
    search.setPlaceholderText("Search services…")
    search.setClearButtonEnabled(True)
    search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tb.addWidget(search)

    state_filter = QComboBox()
    state_filter.addItems(["All", "Running", "Inactive"])
    tb.addWidget(state_filter)

    refresh_btn = QPushButton("Refresh")
    tb.addWidget(refresh_btn)
    root.addWidget(toolbar)

    # ── action buttons ────────────────────────────────────────────────────────
    actions = QFrame()
    al = QHBoxLayout(actions)
    al.setContentsMargins(0, 0, 0, 0)
    al.setSpacing(6)

    btn_start   = QPushButton("Start")
    btn_stop    = QPushButton("Stop")
    btn_restart = QPushButton("Restart")
    btn_enable  = QPushButton("Enable")
    btn_disable = QPushButton("Disable")

    btn_stop.setStyleSheet("QPushButton{color:#c0392b;font-weight:bold;}")
    btn_disable.setStyleSheet("QPushButton{color:#c0392b;}")

    for b in (btn_start, btn_stop, btn_restart, btn_enable, btn_disable):
        al.addWidget(b)
    al.addStretch()

    module._svc_status_lbl = QLabel("")
    module._svc_status_lbl.setFont(QFont("Arial", 9))
    al.addWidget(module._svc_status_lbl)
    root.addWidget(actions)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["Service", "Active", "Sub-state", "Load", "Description"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    table.setColumnWidth(0, 250)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    table.setColumnWidth(1, 80)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    table.setColumnWidth(2, 90)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
    table.setColumnWidth(3, 70)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setFont(QFont("Arial", 9))
    root.addWidget(table)

    # ── output log ────────────────────────────────────────────────────────────
    module._svc_output = QTextEdit()
    module._svc_output.setReadOnly(True)
    module._svc_output.setMaximumHeight(100)
    module._svc_output.setFont(QFont("Courier", 9))
    module._svc_output.setPlaceholderText("Command output will appear here.")
    root.addWidget(module._svc_output)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _selected_service() -> str | None:
        rows = table.selectedItems()
        if not rows:
            return None
        return table.item(table.currentRow(), 0).text()

    def _apply_filter():
        text = search.text().lower()
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            desc = table.item(r, 4)
            visible = (
                text in (item.text().lower() if item else "")
                or text in (desc.text().lower() if desc else "")
            )
            table.setRowHidden(r, not visible)

    search.textChanged.connect(lambda _: _apply_filter())

    def _populate(rows):
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, (unit, active, sub, load, desc) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(unit))
            active_item = QTableWidgetItem(active)
            if active == "active":
                active_item.setForeground(QColor("#27ae60"))
            else:
                active_item.setForeground(QColor("#c0392b"))
            table.setItem(r, 1, active_item)
            table.setItem(r, 2, QTableWidgetItem(sub))
            table.setItem(r, 3, QTableWidgetItem(load))
            table.setItem(r, 4, QTableWidgetItem(desc))
            table.setRowHeight(r, 22)
        table.setSortingEnabled(True)
        _apply_filter()
        refresh_btn.setEnabled(True)

    def _load():
        refresh_btn.setEnabled(False)
        table.setRowCount(0)
        f = state_filter.currentText().lower()
        threading.Thread(
            target=lambda: module.post_ui_update(
                lambda rows=_load_services(f if f != "all" else ""): _populate(rows)
            ),
            daemon=True,
        ).start()

    refresh_btn.clicked.connect(_load)
    state_filter.currentIndexChanged.connect(lambda _: _load())

    def _action(args):
        svc = _selected_service()
        if not svc:
            module._svc_status_lbl.setText("Select a service first.")
            return
        module._svc_output.clear()
        module._svc_action_sig = _Signals()
        module._svc_action_sig.output.connect(module._svc_output.append)
        module._svc_action_sig.done.connect(lambda rc: (
            module._svc_status_lbl.setText("✓ Done" if rc == 0 else "✗ Failed"),
            _load(),
        ))

        def worker():
            rc, out = _run_systemctl([*args, svc])
            module._svc_action_sig.output.emit(out or "(no output)")
            module._svc_action_sig.done.emit(rc)

        threading.Thread(target=worker, daemon=True).start()

    btn_start.clicked.connect(lambda: _action(["start"]))
    btn_stop.clicked.connect(lambda: _action(["stop"]))
    btn_restart.clicked.connect(lambda: _action(["restart"]))
    btn_enable.clicked.connect(lambda: _action(["enable"]))
    btn_disable.clicked.connect(lambda: _action(["disable"]))

    _load()
