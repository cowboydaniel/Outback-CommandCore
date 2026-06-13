"""SSH Key Manager tab for PC-X — authorized_keys, known_hosts, key generation."""

from __future__ import annotations

import os
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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

SSH_DIR = Path.home() / ".ssh"
AUTH_KEYS = SSH_DIR / "authorized_keys"
KNOWN_HOSTS = SSH_DIR / "known_hosts"

KEY_TYPES = ["ed25519", "rsa", "ecdsa"]


class _Signals(QObject):
    done = Signal(int, str)
    loaded = Signal(list)


def _parse_authorized_keys() -> list[tuple[str, str, str]]:
    """Return list of (type, key_snippet, comment) from authorized_keys."""
    rows = []
    if not AUTH_KEYS.exists():
        return rows
    for line in AUTH_KEYS.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        key_type = parts[0] if len(parts) >= 1 else ""
        key_data = parts[1] if len(parts) >= 2 else ""
        comment = parts[2] if len(parts) >= 3 else ""
        snippet = key_data[:24] + "…" if len(key_data) > 24 else key_data
        rows.append((key_type, snippet, comment, line))
    return rows


def _parse_known_hosts() -> list[tuple[str, str]]:
    """Return list of (host, key_type) from known_hosts."""
    rows = []
    if not KNOWN_HOSTS.exists():
        return rows
    for line in KNOWN_HOSTS.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        host = parts[0] if parts else ""
        key_type = parts[1] if len(parts) >= 2 else ""
        rows.append((host, key_type, line))
    return rows


def _list_key_files() -> list[Path]:
    if not SSH_DIR.exists():
        return []
    return sorted(
        p for p in SSH_DIR.iterdir()
        if p.suffix not in (".pub",) and not p.name.startswith(".")
        and p.is_file() and (SSH_DIR / (p.name + ".pub")).exists()
    )


