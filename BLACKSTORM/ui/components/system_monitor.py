"""System monitoring UI components for the dashboard."""
from __future__ import annotations

import os
import time
from typing import Dict, List, Tuple

import psutil
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QFrame,
)


class SystemMonitorDialog(QDialog):
    """Dialog showing system resource information with graphs."""

    def __init__(self, parent=None, show_cpu=True):
        super().__init__(parent)
        self.setWindowTitle("CPU Monitor" if show_cpu else "Memory Monitor")
        self.setMinimumSize(800, 600)
        self.show_cpu = show_cpu

        # Create the graph first
        self.graph = ResourceGraph()
        self.graph.set_line_color("#e74c3c" if show_cpu else "#9b59b6")

        # Set up the UI
        layout = QVBoxLayout(self)
        layout.addWidget(self.graph)

        # Add info text
        self.info_text = QLabel()
        self.info_text.setStyleSheet("font-family: Arial; font-size: 12px;")
        layout.addWidget(self.info_text)

        # Set window to full screen
        screen = self.screen().availableGeometry()
        self.setGeometry(screen)
        self.showMaximized()

        # Start the update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)  # Update every second

        # Initial update
        self.update_info()

    def update_info(self):
        """Update the displayed information."""
        if self.show_cpu:
            # Update CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.graph.add_data_point(cpu_percent)

            # Get CPU frequency
            try:
                freq = psutil.cpu_freq()
                freq_info = f"{freq.current:.0f} MHz" if freq else "N/A"
            except Exception:
                freq_info = "N/A"

            # Get CPU load average
            try:
                load_avg = " / ".join(f"{x:.2f}" for x in psutil.getloadavg())
            except Exception:
                load_avg = "N/A"

            # Get CPU count
            cpu_count = psutil.cpu_count()

            info_text = (
                f"<b>CPU Usage:</b> {cpu_percent:.1f}%<br>"
                f"<b>Frequency:</b> {freq_info}<br>"
                f"<b>Load Average:</b> {load_avg}<br>"
                f"<b>CPU Cores:</b> {cpu_count}"
            )
            self.info_text.setText(info_text)
        else:
            # Update memory info
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            percent = mem.percent

            self.graph.add_data_point(percent)

            # Get swap memory info
            swap = psutil.swap_memory()
            swap_used = swap.used / (1024 ** 3)
            swap_total = swap.total / (1024 ** 3) if swap.total > 0 else 0
            swap_percent = swap.percent if swap.total > 0 else 0

            info_text = (
                f"<b>Memory Usage:</b> {percent:.1f}%<br>"
                f"<b>Used:</b> {used_gb:.1f} GB / {total_gb:.1f} GB<br>"
                f"<b>Available:</b> {mem.available / (1024 ** 3):.1f} GB<br>"
                f"<b>Swap:</b> {swap_percent:.1f}% ({swap_used:.1f} GB / {swap_total:.1f} GB)"
            )
            self.info_text.setText(info_text)

    @staticmethod
    def _bytes_to_gb(bytes_value):
        """Convert bytes to gigabytes."""
        return bytes_value / (1024 ** 3)

    def closeEvent(self, event):
        """Clean up when closing the dialog."""
        if hasattr(self, "timer"):
            self.timer.stop()
        event.accept()


