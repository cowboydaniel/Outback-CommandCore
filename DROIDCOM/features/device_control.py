"""
DROIDCOM - Device Control Feature Module
Device control dialogs and actions implemented with PySide6.
"""

import subprocess

from PySide6 import QtCore, QtWidgets

from ..constants import IS_WINDOWS


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
                cmd = subprocess.run(
                    [adb_cmd, "-s", serial, "reboot", "edl download"],
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

            get_state_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings", "get", "global", "mobile_data"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            current_state = get_state_cmd.stdout.strip()
            new_state = "0" if current_state == "1" else "1"

            cmd = subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "settings",
                    "put",
                    "global",
                    "mobile_data",
                    new_state,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                state_text = "enabled" if new_state == "1" else "disabled"
                self.log_message(f"Mobile data {state_text}")
                self.update_status(f"Mobile data {state_text}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Mobile data has been {state_text}."
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
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
            if current_state == "null" or not current_state.isdigit():
                new_state = "1"
            else:
                new_state = "0" if current_state == "1" else "1"

            cmd = subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "service",
                    "call",
                    "bluetooth_manager",
                    "8",
                    "i32",
                    new_state,
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
                    "settings",
                    "put",
                    "global",
                    "bluetooth_on",
                    new_state,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if cmd.returncode == 0:
                state_text = "enabled" if new_state == "1" else "disabled"
                self.log_message(f"Bluetooth {state_text}")
                self.update_status(f"Bluetooth {state_text}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Bluetooth has been {state_text}."
                )
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
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
                new_state = "0" if current_state == "1" else "1"
                state_desc = "OFF" if new_state == "0" else "ON"

                set_state_cmd = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "put",
                        "global",
                        "airplane_mode_on",
                        new_state,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )

                if set_state_cmd.returncode == 0:
                    broadcast_cmd = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "am",
                            "broadcast",
                            "-a",
                            "android.intent.action.AIRPLANE_MODE",
                            "--ez",
                            "state",
                            "true" if new_state == "1" else "false",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10,
                    )

                    if broadcast_cmd.returncode == 0:
                        self.log_message(f"Airplane mode has been toggled {state_desc}.")
                        self.update_status(f"Airplane mode toggled {state_desc}")
                        QtWidgets.QMessageBox.information(
                            self,
                            "Airplane Mode Toggled",
                            f"Airplane mode has been turned {state_desc} on the device.",
                        )
                    else:
                        error_msg = broadcast_cmd.stderr.strip() or "Unknown error"
                        self.log_message(
                            f"Broadcasting airplane mode change failed: {error_msg}"
                        )
                        self.update_status("Airplane mode toggle incomplete")
                        QtWidgets.QMessageBox.critical(
                            self,
                            "Airplane Mode Toggle Failed",
                            f"Failed to broadcast airplane mode change: {error_msg}",
                        )
                else:
                    error_msg = set_state_cmd.stderr.strip() or "Unknown error"
                    self.log_message(f"Setting airplane mode state failed: {error_msg}")
                    self.update_status("Airplane mode toggle failed")
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Airplane Mode Toggle Failed",
                        f"Failed to set airplane mode state: {error_msg}",
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
                    cmd = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "sendevent",
                            "/dev/input/eventX",
                            "1",
                            "116",
                            "1",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=5,
                    )

                    subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "sendevent",
                            "/dev/input/eventX",
                            "1",
                            "116",
                            "0",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                    )

                    if cmd.returncode == 0:
                        self.log_message("Power button press simulated (alternative method)")
                        self.update_status("Power button pressed")
                    else:
                        error_msg = cmd.stderr.strip() or "Unknown error"
                        self.log_message(f"Failed to simulate power button: {error_msg}")
                        self.update_status("Power button simulation failed")
                        QtWidgets.QMessageBox.critical(
                            self,
                            "Error",
                            f"Failed to simulate power button: {error_msg}",
                        )
                else:
                    error_msg = event_cmd.stderr.strip() or "Unknown error"
                    self.log_message(f"Failed to find power button event: {error_msg}")
                    self.update_status("Power button simulation failed")
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        "Could not simulate power button press on this device.",
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