def setup_sshkeys_tab(module) -> None:
    tab = module.mgmt_tabs["ssh keys"]
    _sigs: list = []
    root = QVBoxLayout(tab)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(6)

    subtabs = QTabWidget()
    root.addWidget(subtabs)

    auth_widget  = QWidget()
    known_widget = QWidget()
    keys_widget  = QWidget()
    subtabs.addTab(auth_widget,  "Authorized Keys")
    subtabs.addTab(known_widget, "Known Hosts")
    subtabs.addTab(keys_widget,  "My Key Pairs")

    module._ssh_output = QTextEdit()
    module._ssh_output.setReadOnly(True)
    module._ssh_output.setMaximumHeight(72)
    module._ssh_output.setFont(QFont("Courier", 9))
    module._ssh_output.setPlaceholderText("Output will appear here.")
    root.addWidget(module._ssh_output)

    def _log(msg):
        module._ssh_output.append(msg)

    # ══ Authorized Keys ════════════════════════════════════════════════════════
    al = QVBoxLayout(auth_widget)
    al.setContentsMargins(4, 4, 4, 4)

    atb = QFrame()
    atbl = QHBoxLayout(atb)
    atbl.setContentsMargins(0, 0, 0, 0)
    a_refresh = QPushButton("Refresh")
    a_add     = QPushButton("Add Key")
    a_del     = QPushButton("Remove Selected")
    a_del.setStyleSheet("QPushButton{color:#c0392b;}")
    for b in (a_refresh, a_add, a_del):
        atbl.addWidget(b)
    atbl.addStretch()
    al.addWidget(atb)

    a_table = QTableWidget()
    a_table.setColumnCount(3)
    a_table.setHorizontalHeaderLabels(["Type", "Key (snippet)", "Comment"])
    a_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    a_table.setColumnWidth(0, 100)
    a_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    a_table.setColumnWidth(1, 200)
    a_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
    a_table.verticalHeader().setVisible(False)
    a_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    a_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    a_table.setSelectionMode(QAbstractItemView.SingleSelection)
    a_table.setAlternatingRowColors(True)
    a_table.setFont(QFont("Arial", 9))
    al.addWidget(a_table)

    module._auth_rows: list = []

    def _populate_auth(rows):
        module._auth_rows = rows
        a_table.setRowCount(len(rows))
        for r, (ktype, snippet, comment, _raw) in enumerate(rows):
            a_table.setItem(r, 0, QTableWidgetItem(ktype))
            a_table.setItem(r, 1, QTableWidgetItem(snippet))
            a_table.setItem(r, 2, QTableWidgetItem(comment))
            a_table.setRowHeight(r, 22)
        a_refresh.setEnabled(True)

    def _reload_auth():
        a_refresh.setEnabled(False)
        _sigs.append(_Signals())
        _sigs[-1].loaded.connect(_populate_auth)
        threading.Thread(
            target=lambda: _sigs[-1].loaded.emit(_parse_authorized_keys()),
            daemon=True,
        ).start()

    def _add_auth_key():
        dlg = QDialog(tab)
        dlg.setWindowTitle("Add Authorized Key")
        fl = QFormLayout(dlg)
        key_edit = QTextEdit()
        key_edit.setPlaceholderText("Paste the full public key line (ssh-ed25519 AAAA… comment)")
        key_edit.setFixedHeight(80)
        fl.addRow("Public key:", key_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        key_line = key_edit.toPlainText().strip()
        if not key_line:
            return
        SSH_DIR.mkdir(mode=0o700, exist_ok=True)
        existing = AUTH_KEYS.read_text(errors="replace") if AUTH_KEYS.exists() else ""
        if key_line in existing:
            _log("Key already present.")
            return
        with AUTH_KEYS.open("a") as f:
            f.write(("\n" if existing and not existing.endswith("\n") else "") + key_line + "\n")
        AUTH_KEYS.chmod(0o600)
        _log("Key added.")
        _reload_auth()

    def _del_auth_key():
        row = a_table.currentRow()
        if row < 0 or row >= len(module._auth_rows):
            _log("Select a key first.")
            return
        _type, snippet, comment, raw = module._auth_rows[row]
        if QMessageBox.question(tab, "Confirm", f"Remove key:\n{raw[:80]}…",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        lines = AUTH_KEYS.read_text(errors="replace").splitlines()
        new_lines = [l for l in lines if l.strip() != raw.strip()]
        AUTH_KEYS.write_text("\n".join(new_lines) + "\n")
        _log("Key removed.")
        _reload_auth()

    a_refresh.clicked.connect(_reload_auth)
    a_add.clicked.connect(_add_auth_key)
    a_del.clicked.connect(_del_auth_key)
    _reload_auth()

    # ══ Known Hosts ════════════════════════════════════════════════════════════
    kl = QVBoxLayout(known_widget)
    kl.setContentsMargins(4, 4, 4, 4)

    ktb = QFrame()
    ktbl = QHBoxLayout(ktb)
    ktbl.setContentsMargins(0, 0, 0, 0)
    k_refresh = QPushButton("Refresh")
    k_del     = QPushButton("Remove Host")
    k_del.setStyleSheet("QPushButton{color:#c0392b;}")
    k_search  = QLineEdit()
    k_search.setPlaceholderText("Filter hosts…")
    k_search.setClearButtonEnabled(True)
    ktbl.addWidget(k_search)
    for b in (k_refresh, k_del):
        ktbl.addWidget(b)
    kl.addWidget(ktb)

    k_table = QTableWidget()
    k_table.setColumnCount(2)
    k_table.setHorizontalHeaderLabels(["Host", "Key Type"])
    k_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    k_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    k_table.setColumnWidth(1, 140)
    k_table.verticalHeader().setVisible(False)
    k_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    k_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    k_table.setSelectionMode(QAbstractItemView.SingleSelection)
    k_table.setAlternatingRowColors(True)
    k_table.setFont(QFont("Arial", 9))
    kl.addWidget(k_table)

    module._known_rows: list = []

    def _populate_known(rows):
        module._known_rows = rows
        _filter_known()
        k_refresh.setEnabled(True)

    def _filter_known():
        text = k_search.text().lower()
        rows = module._known_rows
        filtered = [(h, kt, raw) for h, kt, raw in rows if text in h.lower()]
        k_table.setRowCount(len(filtered))
        for r, (h, kt, _raw) in enumerate(filtered):
            k_table.setItem(r, 0, QTableWidgetItem(h))
            k_table.setItem(r, 1, QTableWidgetItem(kt))
            k_table.setRowHeight(r, 22)
        module._known_filtered = filtered

    k_search.textChanged.connect(lambda _: _filter_known())

    def _reload_known():
        k_refresh.setEnabled(False)
        _sigs.append(_Signals())
        _sigs[-1].loaded.connect(_populate_known)
        threading.Thread(
            target=lambda: _sigs[-1].loaded.emit(_parse_known_hosts()),
            daemon=True,
        ).start()

    def _del_known():
        row = k_table.currentRow()
        filtered = getattr(module, "_known_filtered", [])
        if row < 0 or row >= len(filtered):
            _log("Select a host first.")
            return
        host, _kt, raw = filtered[row]
        if QMessageBox.question(tab, "Confirm", f"Remove host '{host}' from known_hosts?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            subprocess.run(["ssh-keygen", "-R", host], check=True, capture_output=True)
            _log(f"Removed {host} from known_hosts.")
        except Exception as exc:
            _log(f"ssh-keygen -R failed: {exc}")
        _reload_known()

    k_refresh.clicked.connect(_reload_known)
    k_del.clicked.connect(_del_known)
    _reload_known()

    # ══ My Key Pairs ═══════════════════════════════════════════════════════════
    ml = QVBoxLayout(keys_widget)
    ml.setContentsMargins(4, 4, 4, 4)

    mtb = QFrame()
    mtbl = QHBoxLayout(mtb)
    mtbl.setContentsMargins(0, 0, 0, 0)
    m_refresh  = QPushButton("Refresh")
    m_generate = QPushButton("Generate New Key")
    m_copy_pub = QPushButton("Copy Public Key")
    for b in (m_refresh, m_generate, m_copy_pub):
        mtbl.addWidget(b)
    mtbl.addStretch()
    ml.addWidget(mtb)

    m_table = QTableWidget()
    m_table.setColumnCount(3)
    m_table.setHorizontalHeaderLabels(["Key File", "Type (from pub)", "Public Key Preview"])
    m_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
    m_table.setColumnWidth(0, 160)
    m_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
    m_table.setColumnWidth(1, 100)
    m_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
    m_table.verticalHeader().setVisible(False)
    m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    m_table.setSelectionMode(QAbstractItemView.SingleSelection)
    m_table.setAlternatingRowColors(True)
    m_table.setFont(QFont("Arial", 9))
    ml.addWidget(m_table)

    module._key_files: list[Path] = []

    def _reload_keys():
        module._key_files = _list_key_files()
        m_table.setRowCount(len(module._key_files))
        for r, kf in enumerate(module._key_files):
            pub = kf.with_suffix(".pub") if kf.suffix == "" else Path(str(kf) + ".pub")
            pub_path = SSH_DIR / (kf.name + ".pub")
            pub_text = ""
            ktype = ""
            if pub_path.exists():
                pub_text = pub_path.read_text(errors="replace").strip()
                parts = pub_text.split(None, 2)
                ktype = parts[0] if parts else ""
                pub_text = (parts[1][:32] + "…") if len(parts) > 1 else ""
            m_table.setItem(r, 0, QTableWidgetItem(kf.name))
            m_table.setItem(r, 1, QTableWidgetItem(ktype))
            m_table.setItem(r, 2, QTableWidgetItem(pub_text))
            m_table.setRowHeight(r, 22)
        m_refresh.setEnabled(True)

    def _generate_key():
        dlg = QDialog(tab)
        dlg.setWindowTitle("Generate SSH Key Pair")
        fl = QFormLayout(dlg)
        type_cb = QComboBox()
        type_cb.addItems(KEY_TYPES)
        fl.addRow("Key type:", type_cb)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. id_ed25519_work")
        fl.addRow("File name:", name_edit)
        comment_edit = QLineEdit()
        comment_edit.setPlaceholderText("e.g. user@host")
        fl.addRow("Comment:", comment_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        ktype = type_cb.currentText()
        fname = name_edit.text().strip() or f"id_{ktype}"
        comment = comment_edit.text().strip()
        SSH_DIR.mkdir(mode=0o700, exist_ok=True)
        dest = SSH_DIR / fname
        if dest.exists():
            if QMessageBox.question(tab, "Overwrite?", f"{dest} exists. Overwrite?",
                                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        cmd = ["ssh-keygen", "-t", ktype, "-f", str(dest), "-N", "", "-q"]
        if comment:
            cmd += ["-C", comment]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            _log(f"Generated {dest} ({ktype}).")
        except subprocess.CalledProcessError as exc:
            _log(f"ssh-keygen failed: {exc.stderr.decode()}")
        _reload_keys()

    def _copy_pub_key():
        row = m_table.currentRow()
        if row < 0 or row >= len(module._key_files):
            _log("Select a key pair first.")
            return
        kf = module._key_files[row]
        pub_path = SSH_DIR / (kf.name + ".pub")
        if not pub_path.exists():
            _log(f"{pub_path} not found.")
            return
        pub_text = pub_path.read_text(errors="replace").strip()
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(pub_text)
        _log(f"Copied {pub_path.name} to clipboard.")

    m_refresh.clicked.connect(_reload_keys)
    m_generate.clicked.connect(_generate_key)
    m_copy_pub.clicked.connect(_copy_pub_key)
    _reload_keys()
