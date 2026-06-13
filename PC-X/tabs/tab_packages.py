"""Package Manager tab for PC-X — BCU-style bulk uninstaller for Linux."""

from __future__ import annotations

import logging
import subprocess
import threading
from typing import List, Tuple

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGroupBox,
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
    QWidget,
    QCheckBox,
)


# ── signals helper so the worker thread can push to the GUI thread ────────────

class _PackageWorkerSignals(QObject):
    packages_loaded = Signal(list)   # list[tuple[name, version, size_kb, desc, orphan]]
    output_line = Signal(str)
    finished = Signal(int)           # returncode


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_packages() -> List[Tuple[str, str, int, str, bool]]:
    """Return (name, version, size_kb, description, is_orphan) for every installed package."""
    packages: List[Tuple[str, str, int, str, bool]] = []

    try:
        result = subprocess.run(
            [
                "dpkg-query", "-W",
                "-f=${Package}\t${Version}\t${Installed-Size}\t"
                "${db:Status-Abbrev}\t${binary:Summary}\n",
            ],
            capture_output=True, text=True, timeout=30,
        )
        for line in result.stdout.splitlines():
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            name, version, size_str, status, desc = parts
            if not status.startswith("ii"):
                continue
            try:
                size_kb = int(size_str.strip())
            except ValueError:
                size_kb = 0
            packages.append((name.strip(), version.strip(), size_kb, desc.strip(), False))
    except Exception as exc:
        logging.warning("dpkg-query failed: %s", exc)

    # Mark orphans — packages apt would auto-remove
    orphans: set[str] = set()
    try:
        ar = subprocess.run(
            ["apt-get", "--dry-run", "autoremove"],
            capture_output=True, text=True, timeout=15,
        )
        for line in ar.stdout.splitlines():
            if line.startswith("Remv "):
                orphans.add(line.split()[1])
    except Exception:
        pass

    return [
        (n, v, s, d, n in orphans)
        for n, v, s, d, _ in packages
    ]


def _format_size(kb: int) -> str:
    if kb >= 1024 * 1024:
        return f"{kb / 1024 / 1024:.1f} GB"
    if kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb} KB"


# ── tab setup ─────────────────────────────────────────────────────────────────

