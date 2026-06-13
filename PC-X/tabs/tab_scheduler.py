"""Scheduled Tasks tab for PC-X — crontab viewer and editor."""

from __future__ import annotations

import getpass
import os
import subprocess
import tempfile
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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
)

CRON_DIRS = [
    ("/etc/cron.d",       "cron.d"),
    ("/etc/cron.daily",   "daily"),
    ("/etc/cron.hourly",  "hourly"),
    ("/etc/cron.weekly",  "weekly"),
    ("/etc/cron.monthly", "monthly"),
]

SCHEDULE_PRESETS = [
    ("Custom", ""),
    ("Every minute",      "* * * * *"),
    ("Every hour",        "0 * * * *"),
    ("Every day at midnight", "0 0 * * *"),
    ("Every day at noon", "0 12 * * *"),
    ("Every week (Sun midnight)", "0 0 * * 0"),
    ("Every month (1st)",  "0 0 1 * *"),
    ("Every reboot",       "@reboot"),
]


class _Signals(QObject):
    loaded = Signal(list)
    done = Signal(int, str)


def _parse_crontab(text: str, source: str) -> list:
    jobs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 5)
        if len(parts) >= 6 and not line.startswith("@"):
            schedule = " ".join(parts[:5])
            command = parts[5]
        elif line.startswith("@") and len(parts) >= 2:
            schedule = parts[0]
            command = " ".join(parts[1:])
        else:
            continue
        jobs.append((schedule, command, source, line))
    return jobs


