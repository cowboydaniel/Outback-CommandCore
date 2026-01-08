import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QStackedWidget, QStatusBar, QPushButton, QTextEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

class HackAttackGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hack Attack - Professional Security Testing Suite")
        self.setMinimumSize(1200, 800)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QListWidget {
                background-color: #181825;
                border: none;
                font-size: 13px;
                padding: 10px 5px;
                min-width: 280px;
                max-width: 300px;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-radius: 5px;
                margin: 2px 0;
                min-height: 50px;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QLabel {
                font-size: 18px;
                padding: 20px;
            }
            QStatusBar {
                background-color: #181825;
                color: #a6adc8;
            }
        """)
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_sidebar(self):
        """Create the sidebar navigation"""
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(280)
        self.sidebar.setMaximumWidth(300)
        self.sidebar.setWordWrap(True)
        
        # Add navigation items
        nav_items = [
            "Dashboard",
            "Device Discovery & Info",
            "Network & Protocol Analysis",
            "Firmware & OS Analysis",
            "Authentication & Password Testing",
            "Exploitation & Payloads",
            "Mobile & Embedded Tools",
            "Forensics & Incident Response",
            "Settings & Reports",
            "Automation & Scripting",
            "Logs & History",
            "Help & Documentation"
        ]
        
        self.sidebar.addItems(nav_items)
        self.sidebar.currentRowChanged.connect(self.change_page)
        self.main_layout.addWidget(self.sidebar)
    
    def create_placeholder_page(self, title, description, icon_name, show_description=True):
        """Create a modern module page with icon and description"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Header with icon and title
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 20)
        
        # Icon (using text as fallback)
        icon_label = QLabel(icon_name)
        icon_label.setStyleSheet("""
            font-size: 36px;
            color: #89b4fa;
            padding: 15px;
            background-color: rgba(137, 180, 250, 0.1);
            border-radius: 10px;
        """)
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(f"<h1 style='margin: 0; color: #cdd6f4;'>{title}</h1>")
        title_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(title_label, 1)
        
        layout.addWidget(header)
        
        if show_description:
            # Description card
            desc_card = QWidget()
            desc_card.setStyleSheet("""
                background-color: #313244;
                border-radius: 10px;
                padding: 20px;
                border-left: 4px solid #89b4fa;
            """)
            desc_layout = QVBoxLayout(desc_card)

            desc_text = QLabel(description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("color: #cdd6f4; font-size: 14px; line-height: 1.5;")
            desc_layout.addWidget(desc_text)

            layout.addWidget(desc_card)
        
        # Add module-specific content
        if title == "Device Discovery & Info":
            from modules.device_discovery import DeviceDiscoveryGUI
            
            # Create and add the full DeviceDiscoveryGUI
            self.device_discovery_gui = DeviceDiscoveryGUI()
            
            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.device_discovery_gui)
            
        elif title == "Network & Protocol Analysis":
            from modules.network_analysis import NetworkAnalysisGUI
            
            # Create and add the NetworkAnalysisGUI
            self.network_analysis_gui = NetworkAnalysisGUI()
            
            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.network_analysis_gui)
            
        elif title == "Firmware & OS Analysis":
            from modules.firmware_analysis import FirmwareAnalysisGUI
            
            # Create and add the FirmwareAnalysisGUI
            self.firmware_analysis_gui = FirmwareAnalysisGUI()
            
            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.firmware_analysis_gui)
            
        elif title == "Authentication & Password Testing":
            from modules.authentication_testing import AuthenticationTestingGUI
            
            # Create and add the AuthenticationTestingGUI
            self.auth_testing_gui = AuthenticationTestingGUI()
            
            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.auth_testing_gui)
            
        elif title == "Exploitation & Payloads":
            from modules.exploitation import ExploitationGUI
            
            # Create and add the ExploitationGUI
            self.exploitation_gui = ExploitationGUI()
            
            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.exploitation_gui)
            
        elif title == "Mobile & Embedded Tools":
            from modules.mobile_embedded_tools import MobileEmbeddedToolsGUI

            # Create and add the MobileEmbeddedToolsGUI
            self.mobile_embedded_gui = MobileEmbeddedToolsGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.mobile_embedded_gui)

        elif title == "Forensics & Incident Response":
            from modules.forensics import ForensicsGUI

            # Create and add the ForensicsGUI
            self.forensics_gui = ForensicsGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.forensics_gui)

        elif title == "Settings & Reports":
            from modules.settings_reports import SettingsReportsGUI

            # Create and add the SettingsReportsGUI
            self.settings_gui = SettingsReportsGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.settings_gui)

        elif title == "Automation & Scripting":
            from modules.automation import AutomationGUI

            # Create and add the AutomationGUI
            self.automation_gui = AutomationGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.automation_gui)

        elif title == "Logs & History":
            from modules.logs import LogsGUI

            # Create and add the LogsGUI
            self.logs_gui = LogsGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.logs_gui)

        elif title == "Help & Documentation":
            from modules.help_docs import HelpDocsGUI

            # Create and add the HelpDocsGUI
            self.help_gui = HelpDocsGUI()

            # Remove margins and add to layout
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.help_gui)

        elif title == "Dashboard":
            dashboard_widget = self.create_dashboard_widget()
            layout.addWidget(dashboard_widget)

        else:
            missing = QLabel("Module UI not yet implemented. Please check back for updates.")
            missing.setStyleSheet("""
                background-color: #313244;
                color: #f9e2af;
                font-weight: bold;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
                font-size: 14px;
                border: 1px dashed #f9e2af;
            """)
            missing.setAlignment(Qt.AlignCenter)
            layout.addWidget(missing)
        
        # Add some space at the bottom
        layout.addStretch()
        
        page.setLayout(layout)
        return page
        
    def create_main_content(self):
        """Create the main content area with stacked widgets"""
        self.stacked_widget = QStackedWidget()
        
        # Module descriptions
        module_descriptions = [
            ("Dashboard", "Monitor your security assessment activities, view system status, and access quick actions.", "📊"),
            ("Device Discovery & Info", "Scan and analyze connected devices on your network, including detailed hardware and software information.", "🔍"),
            ("Network & Protocol Analysis", "Analyze network traffic, perform protocol analysis, and identify vulnerabilities.", "🌐"),
            ("Firmware & OS Analysis", "Inspect firmware images, analyze operating systems, and identify potential security issues.", "💾"),
            ("Authentication & Password Testing", "Test authentication mechanisms and perform password security assessments.", "🔑"),
            ("Exploitation & Payloads", "Develop and manage exploits and payloads for security testing purposes.", "⚡"),
            ("Mobile & Embedded Tools", "Specialized tools for testing mobile and embedded device security.", "📱"),
            ("Forensics & Incident Response", "Investigate security incidents and perform digital forensics.", "🔍"),
            ("Settings & Reports", "Configure application settings and generate detailed security reports.", "⚙️"),
            ("Automation & Scripting", "Create and manage automated security testing workflows.", "🤖"),
            ("Logs & History", "View detailed logs and history of all security testing activities.", "📝"),
            ("Help & Documentation", "Access user guides, tutorials, and API documentation.", "❓")
        ]
        
        # Create a page for each module
        for i, (title, desc, icon) in enumerate(module_descriptions):
            show_description = title != "Dashboard"
            page = self.create_placeholder_page(title, desc, icon, show_description)
            self.stacked_widget.addWidget(page)
        
        self.main_layout.addWidget(self.stacked_widget, 1)
    
    def change_page(self, index):
        """Change the current page based on sidebar selection"""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            self.status_bar.showMessage(f"Switched to: {self.sidebar.currentItem().text()}")
    
    def run_device_scan(self):
        """This method is no longer used as we're using the full DeviceDiscoveryGUI"""
        pass

    def create_dashboard_widget(self):
        """Create the interactive dashboard widget."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_title = QLabel("Security Operations Snapshot")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #cdd6f4;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        refresh_button = QPushButton("Run Quick Health Check")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        header_layout.addWidget(refresh_button)
        container_layout.addWidget(header)

        metrics_row = QWidget()
        metrics_layout = QHBoxLayout(metrics_row)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(12)

        self.dashboard_metrics = [
            {"label": "Active Targets", "value": 12, "detail": "3 new today"},
            {"label": "Open Findings", "value": 7, "detail": "2 critical"},
            {"label": "Sensors Online", "value": 18, "detail": "100% operational"},
            {"label": "Automations Running", "value": 5, "detail": "Next run in 15m"}
        ]

        self.metric_cards = []
        for metric in self.dashboard_metrics:
            card = QWidget()
            card.setStyleSheet("""
                background-color: #313244;
                border-radius: 10px;
                padding: 14px;
                border: 1px solid #45475a;
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)

            value_label = QLabel(str(metric["value"]))
            value_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #a6e3a1;")
            name_label = QLabel(metric["label"])
            name_label.setStyleSheet("font-size: 13px; color: #cdd6f4;")
            detail_label = QLabel(metric["detail"])
            detail_label.setStyleSheet("font-size: 12px; color: #a6adc8;")

            card_layout.addWidget(value_label)
            card_layout.addWidget(name_label)
            card_layout.addWidget(detail_label)
            metrics_layout.addWidget(card)
            self.metric_cards.append((value_label, detail_label))

        container_layout.addWidget(metrics_row)

        status_and_activity = QWidget()
        status_layout = QHBoxLayout(status_and_activity)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)

        status_column = QWidget()
        status_column_layout = QVBoxLayout(status_column)
        status_column_layout.setContentsMargins(0, 0, 0, 0)
        status_column_layout.setSpacing(10)

        status_title = QLabel("Live Status")
        status_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        status_column_layout.addWidget(status_title)

        self.status_tiles = [
            {"name": "Threat Intel Feed", "state": "Streaming", "accent": "#a6e3a1"},
            {"name": "Credential Watch", "state": "2 alerts", "accent": "#f38ba8"},
            {"name": "Patch Compliance", "state": "92% ready", "accent": "#f9e2af"}
        ]

        self.status_tile_labels = []
        for tile in self.status_tiles:
            tile_card = QWidget()
            tile_card.setStyleSheet(f"""
                background-color: #313244;
                border-radius: 10px;
                padding: 12px;
                border-left: 4px solid {tile["accent"]};
                border-top: 1px solid #45475a;
                border-right: 1px solid #45475a;
                border-bottom: 1px solid #45475a;
            """)
            tile_layout = QVBoxLayout(tile_card)
            tile_layout.setContentsMargins(10, 10, 10, 10)
            tile_layout.setSpacing(4)
            name_label = QLabel(tile["name"])
            name_label.setStyleSheet("font-size: 13px; color: #cdd6f4;")
            state_label = QLabel(tile["state"])
            state_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #cdd6f4;")
            tile_layout.addWidget(name_label)
            tile_layout.addWidget(state_label)
            status_column_layout.addWidget(tile_card)
            self.status_tile_labels.append(state_label)

        status_layout.addWidget(status_column, 1)

        activity_column = QWidget()
        activity_layout = QVBoxLayout(activity_column)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        activity_layout.setSpacing(8)
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        activity_layout.addWidget(activity_title)

        self.activity_feed = QListWidget()
        self.activity_feed.setStyleSheet("""
            QListWidget {
                background-color: #313244;
                border-radius: 10px;
                padding: 6px;
                border: 1px solid #45475a;
                color: #cdd6f4;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(205, 214, 244, 0.1);
            }
        """)

        self.activity_entries = [
            "09:12 - Firmware scan completed on 4 devices.",
            "09:05 - New vulnerability advisory synced.",
            "08:58 - Network sweep queued (segment 10.0.4.0/24).",
            "08:47 - MFA audit report exported."
        ]
        for entry in self.activity_entries:
            self.activity_feed.addItem(entry)

        activity_layout.addWidget(self.activity_feed)
        status_layout.addWidget(activity_column, 2)

        container_layout.addWidget(status_and_activity)

        def refresh_dashboard():
            self.dashboard_metrics[0]["value"] += 1
            self.dashboard_metrics[1]["value"] = max(0, self.dashboard_metrics[1]["value"] - 1)
            self.dashboard_metrics[2]["value"] = 18
            self.dashboard_metrics[3]["value"] = 5

            for metric, labels in zip(self.dashboard_metrics, self.metric_cards):
                value_label, detail_label = labels
                value_label.setText(str(metric["value"]))
                detail_label.setText(metric["detail"])

            self.status_tiles[1]["state"] = "1 alert"
            self.status_tiles[2]["state"] = "93% ready"
            for tile, label in zip(self.status_tiles, self.status_tile_labels):
                label.setText(tile["state"])

            self.activity_entries.insert(0, "09:18 - Health check completed with 0 errors.")
            self.activity_feed.clear()
            for entry in self.activity_entries[:6]:
                self.activity_feed.addItem(entry)

        refresh_button.clicked.connect(refresh_dashboard)

        return container

def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = HackAttackGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
