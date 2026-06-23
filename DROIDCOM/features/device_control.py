"""
DROIDCOM - Device Control Feature Module
Device control dialogs and actions implemented with PySide6.
"""

import subprocess

from PySide6 import QtCore, QtWidgets

from ..app.config import IS_WINDOWS


class DeviceControlMixin:
    """Mixin class providing device control functionality."""

    def _reboot_device_normal(self):
        """Reboot device normally"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Rebooting device...")
            self.log_message("Rebooting device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Reboot failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "reboot"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot initiated.")
                self.update_status("Device rebooting")

                self.device_connected = False
                self.disable_device_actions()

                QtWidgets.QMessageBox.information(
                    self,
                    "Reboot Initiated",
                    "The device has been instructed to reboot. "
                    "Please wait for it to complete and reconnect.",
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot failed: {error_msg}")
                self.update_status("Reboot failed")
                QtWidgets.QMessageBox.critical(
                    self, "Reboot Failed", f"Failed to reboot the device: {error_msg}"
                )

        except Exception as e:
            self.log_message(f"Error during reboot: {str(e)}")
            self.update_status("Reboot error")
            QtWidgets.QMessageBox.critical(
                self,
                "Reboot Error",
                f"An error occurred while trying to reboot the device: {str(e)}",
            )

    def _reboot_device_recovery(self):
        """Reboot device to recovery mode"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            confirm = (
                QtWidgets.QMessageBox.question(
                    self,
                    "Confirm Reboot to Recovery",
                    "Are you sure you want to reboot the device to recovery mode?\n\n"
                    "This is typically used for advanced operations like flashing ROMs "
                    "or performing system updates.",
                )
                == QtWidgets.QMessageBox.Yes
            )

            if not confirm:
                return

            self.update_status("Rebooting to recovery...")
            self.log_message("Rebooting device to recovery mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Reboot failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "reboot", "recovery"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot to recovery initiated.")
                self.update_status("Device rebooting to recovery")

                self.device_connected = False
                self.disable_device_actions()

                QtWidgets.QMessageBox.information(
                    self,
                    "Reboot Initiated",
                    "The device has been instructed to reboot into recovery mode. "
                    "Please wait for it to complete and reconnect.",
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to recovery failed: {error_msg}")
                self.update_status("Reboot failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Reboot Failed",
                    f"Failed to reboot the device to recovery: {error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error during reboot to recovery: {str(e)}")
            self.update_status("Reboot error")
            QtWidgets.QMessageBox.critical(
                self,
                "Reboot Error",
                "An error occurred while trying to reboot the device to recovery: "
                f"{str(e)}",
            )

    def _reboot_device_bootloader(self):
        """Reboot device to bootloader/fastboot mode"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            confirm = (
                QtWidgets.QMessageBox.question(
                    self,
                    "Confirm Reboot to Bootloader",
                    "Are you sure you want to reboot the device to bootloader mode?\n\n"
                    "This is used for advanced operations like unlocking the bootloader "
                    "or flashing system images.",
                )
                == QtWidgets.QMessageBox.Yes
            )

            if not confirm:
                return

            self.update_status("Rebooting to bootloader...")
            self.log_message("Rebooting device to bootloader mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Reboot failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "reboot", "bootloader"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot to bootloader initiated.")
                self.update_status("Device rebooting to bootloader")

                self.device_connected = False
                self.disable_device_actions()

                QtWidgets.QMessageBox.information(
                    self,
                    "Reboot Initiated",
                    "The device has been instructed to reboot into bootloader mode. "
                    "Please wait for it to complete and reconnect.",
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to bootloader failed: {error_msg}")
                self.update_status("Reboot failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Reboot Failed",
                    f"Failed to reboot the device to bootloader: {error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error during reboot to bootloader: {str(e)}")
            self.update_status("Reboot error")
            QtWidgets.QMessageBox.critical(
                self,
                "Reboot Error",
                "An error occurred while trying to reboot the device to bootloader: "
                f"{str(e)}",
            )

    def _reboot_device_edl(self):
        """Reboot device to EDL (Emergency Download) mode"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            confirm = (
                QtWidgets.QMessageBox.question(
                    self,
                    "Confirm Reboot to EDL",
                    "WARNING: Rebooting to EDL mode is an advanced operation.\n\n"
                    "This mode is typically used for low-level operations like firmware "
                    "flashing. The device will appear as a Qualcomm HS-USB device and "
                    "will not boot normally until restarted.\n\n"
                    "Are you sure you want to continue?",
                )
                == QtWidgets.QMessageBox.Yes
            )

            if not confirm:
                return

            self.update_status("Rebooting to EDL mode...")
            self.log_message("Rebooting device to EDL mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Reboot failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "reboot", "edl"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode != 0:
                # Samsung devices use "download" mode instead of "edl"
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "reboot", "download"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

            if cmd.returncode == 0:
                self.log_message("Device reboot to EDL mode initiated.")
                self.update_status("Device rebooting to EDL mode")

                self.device_connected = False
                self.disable_device_actions()

                QtWidgets.QMessageBox.information(
                    self,
                    "EDL Mode Initiated",
                    "The device has been instructed to reboot into EDL mode.\n\n"
                    "The device will now appear as a Qualcomm HS-USB device in Device "
                    "Manager.\nYou will need to manually restart the device to boot "
                    "back to Android.",
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to EDL failed: {error_msg}")
                self.update_status("EDL reboot failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "EDL Reboot Failed",
                    "Failed to reboot the device to EDL mode: "
                    f"{error_msg}\n\n"
                    "Your device may not support standard EDL mode entry.\n"
                    "Some devices require specific button combinations or hardware "
                    "tools to enter EDL mode.",
                )

        except Exception as e:
            self.log_message(f"Error during EDL reboot: {str(e)}")
            self.update_status("EDL reboot error")
            QtWidgets.QMessageBox.critical(
                self,
                "EDL Reboot Error",
                f"An error occurred while trying to reboot to EDL mode: {str(e)}",
            )

    def _toggle_mobile_data(self):
        """Toggle mobile data on/off on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling mobile data...")
            self.log_message("Toggling mobile data state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Mobile data toggle failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            # Read current state from settings DB
            get_state_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings", "get", "global", "mobile_data"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
            )
            current_state = get_state_cmd.stdout.strip()
            enable = current_state != "1"
            svc_arg = "enable" if enable else "disable"
            state_text = "enabled" if enable else "disabled"

            # svc data actually toggles the radio (settings put only writes the DB)
            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "svc", "data", svc_arg],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message(f"Mobile data {state_text}")
                self.update_status(f"Mobile data {state_text}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Mobile data has been {state_text}."
                )
            else:
                error_msg = cmd.stderr.strip() or cmd.stdout.strip() or "Unknown error"
                self.log_message(f"Failed to toggle mobile data: {error_msg}")
                self.update_status("Mobile data toggle failed")
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to toggle mobile data: {error_msg}"
                )

        except Exception as e:
            self.log_message(f"Error toggling mobile data: {str(e)}")
            self.update_status("Mobile data toggle error")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"An error occurred while toggling mobile data: {str(e)}"
            )

    def _toggle_wifi(self):
        """Toggle WiFi on/off on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling WiFi...")
            self.log_message("Toggling WiFi state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("WiFi toggle failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            get_state_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings", "get", "global", "wifi_on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if get_state_cmd.returncode == 0:
                current_state = get_state_cmd.stdout.strip()
                new_state = "0" if current_state == "1" else "1"
                state_desc = "OFF" if new_state == "0" else "ON"

                toggle_cmd = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "svc",
                        "wifi",
                        "disable" if new_state == "0" else "enable",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if toggle_cmd.returncode == 0:
                    self.log_message(f"WiFi has been toggled {state_desc}.")
                    self.update_status(f"WiFi toggled {state_desc}")
                    QtWidgets.QMessageBox.information(
                        self,
                        "WiFi Toggled",
                        f"WiFi has been turned {state_desc} on the device.",
                    )
                else:
                    error_msg = toggle_cmd.stderr.strip() or "Unknown error"
                    self.log_message(f"WiFi toggle failed: {error_msg}")
                    self.update_status("WiFi toggle failed")
                    QtWidgets.QMessageBox.critical(
                        self, "WiFi Toggle Failed", f"Failed to toggle WiFi: {error_msg}"
                    )
            else:
                error_msg = get_state_cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Getting WiFi state failed: {error_msg}")
                self.update_status("WiFi toggle failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "WiFi Toggle Failed",
                    f"Failed to get current WiFi state: {error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error toggling WiFi: {str(e)}")
            self.update_status("WiFi toggle error")
            QtWidgets.QMessageBox.critical(
                self, "WiFi Toggle Error", f"An error occurred while trying to toggle WiFi: {str(e)}"
            )

    def _toggle_bluetooth(self):
        """Toggle Bluetooth on/off on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling Bluetooth...")
            self.log_message("Toggling Bluetooth state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Bluetooth toggle failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            get_state_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings", "get", "global", "bluetooth_on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            current_state = get_state_cmd.stdout.strip()
            enable = current_state != "1"
            svc_arg = "enable" if enable else "disable"
            state_text = "enabled" if enable else "disabled"

            # cmd bluetooth_manager is the reliable path on Android 8+
            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cmd", "bluetooth_manager", svc_arg],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
            )

            # Fallback: svc bluetooth (Android 13+ only, but harmless to try)
            if cmd.returncode != 0 or "Error" in cmd.stdout:
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "svc", "bluetooth", svc_arg],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )

            if cmd.returncode == 0:
                self.log_message(f"Bluetooth {state_text}")
                self.update_status(f"Bluetooth {state_text}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Bluetooth has been {state_text}."
                )
            else:
                error_msg = cmd.stderr.strip() or cmd.stdout.strip() or "Unknown error"
                self.log_message(f"Failed to toggle Bluetooth: {error_msg}")
                self.update_status("Bluetooth toggle failed")
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to toggle Bluetooth: {error_msg}"
                )

        except Exception as e:
            self.log_message(f"Error toggling Bluetooth: {str(e)}")
            self.update_status("Bluetooth toggle error")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while toggling Bluetooth: {str(e)}",
            )

    def _toggle_airplane_mode(self):
        """Toggle airplane mode on/off on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling airplane mode...")
            self.log_message("Toggling airplane mode on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Airplane mode toggle failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            get_state_cmd = subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "settings",
                    "get",
                    "global",
                    "airplane_mode_on",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if get_state_cmd.returncode == 0:
                current_state = get_state_cmd.stdout.strip()
                enable = current_state != "1"
                state_desc = "ON" if enable else "OFF"

                # Android 10+: cmd connectivity airplane-mode is the only reliable path
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "cmd", "connectivity",
                     "airplane-mode", "enable" if enable else "disable"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )

                # Fallback for older Android: settings put + broadcast
                if cmd.returncode != 0:
                    new_val = "1" if enable else "0"
                    subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "settings", "put",
                         "global", "airplane_mode_on", new_val],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                    )
                    cmd = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "am", "broadcast",
                         "-a", "android.intent.action.AIRPLANE_MODE",
                         "--ez", "state", "true" if enable else "false"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                    )

                if cmd.returncode == 0:
                    self.log_message(f"Airplane mode has been toggled {state_desc}.")
                    self.update_status(f"Airplane mode toggled {state_desc}")
                    QtWidgets.QMessageBox.information(
                        self,
                        "Airplane Mode Toggled",
                        f"Airplane mode has been turned {state_desc} on the device.",
                    )
                else:
                    error_msg = cmd.stderr.strip() or cmd.stdout.strip() or "Unknown error"
                    self.log_message(f"Airplane mode toggle failed: {error_msg}")
                    self.update_status("Airplane mode toggle failed")
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Airplane Mode Toggle Failed",
                        f"Failed to toggle airplane mode: {error_msg}",
                    )
            else:
                error_msg = get_state_cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Getting airplane mode state failed: {error_msg}")
                self.update_status("Airplane mode toggle failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Airplane Mode Toggle Failed",
                    f"Failed to get current airplane mode state: {error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error toggling airplane mode: {str(e)}")
            self.update_status("Airplane mode toggle error")
            QtWidgets.QMessageBox.critical(
                self,
                "Airplane Mode Toggle Error",
                "An error occurred while trying to toggle airplane mode: "
                f"{str(e)}",
            )

    def _simulate_power_button(self):
        """Simulate a power button press on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Simulating power button...")
            self.log_message("Simulating power button press on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Power button simulation failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "input", "keyevent", "26"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message("Power button press simulated")
                self.update_status("Power button pressed")
            else:
                self.log_message("Primary power button method failed, trying alternative...")

                event_cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "getevent", "-p"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if event_cmd.returncode == 0 and "KEY_POWER" in event_cmd.stdout:
                    # Parse the actual event device that has KEY_POWER
                    event_device = None
                    current_device = None
                    for line in event_cmd.stdout.splitlines():
                        if line.startswith("add device"):
                            current_device = line.split(":")[-1].strip()
                        elif "KEY_POWER" in line and current_device:
                            event_device = current_device
                            break

                    if event_device:
                        cmd = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "sendevent",
                             event_device, "1", "116", "1"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=5,
                        )
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "sendevent",
                             event_device, "0", "0", "0"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=5,
                        )
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "sendevent",
                             event_device, "1", "116", "0"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=5,
                        )
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "sendevent",
                             event_device, "0", "0", "0"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=5,
                        )

                        if cmd.returncode == 0:
                            self.log_message("Power button press simulated (sendevent method)")
                            self.update_status("Power button pressed")
                        else:
                            error_msg = cmd.stderr.strip() or "Unknown error"
                            self.log_message(f"Failed to simulate power button: {error_msg}")
                            self.update_status("Power button simulation failed")
                            QtWidgets.QMessageBox.critical(
                                self, "Error", f"Failed to simulate power button: {error_msg}"
                            )
                    else:
                        self.log_message("Could not locate power button event device")
                        self.update_status("Power button simulation failed")
                        QtWidgets.QMessageBox.critical(
                            self, "Error", "Could not locate power button input device."
                        )
                else:
                    self.log_message("Power button event not found on this device")
                    self.update_status("Power button simulation failed")
                    QtWidgets.QMessageBox.critical(
                        self, "Error", "Could not simulate power button press on this device."
                    )

        except Exception as e:
            self.log_message(f"Error simulating power button: {str(e)}")
            self.update_status("Power button error")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while simulating power button: {str(e)}",
            )

    def _toggle_screen(self):
        """Toggle device screen on/off"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling screen...")
            self.log_message("Toggling device screen...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Screen toggle failed")
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "input", "keyevent", "26"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                self.log_message("Screen toggle command sent successfully.")
                self.update_status("Screen toggled")
                QtWidgets.QMessageBox.information(
                    self, "Screen Toggled", "Screen has been toggled (on/off)."
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Screen toggle failed: {error_msg}")
                self.update_status("Screen toggle failed")
                QtWidgets.QMessageBox.critical(
                    self, "Screen Toggle Failed", f"Failed to toggle screen: {error_msg}"
                )

        except Exception as e:
            self.log_message(f"Error toggling screen: {str(e)}")
            self.update_status("Screen toggle error")
            QtWidgets.QMessageBox.critical(
                self,
                "Screen Toggle Error",
                f"An error occurred while trying to toggle the screen: {str(e)}",
            )

    def _set_brightness_dialog(self):
        """Show a dialog to set the screen brightness"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Set Screen Brightness")
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"
            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                QtWidgets.QMessageBox.critical(
                    self, "Error", "Could not get device information."
                )
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            try:
                max_brightness_cmd = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "cat",
                        "/sys/class/backlight/panel0-backlight/max_brightness",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if max_brightness_cmd.returncode != 0:
                    max_brightness_cmd = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "cat",
                            "/sys/class/leds/lcd-backlight/max_brightness",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10,
                    )

                if max_brightness_cmd.returncode != 0:
                    max_brightness = 255
                else:
                    max_brightness = int(max_brightness_cmd.stdout.strip() or "255")

                brightness_cmd = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "get",
                        "system",
                        "screen_brightness",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if brightness_cmd.returncode == 0 and brightness_cmd.stdout.strip().isdigit():
                    current_brightness = int(brightness_cmd.stdout.strip())
                    current_brightness = max(0, min(current_brightness, max_brightness))
                else:
                    current_brightness = max_brightness // 2

            except (ValueError, subprocess.SubprocessError) as e:
                self.log_message(f"Error getting brightness: {str(e)}")
                max_brightness = 255
                current_brightness = 128

            main_layout.addWidget(
                QtWidgets.QLabel(f"Set Brightness (0-{max_brightness}):")
            )

            brightness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, dialog)
            brightness_slider.setRange(0, max_brightness)
            brightness_slider.setValue(current_brightness)
            brightness_slider.setMinimumWidth(300)
            main_layout.addWidget(brightness_slider)

            value_label = QtWidgets.QLabel(str(current_brightness), dialog)
            value_label.setAlignment(QtCore.Qt.AlignCenter)
            main_layout.addWidget(value_label)

            def update_value(value):
                value_label.setText(str(int(value)))

            brightness_slider.valueChanged.connect(update_value)

            button_layout = QtWidgets.QHBoxLayout()

            def apply_brightness():
                try:
                    brightness = brightness_slider.value()
                    cmd = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "settings",
                            "put",
                            "system",
                            "screen_brightness",
                            str(brightness),
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10,
                    )

                    subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "su",
                            "-c",
                            f"echo {brightness} > /sys/class/backlight/panel0-backlight/brightness",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                    )

                    if cmd.returncode == 0:
                        self.log_message(f"Brightness set to {brightness}")
                        self.update_status(f"Brightness set to {brightness}")
                        dialog.accept()
                    else:
                        error_msg = cmd.stderr.strip() or "Unknown error"
                        self.log_message(f"Failed to set brightness: {error_msg}")
                        QtWidgets.QMessageBox.critical(
                            dialog,
                            "Error",
                            f"Failed to set brightness: {error_msg}",
                        )

                except Exception as e:
                    self.log_message(f"Error setting brightness: {str(e)}")
                    QtWidgets.QMessageBox.critical(
                        dialog,
                        "Error",
                        f"An error occurred while setting brightness: {str(e)}",
                    )

            apply_button = QtWidgets.QPushButton("Apply", dialog)
            apply_button.clicked.connect(apply_brightness)
            cancel_button = QtWidgets.QPushButton("Cancel", dialog)
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(apply_button)
            button_layout.addWidget(cancel_button)
            main_layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            self.log_message(f"Error in brightness dialog: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open brightness dialog: {str(e)}"
            )

    def _set_screen_timeout_dialog(self):
        """Show a dialog to set the screen timeout duration"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Set Screen Timeout")
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            main_layout.addWidget(
                QtWidgets.QLabel("Set Screen Timeout", dialog)
            )

            timeout_options = [
                ("15 seconds", 15000),
                ("30 seconds", 30000),
                ("1 minute", 60000),
                ("2 minutes", 120000),
                ("5 minutes", 300000),
                ("10 minutes", 600000),
                ("30 minutes", 1800000),
                ("Never (keep on)", 2147483647),
            ]

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"
            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                QtWidgets.QMessageBox.critical(
                    self, "Error", "Could not get device information."
                )
                return

            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            try:
                timeout_cmd = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "get",
                        "system",
                        "screen_off_timeout",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if timeout_cmd.returncode == 0 and timeout_cmd.stdout.strip().isdigit():
                    current_timeout = int(timeout_cmd.stdout.strip())
                else:
                    current_timeout = 30000

            except (ValueError, subprocess.SubprocessError) as e:
                self.log_message(f"Error getting screen timeout: {str(e)}")
                current_timeout = 30000

            options_group = QtWidgets.QButtonGroup(dialog)
            for label_text, value in timeout_options:
                radio = QtWidgets.QRadioButton(label_text, dialog)
                radio.setProperty("timeout_value", value)
                options_group.addButton(radio)
                main_layout.addWidget(radio)
                if value == current_timeout:
                    radio.setChecked(True)

            custom_layout = QtWidgets.QHBoxLayout()
            custom_radio = QtWidgets.QRadioButton("Custom:", dialog)
            custom_layout.addWidget(custom_radio)
            custom_input = QtWidgets.QLineEdit(dialog)
            custom_input.setPlaceholderText("Seconds")
            custom_input.setFixedWidth(80)
            custom_layout.addWidget(custom_input)
            custom_layout.addWidget(QtWidgets.QLabel("seconds", dialog))
            main_layout.addLayout(custom_layout)

            def update_custom_state():
                custom_input.setEnabled(custom_radio.isChecked())
                if custom_radio.isChecked():
                    custom_input.setFocus()

            custom_radio.toggled.connect(update_custom_state)

            if current_timeout not in [value for _, value in timeout_options]:
                custom_radio.setChecked(True)
                custom_input.setText(str(current_timeout // 1000))
            else:
                custom_input.setEnabled(False)

            button_layout = QtWidgets.QHBoxLayout()

            def apply_timeout():
                try:
                    if custom_radio.isChecked():
                        try:
                            seconds = int(custom_input.text())
                            if seconds < 0:
                                raise ValueError("Timeout must be positive")
                            timeout_ms = seconds * 1000
                        except ValueError:
                            QtWidgets.QMessageBox.critical(
                                dialog,
                                "Invalid Input",
                                "Please enter a valid number of seconds.",
                            )
                            return
                    else:
                        checked_button = options_group.checkedButton()
                        timeout_ms = checked_button.property("timeout_value")

                    cmd = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "settings",
                            "put",
                            "system",
                            "screen_off_timeout",
                            str(timeout_ms),
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10,
                    )

                    if cmd.returncode == 0:
                        self.log_message(f"Screen timeout set to {timeout_ms}ms")
                        self.update_status(
                            f"Screen timeout set to {timeout_ms // 1000} seconds"
                        )
                        dialog.accept()
                    else:
                        error_msg = cmd.stderr.strip() or "Unknown error"
                        self.log_message(f"Failed to set screen timeout: {error_msg}")
                        QtWidgets.QMessageBox.critical(
                            dialog,
                            "Error",
                            f"Failed to set screen timeout: {error_msg}",
                        )

                except Exception as e:
                    self.log_message(f"Error setting screen timeout: {str(e)}")
                    QtWidgets.QMessageBox.critical(
                        dialog,
                        "Error",
                        "An error occurred while setting screen timeout: "
                        f"{str(e)}",
                    )

            apply_button = QtWidgets.QPushButton("Apply", dialog)
            apply_button.clicked.connect(apply_timeout)
            cancel_button = QtWidgets.QPushButton("Cancel", dialog)
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(apply_button)
            button_layout.addWidget(cancel_button)
            main_layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            self.log_message(f"Error in screen timeout dialog: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open screen timeout dialog: {str(e)}"
            )

    def _toggle_do_not_disturb(self):
        """Toggle Do Not Disturb mode on/off"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling Do Not Disturb...")
            self.log_message("Toggling Do Not Disturb mode on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"
            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                return
            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            dnd_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings", "get", "global", "zen_mode"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
            )
            current = dnd_cmd.stdout.strip()
            dnd_enabled = current in ("1", "2", "3")
            state_text = "disabled" if dnd_enabled else "enabled"

            # cmd notification set_dnd is the real DND toggle (Android 8+)
            # 0 = off, 1 = priority, 2 = total silence, 3 = alarms only
            cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cmd", "notification",
                 "set_dnd", "off" if dnd_enabled else "priority"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
            )

            # Fallback: settings put for older Android
            if cmd.returncode != 0:
                new_val = "0" if dnd_enabled else "1"
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "settings", "put", "global",
                     "zen_mode", new_val],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )

            if cmd.returncode == 0:
                self.log_message(f"Do Not Disturb {state_text}")
                self.update_status(f"Do Not Disturb {state_text}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Do Not Disturb has been {state_text}."
                )
            else:
                error_msg = cmd.stderr.strip() or cmd.stdout.strip() or "Unknown error"
                self.log_message(f"Failed to toggle DND: {error_msg}")
                self.update_status("DND toggle failed")
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to toggle DND: {error_msg}")

        except Exception as e:
            self.log_message(f"Error toggling DND: {str(e)}")
            self.update_status("DND toggle error")
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _toggle_flashlight(self):
        """Toggle the device flashlight on/off"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            self.update_status("Toggling flashlight...")
            self.log_message("Toggling flashlight on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"
            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                return
            if isinstance(serial, str) and "\n" in serial:
                serial = serial.split("\n")[0].strip()

            # Check current torch state via camera service
            state_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell",
                 "settings get system screen_brightness"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5,
            )

            current_state = getattr(self, "_flashlight_on", False)
            new_state = not current_state

            # Use cmd.notification set-dnd or camera torch command
            # Android 6+ supports camera2 torch mode via service call
            if new_state:
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell",
                     "cmd camera set-torch-mode 0 1"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )
            else:
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell",
                     "cmd camera set-torch-mode 0 0"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )

            # Fallback: use intent broadcast for older devices
            if cmd.returncode != 0 or "Error" in cmd.stdout:
                action = "enable" if new_state else "disable"
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "am", "broadcast",
                     "-a", "net.cactii.flash2.TOGGLE_FLASHLIGHT"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )

            self._flashlight_on = new_state
            state_text = "on" if new_state else "off"
            self.log_message(f"Flashlight turned {state_text}")
            self.update_status(f"Flashlight {state_text}")
            QtWidgets.QMessageBox.information(
                self, "Flashlight", f"Flashlight turned {state_text}.\n\n"
                "Note: flashlight control via ADB may not work on all devices."
            )

        except Exception as e:
            self.log_message(f"Error toggling flashlight: {str(e)}")
            self.update_status("Flashlight error")
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------------ #
    # Blind Device Setup — no display / no touch input                    #
    # ------------------------------------------------------------------ #

    def _blind_setup_dialog(self):
        """
        Fully-automated ADB setup for a device with no display or touch.
        Auto-Watch mode polls every 2 s and acts the instant any ADB-accessible
        state is detected — no manual button clicks needed once watching starts.
        """
        import os
        import threading
        import time

        adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, "adb_path") else "adb"

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Blind Device Setup — No Display / No Touch")
        dlg.resize(700, 640)
        layout = QtWidgets.QVBoxLayout(dlg)

        # ── status banner ────────────────────────────────────────────────
        state_label = QtWidgets.QLabel("Detecting device…")
        state_label.setStyleSheet(
            "font-weight:bold; font-size:13px; padding:6px; "
            "background:#1e1e2e; border-radius:4px;"
        )
        state_label.setWordWrap(True)
        layout.addWidget(state_label)

        # ── log output ───────────────────────────────────────────────────
        log = QtWidgets.QPlainTextEdit()
        log.setReadOnly(True)
        log.setMinimumHeight(200)
        layout.addWidget(log)

        def say(msg):
            from ..utils.qt_dispatcher import emit_ui
            emit_ui(self, lambda: log.appendPlainText(msg))

        # ── action buttons ───────────────────────────────────────────────
        btn_grid = QtWidgets.QGridLayout()
        layout.addLayout(btn_grid)

        def make_btn(label, row, col, handler, tip=""):
            b = QtWidgets.QPushButton(label)
            b.setMinimumHeight(36)
            b.setToolTip(tip)
            b.clicked.connect(handler)
            btn_grid.addWidget(b, row, col)
            return b

        # ── helpers ───────────────────────────────────────────────────────
        def run(args, timeout=15):
            return subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=timeout
            )

        def detect_state():
            """Return (serial, state) or (None, None). state: authorized/unauthorized/recovery/fastboot/none"""
            try:
                r = run([adb_cmd, "devices"])
                lines = [l.strip() for l in r.stdout.splitlines() if "\t" in l]
                if lines:
                    serial, state = lines[0].split("\t", 1)
                    return serial.strip(), state.strip()
                # check fastboot
                r2 = run(["fastboot", "devices"])
                if r2.stdout.strip():
                    serial = r2.stdout.split()[0]
                    return serial, "fastboot"
            except Exception:
                pass
            return None, None

        def refresh_state():
            serial, state = detect_state()
            colours = {
                "device": "#a6e3a1",       # green = authorized
                "recovery": "#89b4fa",     # blue
                "unauthorized": "#f38ba8", # red
                "fastboot": "#fab387",     # orange
                "none": "#6c7086",         # grey
            }
            labels = {
                "device": f"✓ Connected && authorized  ({serial})",
                "recovery": f"⚙  Recovery mode  ({serial}) — ADB shell available",
                "unauthorized": f"⚠  Unauthorized  ({serial}) — device needs to accept the dialog",
                "fastboot": f"⚡ Fastboot mode  ({serial})",
                "none": "✗  No device detected via ADB or Fastboot",
            }
            key = state if state in colours else "none"
            from ..utils.qt_dispatcher import emit_ui
            emit_ui(self, lambda: (
                state_label.setText(labels.get(key, f"Unknown state: {state}")),
                state_label.setStyleSheet(
                    f"font-weight:bold;font-size:13px;padding:6px;"
                    f"background:#1e1e2e;border-radius:4px;color:{colours[key]};"
                )
            ))
            return serial, state

        # ── Step 1: Detect ───────────────────────────────────────────────
        def do_detect():
            say("─── Detecting device state…")
            serial, state = refresh_state()
            say(f"Result: {state or 'none'}  serial={serial or 'N/A'}")
            if state == "device":
                say("Device is already authorized. Use the main Connect button.")
            elif state == "recovery":
                say("Recovery ADB shell is open — you can inject the host key or enable dev mode directly.")
            elif state == "unauthorized":
                say(
                    "Device is connected but ADB is not yet authorized.\n"
                    "The 'Allow USB debugging?' dialog is probably on screen.\n"
                    "→ Use 'Inject Key via OTG' or the OTG keyboard steps below."
                )
            elif state == "fastboot":
                say("Device is in fastboot. Use 'Reboot → Recovery' to get ADB shell access.")
            else:
                say(
                    "No device found.\n"
                    "• Connect phone via USB\n"
                    "• Ensure USB cable supports data (not charge-only)\n"
                    "• If display is dead, hold Power for 10-15s to force reboot.\n"
                    "  Once the phone vibrates or restarts, release Power — do NOT\n"
                    "  hold Vol-Down during boot (that triggers safe mode).\n"
                    "  Then use the Hardware Guide button to enter recovery."
                )

        # ── Step 2: Enable dev mode + USB debugging (needs shell) ────────
        def do_enable_dev_mode():
            serial, state = detect_state()
            if state not in ("device", "recovery"):
                say("✗ Need authorized or recovery shell. Detect first.")
                return

            def task():
                say("─── Enabling developer options…")
                r1 = run([adb_cmd, "-s", serial, "shell",
                           "settings", "put", "global",
                           "development_settings_enabled", "1"])
                say(f"  development_settings_enabled → {'OK' if r1.returncode==0 else r1.stderr.strip()}")

                say("─── Enabling USB debugging…")
                r2 = run([adb_cmd, "-s", serial, "shell",
                           "settings", "put", "global", "adb_enabled", "1"])
                say(f"  adb_enabled → {'OK' if r2.returncode==0 else r2.stderr.strip()}")

                # restart adbd so it picks up new setting
                run([adb_cmd, "-s", serial, "shell", "stop adbd"])
                run([adb_cmd, "-s", serial, "shell", "start adbd"])
                say("  adbd restarted.")
                say("Done. Developer mode and USB debugging are now enabled.")
                refresh_state()

            threading.Thread(target=task, daemon=True).start()

        # ── Step 3: Inject host ADB key directly (recovery path) ─────────
        def do_inject_key():
            serial, state = detect_state()
            if state not in ("device", "recovery"):
                say("✗ Need authorized or recovery shell to inject key.")
                return

            key_paths = [
                os.path.expanduser("~/.android/adbkey.pub"),
                os.path.join(os.environ.get("USERPROFILE", ""), ".android", "adbkey.pub"),
            ]
            key_path = next((p for p in key_paths if os.path.exists(p)), None)

            if not key_path:
                say(
                    "✗ Host ADB public key not found at ~/.android/adbkey.pub\n"
                    "  Run 'adb keygen ~/.android/adbkey' on your PC first, then retry."
                )
                return

            def task():
                try:
                    pub_key = open(key_path).read().strip()
                    say(f"─── Host key found: {key_path}")
                    say("    Pushing to /data/misc/adb/adb_keys…")

                    # Mount /data in recovery if needed (stock recovery)
                    if state == "recovery":
                        run([adb_cmd, "-s", serial, "shell", "mount /data"])

                    # Write key
                    r = run([adb_cmd, "-s", serial, "shell",
                              f"mkdir -p /data/misc/adb && "
                              f"echo '{pub_key}' >> /data/misc/adb/adb_keys && "
                              f"chmod 640 /data/misc/adb/adb_keys && "
                              f"chown system:shell /data/misc/adb/adb_keys"])
                    if r.returncode == 0:
                        say("✓ Key injected successfully.")
                        say("  Rebooting device to system…")
                        run([adb_cmd, "-s", serial, "reboot"])
                        say("  When device boots, ADB will be auto-authorized.")
                    else:
                        say(f"✗ Key injection failed: {r.stderr.strip() or r.stdout.strip()}")
                        say("  Try enabling root access first or use the OTG keyboard method.")
                except Exception as e:
                    say(f"✗ Error: {e}")

            threading.Thread(target=task, daemon=True).start()

        # ── Step 4: Reboot fastboot → recovery ───────────────────────────
        def do_fastboot_to_recovery():
            serial, state = detect_state()
            if state != "fastboot":
                say("✗ Device is not in fastboot mode.")
                return

            def task():
                say("─── Rebooting fastboot → recovery…")
                r = run(["fastboot", "-s", serial, "reboot", "recovery"], timeout=20)
                say(f"  {'OK — wait for recovery to boot (~30s)' if r.returncode==0 else r.stderr.strip()}")
                import time; time.sleep(30)
                refresh_state()

            threading.Thread(target=task, daemon=True).start()

        # ── Step 5: Force recovery via hardware buttons (guide) ──────────
        def do_hardware_guide():
            say(
                "─── Hardware button guide for common manufacturers ───\n"
                "\n"
                "PIXEL / NEXUS\n"
                "  Power off → hold [Vol Down] + [Power] → Fastboot screen\n"
                "  Press Vol Down to highlight 'Recovery' → press Power\n"
                "\n"
                "SAMSUNG\n"
                "  Power off → hold [Vol Up] + [Bixby/Home] + [Power]\n"
                "  Release when Samsung logo appears → Recovery menu\n"
                "  (Use Vol Up/Down to navigate, Power to select)\n"
                "\n"
                "XIAOMI / POCO\n"
                "  Power off → hold [Vol Up] + [Power] → Recovery\n"
                "\n"
                "ONEPLUS\n"
                "  Power off → hold [Vol Down] + [Power] → Fastboot\n"
                "  Or: hold [Vol Up] + [Power] → Recovery\n"
                "\n"
                "MOTOROLA\n"
                "  Power off → hold [Vol Down] + [Power] → Fastboot\n"
                "  Use Vol Down to scroll to 'Recovery' → Power to select\n"
                "\n"
                "LG\n"
                "  Power off → hold [Vol Down] + [Power] → Recovery\n"
                "\n"
                "SONY XPERIA\n"
                "  Power off → hold [Vol Up] + plug USB cable → Fastboot LED\n"
                "  Then: fastboot reboot recovery\n"
                "\n"
                "Once in recovery, hit 'Detect' then 'Inject Key + Reboot'."
            )

        # ── Step 6: OTG keyboard guide ───────────────────────────────────
        def do_otg_guide():
            say(
                "─── OTG Keyboard method for accepting ADB dialog ───\n"
                "\n"
                "1. Get a USB OTG adapter (USB-C or Micro-USB to USB-A)\n"
                "2. Connect a USB keyboard to the OTG adapter, plug into phone\n"
                "3. Wake the phone: press keyboard Power/any key or phone power button\n"
                "4. The 'Allow USB debugging?' dialog should be on screen\n"
                "5. Press [Tab] once to move focus to the checkbox 'Always allow'\n"
                "   (optional), then press [Enter] to accept\n"
                "   — OR just press [Enter] directly if 'Allow' is default-focused\n"
                "6. Disconnect OTG, reconnect direct USB → hit 'Detect' above\n"
                "\n"
                "If you also have a USB-C to HDMI/DisplayPort adapter:\n"
                "  Connect phone → HDMI adapter → TV/monitor to see the screen\n"
                "  (Only works if phone supports DisplayPort Alt Mode over USB-C)\n"
                "\n"
                "Tip: if phone shows charging icon but no dialog, ADB may not be\n"
                "     enabled yet. Use recovery injection path first."
            )

        # ── Step 7: Enable ADB over TCP so future connections need no dialog
        def do_enable_tcpip():
            serial, state = detect_state()
            if state != "device":
                say("✗ Need an authorized connection first.")
                return

            def task():
                say("─── Enabling ADB over TCP/IP (port 5555)…")
                r = run([adb_cmd, "-s", serial, "tcpip", "5555"])
                say(f"  {'OK — connect via: adb connect <device-ip>:5555' if r.returncode==0 else r.stderr.strip()}")
                # get IP
                r2 = run([adb_cmd, "-s", serial, "shell",
                           "ip route | grep wlan | awk '{print $9}'"])
                ip = r2.stdout.strip()
                if ip:
                    say(f"  Device WiFi IP: {ip}")
                    say(f"  → adb connect {ip}:5555")
                    say("  Once connected over WiFi, USB authorization won't be needed again.")

            threading.Thread(target=task, daemon=True).start()

        # ── Auto-Watch state ──────────────────────────────────────────────
        _watching = threading.Event()
        _done = threading.Event()   # set when dialog closes

        # Known Android vendor IDs (covers most manufacturers)
        ANDROID_VIDS = [
            "18d1",  # Google / Nexus / AOSP
            "04e8",  # Samsung
            "2717",  # Xiaomi / POCO
            "12d1",  # Huawei / Honor
            "0bb4",  # HTC
            "19d2",  # ZTE / nubia
            "22b8",  # Motorola
            "0fce",  # Sony / Xperia
            "2a96",  # Oppo / Realme
            "1004",  # LG
            "0421",  # Nokia
            "413c",  # Dell Streak
            "2d95",  # Vivo
            "17ef",  # Lenovo
            "0e8d",  # MediaTek (MTK)
            "05c6",  # Qualcomm EDL / 9008 mode
            "04dd",  # Sharp
            "0b05",  # ASUS / ROG Phone
            "2c7c",  # Quectel
            "1bbb",  # T-Mobile / Alcatel
            "03f0",  # HP
            "0409",  # NEC
            "1d4d",  # Pegatron
        ]

        def _get_usb_devices():
            """Return list of (vid, pid, description) for all USB devices."""
            devices = []
            try:
                if IS_WINDOWS:
                    r = run(["powershell", "-Command",
                             "Get-PnpDevice | Select-Object FriendlyName,Status | ConvertTo-Json"])
                    import json
                    try:
                        items = json.loads(r.stdout)
                        if isinstance(items, dict):
                            items = [items]
                        for item in items:
                            name = item.get("FriendlyName", "")
                            status = item.get("Status", "")
                            devices.append(("????", "????", f"{name} [{status}]"))
                    except Exception:
                        pass
                else:
                    r = run(["lsusb"])
                    for line in r.stdout.splitlines():
                        # Format: Bus 001 Device 002: ID 18d1:4ee7 Google Inc. Nexus/Pixel Device
                        parts = line.strip().split()
                        if len(parts) >= 6 and parts[4].startswith("ID"):
                            vid_pid = parts[5].split(":")
                            vid = vid_pid[0] if vid_pid else "????"
                            pid = vid_pid[1] if len(vid_pid) > 1 else "????"
                            desc = " ".join(parts[6:]) if len(parts) > 6 else ""
                            devices.append((vid, pid, desc))
            except Exception:
                pass
            return devices

        def _usb_connected():
            """Return (found, is_android, description) for connected USB devices."""
            devs = _get_usb_devices()
            android_devs = [(v, p, d) for v, p, d in devs if v.lower() in ANDROID_VIDS]
            if android_devs:
                v, p, d = android_devs[0]
                return True, True, f"VID:{v} PID:{p} {d}".strip()
            # Check for any phone-like device even if VID unknown
            phone_keywords = ["android","samsung","google","xiaomi","huawei","oneplus",
                               "motorola","sony","oppo","realme","vivo","nokia","asus",
                               "poco","redmi","pixel","qualcomm","mediatek","mtk","phone",
                               "mobile","composite","adb","fastboot"]
            for v, p, d in devs:
                if any(k in d.lower() for k in phone_keywords):
                    return True, True, f"VID:{v} PID:{p} {d}".strip()
            if devs:
                return True, False, f"Non-Android USB: {devs[0][2]}"
            return False, False, ""

        def _try_usb_rebind(vid, pid):
            """Linux only: unbind/bind the USB device to force re-enumeration."""
            try:
                import glob as _glob
                pattern = f"/sys/bus/usb/devices/*/idVendor"
                for vf in _glob.glob(pattern):
                    v = open(vf).read().strip()
                    if v.lower() == vid.lower():
                        dev_path = vf.replace("/idVendor", "")
                        dev_id = open(f"{dev_path}/dev").read().strip().replace(":", "/")
                        say(f"  USB rebind: {dev_path}")
                        subprocess.run(f"echo '{dev_path.split('/')[-1]}' | tee /sys/bus/usb/drivers/usb/unbind",
                                       shell=True, capture_output=True)
                        time.sleep(1)
                        subprocess.run(f"echo '{dev_path.split('/')[-1]}' | tee /sys/bus/usb/drivers/usb/bind",
                                       shell=True, capture_output=True)
                        time.sleep(2)
                        return True
            except Exception:
                pass
            return False

        def _scan_network_adb():
            """Scan LAN for open ADB TCP port 5555. Returns list of IPs."""
            import socket
            found = []
            try:
                # Get local subnet
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                prefix = ".".join(local_ip.split(".")[:3])
                say(f"  Scanning {prefix}.1-254 for ADB TCP port 5555…")
                def check(ip):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.3)
                        if s.connect_ex((ip, 5555)) == 0:
                            found.append(ip)
                        s.close()
                    except Exception:
                        pass
                threads = [threading.Thread(target=check, args=(f"{prefix}.{i}",), daemon=True)
                           for i in range(1, 255)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join(timeout=2)
            except Exception as e:
                say(f"  Network scan error: {e}")
            return found

        def _full_auto_setup(serial, state):
            """Called by the watcher when it finds an actionable state."""
            say(f"\n★ Auto-acting on state: {state}  serial={serial}")

            if state == "device":
                # Already authorized — enable TCP so we never need USB auth again
                say("Device is already authorized. Enabling wireless ADB…")
                do_enable_tcpip()
                return

            if state == "fastboot":
                say("Fastboot detected — rebooting to recovery…")
                r = run(["fastboot", "-s", serial, "reboot", "recovery"], timeout=20)
                say(f"  fastboot reboot recovery → rc={r.returncode}")
                say("  Waiting 35 s for recovery to boot…")
                time.sleep(35)
                return   # watcher will pick up next state

            if state in ("recovery", "sideload"):
                say("Recovery ADB shell available — running full setup…")
                # 1. Enable dev mode + USB debug
                for key in ("development_settings_enabled", "adb_enabled"):
                    r = run([adb_cmd, "-s", serial, "shell",
                              "settings", "put", "global", key, "1"])
                    say(f"  {key} → {'OK' if r.returncode==0 else r.stderr.strip()}")
                # 2. Inject host key
                key_path = os.path.expanduser("~/.android/adbkey.pub")
                if not os.path.exists(key_path):
                    say("  ✗ ~/.android/adbkey.pub not found — skipping key injection")
                else:
                    pub_key = open(key_path).read().strip()
                    r = run([adb_cmd, "-s", serial, "shell",
                              f"mkdir -p /data/misc/adb && "
                              f"echo '{pub_key}' >> /data/misc/adb/adb_keys && "
                              f"chmod 640 /data/misc/adb/adb_keys && "
                              f"chown system:shell /data/misc/adb/adb_keys"])
                    say(f"  Key injection → {'OK' if r.returncode==0 else r.stderr.strip()}")
                # 3. Restart adbd to pick up new settings
                run([adb_cmd, "-s", serial, "shell", "stop adbd"])
                run([adb_cmd, "-s", serial, "shell", "start adbd"])
                say("  adbd restarted.")
                say("  Rebooting to system…")
                run([adb_cmd, "-s", serial, "reboot"])
                say("✓ Done. Device will boot and auto-authorize ADB.\n"
                    "  Watch will continue — connect will complete automatically.")

            if state == "unauthorized":
                # Can't run shell on unauthorized device.
                # Kill+restart ADB server to re-trigger the dialog on device,
                # then try mDNS pairing if Android 11+.
                say("Device is unauthorized — attempting to re-trigger auth dialog…")
                run([adb_cmd, "kill-server"])
                time.sleep(1)
                run([adb_cmd, "start-server"])
                time.sleep(2)
                # Try to auto-accept via mDNS pair (Android 11+, needs pairing code)
                r = run([adb_cmd, "mdns", "services"])
                if "adbexperimental" in r.stdout or "_adb-tls-pairing" in r.stdout:
                    say("  Android 11+ mDNS pairing service found.")
                    say("  Cannot auto-accept without the on-screen pairing code.")
                say("  ⚠ USB debugging authorization requires physical acceptance.\n"
                    "    Options:\n"
                    "    • OTG keyboard: plug keyboard → press Enter (accepts dialog)\n"
                    "    • Boot to recovery: power off, then power on holding Vol-Down\n"
                    "      (exact combo shown in 'Hardware Guide' button below)")

        def watch_loop():
            last_state = None
            last_usb_desc = None
            network_scanned = False
            say("◉ Auto-Watch started — polling every 2 s…")
            while not _done.is_set():
                try:
                    serial, state = detect_state()
                    usb_found, is_android, usb_desc = _usb_connected()

                    # Update banner
                    refresh_state()

                    if state != last_state:
                        last_state = state
                        if state and state != "none":
                            _full_auto_setup(serial, state)
                        elif usb_found and is_android and usb_desc != last_usb_desc:
                            last_usb_desc = usb_desc
                            say(f"\n⚡ Android phone detected on USB: {usb_desc}")
                            say("  ADB is not responding — USB debugging is likely OFF.")
                            say("  Attempting ADB server restart…")
                            run([adb_cmd, "kill-server"])
                            time.sleep(1)
                            run([adb_cmd, "start-server"])
                            time.sleep(2)
                            # Re-detect after restart
                            s2, st2 = detect_state()
                            if st2 and st2 != "none":
                                say(f"  ADB responded after restart: {st2}")
                                _full_auto_setup(s2, st2)
                            else:
                                # Try USB rebind to force re-enumeration
                                vid = usb_desc.split("VID:")[-1].split()[0] if "VID:" in usb_desc else ""
                                if vid and not IS_WINDOWS:
                                    say("  Attempting USB rebind to force re-enumeration…")
                                    _try_usb_rebind(vid, "")
                                    time.sleep(3)
                                    run([adb_cmd, "kill-server"])
                                    time.sleep(1)
                                    run([adb_cmd, "start-server"])
                                    time.sleep(2)
                                say("\n─── What the tool can do automatically ───")
                                say("  ✓ If phone boots into FASTBOOT: auto-reboots to recovery")
                                say("  ✓ If phone boots into RECOVERY: auto-enables USB debug + injects key")
                                say("  ✓ If phone reaches AUTHORIZED state: auto-enables wireless ADB")
                                say("")
                                say("─── What you need to do (ONE of these) ───")
                                say("  Option A — Force into Recovery:")
                                say("    Hold Power button for 10-15 s until phone powers off.")
                                say("    Then hold [Vol Down]+[Power] (most phones) until this")
                                say("    display shows FASTBOOT or RECOVERY detected above.")
                                say("")
                                say("  Option B — Network ADB scan:")
                                say("    If phone has wireless ADB enabled (Android 11+),")
                                say("    scanning LAN now…")
                                if not network_scanned:
                                    network_scanned = True
                                    def do_net_scan():
                                        ips = _scan_network_adb()
                                        if ips:
                                            for ip in ips:
                                                say(f"  Found ADB at {ip}:5555 — connecting…")
                                                r = run([adb_cmd, "connect", f"{ip}:5555"])
                                                say(f"  {r.stdout.strip() or r.stderr.strip()}")
                                        else:
                                            say("  No wireless ADB found on LAN.")
                                    threading.Thread(target=do_net_scan, daemon=True).start()
                        elif usb_found and not is_android and usb_desc != last_usb_desc:
                            last_usb_desc = usb_desc
                            say(f"\n⚠ USB device detected but not recognized as Android: {usb_desc}")
                            say("  If this is your phone, its vendor ID may be unknown.")
                            say("  Try: unplug → change USB mode to 'File Transfer' on phone → replug.")
                        elif not usb_found and last_usb_desc is not None:
                            last_usb_desc = None
                            say("⚡ USB device disconnected.")
                        elif not usb_found and last_usb_desc is None and last_state is None:
                            say("No USB device detected. Connect phone via USB data cable.")
                            last_state = "REPORTED"
                except Exception as e:
                    say(f"Watch error: {e}")
                time.sleep(2)

        # ── wire buttons ─────────────────────────────────────────────────
        watch_btn = QtWidgets.QPushButton("▶  Start Auto-Watch  (recommended)")
        watch_btn.setMinimumHeight(44)
        watch_btn.setStyleSheet("font-weight:bold; font-size:13px;")
        layout.addWidget(watch_btn)

        def toggle_watch():
            if _watching.is_set():
                _watching.clear()
                watch_btn.setText("▶  Start Auto-Watch  (recommended)")
                say("◉ Auto-Watch stopped.")
            else:
                _watching.set()
                watch_btn.setText("■  Stop Auto-Watch")
                threading.Thread(target=watch_loop, daemon=True).start()

        watch_btn.clicked.connect(toggle_watch)

        make_btn("Detect Once", 0, 0, do_detect,
                 "One-shot scan of ADB and Fastboot")
        make_btn("Enable Dev Mode + USB Debug", 0, 1, do_enable_dev_mode,
                 "Run via shell (recovery or authorized only)")
        make_btn("Inject Host Key → Reboot", 1, 0, do_inject_key,
                 "Write ~/.android/adbkey.pub to /data/misc/adb/adb_keys")
        make_btn("Fastboot → Recovery", 1, 1, do_fastboot_to_recovery,
                 "Reboot from fastboot into recovery")
        make_btn("Hardware Button Guide", 2, 0, do_hardware_guide,
                 "Per-manufacturer recovery key combos")
        make_btn("OTG Keyboard Guide", 2, 1, do_otg_guide,
                 "Accept ADB dialog using USB keyboard + OTG adapter")
        make_btn("Enable ADB over TCP/IP", 3, 0, do_enable_tcpip,
                 "Switch to wireless ADB once authorized")

        def do_scan_usb():
            say("─── USB Device Scan ───")
            devs = _get_usb_devices()
            if not devs:
                say("  No USB devices detected by lsusb.")
            else:
                for vid, pid, desc in devs:
                    android_flag = " ← Android" if vid.lower() in ANDROID_VIDS else ""
                    say(f"  VID:{vid} PID:{pid}  {desc}{android_flag}")

        def do_scan_network():
            def task():
                say("─── Scanning LAN for wireless ADB (port 5555)…")
                ips = _scan_network_adb()
                if ips:
                    for ip in ips:
                        say(f"  Found: {ip}:5555 — connecting…")
                        r = run([adb_cmd, "connect", f"{ip}:5555"])
                        say(f"  {r.stdout.strip() or r.stderr.strip()}")
                    refresh_state()
                else:
                    say("  No wireless ADB found on this network.")
            threading.Thread(target=task, daemon=True).start()

        def do_force_restart_adb():
            def task():
                say("─── Force-restarting ADB server…")
                run([adb_cmd, "kill-server"])
                time.sleep(1)
                r = run([adb_cmd, "start-server"])
                say(f"  {r.stdout.strip() or r.stderr.strip() or 'ADB server restarted.'}")
                time.sleep(2)
                refresh_state()
            threading.Thread(target=task, daemon=True).start()

        make_btn("Scan All USB Devices", 3, 1, do_scan_usb,
                 "List all USB devices including non-ADB phones")
        make_btn("Scan LAN for Wireless ADB", 4, 0, do_scan_network,
                 "Find phone on WiFi via ADB TCP port 5555")
        make_btn("Force Restart ADB Server", 4, 1, do_force_restart_adb,
                 "Kill and restart ADB server to force re-enumeration")

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setMinimumHeight(36)

        def on_close():
            _done.set()
            _watching.clear()
            dlg.close()

        close_btn.clicked.connect(on_close)
        layout.addWidget(close_btn)

        # Start watching immediately on open
        _watching.set()
        threading.Thread(target=watch_loop, daemon=True).start()
        watch_btn.setText("■  Stop Auto-Watch")
        dlg.exec()
        _done.set()
