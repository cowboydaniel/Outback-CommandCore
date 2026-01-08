#!/usr/bin/env python3
"""PC Tools Module - PySide6 Version

This module serves as a bridge to the refactored PC Tools module in nest.ui.modules.pc_tools
It allows the main Nest application to continue to import from nest.ui.pc_tools while
we transition to the new modular architecture.

This module can also run as a standalone application.
"""

import importlib
import importlib.util
import os
import sys
import time
import platform
import threading
import tempfile
import re
import math
import glob
import shutil
import logging
import subprocess
import queue
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QStyleFactory,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QIcon

PCX_DIR = Path(__file__).resolve().parents[1]
if str(PCX_DIR) not in sys.path:
    sys.path.insert(0, str(PCX_DIR))

from app import config
from core.base import ensure_logs_dir, get_paths
from core.utils import (
    check_and_install_dependencies,
    check_and_setup_sudoers,
    configure_logging,
    setup_passwordless_sudo,
)
from tabs import (
    tab_benchmarks,
    tab_diagnostics,
    tab_hardware,
    tab_network,
    tab_storage,
    tab_system,
    tab_utilities,
)

configure_logging()

ROOT_DIR, _ = get_paths()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
ensure_logs_dir(ROOT_DIR)

if platform.system() == "Linux":
    check_and_install_dependencies()
    if not os.path.exists(config.SUDOERS_FILE):
        setup_passwordless_sudo()


class PCToolsModule(QWidget):
    """PC Tools module for Nest - PySide6 Version"""

    # Class variables for caching SMART data
    smart_data_cache = {}
    smart_cache_timestamps = {}
    smart_cache_max_age = config.SMART_CACHE_MAX_AGE
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
            "smart_cache_max_age": PCToolsModule.smart_cache_max_age,
            "refresh_on_tab_switch": config.CACHE_CONFIG["refresh_on_tab_switch"],
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
        self.colors = dict(config.COLOR_PALETTE)

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
            "_cache_config": dict(config.CACHE_CONFIG),
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
        self.refresh_timer.start(config.LIVE_REFRESH_INTERVAL_MS)  # 1 second interval

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
        if not hasattr(self, "last_update_label"):
            return
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
        tab_system.setup_system_info_tab(self)

    def setup_hardware_tab(self):
        """Set up the Hardware tab with CPU, RAM, and GPU information."""
        tab_hardware.setup_hardware_tab(self)

    def setup_storage_tab(self):
        """Set up the Storage tab with disk and partition information."""
        tab_storage.setup_storage_tab(self)

    def setup_network_tab(self):
        """Set up the Network tab with interface and speed information."""
        tab_network.setup_network_tab(self)

    def setup_benchmarks_tab(self):
        """Set up the Benchmarks tab."""
        tab_benchmarks.setup_benchmarks_tab(self)

    def setup_utilities_tab(self):
        """Set up the Utilities tab."""
        tab_utilities.setup_utilities_tab(self)

    def setup_diagnostics_tab(self):
        """Set up the Diagnostics tab."""
        tab_diagnostics.setup_diagnostics_tab(self)

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
            if importlib.util.find_spec("speedtest") is None:
                QTimer.singleShot(0, lambda: self.phase_label.setText(
                    "speedtest-cli not installed. Run: pip install speedtest-cli"
                ))
                QTimer.singleShot(0, lambda: self.test_button.setEnabled(True))
                QTimer.singleShot(0, lambda: self.test_button.setText("Start Speed Test"))
                return

            speedtest = importlib.import_module("speedtest")
            try:
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
                    file_size = config.DISK_BENCHMARK_FILE_SIZE_BYTES  # 100MB
                    block_size = config.DISK_BENCHMARK_BLOCK_SIZE_BYTES

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

                # Simple CPU benchmark - calculate primes
                start = time.time()
                count = 0
                for num in range(2, config.CPU_BENCHMARK_MAX):
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
    if importlib.util.find_spec("PIL") is not None:
        from PIL import Image  # noqa: F401

        icon_path = ROOT_DIR / "icons" / "pc-x.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("PC Tools Module")
    main_window.setGeometry(100, 100, 1024, 768)

    # Create and set central widget
    pc_tools = PCToolsModule(main_window, {"name": "Test User"})
    main_window.setCentralWidget(pc_tools)

    main_window.show()
    sys.exit(app.exec())
