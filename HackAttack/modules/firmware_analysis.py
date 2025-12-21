import sys
import os
import subprocess
import json
import platform
import hashlib
import warnings
from datetime import datetime

# Suppress specific warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Set environment variable to suppress IBus warning
os.environ["QT_LOGGING_RULES"] = "qt.dbus.integration.warning=false"

# Import PySide6 components with error handling for standalone execution
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QLabel, QPushButton, QFileDialog,
                                   QTextEdit, QGroupBox, QFormLayout, QLineEdit,
                                   QProgressBar, QTabWidget, QTreeWidget, QTreeWidgetItem,
                                   QHeaderView, QSplitter, QStatusBar)
    from PySide6.QtCore import Qt, QThread, Signal
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("Error: PySide6 is required to run this application.")
    sys.exit(1)

class FirmwareAnalysisGUI(QWidget):
    """
    Firmware & OS Analysis module for Hack Attack
    Provides tools for analyzing firmware images and operating systems
    """
    def __init__(self):
        super().__init__()
        self.current_firmware = None
        self.init_ui()
        self.apply_styles()
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-size: 13px;
            }
            QTreeWidget, QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                background: #1e1e2e;
                margin: 0px;
                padding: 0px;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 100px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
                min-height: 25px;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                background: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 4px;
                margin-top: 1em;
                padding: 10px;
                color: #cdd6f4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #89b4fa;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e2e;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #1e1e2e;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #45475a;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.tab_firmware = self.create_firmware_tab()
        self.tab_os = self.create_os_tab()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.tab_firmware, "Firmware Analysis")
        self.tabs.addTab(self.tab_os, "OS Analysis")
        
        main_layout.addWidget(self.tabs)
    
    def create_firmware_tab(self):
        """Create the Firmware Analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top section - File selection and info
        top_group = QGroupBox("Firmware Image")
        top_layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_firmware)
        
        top_layout.addWidget(QLabel("Firmware:"))
        top_layout.addWidget(self.file_path, 1)
        top_layout.addWidget(browse_btn)
        top_group.setLayout(top_layout)
        
        # Middle section - Analysis controls
        ctrl_group = QGroupBox("Analysis Controls")
        ctrl_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Analyze Firmware")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.analyze_firmware)
        
        self.extract_btn = QPushButton("Extract Files")
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.extract_firmware)
        
        ctrl_layout.addWidget(self.analyze_btn)
        ctrl_layout.addWidget(self.extract_btn)
        ctrl_layout.addStretch()
        ctrl_group.setLayout(ctrl_layout)
        
        # Bottom section - Results
        result_group = QGroupBox("Analysis Results")
        result_layout = QVBoxLayout()
        
        # Create tabs for different types of results
        result_tabs = QTabWidget()
        
        # File info tab
        file_info_tab = QWidget()
        file_info_layout = QFormLayout()
        
        self.file_info = QTextEdit()
        self.file_info.setReadOnly(True)
        file_info_layout.addRow(self.file_info)
        file_info_tab.setLayout(file_info_layout)
        
        # Binary analysis tab
        bin_analysis_tab = QWidget()
        bin_analysis_layout = QVBoxLayout()
        
        self.bin_analysis = QTextEdit()
        self.bin_analysis.setReadOnly(True)
        bin_analysis_layout.addWidget(self.bin_analysis)
        bin_analysis_tab.setLayout(bin_analysis_layout)
        
        # Strings tab
        strings_tab = QWidget()
        strings_layout = QVBoxLayout()
        
        self.strings_output = QTextEdit()
        self.strings_output.setReadOnly(True)
        strings_layout.addWidget(self.strings_output)
        strings_tab.setLayout(strings_layout)
        
        # Add tabs to results
        result_tabs.addTab(file_info_tab, "File Info")
        result_tabs.addTab(bin_analysis_tab, "Binary Analysis")
        result_tabs.addTab(strings_tab, "Strings")
        
        result_layout.addWidget(result_tabs)
        result_group.setLayout(result_layout)
        
        # Add all sections to main layout
        layout.addWidget(top_group)
        layout.addWidget(ctrl_group)
        layout.addWidget(result_group, 1)  # Give more space to results
        
        return tab
    
    def create_os_tab(self):
        """Create the OS Analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # OS Info section
        os_group = QGroupBox("Operating System Information")
        os_layout = QFormLayout()
        
        # Display basic OS info
        self.os_info = QTextEdit()
        self.os_info.setReadOnly(True)
        self.populate_os_info()
        
        os_layout.addRow(self.os_info)
        os_group.setLayout(os_layout)
        
        # System security checks
        sec_group = QGroupBox("Security Checks")
        sec_layout = QVBoxLayout()
        
        self.run_sec_btn = QPushButton("Run Security Checks")
        self.run_sec_btn.clicked.connect(self.run_security_checks)
        
        self.sec_results = QTextEdit()
        self.sec_results.setReadOnly(True)
        
        sec_layout.addWidget(self.run_sec_btn)
        sec_layout.addWidget(self.sec_results, 1)
        sec_group.setLayout(sec_layout)
        
        # Add all sections to main layout
        layout.addWidget(os_group)
        layout.addWidget(sec_group, 1)
        
        return tab
    
    def browse_firmware(self):
        """Open file dialog to select firmware image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware Image",
            "",
            "Firmware Images (*.bin *.img *.rom *.fw);;All Files (*)"
        )
        
        if file_path:
            self.file_path.setText(file_path)
            self.current_firmware = file_path
            self.analyze_btn.setEnabled(True)
            self.extract_btn.setEnabled(True)
            self.update_file_info(file_path)
    
    def update_file_info(self, file_path):
        """Update file information in the UI"""
        try:
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate hash
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            file_info = f"""
            <b>File:</b> {os.path.basename(file_path)}<br>
            <b>Path:</b> {file_path}<br>
            <b>Size:</b> {file_size:,} bytes<br>
            <b>Modified:</b> {modified_time}<br>
            <b>SHA-256:</b> {sha256_hash.hexdigest()}<br>
            """
            
            self.file_info.setHtml(f"<pre>{file_info}</pre>")
            
        except Exception as e:
            self.file_info.setText(f"Error reading file: {str(e)}")
    
    def analyze_firmware(self):
        """Analyze the selected firmware image"""
        if not self.current_firmware:
            return
            
        # Update UI
        self.bin_analysis.setText("Analyzing firmware...")
        self.strings_output.setText("Extracting strings...")
        
        # Run analysis in a separate thread
        self.analysis_thread = FirmwareAnalysisThread(self.current_firmware)
        self.analysis_thread.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_thread.start()
    
    def on_analysis_complete(self, results):
        """Handle analysis completion"""
        if 'error' in results:
            self.bin_analysis.setText(f"Error during analysis: {results['error']}")
            return
            
        if 'binwalk' in results:
            self.bin_analysis.setText(results['binwalk'])
            
        if 'strings' in results:
            self.strings_output.setText(results['strings'])
    
    def extract_firmware(self):
        """Extract files from firmware image"""
        if not self.current_firmware:
            return
            
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if output_dir:
            self.bin_analysis.append(f"\nExtracting files to: {output_dir}")
            # Here you would add the actual extraction logic
    
    def populate_os_info(self):
        """Populate OS information"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            os_info = f"""
            <b>System:</b> {system}<br>
            <b>Release:</b> {release}<br>
            <b>Version:</b> {version}<br>
            <b>Machine:</b> {machine}<br>
            <b>Processor:</b> {processor}<br>
            """
            
            # Add more detailed info based on OS
            if system == "Linux":
                try:
                    with open("/etc/os-release") as f:
                        os_release = {}
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                os_release[key] = value.strip('"')
                    
                    os_info += f"<b>Distribution:</b> {os_release.get('PRETTY_NAME', 'Unknown')}<br>"
                    os_info += f"<b>ID:</b> {os_release.get('ID', 'Unknown')}<br>"
                    os_info += f"<b>Version ID:</b> {os_release.get('VERSION_ID', 'Unknown')}<br>"
                except Exception as e:
                    os_info += f"<br><i>Could not read /etc/os-release: {str(e)}</i><br>"
            
            self.os_info.setHtml(f"<pre>{os_info}</pre>")
            
        except Exception as e:
            self.os_info.setText(f"Error getting OS info: {str(e)}")
    
    def run_security_checks(self):
        """Run basic security checks on the system"""
        self.sec_results.setText("Running security checks...")
        
        # Run security checks in a separate thread
        self.sec_thread = SecurityCheckThread()
        self.sec_thread.results_ready.connect(self.on_security_results)
        self.sec_thread.start()
    
    def on_security_results(self, results):
        """Display security check results"""
        if not results:
            self.sec_results.setText("No security check results available.")
            return
            
        report = "=== Security Check Report ===\n\n"
        
        for check, result in results.items():
            status = "[PASS]" if result['status'] else "[FAIL]"
            report += f"{status} {check}\n"
            report += f"   {result['description']}\n"
            if result.get('details'):
                report += f"   Details: {result['details']}\n\n"
        
        self.sec_results.setText(report)


class FirmwareAnalysisThread(QThread):
    """Thread for running firmware analysis in the background"""
    analysis_complete = Signal(dict)
    
    def __init__(self, firmware_path):
        super().__init__()
        self.firmware_path = firmware_path
    
    def run(self):
        results = {}
        
        try:
            # Run binwalk analysis
            try:
                binwalk_result = subprocess.run(
                    ['binwalk', self.firmware_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                results['binwalk'] = binwalk_result.stdout
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                results['binwalk'] = f"Binwalk not found or error: {str(e)}\n"
                if hasattr(e, 'stderr') and e.stderr:
                    results['binwalk'] += f"Error details: {e.stderr}\n"
            
            # Extract strings
            try:
                strings_result = subprocess.run(
                    ['strings', self.firmware_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                results['strings'] = strings_result.stdout[:10000] + "\n... (truncated)"  # Limit output size
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                results['strings'] = f"Error extracting strings: {str(e)}"
            
        except Exception as e:
            results['error'] = str(e)
        
        self.analysis_complete.emit(results)


class SecurityCheckThread(QThread):
    """Thread for running security checks in the background"""
    results_ready = Signal(dict)
    
    def run(self):
        results = {}
        
        # Check for common security issues
        self.check_sudo_perms(results)
        self.check_ssh_config(results)
        self.check_firewall_status(results)
        self.check_system_updates(results)
        
        self.results_ready.emit(results)
    
    def check_sudo_perms(self, results):
        """Check sudo permissions"""
        try:
            # Check if the current user has passwordless sudo
            test = subprocess.run(
                ['sudo', '-n', 'true'],
                stderr=subprocess.PIPE,
                text=True
            )
            
            if test.returncode == 0:
                results['sudo_perms'] = {
                    'status': False,
                    'description': 'Passwordless sudo is enabled',
                    'details': 'Passwordless sudo can be a security risk. Consider requiring a password for sudo commands.'
                }
            else:
                results['sudo_perms'] = {
                    'status': True,
                    'description': 'Sudo password is required',
                    'details': 'Good security practice: sudo requires authentication.'
                }
                
        except Exception as e:
            results['sudo_perms'] = {
                'status': False,
                'description': 'Error checking sudo permissions',
                'details': str(e)
            }
    
    def check_ssh_config(self, results):
        """Check SSH server configuration"""
        try:
            # Check if SSH server is running
            ssh_check = subprocess.run(
                ['systemctl', 'is-active', 'ssh'],
                capture_output=True,
                text=True
            )
            
            if ssh_check.returncode == 0:  # SSH is active
                # Check SSH config for common security settings
                config_checks = {
                    'PermitRootLogin': 'no',
                    'PasswordAuthentication': 'no',
                    'Protocol': '2',
                    'X11Forwarding': 'no'
                }
                
                try:
                    sshd_config = '/etc/ssh/sshd_config'
                    with open(sshd_config, 'r') as f:
                        config = f.read()
                    
                    issues = []
                    for setting, expected in config_checks.items():
                        if f"{setting} {expected}" not in config:
                            issues.append(f"{setting} should be set to {expected}")
                    
                    if issues:
                        results['ssh_config'] = {
                            'status': False,
                            'description': 'SSH server has potential security issues',
                            'details': '\n   '.join(issues)
                        }
                    else:
                        results['ssh_config'] = {
                            'status': True,
                            'description': 'SSH server configuration is secure',
                            'details': 'All recommended security settings are in place.'
                        }
                        
                except Exception as e:
                    results['ssh_config'] = {
                        'status': False,
                        'description': 'Error reading SSH configuration',
                        'details': str(e)
                    }
            else:
                results['ssh_config'] = {
                    'status': True,
                    'description': 'SSH server is not running',
                    'details': 'SSH service is not active, which reduces attack surface.'
                }
                
        except Exception as e:
            results['ssh_config'] = {
                'status': False,
                'description': 'Error checking SSH service',
                'details': str(e)
            }
    
    def check_firewall_status(self, results):
        """Check if firewall is active"""
        try:
            # Try ufw (Ubuntu)
            ufw = subprocess.run(
                ['sudo', 'ufw', 'status'],
                capture_output=True,
                text=True
            )
            
            if 'active (running)' in ufw.stdout.lower():
                results['firewall'] = {
                    'status': True,
                    'description': 'Firewall (UFW) is active',
                    'details': 'Firewall is properly configured and running.'
                }
                return
                
            # Try firewalld (RHEL/CentOS)
            firewalld = subprocess.run(
                ['sudo', 'firewall-cmd', '--state'],
                capture_output=True,
                text=True
            )
            
            if 'running' in firewalld.stdout.lower():
                results['firewall'] = {
                    'status': True,
                    'description': 'Firewall (firewalld) is active',
                    'details': 'Firewall is properly configured and running.'
                }
                return
                
            # If we get here, no active firewall was found
            results['firewall'] = {
                'status': False,
                'description': 'No active firewall detected',
                'details': 'Consider enabling and configuring a firewall for better security.'
            }
            
        except Exception as e:
            results['firewall'] = {
                'status': False,
                'description': 'Error checking firewall status',
                'details': str(e)
            }
    
    def check_system_updates(self, results):
        """Check if system updates are available"""
        try:
            # Check for updates based on the package manager
            if os.path.exists('/usr/bin/apt'):  # Debian/Ubuntu
                update_check = subprocess.run(
                    ['sudo', 'apt', 'update'],
                    stderr=subprocess.STDOUT,
                    stdout=subprocess.PIPE,
                    text=True
                )
                
                if update_check.returncode != 0:
                    results['updates'] = {
                        'status': False,
                        'description': 'Error checking for updates',
                        'details': 'Failed to update package lists.'
                    }
                    return
                
                upgrade_check = subprocess.run(
                    ['apt', 'list', '--upgradable'],
                    capture_output=True,
                    text=True
                )
                
                if upgrade_check.returncode == 0 and 'upgradable' in upgrade_check.stdout:
                    updates = [line.split('/')[0] for line in upgrade_check.stdout.split('\n') if '/focal' in line]
                    more_text = "... (more)" if len(updates) > 5 else ""
                    updates_text = ", ".join(updates[:5])
                    results['updates'] = {
                        'status': False,
                        'description': f'{len(updates)} updates available',
                        'details': f'Packages with updates: {updates_text}{more_text}'
                    }
                else:
                    results['updates'] = {
                        'status': True,
                        'description': 'System is up to date',
                        'details': 'All packages are at their latest versions.'
                    }
                    
            elif os.path.exists('/usr/bin/dnf'):  # Fedora/RHEL 8+
                try:
                    update_check = subprocess.run(
                        ['sudo', 'dnf', 'check-update', '--quiet'],
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        text=True
                    )
                    
                    if update_check.returncode == 100:  # Updates available
                        updates = [line.split()[0] for line in update_check.stdout.split('\n') if len(line.split()) > 1]
                        more_text = "... (more)" if len(updates) > 5 else ""
                        updates_text = ", ".join(updates[:5])
                        results['updates'] = {
                            'status': False,
                            'description': f'{len(updates)} updates available',
                            'details': f'Packages with updates: {updates_text}{more_text}'
                        }
                    elif update_check.returncode == 0:  # No updates
                        results['updates'] = {
                            'status': True,
                            'description': 'System is up to date',
                            'details': 'All packages are at their latest versions.'
                        }
                    else:  # Error
                        results['updates'] = {
                            'status': False,
                            'description': 'Error checking for updates',
                            'details': update_check.stderr or 'Unknown error'
                        }
                except Exception as e:
                    results['updates'] = {
                        'status': False,
                        'description': 'Error checking for updates',
                        'details': str(e)
                    }
                    
            else:
                results['updates'] = {
                    'status': None,
                    'description': 'Update check not implemented for this distribution',
                    'details': 'Automatic update checking is not supported for your package manager.'
                }
                
        except Exception as e:
            results['updates'] = {
                'status': False,
                'description': 'Error checking for updates',
                'details': str(e)
            }


def main():
    """Main function to run the Firmware & OS Analysis as a standalone application"""
    if not PYSIDE6_AVAILABLE:
        print("Error: PySide6 is required to run this application.")
        return 1
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Firmware & OS Analysis - Hack Attack")
    main_window.setMinimumSize(1000, 700)
    
    # Create the main widget and layout
    main_widget = QWidget()
    main_layout = QVBoxLayout()
    
    # Create and add the firmware analysis widget
    firmware_analysis = FirmwareAnalysisGUI()
    main_layout.addWidget(firmware_analysis)
    
    # Set the layout and show the window
    main_widget.setLayout(main_layout)
    main_window.setCentralWidget(main_widget)
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
