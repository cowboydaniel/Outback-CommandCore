"""Firewall Manager tab for PC-X — ufw rule management."""

from __future__ import annotations

import re
import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)


class _Signals(QObject):
    status_loaded = Signal(str, list)   # status_text, rules
    output = Signal(str)
    done = Signal(int)


def _parse_ufw_status() -> tuple[str, list]:
    """Return (status_line, list_of_rule_dicts)."""
    try:
        result = subprocess.run(
            ["ufw", "status", "numbered"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout
    except Exception as exc:
        return f"Error: {exc}", []

    lines = output.splitlines()
    status = "unknown"
    for line in lines:
        if line.lower().startswith("status:"):
            status = line.split(":", 1)[1].strip()
            break

    rules = []
    rule_re = re.compile(r"^\[\s*(\d+)\]\s+(.+?)\s{2,}(ALLOW|DENY|REJECT|LIMIT)\s+(IN|OUT|FWD)?\s*(.*)")
    for line in lines:
        m = rule_re.match(line)
        if m:
            num, to, action, direction, frm = m.groups()
            rules.append({
                "num": num,
                "to": to.strip(),
                "action": action.strip(),
                "direction": (direction or "").strip(),
                "from": (frm or "Anywhere").strip(),
            })
    return status, rules


def _run_ufw(args: list) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["sudo", "-n", "ufw", *args],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 and "sudo" in result.stderr.lower():
            from core.utils import run_privileged_command
            result = run_privileged_command(["ufw", *args], timeout=15)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def setup_firewall_tab(module) -> None:
    tab = module.mgmt_tabs["firewall"]
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    # ── status bar ────────────────────────────────────────────────────────────
    status_frame = QFrame()
    sf = QHBoxLayout(status_frame)
    sf.setContentsMargins(0, 0, 0, 0)

    module._fw_status_lbl = QLabel("Loading…")
    module._fw_status_lbl.setFont(QFont("Arial", 11, QFont.Bold))
    sf.addWidget(module._fw_status_lbl)
    sf.addStretch()

    btn_enable  = QPushButton("Enable Firewall")
    btn_disable = QPushButton("Disable Firewall")
    btn_reload  = QPushButton("Reload")
    btn_disable.setStyleSheet("QPushButton{color:#c0392b;font-weight:bold;}")
    for b in (btn_enable, btn_disable, btn_reload):
        sf.addWidget(b)
    root.addWidget(status_frame)

    # ── rules table ───────────────────────────────────────────────────────────
    rules_group = QGroupBox("Active Rules")
    rg = QVBoxLayout(rules_group)

    table = QTableWidget()
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["#", "To / Port", "Action", "Direction", "From"])
    table.horizontalHeader().setSectionResizeMode(0, Qt.Fixed if hasattr(Qt, 'Fixed') else QHeaderView.Fixed)
    table.setColumnWidth(0, 36)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
    table.setColumnWidth(1, 200)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    table.setColumnWidth(2, 80)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
    table.setColumnWidth(3, 80)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setFont(QFont("Arial", 9))
    rg.addWidget(table)

    del_btn = QPushButton("Delete Selected Rule")
    del_btn.setStyleSheet("QPushButton{color:#c0392b;}")
    rg.addWidget(del_btn)
    root.addWidget(rules_group)

    # ── add rule form ─────────────────────────────────────────────────────────
    add_group = QGroupBox("Add Rule")
    ag = QGridLayout(add_group)

    ag.addWidget(QLabel("Action:"), 0, 0)
    action_cb = QComboBox()
    action_cb.addItems(["allow", "deny", "reject", "limit"])
    ag.addWidget(action_cb, 0, 1)

    ag.addWidget(QLabel("Direction:"), 0, 2)
    dir_cb = QComboBox()
    dir_cb.addItems(["in", "out"])
    ag.addWidget(dir_cb, 0, 3)

    ag.addWidget(QLabel("Port / Service:"), 1, 0)
    port_edit = QLineEdit()
    port_edit.setPlaceholderText("e.g. 22, 80/tcp, ssh, 8000:9000/tcp")
    ag.addWidget(port_edit, 1, 1, 1, 2)

    ag.addWidget(QLabel("From IP (optional):"), 1, 3)
    from_edit = QLineEdit()
    from_edit.setPlaceholderText("e.g. 192.168.1.0/24")
    ag.addWidget(from_edit, 1, 4)

    add_btn = QPushButton("Add Rule")
    add_btn.setStyleSheet("QPushButton{font-weight:bold;}")
    ag.addWidget(add_btn, 0, 4)
    root.addWidget(add_group)

    # ── output ────────────────────────────────────────────────────────────────
    module._fw_output = QTextEdit()
    module._fw_output.setReadOnly(True)
    module._fw_output.setMaximumHeight(90)
    module._fw_output.setFont(QFont("Courier", 9))
    module._fw_output.setPlaceholderText("Command output will appear here.")
    root.addWidget(module._fw_output)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _populate(status_text, rules):
        module._fw_status_lbl.setText(f"Firewall: {status_text.upper()}")
        colour = "#27ae60" if status_text.lower() == "active" else "#c0392b"
        module._fw_status_lbl.setStyleSheet(f"color:{colour};")

        table.setRowCount(len(rules))
        for r, rule in enumerate(rules):
            table.setItem(r, 0, QTableWidgetItem(rule["num"]))
            table.setItem(r, 1, QTableWidgetItem(rule["to"]))
            action_item = QTableWidgetItem(rule["action"])
            action_item.setForeground(
                QColor("#27ae60") if rule["action"] == "ALLOW" else QColor("#c0392b")
            )
            table.setItem(r, 2, action_item)
            table.setItem(r, 3, QTableWidgetItem(rule["direction"]))
            table.setItem(r, 4, QTableWidgetItem(rule["from"]))
            table.setRowHeight(r, 22)

    def _refresh():
        sig = _Signals()
        sig.status_loaded.connect(_populate)
        threading.Thread(
            target=lambda: sig.status_loaded.emit(*_parse_ufw_status()),
            daemon=True,
        ).start()

    def _run(args, confirm_msg=None):
        if confirm_msg:
            if QMessageBox.question(tab, "Confirm", confirm_msg,
                                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        module._fw_output.clear()
        sig = _Signals()
        sig.output.connect(module._fw_output.append)
        sig.done.connect(lambda rc: _refresh())

        def worker():
            rc, out = _run_ufw(args)
            sig.output.emit(out or "(no output)")
            sig.done.emit(rc)

        threading.Thread(target=worker, daemon=True).start()

    btn_enable.clicked.connect(lambda: _run(["--force", "enable"], "Enable the firewall?"))
    btn_disable.clicked.connect(lambda: _run(["disable"], "Disable the firewall? All traffic will be allowed."))
    btn_reload.clicked.connect(lambda: _run(["reload"]))

    def _delete_selected():
        row = table.currentRow()
        if row < 0:
            module._fw_output.setText("Select a rule to delete.")
            return
        num = table.item(row, 0).text()
        _run(["--force", "delete", num], f"Delete rule #{num}?")

    del_btn.clicked.connect(_delete_selected)

    def _add_rule():
        action = action_cb.currentText()
        direction = dir_cb.currentText()
        port = port_edit.text().strip()
        from_ip = from_edit.text().strip()

        if not port:
            module._fw_output.setText("Enter a port or service name.")
            return

        args = [action, direction]
        if from_ip:
            args += ["from", from_ip]
        args += ["to", "any", "port", port]
        _run(args)
        port_edit.clear()
        from_edit.clear()

    add_btn.clicked.connect(_add_rule)

    _refresh()
