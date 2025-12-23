"""
Help & Documentation Module for HackAttack
Provides user guides, API documentation, and help resources.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QSplitter, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HelpDocsGUI(QWidget):
    """Help & Documentation GUI."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up the help interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # Quick Start Tab
        quickstart_tab = self.create_quickstart_tab()
        self.tabs.addTab(quickstart_tab, "Quick Start")

        # User Guide Tab
        guide_tab = self.create_user_guide_tab()
        self.tabs.addTab(guide_tab, "User Guide")

        # API Reference Tab
        api_tab = self.create_api_reference_tab()
        self.tabs.addTab(api_tab, "API Reference")

        # FAQ Tab
        faq_tab = self.create_faq_tab()
        self.tabs.addTab(faq_tab, "FAQ")

        # About Tab
        about_tab = self.create_about_tab()
        self.tabs.addTab(about_tab, "About")

        layout.addWidget(self.tabs)

    def create_quickstart_tab(self):
        """Create the quick start tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setFont(QFont("Sans", 11))
        content.setHtml("""
            <h1 style='color: #89b4fa;'>Welcome to HackAttack</h1>
            <p>HackAttack is a professional security testing suite designed for authorized
            penetration testing and security assessments.</p>

            <h2 style='color: #a6e3a1;'>Getting Started</h2>
            <ol>
                <li><b>Device Discovery</b> - Start by scanning your network to discover devices</li>
                <li><b>Network Analysis</b> - Analyze network traffic and protocols</li>
                <li><b>Vulnerability Scanning</b> - Identify potential security issues</li>
                <li><b>Exploitation Testing</b> - Test identified vulnerabilities (with authorization)</li>
                <li><b>Report Generation</b> - Create comprehensive security reports</li>
            </ol>

            <h2 style='color: #a6e3a1;'>Important Notes</h2>
            <ul>
                <li style='color: #f38ba8;'><b>Authorization Required</b> - Always obtain proper authorization
                before testing any systems you do not own.</li>
                <li>Use stealth mode when testing production environments</li>
                <li>Document all findings for compliance purposes</li>
                <li>Follow responsible disclosure practices</li>
            </ul>

            <h2 style='color: #a6e3a1;'>Keyboard Shortcuts</h2>
            <table border='1' cellpadding='5' style='border-collapse: collapse;'>
                <tr><td><b>Ctrl+N</b></td><td>New Scan</td></tr>
                <tr><td><b>Ctrl+S</b></td><td>Save Results</td></tr>
                <tr><td><b>Ctrl+E</b></td><td>Export Report</td></tr>
                <tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>
                <tr><td><b>F1</b></td><td>Help</td></tr>
                <tr><td><b>Esc</b></td><td>Cancel Operation</td></tr>
            </table>
        """)
        layout.addWidget(content)

        return tab

    def create_user_guide_tab(self):
        """Create the user guide tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search
        search_row = QHBoxLayout()
        self.guide_search = QLineEdit()
        self.guide_search.setPlaceholderText("Search documentation...")
        self.guide_search.textChanged.connect(self.search_guide)
        search_row.addWidget(self.guide_search)
        layout.addLayout(search_row)

        # Splitter for TOC and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Table of contents
        self.toc = QTreeWidget()
        self.toc.setHeaderLabel("Contents")
        self.toc.itemClicked.connect(self.show_guide_section)

        # Build TOC
        topics = {
            "Introduction": ["Overview", "System Requirements", "Installation"],
            "Device Discovery": ["Network Scanning", "Host Detection", "Service Enumeration"],
            "Network Analysis": ["Packet Capture", "Protocol Analysis", "Traffic Monitoring"],
            "Vulnerability Scanning": ["Scan Types", "Custom Scans", "CVE Database"],
            "Exploitation": ["Payload Generation", "Exploit Modules", "Post-Exploitation"],
            "Mobile Tools": ["Android Testing", "iOS Testing", "Mobile Security"],
            "Forensics": ["File Analysis", "Memory Analysis", "Timeline"],
            "Reporting": ["Report Templates", "Export Formats", "Customization"],
        }

        for topic, subtopics in topics.items():
            item = QTreeWidgetItem([topic])
            for subtopic in subtopics:
                child = QTreeWidgetItem([subtopic])
                item.addChild(child)
            self.toc.addTopLevelItem(item)

        splitter.addWidget(self.toc)

        # Content area
        self.guide_content = QTextEdit()
        self.guide_content.setReadOnly(True)
        self.guide_content.setFont(QFont("Sans", 11))
        self.guide_content.setHtml("""
            <h1>User Guide</h1>
            <p>Select a topic from the table of contents to view its documentation.</p>
        """)
        splitter.addWidget(self.guide_content)

        splitter.setSizes([250, 550])
        layout.addWidget(splitter)

        return tab

    def create_api_reference_tab(self):
        """Create the API reference tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setFont(QFont("Monospace", 10))
        content.setHtml("""
            <h1 style='color: #89b4fa;'>API Reference</h1>

            <h2 style='color: #a6e3a1;'>Scanner Module</h2>
            <pre style='background: #313244; padding: 10px; border-radius: 5px;'>
