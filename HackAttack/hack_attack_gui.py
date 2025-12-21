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
    
    def create_placeholder_page(self, title, description, icon_name):
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
            
        else:
            # Default banner for other modules
            banner = QLabel("🚀 Coming Soon")
            banner.setStyleSheet("""
                background: linear-gradient(90deg, #1e1e2e, #313244);
                color: #a6e3a1;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                font-size: 16px;
                border: 1px solid #45475a;
                margin-top: 20px;
            """)
            layout.addWidget(banner)
        
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
            page = self.create_placeholder_page(title, desc, icon)
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