def _load_all_jobs(user: str) -> list:
    jobs = []

    # User crontab
    try:
        cmd = ["crontab", "-l"] if user == getpass.getuser() else ["sudo", "-n", "crontab", "-u", user, "-l"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            jobs += _parse_crontab(r.stdout, f"crontab ({user})")
    except Exception:
        pass

    # System cron directories
    for path, label in CRON_DIRS:
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            fpath = os.path.join(path, fname)
            try:
                with open(fpath, "r", errors="replace") as f:
                    jobs += _parse_crontab(f.read(), f"{label}/{fname}")
            except Exception:
                pass

    return jobs


def _write_crontab(user: str, lines: list) -> tuple[int, str]:
    content = "\n".join(lines) + "\n"
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        if user == getpass.getuser():
            r = subprocess.run(["crontab", tmp_path], capture_output=True, text=True, timeout=10)
        else:
            r = subprocess.run(
                ["sudo", "-n", "crontab", "-u", user, tmp_path],
                capture_output=True, text=True, timeout=10,
            )
        os.unlink(tmp_path)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def _get_crontab_lines(user: str) -> list:
    try:
        cmd = ["crontab", "-l"] if user == getpass.getuser() else ["sudo", "-n", "crontab", "-u", user, "-l"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.splitlines()
    except Exception:
        pass
    return []


def setup_scheduler_tab(module) -> None:
    tab = module.mgmt_tabs["scheduler"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── toolbar ───────────────────────────────────────────────────────────────
    toolbar = QFrame()
    tbl = QHBoxLayout(toolbar)
    tbl.setContentsMargins(0, 0, 0, 0)

    tbl.addWidget(QLabel("User:"))
    user_cb = QComboBox()
    try:
        users = [p.split(":")[0] for p in open("/etc/passwd").read().splitlines()
                 if not p.startswith("#")]
    except Exception:
        users = [getpass.getuser()]
    user_cb.addItems(users)
    # Default to current user
    try:
        idx = users.index(getpass.getuser())
        user_cb.setCurrentIndex(idx)
    except ValueError:
        pass
    tbl.addWidget(user_cb)

    refresh_btn = QPushButton("Refresh")
    tbl.addWidget(refresh_btn)
    tbl.addStretch()
    root.addWidget(toolbar)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(3)
    table.setHorizontalHeaderLabels(["Schedule", "Command", "Source"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    table.setColumnWidth(0, 160)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
    table.setColumnWidth(2, 160)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setFont(QFont("Arial", 9))
    root.addWidget(table)

    module._sched_raw: list = []  # raw (schedule, cmd, source, original_line)

    def _populate(jobs):
        module._sched_raw = jobs
        table.setSortingEnabled(False)
        table.setRowCount(len(jobs))
        for r, (sched, cmd, src, _) in enumerate(jobs):
            table.setItem(r, 0, QTableWidgetItem(sched))
            table.setItem(r, 1, QTableWidgetItem(cmd))
            table.setItem(r, 2, QTableWidgetItem(src))
            table.setRowHeight(r, 22)
        table.setSortingEnabled(True)
        refresh_btn.setEnabled(True)

    def _reload():
        refresh_btn.setEnabled(False)
        user = user_cb.currentText()
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.loaded.connect(_populate)
        threading.Thread(
            target=lambda: sig.loaded.emit(_load_all_jobs(user)),
            daemon=True,
        ).start()

    refresh_btn.clicked.connect(_reload)
    user_cb.currentIndexChanged.connect(lambda _: _reload())

    # ── add / edit / delete ───────────────────────────────────────────────────
    btn_row = QFrame()
    brl = QHBoxLayout(btn_row)
    brl.setContentsMargins(0, 0, 0, 0)
    add_btn = QPushButton("Add Job")
    edit_btn = QPushButton("Edit Job")
    del_btn = QPushButton("Delete Job")
    del_btn.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (add_btn, edit_btn, del_btn):
        brl.addWidget(b)
    brl.addStretch()
    root.addWidget(btn_row)

    module._sched_output = QTextEdit()
    module._sched_output.setReadOnly(True)
    module._sched_output.setMaximumHeight(80)
    module._sched_output.setFont(QFont("Courier", 9))
    module._sched_output.setPlaceholderText("Output will appear here.")
    root.addWidget(module._sched_output)

    def _job_dialog(title, schedule="", command="") -> tuple[str, str] | None:
        dlg = QDialog(tab)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(500)
        fl = QFormLayout(dlg)

        preset_cb = QComboBox()
        for label, _ in SCHEDULE_PRESETS:
            preset_cb.addItem(label)
        fl.addRow("Preset:", preset_cb)

        sched_edit = QLineEdit(schedule)
        sched_edit.setPlaceholderText("e.g. 0 * * * *  or  @reboot")
        fl.addRow("Schedule:", sched_edit)

        cmd_edit = QLineEdit(command)
        cmd_edit.setPlaceholderText("Full command to run")
        fl.addRow("Command:", cmd_edit)

        def _apply_preset(idx):
            val = SCHEDULE_PRESETS[idx][1]
            if val:
                sched_edit.setText(val)

        preset_cb.currentIndexChanged.connect(_apply_preset)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)

        if dlg.exec() != QDialog.Accepted:
            return None
        s = sched_edit.text().strip()
        c = cmd_edit.text().strip()
        if not s or not c:
            return None
        return s, c

    def _selected_row():
        r = table.currentRow()
        return r if r >= 0 else None

    def _add_job():
        result = _job_dialog("Add Cron Job")
        if not result:
            return
        sched, cmd = result
        user = user_cb.currentText()
        lines = _get_crontab_lines(user)
        lines.append(f"{sched} {cmd}")
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (
            module._sched_output.append("Job added." if rc == 0 else f"Failed: {out}"),
            _reload(),
        ))
        threading.Thread(
            target=lambda: sig.done.emit(*_write_crontab(user, lines)),
            daemon=True,
        ).start()

    def _edit_job():
        r = _selected_row()
        if r is None:
            module._sched_output.setText("Select a job first.")
            return
        sched, cmd, src, orig = module._sched_raw[r]
        if not src.startswith("crontab"):
            QMessageBox.information(tab, "Read Only",
                                    f"'{src}' is a system cron file — edit it manually.")
            return
        result = _job_dialog("Edit Cron Job", sched, cmd)
        if not result:
            return
        new_sched, new_cmd = result
        user = user_cb.currentText()
        lines = _get_crontab_lines(user)
        new_lines = [f"{new_sched} {new_cmd}" if l.strip() == orig.strip() else l
                     for l in lines]
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (
            module._sched_output.append("Job updated." if rc == 0 else f"Failed: {out}"),
            _reload(),
        ))
        threading.Thread(
            target=lambda: sig.done.emit(*_write_crontab(user, new_lines)),
            daemon=True,
        ).start()

    def _delete_job():
        r = _selected_row()
        if r is None:
            module._sched_output.setText("Select a job first.")
            return
        sched, cmd, src, orig = module._sched_raw[r]
        if not src.startswith("crontab"):
            QMessageBox.information(tab, "Read Only",
                                    f"'{src}' is a system cron file — edit it manually.")
            return
        if QMessageBox.question(tab, "Confirm", f"Delete job:\n{sched}  {cmd}",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        user = user_cb.currentText()
        lines = _get_crontab_lines(user)
        new_lines = [l for l in lines if l.strip() != orig.strip()]
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (
            module._sched_output.append("Job deleted." if rc == 0 else f"Failed: {out}"),
            _reload(),
        ))
        threading.Thread(
            target=lambda: sig.done.emit(*_write_crontab(user, new_lines)),
            daemon=True,
        ).start()

    add_btn.clicked.connect(_add_job)
    edit_btn.clicked.connect(_edit_job)
    del_btn.clicked.connect(_delete_job)

    _reload()
