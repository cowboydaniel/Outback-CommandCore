"""Kernel Module Manager tab for PC-X — lsmod viewer with load/unload."""

from __future__ import annotations

import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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
)


class _Signals(QObject):
    loaded = Signal(list)
    done = Signal(int, str)


def _run_priv(args, timeout=15):
    try:
        result = subprocess.run(["sudo", "-n", *args], capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 and "sudo" in result.stderr.lower():
            from core.utils import run_privileged_command
            result = run_privileged_command(args, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def _load_modules() -> list:
    rows = []
    try:
        r = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines()[1:]:  # skip header
            parts = line.split(None, 3)
            if len(parts) < 3:
                continue
            name = parts[0]
            size = parts[1]
            used = parts[2]
            used_by = parts[3].strip(" ,") if len(parts) > 3 else ""
            rows.append((name, size, used, used_by))
    except Exception:
        pass
    return rows


def _module_info(name: str) -> str:
    try:
        r = subprocess.run(["modinfo", name], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as exc:
        return str(exc)


def setup_kernelmods_tab(module) -> None:
    tab = module.mgmt_tabs["kernel mods"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tl = QHBoxLayout(toolbar)
    tl.setContentsMargins(0, 0, 0, 0)
    tl.setSpacing(8)

    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search modules…")
    search_edit.setClearButtonEnabled(True)
    search_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tl.addWidget(search_edit)

    refresh_btn = QPushButton("Refresh")
    tl.addWidget(refresh_btn)

    root.addWidget(toolbar)

    # ── action buttons ────────────────────────────────────────────────────────
    act = QFrame()
    al = QHBoxLayout(act)
    al.setContentsMargins(0, 0, 0, 0)
    al.setSpacing(6)

    btn_info   = QPushButton("Module Info")
    btn_load   = QPushButton("Load Module…")
    btn_unload = QPushButton("Unload")
    btn_unload.setStyleSheet("QPushButton{color:#c0392b;font-weight:bold;}")
    for b in (btn_info, btn_load, btn_unload):
        al.addWidget(b)
    al.addStretch()

    module._kmod_count_lbl = QLabel("")
    module._kmod_count_lbl.setFont(QFont("Arial", 9))
    al.addWidget(module._kmod_count_lbl)
    root.addWidget(act)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels(["Module", "Size (bytes)", "Used by #", "Used by"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    table.setColumnWidth(0, 220)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    table.setColumnWidth(1, 110)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    table.setColumnWidth(2, 80)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setFont(QFont("Arial", 9))
    root.addWidget(table)

    # ── info / output pane ────────────────────────────────────────────────────
    module._kmod_output = QTextEdit()
    module._kmod_output.setReadOnly(True)
    module._kmod_output.setMaximumHeight(130)
    module._kmod_output.setFont(QFont("Courier", 9))
    module._kmod_output.setPlaceholderText("Select a module and click Module Info, or use Load/Unload.")
    root.addWidget(module._kmod_output)

    module._kmod_rows: list = []

    def _populate(rows):
        module._kmod_rows = rows
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, (name, size, used, used_by) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(name))
            sz_item = QTableWidgetItem(size)
            try:
                sz_item.setData(Qt.UserRole, int(size))
            except ValueError:
                pass
            table.setItem(r, 1, sz_item)
            table.setItem(r, 2, QTableWidgetItem(used))
            table.setItem(r, 3, QTableWidgetItem(used_by))
            table.setRowHeight(r, 22)
        table.setSortingEnabled(True)
        _apply_filter()
        module._kmod_count_lbl.setText(f"{len(rows)} modules loaded")
        refresh_btn.setEnabled(True)

    def _apply_filter():
        text = search_edit.text().lower()
        visible = 0
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            dep  = table.item(r, 3)
            show = (not text
                    or text in (item.text().lower() if item else "")
                    or text in (dep.text().lower() if dep else ""))
            table.setRowHidden(r, not show)
            if show:
                visible += 1
        module._kmod_count_lbl.setText(
            f"{visible} of {table.rowCount()} modules"
        )

    search_edit.textChanged.connect(lambda _: _apply_filter())

    def _reload():
        refresh_btn.setEnabled(False)
        threading.Thread(
            target=lambda: module.post_ui_update(
                lambda mods=_load_modules(): _populate(mods)
            ),
            daemon=True,
        ).start()

    def _selected_module() -> str | None:
        row = table.currentRow()
        item = table.item(row, 0)
        return item.text() if item else None

    def _show_info():
        name = _selected_module()
        if not name:
            module._kmod_output.setText("Select a module first.")
            return
        module._kmod_output.setText(f"Loading info for '{name}'…")
        threading.Thread(
            target=lambda: module._kmod_output.setText(_module_info(name)),
            daemon=True,
        ).start()

    def _load_module():
        dlg = QDialog(tab)
        dlg.setWindowTitle("Load Kernel Module")
        fl = QFormLayout(dlg)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. loop, nbd, vboxdrv")
        fl.addRow("Module name:", name_edit)
        params_edit = QLineEdit()
        params_edit.setPlaceholderText("Optional parameters, e.g. max_part=8")
        fl.addRow("Parameters:", params_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        name = name_edit.text().strip()
        if not name:
            return
        params = params_edit.text().strip()
        args = ["modprobe", name] + (params.split() if params else [])
        _sigs.append(_Signals())
        sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (
            module._kmod_output.append(out or ("Loaded." if rc == 0 else "Failed.")),
            _reload(),
        ))
        threading.Thread(
            target=lambda: sig.done.emit(*_run_priv(args)),
            daemon=True,
        ).start()

    def _unload_module():
        name = _selected_module()
        if not name:
            module._kmod_output.setText("Select a module first.")
            return
        row = table.currentRow()
        used = table.item(row, 2).text() if table.item(row, 2) else "0"
        if used != "0":
            if QMessageBox.question(
                tab, "In Use",
                f"Module '{name}' is used by {used} other module(s).\nForce unload anyway?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
        if QMessageBox.question(tab, "Confirm", f"Unload module '{name}'?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        _sigs.append(_Signals())
        sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (
            module._kmod_output.append(out or ("Unloaded." if rc == 0 else "Failed.")),
            _reload(),
        ))
        threading.Thread(
            target=lambda: sig.done.emit(*_run_priv(["rmmod", name])),
            daemon=True,
        ).start()

    btn_info.clicked.connect(_show_info)
    btn_load.clicked.connect(_load_module)
    btn_unload.clicked.connect(_unload_module)
    refresh_btn.clicked.connect(_reload)
    table.doubleClicked.connect(lambda _: _show_info())

    _reload()
