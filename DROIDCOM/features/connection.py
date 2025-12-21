"""
DROIDCOM - Connection Feature Module
Handles device connection, WiFi ADB setup, and device list management.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import re
import logging

from ..constants import IS_WINDOWS


class ConnectionMixin:
    """Mixin class providing device connection functionality."""

    def setup_wifi_adb(self):
        """Setup ADB over WiFi for the connected device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first")
            return

        # Create a status window
        status_window = tk.Toplevel(self.parent)
        status_window.title("WiFi ADB Setup")
        status_window.geometry("500x300")

        # Add a text widget for output
        output_text = scrolledtext.ScrolledText(status_window, wrap=tk.WORD)
        output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def update_output(message):
            output_text.insert(tk.END, message + "\n")
            output_text.see(tk.END)
            status_window.update()

        # Start the setup process
        update_output("Setting up WiFi ADB...")

        # Get device IP address
        update_output("Getting device IP address...")
        adb_cmd = self.adb_path if self.adb_path else 'adb'
        ip_cmd = f"{adb_cmd} -s {self.device_serial} shell ip addr show wlan0"
        try:
            result = subprocess.check_output(ip_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result)
            if not ip_match:
                update_output("Error: Could not find IP address. Make sure WiFi is enabled.")
                return

            ip_address = ip_match.group(1)
            update_output(f"Device IP address: {ip_address}")

            # Enable ADB over TCP/IP
            update_output("Enabling ADB over TCP/IP...")
            tcp_cmd = f"{adb_cmd} -s {self.device_serial} tcpip 5555"
            tcp_result = subprocess.check_output(tcp_cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            update_output(tcp_result)

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
                        # Update device list to show the new wireless connection
                        self.parent.after(1000, self.refresh_device_list)
                    else:
                        update_output(f"\nFailed to connect wirelessly. Please try manually:\nadb connect {ip}:5555")
                except Exception as e:
                    update_output(f"Error connecting: {str(e)}")

            # Start monitoring for USB disconnect
            auto_connect()
            update_output("\nWiFi ADB setup initiated. Waiting for USB disconnect...")

        except subprocess.CalledProcessError as e:
            update_output(f"Error: {e.output.decode('utf-8')}")

    def connect_device(self):
        """Connect to the selected Android device"""
        if not self.platform_tools_installed:
            messagebox.showinfo("Not Installed", "Android Platform Tools are not installed.")
            return

        # Check if a device is selected
        selected = self.device_listbox.curselection()
        if not selected:
            messagebox.showinfo("No Device Selected", "Please select a device from the list.")
            return

        # Check if the selected device might be offline
        device_entry = self.device_listbox.get(selected[0])
        if "DISCONNECTED" in device_entry:
            messagebox.showinfo("Device Offline",
                              "The selected device appears to be offline and cannot be connected.\n\n"
                              "Please use the 'Remove Offline' button to clear disconnected devices from the list.")
            return

        # Start connecting in a separate thread
        threading.Thread(target=self._connect_device_task, daemon=True).start()

    def _connect_device_task(self):
        """Worker thread to connect to the selected Android device"""
        try:
            selected = self.device_listbox.curselection()
            if not selected:
                self.after(0, lambda: messagebox.showinfo("No Device Selected", "Please select a device from the list"))
                return

            # Get the selected device serial
            device_entry = self.device_listbox.get(selected[0])

            # Check if the device is marked as offline/disconnected
            if "DISCONNECTED" in device_entry or "Offline" in device_entry or "❌" in device_entry:
                self.log_message(f"Rejected connection attempt to offline device: {device_entry}")
                self.after(0, lambda: messagebox.showinfo("Device Offline",
                    "The selected device is offline and cannot be connected.\n\n"
                    "Please use the 'Remove Offline' button to clear disconnected devices from the list."))
                return

            # Extract the serial number from the device entry
            if '[' in device_entry:
                serial = device_entry.split('[')[0].strip()
            elif '(' in device_entry and ')' in device_entry:
                serial = device_entry.split('(')[1].split(')')[0].strip()
            else:
                serial = device_entry.strip()

            self.log_message(f"Connecting to device: {serial}")
            self.update_status(f"Connecting to {serial}...")

            # Get the platform tools path
            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    self.update_status("ADB not found")
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
                self.log_message(f"Device {serial} not found or disconnected")
                self.update_status("Device not found")
                messagebox.showerror("Connection Error", "Device not found or disconnected. Try refreshing the device list.")
                return

            # Get device information
            self.log_message("Retrieving device information...")
            self.update_status("Getting device info...")
            self.device_info = self._get_device_info(serial, adb_cmd)

            if self.device_info:
                self.device_connected = True
                self.device_serial = serial
                self.after(0, self.update_device_info)
                self.after(0, self.enable_device_actions)
                self.log_message("Device connected successfully")
                self.update_status(f"Connected to {self.device_info.get('model', serial)}")
            else:
                self.device_connected = False
                self.log_message("Failed to get device information")
                self.update_status("Connection failed")
                messagebox.showerror("Connection Error",
                    "Failed to get device information. The device may be locked or not responding.")

        except Exception as e:
            self.log_message(f"Error connecting to device: {str(e)}")
            self.update_status("Connection failed")
            messagebox.showerror("Connection Error", f"Failed to connect to device: {str(e)}")

    def auto_connect_sequence(self):
        """Start automatic device detection and connection"""
        self.auto_connecting = True
        self.log_message("Starting auto-connect sequence - will only connect to online devices")
        threading.Thread(target=self._auto_refresh_device_list_task, daemon=True).start()

    def _auto_refresh_device_list_task(self):
        """Worker thread for auto-refresh device list"""
        try:
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"
            self.update_status("Refreshing device list...")

            result = subprocess.run(
                [adb_cmd, "devices"], capture_output=True, text=True, check=True
            )

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
                self.device_listbox.delete(0, tk.END)

                if devices:
                    for serial, state in devices:
                        if "DISCONNECTED" in state:
                            entry = f"{serial} [{state}]"
                        else:
                            entry = serial
                        self.device_listbox.insert(tk.END, entry)

                    # Select the first connected device
                    for i in range(self.device_listbox.size()):
                        entry = self.device_listbox.get(i)
                        if "DISCONNECTED" not in entry:
                            self.device_listbox.selection_set(i)
                            break
                    else:
                        if self.device_listbox.size() > 0:
                            self.device_listbox.selection_set(0)

                if getattr(self, 'auto_connecting', False):
                    self.log_message("Auto-connect mode detected - attempting to connect to first available device")
                    self.auto_connecting = False

                    connected_device_index = None
                    for i in range(self.device_listbox.size()):
                        entry = self.device_listbox.get(i)
                        if "DISCONNECTED" not in entry and "Offline" not in entry and "❌" not in entry:
                            connected_device_index = i
                            break

                    if connected_device_index is not None:
                        self.log_message(f"Found available device at index {connected_device_index} - initiating connection")
                        self.device_listbox.selection_clear(0, tk.END)
                        self.device_listbox.selection_set(connected_device_index)
                        self.device_listbox.see(connected_device_index)
                        self.after(100, self._trigger_connect)
                    else:
                        self.log_message("Auto-connect: No available devices found for automatic connection")
                else:
                    self.update_status("No devices found")

            self.after(0, update_ui)

        except Exception as e:
            logging.error(f"Error refreshing device list: {e}", exc_info=True)
            self.after(0, lambda: self.update_status(f"Error refreshing device list: {str(e)}"))

    def _trigger_connect(self):
        """Helper method to trigger the connect_device method after a short delay"""
        self.log_message("Triggering device connection...")
        self.connect_device()

    def remove_offline_devices(self):
        """Remove all offline devices from the list"""
        if not self.platform_tools_installed:
            messagebox.showinfo("Not Installed", "Android Platform Tools are not installed.")
            return
        threading.Thread(target=self._remove_offline_devices_task, daemon=True).start()

    def _remove_offline_devices_task(self):
        """Worker thread to remove offline devices from the list"""
        try:
            self.update_status("Removing offline devices...")
            self.log_message("Removing offline devices from the list...")

            if IS_WINDOWS:
                adb_cmd = self._find_adb_path()
                if not adb_cmd:
                    self.update_status("ADB not found")
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
                self.update_status("Failed to check connected devices")
                self.log_message(f"Error checking connected devices: {result.stderr.strip()}")
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
            for i in range(self.device_listbox.size()):
                device_entry = self.device_listbox.get(i)
                if '[' in device_entry:
                    serial = device_entry.split('[')[0].strip()
                elif '(' in device_entry and ')' in device_entry:
                    serial = device_entry.split('(')[1].split(')')[0].strip()
                else:
                    serial = device_entry.strip()
                current_devices.append(serial)

            devices_to_remove = [s for s in current_devices if s not in connected_serials]

            self.after(0, lambda: self.device_listbox.delete(0, tk.END))

            for serial in connected_serials:
                self.after(0, lambda s=serial: self.device_listbox.insert(tk.END, s))

            if devices_to_remove:
                self.update_status(f"Removed {len(devices_to_remove)} offline device(s)")
                self.log_message(f"Removed offline devices: {', '.join(devices_to_remove)}")
            else:
                self.update_status("No offline devices to remove")
                self.log_message("No offline devices found to remove")

            if self.device_listbox.size() > 0:
                self.after(0, lambda: self.device_listbox.selection_set(0))

        except Exception as e:
            self.update_status("Failed to remove offline devices")
            self.log_message(f"Error removing offline devices: {str(e)}")

    def refresh_device_list(self):
        """Refresh the list of connected devices"""
        if not getattr(self, 'auto_connecting', False):
            self.auto_connecting = False
        self._run_in_thread(self._refresh_device_list_task)

    def _refresh_device_list_task(self):
        """Worker thread to refresh the device list"""
        try:
            self.update_status("Refreshing device list...")
            self.log_message("Refreshing list of connected Android devices...")

            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    self.update_status("ADB not found")
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            self.after(0, lambda: self.device_listbox.delete(0, tk.END))

            result = subprocess.run(
                [adb_cmd, 'devices', '-l'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                self.log_message(f"Error getting device list: {result.stderr.strip()}")
                self.update_status("Failed to get device list")
                return

            lines = result.stdout.strip().split('\n')

            if len(lines) > 1:
                devices = []
                for line in lines[1:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            serial = parts[0]
                            status = parts[1]

                            device_info = {
                                'serial': serial,
                                'status': status,
                                'details': ' '.join(parts[2:]) if len(parts) > 2 else ''
                            }

                            if status == 'device':
                                devices.append(device_info)

                if devices:
                    for idx, device in enumerate(devices):
                        display_text = f"{device['serial']}"
                        if device['details']:
                            model_info = ''
                            for detail in device['details'].split():
                                if detail.startswith('model:'):
                                    model_info = detail.split(':', 1)[1]
                                    break

                            if model_info:
                                display_text = f"{model_info} ({device['serial']})"

                        self.after(0, lambda t=display_text: self.device_listbox.insert(tk.END, t))

                    self.log_message(f"Found {len(devices)} connected device(s)")
                    self.update_status(f"{len(devices)} device(s) found")
                else:
                    self.log_message("No connected devices found")
                    self.update_status("No devices found")
            else:
                self.log_message("No connected devices found")
                self.update_status("No devices found")

        except Exception as e:
            self.log_message(f"Error refreshing device list: {str(e)}")
            self.update_status("Failed to refresh device list")
