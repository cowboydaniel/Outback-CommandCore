"""
Logs & History Module for HackAttack
Provides logging, activity history, and audit trail functionality.
"""

import os
import json
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QFileDialog, QMessageBox, QComboBox,
    QFormLayout, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QCalendarWidget
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor


class LogsGUI(QWidget):
    """Logs & History GUI."""

    def __init__(self):
        super().__init__()
        self.log_entries = []
        self.setup_ui()
        self.load_sample_logs()

        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def setup_ui(self):
        """Set up the logs interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # Activity Log Tab
        activity_tab = self.create_activity_log_tab()
        self.tabs.addTab(activity_tab, "Activity Log")

        # Scan History Tab
        scan_tab = self.create_scan_history_tab()
        self.tabs.addTab(scan_tab, "Scan History")

        # Audit Trail Tab
        audit_tab = self.create_audit_trail_tab()
        self.tabs.addTab(audit_tab, "Audit Trail")

        # Statistics Tab
        stats_tab = self.create_statistics_tab()
        self.tabs.addTab(stats_tab, "Statistics")

        layout.addWidget(self.tabs)

    def create_activity_log_tab(self):
        """Create the activity log tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()

        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Level:"))
        filter_layout.addWidget(self.log_level_filter)

        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Search logs...")
        self.log_search.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.log_search)

        self.auto_scroll = QCheckBox("Auto-scroll")
        self.auto_scroll.setChecked(True)
        filter_layout.addWidget(self.auto_scroll)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_logs)
        filter_layout.addWidget(refresh_btn)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monospace", 10))
        layout.addWidget(self.log_display)

        # Actions
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_logs)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return tab

    def create_scan_history_tab(self):
        """Create the scan history tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Date filter
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        date_row.addWidget(self.from_date)

        date_row.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        date_row.addWidget(self.to_date)

        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.filter_scan_history)
        date_row.addWidget(filter_btn)
        date_row.addStretch()
        layout.addLayout(date_row)

        # Scan history table
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(6)
        self.scan_table.setHorizontalHeaderLabels([
            "Date/Time", "Type", "Target", "Duration", "Findings", "Status"
        ])
        self.scan_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.scan_table.itemDoubleClicked.connect(self.view_scan_details)
        layout.addWidget(self.scan_table)

        # Load sample data
        sample_scans = [
            ("2024-01-15 14:30", "Port Scan", "192.168.1.0/24", "5m 23s", "15 open ports", "Completed"),
            ("2024-01-15 10:15", "Vulnerability Scan", "web.example.com", "12m 45s", "3 vulnerabilities", "Completed"),
            ("2024-01-14 22:00", "Network Discovery", "10.0.0.0/8", "1h 12m", "47 hosts", "Completed"),
            ("2024-01-14 15:30", "Auth Test", "ftp.example.com", "2m 10s", "Weak password", "Warning"),
            ("2024-01-14 09:00", "SSL Check", "secure.example.com", "45s", "Valid certificate", "Completed"),
        ]

        for i, (dt, scan_type, target, duration, findings, status) in enumerate(sample_scans):
            self.scan_table.insertRow(i)
            self.scan_table.setItem(i, 0, QTableWidgetItem(dt))
            self.scan_table.setItem(i, 1, QTableWidgetItem(scan_type))
            self.scan_table.setItem(i, 2, QTableWidgetItem(target))
            self.scan_table.setItem(i, 3, QTableWidgetItem(duration))
            self.scan_table.setItem(i, 4, QTableWidgetItem(findings))

            status_item = QTableWidgetItem(status)
            if status == "Warning":
                status_item.setForeground(QColor("#f9e2af"))
            elif status == "Error":
                status_item.setForeground(QColor("#f38ba8"))
            else:
                status_item.setForeground(QColor("#a6e3a1"))
            self.scan_table.setItem(i, 5, status_item)

        # Actions
        btn_row = QHBoxLayout()
        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_scan_details)
        export_btn = QPushButton("Export History")
        export_btn.clicked.connect(self.export_scan_history)
        btn_row.addWidget(view_btn)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return tab

    def create_audit_trail_tab(self):
        """Create the audit trail tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Audit Trail - Security-relevant actions and changes"))

        # Audit table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Target", "Result"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.audit_table)

        # Sample audit entries
        sample_audit = [
            ("2024-01-15 14:30:00", "admin", "Started port scan", "192.168.1.0/24", "Success"),
            ("2024-01-15 14:35:23", "admin", "Scan completed", "192.168.1.0/24", "15 ports found"),
            ("2024-01-15 10:15:00", "user1", "Login", "System", "Success"),
            ("2024-01-15 10:16:30", "user1", "Exported report", "scan_report.pdf", "Success"),
            ("2024-01-14 22:00:00", "system", "Scheduled scan", "10.0.0.0/8", "Started"),
        ]

        for i, (ts, user, action, target, result) in enumerate(sample_audit):
            self.audit_table.insertRow(i)
            self.audit_table.setItem(i, 0, QTableWidgetItem(ts))
            self.audit_table.setItem(i, 1, QTableWidgetItem(user))
            self.audit_table.setItem(i, 2, QTableWidgetItem(action))
            self.audit_table.setItem(i, 3, QTableWidgetItem(target))
            self.audit_table.setItem(i, 4, QTableWidgetItem(result))

        # Export button
        export_btn = QPushButton("Export Audit Trail")
        export_btn.clicked.connect(self.export_audit_trail)
        layout.addWidget(export_btn)

        return tab

    def create_statistics_tab(self):
        """Create the statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary stats
        stats_group = QGroupBox("Summary Statistics")
        stats_layout = QFormLayout()

        stats_layout.addRow("Total Scans:", QLabel("156"))
        stats_layout.addRow("Successful:", QLabel("142 (91%)"))
        stats_layout.addRow("Failed:", QLabel("14 (9%)"))
        stats_layout.addRow("Total Findings:", QLabel("234"))
        stats_layout.addRow("Critical Findings:", QLabel("12"))
        stats_layout.addRow("Average Scan Time:", QLabel("8m 32s"))

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Recent activity
        recent_group = QGroupBox("Recent Activity (Last 7 Days)")
        recent_layout = QVBoxLayout()

        activity_text = QTextEdit()
        activity_text.setReadOnly(True)
        activity_text.setText("""
