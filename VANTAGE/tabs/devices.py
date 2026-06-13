"""Devices tab — add/remove/monitor remote servers."""
import logging
import threading
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from core.server_registry import ServerRegistry, ServerEntry
from core.remote_client import RemoteClient

logger = logging.getLogger(__name__)


class AddServerDialog(QDialog):
    """Modal dialog for entering SSH connection details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Remote Server")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._client = None   # kept only for the Test button
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("hostname or IP")

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("e.g. ubuntu")

        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["Password", "SSH Key"])
        self.auth_combo.currentIndexChanged.connect(self._on_auth_changed)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("SSH password")

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Path to private key")
        self.key_browse = QPushButton("Browse…")
        self.key_browse.clicked.connect(self._browse_key)
        key_row = QHBoxLayout()
        key_row.addWidget(self.key_edit)
        key_row.addWidget(self.key_browse)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional friendly name")

        form.addRow("Host:", self.host_edit)
        form.addRow("Port:", self.port_spin)
        form.addRow("Username:", self.user_edit)
        form.addRow("Auth:", self.auth_combo)
        form.addRow("Password:", self.password_edit)
        form.addRow("Key file:", key_row)
        form.addRow("Display name:", self.name_edit)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #b0b0b0;")

        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        add_btn = QPushButton("Add Server")
        add_btn.setDefault(True)
        add_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.test_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(add_btn)

        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_row)

        self._on_auth_changed(0)

    def _on_auth_changed(self, index):
        is_password = index == 0
        self.password_edit.setVisible(is_password)
        self.key_edit.setVisible(not is_password)
        self.key_browse.setVisible(not is_password)

    def _browse_key(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select SSH Private Key", "", "All Files (*)")
        if path:
            self.key_edit.setText(path)

    def _test_connection(self):
        client = self._build_client()
        if client is None:
            return
        self.test_btn.setEnabled(False)
        self.status_label.setText("Testing…")
        self.status_label.setStyleSheet("color: #b0b0b0;")

        def run():
            ok, msg = client.test_connection()
            return ok, msg

        def done(ok, msg):
            self.test_btn.setEnabled(True)
            color = "#00d4aa" if ok else "#ff6b6b"
            self.status_label.setStyleSheet(f"color: {color};")
            self.status_label.setText(msg)

        t = threading.Thread(target=lambda: done(*run()), daemon=True)
        t.start()

    def _build_client(self) -> RemoteClient | None:
        host = self.host_edit.text().strip()
        user = self.user_edit.text().strip()
        if not host or not user:
            self.status_label.setStyleSheet("color: #ff6b6b;")
            self.status_label.setText("Host and username are required.")
            return None
        is_key = self.auth_combo.currentIndex() == 1
        return RemoteClient(
            host=host,
            port=self.port_spin.value(),
            username=user,
            password=self.password_edit.text() if not is_key else None,
            key_path=self.key_edit.text().strip() if is_key else None,
        )

    def get_entry(self) -> ServerEntry | None:
        host = self.host_edit.text().strip()
        user = self.user_edit.text().strip()
        if not host or not user:
            return None
        port = self.port_spin.value()
        is_key = self.auth_combo.currentIndex() == 1
        display = self.name_edit.text().strip() or f"{host}:{port}"
        return ServerEntry(
            server_id=f"{host}:{port}",
            display_name=display,
            host=host,
            port=port,
            username=user,
            auth_type="key" if is_key else "password",
            password=self.password_edit.text() if not is_key else "",
            key_path=self.key_edit.text().strip() if is_key else "",
        )


class DevicesTab(QWidget):
    """Manage remote servers and see their live status."""

    COL_NAME   = 0
    COL_HOST   = 1
    COL_STATUS = 2
    COL_LAST   = 3
    COL_REMOVE = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DevicesTab")
        self._registry = ServerRegistry()
        self._clients: dict[str, RemoteClient] = {}
        self._setup_ui()
        self._registry.servers_changed.connect(self._refresh_table)
        self._refresh_table()
        # Ping all servers every 30 seconds
        self._ping_timer = QTimer(self)
        self._ping_timer.timeout.connect(self._check_all_statuses)
        self._ping_timer.start(30_000)
        QTimer.singleShot(0, self._check_all_statuses)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Remote Servers")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px 0;")
        add_btn = QPushButton("+ Add Server")
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self._add_server)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(5)
        self.devices_table.setHorizontalHeaderLabels(
            ["Name", "Host", "Status", "Last Seen", ""]
        )
        hdr = self.devices_table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_NAME,   QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_HOST,   QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_LAST,   QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_REMOVE, QHeaderView.Fixed)
        self.devices_table.setColumnWidth(self.COL_REMOVE, 80)
        self.devices_table.verticalHeader().setVisible(False)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.devices_table)

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def _refresh_table(self):
        servers = self._registry.all_servers()
        self.devices_table.setRowCount(len(servers))
        for row, entry in enumerate(servers):
            self.devices_table.setItem(row, self.COL_NAME, QTableWidgetItem(entry.display_name))
            self.devices_table.setItem(row, self.COL_HOST, QTableWidgetItem(f"{entry.host}:{entry.port}"))
            status_item = QTableWidgetItem(entry.status.capitalize())
            status_item.setData(Qt.UserRole, entry.server_id)
            color = {"online": "#00d4aa", "offline": "#ff6b6b"}.get(entry.status, "#b0b0b0")
            status_item.setForeground(QColor(color))
            self.devices_table.setItem(row, self.COL_STATUS, status_item)
            self.devices_table.setItem(row, self.COL_LAST, QTableWidgetItem(entry.last_seen))

            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("server_id", entry.server_id)
            remove_btn.clicked.connect(self._on_remove_clicked)
            self.devices_table.setCellWidget(row, self.COL_REMOVE, remove_btn)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_server(self):
        dlg = AddServerDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        entry = dlg.get_entry()
        if entry is None:
            QMessageBox.warning(self, "Missing fields", "Host and username are required.")
            return
        if self._registry.get(entry.server_id):
            QMessageBox.information(self, "Already added",
                                    f"{entry.server_id} is already in the list.")
            return
        self._registry.add_server(entry)
        # Kick off an immediate status check for the new server
        threading.Thread(target=self._ping_server, args=(entry.server_id,), daemon=True).start()

    def _on_remove_clicked(self):
        server_id = self.sender().property("server_id")
        if server_id:
            client = self._clients.pop(server_id, None)
            if client:
                client.disconnect()
            self._registry.remove_server(server_id)

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    def _check_all_statuses(self):
        for entry in self._registry.all_servers():
            threading.Thread(
                target=self._ping_server, args=(entry.server_id,), daemon=True
            ).start()

    def _ping_server(self, server_id: str):
        entry = self._registry.get(server_id)
        if entry is None:
            return
        if server_id not in self._clients:
            self._clients[server_id] = RemoteClient(
                host=entry.host, port=entry.port, username=entry.username,
                password=entry.password or None,
                key_path=entry.key_path or None,
            )
        client = self._clients[server_id]
        ok = client.connect() if not client.is_connected else True
        status = "online" if ok else "offline"
        last_seen = datetime.now().strftime("%H:%M:%S") if ok else entry.last_seen
        self._registry.update_status(server_id, status, last_seen)
