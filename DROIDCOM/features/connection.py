"""
DROIDCOM - Connection Feature Module
Handles device connection, WiFi ADB setup, and device list management.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import threading
import time
import re
import logging

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import append_text, emit_ui, schedule_ui


class ConnectionMixin:
    """Mixin class providing device connection functionality."""

    def setup_wifi_adb(self):
        """Setup ADB over WiFi for the connected device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self.parent, "Not Connected", "Please connect to a device first"
            )
            return

        # Create a status window
        status_window = QtWidgets.QDialog(self.parent)
        status_window.setWindowTitle("WiFi ADB Setup")
        status_window.resize(500, 300)
        layout = QtWidgets.QVBoxLayout(status_window)

        # Add a text widget for output
        output_text = QtWidgets.QPlainTextEdit()
        output_text.setReadOnly(True)
        output_text.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        layout.addWidget(output_text)

        # Show the dialog so user can see the status
        status_window.show()

        def update_output(message):
            def append_text():
                output_text.appendPlainText(message)
            emit_ui(self, append_text)

        # Start the setup process
        update_output("Setting up WiFi ADB...")

        # Get device IP address
        update_output("Getting device IP address...")
        adb_cmd = self.adb_path if self.adb_path else 'adb'

        # Try multiple interfaces: WiFi, hotspot/tethering, USB tethering
        interfaces = ['wlan0', 'ap0', 'swlan0', 'wlan1', 'rndis0', 'usb0']
        ip_address = None

        for iface in interfaces:
            try:
                ip_cmd = f"{adb_cmd} -s {self.device_serial} shell ip addr show {iface}"
                result = subprocess.check_output(ip_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result)
                if ip_match:
                    ip_address = ip_match.group(1)
                    update_output(f"Found IP on {iface}: {ip_address}")
                    break
            except subprocess.CalledProcessError:
                continue

        # Fallback: get all IPs and find a suitable one
        if not ip_address:
            try:
                ip_cmd = f"{adb_cmd} -s {self.device_serial} shell ip addr"
                result = subprocess.check_output(ip_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
                # Find all IPv4 addresses, excluding loopback
                all_ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)
                for ip in all_ips:
                    if not ip.startswith('127.'):
                        ip_address = ip
                        update_output(f"Found IP: {ip_address}")
                        break
            except subprocess.CalledProcessError:
                pass

        if not ip_address:
            update_output("Error: Could not find IP address.")
            update_output("Make sure WiFi or hotspot is enabled on the device.")
            return

        update_output(f"Device IP address: {ip_address}")

        # Enable ADB over TCP/IP
        try:
            update_output("Enabling ADB over TCP/IP...")
            tcp_cmd = f"{adb_cmd} -s {self.device_serial} tcpip 5555"
            tcp_result = subprocess.check_output(tcp_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            update_output(tcp_result)
        except subprocess.CalledProcessError as e:
            update_output(f"Error enabling TCP/IP: {e.output.decode('utf-8')}")
            return

        # Add connect button
        update_output("\nWaiting for USB disconnect to connect automatically...")

        def auto_connect():
            # Function to monitor USB disconnect and connect via WiFi
            threading.Thread(target=monitor_and_connect, args=(ip_address,), daemon=True).start()

        def monitor_and_connect(ip):
            # Check every second if device is disconnected
            update_output("Please disconnect the USB cable now...")

            # Wait for the device to disappear from USB devices
            while True:
                try:
                    devices_cmd = f"{adb_cmd} devices"
                    devices_output = subprocess.check_output(devices_cmd, shell=True).decode('utf-8')
                    if self.device_serial not in devices_output:
                        break
                    time.sleep(1)
                except Exception:
                    break

            # Try to connect via WiFi
            update_output(f"USB disconnected. Connecting to {ip}:5555...")
            try:
                connect_cmd = f"{adb_cmd} connect {ip}:5555"
                connect_result = subprocess.check_output(connect_cmd, shell=True).decode('utf-8')
                update_output(connect_result)

                # Check if connection was successful
                if 'connected' in connect_result.lower():
                    update_output("\nWiFi ADB connection successful!")
                    # Update device list to show the new wireless connection after brief delay
                    def refresh_with_delay():
                        time.sleep(1.0)
                        self.refresh_device_list()
                    threading.Thread(target=refresh_with_delay, daemon=True).start()
                else:
                    update_output(f"\nFailed to connect wirelessly. Please try manually:\nadb connect {ip}:5555")
            except Exception as e:
                update_output(f"Error connecting: {str(e)}")

        # Start monitoring for USB disconnect
        auto_connect()
        update_output("\nWiFi ADB setup initiated. Waiting for USB disconnect...")

    def connect_device(self):
        """Connect to the selected Android device"""
        if not self.platform_tools_installed:
            QtWidgets.QMessageBox.information(
                self.parent, "Not Installed", "Android Platform Tools are not installed."
            )
            return

        # Check if a device is selected
        selected_items = self.device_listbox.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.information(
                self.parent, "No Device Selected", "Please select a device from the list."
            )
            return

        # Check if the selected device might be offline
        device_entry = selected_items[0].text()
        if "DISCONNECTED" in device_entry:
            QtWidgets.QMessageBox.information(
                self.parent,
                "Device Offline",
                "The selected device appears to be offline and cannot be connected.\n\n"
                "Please use the 'Remove Offline' button to clear disconnected devices from the list.",
            )
            return

        # Start connecting in a separate thread
        threading.Thread(target=self._connect_device_task, args=(device_entry,), daemon=True).start()

    def _connect_device_task(self, device_entry):
        """Worker thread to connect to the selected Android device"""
        try:

            # Check if the device is marked as offline/disconnected
            if "DISCONNECTED" in device_entry or "Offline" in device_entry or "❌" in device_entry:
                emit_ui(self, lambda: self.log_message(f"Rejected connection attempt to offline device: {device_entry}"))
                emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                    self.parent,
                    "Device Offline",
                    "The selected device is offline and cannot be connected.\n\n"
                    "Please use the 'Remove Offline' button to clear disconnected devices from the list.",
                ))
                return

            # Extract the serial number from the device entry
            if '[' in device_entry:
                serial = device_entry.split('[')[0].strip()
            elif '(' in device_entry and ')' in device_entry:
                serial = device_entry.split('(')[1].split(')')[0].strip()
            else:
                serial = device_entry.strip()

            emit_ui(self, lambda: self.log_message(f"Connecting to device: {serial}"))
            emit_ui(self, lambda: self.update_status(f"Connecting to {serial}..."))

            # Get the platform tools path
            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            # Check if device is still connected
            result = subprocess.run(
                [adb_cmd, 'devices'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0 or serial not in result.stdout:
                emit_ui(self, lambda: self.log_message(f"Device {serial} not found or disconnected"))
                emit_ui(self, lambda: self.update_status("Device not found"))
                emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                    self.parent,
                    "Connection Error",
                    "Device not found or disconnected. Try refreshing the device list.",
                ))
                return

            # Get device information
            emit_ui(self, lambda: self.log_message("Retrieving device information..."))
            emit_ui(self, lambda: self.update_status("Getting device info..."))
            self.device_info = self._get_device_info(serial, adb_cmd)

            if self.device_info:
                self.device_connected = True
                self.device_serial = serial
                emit_ui(self, self.update_device_info)
                emit_ui(self, self.enable_device_actions)
                emit_ui(self, lambda: self.log_message("Device connected successfully"))
                emit_ui(self, lambda: self.update_status(f"Connected to {self.device_info.get('model', serial)}"))
            else:
                self.device_connected = False
                emit_ui(self, lambda: self.log_message("Failed to get device information"))
                emit_ui(self, lambda: self.update_status("Connection failed"))
                emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                    self.parent,
                    "Connection Error",
                    "Failed to get device information. The device may be locked or not responding.",
                ))

        except Exception as e:
            emit_ui(self, lambda: self.log_message(f"Error connecting to device: {str(e)}"))
            emit_ui(self, lambda: self.update_status("Connection failed"))
            emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                self.parent, "Connection Error", f"Failed to connect to device: {str(e)}"
            ))

    def auto_connect_sequence(self):
        """Start automatic device detection and connection"""
        self.auto_connecting = True
        self.log_message("Starting auto-connect sequence - will only connect to online devices")
        threading.Thread(target=self._auto_refresh_device_list_task, daemon=True).start()

    def _auto_refresh_device_list_task(self):
        """Worker thread for auto-refresh device list"""
        try:
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"
            emit_ui(self, lambda: self.update_status("Refreshing device list..."))

            result = subprocess.run(
                [adb_cmd, "devices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                emit_ui(self, lambda: self.update_status(f"Error refreshing device list: {result.stderr.strip()}"))
                return

            lines = result.stdout.strip().split("\n")
            devices = []

            for line in lines[1:]:
                if line.strip():
                    parts = line.strip().split("\t")
                    if len(parts) == 2:
                        serial, state = parts
                        if state == "device":
                            devices.append((serial, "✅ Ready"))
                        elif state == "unauthorized":
                            devices.append((serial, "⚠ Unauthorized"))
                        else:
                            devices.append((serial, f"❌ {state.capitalize()} (DISCONNECTED)"))

            def update_ui():
                self.device_listbox.clear()

                if devices:
                    for serial, state in devices:
                        if "DISCONNECTED" in state:
                            entry = f"{serial} [{state}]"
                        else:
                            entry = serial
                        self.device_listbox.addItem(entry)

                    # Select the first connected device
                    for i in range(self.device_listbox.count()):
                        entry = self.device_listbox.item(i).text()
                        if "DISCONNECTED" not in entry:
                            self.device_listbox.setCurrentRow(i)
                            break
                    else:
                        if self.device_listbox.count() > 0:
                            self.device_listbox.setCurrentRow(0)

                if getattr(self, 'auto_connecting', False):
                    self.log_message("Auto-connect mode detected - attempting to connect to first available device")
                    self.auto_connecting = False

                    connected_device_index = None
                    for i in range(self.device_listbox.count()):
                        entry = self.device_listbox.item(i).text()
                        if "DISCONNECTED" not in entry and "Offline" not in entry and "❌" not in entry:
                            connected_device_index = i
                            break

                    if connected_device_index is not None:
                        self.log_message(f"Found available device at index {connected_device_index} - initiating connection")
                        self.device_listbox.setCurrentRow(connected_device_index)
                        self.device_listbox.scrollToItem(
                            self.device_listbox.item(connected_device_index)
                        )
                        # Schedule connection on main thread (emit_ui handles thread marshalling)
                        emit_ui(self, self._trigger_connect)
                    else:
                        self.log_message("Auto-connect: No available devices found for automatic connection")
                else:
                    self.update_status("No devices found")

            emit_ui(self, update_ui)

        except subprocess.TimeoutExpired:
            emit_ui(self, lambda: self.log_message("Device list refresh timed out"))
            emit_ui(self, lambda: self.update_status("Timeout refreshing device list"))
        except Exception as e:
            logging.error(f"Error refreshing device list: {e}", exc_info=True)
            emit_ui(self, lambda: self.update_status(f"Error refreshing device list: {str(e)}"))

    def _trigger_connect(self):
        """Helper method to trigger the connect_device method after a short delay"""
        self.log_message("Triggering device connection...")
        self.connect_device()

    def remove_offline_devices(self):
        """Remove all offline devices from the list"""
        if not self.platform_tools_installed:
            QtWidgets.QMessageBox.information(
                self.parent, "Not Installed", "Android Platform Tools are not installed."
            )
            return
        threading.Thread(target=self._remove_offline_devices_task, daemon=True).start()

    def _remove_offline_devices_task(self):
        """Worker thread to remove offline devices from the list"""
        try:
            emit_ui(self, lambda: self.update_status("Removing offline devices..."))
            emit_ui(self, lambda: self.log_message("Removing offline devices from the list..."))

            if IS_WINDOWS:
                adb_cmd = self._find_adb_path()
                if not adb_cmd:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
            else:
                adb_cmd = 'adb'

            result = subprocess.run(
                [adb_cmd, 'devices'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                emit_ui(self, lambda: self.update_status("Failed to check connected devices"))
                emit_ui(self, lambda: self.log_message(
                    f"Error checking connected devices: {result.stderr.strip()}"
                ))
                return

            lines = result.stdout.strip().split('\n')
            connected_serials = []

            for line in lines[1:]:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        serial = parts[0]
                        status = parts[1]
                        if status == 'device':
                            connected_serials.append(serial)

            current_devices = []
            for i in range(self.device_listbox.count()):
                device_entry = self.device_listbox.item(i).text()
                if '[' in device_entry:
                    serial = device_entry.split('[')[0].strip()
                elif '(' in device_entry and ')' in device_entry:
                    serial = device_entry.split('(')[1].split(')')[0].strip()
                else:
                    serial = device_entry.strip()
                current_devices.append(serial)

            devices_to_remove = [s for s in current_devices if s not in connected_serials]

            def update_ui():
                self.device_listbox.clear()
                for serial in connected_serials:
                    self.device_listbox.addItem(serial)
                if self.device_listbox.count() > 0:
                    self.device_listbox.setCurrentRow(0)

            emit_ui(self, update_ui)

        except subprocess.TimeoutExpired:
            emit_ui(self, lambda: self.log_message("Device check timed out"))
            emit_ui(self, lambda: self.update_status("Timeout checking devices"))
        except Exception as e:
            emit_ui(self, lambda: self.update_status("Failed to remove offline devices"))
            emit_ui(self, lambda: self.log_message(f"Error removing offline devices: {str(e)}"))

    def refresh_device_list(self):
        """Refresh the list of connected devices"""
        if not getattr(self, 'auto_connecting', False):
            self.auto_connecting = False
        self._run_in_thread(self._refresh_device_list_task)

    def _refresh_device_list_task(self):
        """Worker thread to refresh the device list"""
        try:
            emit_ui(self, lambda: self.update_status("Refreshing device list..."))
            emit_ui(self, lambda: self.log_message("Refreshing list of connected Android devices..."))
            emit_ui(self, lambda: self.device_listbox.clear())

            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            result = subprocess.run(
                [adb_cmd, 'devices', '-l'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                emit_ui(self, lambda: self.log_message(
                    f"Error getting device list: {result.stderr.strip()}"
                ))
                emit_ui(self, lambda: self.update_status("Failed to get device list"))
                return

            lines = result.stdout.strip().split('\n')

            if len(lines) > 1:
                devices = []
                display_items = []

                for line in lines[1:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            serial = parts[0]
                            status = parts[1]

                            if status == 'device':
                                device_info = {
                                    'serial': serial,
                                    'status': status,
                                    'details': ' '.join(parts[2:]) if len(parts) > 2 else ''
                                }
                                devices.append(device_info)

                                # Extract model information for display
                                display_text = f"{device_info['serial']}"
                                if device_info['details']:
                                    for detail in device_info['details'].split():
                                        if detail.startswith('model:'):
                                            model_info = detail.split(':', 1)[1]
                                            display_text = f"{model_info} ({device_info['serial']})"
                                            break

                                display_items.append(display_text)

                if display_items:
                    def update_ui():
                        for item in display_items:
                            self.device_listbox.addItem(item)
                        self.log_message(f"Found {len(display_items)} connected device(s)")
                        self.update_status(f"{len(display_items)} device(s) found")

                    emit_ui(self, update_ui)
                else:
                    emit_ui(self, lambda: self.log_message("No connected devices found"))
                    emit_ui(self, lambda: self.update_status("No devices found"))
            else:
                emit_ui(self, lambda: self.log_message("No connected devices found"))
                emit_ui(self, lambda: self.update_status("No devices found"))

        except Exception as e:
            emit_ui(self, lambda: self.log_message(f"Error refreshing device list: {str(e)}"))
            emit_ui(self, lambda: self.update_status("Failed to refresh device list"))