class SystemMonitor:
    """Class to monitor system resources like CPU and memory usage."""

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage as a percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            print(f"Error getting CPU usage: {e}")
            return 0.0

    @staticmethod
    def get_memory_usage() -> Tuple[float, float, float]:
        """Get memory usage statistics.

        Returns:
            tuple: (used_memory_gb, total_memory_gb, percent_used)
        """
        try:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)  # Convert to GB
            total_gb = mem.total / (1024 ** 3)  # Convert to GB
            return round(used_gb, 1), round(total_gb, 1), mem.percent
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return 0.0, 0.0, 0.0

    @staticmethod
    def show_cpu_monitor(parent=None):
        """Show the CPU information dialog."""
        try:
            dialog = SystemMonitorDialog(parent, show_cpu=True)
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            dialog.show()
        except Exception as e:
            print(f"Error showing CPU monitor: {e}")

    @staticmethod
    def show_memory_monitor(parent=None):
        """Show the memory information dialog."""
        try:
            dialog = SystemMonitorDialog(parent, show_cpu=False)
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            dialog.show()
        except Exception as e:
            print(f"Error showing memory monitor: {e}")

    @staticmethod
    def get_connected_devices() -> List[Dict[str, any]]:
        """
        Get a list of connected physical storage devices with their partitions.

        Returns:
            List[Dict[str, any]]: List of dictionaries containing device and partition information
        """
        print("\n=== Starting device detection ===")
        devices = []
        try:
            # First, get all physical block devices
            if not os.path.exists('/sys/block'):
                print("Error: /sys/block does not exist")
                return []

            print(f"Found devices in /sys/block: {os.listdir('/sys/block')}")

            for dev in os.listdir('/sys/block'):
                print(f"\nChecking device: {dev}")

                # Skip virtual and non-physical devices
                skip_prefixes = ['loop', 'ram', 'sr', 'dm-', 'zram', 'md', 'nbd', 'fd']
                if any(dev.startswith(x) for x in skip_prefixes):
                    print("  - Skipping (virtual/ignored device type)")
                    continue

                # Check if it's a partition (for non-NVMe devices)
                # NVMe devices have names like nvme0n1 (whole disk) and nvme0n1p1 (partition)
                is_nvme = dev.startswith('nvme')
                if is_nvme:
                    # For NVMe, check if it's a partition (ends with pX where X is a number)
                    if any(dev.endswith(f'p{i}') for i in range(10)):
                        print(f"  - Skipping (NVMe partition: {dev})")
                        continue
                else:
                    # For non-NVMe (sda, hda, etc.), check if it ends with a number
                    if any(dev[-1] == str(i) for i in range(10)):
                        print(f"  - Skipping (partition: {dev})")
                        continue

                dev_path = f"/dev/{dev}"
                print(f"  - Found potential storage device: {dev_path}")

                try:
                    # Get device information
                    size = 0
                    size_path = f'/sys/block/{dev}/size'
                    if os.path.exists(size_path):
                        with open(size_path, 'r') as f:
                            # Size is in 512-byte sectors
                            size = int(f.read().strip()) * 512

                    # Skip very small devices (likely virtual)
                    if size < 100 * 1024 * 1024:  # Less than 100MB
                        continue

                    # Get model and vendor
                    model = 'Unknown'
                    model_path = f'/sys/block/{dev}/device/model'
                    if os.path.exists(model_path):
                        with open(model_path, 'r') as f:
                            model = f.read().strip()

                    vendor = ''
                    vendor_path = f'/sys/block/{dev}/device/vendor'
                    if os.path.exists(vendor_path):
                        with open(vendor_path, 'r') as f:
                            vendor = f.read().strip()

                    # Skip RAM disks and other non-physical devices
                    if any(x in model.lower() for x in ['ram', 'virtual', 'nbd']):
                        continue

                    # Check if it's removable
                    is_removable = False
                    removable_path = f'/sys/block/{dev}/removable'
                    if os.path.exists(removable_path):
                        with open(removable_path, 'r') as f:
                            is_removable = f.read().strip() == '1'

                    # Get partitions for this device
                    partitions = []
                    if os.path.exists(f'/sys/block/{dev}'):
                        for item in os.listdir(f'/sys/block/{dev}'):
                            if item.startswith(dev) and item != dev:
                                part_path = f'/dev/{item}'
                                part_info = {
                                    'device': part_path,
                                    'mountpoint': '',
                                    'fstype': '',
                                    'size': 0,
                                    'number': item[len(dev):] if not is_nvme else item[len(dev)+1:]
                                }

                                # Get partition info from /proc/mounts
                                with open('/proc/mounts', 'r') as f:
                                    for line in f:
                                        fields = line.split()
                                        if fields[0] == part_path:
                                            part_info['mountpoint'] = fields[1]
                                            part_info['fstype'] = fields[2]
                                            break

                                # Get partition size
                                part_size_path = f'/sys/block/{dev}/{item}/size'
                                if os.path.exists(part_size_path):
                                    with open(part_size_path, 'r') as f:
                                        part_size = int(f.read().strip()) * 512  # 512-byte sectors
                                        part_info['size'] = round(part_size / (1024 ** 3), 1)  # Convert to GB

                                partitions.append(part_info)

                    # Create device info
                    device_info = {
                        'device': dev_path,
                        'model': model,
                        'vendor': vendor,
                        'size_gb': round(size / (1024 ** 3), 1),  # Convert to GB
                        'removable': is_removable,
                        'partitions': partitions
                    }

                    # Add to devices list
                    devices.append(device_info)

                except (PermissionError, OSError, ValueError) as e:
                    print(f"Error processing device {dev_path}: {e}")
                    continue

        except Exception as e:
            print(f"Error getting connected devices: {e}")

        return devices

    @staticmethod
    def get_connected_devices_count() -> int:
        """Get the count of connected storage devices."""
        try:
            return len(SystemMonitor.get_connected_devices())
        except Exception as e:
            print(f"Error getting connected devices count: {e}")
            return 0