class NetworkScanner:
    def __init__(self, target: str, ports: str = "1-1000"):
        '''Initialize network scanner'''

    def scan(self) -> List[ScanResult]:
        '''Perform network scan'''

    def get_services(self) -> Dict[int, str]:
        '''Get detected services'''
            </pre>

            <h2 style='color: #a6e3a1;'>Exploit Module</h2>
            <pre style='background: #313244; padding: 10px; border-radius: 5px;'>
class ExploitFramework:
    def load_module(self, name: str) -> Module:
        '''Load exploit module'''

    def set_target(self, host: str, port: int):
        '''Set target for exploitation'''

    def run(self) -> ExploitResult:
        '''Execute the exploit'''
            </pre>

            <h2 style='color: #a6e3a1;'>Report Module</h2>
            <pre style='background: #313244; padding: 10px; border-radius: 5px;'>
class ReportGenerator:
    def __init__(self, title: str, format: str = "html"):
        '''Initialize report generator'''

    def add_finding(self, finding: Finding):
        '''Add a security finding'''

    def generate(self, output_path: str):
        '''Generate the report'''
            </pre>
        """)
        layout.addWidget(content)

        return tab

    def create_faq_tab(self):
        """Create the FAQ tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        faq_list = QListWidget()
        faq_list.itemClicked.connect(lambda item: self.show_faq_answer(item, faq_answer))

        faqs = [
            ("How do I start a network scan?",
             "Go to Device Discovery, select your network range, and click 'Start Scan'. "
             "You can customize scan options including port ranges, timing, and stealth settings."),
            ("What is stealth mode?",
             "Stealth mode uses techniques to minimize detection by intrusion detection systems. "
             "This includes slower scanning speeds and randomized packet patterns."),
            ("How do I export my findings?",
             "Go to Settings & Reports, select your desired format (HTML, PDF, JSON), "
             "and click 'Generate Report'. You can also use Ctrl+E for quick export."),
            ("Is this tool legal to use?",
             "HackAttack is designed for AUTHORIZED security testing only. Always obtain "
             "written permission before testing systems. Unauthorized access is illegal."),
            ("How do I update the vulnerability database?",
             "Go to Settings, click 'Update Database'. The tool will download the latest "
             "CVE and exploit information from configured sources."),
            ("Can I create custom scan profiles?",
             "Yes, go to Settings, create a new profile, configure your preferred options, "
             "and save it. You can then select this profile for future scans."),
            ("What network interfaces are supported?",
             "HackAttack supports Ethernet, WiFi, and virtual interfaces. For packet capture, "
             "you may need to run with elevated privileges."),
            ("How do I troubleshoot connection issues?",
             "Check your firewall settings, ensure the target is reachable via ping, "
             "verify you have the correct permissions, and check the logs for details."),
        ]

        for question, _ in faqs:
            faq_list.addItem(question)

        layout.addWidget(faq_list)

        faq_answer = QTextEdit()
        faq_answer.setReadOnly(True)
        faq_answer.setPlaceholderText("Select a question to see the answer...")
        faq_answer.setMaximumHeight(200)
        layout.addWidget(faq_answer)

        # Store FAQs for answer lookup
        self.faqs = faqs

        return tab

    def create_about_tab(self):
        """Create the about tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setFont(QFont("Sans", 11))
        content.setHtml("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #89b4fa; font-size: 36px;'>HackAttack</h1>
                <p style='font-size: 18px; color: #a6adc8;'>Professional Security Testing Suite</p>
                <p style='font-size: 14px;'>Version 1.0.0</p>

                <hr style='border: 1px solid #45475a; margin: 20px 0;'>

                <p>A comprehensive penetration testing and security assessment toolkit
                designed for security professionals.</p>

                <h3 style='color: #a6e3a1;'>Features</h3>
                <ul style='text-align: left;'>
                    <li>Network Discovery & Scanning</li>
                    <li>Vulnerability Assessment</li>
                    <li>Exploitation Framework</li>
                    <li>Mobile Security Testing</li>
                    <li>Forensic Analysis</li>
                    <li>Automated Reporting</li>
                </ul>

                <h3 style='color: #a6e3a1;'>Credits</h3>
                <p>Built with PySide6 and Python</p>
                <p>Part of the CommandCore Security Suite</p>

                <hr style='border: 1px solid #45475a; margin: 20px 0;'>

                <p style='color: #f38ba8;'><b>Legal Disclaimer</b></p>
                <p style='font-size: 12px;'>This tool is intended for authorized security testing only.
                Unauthorized access to computer systems is illegal. Always obtain proper authorization
                before conducting any security assessments.</p>

                <p style='margin-top: 20px; color: #6c7086;'>© 2024 CommandCore. All rights reserved.</p>
            </div>
        """)
        layout.addWidget(content)

        return tab

    def search_guide(self, text):
        """Search the user guide."""
        # Highlight matching items in TOC
        for i in range(self.toc.topLevelItemCount()):
            item = self.toc.topLevelItem(i)
            matches = text.lower() in item.text(0).lower()
            for j in range(item.childCount()):
                child = item.child(j)
                child_matches = text.lower() in child.text(0).lower()
                child.setHidden(bool(text) and not child_matches and not matches)
            item.setHidden(bool(text) and not matches and
                          all(item.child(j).isHidden() for j in range(item.childCount())))

    def show_guide_section(self, item, column):
        """Show the selected guide section."""
        section = item.text(0)

        # Section content
        content = {
            "Overview": "<h2>Overview</h2><p>HackAttack is a comprehensive security testing suite...</p>",
            "System Requirements": "<h2>System Requirements</h2><ul><li>Python 3.8+</li><li>PySide6</li><li>Linux/macOS/Windows</li></ul>",
            "Network Scanning": "<h2>Network Scanning</h2><p>Use the network scanner to discover hosts and services on your network...</p>",
            "Packet Capture": "<h2>Packet Capture</h2><p>Capture and analyze network packets in real-time...</p>",
            "Scan Types": "<h2>Scan Types</h2><p>Various scan types are available: SYN, Connect, UDP, etc...</p>",
        }

        html = content.get(section, f"<h2>{section}</h2><p>Documentation for this section is being prepared.</p>")
        self.guide_content.setHtml(html)

    def show_faq_answer(self, item, answer_widget):
        """Show the answer for selected FAQ."""
        index = item.listWidget().row(item)
        if index >= 0 and index < len(self.faqs):
            question, answer = self.faqs[index]
            answer_widget.setHtml(f"<h3>{question}</h3><p>{answer}</p>")
