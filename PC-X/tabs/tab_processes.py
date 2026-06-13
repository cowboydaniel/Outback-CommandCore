"""Process Manager tab for PC-X — interactive process list with kill/renice."""

from __future__ import annotations

import os
import signal
import subprocess
import threading

import psutil
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

SIGNALS = [
    ("SIGTERM (15) — graceful quit", signal.SIGTERM),
    ("SIGKILL (9)  — force kill",    signal.SIGKILL),
    ("SIGINT  (2)  — interrupt",     signal.SIGINT),
    ("SIGHUP  (1)  — reload",        signal.SIGHUP),
    ("SIGSTOP (19) — pause",         signal.SIGSTOP),
    ("SIGCONT (18) — resume",        signal.SIGCONT),
]


class _Signals(QObject):
    loaded = Signal(list)


def _load_procs(filter_user: str, filter_text: str) -> list:
    rows = []
    my_pid = os.getpid()
    try:
        for p in psutil.process_iter(
            ["pid", "name", "username", "status", "cpu_percent",
             "memory_info", "nice", "cmdline"]
        ):
            try:
                info = p.info
                if filter_user and filter_user != "All" and info["username"] != filter_user:
                    continue
                name = info["name"] or ""
                cmd = " ".join(info["cmdline"] or []) or name
                if filter_text and filter_text.lower() not in name.lower() \
                        and filter_text.lower() not in cmd.lower():
                    continue
                mem_mb = (info["memory_info"].rss / (1024 * 1024)) if info["memory_info"] else 0
                rows.append((
                    info["pid"],
                    name,
                    info["username"] or "",
                    info["status"] or "",
                    round(info["cpu_percent"] or 0, 1),
                    round(mem_mb, 1),
                    info["nice"] if info["nice"] is not None else 0,
                    cmd,
                    info["pid"] == my_pid,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    rows.sort(key=lambda r: r[4], reverse=True)
    return rows


def _run_priv(args, timeout=15):
    try:
        result = subprocess.run(["sudo", "-n", *args], capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 and "sudo" in result.stderr.lower():
            from core.utils import run_privileged_command
            result = run_privileged_command(args, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def setup_processes_tab(module) -> None:
    tab = module.tools_tabs["processes"]
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
    search_edit.setPlaceholderText("Filter by name or command…")
    search_edit.setClearButtonEnabled(True)
    search_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tl.addWidget(search_edit)

    tl.addWidget(QLabel("User:"))
    user_cb = QComboBox()
    users = sorted({p.username() for p in psutil.process_iter(["username"])
                    if p.info.get("username")})
    user_cb.addItems(["All"] + users)
    tl.addWidget(user_cb)

    refresh_btn = QPushButton("Refresh")
    tl.addWidget(refresh_btn)

    auto_chk_lbl = QLabel("Auto (3 s)")
    tl.addWidget(auto_chk_lbl)
    from PySide6.QtWidgets import QCheckBox
    auto_chk = QCheckBox()
    auto_chk.setChecked(True)
    tl.addWidget(auto_chk)

    root.addWidget(toolbar)

    # ── action buttons ────────────────────────────────────────────────────────
    act_row = QFrame()
    al = QHBoxLayout(act_row)
    al.setContentsMargins(0, 0, 0, 0)
    al.setSpacing(6)

    btn_kill   = QPushButton("Send Signal…")
    btn_renice = QPushButton("Renice…")
    btn_kill.setStyleSheet("QPushButton{color:#c0392b;font-weight:bold;}")
    for b in (btn_kill, btn_renice):
        al.addWidget(b)
    al.addStretch()

    module._proc_count_lbl = QLabel("")
    module._proc_count_lbl.setFont(QFont("Arial", 9))
    al.addWidget(module._proc_count_lbl)
    root.addWidget(act_row)

    # ── table ─────────────────────────────────────────────────────────────────
    table = QTableWidget()
    table.setColumnCount(8)
    table.setHorizontalHeaderLabels(["PID", "Name", "User", "Status", "CPU %", "MEM MB", "Nice", "Command"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    table.setColumnWidth(0, 60)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
    table.setColumnWidth(1, 160)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
    table.setColumnWidth(2, 100)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
    table.setColumnWidth(3, 80)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
    table.setColumnWidth(4, 65)
    table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
    table.setColumnWidth(5, 75)
    table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
    table.setColumnWidth(6, 50)
    table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setFont(QFont("Arial", 9))
    root.addWidget(table)

    module._proc_output = QTextEdit()
    module._proc_output.setReadOnly(True)
    module._proc_output.setMaximumHeight(60)
    module._proc_output.setFont(QFont("Courier", 9))
    module._proc_output.setPlaceholderText("Output will appear here.")
    root.addWidget(module._proc_output)

    module._proc_rows: list = []

    def _populate(rows):
        module._proc_rows = rows
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, (pid, name, user, status, cpu, mem, nice, cmd, is_self) in enumerate(rows):
            pid_item = QTableWidgetItem(str(pid))
            pid_item.setData(Qt.UserRole, pid)
            table.setItem(r, 0, pid_item)
            table.setItem(r, 1, QTableWidgetItem(name))
            table.setItem(r, 2, QTableWidgetItem(user))

            status_item = QTableWidgetItem(status)
            if status == "running":
                status_item.setForeground(QColor("#27ae60"))
            elif status in ("zombie", "dead"):
                status_item.setForeground(QColor("#e74c3c"))
            table.setItem(r, 3, status_item)

            cpu_item = QTableWidgetItem(f"{cpu:.1f}")
            cpu_item.setData(Qt.UserRole, cpu)
            if cpu > 50:
                cpu_item.setForeground(QColor("#e74c3c"))
            elif cpu > 20:
                cpu_item.setForeground(QColor("#e67e22"))
            table.setItem(r, 4, cpu_item)

            mem_item = QTableWidgetItem(f"{mem:.1f}")
            mem_item.setData(Qt.UserRole, mem)
            table.setItem(r, 5, mem_item)

            table.setItem(r, 6, QTableWidgetItem(str(nice)))
            table.setItem(r, 7, QTableWidgetItem(cmd))
            table.setRowHeight(r, 22)

            if is_self:
                for c in range(8):
                    item = table.item(r, c)
                    if item:
                        item.setForeground(QColor("#7f8c8d"))

        table.setSortingEnabled(True)
        module._proc_count_lbl.setText(f"{len(rows)} processes")
        refresh_btn.setEnabled(True)

    def _load():
        refresh_btn.setEnabled(False)
        fu = user_cb.currentText()
        ft = search_edit.text()
        _sigs.append(_Signals())
        _sigs[-1].loaded.connect(_populate)
        threading.Thread(
            target=lambda: _sigs[-1].loaded.emit(_load_procs(fu, ft)),
            daemon=True,
        ).start()

    def _selected_pid() -> int | None:
        row = table.currentRow()
        item = table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _send_signal():
        pid = _selected_pid()
        if pid is None:
            module._proc_output.setText("Select a process first.")
            return
        dlg = QDialog(tab)
        dlg.setWindowTitle(f"Send Signal to PID {pid}")
        fl = QFormLayout(dlg)
        sig_cb = QComboBox()
        for label, _ in SIGNALS:
            sig_cb.addItem(label)
        fl.addRow("Signal:", sig_cb)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        _, signum = SIGNALS[sig_cb.currentIndex()]
        try:
            os.kill(pid, signum)
            module._proc_output.append(f"Sent {signum.name} to PID {pid}.")
        except PermissionError:
            rc, out = _run_priv(["kill", f"-{signum.value}", str(pid)])
            module._proc_output.append(out or ("Done." if rc == 0 else "Failed."))
        except ProcessLookupError:
            module._proc_output.append(f"PID {pid} no longer exists.")
        _load()

    def _renice():
        pid = _selected_pid()
        if pid is None:
            module._proc_output.setText("Select a process first.")
            return
        row = table.currentRow()
        cur_nice = int(table.item(row, 6).text()) if table.item(row, 6) else 0
        dlg = QDialog(tab)
        dlg.setWindowTitle(f"Renice PID {pid}")
        fl = QFormLayout(dlg)
        nice_spin = QSpinBox()
        nice_spin.setRange(-20, 19)
        nice_spin.setValue(cur_nice)
        nice_spin.setToolTip("-20 = highest priority, 19 = lowest")
        fl.addRow("Nice value:", nice_spin)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        new_nice = nice_spin.value()
        try:
            os.setpriority(os.PRIO_PROCESS, pid, new_nice)
            module._proc_output.append(f"PID {pid} nice set to {new_nice}.")
        except PermissionError:
            rc, out = _run_priv(["renice", "-n", str(new_nice), "-p", str(pid)])
            module._proc_output.append(out or ("Done." if rc == 0 else "Failed."))
        except ProcessLookupError:
            module._proc_output.append(f"PID {pid} no longer exists.")
        _load()

    btn_kill.clicked.connect(_send_signal)
    btn_renice.clicked.connect(_renice)
    refresh_btn.clicked.connect(_load)
    search_edit.textChanged.connect(lambda _: _load())
    user_cb.currentIndexChanged.connect(lambda _: _load())

    # ── auto-refresh timer ────────────────────────────────────────────────────
    module._proc_timer = QTimer()
    module._proc_timer.setInterval(3000)
    module._proc_timer.timeout.connect(_load)

    def _toggle_auto(state):
        if state:
            module._proc_timer.start()
        else:
            module._proc_timer.stop()

    auto_chk.stateChanged.connect(_toggle_auto)
    module._proc_timer.start()

    _load()