class ResourceGraph(QGraphicsView):
    """Custom widget to display resource usage graphs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(600, 300)  # Increased minimum size for better visibility

        # Data storage - 600 seconds = 10 minutes of data points (1 per second)
        self.data_points = []
        self.max_points = 600  # Show 10 minutes of data (600 seconds)
        self.current_value = 0
        self.time_data = []  # Store timestamps for x-axis

        # Margins (left, top, right, bottom)
        self.margins = {
            'left': 50,    # Space for Y-axis labels
            'top': 40,     # Space for title/header
            'right': 20,   # Space for value display
            'bottom': 40   # Space for X-axis labels
        }

        # Colors - Dark theme
        self.background_color = QColor(30, 30, 40)  # Dark background
        self.grid_color = QColor(80, 80, 100, 100)  # Lighter grid lines for dark theme
        self.line_color = QColor(231, 76, 60)  # Default to CPU color (red)

        # Set up the scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Set up the view
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def set_line_color(self, color):
        """Set the line color for the graph."""
        self.line_color = QColor(color)

    def add_data_point(self, value):
        """Add a new data point to the graph."""
        self.current_value = value
        current_time = time.time()

        # Add the new data point with timestamp
        self.data_points.append(value)
        self.time_data.append(current_time)

        # Remove data points older than 1 hour
        while len(self.data_points) > 0 and (current_time - self.time_data[0]) > 3600:
            self.data_points.pop(0)
            self.time_data.pop(0)

        self.update_graph()

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_graph()

    def update_graph(self):
        """Update the graph with current data."""
        self.scene.clear()

        if not self.data_points:
            return

        # Get available size minus margins
        width = self.width() - self.margins['left'] - self.margins['right']
        height = self.height() - self.margins['top'] - self.margins['bottom']

        # Draw background for the entire widget
        self.scene.setBackgroundBrush(self.background_color)

        # Draw a dark rectangle for the plot area
        plot_area = QRectF(
            self.margins['left'],
            self.margins['top'],
            width,
            height,
        )
        self.scene.addRect(plot_area, self.grid_color, self.background_color)

        # Draw grid lines
        for i in range(5):
            y = self.margins['top'] + (height / 4) * i
            self.scene.addLine(self.margins['left'], y, self.margins['left'] + width, y, self.grid_color)

            # Add y-axis labels
            if i < 5:
                value = 100 - (i * 25)
                label = self.scene.addText(f"{value}%")
                label.setDefaultTextColor(Qt.GlobalColor.white)
                label.setPos(5, y - 10)

        # Draw x-axis labels (time)
        if len(self.data_points) > 0:
            # Calculate time labels
            current_time = time.time()
            # Create time labels for last 10 minutes (every 2 minutes)
            for i in range(0, 6):
                minutes_ago = (5 - i) * 2
                x_pos = self.margins['left'] + (width / 5) * i
                label_time = time.strftime('%H:%M', time.localtime(current_time - minutes_ago * 60))
                label = self.scene.addText(label_time)
                label.setDefaultTextColor(Qt.GlobalColor.white)
                label.setPos(x_pos - 20, self.margins['top'] + height + 5)

        # Draw graph line
        if len(self.data_points) > 1:
            path = self._create_graph_path(width, height)
            self.scene.addPath(path, self.line_color)

        # Draw current value
        value_text = self.scene.addText(f"{self.current_value:.1f}%")
        value_text.setDefaultTextColor(Qt.GlobalColor.white)
        value_text.setPos(self.width() - 60, 10)

    def _create_graph_path(self, width, height):
        """Create the graph path from data points."""
        path = QPainter().path()

        # Calculate the starting point
        x_step = width / (self.max_points - 1)
        x_start = self.margins['left']

        # Calculate the y position for each data point
        max_value = 100.0  # Percentage
        scale = height / max_value

        # Create path for data points
        first_point = True
        for i, value in enumerate(self.data_points):
            x = x_start + (i * x_step)
            y = self.margins['top'] + height - (value * scale)

            if first_point:
                path.moveTo(x, y)
                first_point = False
            else:
                path.lineTo(x, y)

        return path
