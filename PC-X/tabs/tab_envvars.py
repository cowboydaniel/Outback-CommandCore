"""Environment Variables tab for PC-X — view/edit /etc/environment and shell profiles."""

from __future__ import annotations

import os
import re
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

ENV_FILES = [
    ("Current session",  None),                                    # os.environ snapshot
    ("/etc/environment", Path("/etc/environment")),
    ("~/.bashrc",        Path.home() / ".bashrc"),
    ("~/.profile",       Path.home() / ".profile"),
    ("~/.bash_profile",  Path.home() / ".bash_profile"),
    ("/etc/profile",     Path("/etc/profile")),
]


class _Signals(QObject):
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


def _parse_env_file(path: Path) -> list[tuple[str, str]]:
    """Extract KEY=VALUE lines from a shell or /etc/environment file."""
    pairs = []
    try:
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # strip leading 'export '
            line = re.sub(r"^export\s+", "", line)
            if "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip("'\"")
                pairs.append((k.strip(), v))
    except Exception:
        pass
    return pairs


def _session_vars() -> list[tuple[str, str]]:
    return sorted(os.environ.items())


def setup_envvars_tab(module) -> None:
    tab = module.mgmt_tabs["env vars"]
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tl = QHBoxLayout(toolbar)
    tl.setContentsMargins(0, 0, 0, 0)
    tl.setSpacing(8)

    source_cb = QComboBox()
    for label, _ in ENV_FILES:
        source_cb.addItem(label)
    source_cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tl.addWidget(source_cb)

    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search…")
    search_edit.setClearButtonEnabled(True)
    search_edit.setFixedWidth(200)
    tl.addWidget(search_edit)

    refresh_btn = QPushButton("Refresh")
    add_btn     = QPushButton("Add / Set")
    del_btn     = QPushButton("Delete")
    del_btn.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (refresh_btn, add_btn, del_btn):
        tl.addWidget(b)

    root.addWidget(toolbar)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["Variable", "Value"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    table.setColumnWidth(0, 220)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setFont(QFont("Courier", 9))
    root.addWidget(table)

    module._env_output = QTextEdit()
    module._env_output.setReadOnly(True)
    module._env_output.setMaximumHeight(72)
    module._env_output.setFont(QFont("Courier", 9))
    module._env_output.setPlaceholderText("Output will appear here.")
    root.addWidget(module._env_output)

    module._env_rows: list[tuple[str, str]] = []

    def _log(msg):
        module._env_output.append(msg)

    def _populate(pairs: list[tuple[str, str]]):
        module._env_rows = pairs
        _apply_filter()

    def _apply_filter():
        text = search_edit.text().lower()
        table.setSortingEnabled(False)
        pairs = module._env_rows
        filtered = [(k, v) for k, v in pairs if text in k.lower() or text in v.lower()]
        table.setRowCount(len(filtered))
        for r, (k, v) in enumerate(filtered):
            table.setItem(r, 0, QTableWidgetItem(k))
            table.setItem(r, 1, QTableWidgetItem(v))
            table.setRowHeight(r, 22)
        table.setSortingEnabled(True)
        refresh_btn.setEnabled(True)

    search_edit.textChanged.connect(lambda _: _apply_filter())

    def _current_source():
        idx = source_cb.currentIndex()
        return ENV_FILES[idx][1]  # Path or None

    def _load():
        refresh_btn.setEnabled(False)
        src = _current_source()
        if src is None:
            _populate(_session_vars())
        else:
            _populate(_parse_env_file(src))

    def _is_readonly():
        src = _current_source()
        return src is None  # session is always read-only

    refresh_btn.clicked.connect(_load)
    source_cb.currentIndexChanged.connect(lambda _: _load())

    def _selected_key():
        row = table.currentRow()
        item = table.item(row, 0)
        return item.text() if item else None

    def _add_or_set():
        src = _current_source()
        if src is None:
            QMessageBox.information(tab, "Read Only",
                                    "Current session variables are read-only.\nSelect a file source to edit.")
            return
        dlg = QDialog(tab)
        dlg.setWindowTitle("Add / Set Variable")
        fl = QFormLayout(dlg)
        key_edit = QLineEdit()
        val_edit = QLineEdit()
        selected = _selected_key()
        if selected:
            key_edit.setText(selected)
            row = table.currentRow()
            val_item = table.item(row, 1)
            if val_item:
                val_edit.setText(val_item.text())
        fl.addRow("Variable:", key_edit)
        fl.addRow("Value:", val_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        key = key_edit.text().strip()
        val = val_edit.text().strip()
        if not key:
            return
        _write_var(src, key, val)

    def _write_var(src: Path, key: str, val: str):
        try:
            text = src.read_text(errors="replace") if src.exists() else ""
        except Exception:
            text = ""
        lines = text.splitlines()
        pattern = re.compile(rf"^(export\s+)?{re.escape(key)}\s*=")
        new_line = f"{key}={val}"
        replaced = False
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[i] = new_line
                replaced = True
                break
        if not replaced:
            lines.append(new_line)
        new_text = "\n".join(lines) + "\n"

        # use sudo for system files
        needs_priv = not os.access(src, os.W_OK)
        if needs_priv:
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
                tmp.write(new_text)
                tmp_path = tmp.name
            rc, out = _run_priv(["cp", tmp_path, str(src)])
            os.unlink(tmp_path)
        else:
            try:
                src.write_text(new_text)
                rc, out = 0, ""
            except Exception as exc:
                rc, out = 1, str(exc)

        _log(f"Set {key}={val} in {src}" if rc == 0 else f"Failed: {out}")
        _load()

    def _delete_var():
        src = _current_source()
        if src is None:
            QMessageBox.information(tab, "Read Only", "Current session is read-only.")
            return
        key = _selected_key()
        if not key:
            _log("Select a variable first.")
            return
        if QMessageBox.question(tab, "Confirm", f"Remove '{key}' from {src}?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            text = src.read_text(errors="replace")
        except Exception:
            _log("Cannot read file.")
            return
        pattern = re.compile(rf"^(export\s+)?{re.escape(key)}\s*=.*$", re.MULTILINE)
        new_text = pattern.sub("", text)
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)

        needs_priv = not os.access(src, os.W_OK)
        if needs_priv:
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
                tmp.write(new_text)
                tmp_path = tmp.name
            rc, out = _run_priv(["cp", tmp_path, str(src)])
            os.unlink(tmp_path)
        else:
            try:
                src.write_text(new_text)
                rc, out = 0, ""
            except Exception as exc:
                rc, out = 1, str(exc)

        _log(f"Removed '{key}' from {src}" if rc == 0 else f"Failed: {out}")
        _load()

    add_btn.clicked.connect(_add_or_set)
    del_btn.clicked.connect(_delete_var)

    _load()