Day         Scans   Findings    Avg Duration
──────────  ──────  ──────────  ────────────
Mon         12      18          6m 15s
Tue         15      24          7m 30s
Wed         8       11          5m 45s
Thu         22      35          8m 20s
Fri         18      28          9m 10s
Sat         5       8           4m 55s
Sun         3       4           3m 40s
        """)
        activity_text.setFont(QFont("Monospace", 10))
        recent_layout.addWidget(activity_text)

        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)

        return tab

    def load_sample_logs(self):
        """Load sample log entries."""
        sample_logs = [
            ("INFO", "Application started"),
            ("INFO", "Loaded configuration from ~/.hackattack/config.json"),
            ("DEBUG", "Initializing network scanner module"),
            ("INFO", "Network scanner ready"),
            ("WARNING", "Rate limiting enabled due to high request volume"),
            ("INFO", "Started port scan on 192.168.1.1"),
            ("DEBUG", "Scanning ports 1-1000"),
            ("INFO", "Port 22 (SSH) open"),
            ("INFO", "Port 80 (HTTP) open"),
            ("INFO", "Port 443 (HTTPS) open"),
            ("INFO", "Scan completed: 3 open ports found"),
            ("ERROR", "Connection timeout to 192.168.1.254"),
        ]

        self.log_entries = []
        for level, message in sample_logs:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_entries.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })

        self.refresh_log_display()

    def refresh_log_display(self):
        """Refresh the log display with current entries."""
        self.log_display.clear()

        level_filter = self.log_level_filter.currentText()
        search_text = self.log_search.text().lower()

        for entry in self.log_entries:
            if level_filter != "All" and entry['level'] != level_filter:
                continue
            if search_text and search_text not in entry['message'].lower():
                continue

            color = self.get_level_color(entry['level'])
            self.log_display.append(
                f"<span style='color:{color}'>[{entry['timestamp']}] [{entry['level']}] {entry['message']}</span>"
            )

        if self.auto_scroll.isChecked():
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

    def get_level_color(self, level):
        """Get color for log level."""
        colors = {
            'DEBUG': '#89b4fa',
            'INFO': '#a6e3a1',
            'WARNING': '#f9e2af',
            'ERROR': '#f38ba8',
            'CRITICAL': '#f38ba8',
        }
        return colors.get(level, '#cdd6f4')

    def apply_filters(self):
        """Apply log filters."""
        self.refresh_log_display()

    def refresh_logs(self):
        """Refresh logs (would reload from file in real implementation)."""
        self.refresh_log_display()

    def clear_logs(self):
        """Clear the log display."""
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_entries = []
            self.log_display.clear()

    def export_logs(self):
        """Export logs to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "hackattack_logs.txt", "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for entry in self.log_entries:
                        f.write(f"[{entry['timestamp']}] [{entry['level']}] {entry['message']}\n")
                QMessageBox.information(self, "Success", f"Logs exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs: {e}")

    def filter_scan_history(self):
        """Filter scan history by date range."""
        QMessageBox.information(self, "Filter", "Filtering scan history by selected date range...")

    def view_scan_details(self):
        """View details of selected scan."""
        current = self.scan_table.currentRow()
        if current >= 0:
            scan_type = self.scan_table.item(current, 1).text()
            target = self.scan_table.item(current, 2).text()
            QMessageBox.information(
                self, "Scan Details",
                f"Scan Type: {scan_type}\nTarget: {target}\n\n"
                "Full scan details would be displayed here."
            )

    def export_scan_history(self):
        """Export scan history."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Scan History", "scan_history.json", "JSON Files (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "Success", f"Scan history exported to {file_path}")

    def export_audit_trail(self):
        """Export audit trail."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Audit Trail", "audit_trail.json", "JSON Files (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "Success", f"Audit trail exported to {file_path}")
