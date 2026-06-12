"""System Configuration tab for PC-X — hostname, timezone, locale."""

from __future__ import annotations

import os
import subprocess
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
)


class _Signals(QObject):
    done = Signal(int, str)
    timezones_loaded = Signal(list)
    locales_loaded = Signal(list)


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


def _current_hostname() -> str:
    try:
        return subprocess.run(
            ["hostname"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        return ""


def _current_timezone() -> str:
    try:
        r = subprocess.run(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip()
    except Exception:
        pass
    try:
        link = os.readlink("/etc/localtime")
        return link.split("/zoneinfo/", 1)[-1]
    except Exception:
        return ""


def _current_locale() -> str:
    try:
        r = subprocess.run(
            ["localectl", "status"], capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.splitlines():
            if "LANG=" in line:
                return line.split("LANG=", 1)[1].strip()
    except Exception:
        pass
    return os.environ.get("LANG", "")


def _list_timezones() -> list:
    try:
        r = subprocess.run(
            ["timedatectl", "list-timezones"],
            capture_output=True, text=True, timeout=15,
        )
        return r.stdout.strip().splitlines()
    except Exception:
        return []


def _list_locales() -> list:
    try:
        r = subprocess.run(
            ["locale", "-a"], capture_output=True, text=True, timeout=10
        )
        return sorted(r.stdout.strip().splitlines())
    except Exception:
        return []


def setup_sysconfig_tab(module) -> None:
    tab = module.mgmt_tabs["sysconfig"]
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(8)

    module._syscfg_output = QTextEdit()
    module._syscfg_output.setReadOnly(True)
    module._syscfg_output.setMaximumHeight(80)
    module._syscfg_output.setFont(QFont("Courier", 9))
    module._syscfg_output.setPlaceholderText("Command output will appear here.")

    def _log(msg):
        module._syscfg_output.append(msg)

    def _run_bg(args, success_msg="Done.", reload_fn=None):
        sig = _Signals()
        sig.done.connect(lambda rc, out: (
            _log(success_msg if rc == 0 else f"Failed: {out}"),
            reload_fn() if reload_fn and rc == 0 else None,
        ))
        def worker():
            rc, out = _run_priv(args)
            sig.done.emit(rc, out)
        threading.Thread(target=worker, daemon=True).start()

    # ── Hostname ──────────────────────────────────────────────────────────────
    hn_group = QGroupBox("Hostname")
    hn_grid = QGridLayout(hn_group)

    hn_grid.addWidget(QLabel("Current:"), 0, 0)
    module._hn_current = QLabel(_current_hostname())
    module._hn_current.setFont(QFont("Arial", 10, QFont.Bold))
    hn_grid.addWidget(module._hn_current, 0, 1)

    hn_grid.addWidget(QLabel("New hostname:"), 1, 0)
    hn_edit = QLineEdit()
    hn_edit.setPlaceholderText("e.g. my-laptop")
    hn_grid.addWidget(hn_edit, 1, 1)

    hn_apply = QPushButton("Apply")
    hn_grid.addWidget(hn_apply, 1, 2)
    root.addWidget(hn_group)

    def _apply_hostname():
        name = hn_edit.text().strip()
        if not name:
            return
        if QMessageBox.question(tab, "Confirm",
                                f"Change hostname to '{name}'?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        def reload():
            module._hn_current.setText(_current_hostname())
            hn_edit.clear()

        _run_bg(["hostnamectl", "set-hostname", name], f"Hostname set to '{name}'.", reload)

    hn_apply.clicked.connect(_apply_hostname)

    # ── Timezone ──────────────────────────────────────────────────────────────
    tz_group = QGroupBox("Timezone")
    tz_grid = QGridLayout(tz_group)

    tz_grid.addWidget(QLabel("Current:"), 0, 0)
    module._tz_current = QLabel(_current_timezone())
    module._tz_current.setFont(QFont("Arial", 10, QFont.Bold))
    tz_grid.addWidget(module._tz_current, 0, 1)

    tz_grid.addWidget(QLabel("New timezone:"), 1, 0)
    tz_combo = QComboBox()
    tz_combo.setEditable(True)
    tz_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    tz_combo.setPlaceholderText("Loading timezones…")
    tz_grid.addWidget(tz_combo, 1, 1)

    tz_apply = QPushButton("Apply")
    tz_grid.addWidget(tz_apply, 1, 2)
    root.addWidget(tz_group)

    def _load_timezones():
        sig = _Signals()
        sig.timezones_loaded.connect(lambda tzs: (
            tz_combo.clear(),
            tz_combo.addItems(tzs),
            tz_combo.setCurrentText(_current_timezone()),
        ))
        threading.Thread(
            target=lambda: sig.timezones_loaded.emit(_list_timezones()),
            daemon=True,
        ).start()

    def _apply_timezone():
        tz = tz_combo.currentText().strip()
        if not tz:
            return

        def reload():
            module._tz_current.setText(_current_timezone())

        _run_bg(["timedatectl", "set-timezone", tz], f"Timezone set to '{tz}'.", reload)

    tz_apply.clicked.connect(_apply_timezone)
    _load_timezones()

    # ── Locale ────────────────────────────────────────────────────────────────
    lc_group = QGroupBox("Locale")
    lc_grid = QGridLayout(lc_group)

    lc_grid.addWidget(QLabel("Current:"), 0, 0)
    module._lc_current = QLabel(_current_locale())
    module._lc_current.setFont(QFont("Arial", 10, QFont.Bold))
    lc_grid.addWidget(module._lc_current, 0, 1)

    lc_grid.addWidget(QLabel("New locale:"), 1, 0)
    lc_combo = QComboBox()
    lc_combo.setEditable(True)
    lc_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    lc_combo.setPlaceholderText("Loading locales…")
    lc_grid.addWidget(lc_combo, 1, 1)

    lc_apply = QPushButton("Apply")
    lc_grid.addWidget(lc_apply, 1, 2)
    root.addWidget(lc_group)

    def _load_locales():
        sig = _Signals()
        sig.locales_loaded.connect(lambda lcs: (
            lc_combo.clear(),
            lc_combo.addItems(lcs),
            lc_combo.setCurrentText(_current_locale()),
        ))
        threading.Thread(
            target=lambda: sig.locales_loaded.emit(_list_locales()),
            daemon=True,
        ).start()

    def _apply_locale():
        locale = lc_combo.currentText().strip()
        if not locale:
            return

        def reload():
            module._lc_current.setText(_current_locale())

        _run_bg(["localectl", "set-locale", f"LANG={locale}"],
                f"Locale set to '{locale}'. Re-login to fully apply.", reload)

    lc_apply.clicked.connect(_apply_locale)
    _load_locales()

    # ── NTP / Time sync ───────────────────────────────────────────────────────
    ntp_group = QGroupBox("Time Synchronisation")
    ntp_layout = QHBoxLayout(ntp_group)

    module._ntp_status = QLabel("Checking…")
    module._ntp_status.setFont(QFont("Arial", 10))
    ntp_layout.addWidget(module._ntp_status)
    ntp_layout.addStretch()

    ntp_on  = QPushButton("Enable NTP")
    ntp_off = QPushButton("Disable NTP")
    ntp_layout.addWidget(ntp_on)
    ntp_layout.addWidget(ntp_off)
    root.addWidget(ntp_group)

    def _refresh_ntp():
        try:
            r = subprocess.run(
                ["timedatectl", "show", "--property=NTP", "--value"],
                capture_output=True, text=True, timeout=5,
            )
            val = r.stdout.strip()
            module._ntp_status.setText(f"NTP: {'enabled' if val == 'yes' else 'disabled'}")
        except Exception:
            module._ntp_status.setText("NTP status unknown")

    ntp_on.clicked.connect(lambda: _run_bg(
        ["timedatectl", "set-ntp", "true"], "NTP enabled.", _refresh_ntp))
    ntp_off.clicked.connect(lambda: _run_bg(
        ["timedatectl", "set-ntp", "false"], "NTP disabled.", _refresh_ntp))
    _refresh_ntp()

    root.addStretch()
    root.addWidget(module._syscfg_output)
