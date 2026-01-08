#!/usr/bin/env python3
"""PC Tools Module - PySide6 Version

This module serves as a bridge to the refactored PC Tools module in nest.ui.modules.pc_tools
It allows the main Nest application to continue to import from nest.ui.pc_tools while
we transition to the new modular architecture.

This module can also run as a standalone application.
"""

import os
import sys
import time
import platform
import datetime
import psutil
import threading
import tempfile
import re
import math
import glob
import shutil
import json
import logging
import importlib.util
import socket
import struct
import subprocess
import queue
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import getpass
import shlex

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTabWidget, QGroupBox, QComboBox,
    QTreeWidget, QTreeWidgetItem, QScrollArea, QSplitter, QProgressBar,
    QTextEdit, QMessageBox, QDialog, QSizePolicy, QSpacerItem, QStatusBar,
    QHeaderView, QStyleFactory
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThread, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap


def check_and_setup_sudoers(parent=None) -> Tuple[bool, str]:
    """
    Check if sudoers setup is needed and run it with a GUI prompt if required.

    Args:
        parent: Parent window for the dialog

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Check if we already have the required permissions
        test_cmd = ['sudo', '-n', 'smartctl', '--version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)

        # If the command succeeded, we already have passwordless sudo
        if result.returncode == 0:
            return True, "Already configured with passwordless sudo access"

        # If we get here, we need to set up passwordless sudo
        if parent:
            reply = QMessageBox.question(
                parent,
                "Elevated Permissions Required",
                "PC Tools requires elevated permissions to access hardware information.\n\n"
                "Would you like to set up passwordless sudo access now?\n\n"
                "You will be prompted for your password once.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False, "User declined to set up passwordless sudo"

        # Get the path to the setup script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'setup_sudoers.sh')

        if not os.path.exists(script_path):
            return False, f"Setup script not found at {script_path}"

        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Get the current username
        username = getpass.getuser()

        # Run the setup script with pkexec for GUI password prompt
        cmd = ['pkexec', '--user', 'root', 'bash', script_path]

        # Show a message that we're about to prompt for password
        if parent:
            QMessageBox.information(
                parent,
                "Authentication Required",
                f"You will now be prompted for your password to set up passwordless sudo access for user '{username}'."
            )

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True, "Successfully set up passwordless sudo access"
        else:
            error_msg = f"Failed to set up passwordless sudo: {result.stderr or 'Unknown error'}"
            if parent:
                QMessageBox.critical(parent, "Setup Failed", error_msg)
            return False, error_msg

    except Exception as e:
        error_msg = f"Error setting up passwordless sudo: {str(e)}"
        if parent:
            QMessageBox.critical(parent, "Error", error_msg)
        return False, error_msg


# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def check_and_install_dependencies():
    """Check for required system packages and install them if missing"""
    logging.info("Checking for required system packages...")

    # Define required tools by distro family
    required_tools = {
        'debian': {
            'smartmontools': 'smartctl',
            'lm-sensors': 'sensors',
            'dmidecode': 'dmidecode',
            'lshw': 'lshw',
            'pciutils': 'lspci',
            'parted': 'parted',
            'iw': 'iw',
            'ethtool': 'ethtool',
            'iputils-ping': 'ping',
            'speedtest-cli': 'speedtest-cli',
            'sudo': 'sudo',
            'libcap2-bin': 'setcap'
        },
        'redhat': {
            'smartmontools': 'smartctl',
            'lm_sensors': 'sensors',
            'dmidecode': 'dmidecode',
            'lshw': 'lshw',
            'pciutils': 'lspci',
            'parted': 'parted',
            'iw': 'iw',
            'ethtool': 'ethtool',
            'iputils': 'ping',
            'speedtest-cli': 'speedtest-cli',
            'sudo': 'sudo',
            'libcap2': 'setcap'
        }
    }

    # Detect distro family
    distro_family = None
    try:
        if os.path.exists('/etc/debian_version'):
            distro_family = 'debian'
        elif os.path.exists('/etc/redhat-release') or os.path.exists('/etc/fedora-release'):
            distro_family = 'redhat'
        else:
            try:
                import distro
                dist_id = distro.id()
                if dist_id in ['ubuntu', 'debian', 'linuxmint', 'pop']:
                    distro_family = 'debian'
                elif dist_id in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']:
                    distro_family = 'redhat'
            except ImportError:
                pass
    except Exception as e:
        logging.error(f"Error detecting Linux distribution: {e}")

    if not distro_family or platform.system() != 'Linux':
        logging.info("Auto-installation only supported on Linux. Skipping dependency check.")
        return

    # Determine installation command
    if distro_family == 'debian':
        install_cmd = 'apt-get -y install'
    elif distro_family == 'redhat':
        install_cmd = 'dnf -y install'

    # Check for missing tools
    missing_tools = []
    for package, binary in required_tools[distro_family].items():
        if binary:
            which_cmd = f"which {binary} 2>/dev/null"
            if subprocess.run(which_cmd, shell=True).returncode != 0:
                missing_tools.append(package)

    # Install missing tools if any
    if missing_tools:
        cmd = f"sudo {install_cmd} {' '.join(missing_tools)}"
        print(f"Installing missing tools with: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            print("Please make sure you have sudo permissions or install the following packages manually:")
            print(" ".join(missing_tools))
            return
        except Exception as e:
            logging.error(f"Error installing system packages: {e}")
    else:
        logging.info("All required system packages are already installed")


def setup_passwordless_sudo():
    """Set up passwordless sudo for required commands."""
    import stat

    if os.geteuid() == 0:
        return True

    script_content = """#!/bin/bash
set -e

CURRENT_USER=$(who am i | awk '{print $1}')
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(whoami)
fi

echo "Setting up passwordless sudo for user: $CURRENT_USER"

SUDOERS_FILE="/etc/sudoers.d/99-nest-pc-tools"

if [ -f "$SUDOERS_FILE" ]; then
    echo "Backing up existing sudoers file to ${SUDOERS_FILE}.bak"
    cp "$SUDOERS_FILE" "${SUDOERS_FILE}.bak"
fi

echo "# Allow $CURRENT_USER to run required commands without a password" > "$SUDOERS_FILE"
echo "# This file was automatically generated by Nest PC Tools" >> "$SUDOERS_FILE"
echo "" >> "$SUDOERS_FILE"

