#!/usr/bin/env python3
"""PC Tools Module - Compatibility Bridge

This module serves as a bridge to the refactored PC Tools module in nest.ui.modules.pc_tools.
It allows the main Nest application to continue to import from nest.ui.pc_tools while
we transition to the new modular architecture.

This module can also run as a standalone application.
"""

from __future__ import annotations

import datetime
import getpass
import logging
import os
import platform
import psutil
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QDateTime, QThread, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QGroupBox,
)


def check_and_setup_sudoers(parent: Optional[QWidget] = None) -> Tuple[bool, str]:
    """
    Check if sudoers setup is needed and run it with a GUI prompt if required.

    Args:
        parent: Parent window for the dialog

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        test_cmd = ['sudo', '-n', 'smartctl', '--version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True, "Already configured with passwordless sudo access"

        if parent:
            response = QMessageBox.question(
                parent,
                "Elevated Permissions Required",
                "PC Tools requires elevated permissions to access hardware information.\n\n"
                "Would you like to set up passwordless sudo access now?\n\n"
                "You will be prompted for your password once.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if response != QMessageBox.Yes:
                return False, "User declined to set up passwordless sudo"

        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'setup_sudoers.sh')

        if not os.path.exists(script_path):
            return False, f"Setup script not found at {script_path}"

        os.chmod(script_path, 0o755)

        username = getpass.getuser()
        cmd = ['pkexec', '--user', 'root', 'bash', script_path]

        if parent:
            QMessageBox.information(
                parent,
                "Authentication Required",
                "You will now be prompted for your password to set up passwordless sudo access for "
                f"user '{username}'.",
            )

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True, "Successfully set up passwordless sudo access"

        error_msg = f"Failed to set up passwordless sudo: {result.stderr or 'Unknown error'}"
        if parent:
            QMessageBox.critical(parent, "Setup Failed", error_msg)
        return False, error_msg

    except Exception as exc:
        error_msg = f"Error setting up passwordless sudo: {exc}"
        if parent:
            QMessageBox.critical(parent, "Error", error_msg)
        return False, error_msg


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)


def check_and_install_dependencies() -> None:
    """Check for required system packages and install them if missing."""
    logging.info("Checking for required system packages...")

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
            'python3-pyside6': None,
            'sudo': 'sudo',
            'libcap2-bin': 'setcap',
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
            'python3-pyside6': None,
            'sudo': 'sudo',
            'libcap2': 'setcap',
        },
    }

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
    except Exception as exc:
        logging.error(f"Error detecting Linux distribution: {exc}")

    if not distro_family or platform.system() != 'Linux':
        logging.info("Auto-installation only supported on Linux. Skipping dependency check.")
        return

    install_cmd = 'apt-get -y install' if distro_family == 'debian' else 'dnf -y install'

    missing_tools = []
    for package, binary in required_tools[distro_family].items():
        if binary:
            which_cmd = f"which {binary} 2>/dev/null"
            if subprocess.run(which_cmd, shell=True).returncode != 0:
                missing_tools.append(package)
        else:
            if package == 'python3-pyside6':
                try:
                    import PySide6  # noqa: F401
                except ImportError:
                    missing_tools.append(package)

    if missing_tools:
        cmd = f"sudo {install_cmd} {' '.join(missing_tools)}"
        print(f"Installing missing tools with: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"Failed to install packages: {exc}")
            print("Please make sure you have sudo permissions or install the following packages manually:")
            print(" ".join(missing_tools))
        except Exception as exc:
            logging.error(f"Error installing system packages: {exc}")
    else:
        logging.info("All required system packages are already installed")


def setup_passwordless_sudo() -> bool:
    """Set up passwordless sudo for required commands."""
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
echo "# It will be automatically removed when the application is uninstalled" >> "$SUDOERS_FILE"
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
echo "You may need to log out and log back in for all changes to take effect."
"""

    try:
        with open(Path('/tmp/pc_tools_sudoers_setup.sh'), 'w', encoding='utf-8') as script_file:
            script_file.write(script_content)
        os.chmod(script_file.name, 0o755)

        print("Setting up passwordless sudo. You may be prompted for your password...")
        result = subprocess.run(['sudo', 'bash', script_file.name], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        try:
            os.unlink(script_file.name)
        except OSError:
            pass

        if result.returncode == 0:
            print("Successfully set up passwordless sudo!")
            return True

        print("Failed to set up passwordless sudo:")
        print(result.stderr)
        return False

    except Exception as exc:
        print(f"Error setting up passwordless sudo: {exc}")
        return False


if platform.system() == 'Linux':
    check_and_install_dependencies()
    if not os.path.exists("/etc/sudoers.d/99-nest-pc-tools"):
        setup_passwordless_sudo()


class UpdateCheckThread(QThread):
    success = Signal(str, str)
    error = Signal(str)

    def run(self) -> None:
        updates_count = "Unknown"
        last_update = "Unknown"
        try:
            if os.path.exists('/usr/bin/apt') or os.path.exists('/bin/apt'):
                updates_count, last_update = self._check_updates_apt()
            elif os.path.exists('/usr/bin/dnf') or os.path.exists('/bin/dnf'):
                updates_count, last_update = self._check_updates_dnf()
            else:
                updates_count = "N/A"
                last_update = "N/A"
            self.success.emit(str(updates_count), str(last_update))
        except Exception as exc:
            self.error.emit(str(exc))

    @staticmethod
    def _check_updates_apt() -> Tuple[str, str]:
        try:
            result = subprocess.run(['apt', 'list', '--upgradable'], capture_output=True, text=True, timeout=10)
            updates = [line for line in result.stdout.splitlines() if '/' in line and not line.startswith('Listing...')]
            updates_count = str(len(updates))
        except Exception as exc:
            logging.error(f"APT update check failed: {exc}")
            updates_count = "Error checking"

        try:
            if os.path.exists('/var/lib/apt/periodic/update-success-stamp'):
                timestamp = os.path.getmtime('/var/lib/apt/periodic/update-success-stamp')
                last_update = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            else:
                history_result = subprocess.run(
                    "grep -h 'Start-Date' /var/log/apt/history.log 2>/dev/null | tail -n 1",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if history_result.returncode == 0 and history_result.stdout.strip():
                    last_line = history_result.stdout.strip()
                    last_update = last_line.replace("Start-Date:", "").strip() if "Start-Date:" in last_line else "No updates found"
                else:
                    last_update = "No history found"
        except Exception as exc:
            logging.error(f"APT last update time check failed: {exc}")
            last_update = "Error checking"

        return updates_count, last_update

    @staticmethod
    def _check_updates_dnf() -> Tuple[str, str]:
        try:
            result = subprocess.run(['dnf', 'check-update', '--quiet'], capture_output=True, text=True, timeout=15)
            if result.returncode == 100:
                updates = [line for line in result.stdout.splitlines() if line.strip() and not line.startswith('Last metadata')]
                updates_count = str(len(updates))
            elif result.returncode == 0:
                updates_count = "0"
            else:
                updates_count = f"Error ({result.returncode})"
        except Exception as exc:
            logging.error(f"DNF update check failed: {exc}")
            updates_count = "Error checking"

        try:
            result = subprocess.run(['dnf', 'history', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.splitlines()
                last_update = lines[2].strip() if len(lines) > 2 else "No history found"
            else:
                last_update = "No history found"
        except Exception as exc:
            logging.error(f"DNF history check failed: {exc}")
            last_update = "Error checking"

        return updates_count, last_update


class PCToolsModule(QWidget):
    """PC Tools module for Nest (PySide6 implementation)."""

    def __init__(self, parent: Optional[QWidget] = None, current_user: Optional[Dict[str, str]] = None):
        super().__init__(parent)
        self.current_user = current_user or {}

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
            "accent": "#00B8D4",
        }

        self.text_panels: Dict[str, QPlainTextEdit] = {}
        self.status_message = QLabel("Ready")
        self.last_update = QLabel("")
        self.update_thread: Optional[UpdateCheckThread] = None

        if platform.system() == 'Linux' and not hasattr(PCToolsModule, '_sudo_checked'):
            success, message = check_and_setup_sudoers(self.window())
            logging.info(f"Sudo setup check: {message}")
            PCToolsModule._sudo_checked = True

        self._build_ui()
        self._start_timer()
        self.refresh_all()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        header = QLabel("PC Tools & Diagnostics")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.colors['primary']};")
        main_layout.addWidget(header)

        status_group = QGroupBox("Tools Status")
        status_layout = QVBoxLayout(status_group)
        smartctl_available = shutil.which("smartctl") is not None
        lshw_available = shutil.which("lshw") is not None
        self.smartctl_label = QLabel(
            f"SMART Diagnostics Tools: {'✅ Available' if smartctl_available else '❌ Not Available'}"
        )
        self.lshw_label = QLabel(
            f"Hardware Info Tools: {'✅ Available' if lshw_available else '❌ Not Available'}"
        )
        status_layout.addWidget(self.smartctl_label)
        status_layout.addWidget(self.lshw_label)
        main_layout.addWidget(status_group)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.device_tab = QWidget()
        self.tools_tab = QWidget()
        self.tabs.addTab(self.device_tab, "Device Info")
        self.tabs.addTab(self.tools_tab, "PC Tools")

        self._build_device_tabs()
        self._build_tools_tabs()

        status_bar = QHBoxLayout()
        status_bar.addWidget(self.status_message)
        status_bar.addStretch(1)
        status_bar.addWidget(self.last_update)
        main_layout.addLayout(status_bar)

    def _build_device_tabs(self) -> None:
        layout = QVBoxLayout(self.device_tab)
        sub_tabs = QTabWidget()
        layout.addWidget(sub_tabs)

        for name in ["System", "Hardware", "Storage", "Network"]:
            sub_tab = QWidget()
            sub_layout = QVBoxLayout(sub_tab)

            button_row = QHBoxLayout()
            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(lambda checked=False, n=name.lower(): self.refresh_panel(n))
            button_row.addWidget(refresh_button)

            if name == "System":
                update_button = QPushButton("Check Updates")
                update_button.clicked.connect(self.check_system_updates)
                button_row.addWidget(update_button)

            button_row.addStretch(1)
            sub_layout.addLayout(button_row)

            text_panel = QPlainTextEdit()
            text_panel.setReadOnly(True)
            sub_layout.addWidget(text_panel)
            self.text_panels[name.lower()] = text_panel

            sub_tabs.addTab(sub_tab, name)

    def _build_tools_tabs(self) -> None:
        layout = QVBoxLayout(self.tools_tab)
        sub_tabs = QTabWidget()
        layout.addWidget(sub_tabs)

        for name in ["Benchmarks", "Utilities", "Diagnostics"]:
            sub_tab = QWidget()
            sub_layout = QVBoxLayout(sub_tab)

            if name == "Benchmarks":
                run_button = QPushButton("Run Sample Benchmark")
                run_button.clicked.connect(self._run_sample_benchmark)
                sub_layout.addWidget(run_button)

            text_panel = QPlainTextEdit()
            text_panel.setReadOnly(True)
            sub_layout.addWidget(text_panel)
            self.text_panels[name.lower()] = text_panel

            sub_tabs.addTab(sub_tab, name)

    def _start_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

    def _update_time(self) -> None:
        self.last_update.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"))

    def refresh_all(self) -> None:
        for panel in ["system", "hardware", "storage", "network", "benchmarks", "utilities", "diagnostics"]:
            self.refresh_panel(panel)
        self.status_message.setText("Ready")
        self.log_message("PC Tools module initialized")

    def refresh_panel(self, name: str) -> None:
        panel = self.text_panels.get(name)
        if not panel:
            return

        if name == "system":
            panel.setPlainText(self._build_system_info())
        elif name == "hardware":
            panel.setPlainText(self._build_hardware_info())
        elif name == "storage":
            panel.setPlainText(self._build_storage_info())
        elif name == "network":
            panel.setPlainText(self._build_network_info())
        elif name == "benchmarks":
            panel.setPlainText("Ready to run benchmarks. Click the button above to run a sample.")
        elif name == "utilities":
            panel.setPlainText("Utilities are available in the main application. Use this view for logs.")
        elif name == "diagnostics":
            panel.setPlainText("Diagnostics status is ready. Run checks from the main application.")

    def _build_system_info(self) -> str:
        uptime_seconds = time.time() - psutil.boot_time()
        uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))
        return "\n".join(
            [
                f"OS: {platform.platform()}",
                f"Hostname: {platform.node()}",
                f"Python: {platform.python_version()}",
                f"CPU Cores: {psutil.cpu_count(logical=True)}",
                f"Total Memory: {psutil.virtual_memory().total / (1024 ** 3):.1f} GB",
                f"Uptime: {uptime}",
            ]
        )

    def _build_hardware_info(self) -> str:
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        return "\n".join(
            [
                f"CPU Usage: {psutil.cpu_percent(interval=0.2)}%",
                f"CPU Frequency: {cpu_freq.current:.0f} MHz" if cpu_freq else "CPU Frequency: N/A",
                f"Memory Used: {mem.used / (1024 ** 3):.1f} GB",
                f"Memory Available: {mem.available / (1024 ** 3):.1f} GB",
            ]
        )

    def _build_storage_info(self) -> str:
        lines = []
        for partition in psutil.disk_partitions(all=False):
            usage = psutil.disk_usage(partition.mountpoint)
            lines.append(
                f"{partition.device} ({partition.mountpoint}) - {usage.used / (1024 ** 3):.1f} GB used / "
                f"{usage.total / (1024 ** 3):.1f} GB total"
            )
        if not lines:
            lines.append("No disk partitions detected.")
        return "\n".join(lines)

    def _build_network_info(self) -> str:
        lines = []
        for interface, addrs in psutil.net_if_addrs().items():
            lines.append(f"Interface: {interface}")
            for addr in addrs:
                lines.append(f"  {addr.family.name}: {addr.address}")
        if not lines:
            lines.append("No network interfaces detected.")
        return "\n".join(lines)

    def _run_sample_benchmark(self) -> None:
        panel = self.text_panels.get("benchmarks")
        if not panel:
            return
        start = time.time()
        sum(range(5000000))
        elapsed = time.time() - start
        panel.appendPlainText(f"Sample benchmark completed in {elapsed:.3f} seconds.")
        self.log_message("Sample benchmark completed")

    def check_system_updates(self) -> None:
        if self.update_thread and self.update_thread.isRunning():
            self.log_message("Update check already running.")
            return

        self.status_message.setText("Checking for updates...")
        self.update_thread = UpdateCheckThread(self)
        self.update_thread.success.connect(self._update_check_success)
        self.update_thread.error.connect(self._update_check_error)
        self.update_thread.start()

    def _update_check_success(self, updates_count: str, last_update: str) -> None:
        panel = self.text_panels.get("system")
        if panel:
            panel.appendPlainText(f"\nUpdates Available: {updates_count}\nLast System Update: {last_update}")
        self.status_message.setText("Update check complete")
        self.log_message(f"System update check complete. {updates_count} updates available.")

    def _update_check_error(self, error_msg: str) -> None:
        panel = self.text_panels.get("system")
        if panel:
            panel.appendPlainText(f"\nSystem update check failed: {error_msg}")
        self.status_message.setText("Update check failed")
        self.log_message(f"System update check failed: {error_msg}")

    def log_message(self, message: str) -> None:
        logging.info(message)
        for key in ("utilities", "diagnostics"):
            panel = self.text_panels.get(key)
            if panel:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                panel.appendPlainText(f"[{timestamp}] {message}")


__all__ = ['PCToolsModule']

logging.info("PC Tools module loaded - standalone implementation")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("PC Tools Module")
    window.resize(1024, 768)

    pctools_widget = PCToolsModule(window, {"name": "Test User"})
    window.setCentralWidget(pctools_widget)
    window.show()

    sys.exit(app.exec())
