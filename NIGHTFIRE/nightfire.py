#!/usr/bin/env python3
"""
NIGHTFIRE - Real-time Active Defense and Monitoring Tool
"""
import sys
import os
import time
import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTextEdit, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QStatusBar, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette, QIcon

class SignalEmitter(QObject):
    alert_triggered = Signal(str, str)  # alert_type, message
    log_message = Signal(str, str)      # level, message

class NightfireUI(QMainWindow):
    def __init__(self, nightfire):
        super().__init__()
        self.nightfire = nightfire
        self.signal_emitter = SignalEmitter()

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons', 'nightfire.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the main UI components."""
        self.setWindowTitle("NIGHTFIRE - Active Defense System")
        self.setMinimumSize(900, 600)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Dashboard tab
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Alerts tab
        self.alerts_tab = QWidget()
        self.setup_alerts_tab()
        self.tabs.addTab(self.alerts_tab, "Alerts")
        
        # Log tab
        self.log_tab = QWidget()
        self.setup_log_tab()
        self.tabs.addTab(self.log_tab, "Logs")
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")
    
    def setup_dashboard_tab(self):
        """Set up the dashboard tab."""
        layout = QVBoxLayout(self.dashboard_tab)
        
        # Status overview
        status_group = QWidget()
        status_layout = QHBoxLayout(status_group)
        
        # System status
        sys_status = QWidget()
        sys_layout = QVBoxLayout(sys_status)
        sys_layout.addWidget(QLabel("<h3>System Status</h3>"))
        self.status_indicator = QLabel("OPERATIONAL")
        self.status_indicator.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")
        sys_layout.addWidget(self.status_indicator)
        status_layout.addWidget(sys_status)
        
        # Threat level
        threat_status = QWidget()
        threat_layout = QVBoxLayout(threat_status)
        threat_layout.addWidget(QLabel("<h3>Threat Level</h3>"))
        self.threat_level = QLabel("LOW")
        self.threat_level.setStyleSheet("font-size: 24px; font-weight: bold; color: orange;")
        threat_layout.addWidget(self.threat_level)
        status_layout.addWidget(threat_status)
        
        layout.addWidget(status_group)
        
        # Quick actions
        actions_group = QWidget()
        actions_layout = QHBoxLayout(actions_group)
        
        self.btn_start = QPushButton("Start Monitoring")
        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.setEnabled(False)
        
        actions_layout.addWidget(self.btn_start)
        actions_layout.addWidget(self.btn_stop)
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        layout.addStretch()
    
    def setup_alerts_tab(self):
        """Set up the alerts tab."""
        layout = QVBoxLayout(self.alerts_tab)
        
        # Alerts table
        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Message"])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.alerts_table)
        
        # Alert controls
        controls = QHBoxLayout()
        btn_clear = QPushButton("Clear All Alerts")
        btn_clear.clicked.connect(self.clear_alerts)
        controls.addWidget(btn_clear)
        controls.addStretch()
        
        layout.addLayout(controls)
    
    def setup_log_tab(self):
        """Set up the log tab."""
        layout = QVBoxLayout(self.log_tab)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monospace"))
        
        layout.addWidget(self.log_display)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.signal_emitter.alert_triggered.connect(self.handle_alert)
        self.signal_emitter.log_message.connect(self.log_message)
    
    def start_monitoring(self):
        """Start the monitoring service."""
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.update_status("Monitoring started")
        self.log_message("INFO", "Monitoring service started")
        # In a real app, this would start the monitoring in a separate thread
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.update_status("Monitoring stopped")
        self.log_message("INFO", "Monitoring service stopped")
    
    def handle_alert(self, alert_type, message):
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
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts_table.setRowCount(0)
        self.log_message("INFO", "Cleared all alerts")
    
    def log_message(self, level, message):
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
    
    def update_status(self, message):
        """Update the status bar message."""
        self.status_bar.showMessage(message)


class Nightfire:
    def __init__(self, ui):
        self.running = False
        self.logger = self._setup_logging()
        self.alert_thresholds = {
            'network_scan': 10,  # alerts after 10 scan attempts
            'failed_auth': 5,    # alerts after 5 failed auth attempts
        }
        self.detected_threats: Dict[str, int] = {}
        self.ui = ui
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_threats)
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the NIGHTFIRE system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('NIGHTFIRE')
    
    def start_monitoring(self):
        """Start the monitoring service."""
        self.running = True
        self.timer.start(2000)  # Check every 2 seconds
        self.ui.signal_emitter.log_message.emit("INFO", "NIGHTFIRE monitoring service started")
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.running = False
        self.timer.stop()
        self.ui.signal_emitter.log_message.emit("INFO", "NIGHTFIRE monitoring service stopped")
    
    def check_for_threats(self):
        """Simulate checking for threats."""
        if not self.running:
            return
            
        # Simulate random threats for demo purposes
        import random
        threats = ['network_scan', 'failed_auth', 'intrusion_attempt', 'malware_detected']
        if random.random() > 0.7:  # 30% chance of a threat
            threat = random.choice(threats)
            self.detected_threats[threat] = self.detected_threats.get(threat, 0) + 1
            self.ui.signal_emitter.alert_triggered.emit(
                threat,
                f"Detected {self.detected_threats[threat]} occurrences"
            )
            self._check_thresholds()
    
    def _check_thresholds(self):
        """Check if any threat thresholds have been exceeded."""
        for threat_type, count in self.detected_threats.items():
            if count >= self.alert_thresholds.get(threat_type, float('inf')):
                self._trigger_alert(threat_type, count)

    def _trigger_alert(self, threat_type: str, count: int):
        """Trigger an alert for a detected threat."""
        message = f"{threat_type} detected {count} times (threshold: {self.alert_thresholds.get(threat_type)})"
        self.ui.signal_emitter.alert_triggered.emit("THRESHOLD_EXCEEDED", message)
        self.ui.signal_emitter.log_message.emit("WARNING", f"Alert: {message}")

def main():
    """Main entry point for NIGHTFIRE."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create UI first
    nightfire = None  # Will be set after UI is created
    ui = NightfireUI(nightfire)
    
    # Now create Nightfire with reference to UI
    nightfire = Nightfire(ui)
    ui.nightfire = nightfire
    
    # Connect UI buttons to nightfire methods
    ui.btn_start.clicked.connect(nightfire.start_monitoring)
    ui.btn_stop.clicked.connect(nightfire.stop_monitoring)
    
    # Show the main window
    ui.show()
    
    # Start with monitoring off
    ui.btn_start.setEnabled(True)
    ui.btn_stop.setEnabled(False)
    
    # Simulate some initial threats for demo
    def simulate_threats():
        threats = ['network_scan', 'failed_auth', 'intrusion_attempt']
        for _ in range(3):
            threat = random.choice(threats)
            nightfire.detected_threats[threat] = nightfire.detected_threats.get(threat, 0) + 1
            ui.signal_emitter.alert_triggered.emit(
                threat,
                f"Detected {nightfire.detected_threats[threat]} occurrences"
            )
    
    # Schedule some demo threats
    QTimer.singleShot(5000, simulate_threats)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

