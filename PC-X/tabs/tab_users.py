"""User & Group Manager tab for PC-X."""

from __future__ import annotations

import grp
import pwd
import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)


class _Signals(QObject):
    done = Signal(int, str)


def _run_priv(args, timeout=15):
    try:
        result = subprocess.run(
            ["sudo", "-n", *args],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0 and "sudo" in result.stderr.lower():
            from core.utils import run_privileged_command
            result = run_privileged_command(args, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def _last_login(username: str) -> str:
    try:
        r = subprocess.run(
            ["lastlog", "-u", username],
            capture_output=True, text=True, timeout=5,
        )
        lines = r.stdout.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split(None, 1)
            return parts[1].strip() if len(parts) > 1 else "Never"
    except Exception:
        pass
    return ""


def _is_locked(username: str) -> bool:
    try:
        r = subprocess.run(
            ["passwd", "-S", username],
            capture_output=True, text=True, timeout=5,
        )
        return " L " in r.stdout
    except Exception:
        return False


def _load_users():
    rows = []
    for p in sorted(pwd.getpwall(), key=lambda x: x.pw_uid):
        locked = _is_locked(p.pw_name)
        rows.append((
            p.pw_name, str(p.pw_uid), str(p.pw_gid),
            p.pw_dir, p.pw_shell, locked,
        ))
    return rows


def _load_groups():
    rows = []
    for g in sorted(grp.getgrall(), key=lambda x: x.gr_gid):
        rows.append((g.gr_name, str(g.gr_gid), ", ".join(g.gr_mem)))
    return rows


def setup_users_tab(module) -> None:
    tab = module.mgmt_tabs["users"]
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    subtabs = QTabWidget()
    root.addWidget(subtabs)

    users_widget = QWidget()
    groups_widget = QWidget()
    subtabs.addTab(users_widget, "Users")
    subtabs.addTab(groups_widget, "Groups")

    # ── output shared ─────────────────────────────────────────────────────────
    module._usr_output = QTextEdit()
    module._usr_output.setReadOnly(True)
    module._usr_output.setMaximumHeight(80)
    module._usr_output.setFont(QFont("Courier", 9))
    module._usr_output.setPlaceholderText("Command output will appear here.")
    root.addWidget(module._usr_output)

    # ══════════════════════════════════════════════════════════════════════════
    # USERS subtab
    # ══════════════════════════════════════════════════════════════════════════
    ul = QVBoxLayout(users_widget)
    ul.setContentsMargins(4, 4, 4, 4)

    # toolbar
    utb = QFrame()
    utbl = QHBoxLayout(utb)
    utbl.setContentsMargins(0, 0, 0, 0)
    u_search = QLineEdit()
    u_search.setPlaceholderText("Search users…")
    u_search.setClearButtonEnabled(True)
    utbl.addWidget(u_search)
    u_refresh = QPushButton("Refresh")
    u_add     = QPushButton("Add User")
    u_del     = QPushButton("Delete User")
    u_lock    = QPushButton("Lock / Unlock")
    u_passwd  = QPushButton("Change Password")
    u_del.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (u_refresh, u_add, u_del, u_lock, u_passwd):
        utbl.addWidget(b)
    ul.addWidget(utb)

    u_table = QTableWidget()
    u_table.setColumnCount(6)
    u_table.setHorizontalHeaderLabels(["Username", "UID", "GID", "Home", "Shell", "Locked"])
    u_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    u_table.setColumnWidth(0, 140)
    for col in (1, 2):
        u_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
        u_table.setColumnWidth(col, 55)
    u_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
    u_table.setColumnWidth(3, 180)
    u_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
    u_table.setColumnWidth(4, 120)
    u_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
    u_table.setColumnWidth(5, 60)
    u_table.verticalHeader().setVisible(False)
    u_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    u_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    u_table.setSelectionMode(QAbstractItemView.SingleSelection)
    u_table.setAlternatingRowColors(True)
    u_table.setFont(QFont("Arial", 9))
    ul.addWidget(u_table)

    def _populate_users(rows):
        u_table.setSortingEnabled(False)
        u_table.setRowCount(len(rows))
        for r, (name, uid, gid, home, shell, locked) in enumerate(rows):
            u_table.setItem(r, 0, QTableWidgetItem(name))
            u_table.setItem(r, 1, QTableWidgetItem(uid))
            u_table.setItem(r, 2, QTableWidgetItem(gid))
            u_table.setItem(r, 3, QTableWidgetItem(home))
            u_table.setItem(r, 4, QTableWidgetItem(shell))
            lock_item = QTableWidgetItem("Yes" if locked else "No")
            if locked:
                lock_item.setForeground(QColor("#c0392b"))
            u_table.setItem(r, 5, lock_item)
            u_table.setRowHeight(r, 22)
        u_table.setSortingEnabled(True)
        _filter_users()
        u_refresh.setEnabled(True)

    def _filter_users():
        text = u_search.text().lower()
        for r in range(u_table.rowCount()):
            item = u_table.item(r, 0)
            u_table.setRowHidden(r, text not in (item.text().lower() if item else ""))

    u_search.textChanged.connect(lambda _: _filter_users())

    def _reload_users():
        u_refresh.setEnabled(False)
        threading.Thread(
            target=lambda: module.post_ui_update(lambda rows=_load_users(): _populate_users(rows)),
            daemon=True,
        ).start()

    u_refresh.clicked.connect(_reload_users)

    def _selected_user():
        row = u_table.currentRow()
        if row < 0:
            return None
        return u_table.item(row, 0).text()

    def _run_and_refresh(args, msg=None):
        if msg and QMessageBox.question(tab, "Confirm", msg,
                                        QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        module._usr_output.clear()
        sig = _Signals()
        sig.done.connect(lambda rc, out: (
            module._usr_output.append(out or "(done)"),
            _reload_users(),
        ))
        def worker():
            rc, out = _run_priv(args)
            sig.done.emit(rc, out)
        threading.Thread(target=worker, daemon=True).start()

    def _add_user():
        dlg = QDialog(tab)
        dlg.setWindowTitle("Add User")
        fl = QFormLayout(dlg)
        name_edit = QLineEdit()
        home_edit = QLineEdit()
        shell_edit = QLineEdit()
        shell_edit.setText("/bin/bash")
        create_home = QCheckBox("Create home directory")
        create_home.setChecked(True)
        fl.addRow("Username:", name_edit)
        fl.addRow("Home directory (optional):", home_edit)
        fl.addRow("Shell:", shell_edit)
        fl.addRow("", create_home)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        uname = name_edit.text().strip()
        if not uname:
            return
        args = ["useradd"]
        if create_home.isChecked():
            args.append("-m")
        if home_edit.text().strip():
            args += ["-d", home_edit.text().strip()]
        if shell_edit.text().strip():
            args += ["-s", shell_edit.text().strip()]
        args.append(uname)
        _run_and_refresh(args)

    def _delete_user():
        uname = _selected_user()
        if not uname:
            module._usr_output.setText("Select a user first.")
            return
        _run_and_refresh(["userdel", "-r", uname],
                         f"Delete user '{uname}' and their home directory?")

    def _toggle_lock():
        uname = _selected_user()
        if not uname:
            module._usr_output.setText("Select a user first.")
            return
        locked = _is_locked(uname)
        args = ["passwd", "-u" if locked else "-l", uname]
        _run_and_refresh(args, f"{'Unlock' if locked else 'Lock'} account '{uname}'?")

    def _change_password():
        uname = _selected_user()
        if not uname:
            module._usr_output.setText("Select a user first.")
            return
        dlg = QDialog(tab)
        dlg.setWindowTitle(f"Change Password — {uname}")
        fl = QFormLayout(dlg)
        pw1 = QLineEdit()
        pw1.setEchoMode(QLineEdit.Password)
        pw2 = QLineEdit()
        pw2.setEchoMode(QLineEdit.Password)
        fl.addRow("New password:", pw1)
        fl.addRow("Confirm:", pw2)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        if pw1.text() != pw2.text():
            QMessageBox.warning(tab, "Mismatch", "Passwords do not match.")
            return
        if not pw1.text():
            return
        module._usr_output.clear()
        sig = _Signals()
        sig.done.connect(lambda rc, out: module._usr_output.append(
            "Password changed." if rc == 0 else f"Failed: {out}"
        ))
        pw = pw1.text()
        def worker():
            try:
                from core.utils import run_privileged_command
                result = run_privileged_command(
                    ["chpasswd"],
                    timeout=10,
                )
                # chpasswd reads "user:password" from stdin — workaround via bash
                r2 = subprocess.run(
                    ["bash", "-c", f"echo '{uname}:{pw}' | sudo -n chpasswd"],
                    capture_output=True, text=True, timeout=10,
                )
                sig.done.emit(r2.returncode, (r2.stdout + r2.stderr).strip())
            except Exception as exc:
                sig.done.emit(1, str(exc))
        threading.Thread(target=worker, daemon=True).start()

    u_add.clicked.connect(_add_user)
    u_del.clicked.connect(_delete_user)
    u_lock.clicked.connect(_toggle_lock)
    u_passwd.clicked.connect(_change_password)

    # ══════════════════════════════════════════════════════════════════════════
    # GROUPS subtab
    # ══════════════════════════════════════════════════════════════════════════
    gl = QVBoxLayout(groups_widget)
    gl.setContentsMargins(4, 4, 4, 4)

    gtb = QFrame()
    gtbl = QHBoxLayout(gtb)
    gtbl.setContentsMargins(0, 0, 0, 0)
    g_search = QLineEdit()
    g_search.setPlaceholderText("Search groups…")
    g_search.setClearButtonEnabled(True)
    gtbl.addWidget(g_search)
    g_refresh = QPushButton("Refresh")
    g_add     = QPushButton("Add Group")
    g_del     = QPushButton("Delete Group")
    g_del.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (g_refresh, g_add, g_del):
        gtbl.addWidget(b)
    gl.addWidget(gtb)

    g_table = QTableWidget()
    g_table.setColumnCount(3)
    g_table.setHorizontalHeaderLabels(["Group", "GID", "Members"])
    g_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    g_table.setColumnWidth(0, 180)
    g_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    g_table.setColumnWidth(1, 60)
    g_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
    g_table.verticalHeader().setVisible(False)
    g_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    g_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    g_table.setSelectionMode(QAbstractItemView.SingleSelection)
    g_table.setAlternatingRowColors(True)
    g_table.setFont(QFont("Arial", 9))
    gl.addWidget(g_table)

    def _populate_groups(rows):
        g_table.setRowCount(len(rows))
        for r, (name, gid, members) in enumerate(rows):
            g_table.setItem(r, 0, QTableWidgetItem(name))
            g_table.setItem(r, 1, QTableWidgetItem(gid))
            g_table.setItem(r, 2, QTableWidgetItem(members))
            g_table.setRowHeight(r, 22)
        _filter_groups()
        g_refresh.setEnabled(True)

    def _filter_groups():
        text = g_search.text().lower()
        for r in range(g_table.rowCount()):
            item = g_table.item(r, 0)
            g_table.setRowHidden(r, text not in (item.text().lower() if item else ""))

    g_search.textChanged.connect(lambda _: _filter_groups())

    def _reload_groups():
        g_refresh.setEnabled(False)
        threading.Thread(
            target=lambda: module.post_ui_update(lambda rows=_load_groups(): _populate_groups(rows)),
            daemon=True,
        ).start()

    g_refresh.clicked.connect(_reload_groups)

    def _selected_group():
        row = g_table.currentRow()
        return g_table.item(row, 0).text() if row >= 0 else None

    def _add_group():
        name, ok = QLineEdit.getText if False else (None, False)
        dlg = QDialog(tab)
        dlg.setWindowTitle("Add Group")
        fl = QFormLayout(dlg)
        gname_edit = QLineEdit()
        fl.addRow("Group name:", gname_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        gname = gname_edit.text().strip()
        if not gname:
            return
        sig = _Signals()
        sig.done.connect(lambda rc, out: (
            module._usr_output.append(out or "(done)"),
            _reload_groups(),
        ))
        def worker():
            rc, out = _run_priv(["groupadd", gname])
            sig.done.emit(rc, out)
        threading.Thread(target=worker, daemon=True).start()

    def _delete_group():
        gname = _selected_group()
        if not gname:
            module._usr_output.setText("Select a group first.")
            return
        if QMessageBox.question(tab, "Confirm", f"Delete group '{gname}'?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        sig = _Signals()
        sig.done.connect(lambda rc, out: (
            module._usr_output.append(out or "(done)"),
            _reload_groups(),
        ))
        def worker():
            rc, out = _run_priv(["groupdel", gname])
            sig.done.emit(rc, out)
        threading.Thread(target=worker, daemon=True).start()

    g_add.clicked.connect(_add_group)
    g_del.clicked.connect(_delete_group)

    # Initial load
    _reload_users()
    _reload_groups()