cat << 'EOT' >> "$SUDOERS_FILE"
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/smartctl *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/hdparm *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/fdisk *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/parted *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/lsblk *
CURRENT_USER ALL=(root) NOPASSWD: /bin/mount *
CURRENT_USER ALL=(root) NOPASSWD: /bin/umount *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/wipefs *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/sfdisk *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lshw *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/dmidecode *
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/hddtemp *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lspci *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lsusb *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/killall *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/pkexec *
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/setcap *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/journalctl *
CURRENT_USER ALL=(root) NOPASSWD: /bin/cat /var/log/*
EOT

sed -i "s/CURRENT_USER/$CURRENT_USER/g" "$SUDOERS_FILE"
chmod 0440 "$SUDOERS_FILE"

if [ -x "/usr/sbin/smartctl" ]; then
    setcap cap_sys_rawio,cap_dac_override,cap_sys_admin,cap_sys_nice+ep /usr/sbin/smartctl 2>/dev/null || true
    echo "Set capabilities on smartctl for non-root access"
fi

echo ""
echo "Passwordless sudo setup complete!"
"""

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            script_path = f.name
            f.write(script_content)

        os.chmod(script_path, 0o755)

        print("Setting up passwordless sudo. You may be prompted for your password...")
        result = subprocess.run(['sudo', 'bash', script_path],
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              text=True)

        try:
            os.unlink(script_path)
        except:
            pass

        if result.returncode == 0:
            print("Successfully set up passwordless sudo!")
            return True
        else:
            print("Failed to set up passwordless sudo:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"Error setting up passwordless sudo: {e}")
        return False


# Run dependency check when module is imported
if platform.system() == 'Linux':
    check_and_install_dependencies()
    if not os.path.exists("/etc/sudoers.d/99-nest-pc-tools"):
        setup_passwordless_sudo()

# Get the absolute path to this file
THIS_FILE = os.path.abspath(__file__)
UI_DIR = os.path.dirname(THIS_FILE)
NEST_DIR = os.path.dirname(UI_DIR)
ROOT_DIR = os.path.dirname(NEST_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

os.makedirs(os.path.join(ROOT_DIR, 'logs'), exist_ok=True)


class PCToolsModule(QWidget):
    """PC Tools module for Nest - PySide6 Version"""

    # Class variables for caching SMART data
    smart_data_cache = {}
    smart_cache_timestamps = {}
    smart_cache_max_age = 600
    sudo_authenticated = False
    smartctl_capabilities_set = False

    def __init__(self, parent=None, current_user=None):
        """Initialize the PC Tools module."""
        super().__init__(parent)

        if platform.system() == 'Linux':
            check_and_install_dependencies()

            if not hasattr(PCToolsModule, '_sudo_checked'):
                success, message = check_and_setup_sudoers(self)
                logging.info(f"Sudo setup check: {message}")
                PCToolsModule._sudo_checked = True

        self.parent_widget = parent
        self.refresh_timer = None

        # Initialize cache configuration
        self.cache_config = {
            'smart_cache_max_age': PCToolsModule.smart_cache_max_age,
            'refresh_on_tab_switch': True
        }
        self.current_user = current_user or {}
        self.threads = []
        self.log_text_widget = None

        # Session start time for performance tracking
        self.session_start_time = time.time()

        # Initialize performance metrics
        self.performance_metrics = {
            'startup_time': 0,
            'tab_switch_times': [],
            'data_load_times': {}
        }

        # Initialize colors
        self.colors = {
            "primary": "#017E84",
            "primary_dark": "#016169",
            "secondary": "#4CAF50",
            "warning": "#FF9800",
            "danger": "#F44336",
            "background": "#F5F5F5",
            "card_bg": "#FFFFFF",
            "text_primary": "#212121",
            "text_secondary": "#757575",
            "border": "#E0E0E0",
            "highlight": "#E6F7F7",
            "accent": "#00B8D4"
        }

        # Initialize shared state
        self.shared_state = {
            "current_user": current_user,
            "system_info": {},
            "diagnostic_results": {},
            "benchmark_results": {},
            "colors": self.colors,
            "refresh_callbacks": {},
            "_session_id": f"pc_tools_session_{int(time.time())}",
            "_timestamps": {},
            "_performance": self.performance_metrics,
            "_cache_config": {
                "enabled": True,
                "ttl": 300,
                "refresh_on_tab_switch": True
            }
        }

        self.cache_config = self.shared_state["_cache_config"]
        self.tab_instances = {}

        # Label dictionaries for updating
        self.system_info_labels = {}
        self.hardware_info_labels = {}
        self.storage_info_labels = {}

        # Selected drive for SMART info
        self.selected_drive = None

        # Update queue for thread-safe UI updates
        self.update_queue = queue.Queue()

        # Create the UI
        self.create_widgets()

    def create_widgets(self):
        """Create the main UI widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Start the live refresh timer
        self.start_live_refresh()

        # Header with logo
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_label = QLabel("PC Tools & Diagnostics")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet(f"color: {self.colors['primary']};")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        main_layout.addWidget(header_frame)

        # Tools Status frame
        status_group = QGroupBox("Tools Status")
        status_layout = QVBoxLayout(status_group)

        smartctl_available = shutil.which("smartctl") is not None
        tools_status = "Available" if smartctl_available else "Not Available"
        status_icon = "\u2705" if smartctl_available else "\u274C"

        self.smartctl_label = QLabel(f"SMART Diagnostics Tools: {status_icon} {tools_status}")
        self.smartctl_label.setFont(QFont("Arial", 10))
        status_layout.addWidget(self.smartctl_label)

        lshw_available = shutil.which("lshw") is not None
        lshw_status = "Available" if lshw_available else "Not Available"
        lshw_icon = "\u2705" if lshw_available else "\u274C"

        self.lshw_label = QLabel(f"Hardware Info Tools: {lshw_icon} {lshw_status}")
        self.lshw_label.setFont(QFont("Arial", 10))
        status_layout.addWidget(self.lshw_label)

        main_layout.addWidget(status_group)

        # Main notebook/tabs
        self.notebook = QTabWidget()
        self.notebook.currentChanged.connect(self.on_tab_changed)

        # Create the two main tabs
        self.device_info_tab = QWidget()
        self.pc_tools_tab = QWidget()

        self.notebook.addTab(self.device_info_tab, "Device Info")
        self.notebook.addTab(self.pc_tools_tab, "PC Tools")

        # Create Device Info subtabs
        device_layout = QVBoxLayout(self.device_info_tab)
        device_layout.setContentsMargins(5, 5, 5, 5)

        self.device_notebook = QTabWidget()
        device_layout.addWidget(self.device_notebook)

        self.device_tabs = {}
        device_subtabs = ["System", "Hardware", "Storage", "Network"]

        for name in device_subtabs:
            tab = QWidget()
            self.device_notebook.addTab(tab, name)
            self.device_tabs[name.lower()] = tab

        # Create PC Tools subtabs
        tools_layout = QVBoxLayout(self.pc_tools_tab)
        tools_layout.setContentsMargins(5, 5, 5, 5)

        self.tools_notebook = QTabWidget()
        tools_layout.addWidget(self.tools_notebook)

        self.tools_tabs = {}
        tools_subtabs = ["Benchmarks", "Utilities", "Diagnostics"]

        for name in tools_subtabs:
            tab = QWidget()
            self.tools_notebook.addTab(tab, name)
            self.tools_tabs[name.lower()] = tab

        main_layout.addWidget(self.notebook)

        # Status bar
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet(f"background-color: {self.colors['border']};")
        status_bar_layout = QHBoxLayout(self.status_bar)
        status_bar_layout.setContentsMargins(8, 4, 8, 4)

        self.status_message_label = QLabel("Ready")
        self.status_message_label.setFont(QFont("Arial", 8))
        status_bar_layout.addWidget(self.status_message_label)

        status_bar_layout.addStretch()

        self.last_update_label = QLabel("")
        self.last_update_label.setFont(QFont("Arial", 8))
        status_bar_layout.addWidget(self.last_update_label)

        main_layout.addWidget(self.status_bar)

        # Set up tab contents
        self.setup_system_info_tab()
        self.setup_hardware_tab()
        self.setup_storage_tab()
        self.setup_network_tab()
        self.setup_benchmarks_tab()
        self.setup_utilities_tab()
        self.setup_diagnostics_tab()

        # Initial update
        self.update_last_update_time()
        self.refresh_system_info()

        self.log_message("PC Tools module initialized")
        self.update_status("Ready")

    def start_live_refresh(self):
        """Start the live refresh timer for real-time updates."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.live_refresh_callback)
        self.refresh_timer.start(1000)  # 1 second interval

    def live_refresh_callback(self):
        """Callback for live refresh timer."""
        try:
            # Update CPU usage
            if "CPU Usage" in self.hardware_info_labels:
                cpu_usage = f"{psutil.cpu_percent(interval=0)}%"
                self.hardware_info_labels["CPU Usage"].setText(cpu_usage)

            # Update CPU temperature
            if "CPU Temperature" in self.hardware_info_labels:
                temp = self.get_cpu_temp()
                self.hardware_info_labels["CPU Temperature"].setText(
                    f"{temp:.1f}\u00B0C" if temp else "N/A"
                )

            # Update memory usage
            if "Used Memory" in self.hardware_info_labels:
                mem = psutil.virtual_memory()
                self.hardware_info_labels["Used Memory"].setText(
                    f"{mem.used / (1024**3):.2f} GB ({mem.percent}%)"
                )
            if "Available Memory" in self.hardware_info_labels:
                mem = psutil.virtual_memory()
                self.hardware_info_labels["Available Memory"].setText(
                    f"{mem.available / (1024**3):.2f} GB"
                )

            # Update battery info if present
            if hasattr(self, 'battery_charge_label'):
                battery = psutil.sensors_battery()
                if battery:
                    self.battery_charge_label.setText(f"{battery.percent:.0f}%")

            if hasattr(self, 'battery_status_label'):
                battery = psutil.sensors_battery()
                if battery:
                    status = "Charging" if battery.power_plugged else "Discharging"
                    self.battery_status_label.setText(status)

            # Process update queue
            self.process_update_queue()

        except Exception as e:
            logging.debug(f"Error in live refresh: {e}")

    def on_tab_changed(self, index):
        """Handle tab change events."""
        self.update_last_update_time()

    def update_last_update_time(self):
        """Update the last update time display."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.setText(f"Last update: {current_time}")

    def update_status(self, message):
        """Update the status bar message."""
        self.status_message_label.setText(message)

    def log_message(self, message):
        """Log a message to the activity log."""
        logging.info(message)

        if self.log_text_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text_widget.append(f"[{timestamp}] {message}")

        if hasattr(self, 'utils_log') and self.utils_log:
            self.utils_log.append(message)

    def setup_system_info_tab(self):
        """Set up the System Information tab."""
        system_tab = self.device_tabs["system"]

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("System Information")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # Operating System Info
        os_group = QGroupBox("Operating System")
        os_layout = QGridLayout(os_group)

        os_info = [
            ("OS", platform.system()),
            ("OS Version", platform.version()),
            ("OS Release", platform.release()),
            ("Architecture", platform.machine()),
            ("Hostname", socket.gethostname()),
            ("Python Version", platform.python_version()),
        ]

        for row, (label, value) in enumerate(os_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            os_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            os_layout.addWidget(value_label, row, 1)
            self.system_info_labels[label] = value_label

        content_layout.addWidget(os_group)

        # User Info
        user_group = QGroupBox("User Information")
        user_layout = QGridLayout(user_group)

        user_info = [
            ("Current User", getpass.getuser()),
            ("Home Directory", os.path.expanduser("~")),
            ("Current Directory", os.getcwd()),
        ]

        for row, (label, value) in enumerate(user_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            user_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            user_layout.addWidget(value_label, row, 1)

        content_layout.addWidget(user_group)

        # Boot Time
        boot_group = QGroupBox("System Uptime")
        boot_layout = QGridLayout(boot_group)

        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0]
        except:
            boot_time = "Unknown"
            uptime_str = "Unknown"

        boot_info = [
            ("Boot Time", str(boot_time)),
            ("Uptime", uptime_str),
        ]

        for row, (label, value) in enumerate(boot_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            boot_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            boot_layout.addWidget(value_label, row, 1)
            self.system_info_labels[label] = value_label

        content_layout.addWidget(boot_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        # Set layout for the tab
        tab_layout = QVBoxLayout(system_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def setup_hardware_tab(self):
        """Set up the Hardware tab with CPU, RAM, and GPU information."""
        hardware_tab = self.device_tabs["hardware"]

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Hardware Information")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # CPU Information
        cpu_group = QGroupBox("CPU Information")
        cpu_layout = QGridLayout(cpu_group)

        # Detect CPU info
        cpu_model = "Unknown"
        cpu_cores = str(os.cpu_count()) if os.cpu_count() else "Unknown"
        cpu_freq = "Unknown"
        cpu_cache = "Unknown"

        try:
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split('\n'):
                        if line.startswith('model name'):
                            cpu_model = line.split(':', 1)[1].strip()
                        elif line.startswith('cpu MHz'):
                            freq = float(line.split(':')[1].strip())
                            cpu_freq = f"{freq:.2f} MHz"

                    cache_match = re.search(r'cache size\s+:\s+(\d+)\s+KB', cpuinfo)
                    if cache_match:
                        cache_kb = int(cache_match.group(1))
                        cpu_cache = f"{cache_kb / 1024:.1f} MB" if cache_kb >= 1024 else f"{cache_kb} KB"
        except Exception as e:
            logging.error(f"Error detecting CPU info: {e}")

        cpu_info = [
            ("CPU Model", cpu_model),
            ("CPU Cores", cpu_cores),
            ("CPU Cache", cpu_cache),
            ("CPU Frequency", cpu_freq),
            ("CPU Usage", f"{psutil.cpu_percent(interval=0.1)}%"),
            ("CPU Temperature", f"{self.get_cpu_temp():.1f}\u00B0C" if self.get_cpu_temp() else "N/A"),
        ]

        for row, (label, value) in enumerate(cpu_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            cpu_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            cpu_layout.addWidget(value_label, row, 1)
            self.hardware_info_labels[label] = value_label

        content_layout.addWidget(cpu_group)

        # Memory Information
        memory_group = QGroupBox("Memory Information")
        memory_layout = QGridLayout(memory_group)

        try:
            mem = psutil.virtual_memory()
            total_ram = f"{mem.total / (1024**3):.2f} GB"
            available_ram = f"{mem.available / (1024**3):.2f} GB"
            used_ram = f"{mem.used / (1024**3):.2f} GB ({mem.percent}%)"
            ram_speed = self.get_ram_speed()
        except:
            total_ram = available_ram = used_ram = ram_speed = "Unknown"

        memory_info = [
            ("Total Memory", total_ram),
            ("Available Memory", available_ram),
            ("Used Memory", used_ram),
            ("Memory Speed", ram_speed),
        ]

        for row, (label, value) in enumerate(memory_info):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            memory_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            memory_layout.addWidget(value_label, row, 1)
            if label in ["Used Memory", "Available Memory"]:
                self.hardware_info_labels[label] = value_label

        content_layout.addWidget(memory_group)

        # GPU Information
        gpu_group = QGroupBox("Graphics Information")
        gpu_layout = QGridLayout(gpu_group)

        gpu_info = self.get_gpu_info()
        gpu_temp = self.get_gpu_temp()
        gpu_freq = self.get_gpu_freq()

        row = 0
        for i, gpu in enumerate(gpu_info):
            label_widget = QLabel(f"GPU {i+1}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            gpu_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(gpu)
            value_label.setFont(QFont("Arial", 10))
            gpu_layout.addWidget(value_label, row, 1)
            row += 1

        # GPU Temperature
        temp_label = QLabel("GPU Temperature:")
        temp_label.setFont(QFont("Arial", 10, QFont.Bold))
        gpu_layout.addWidget(temp_label, row, 0)

        gpu_temp_value = QLabel(f"{gpu_temp:.1f}\u00B0C" if gpu_temp else "N/A")
        gpu_layout.addWidget(gpu_temp_value, row, 1)
        self.hardware_info_labels["GPU Temperature"] = gpu_temp_value
        row += 1

        # GPU Frequency
        freq_label = QLabel("GPU Frequency:")
        freq_label.setFont(QFont("Arial", 10, QFont.Bold))
        gpu_layout.addWidget(freq_label, row, 0)

        gpu_freq_value = QLabel(f"{gpu_freq:.0f} MHz" if gpu_freq else "N/A")
        gpu_layout.addWidget(gpu_freq_value, row, 1)
        self.hardware_info_labels["GPU Frequency"] = gpu_freq_value

        content_layout.addWidget(gpu_group)

        # Battery Information
        battery_group = QGroupBox("Battery Information")
        battery_layout = QGridLayout(battery_group)

        battery_info = self.get_battery_info()

        if battery_info['present']:
            battery_data = [
                ("Battery Device", battery_info['device']),
                ("Model/Manufacturer", battery_info['model']),
                ("Serial Number", battery_info['serial']),
                ("Charge Level", f"{battery_info['capacity']}%"),
                ("Status", battery_info['status']),
                ("Health", battery_info['health']),
                ("Recommendation", battery_info['recommendation']),
            ]

            for row, (label, value) in enumerate(battery_data):
                label_widget = QLabel(f"{label}:")
                label_widget.setFont(QFont("Arial", 10, QFont.Bold))
                battery_layout.addWidget(label_widget, row, 0)

                value_label = QLabel(str(value))
                value_label.setFont(QFont("Arial", 10))
                battery_layout.addWidget(value_label, row, 1)

                if label == "Charge Level":
                    self.battery_charge_label = value_label
                elif label == "Status":
                    self.battery_status_label = value_label
                elif label == "Health":
                    self.battery_health_label = value_label
        else:
            no_battery = QLabel("No battery detected on this system")
            no_battery.setFont(QFont("Arial", 10, QFont.Italic))
            battery_layout.addWidget(no_battery, 0, 0, 1, 2)

        content_layout.addWidget(battery_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        tab_layout = QVBoxLayout(hardware_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def setup_storage_tab(self):
        """Set up the Storage tab with disk and partition information."""
        storage_tab = self.device_tabs["storage"]

        # Create main splitter
        splitter = QSplitter(Qt.Vertical)

        # Top section - Partitions
        partitions_group = QGroupBox("Disk Partitions")
        partitions_layout = QVBoxLayout(partitions_group)

        # Partition tree
        self.partition_tree = QTreeWidget()
        self.partition_tree.setHeaderLabels(["Device", "Size", "Type", "Mount Point", "File System"])
        self.partition_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        try:
            result = subprocess.run(
                ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE', '--json'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)

                for device in data.get('blockdevices', []):
                    device_item = QTreeWidgetItem([
                        f"/dev/{device['name']}",
                        device.get('size', ''),
                        device.get('type', ''),
                        device.get('mountpoint', '') or '',
                        device.get('fstype', '') or ''
                    ])
                    self.partition_tree.addTopLevelItem(device_item)

                    for child in device.get('children', []):
                        child_item = QTreeWidgetItem([
                            f"/dev/{child['name']}",
                            child.get('size', ''),
                            child.get('type', ''),
                            child.get('mountpoint', '') or '',
                            child.get('fstype', '') or ''
                        ])
                        device_item.addChild(child_item)

                    device_item.setExpanded(True)
        except Exception as e:
            logging.error(f"Error getting partition info: {e}")

        partitions_layout.addWidget(self.partition_tree)

        # Check partition scheme button
        scheme_btn = QPushButton("Check Partition Scheme")
        scheme_btn.clicked.connect(lambda: self.check_partition_scheme())
        partitions_layout.addWidget(scheme_btn)

        splitter.addWidget(partitions_group)

        # Bottom section - SMART Data
        smart_group = QGroupBox("SMART Data")
        smart_layout = QVBoxLayout(smart_group)

        # Drive selection
        drive_frame = QFrame()
        drive_layout = QHBoxLayout(drive_frame)
        drive_layout.setContentsMargins(0, 0, 0, 0)

        drive_label = QLabel("Select Drive:")
        drive_label.setFont(QFont("Arial", 10, QFont.Bold))
        drive_layout.addWidget(drive_label)

        self.drive_combo = QComboBox()
        drives = self.list_block_devices()
        self.drive_combo.addItems(drives)
        if drives:
            self.selected_drive = drives[0]
        self.drive_combo.currentTextChanged.connect(self.on_drive_selected)
        drive_layout.addWidget(self.drive_combo)

        drive_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_smart_info)
        drive_layout.addWidget(refresh_btn)

        smart_layout.addWidget(drive_frame)

        # SMART info display
        self.smart_info_text = QTextEdit()
        self.smart_info_text.setReadOnly(True)
        self.smart_info_text.setFont(QFont("Courier", 9))
        smart_layout.addWidget(self.smart_info_text)

        splitter.addWidget(smart_group)

        # Set initial splitter sizes
        splitter.setSizes([300, 400])

        tab_layout = QVBoxLayout(storage_tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        tab_layout.addWidget(splitter)

        # Initial SMART info load
        if drives:
            self.refresh_smart_info()

    def setup_network_tab(self):
        """Set up the Network tab with interface and speed information."""
        network_tab = self.device_tabs["network"]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Network Information")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # Network Interfaces
        interfaces_group = QGroupBox("Network Interfaces")
        interfaces_layout = QVBoxLayout(interfaces_group)

        try:
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for iface, addrs in net_if_addrs.items():
                iface_frame = QGroupBox(iface)
                iface_layout = QGridLayout(iface_frame)

                row = 0
                for addr in addrs:
                    if addr.family.name == 'AF_INET':
                        label = QLabel("IPv4 Address:")
                        label.setFont(QFont("Arial", 9, QFont.Bold))
                        iface_layout.addWidget(label, row, 0)
                        iface_layout.addWidget(QLabel(addr.address), row, 1)
                        row += 1
                    elif addr.family.name == 'AF_INET6':
                        label = QLabel("IPv6 Address:")
                        label.setFont(QFont("Arial", 9, QFont.Bold))
                        iface_layout.addWidget(label, row, 0)
                        iface_layout.addWidget(QLabel(addr.address[:30] + "..."), row, 1)
                        row += 1
                    elif addr.family.name == 'AF_PACKET':
                        label = QLabel("MAC Address:")
                        label.setFont(QFont("Arial", 9, QFont.Bold))
                        iface_layout.addWidget(label, row, 0)
                        iface_layout.addWidget(QLabel(addr.address), row, 1)
                        row += 1

                # Stats
                if iface in net_if_stats:
                    stats = net_if_stats[iface]
                    label = QLabel("Status:")
                    label.setFont(QFont("Arial", 9, QFont.Bold))
                    iface_layout.addWidget(label, row, 0)
                    status = "Up" if stats.isup else "Down"
                    iface_layout.addWidget(QLabel(status), row, 1)
                    row += 1

                    label = QLabel("Speed:")
                    label.setFont(QFont("Arial", 9, QFont.Bold))
                    iface_layout.addWidget(label, row, 0)
                    speed = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"
                    iface_layout.addWidget(QLabel(speed), row, 1)

                interfaces_layout.addWidget(iface_frame)
        except Exception as e:
            logging.error(f"Error getting network info: {e}")
            interfaces_layout.addWidget(QLabel(f"Error: {e}"))

        content_layout.addWidget(interfaces_group)

        # Speed Test Section
        speed_group = QGroupBox("Internet Speed Test")
        speed_layout = QVBoxLayout(speed_group)

        # Results display
        results_frame = QFrame()
        results_layout = QGridLayout(results_frame)

        results_layout.addWidget(QLabel("Server:"), 0, 0)
        self.server_label = QLabel("Not tested")
        results_layout.addWidget(self.server_label, 0, 1)

        results_layout.addWidget(QLabel("Download:"), 1, 0)
        self.download_speed = QLabel("--")
        self.download_speed.setFont(QFont("Arial", 14, QFont.Bold))
        results_layout.addWidget(self.download_speed, 1, 1)

        results_layout.addWidget(QLabel("Upload:"), 2, 0)
        self.upload_speed = QLabel("--")
        self.upload_speed.setFont(QFont("Arial", 14, QFont.Bold))
        results_layout.addWidget(self.upload_speed, 2, 1)

        results_layout.addWidget(QLabel("Ping:"), 3, 0)
        self.ping_label = QLabel("--")
        results_layout.addWidget(self.ping_label, 3, 1)

        speed_layout.addWidget(results_frame)

        # Progress bar
        self.speed_progress = QProgressBar()
        self.speed_progress.setValue(0)
        speed_layout.addWidget(self.speed_progress)

        self.phase_label = QLabel("Click 'Start Speed Test' to begin")
        speed_layout.addWidget(self.phase_label)

        # Test button
        self.test_button = QPushButton("Start Speed Test")
        self.test_button.clicked.connect(self.run_speed_test)
        speed_layout.addWidget(self.test_button)

        content_layout.addWidget(speed_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        tab_layout = QVBoxLayout(network_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def setup_benchmarks_tab(self):
        """Set up the Benchmarks tab."""
        benchmarks_tab = self.tools_tabs["benchmarks"]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("System Benchmarks")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # Disk Benchmark
        disk_group = QGroupBox("Disk Speed Test")
        disk_layout = QVBoxLayout(disk_group)

        disk_info = QLabel("Test sequential read/write speeds of your storage devices.")
        disk_layout.addWidget(disk_info)

        # Results display
        self.disk_results = QTextEdit()
        self.disk_results.setReadOnly(True)
        self.disk_results.setMaximumHeight(150)
        disk_layout.addWidget(self.disk_results)

        disk_btn = QPushButton("Run Disk Benchmark")
        disk_btn.clicked.connect(self.run_disk_speed_test)
        disk_layout.addWidget(disk_btn)

        content_layout.addWidget(disk_group)

        # CPU Benchmark placeholder
        cpu_group = QGroupBox("CPU Benchmark")
        cpu_layout = QVBoxLayout(cpu_group)

        cpu_info = QLabel("Test CPU performance with multi-threaded workloads.")
        cpu_layout.addWidget(cpu_info)

        self.cpu_results = QTextEdit()
        self.cpu_results.setReadOnly(True)
        self.cpu_results.setMaximumHeight(150)
        cpu_layout.addWidget(self.cpu_results)

        cpu_btn = QPushButton("Run CPU Benchmark")
        cpu_btn.clicked.connect(self.run_cpu_benchmark)
        cpu_layout.addWidget(cpu_btn)

        content_layout.addWidget(cpu_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        tab_layout = QVBoxLayout(benchmarks_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def setup_utilities_tab(self):
        """Set up the Utilities tab."""
        utilities_tab = self.tools_tabs["utilities"]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("System Utilities")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # System Cleanup
        cleanup_group = QGroupBox("System Cleanup")
        cleanup_layout = QVBoxLayout(cleanup_group)

        cleanup_info = QLabel("Clean temporary files and caches to free disk space.")
        cleanup_layout.addWidget(cleanup_info)

        cleanup_btn = QPushButton("Analyze Disk Space")
        cleanup_btn.clicked.connect(self.analyze_disk_space)
        cleanup_layout.addWidget(cleanup_btn)

        content_layout.addWidget(cleanup_group)

        # Activity Log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)

        self.utils_log = QTextEdit()
        self.utils_log.setReadOnly(True)
        self.utils_log.setMaximumHeight(200)
        log_layout.addWidget(self.utils_log)

        content_layout.addWidget(log_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        tab_layout = QVBoxLayout(utilities_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def setup_diagnostics_tab(self):
        """Set up the Diagnostics tab."""
        diagnostics_tab = self.tools_tabs["diagnostics"]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("System Diagnostics")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet(f"color: {self.colors['primary']};")
        content_layout.addWidget(header)

        # Quick Diagnostics
        quick_group = QGroupBox("Quick System Check")
        quick_layout = QVBoxLayout(quick_group)

        quick_info = QLabel("Run a quick diagnostic check on your system.")
        quick_layout.addWidget(quick_info)

        self.diag_results = QTextEdit()
        self.diag_results.setReadOnly(True)
        self.diag_results.setMaximumHeight(250)
        quick_layout.addWidget(self.diag_results)

        quick_btn = QPushButton("Run Quick Diagnostics")
        quick_btn.clicked.connect(self.run_quick_diagnostics)
        quick_layout.addWidget(quick_btn)

        content_layout.addWidget(quick_group)

        # Logs viewer
        logs_group = QGroupBox("System Logs")
        logs_layout = QVBoxLayout(logs_group)

        self.log_text_widget = QTextEdit()
        self.log_text_widget.setReadOnly(True)
        self.log_text_widget.setMaximumHeight(200)
        logs_layout.addWidget(self.log_text_widget)

        logs_btn = QPushButton("View Recent Logs")
        logs_btn.clicked.connect(self.view_system_logs)
        logs_layout.addWidget(logs_btn)

        content_layout.addWidget(logs_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)

        tab_layout = QVBoxLayout(diagnostics_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    # Helper methods

    def get_cpu_temp(self):
        """Get CPU temperature."""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name in ['coretemp', 'k10temp', 'zenpower', 'cpu_thermal']:
                        if name in temps and temps[name]:
                            return temps[name][0].current

                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current

            # Try lm-sensors
            result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if re.search(r'(Core|Tdie|CPU|Package).*\+[0-9.]+', line):
                        match = re.search(r'\+([0-9.]+)', line)
                        if match:
                            return float(match.group(1))
        except Exception as e:
            logging.debug(f"Error getting CPU temp: {e}")
        return None

    def get_gpu_temp(self):
        """Get GPU temperature."""
        try:
            if shutil.which('nvidia-smi'):
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())

            # Check hwmon
            card_path = '/sys/class/drm/card0/device/hwmon/'
            if os.path.exists(card_path):
                hwmon_dirs = glob.glob(os.path.join(card_path, 'hwmon*'))
                if hwmon_dirs:
                    temp_path = os.path.join(hwmon_dirs[0], 'temp1_input')
                    if os.path.exists(temp_path):
                        with open(temp_path, 'r') as f:
                            return int(f.read().strip()) / 1000.0
        except Exception as e:
            logging.debug(f"Error getting GPU temp: {e}")
        return None

    def get_gpu_freq(self):
        """Get GPU frequency."""
        try:
            if shutil.which('nvidia-smi'):
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=clocks.current.graphics', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())

            # Check sysfs for Intel
            cards = glob.glob('/sys/class/drm/card*')
            for card in cards:
                intel_path = os.path.join(card, 'gt_cur_freq_mhz')
                if os.path.exists(intel_path):
                    with open(intel_path, 'r') as f:
                        return float(f.read().strip())
        except Exception as e:
            logging.debug(f"Error getting GPU freq: {e}")
        return None

    def get_gpu_info(self):
        """Get GPU information."""
        gpu_list = []
        try:
            result = subprocess.run(['lspci', '-v'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "VGA" in line or "3D controller" in line:
                        full_desc = line.split(':', 1)[1].strip()
                        gpu_list.append(self.get_friendly_gpu_name(full_desc))
        except Exception as e:
            logging.error(f"Error getting GPU info: {e}")
        return gpu_list if gpu_list else ["Unknown"]

    def get_friendly_gpu_name(self, gpu_string):
        """Convert raw GPU identification to friendly name."""
        clean_name = gpu_string
        patterns_to_remove = [
            r'\[.*?\]', r'\(rev \w+\)', r'Corporation\s+',
            r'Technologies\s+Inc\.?\s*', r'Semiconductor\s+',
        ]
        for pattern in patterns_to_remove:
            clean_name = re.sub(pattern, ' ', clean_name, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', clean_name).strip()

    def get_ram_speed(self):
        """Get RAM speed."""
        try:
            result = subprocess.run(['sudo', 'dmidecode', '-t', 'memory'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Speed:' in line and 'Unknown' not in line:
                        return line.split(':')[1].strip()
        except Exception as e:
            logging.debug(f"Error getting RAM speed: {e}")
        return "Unknown"

    def get_battery_info(self):
        """Get battery information."""
        info = {
            'present': False,
            'device': 'N/A',
            'model': 'N/A',
            'serial': 'N/A',
            'capacity': 0,
            'status': 'N/A',
            'health': 'N/A',
            'recommendation': 'N/A'
        }

        try:
            battery = psutil.sensors_battery()
            if battery:
                info['present'] = True
                info['capacity'] = int(battery.percent)
                info['status'] = "Charging" if battery.power_plugged else "Discharging"
                info['device'] = "System Battery"

                if battery.percent > 80:
                    info['health'] = "Good"
                    info['recommendation'] = "Battery health is good"
                elif battery.percent > 40:
                    info['health'] = "Fair"
                    info['recommendation'] = "Consider charging soon"
                else:
                    info['health'] = "Low"
                    info['recommendation'] = "Please charge the battery"

                # Try to get more info from sysfs
                battery_paths = glob.glob('/sys/class/power_supply/BAT*')
                if battery_paths:
                    bat_path = battery_paths[0]
                    info['device'] = os.path.basename(bat_path)

                    model_path = os.path.join(bat_path, 'model_name')
                    if os.path.exists(model_path):
                        with open(model_path, 'r') as f:
                            info['model'] = f.read().strip()

                    serial_path = os.path.join(bat_path, 'serial_number')
                    if os.path.exists(serial_path):
                        with open(serial_path, 'r') as f:
                            info['serial'] = f.read().strip()
        except Exception as e:
            logging.debug(f"Error getting battery info: {e}")

        return info

    def list_block_devices(self):
        """List all block devices."""
        try:
            result = subprocess.run(['lsblk', '-dn', '-o', 'NAME'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=5)
            if result.returncode == 0:
                devices = [f"/dev/{dev}" for dev in result.stdout.strip().split('\n') if dev]
                return devices if devices else ["/dev"]
        except Exception as e:
            logging.error(f"Error listing block devices: {e}")
        return ["/dev"]

    def on_drive_selected(self, drive):
        """Handle drive selection change."""
        self.selected_drive = drive
        self.refresh_smart_info()

    def refresh_smart_info(self):
        """Refresh SMART information for the selected drive."""
        if not self.selected_drive:
            self.smart_info_text.setText("No drive selected")
            return

        self.smart_info_text.setText(f"Loading SMART data for {self.selected_drive}...")

        def worker():
            try:
                device = self.selected_drive
                dev_type = self.get_device_type(device)

                if not dev_type:
                    return "Unknown device type"

                result = subprocess.run(
                    ['sudo', 'smartctl', '-a', '-d', dev_type, device],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30
                )
                return result.stdout if result.returncode == 0 else result.stderr
            except Exception as e:
                return f"Error: {e}"

        # Run in thread
        thread = threading.Thread(target=lambda: self.update_smart_display(worker()))
        thread.daemon = True
        thread.start()

    def update_smart_display(self, text):
        """Update SMART display with text."""
        QTimer.singleShot(0, lambda: self.smart_info_text.setText(text))

    def get_device_type(self, device):
        """Determine device type for SMART commands."""
        if "nvme" in device:
            return "nvme"
        elif "sd" in device or "hd" in device:
            return "ata"
        return None

    def check_partition_scheme(self):
        """Check partition scheme for all disks."""
        results = []
        try:
            result = subprocess.run(['lsblk', '-dn', '-o', 'NAME'],
                                  stdout=subprocess.PIPE, text=True)
            disks = [f"/dev/{d}" for d in result.stdout.strip().split('\n') if d]

            for disk in disks:
                try:
                    parted = subprocess.run(['sudo', 'parted', '-s', disk, 'print'],
                                          capture_output=True, text=True, timeout=5)
                    for line in parted.stdout.splitlines():
                        if "Partition Table:" in line:
                            scheme = line.split(":")[1].strip()
                            results.append(f"{disk}: {scheme}")
                            break
                except:
                    results.append(f"{disk}: Unknown")

            if results:
                QMessageBox.information(self, "Partition Schemes", "\n".join(results))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to check partition schemes: {e}")

    def run_speed_test(self):
        """Run internet speed test."""
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")
        self.phase_label.setText("Initializing speed test...")
        self.speed_progress.setValue(0)

        def run_test():
            try:
                import speedtest
                st = speedtest.Speedtest()

                QTimer.singleShot(0, lambda: self.phase_label.setText("Finding best server..."))
                server = st.get_best_server()
                QTimer.singleShot(0, lambda: self.server_label.setText(
                    f"{server['name']} ({server['country']})"
                ))

                QTimer.singleShot(0, lambda: self.phase_label.setText("Testing download..."))
                QTimer.singleShot(0, lambda: self.speed_progress.setValue(25))
                download = st.download()
                QTimer.singleShot(0, lambda: self.download_speed.setText(
                    f"{download / 1_000_000:.2f} Mbps"
                ))

                QTimer.singleShot(0, lambda: self.phase_label.setText("Testing upload..."))
                QTimer.singleShot(0, lambda: self.speed_progress.setValue(50))
                upload = st.upload()
                QTimer.singleShot(0, lambda: self.upload_speed.setText(
                    f"{upload / 1_000_000:.2f} Mbps"
                ))

                results = st.results.dict()
                QTimer.singleShot(0, lambda: self.ping_label.setText(f"{results['ping']:.0f} ms"))
                QTimer.singleShot(0, lambda: self.speed_progress.setValue(100))
                QTimer.singleShot(0, lambda: self.phase_label.setText("Test completed!"))

            except ImportError:
                QTimer.singleShot(0, lambda: self.phase_label.setText(
                    "speedtest-cli not installed. Run: pip install speedtest-cli"
                ))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.phase_label.setText(f"Error: {e}"))
            finally:
                QTimer.singleShot(0, lambda: self.test_button.setEnabled(True))
                QTimer.singleShot(0, lambda: self.test_button.setText("Start Speed Test"))

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

    def run_disk_speed_test(self):
        """Run disk speed benchmark."""
        self.disk_results.setText("Running disk benchmark...")

        def run_test():
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_file = os.path.join(temp_dir, 'speedtest.tmp')
                    file_size = 100 * 1024 * 1024  # 100MB
                    block_size = 1024 * 1024

                    # Write test
                    start = time.time()
                    with open(test_file, 'wb') as f:
                        for _ in range(file_size // block_size):
                            f.write(os.urandom(block_size))
                            f.flush()
                            os.fsync(f.fileno())
                    write_time = time.time() - start
                    write_speed = (file_size / (1024 * 1024)) / write_time

                    # Read test
                    start = time.time()
                    with open(test_file, 'rb') as f:
                        while f.read(block_size):
                            pass
                    read_time = time.time() - start
                    read_speed = (file_size / (1024 * 1024)) / read_time

                    result = (
                        f"Disk Speed Test Results\n"
                        f"========================\n"
                        f"Test Size: 100 MB\n"
                        f"Write Speed: {write_speed:.2f} MB/s\n"
                        f"Read Speed: {read_speed:.2f} MB/s\n"
                    )
                    QTimer.singleShot(0, lambda: self.disk_results.setText(result))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.disk_results.setText(f"Error: {e}"))

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

    def run_cpu_benchmark(self):
        """Run CPU benchmark."""
        self.cpu_results.setText("Running CPU benchmark...")

        def run_test():
            try:
                import time
                import math

                # Simple CPU benchmark - calculate primes
                start = time.time()
                count = 0
                for num in range(2, 100000):
                    is_prime = True
                    for i in range(2, int(math.sqrt(num)) + 1):
                        if num % i == 0:
                            is_prime = False
                            break
                    if is_prime:
                        count += 1
                elapsed = time.time() - start

                result = (
                    f"CPU Benchmark Results\n"
                    f"=====================\n"
                    f"Test: Prime number calculation\n"
                    f"Range: 2 to 100,000\n"
                    f"Primes found: {count}\n"
                    f"Time: {elapsed:.2f} seconds\n"
                    f"Score: {int(10000 / elapsed)} points\n"
                )
                QTimer.singleShot(0, lambda: self.cpu_results.setText(result))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.cpu_results.setText(f"Error: {e}"))

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

    def analyze_disk_space(self):
        """Analyze disk space usage."""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("Disk Space Analysis:\n" + result.stdout)
            else:
                self.log_message("Failed to analyze disk space")
        except Exception as e:
            self.log_message(f"Error: {e}")

    def run_quick_diagnostics(self):
        """Run quick system diagnostics."""
        self.diag_results.setText("Running diagnostics...")

        results = []
        results.append("=== Quick System Diagnostics ===\n")

        # CPU check
        cpu_usage = psutil.cpu_percent(interval=1)
        status = "OK" if cpu_usage < 90 else "HIGH"
        results.append(f"CPU Usage: {cpu_usage}% [{status}]")

        # Memory check
        mem = psutil.virtual_memory()
        status = "OK" if mem.percent < 90 else "HIGH"
        results.append(f"Memory Usage: {mem.percent}% [{status}]")

        # Disk check
        disk = psutil.disk_usage('/')
        status = "OK" if disk.percent < 90 else "HIGH"
        results.append(f"Disk Usage: {disk.percent}% [{status}]")

        # Temperature check
        temp = self.get_cpu_temp()
        if temp:
            status = "OK" if temp < 80 else "HIGH"
            results.append(f"CPU Temperature: {temp:.1f}\u00B0C [{status}]")

        results.append("\n=== Diagnostics Complete ===")
        self.diag_results.setText("\n".join(results))

    def view_system_logs(self):
        """View recent system logs."""
        try:
            result = subprocess.run(
                ['journalctl', '-n', '50', '--no-pager'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.log_text_widget.setText(result.stdout)
            else:
                self.log_text_widget.setText("Failed to retrieve logs. Try running with sudo.")
        except Exception as e:
            self.log_text_widget.setText(f"Error: {e}")

    def refresh_system_info(self):
        """Refresh system information."""
        try:
            # Update uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            if "Uptime" in self.system_info_labels:
                self.system_info_labels["Uptime"].setText(str(uptime).split('.')[0])
            if "Boot Time" in self.system_info_labels:
                self.system_info_labels["Boot Time"].setText(str(boot_time))
        except Exception as e:
            logging.error(f"Error refreshing system info: {e}")

    def process_update_queue(self):
        """Process update queue for thread-safe UI updates."""
        try:
            while not self.update_queue.empty():
                item = self.update_queue.get_nowait()
                if item[0] == 'success':
                    self.update_ui_callback(item[1], item[2])
                elif item[0] == 'error':
                    self.update_error_callback(item[1])
                self.update_queue.task_done()
        except Exception as e:
            logging.debug(f"Error processing queue: {e}")

    def update_ui_callback(self, updates_count, last_update):
        """Update UI with update check results."""
        if "Updates Available" in self.system_info_labels:
            self.system_info_labels["Updates Available"].setText(str(updates_count))
        self.log_message(f"System update check complete. {updates_count} updates available.")

    def update_error_callback(self, error_msg):
        """Update UI with error status."""
        self.log_message(f"System update check failed: {error_msg}")


# Export the PCToolsModule for the main Nest application
__all__ = ['PCToolsModule']

# Log successful setup
logging.info("PC Tools module loaded - PySide6 implementation")


# For standalone execution
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle(QStyleFactory.create("Fusion"))

    # Set window icon
    try:
        from PIL import Image
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons', 'pc-x.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except:
        pass

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("PC Tools Module")
    main_window.setGeometry(100, 100, 1024, 768)

    # Create and set central widget
    pc_tools = PCToolsModule(main_window, {"name": "Test User"})
    main_window.setCentralWidget(pc_tools)

    main_window.show()
    sys.exit(app.exec())
