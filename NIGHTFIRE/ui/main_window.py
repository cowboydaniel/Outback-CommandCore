"""Main window implementation for NIGHTFIRE."""
from pathlib import Path
import time

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QMessageBox,
    QTableWidgetItem,
)
from PySide6.QtGui import QColor, QIcon

from NIGHTFIRE.app import config
from NIGHTFIRE.tabs import tab_dashboard, tab_alerts, tab_logs
from NIGHTFIRE.ui.components.signal_emitter import SignalEmitter


class NightfireUI(QMainWindow):
    def __init__(self, nightfire=None) -> None:
        super().__init__()
        self.nightfire = nightfire
        self.signal_emitter = SignalEmitter()

        # Set window icon
        icon_path = Path(__file__).resolve().parents[2] / "icons" / "nightfire.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self) -> None:
        """Set up the main UI components."""
        self.setWindowTitle(config.WINDOW_TITLE)
        self.setMinimumSize(*config.MIN_WINDOW_SIZE)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Dashboard tab
        self.dashboard_tab = tab_dashboard.setup_dashboard_tab(self)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # Alerts tab
        self.alerts_tab = tab_alerts.setup_alerts_tab(self)
        self.tabs.addTab(self.alerts_tab, "Alerts")

        # Log tab
        self.log_tab = tab_logs.setup_log_tab(self)
        self.tabs.addTab(self.log_tab, "Logs")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")

    def setup_connections(self) -> None:
        """Set up signal connections."""
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.signal_emitter.alert_triggered.connect(self.handle_alert)
        self.signal_emitter.log_message.connect(self.log_message)

    def start_monitoring(self) -> None:
        """Start the monitoring service."""
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.update_status("Monitoring started")
        self.log_message("INFO", "Monitoring service started")
        # In a real app, this would start the monitoring in a separate thread

    def stop_monitoring(self) -> None:
        """Stop the monitoring service."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_status("Monitoring stopped")
        self.log_message("INFO", "Monitoring service stopped")

    def handle_alert(self, alert_type: str, message: str) -> None:
        """Handle a new alert."""
        row = self.alerts_table.rowCount()
        self.alerts_table.insertRow(row)

        time_item = QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M:%S"))
        type_item = QTableWidgetItem(alert_type)
        severity_item = QTableWidgetItem("High")
        message_item = QTableWidgetItem(message)

        self.alerts_table.setItem(row, 0, time_item)
        self.alerts_table.setItem(row, 1, type_item)
        self.alerts_table.setItem(row, 2, severity_item)
        self.alerts_table.setItem(row, 3, message_item)

        # Auto-scroll to the new alert
        self.alerts_table.scrollToBottom()

        # Show alert in status bar
        self.update_status(f"ALERT: {alert_type} - {message}")

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self.alerts_table.setRowCount(0)
        self.log_message("INFO", "Cleared all alerts")

    def log_message(self, level: str, message: str) -> None:
        """Add a message to the log display."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"

        # Color code log levels
        if level.upper() == "ERROR":
            color = "red"
        elif level.upper() == "WARNING":
            color = "orange"
        elif level.upper() == "INFO":
            color = "black"
        else:
            color = "gray"

        # Append to log display
        self.log_display.setTextColor(QColor(color))
        self.log_display.append(log_entry)

        # Auto-scroll to bottom
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_bar.showMessage(message)

    def show_error(self, message: str) -> None:
        """Display an error dialog."""
        QMessageBox.critical(self, "Error", message)
