"""Startup Apps tab for PC-X — systemd user services + XDG autostart entries."""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

XDG_AUTOSTART_DIRS = [
    Path("/etc/xdg/autostart"),
    Path.home() / ".config" / "autostart",
]


class _Signals(QObject):
    done = Signal(int, str)
    loaded = Signal(list)


def _run(args, timeout=15):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def _run_priv(args, timeout=15):
    try:
        result = subprocess.run(["sudo", "-n", *args], capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 and "sudo" in result.stderr.lower():
            from core.utils import run_privileged_command
            result = run_privileged_command(args, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


# ── systemd user services ─────────────────────────────────────────────────────

def _load_systemd_user() -> list:
    """Return list of (unit, description, enabled, active) for systemd user services."""
    rows = []
    try:
        r = subprocess.run(
            ["systemctl", "--user", "list-unit-files", "--type=service", "--no-pager", "--no-legend"],
            capture_output=True, text=True, timeout=10,
        )
        unit_states = {}
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                unit_states[parts[0]] = parts[1]

        r2 = subprocess.run(
            ["systemctl", "--user", "list-units", "--type=service", "--all", "--no-pager", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
        active_map = {}
        for line in r2.stdout.splitlines():
            parts = line.split(None, 4)
            if len(parts) >= 4:
                active_map[parts[0]] = parts[2]  # active/inactive/failed

        for unit, state in unit_states.items():
            active = active_map.get(unit, "")
            desc = ""
            try:
                rd = subprocess.run(
                    ["systemctl", "--user", "show", unit, "--property=Description", "--value"],
                    capture_output=True, text=True, timeout=5,
                )
                desc = rd.stdout.strip()
            except Exception:
                pass
            rows.append((unit, desc, state, active))
    except Exception:
        pass
    return rows


# ── XDG autostart ─────────────────────────────────────────────────────────────

def _parse_desktop(path: Path) -> dict:
    data = {}
    try:
        for line in path.read_text(errors="replace").splitlines():
            if "=" in line and not line.startswith("#") and not line.startswith("["):
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip()
    except Exception:
        pass
    return data


def _load_autostart() -> list:
    rows = []
    seen = set()
    for d in XDG_AUTOSTART_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.desktop")):
            if f.name in seen:
                continue
            seen.add(f.name)
            info = _parse_desktop(f)
            hidden = info.get("Hidden", "false").lower() == "true"
            no_display = info.get("NoDisplay", "false").lower() == "true"
            rows.append((
                info.get("Name", f.stem),
                info.get("Exec", ""),
                str(d),
                "Disabled" if (hidden or no_display) else "Enabled",
                str(f),
            ))
    return rows


# ── tab setup ─────────────────────────────────────────────────────────────────

def setup_startup_tab(module) -> None:
    tab = module.mgmt_tabs["startup"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    subtabs = QTabWidget()
    root.addWidget(subtabs)

    svc_widget = QWidget()
    xdg_widget = QWidget()
    subtabs.addTab(svc_widget, "Systemd User Services")
    subtabs.addTab(xdg_widget, "XDG Autostart")

    module._startup_output = QTextEdit()
    module._startup_output.setReadOnly(True)
    module._startup_output.setMaximumHeight(72)
    module._startup_output.setFont(QFont("Courier", 9))
    module._startup_output.setPlaceholderText("Output will appear here.")
    root.addWidget(module._startup_output)

    def _log(msg):
        module._startup_output.append(msg)

    # ══ Systemd user services ══════════════════════════════════════════════════
    svl = QVBoxLayout(svc_widget)
    svl.setContentsMargins(4, 4, 4, 4)

    sv_toolbar = QFrame()
    svtl = QHBoxLayout(sv_toolbar)
    svtl.setContentsMargins(0, 0, 0, 0)
    sv_refresh = QPushButton("Refresh")
    sv_enable  = QPushButton("Enable")
    sv_disable = QPushButton("Disable")
    sv_start   = QPushButton("Start")
    sv_stop    = QPushButton("Stop")
    for b in (sv_refresh, sv_enable, sv_disable, sv_start, sv_stop):
        svtl.addWidget(b)
    svtl.addStretch()
    svl.addWidget(sv_toolbar)

    sv_table = QTableWidget()
    sv_table.setColumnCount(4)
    sv_table.setHorizontalHeaderLabels(["Unit", "Description", "Enabled", "Active"])
    sv_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    sv_table.setColumnWidth(0, 220)
    sv_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    sv_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    sv_table.setColumnWidth(2, 90)
    sv_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
    sv_table.setColumnWidth(3, 80)
    sv_table.verticalHeader().setVisible(False)
    sv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    sv_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    sv_table.setSelectionMode(QAbstractItemView.SingleSelection)
    sv_table.setAlternatingRowColors(True)
    sv_table.setFont(QFont("Arial", 9))
    svl.addWidget(sv_table)

    def _populate_svc(rows):
        sv_table.setRowCount(len(rows))
        for r, (unit, desc, enabled, active) in enumerate(rows):
            sv_table.setItem(r, 0, QTableWidgetItem(unit))
            sv_table.setItem(r, 1, QTableWidgetItem(desc))
            en_item = QTableWidgetItem(enabled)
            if enabled == "enabled":
                en_item.setForeground(QColor("#2ecc71"))
            elif enabled in ("disabled", "masked"):
                en_item.setForeground(QColor("#e74c3c"))
            sv_table.setItem(r, 2, en_item)
            act_item = QTableWidgetItem(active)
            if active == "active":
                act_item.setForeground(QColor("#2ecc71"))
            elif active in ("failed",):
                act_item.setForeground(QColor("#e74c3c"))
            sv_table.setItem(r, 3, act_item)
            sv_table.setRowHeight(r, 22)
        sv_refresh.setEnabled(True)

    def _reload_svc():
        sv_refresh.setEnabled(False)
        threading.Thread(
            target=lambda: module.post_ui_update(
                lambda rows=_load_systemd_user(): _populate_svc(rows)
            ),
            daemon=True,
        ).start()

    def _selected_unit():
        row = sv_table.currentRow()
        return sv_table.item(row, 0).text() if row >= 0 else None

    def _svc_action(action):
        unit = _selected_unit()
        if not unit:
            _log("Select a service first.")
            return
        _sigs.append(_Signals()); sig = _sigs[-1]
        sig.done.connect(lambda rc, out: (_log(out or action + " done"), _reload_svc()))
        threading.Thread(
            target=lambda: sig.done.emit(*_run(["systemctl", "--user", action, unit])),
            daemon=True,
        ).start()

    sv_refresh.clicked.connect(_reload_svc)
    sv_enable.clicked.connect(lambda: _svc_action("enable"))
    sv_disable.clicked.connect(lambda: _svc_action("disable"))
    sv_start.clicked.connect(lambda: _svc_action("start"))
    sv_stop.clicked.connect(lambda: _svc_action("stop"))
    _reload_svc()

    # ══ XDG Autostart ══════════════════════════════════════════════════════════
    xdgl = QVBoxLayout(xdg_widget)
    xdgl.setContentsMargins(4, 4, 4, 4)

    xdg_toolbar = QFrame()
    xdgtl = QHBoxLayout(xdg_toolbar)
    xdgtl.setContentsMargins(0, 0, 0, 0)
    xdg_refresh = QPushButton("Refresh")
    xdg_add     = QPushButton("Add Entry")
    xdg_toggle  = QPushButton("Enable / Disable")
    xdg_delete  = QPushButton("Delete")
    xdg_delete.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (xdg_refresh, xdg_add, xdg_toggle, xdg_delete):
        xdgtl.addWidget(b)
    xdgtl.addStretch()
    xdgl.addWidget(xdg_toolbar)

    xdg_table = QTableWidget()
    xdg_table.setColumnCount(4)
    xdg_table.setHorizontalHeaderLabels(["Name", "Command", "Location", "State"])
    xdg_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    xdg_table.setColumnWidth(0, 160)
    xdg_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    xdg_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
    xdg_table.setColumnWidth(2, 140)
    xdg_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
    xdg_table.setColumnWidth(3, 75)
    xdg_table.verticalHeader().setVisible(False)
    xdg_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    xdg_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    xdg_table.setSelectionMode(QAbstractItemView.SingleSelection)
    xdg_table.setAlternatingRowColors(True)
    xdg_table.setFont(QFont("Arial", 9))
    xdgl.addWidget(xdg_table)

    module._xdg_rows: list = []

    def _populate_xdg(rows):
        module._xdg_rows = rows
        xdg_table.setRowCount(len(rows))
        for r, (name, exe, loc, state, _path) in enumerate(rows):
            xdg_table.setItem(r, 0, QTableWidgetItem(name))
            xdg_table.setItem(r, 1, QTableWidgetItem(exe))
            xdg_table.setItem(r, 2, QTableWidgetItem(loc))
            st_item = QTableWidgetItem(state)
            if state == "Enabled":
                st_item.setForeground(QColor("#2ecc71"))
            else:
                st_item.setForeground(QColor("#e74c3c"))
            xdg_table.setItem(r, 3, st_item)
            xdg_table.setRowHeight(r, 22)
        xdg_refresh.setEnabled(True)

    def _reload_xdg():
        xdg_refresh.setEnabled(False)
        threading.Thread(
            target=lambda: module.post_ui_update(
                lambda rows=_load_autostart(): _populate_xdg(rows)
            ),
            daemon=True,
        ).start()

    def _selected_xdg():
        row = xdg_table.currentRow()
        if row < 0 or row >= len(module._xdg_rows):
            return None
        return module._xdg_rows[row]

    def _add_xdg():
        dlg = QDialog(tab)
        dlg.setWindowTitle("Add Autostart Entry")
        fl = QFormLayout(dlg)
        name_edit = QLineEdit()
        exec_edit = QLineEdit()
        fl.addRow("Name:", name_edit)
        fl.addRow("Command:", exec_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        name = name_edit.text().strip()
        exe = exec_edit.text().strip()
        if not name or not exe:
            return
        dest = Path.home() / ".config" / "autostart"
        dest.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        fpath = dest / f"{safe}.desktop"
        fpath.write_text(
            f"[Desktop Entry]\nType=Application\nName={name}\nExec={exe}\nHidden=false\n"
        )
        _log(f"Created {fpath}")
        _reload_xdg()

    def _toggle_xdg():
        row_data = _selected_xdg()
        if not row_data:
            _log("Select an entry first.")
            return
        name, exe, loc, state, fpath = row_data
        p = Path(fpath)
        if not p.exists():
            _log(f"File not found: {fpath}")
            return
        text = p.read_text(errors="replace")
        if state == "Enabled":
            text = _set_desktop_key(text, "Hidden", "true")
            _log(f"Disabled {p.name}")
        else:
            text = _set_desktop_key(text, "Hidden", "false")
            _log(f"Enabled {p.name}")
        p.write_text(text)
        _reload_xdg()

    def _set_desktop_key(text: str, key: str, value: str) -> str:
        lines = text.splitlines()
        replaced = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{key}={value}")
        return "\n".join(lines) + "\n"

    def _delete_xdg():
        row_data = _selected_xdg()
        if not row_data:
            _log("Select an entry first.")
            return
        name, _, _, _, fpath = row_data
        p = Path(fpath)
        if QMessageBox.question(tab, "Confirm", f"Delete autostart entry '{name}'?\n{fpath}",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            p.unlink()
            _log(f"Deleted {fpath}")
        except Exception as exc:
            _log(f"Error: {exc}")
        _reload_xdg()

    xdg_refresh.clicked.connect(_reload_xdg)
    xdg_add.clicked.connect(_add_xdg)
    xdg_toggle.clicked.connect(_toggle_xdg)
    xdg_delete.clicked.connect(_delete_xdg)
    _reload_xdg()