class Nightfire:
    def __init__(self):
        self.running = False
        self.logger = self._setup_logging()
        self.alert_thresholds = {
            'network_scan': 10,  # alerts after 10 scan attempts
            'failed_auth': 5,    # alerts after 5 failed auth attempts
        }
        self.detected_threats: Dict[str, int] = {}

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the NIGHTFIRE system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('NIGHTFIRE')

    def start_monitoring(self):
        """Start the monitoring service."""
        self.running = True
        self.logger.info("NIGHTFIRE monitoring service started")
        try:
            while self.running:
                # In a real implementation, this would monitor system/network activity
                time.sleep(1)  # Prevent high CPU usage
                
                # Example: Check for threats periodically
                self._check_thresholds()
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down NIGHTFIRE monitoring service")
            self.running = False

    def _check_thresholds(self):
        """Check if any threat thresholds have been exceeded."""
        for threat_type, count in self.detected_threats.items():
            if count >= self.alert_thresholds.get(threat_type, float('inf')):
                self._trigger_alert(threat_type, count)

    def _trigger_alert(self, threat_type: str, count: int):
        """Trigger an alert for a detected threat."""
        message = f"ALERT: {threat_type} detected {count} times (threshold: {self.alert_thresholds.get(threat_type)})"
        self.logger.warning(message)
        # In a real implementation, this would trigger notifications, etc.

def main():
    """Main entry point for NIGHTFIRE."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationVersion("1.0.0")
    
    print("NIGHTFIRE - Real-time Active Defense and Monitoring Tool")
    print(f"Version: {app.applicationVersion()}")
    print("Initializing...")
    
    nightfire = Nightfire()
    nightfire.start_monitoring()

if __name__ == "__main__":
    main()
