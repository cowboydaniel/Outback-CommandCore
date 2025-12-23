"""
Settings & Reports Module for HackAttack
Provides application settings and report generation tools.
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QFileDialog, QMessageBox, QComboBox,
    QFormLayout, QCheckBox, QSpinBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class SettingsReportsGUI(QWidget):
    """Settings & Reports GUI."""

    settings_changed = Signal()

    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.setup_ui()

    def setup_ui(self):
        """Set up the settings interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # General Settings Tab
        general_tab = self.create_general_settings_tab()
        self.tabs.addTab(general_tab, "General")

        # Security Settings Tab
        security_tab = self.create_security_settings_tab()
        self.tabs.addTab(security_tab, "Security")

        # Report Generation Tab
        reports_tab = self.create_reports_tab()
        self.tabs.addTab(reports_tab, "Reports")

        # Export/Import Tab
        export_tab = self.create_export_tab()
        self.tabs.addTab(export_tab, "Export/Import")

        layout.addWidget(self.tabs)

        # Save/Reset buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_settings)
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def create_general_settings_tab(self):
        """Create the general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout()

        self.auto_save = QCheckBox()
        self.auto_save.setChecked(self.settings.get('auto_save', True))
        app_layout.addRow("Auto-save results:", self.auto_save)

        self.results_dir = QLineEdit()
        self.results_dir.setText(self.settings.get('results_dir', os.path.expanduser('~/hackattack_results')))
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_results_dir)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.results_dir)
        dir_row.addWidget(browse_btn)
        app_layout.addRow("Results directory:", dir_row)

        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 64)
        self.max_threads.setValue(self.settings.get('max_threads', 4))
        app_layout.addRow("Max threads:", self.max_threads)

        self.timeout = QSpinBox()
        self.timeout.setRange(5, 600)
        self.timeout.setValue(self.settings.get('timeout', 30))
        self.timeout.setSuffix(" seconds")
        app_layout.addRow("Default timeout:", self.timeout)

        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        # Interface Settings
        ui_group = QGroupBox("Interface Settings")
        ui_layout = QFormLayout()

        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light", "System"])
        self.theme.setCurrentText(self.settings.get('theme', 'Dark'))
        ui_layout.addRow("Theme:", self.theme)

        self.show_tooltips = QCheckBox()
        self.show_tooltips.setChecked(self.settings.get('show_tooltips', True))
        ui_layout.addRow("Show tooltips:", self.show_tooltips)

        self.confirm_actions = QCheckBox()
        self.confirm_actions.setChecked(self.settings.get('confirm_actions', True))
        ui_layout.addRow("Confirm destructive actions:", self.confirm_actions)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        layout.addStretch()
        return tab

    def create_security_settings_tab(self):
        """Create the security settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scan Settings
        scan_group = QGroupBox("Scan Settings")
        scan_layout = QFormLayout()

        self.aggressive_scan = QCheckBox()
        self.aggressive_scan.setChecked(self.settings.get('aggressive_scan', False))
        scan_layout.addRow("Aggressive scanning:", self.aggressive_scan)

        self.stealth_mode = QCheckBox()
        self.stealth_mode.setChecked(self.settings.get('stealth_mode', True))
        scan_layout.addRow("Stealth mode:", self.stealth_mode)

        self.rate_limit = QSpinBox()
        self.rate_limit.setRange(1, 1000)
        self.rate_limit.setValue(self.settings.get('rate_limit', 100))
        self.rate_limit.setSuffix(" req/sec")
        scan_layout.addRow("Rate limit:", self.rate_limit)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # Logging Settings
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout()

        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText(self.settings.get('log_level', 'INFO'))
        log_layout.addRow("Log level:", self.log_level)

        self.log_to_file = QCheckBox()
        self.log_to_file.setChecked(self.settings.get('log_to_file', True))
        log_layout.addRow("Log to file:", self.log_to_file)

        self.log_sensitive = QCheckBox()
        self.log_sensitive.setChecked(self.settings.get('log_sensitive', False))
        log_layout.addRow("Log sensitive data:", self.log_sensitive)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        return tab

    def create_reports_tab(self):
        """Create the reports tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Report Format
        format_group = QGroupBox("Report Format")
        format_layout = QFormLayout()

        self.report_format = QComboBox()
        self.report_format.addItems(["HTML", "PDF", "JSON", "XML", "Markdown"])
        format_layout.addRow("Default format:", self.report_format)

        self.include_screenshots = QCheckBox()
        self.include_screenshots.setChecked(True)
        format_layout.addRow("Include screenshots:", self.include_screenshots)

        self.include_raw_data = QCheckBox()
        format_layout.addRow("Include raw data:", self.include_raw_data)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Generate Report
        gen_group = QGroupBox("Generate Report")
        gen_layout = QVBoxLayout()

        self.report_title = QLineEdit()
        self.report_title.setPlaceholderText("Report title...")
        gen_layout.addWidget(self.report_title)

        self.report_content = QTextEdit()
        self.report_content.setPlaceholderText("Enter report content or notes here...")
        gen_layout.addWidget(self.report_content)

        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        gen_layout.addWidget(generate_btn)

        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        return tab

    def create_export_tab(self):
        """Create the export/import tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Export Settings
        export_group = QGroupBox("Export Settings")
        export_layout = QVBoxLayout()

        export_btn = QPushButton("Export Settings to File")
        export_btn.clicked.connect(self.export_settings)
        export_layout.addWidget(export_btn)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # Import Settings
        import_group = QGroupBox("Import Settings")
        import_layout = QVBoxLayout()

        import_btn = QPushButton("Import Settings from File")
        import_btn.clicked.connect(self.import_settings)
        import_layout.addWidget(import_btn)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # Session History
        history_group = QGroupBox("Session History")
        history_layout = QVBoxLayout()

        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)

        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_history_btn)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        return tab

    def browse_results_dir(self):
        """Browse for results directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Results Directory")
        if dir_path:
            self.results_dir.setText(dir_path)

    def load_settings(self):
        """Load settings from file."""
        settings_path = os.path.expanduser('~/.hackattack_settings.json')
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_settings(self):
        """Save settings to file."""
        self.settings = {
            'auto_save': self.auto_save.isChecked(),
            'results_dir': self.results_dir.text(),
            'max_threads': self.max_threads.value(),
            'timeout': self.timeout.value(),
            'theme': self.theme.currentText(),
            'show_tooltips': self.show_tooltips.isChecked(),
            'confirm_actions': self.confirm_actions.isChecked(),
            'aggressive_scan': self.aggressive_scan.isChecked(),
            'stealth_mode': self.stealth_mode.isChecked(),
            'rate_limit': self.rate_limit.value(),
            'log_level': self.log_level.currentText(),
            'log_to_file': self.log_to_file.isChecked(),
            'log_sensitive': self.log_sensitive.isChecked(),
        }

        settings_path = os.path.expanduser('~/.hackattack_settings.json')
        try:
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = {}
            self.auto_save.setChecked(True)
            self.results_dir.setText(os.path.expanduser('~/hackattack_results'))
            self.max_threads.setValue(4)
            self.timeout.setValue(30)
            self.theme.setCurrentText('Dark')
            self.show_tooltips.setChecked(True)
            self.confirm_actions.setChecked(True)
            self.aggressive_scan.setChecked(False)
            self.stealth_mode.setChecked(True)
            self.rate_limit.setValue(100)
            self.log_level.setCurrentText('INFO')
            self.log_to_file.setChecked(True)
            self.log_sensitive.setChecked(False)

    def generate_report(self):
        """Generate a report."""
        title = self.report_title.text() or "Security Assessment Report"
        content = self.report_content.toPlainText()
        format_type = self.report_format.currentText()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", f"{title}.{format_type.lower()}",
            f"{format_type} Files (*.{format_type.lower()})"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    if format_type == "HTML":
                        f.write(f"<html><head><title>{title}</title></head>")
                        f.write(f"<body><h1>{title}</h1>")
                        f.write(f"<p>Generated: {datetime.now()}</p>")
                        f.write(f"<pre>{content}</pre></body></html>")
                    elif format_type == "JSON":
                        json.dump({'title': title, 'content': content, 'generated': str(datetime.now())}, f)
                    else:
                        f.write(f"# {title}\n\nGenerated: {datetime.now()}\n\n{content}")
                QMessageBox.information(self, "Success", f"Report saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report: {e}")

    def export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "hackattack_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.settings, f, indent=2)
                QMessageBox.information(self, "Success", f"Settings exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.settings = json.load(f)
                self.save_settings()
                QMessageBox.information(self, "Success", "Settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")

    def clear_history(self):
        """Clear session history."""
        self.history_list.clear()