def setup_packages_tab(module) -> None:
    """Set up the Package Manager tab."""
    tab = module.tools_tabs["packages"]
    _sigs: list = []

    root_layout = QVBoxLayout(tab)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    toolbar_layout.setSpacing(8)

    search_box = QLineEdit()
    search_box.setPlaceholderText("Search packages…")
    search_box.setClearButtonEnabled(True)
    search_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    toolbar_layout.addWidget(search_box)

    module._pkg_orphans_only = QCheckBox("Orphans only")
    toolbar_layout.addWidget(module._pkg_orphans_only)

    refresh_btn = QPushButton("Refresh")
    toolbar_layout.addWidget(refresh_btn)

    select_all_btn = QPushButton("Select All")
    toolbar_layout.addWidget(select_all_btn)

    deselect_btn = QPushButton("Deselect All")
    toolbar_layout.addWidget(deselect_btn)

    mark_orphans_btn = QPushButton("Mark Orphans")
    mark_orphans_btn.setToolTip("Check all packages that apt autoremove would remove")
    toolbar_layout.addWidget(mark_orphans_btn)

    remove_btn = QPushButton("Remove Selected")
    remove_btn.setStyleSheet("QPushButton { background-color: #c0392b; color: white; font-weight: bold; }")
    toolbar_layout.addWidget(remove_btn)

    root_layout.addWidget(toolbar)

    # ── summary label ─────────────────────────────────────────────────────────
    module._pkg_summary_label = QLabel("Loading package list…")
    module._pkg_summary_label.setFont(QFont("Arial", 9))
    root_layout.addWidget(module._pkg_summary_label)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["", "Package", "Version", "Size", "Description"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    table.setColumnWidth(0, 28)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
    table.setColumnWidth(1, 220)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
    table.setColumnWidth(2, 160)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
    table.setColumnWidth(3, 90)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.horizontalHeader().setSortIndicator(3, Qt.DescendingOrder)  # default: biggest first
    table.setFont(QFont("Arial", 9))
    root_layout.addWidget(table)

    module._pkg_table = table
    module._pkg_all_rows: List[Tuple[str, str, int, str, bool]] = []

    # ── output log ────────────────────────────────────────────────────────────
    output_group = QGroupBox("Output")
    output_layout = QVBoxLayout(output_group)
    output_layout.setContentsMargins(4, 4, 4, 4)
    module._pkg_output = QTextEdit()
    module._pkg_output.setReadOnly(True)
    module._pkg_output.setMaximumHeight(120)
    module._pkg_output.setFont(QFont("Courier", 9))
    module._pkg_output.setPlaceholderText("Removal output will appear here.")
    output_layout.addWidget(module._pkg_output)
    root_layout.addWidget(output_group)

    # ── wire up ───────────────────────────────────────────────────────────────
    def _apply_filter():
        text = search_box.text().lower()
        orphans_only = module._pkg_orphans_only.isChecked()
        for row in range(table.rowCount()):
            pkg_item = table.item(row, 1)
            desc_item = table.item(row, 4)
            orphan_flag = table.item(row, 1).data(Qt.UserRole + 1) if pkg_item else False
            match = (text in (pkg_item.text().lower() if pkg_item else "")
                     or text in (desc_item.text().lower() if desc_item else ""))
            visible = match and (not orphans_only or orphan_flag)
            table.setRowHidden(row, not visible)
        _update_summary()

    search_box.textChanged.connect(lambda _: _apply_filter())
    module._pkg_orphans_only.stateChanged.connect(lambda _: _apply_filter())

    def _update_summary():
        visible = sum(1 for r in range(table.rowCount()) if not table.isRowHidden(r))
        checked = _checked_packages()
        total_kb = sum(
            (table.item(r, 3).data(Qt.UserRole) or 0) if table.item(r, 3) else 0
            for r in range(table.rowCount())
            if not table.isRowHidden(r)
        )
        checked_kb = sum(
            (table.item(r, 3).data(Qt.UserRole) or 0) if table.item(r, 3) else 0
            for r in _checked_rows()
        )
        module._pkg_summary_label.setText(
            f"Showing {visible} of {table.rowCount()} packages  "
            f"({_format_size(total_kb)} shown)   "
            f"  {len(checked)} selected ({_format_size(checked_kb)})"
        )

    def _populate_table(rows: List[Tuple[str, str, int, str, bool]]):
        module._pkg_all_rows = rows
        table.setSortingEnabled(False)
        try:
            table.itemChanged.disconnect()
        except RuntimeError:
            pass
        table.setRowCount(len(rows))
        for r, (name, version, size_kb, desc, orphan) in enumerate(rows):
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            table.setItem(r, 0, chk)

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole + 1, orphan)
            if orphan:
                name_item.setForeground(QColor("#e67e22"))
                name_item.setToolTip("This package would be removed by apt autoremove")
            table.setItem(r, 1, name_item)

            table.setItem(r, 2, QTableWidgetItem(version))

            size_item = QTableWidgetItem(_format_size(size_kb))
            size_item.setData(Qt.UserRole, size_kb)
            size_item.setData(Qt.DisplayRole, _format_size(size_kb))
            # Store numeric value for proper sorting
            size_item.setData(Qt.UserRole + 2, size_kb)
            table.setItem(r, 3, size_item)

            table.setItem(r, 4, QTableWidgetItem(desc))

            table.setRowHeight(r, 22)

        table.setSortingEnabled(True)
        table.sortByColumn(3, Qt.DescendingOrder)
        _apply_filter()
        table.itemChanged.connect(lambda _: _update_summary())

    def _checked_rows():
        return [
            r for r in range(table.rowCount())
            if table.item(r, 0) and table.item(r, 0).checkState() == Qt.Checked
        ]

    def _checked_packages():
        return [
            table.item(r, 1).text()
            for r in _checked_rows()
            if table.item(r, 1)
        ]

    def _load_in_background():
        refresh_btn.setEnabled(False)
        module._pkg_summary_label.setText("Loading package list…")
        table.setRowCount(0)

        _sigs.append(_PackageWorkerSignals()); signals = _sigs[-1]
        signals.packages_loaded.connect(_populate_table)

        def worker():
            pkgs = _load_packages()
            signals.packages_loaded.emit(pkgs)
            refresh_btn.setEnabled(True)

        threading.Thread(target=worker, daemon=True).start()

    refresh_btn.clicked.connect(_load_in_background)

    select_all_btn.clicked.connect(lambda: _set_all_checked(Qt.Checked))
    deselect_btn.clicked.connect(lambda: _set_all_checked(Qt.Unchecked))

    def _disconnect_item_changed():
        try:
            table.itemChanged.disconnect()
        except RuntimeError:
            pass

    def _set_all_checked(state):
        _disconnect_item_changed()
        for r in range(table.rowCount()):
            if not table.isRowHidden(r) and table.item(r, 0):
                table.item(r, 0).setCheckState(state)
        table.itemChanged.connect(lambda _: _update_summary())
        _update_summary()

    def _mark_orphans():
        _disconnect_item_changed()
        for r in range(table.rowCount()):
            item = table.item(r, 1)
            if item and item.data(Qt.UserRole + 1):
                table.item(r, 0).setCheckState(Qt.Checked)
        table.itemChanged.connect(lambda _: _update_summary())
        _update_summary()

    mark_orphans_btn.clicked.connect(_mark_orphans)

    remove_btn.clicked.connect(lambda: _remove_selected(module))

    def _remove_selected(mod):
        pkgs = _checked_packages()
        if not pkgs:
            QMessageBox.information(tab, "Nothing selected", "Check at least one package to remove.")
            return

        total_kb = sum(
            table.item(r, 3).data(Qt.UserRole) or 0
            for r in _checked_rows()
        )
        reply = QMessageBox.question(
            tab,
            "Confirm Removal",
            f"Remove {len(pkgs)} package(s)?\n\n"
            + "\n".join(f"  • {p}" for p in pkgs[:20])
            + (f"\n  … and {len(pkgs) - 20} more" if len(pkgs) > 20 else "")
            + f"\n\nTotal freed: ~{_format_size(total_kb)}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        remove_btn.setEnabled(False)
        mod._pkg_output.clear()
        mod._pkg_output.append(f"Removing {len(pkgs)} package(s)…\n")

        _sigs.append(_PackageWorkerSignals()); signals = _sigs[-1]
        signals.output_line.connect(mod._pkg_output.append)
        signals.finished.connect(lambda rc: _on_removal_done(rc, pkgs))

        def worker():
            try:
                from core.utils import run_privileged_command
                result = run_privileged_command(
                    ["apt-get", "remove", "--purge", "-y", *pkgs],
                    timeout=300,
                )
                for line in (result.stdout + result.stderr).splitlines():
                    signals.output_line.emit(line)
                signals.finished.emit(result.returncode)
            except Exception as exc:
                signals.output_line.emit(f"Error: {exc}")
                signals.finished.emit(1)

        threading.Thread(target=worker, daemon=True).start()

    def _on_removal_done(returncode: int, removed: List[str]):
        remove_btn.setEnabled(True)
        if returncode == 0:
            module._pkg_output.append("\n✓ Removal complete.")
            names_removed = set(removed)
            rows_to_delete = [
                r for r in range(table.rowCount())
                if table.item(r, 1) and table.item(r, 1).text() in names_removed
            ]
            for r in reversed(rows_to_delete):
                table.removeRow(r)
            _update_summary()
        else:
            module._pkg_output.append(f"\n✗ Removal failed (exit {returncode}).")

    # Initial load
    _load_in_background()
