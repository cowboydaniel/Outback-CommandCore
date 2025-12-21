"""
DROIDCOM - Security Feature Module
PySide6 migration for security dialogs.
"""

from PySide6 import QtCore, QtWidgets
import logging
import os
import re
import subprocess
import tempfile
import threading
import time
from datetime import datetime

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui, append_text, clear_text, set_progress, set_text


def append_text_safe(widget, text):
    if hasattr(widget, "appendPlainText"):
        widget.appendPlainText(text.rstrip("\n"))
        return
    append_text(widget, text)


class SecurityMixin:
    """Mixin class providing security functionality."""

    def _get_adb_command(self):
        if IS_WINDOWS:
            return self.adb_path or "adb"
        return "adb"

    def _get_device_serial(self):
        return self.device_info.get("serial") or self.device_serial

    def _run_adb_shell(self, command, timeout=None):
        """Run an adb shell command and return (success, stdout, stderr)."""
        if not self.device_connected:
            return False, "", "No device connected"

        serial = self._get_device_serial()
        if not serial:
            return False, "", "Device serial not available"

        adb_cmd = self._get_adb_command()
        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        except Exception as exc:
            return False, "", str(exc)

        success = result.returncode == 0
        return success, result.stdout.strip(), result.stderr.strip()

    def _check_root_status(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        serial = self._get_device_serial()
        if not serial:
            QtWidgets.QMessageBox.warning(
                self, "Root Status", "Device serial not found."
            )
            return

        adb_cmd = self._get_adb_command()

        try:
            which_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "which", "su"],
                capture_output=True,
                text=True,
            )

            if which_cmd.returncode == 0 and "/su" in which_cmd.stdout:
                QtWidgets.QMessageBox.information(self, "Root Status", "Device is rooted!")
                return

            su_cmd = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "su", "-c", "id"],
                capture_output=True,
                text=True,
            )

            if su_cmd.returncode == 0 and "uid=0" in su_cmd.stdout:
                QtWidgets.QMessageBox.information(self, "Root Status", "Device is rooted!")
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "Root Status",
                    "Device is not rooted or root access is not properly configured.",
                )

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Root Status", f"Failed to check root status: {exc}"
            )

    def _check_encryption_status(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        serial = self._get_device_serial()
        if not serial:
            QtWidgets.QMessageBox.warning(
                self, "Encryption Status", "Device serial not found."
            )
            return

        adb_cmd = self._get_adb_command()

        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop", "ro.crypto.state"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Encryption Status",
                    f"Failed to get encryption status: {result.stderr}",
                )
                return

            crypto_state = result.stdout.strip().lower()

            if crypto_state == "encrypted":
                crypto_type = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "getprop", "ro.crypto.type"],
                    capture_output=True,
                    text=True,
                )
                crypto_type_value = (
                    crypto_type.stdout.strip() if crypto_type.returncode == 0 else "unknown"
                )

                fde_required = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "getprop", "ro.crypto.fde_required"],
                    capture_output=True,
                    text=True,
                )
                fde_required_value = (
                    fde_required.stdout.strip() if fde_required.returncode == 0 else ""
                )

                msg = "Device is ENCRYPTED\n"
                msg += f"Encryption type: {crypto_type_value.upper()}\n"

                if fde_required_value:
                    msg += f"File-based encryption required: {fde_required_value}\n"

                lock_state = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "locksettings", "get-disabled"],
                    capture_output=True,
                    text=True,
                )
                if lock_state.returncode == 0 and "false" in lock_state.stdout.lower():
                    msg += "Device is secured with a lock screen\n"
                else:
                    msg += "Warning: Device is not secured with a lock screen\n"

                QtWidgets.QMessageBox.information(self, "Encryption Status", msg)
            else:
                QtWidgets.QMessageBox.information(
                    self, "Encryption Status", "Device is NOT encrypted"
                )

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Encryption Status", f"Failed to check encryption status: {exc}"
            )

    def _check_lock_screen_status(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        serial = self._get_device_serial()
        if not serial:
            QtWidgets.QMessageBox.warning(
                self, "Lock Screen Status", "Device serial not found."
            )
            return

        adb_cmd = self._get_adb_command()

        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "locksettings", "get-disabled"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Lock Screen Status",
                    f"Failed to get lock screen status: {result.stderr}",
                )
                return

            is_disabled = "true" in result.stdout.lower()

            if is_disabled:
                QtWidgets.QMessageBox.information(
                    self, "Lock Screen Status", "Lock screen is DISABLED (no security)"
                )
                return

            msg = "Lock screen is ENABLED\n\n"
            lock_type = self._detect_lock_screen_type(serial)

            if lock_type and lock_type != "swipe":
                msg += "Security Type: Secure (PIN/Pattern/Password)\n"
                msg += f"Lock Type: {lock_type.upper()}\n"

                visible_pattern = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "get",
                        "secure",
                        "lock_pattern_visible_pattern",
                    ],
                    capture_output=True,
                    text=True,
                )
                if visible_pattern.returncode == 0 and "1" in visible_pattern.stdout:
                    msg += "Visible Pattern: ENABLED (less secure)\n"

                owner_info = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "secure",
                        "get",
                        "lock_screen_owner_info_enabled",
                    ],
                    capture_output=True,
                    text=True,
                )
                if owner_info.returncode == 0 and "1" in owner_info.stdout:
                    msg += "Owner Info on Lock Screen: ENABLED\n"

                lock_timeout = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "secure",
                        "get",
                        "lock_screen_lock_after_timeout",
                    ],
                    capture_output=True,
                    text=True,
                )
                if lock_timeout.returncode == 0 and lock_timeout.stdout.strip().isdigit():
                    timeout_ms = int(lock_timeout.stdout.strip())
                    if timeout_ms > 0:
                        msg += f"Auto-lock after: {timeout_ms / 1000:.0f} seconds\n"

            else:
                keyguard = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "locksettings", "get-keyguard-secure"],
                    capture_output=True,
                    text=True,
                )
                if keyguard.returncode == 0 and "true" in keyguard.stdout.lower():
                    msg += "Security Type: Secure (PIN/Pattern/Password)\n"
                    msg += (
                        f"Lock Type: {lock_type.upper()}\n" if lock_type else "Lock Type: UNKNOWN\n"
                    )
                else:
                    msg += "Security Type: Swipe (no security)\n"

            encrypt_check = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop", "ro.crypto.state"],
                capture_output=True,
                text=True,
            )
            if encrypt_check.returncode == 0 and "encrypted" in encrypt_check.stdout.lower():
                msg += "\nDevice is ENCRYPTED"
            else:
                msg += "\nDevice is NOT encrypted (less secure)"

            QtWidgets.QMessageBox.information(self, "Lock Screen Status", msg)

        except Exception as exc:
            logging.error("Error checking lock screen status", exc_info=exc)
            QtWidgets.QMessageBox.critical(
                self, "Lock Screen Status", f"Failed to check lock screen status: {exc}"
            )

    def run_screen_lock_brute_forcer(self):
        """Launch the screen lock brute force testing utility."""
        self.log_message("Starting Screen Lock Brute Forcer...")

        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Screen Lock Brute Forcer")
        dialog.resize(750, 850)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        form_group = QtWidgets.QGroupBox("Brute Force Configuration")
        form_layout = QtWidgets.QGridLayout(form_group)

        form_layout.addWidget(QtWidgets.QLabel("Lock Type:"), 0, 0)
        lock_type_group = QtWidgets.QButtonGroup(dialog)
        pin_radio = QtWidgets.QRadioButton("PIN")
        pattern_radio = QtWidgets.QRadioButton("Pattern")
        pin_radio.setChecked(True)
        lock_type_group.addButton(pin_radio)
        lock_type_group.addButton(pattern_radio)
        lock_type_group.setId(pin_radio, 0)
        lock_type_group.setId(pattern_radio, 1)
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.addWidget(pin_radio)
        type_layout.addWidget(pattern_radio)
        type_layout.addStretch()
        form_layout.addLayout(type_layout, 0, 1)

        form_layout.addWidget(QtWidgets.QLabel("PIN Length:"), 1, 0)
        pin_length_combo = QtWidgets.QComboBox()
        pin_length_combo.addItems(["4", "5", "6"])
        form_layout.addWidget(pin_length_combo, 1, 1)

        form_layout.addWidget(QtWidgets.QLabel("Start Value (optional):"), 2, 0)
        start_value_edit = QtWidgets.QLineEdit()
        form_layout.addWidget(start_value_edit, 2, 1)

        form_layout.addWidget(QtWidgets.QLabel("Delay Between Attempts (ms):"), 3, 0)
        delay_edit = QtWidgets.QLineEdit("500")
        form_layout.addWidget(delay_edit, 3, 1)

        main_layout.addWidget(form_group)

        warning_label = QtWidgets.QLabel(
            "WARNING: This tool is for educational and security testing purposes only. "
            "Using this on devices without authorization is illegal and unethical. "
            "Always obtain explicit permission before testing any device."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: red;")
        main_layout.addWidget(warning_label)

        log_group = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        log_text = QtWidgets.QPlainTextEdit()
        log_text.setReadOnly(True)
        log_layout.addWidget(log_text)
        main_layout.addWidget(log_group)

        button_layout = QtWidgets.QHBoxLayout()
        start_btn = QtWidgets.QPushButton("Start Brute Force")
        stop_btn = QtWidgets.QPushButton("Stop Brute Force")
        stop_btn.setEnabled(False)
        button_layout.addWidget(start_btn)
        button_layout.addWidget(stop_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        running = {"active": False}

        def add_log(message):
            append_text_safe(log_text, message)

        def on_complete():
            def finish():
                running["active"] = False
                start_btn.setEnabled(True)
                stop_btn.setEnabled(False)
                append_text_safe(log_text, "Brute force operation completed or stopped.")

            emit_ui(self, finish)

        def start_brute_force():
            if running["active"]:
                return

            try:
                pin_len = int(pin_length_combo.currentText())
                if pin_len < 3 or pin_len > 8:
                    add_log("Invalid PIN length. Must be between 3 and 8 digits.")
                    return
            except ValueError:
                add_log("PIN length must be a number.")
                return

            try:
                delay = int(delay_edit.text().strip())
                if delay < 100:
                    add_log("WARNING: Very small delay might cause device instability.")
            except ValueError:
                add_log("Delay must be a number.")
                return

            start_value = 0
            if start_value_edit.text().strip():
                try:
                    start_value = int(start_value_edit.text().strip())
                except ValueError:
                    add_log("Start value must be a number.")
                    return

            running["active"] = True
            start_btn.setEnabled(False)
            stop_btn.setEnabled(True)
            selected_lock_type = "pin" if pin_radio.isChecked() else "pattern"
            add_log(
                f"Starting {'PIN' if selected_lock_type == 'pin' else 'Pattern'} brute force..."
            )

            thread = threading.Thread(
                target=lambda: self._run_screen_lock_brute_force(
                    selected_lock_type,
                    pin_len,
                    start_value,
                    delay,
                    lambda msg: emit_ui(self, lambda: add_log(msg)),
                    lambda: running["active"],
                    on_complete,
                ),
                daemon=True,
            )
            thread.start()

        def stop_brute_force():
            running["active"] = False
            add_log("Stopping brute force operation...")

        start_btn.clicked.connect(start_brute_force)
        stop_btn.clicked.connect(stop_brute_force)

        add_log("Configure the brute force parameters and click Start to begin.")
        dialog.exec()

    def _run_screen_lock_brute_force(
        self,
        lock_type,
        pin_length,
        start_value,
        delay_ms,
        log_callback,
        should_continue,
        on_complete,
    ):
        """Execute the actual brute force operation."""
        try:
            if not self.device_connected:
                log_callback("No device connected. Aborting.")
                return

            adb_cmd = self._get_adb_command()
            serial = self._get_device_serial()
            if not serial:
                log_callback("Device serial not found. Aborting.")
                return

            subprocess.run(
                [adb_cmd, "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"],
                capture_output=True,
                text=True,
            )
            time.sleep(1)

            subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "input",
                    "swipe",
                    "500",
                    "1500",
                    "500",
                    "500",
                ],
                capture_output=True,
                text=True,
            )
            time.sleep(1)

            window_dump = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "window"],
                capture_output=True,
                text=True,
            )
            if window_dump.returncode == 0 and "mDreamingLockscreen=true" not in window_dump.stdout:
                log_callback("Device does not appear to be locked. Lock the screen first.")
                return

            max_attempts = 10 ** pin_length
            log_callback(
                f"Maximum possible {pin_length}-digit PIN combinations: {max_attempts}"
            )

            current = start_value
            count = 0

            if lock_type == "pin":
                while should_continue() and current < max_attempts:
                    pin_value = str(current).zfill(pin_length)
                    log_callback(
                        f"Trying PIN: {pin_value} ({current + 1 - start_value}/{max_attempts - start_value} attempts)"
                    )

                    for digit in pin_value:
                        subprocess.run(
                            [
                                adb_cmd,
                                "-s",
                                serial,
                                "shell",
                                "input",
                                "text",
                                digit,
                            ],
                            capture_output=True,
                            text=True,
                        )
                        time.sleep(0.1)

                    subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "input",
                            "keyevent",
                            "KEYCODE_ENTER",
                        ],
                        capture_output=True,
                        text=True,
                    )

                    current += 1
                    count += 1

                    if count % 5 == 0:
                        locked_check = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "dumpsys", "window"],
                            capture_output=True,
                            text=True,
                        )
                        if (
                            locked_check.returncode == 0
                            and "mDreamingLockscreen=false" in locked_check.stdout
                        ):
                            log_callback(f"SUCCESS! Device unlocked with PIN: {pin_value}")
                            break

                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "input", "tap", "500", "1000"],
                            capture_output=True,
                            text=True,
                        )

                        timeout_text = self._check_lockout_message(adb_cmd, serial)
                        self._handle_lockout_wait(timeout_text, log_callback, should_continue)

                    time.sleep(delay_ms / 1000)

            elif lock_type == "pattern":
                common_patterns = [
                    "0123678",
                    "0124876",
                    "01258",
                    "02468",
                    "048",
                    "0124",
                    "01236",
                    "2748",
                    "0246",
                    "0,1,2,5,8,7,6,3,0",
                ]

                width, height = self._get_screen_size(adb_cmd, serial)
                grid = [
                    (width // 4, height // 4),
                    (width // 2, height // 4),
                    (3 * width // 4, height // 4),
                    (width // 4, height // 2),
                    (width // 2, height // 2),
                    (3 * width // 4, height // 2),
                    (width // 4, 3 * height // 4),
                    (width // 2, 3 * height // 4),
                    (3 * width // 4, 3 * height // 4),
                ]

                for pattern in common_patterns:
                    if not should_continue():
                        break

                    log_callback(f"Trying pattern: {pattern}")

                    subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "input",
                            "keyevent",
                            "KEYCODE_ESCAPE",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    time.sleep(1)

                    coords = [
                        grid[int(char)]
                        for char in pattern
                        if char.isdigit() and 0 <= int(char) <= 8
                    ]

                    if len(coords) >= 2:
                        swipe_cmd = [adb_cmd, "-s", serial, "shell", "input", "swipe"]
                        for x, y in coords:
                            swipe_cmd.extend([str(x), str(y)])

                        subprocess.run(swipe_cmd, capture_output=True, text=True)
                        time.sleep(1)

                        locked_check = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "dumpsys", "window"],
                            capture_output=True,
                            text=True,
                        )
                        if (
                            locked_check.returncode == 0
                            and "mDreamingLockscreen=false" in locked_check.stdout
                        ):
                            log_callback(f"SUCCESS! Device unlocked with pattern: {pattern}")
                            break

                        timeout_text = self._check_lockout_message(adb_cmd, serial)
                        self._handle_lockout_wait(timeout_text, log_callback, should_continue)

                        time.sleep(delay_ms / 1000)

            if should_continue():
                log_callback("Brute force completed without finding the correct combination.")

        except Exception as exc:
            log_callback(f"Error during brute force: {exc}")
            import traceback

            log_callback(traceback.format_exc())
        finally:
            on_complete()

    def _check_lockout_message(self, adb_cmd, serial):
        """Dump UI hierarchy and look for lockout messages."""
        try:
            subprocess.run(
                [adb_cmd, "-s", serial, "shell", "uiautomator", "dump", "/sdcard/ui.xml"],
                capture_output=True,
                text=True,
            )
            dump_result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cat", "/sdcard/ui.xml"],
                capture_output=True,
                text=True,
            )
            if dump_result.returncode == 0:
                return dump_result.stdout.lower()
            return ""
        finally:
            subprocess.run(
                [adb_cmd, "-s", serial, "shell", "rm", "/sdcard/ui.xml"],
                capture_output=True,
                text=True,
            )

    def _handle_lockout_wait(self, ui_text, log_callback, should_continue):
        if not ui_text or "try again" not in ui_text:
            return

        timeout_match = re.search(r"try again.* (\d+) (second|minute)s?", ui_text)
        if timeout_match:
            time_value = int(timeout_match.group(1))
            time_unit = timeout_match.group(2)
            wait_seconds = time_value if time_unit == "second" else time_value * 60
            wait_seconds += 5
        else:
            wait_seconds = 60

        log_callback(f"Lockout detected! Waiting {wait_seconds} seconds before resuming...")
        for i in range(wait_seconds):
            if not should_continue():
                break
            time.sleep(1)
            if i % 5 == 0:
                log_callback(f"Waiting for lockout: {wait_seconds - i} seconds remaining...")

    def _get_screen_size(self, adb_cmd, serial):
        size_result = subprocess.run(
            [adb_cmd, "-s", serial, "shell", "wm", "size"],
            capture_output=True,
            text=True,
        )
        width, height = 1080, 1920
        if size_result.returncode == 0 and "Physical size:" in size_result.stdout:
            try:
                size_str = size_result.stdout.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split("x"))
            except (IndexError, ValueError):
                pass
        return width, height

    def _detect_lock_screen_type(self, serial):
        adb_cmd = self._get_adb_command()
        lock_type = None
        logging.info("Starting enhanced lock screen type detection...")

        try:
            power_result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "power"],
                capture_output=True,
                text=True,
            )
            screen_on = (
                "mWakefulness=Awake" in power_result.stdout
                or "Display Power: state=ON" in power_result.stdout
            )

            if screen_on:
                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "input", "keyevent", "KEYCODE_POWER"],
                    capture_output=True,
                    text=True,
                )
                time.sleep(1)

            subprocess.run(
                [adb_cmd, "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"],
                capture_output=True,
                text=True,
            )
            time.sleep(1.5)

            width, height = self._get_screen_size(adb_cmd, serial)
            subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "input",
                    "swipe",
                    str(width // 2),
                    str(int(height * 0.9)),
                    str(width // 2),
                    str(int(height * 0.5)),
                    "300",
                ],
                capture_output=True,
                text=True,
            )
            time.sleep(1)

            status_result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "window"],
                capture_output=True,
                text=True,
            )
            window_status = status_result.stdout
            logging.info(
                "Window status check: Keyguard showing = %s",
                "mShowingLockscreen=true" in window_status
                or "isStatusBarKeyguard=true" in window_status,
            )

            subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "input",
                    "swipe",
                    str(width // 2),
                    str(int(height * 0.95)),
                    str(width // 2),
                    str(int(height * 0.1)),
                    "500",
                ],
                capture_output=True,
                text=True,
            )
            time.sleep(1)

            tap_cmd = [adb_cmd, "-s", serial, "shell", "input", "tap", str(width // 2), str(height // 2)]
            subprocess.run(tap_cmd, capture_output=True, text=True)
            time.sleep(0.3)
            subprocess.run(tap_cmd, capture_output=True, text=True)
            time.sleep(0.7)

            subprocess.run(
                [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "input",
                    "tap",
                    str(width // 2),
                    str(int(height * 0.9)),
                ],
                capture_output=True,
                text=True,
            )
            time.sleep(0.5)

            ui_content = ""
            with tempfile.TemporaryDirectory() as temp_dir:
                ui_dump_path = os.path.join(temp_dir, "ui_dump.xml")
                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"],
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [adb_cmd, "-s", serial, "pull", "/sdcard/ui_dump.xml", ui_dump_path],
                    capture_output=True,
                    text=True,
                )

                if os.path.exists(ui_dump_path):
                    with open(ui_dump_path, "r", encoding="utf-8") as handle:
                        ui_content = handle.read().lower()

                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "rm", "/sdcard/ui_dump.xml"],
                    capture_output=True,
                    text=True,
                )

            if ui_content:
                digit_buttons = [
                    str(digit)
                    for digit in range(10)
                    if f'text="{digit}"' in ui_content or f"text='{digit}'" in ui_content
                ]
                numeric_keyboard = len(digit_buttons) >= 3

                keyboard_rows = 0
                if "row=\"0\"" in ui_content and "row=\"1\"" in ui_content and "row=\"2\"" in ui_content:
                    keyboard_rows += 1

                pin_markers = [
                    "numpad",
                    "numpadkey",
                    "numericpadkey",
                    "numpinentry",
                    "pinkeyboardview",
                    "pin_view",
                ]
                found_pin_markers = [marker for marker in pin_markers if marker in ui_content]

                if numeric_keyboard or found_pin_markers or keyboard_rows > 0:
                    lock_type = "pin"

                pattern_markers = ["pattern", "patternview", "lockpatternview", "gesturepasswordview"]
                found_pattern_markers = [marker for marker in pattern_markers if marker in ui_content]
                if not lock_type and found_pattern_markers:
                    lock_type = "pattern"

                if not lock_type:
                    password_markers = [
                        "passwordentry",
                        "passwordview",
                        "passwordfieldview",
                        "edittextpassword",
                    ]
                    found_password_markers = [marker for marker in password_markers if marker in ui_content]
                    if "password" in ui_content and not numeric_keyboard:
                        found_password_markers.append("password")

                    if found_password_markers:
                        lock_type = "password"

                swipe_markers = ["swipe", "slide", "slidingchallenge"]
                found_swipe_markers = [marker for marker in swipe_markers if marker in ui_content]
                if not lock_type and "keyguard" in ui_content and found_swipe_markers:
                    lock_type = "swipe"

            if not lock_type:
                keyguard_result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "dumpsys", "keyguard"],
                    capture_output=True,
                    text=True,
                )
                if keyguard_result.returncode == 0:
                    kg_output = keyguard_result.stdout.lower()
                    if any(
                        marker in kg_output
                        for marker in [
                            "pattern",
                            "patternview",
                            "mpatternview",
                            "patternunlockcontroller",
                        ]
                    ):
                        lock_type = "pattern"
                    elif any(
                        marker in kg_output
                        for marker in ["pin", "pinkeyboardview", "pinview", "pinsliderview"]
                    ):
                        lock_type = "pin"
                    elif any(
                        marker in kg_output
                        for marker in [
                            "password",
                            "passwordview",
                            "keyguardpasswordview",
                            "passwordtextview",
                        ]
                    ):
                        lock_type = "password"

            if not lock_type:
                pw_result = subprocess.run(
                    [
                        adb_cmd,
                        "-s",
                        serial,
                        "shell",
                        "settings",
                        "get",
                        "secure",
                        "lockscreen.password_type",
                    ],
                    capture_output=True,
                    text=True,
                )
                if pw_result.returncode == 0 and pw_result.stdout.strip() and pw_result.stdout.strip() != "null":
                    try:
                        pw_type_val = int(pw_result.stdout.strip())
                        if pw_type_val in [65536, 131072, 196608]:
                            lock_type = "pin"
                        elif pw_type_val >= 262144:
                            lock_type = "password"
                        elif pw_type_val in [65536, 1]:
                            lock_type = "pattern"
                    except ValueError:
                        pass

                if not lock_type:
                    pattern_result = subprocess.run(
                        [
                            adb_cmd,
                            "-s",
                            serial,
                            "shell",
                            "settings",
                            "get",
                            "secure",
                            "lock_pattern_autolock",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if pattern_result.returncode == 0 and pattern_result.stdout.strip() == "1":
                        lock_type = "pattern"

            if not lock_type:
                disabled_result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "locksettings", "get-disabled"],
                    capture_output=True,
                    text=True,
                )
                if disabled_result.returncode == 0 and "false" in disabled_result.stdout.lower():
                    secure_result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "locksettings", "get-keyguard-secure"],
                        capture_output=True,
                        text=True,
                    )
                    if secure_result.returncode == 0 and "false" in secure_result.stdout.lower():
                        lock_type = "swipe"

        except Exception as exc:
            logging.error("Error detecting lock screen type: %s", exc)

        logging.info("Final lock type detection result: %s", lock_type)
        return lock_type

    def _check_security_patch_level(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Security Patch Level")
        dialog.resize(700, 550)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        info_group = QtWidgets.QGroupBox("Device Information")
        info_layout = QtWidgets.QGridLayout(info_group)
        device_label = QtWidgets.QLabel("")
        version_label = QtWidgets.QLabel("")
        build_label = QtWidgets.QLabel("")

        info_layout.addWidget(QtWidgets.QLabel("Device:"), 0, 0)
        info_layout.addWidget(device_label, 0, 1)
        info_layout.addWidget(QtWidgets.QLabel("Android Version:"), 1, 0)
        info_layout.addWidget(version_label, 1, 1)
        info_layout.addWidget(QtWidgets.QLabel("Build ID:"), 2, 0)
        info_layout.addWidget(build_label, 2, 1)

        main_layout.addWidget(info_group)

        patch_group = QtWidgets.QGroupBox("Security Patch Status")
        patch_layout = QtWidgets.QVBoxLayout(patch_group)
        patch_title = QtWidgets.QLabel("Current Patch Level:")
        patch_title.setStyleSheet("font-weight: bold;")
        patch_label = QtWidgets.QLabel("")
        patch_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_label = QtWidgets.QLabel("Checking...")
        patch_layout.addWidget(patch_title, alignment=QtCore.Qt.AlignCenter)
        patch_layout.addWidget(patch_label, alignment=QtCore.Qt.AlignCenter)
        patch_layout.addWidget(status_label, alignment=QtCore.Qt.AlignCenter)
        main_layout.addWidget(patch_group)

        details_group = QtWidgets.QGroupBox("Patch Details")
        details_layout = QtWidgets.QVBoxLayout(details_group)
        details_text = QtWidgets.QPlainTextEdit()
        details_text.setReadOnly(True)
        details_layout.addWidget(details_text)
        main_layout.addWidget(details_group)

        button_layout = QtWidgets.QHBoxLayout()
        update_btn = QtWidgets.QPushButton("Check for Updates")
        update_btn.clicked.connect(lambda: self._check_for_updates(details_text))
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(update_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        def update_ui():
            try:
                device_model = self._run_adb_shell("getprop ro.product.model")[1]
                device_manufacturer = self._run_adb_shell("getprop ro.product.manufacturer")[1]
                build_version = self._run_adb_shell("getprop ro.build.version.release")[1]
                build_id = self._run_adb_shell("getprop ro.build.id")[1]
                patch_level = self._run_adb_shell("getprop ro.build.version.security_patch")[1]

                def apply_updates():
                    device_label.setText(f"{device_manufacturer} {device_model}".strip())
                    version_label.setText(build_version)
                    build_label.setText(build_id)

                    if not patch_level:
                        patch_label.setText("Unknown")
                        patch_label.setStyleSheet("color: orange; font-weight: bold;")
                        status_label.setText("Could not determine security patch level")
                        status_label.setStyleSheet("color: orange;")
                        return

                    patch_label.setText(patch_level)
                    patch_label.setStyleSheet("font-size: 14px; font-weight: bold;")

                    details_text.clear()

                    try:
                        patch_date = datetime.strptime(patch_level, "%Y-%m-%d")
                        today = datetime.now()
                        days_since_patch = (today - patch_date).days

                        if days_since_patch < 0:
                            status_label.setText("Warning: Patch date is in the future!")
                            status_label.setStyleSheet("color: orange;")
                            details_text.appendPlainText(
                                "The reported patch date is in the future. This usually indicates an incorrect system clock."
                            )
                        elif days_since_patch == 0:
                            status_label.setText("Your device is up to date!")
                            status_label.setStyleSheet("color: green;")
                            details_text.appendPlainText(
                                "Your device has the latest security patches installed."
                            )
                        elif days_since_patch <= 30:
                            status_label.setText("Your device is up to date!")
                            status_label.setStyleSheet("color: green;")
                            details_text.appendPlainText(
                                f"Your device was patched {days_since_patch} days ago."
                            )
                        elif days_since_patch <= 90:
                            status_label.setText(
                                f"Update available ({days_since_patch} days old)"
                            )
                            status_label.setStyleSheet("color: orange;")
                            details_text.appendPlainText(
                                f"Your device security patch is {days_since_patch} days old."
                            )
                            details_text.appendPlainText(
                                "Consider updating your device to receive the latest security fixes."
                            )
                        else:
                            status_label.setText("Update required!")
                            status_label.setStyleSheet("color: red;")
                            details_text.appendPlainText(
                                f"WARNING: Your device security patch is {days_since_patch} days old!"
                            )
                            details_text.appendPlainText(
                                "Your device is vulnerable to known security issues."
                            )
                            details_text.appendPlainText(
                                "Please update your device as soon as possible."
                            )

                        details_text.appendPlainText("")
                        details_text.appendPlainText(
                            "Security patches protect your device from known vulnerabilities."
                        )
                        details_text.appendPlainText(
                            "Google releases security patches monthly, and device manufacturers distribute them to their devices."
                        )

                        pending_update = self._run_adb_shell(
                            "dumpsys package system | grep -i 'update_available' | grep -i 'true'"
                        )[1]
                        if pending_update:
                            details_text.appendPlainText("")
                            details_text.appendPlainText(
                                "There is a pending system update available. Please install it to get the latest security patches."
                            )

                    except ValueError as ve:
                        status_label.setText("Error parsing patch date")
                        status_label.setStyleSheet("color: red;")
                        details_text.setPlainText(
                            f"Error: Could not parse patch date: {ve}"
                        )

                emit_ui(self, apply_updates)

            except Exception as exc:
                def show_error():
                    status_label.setText("Error checking patch level")
                    status_label.setStyleSheet("color: red;")
                    details_text.setPlainText(f"Error: {exc}")

                emit_ui(self, show_error)

        threading.Thread(target=update_ui, daemon=True).start()
        dialog.exec()

    def _check_for_updates(self, details_text):
        try:
            clear_text(details_text)
            append_text_safe(details_text, "Checking for updates...")

            update_commands = [
                "dumpsys package system | grep -i 'update_available'",
                "getprop | grep -i update",
                "pm list packages | grep -i update",
            ]

            update_found = False

            for cmd in update_commands:
                result = self._run_adb_shell(cmd, timeout=5)[1]
                if result and "not found" not in result.lower():
                    append_text_safe(details_text, f"\nUpdate check result:\n{result}")
                    if "true" in result.lower():
                        update_found = True

            if not update_found:
                append_text_safe(details_text, "\nNo pending updates found. Your device is up to date.")
            else:
                append_text_safe(
                    details_text,
                    "\n\nNote: Updates may be available. Please check your device's System Update section in Settings.",
                )

        except Exception as exc:
            clear_text(details_text)
            append_text_safe(details_text, f"Error checking for updates: {exc}")

    def _scan_dangerous_permissions(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Dangerous Permissions Scanner")
        dialog.resize(900, 700)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        progress_group = QtWidgets.QGroupBox("Scan Progress")
        progress_layout = QtWidgets.QVBoxLayout(progress_group)
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setRange(0, 100)
        progress_layout.addWidget(progress_bar)
        status_label = QtWidgets.QLabel("Preparing to scan...")
        progress_layout.addWidget(status_label)
        main_layout.addWidget(progress_group)

        results_group = QtWidgets.QGroupBox("Scan Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Application", "Permissions", "Risk Level"])
        tree.setColumnWidth(0, 250)
        tree.setColumnWidth(1, 500)
        results_layout.addWidget(tree)
        main_layout.addWidget(results_group)

        details_group = QtWidgets.QGroupBox("Permission Details")
        details_layout = QtWidgets.QVBoxLayout(details_group)
        details_text = QtWidgets.QPlainTextEdit()
        details_text.setReadOnly(True)
        details_layout.addWidget(details_text)
        main_layout.addWidget(details_group)

        button_layout = QtWidgets.QHBoxLayout()
        scan_btn = QtWidgets.QPushButton("Start Scan")
        export_btn = QtWidgets.QPushButton("Export Results")
        export_btn.setEnabled(False)
        close_btn = QtWidgets.QPushButton("Close")
        button_layout.addWidget(scan_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        scan_btn.clicked.connect(
            lambda: self._start_permission_scan(
                dialog, tree, details_text, status_label, progress_bar, scan_btn
            )
        )
        export_btn.clicked.connect(lambda: self._export_permission_scan(tree, dialog))
        close_btn.clicked.connect(dialog.close)

        tree.itemSelectionChanged.connect(
            lambda: self._on_permission_select(tree, details_text, export_btn)
        )

        dialog.exec()

    def _start_permission_scan(
        self, dialog, tree, details_text, status_label, progress_bar, scan_btn
    ):
        def update_status(message, progress=None):
            emit_ui(self, lambda: set_text(status_label, message))
            if progress is not None:
                emit_ui(self, lambda: set_progress(progress_bar, progress))

        def scan_complete():
            emit_ui(self, lambda: scan_btn.setEnabled(True))
            update_status("Scan complete!", 100)
            emit_ui(self, lambda: append_text_safe(details_text, "\n✅ Scan complete!"))

        def scan_worker():
            try:
                emit_ui(self, lambda: tree.clear())
                emit_ui(self, lambda: clear_text(details_text))
                emit_ui(self, lambda: append_text_safe(details_text, "Scanning for dangerous permissions..."))
                emit_ui(self, lambda: scan_btn.setEnabled(False))

                dangerous_permissions = {
                    "android.permission.READ_CALENDAR": "High: Can read calendar events",
                    "android.permission.WRITE_CALENDAR": "High: Can modify calendar events",
                    "android.permission.CAMERA": "High: Can access camera",
                    "android.permission.READ_CONTACTS": "High: Can read contacts",
                    "android.permission.WRITE_CONTACTS": "High: Can modify contacts",
                    "android.permission.GET_ACCOUNTS": "High: Can access account information",
                    "android.permission.ACCESS_FINE_LOCATION": "High: Precise location access",
                    "android.permission.ACCESS_COARSE_LOCATION": "High: Approximate location access",
                    "android.permission.RECORD_AUDIO": "High: Can record audio",
                    "android.permission.READ_PHONE_STATE": "High: Can read phone state",
                    "android.permission.READ_PHONE_NUMBERS": "High: Can read phone numbers",
                    "android.permission.CALL_PHONE": "High: Can make phone calls",
                    "android.permission.ANSWER_PHONE_CALLS": "High: Can answer calls",
                    "android.permission.READ_CALL_LOG": "High: Can read call history",
                    "android.permission.WRITE_CALL_LOG": "High: Can modify call history",
                    "android.permission.ADD_VOICEMAIL": "High: Can add voicemail",
                    "android.permission.USE_SIP": "High: Can make SIP calls",
                    "android.permission.PROCESS_OUTGOING_CALLS": "High: Can monitor outgoing calls",
                    "android.permission.BODY_SENSORS": "High: Can access health data",
                    "android.permission.SEND_SMS": "High: Can send SMS",
                    "android.permission.RECEIVE_SMS": "High: Can receive SMS",
                    "android.permission.READ_SMS": "High: Can read SMS",
                    "android.permission.RECEIVE_WAP_PUSH": "High: Can receive WAP push",
                    "android.permission.RECEIVE_MMS": "High: Can receive MMS",
                    "android.permission.READ_EXTERNAL_STORAGE": "High: Can read external storage",
                    "android.permission.WRITE_EXTERNAL_STORAGE": "High: Can write to external storage",
                    "android.permission.MOUNT_UNMOUNT_FILESYSTEMS": "High: Can mount/unmount filesystems",
                    "android.permission.READ_LOGS": "High: Can read system logs",
                    "android.permission.SET_ANIMATION_SCALE": "High: Can modify system animation",
                    "android.permission.PACKAGE_USAGE_STATS": "High: Can access usage statistics",
                    "android.permission.REQUEST_INSTALL_PACKAGES": "High: Can install packages",
                    "android.permission.DELETE_PACKAGES": "High: Can delete packages",
                    "android.permission.ACCESS_WIFI_STATE": "Medium: Can access WiFi info",
                    "android.permission.CHANGE_WIFI_STATE": "Medium: Can modify WiFi state",
                    "android.permission.BLUETOOTH": "Medium: Can access Bluetooth",
                    "android.permission.BLUETOOTH_ADMIN": "Medium: Can modify Bluetooth",
                    "android.permission.NFC": "Medium: Can access NFC",
                    "android.permission.INTERNET": "Medium: Can access internet",
                    "android.permission.ACCESS_NETWORK_STATE": "Low: Can check network state",
                    "android.permission.VIBRATE": "Low: Can control vibration",
                    "android.permission.WAKE_LOCK": "Low: Can prevent sleep",
                    "android.permission.RECEIVE_BOOT_COMPLETED": "Low: Can run at boot",
                    "android.permission.SYSTEM_ALERT_WINDOW": "High: Can draw over other apps",
                    "android.permission.WRITE_SETTINGS": "High: Can modify system settings",
                    "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS": "Medium: Can ignore battery optimization",
                    "android.permission.BIND_ACCESSIBILITY_SERVICE": "High: Can capture screen content",
                    "android.permission.PACKAGE_VERIFICATION_AGENT": "High: Can verify app installs",
                }

                update_status("Getting list of installed apps...", 10)
                packages_output = self._run_adb_shell("pm list packages -f -3")[1]
                packages = []

                for line in packages_output.splitlines():
                    if "=" in line:
                        parts = line.split("=")
                        if len(parts) == 2:
                            pkg_path = parts[0].split(":")[-1].strip()
                            pkg_name = parts[1].strip()
                            packages.append((pkg_name, pkg_path))

                if not packages:
                    emit_ui(
                        self,
                        lambda: append_text_safe(
                            details_text,
                            "No third-party apps found or could not retrieve package list.",
                        ),
                    )
                    scan_complete()
                    return

                update_status(
                    f"Scanning {len(packages)} apps for dangerous permissions...", 20
                )

                dangerous_apps = {}
                total_packages = len(packages)

                for i, (pkg_name, pkg_path) in enumerate(packages, 1):
                    progress = 20 + int((i / total_packages) * 70)
                    update_status(f"Scanning {i}/{total_packages}: {pkg_name[:20]}...", progress)

                    app_label = self._run_adb_shell(f"pm list packages -f {pkg_name} -l")[1]
                    if "=" in app_label:
                        app_label = app_label.split("=")[1].strip()
                    else:
                        app_label = pkg_name

                    perms_output = self._run_adb_shell(
                        f'dumpsys package {pkg_name} | grep -A 1 "requested permissions"'
                    )[1]

                    dangerous_perms = []
                    for perm, desc in dangerous_permissions.items():
                        if perm in perms_output:
                            dangerous_perms.append(f"{perm}: {desc}")

                    if dangerous_perms:
                        dangerous_apps[app_label] = dangerous_perms

                update_status("Processing results...", 95)

                sorted_apps = sorted(
                    dangerous_apps.items(), key=lambda x: len(x[1]), reverse=True
                )

                def add_results():
                    for app_label, perms in sorted_apps:
                        risk_level = "High" if any("High" in p for p in perms) else "Medium"
                        item = QtWidgets.QTreeWidgetItem(
                            [
                                app_label[:50] + ("..." if len(app_label) > 50 else ""),
                                "\n".join(perms),
                                risk_level,
                            ]
                        )
                        item.setData(0, QtCore.Qt.UserRole, perms)
                        tree.addTopLevelItem(item)

                    if not dangerous_apps:
                        tree.addTopLevelItem(
                            QtWidgets.QTreeWidgetItem(
                                [
                                    "No dangerous permissions found",
                                    "All apps appear to be well-behaved",
                                    "",
                                ]
                            )
                        )

                emit_ui(self, add_results)
                scan_complete()

            except Exception as exc:
                emit_ui(
                    self,
                    lambda: append_text_safe(details_text, f"\n❌ Error during scan: {exc}"),
                )
                update_status(f"Error: {str(exc)[:50]}...", 0)
                emit_ui(self, lambda: scan_btn.setEnabled(True))

        threading.Thread(target=scan_worker, daemon=True).start()

    def _on_permission_select(self, tree, details_text, export_btn):
        selected_items = tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        app_name = item.text(0)
        permissions = item.data(0, QtCore.Qt.UserRole) or []

        clear_text(details_text)
        append_text_safe(details_text, f"Application: {app_name}")
        append_text_safe(details_text, "=" * 50)

        if len(permissions) == 1 and "No dangerous permissions" in permissions[0]:
            append_text_safe(details_text, "✅ This app doesn't request any dangerous permissions.")
        elif permissions:
            append_text_safe(
                details_text, f"⚠️ This app requests {len(permissions)} dangerous permissions:\n"
            )
            for perm in permissions:
                append_text_safe(details_text, f"• {perm}")

        export_btn.setEnabled(True)

    def _export_permission_scan(self, tree, parent):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            "Save Permission Scan Results As",
            "",
            "Text Files (*.txt);;All Files (*)",
        )

        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as handle:
                handle.write("Dangerous Permissions Scan Results\n")
                handle.write("=" * 50 + "\n\n")
                handle.write(f"{'Application':<40} | {'Permissions':<40} | {'Risk Level'}\n")
                handle.write("-" * 100 + "\n")

                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    app_name = item.text(0)
                    perms = item.text(1).replace("\n", ", ")
                    risk = item.text(2)
                    handle.write(f"{app_name:<40} | {perms:<40} | {risk}\n")

                handle.write("\nGenerated by Nest Android Tools\n")
                handle.write(
                    f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

            QtWidgets.QMessageBox.information(
                parent, "Export Complete", f"Results have been exported to:\n{filename}"
            )

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                parent, "Export Error", f"Failed to export results:\n{exc}"
            )

    def _check_certificates(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Certificate Checker")
        dialog.resize(1000, 700)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        info_group = QtWidgets.QGroupBox("Certificate Stores")
        info_layout = QtWidgets.QVBoxLayout(info_group)

        cert_stores = [
            ("/system/etc/security/cacerts", "System Trusted Certificates"),
            ("/system/etc/security/cacerts_google", "Google Trusted Certificates"),
            ("/data/misc/user/0/cacerts-added", "User Added Certificates"),
            ("/data/misc/keystore/user_0", "User Keystore"),
        ]

        store_status = {}
        for path, name in cert_stores:
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(f"{name}:"))
            status_label = QtWidgets.QLabel("Checking...")
            status_label.setStyleSheet("color: blue;")
            row.addWidget(status_label)
            row.addStretch()
            info_layout.addLayout(row)
            store_status[path] = status_label

        main_layout.addWidget(info_group)

        notebook = QtWidgets.QTabWidget()
        certs_tab = QtWidgets.QWidget()
        certs_layout = QtWidgets.QVBoxLayout(certs_tab)

        columns = ["Store", "Certificate", "Subject", "Issuer", "Expires", "Status"]
        cert_table = QtWidgets.QTableWidget(0, len(columns))
        cert_table.setHorizontalHeaderLabels(columns)
        cert_table.horizontalHeader().setStretchLastSection(True)
        cert_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        certs_layout.addWidget(cert_table)

        notebook.addTab(certs_tab, "Certificates")

        details_tab = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(details_tab)
        details_text = QtWidgets.QPlainTextEdit()
        details_text.setReadOnly(True)
        details_layout.addWidget(details_text)
        notebook.addTab(details_tab, "Certificate Details")

        main_layout.addWidget(notebook)

        button_layout = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton("Export Selected")
        export_btn.setEnabled(False)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        close_btn = QtWidgets.QPushButton("Close")
        button_layout.addWidget(export_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        export_btn.clicked.connect(lambda: self._export_certificate(dialog, cert_table))
        refresh_btn.clicked.connect(
            lambda: self._update_certificates(
                dialog, cert_stores, store_status, cert_table, details_text, export_btn
            )
        )
        close_btn.clicked.connect(dialog.close)

        cert_table.itemSelectionChanged.connect(
            lambda: self._on_cert_select(cert_table, details_text, export_btn)
        )

        self._update_certificates(
            dialog, cert_stores, store_status, cert_table, details_text, export_btn
        )
        dialog.exec()

    def _update_certificates(
        self, dialog, cert_stores, store_status, cert_table, details_text, export_btn
    ):
        try:
            cert_table.setRowCount(0)
            clear_text(details_text)
            export_btn.setEnabled(False)

            for cert_dir, store_name in cert_stores:
                ls_result = self._run_adb_shell(f"ls -la {cert_dir} 2>/dev/null", timeout=5)[1]

                if not ls_result or "No such file or directory" in ls_result:
                    store_status[cert_dir].setText("Not found")
                    store_status[cert_dir].setStyleSheet("color: gray;")
                    continue

                store_status[cert_dir].setText("Found")
                store_status[cert_dir].setStyleSheet("color: green;")

                cert_files = self._run_adb_shell(
                    "find {path} -type f \\( -name '*.0' -o -name '*.cer' -o -name '*.crt' -o -name '*.pem' \\) 2>/dev/null".format(
                        path=cert_dir
                    ),
                    timeout=10,
                )[1]

                if not cert_files:
                    continue

                for cert_file in cert_files.split("\n"):
                    cert_file = cert_file.strip()
                    if not cert_file:
                        continue

                    cert_info = self._run_adb_shell(
                        f"openssl x509 -in {cert_file} -noout -subject -issuer -enddate 2>/dev/null",
                        timeout=5,
                    )[1]
                    if not cert_info or "unable to load certificate" in cert_info.lower():
                        continue

                    subject = ""
                    issuer = ""
                    expires = ""
                    status = "Valid"

                    for line in cert_info.split("\n"):
                        line = line.strip()
                        if line.startswith("subject="):
                            subject = line.replace("subject=", "").strip()
                        elif line.startswith("issuer="):
                            issuer = line.replace("issuer=", "").strip()
                        elif line.startswith("notAfter="):
                            date_str = line.replace("notAfter=", "").strip()
                            try:
                                exp_date = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                                expires = exp_date.strftime("%Y-%m-%d")
                                now = datetime.now()
                                if exp_date < now:
                                    status = "Expired"
                                else:
                                    days_left = (exp_date - now).days
                                    if days_left < 30:
                                        status = f"Expires in {days_left} days"
                            except ValueError:
                                expires = date_str

                    row = cert_table.rowCount()
                    cert_table.insertRow(row)
                    values = [
                        store_name,
                        os.path.basename(cert_file),
                        subject,
                        issuer,
                        expires,
                        status,
                    ]
                    for col, value in enumerate(values):
                        item = QtWidgets.QTableWidgetItem(value)
                        if col == 1:
                            item.setData(QtCore.Qt.UserRole, cert_file)
                        cert_table.setItem(row, col, item)

        except Exception as exc:
            clear_text(details_text)
            append_text_safe(details_text, f"Error updating certificate information: {exc}")

    def _on_cert_select(self, cert_table, details_text, export_btn):
        selected_items = cert_table.selectedItems()
        if not selected_items:
            return

        cert_item = selected_items[1]
        cert_file = cert_item.data(QtCore.Qt.UserRole)
        if not cert_file:
            return

        cert_info = self._run_adb_shell(
            f"openssl x509 -in {cert_file} -noout -text 2>/dev/null"
        )[1]

        clear_text(details_text)
        append_text_safe(details_text, cert_info or "Unable to load certificate details.")
        export_btn.setEnabled(True)

    def _export_certificate(self, parent, cert_table):
        selected_items = cert_table.selectedItems()
        if not selected_items:
            return

        cert_item = selected_items[1]
        cert_file = cert_item.data(QtCore.Qt.UserRole)
        cert_name = cert_item.text()

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            "Save Certificate As",
            cert_name,
            "Certificate files (*.cer *.crt *.pem);;All Files (*)",
        )

        if not filename:
            return

        try:
            cert_content = self._run_adb_shell(f"cat {cert_file}")[1]
            if not cert_content:
                raise ValueError("Certificate content not found")

            with open(filename, "w", encoding="utf-8") as handle:
                handle.write(cert_content)

            QtWidgets.QMessageBox.information(
                parent, "Success", f"Certificate saved to:\n{filename}"
            )

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                parent, "Error", f"Failed to export certificate: {exc}"
            )

    def _verify_boot_integrity(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Boot Integrity Check")
        dialog.resize(700, 600)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        info_group = QtWidgets.QGroupBox("Boot Status Overview")
        info_layout = QtWidgets.QGridLayout(info_group)

        status_labels = {}
        status_items = [
            ("Boot State", "boot_state"),
            ("Verified Boot", "verified_boot"),
            ("AVB State", "avb_state"),
            ("Bootloader Locked", "bootloader_locked"),
            ("DM-Verity", "dm_verity"),
            ("SELinux", "selinux"),
            ("Root Status", "root_status"),
            ("Secure Boot", "secure_boot"),
        ]

        for i, (label_text, key) in enumerate(status_items):
            info_layout.addWidget(QtWidgets.QLabel(f"{label_text}:"), i, 0)
            status_label = QtWidgets.QLabel("Checking...")
            info_layout.addWidget(status_label, i, 1)
            status_labels[key] = status_label

        main_layout.addWidget(info_group)

        details_group = QtWidgets.QGroupBox("Detailed Information")
        details_layout = QtWidgets.QVBoxLayout(details_group)
        details_text = QtWidgets.QPlainTextEdit()
        details_text.setReadOnly(True)
        details_layout.addWidget(details_text)
        main_layout.addWidget(details_group)

        button_layout = QtWidgets.QHBoxLayout()
        refresh_btn = QtWidgets.QPushButton("Refresh")
        close_btn = QtWidgets.QPushButton("Close")
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        refresh_btn.clicked.connect(
            lambda: self._update_boot_integrity(dialog, status_labels, details_text)
        )
        close_btn.clicked.connect(dialog.close)

        self._update_boot_integrity(dialog, status_labels, details_text)
        dialog.exec()

    def _update_boot_integrity(self, dialog, status_labels, details_text):
        try:
            clear_text(details_text)

            boot_status = self._run_adb_shell("getprop ro.boot.verifiedbootstate")[1] or "Unknown"
            boot_verified = self._run_adb_shell("getprop ro.boot.veritymode")[1] or "Unknown"
            boot_flash = self._run_adb_shell("getprop ro.boot.flash.locked")[1] or "Unknown"
            boot_verified_bootstate = (
                self._run_adb_shell("getprop ro.boot.verifiedstate")[1] or "Unknown"
            )
            boot_vbmeta = (
                self._run_adb_shell("getprop ro.boot.vbmeta.device_state")[1]
                or "Unknown"
            )

            bootloader_unlocked = boot_status != "green"
            verity_mode = boot_verified or "Not supported"

            selinux_status = self._run_adb_shell("getenforce")[1]
            selinux_mode = "Enforcing" if selinux_status == "Enforcing" else "Permissive"

            root_output = self._run_adb_shell("su -c id")[1]
            root_status = "Root access detected" if "uid=0" in root_output else "No root access"

            secure_boot = self._run_adb_shell("getprop ro.secure")[1]
            secure_boot_value = "Enabled" if secure_boot == "1" else "Disabled"

            def set_status(label, value, color=None):
                set_text(label, value)
                if color:
                    label.setStyleSheet(f"color: {color};")

            set_status(
                status_labels["boot_state"],
                boot_status,
                "green" if boot_status == "green" else "red",
            )
            set_status(
                status_labels["verified_boot"],
                boot_verified,
                "green" if boot_verified == "enforcing" else "red",
            )
            set_status(
                status_labels["avb_state"],
                boot_vbmeta,
                "green" if boot_vbmeta == "locked" else "red",
            )
            set_status(
                status_labels["bootloader_locked"],
                "Yes" if boot_flash == "1" else "No",
                "green" if boot_flash == "1" else "red",
            )
            set_status(
                status_labels["dm_verity"],
                verity_mode,
                "green" if verity_mode == "enforcing" else "red",
            )
            set_status(
                status_labels["selinux"],
                selinux_mode,
                "green" if selinux_mode == "Enforcing" else "red",
            )
            set_status(
                status_labels["root_status"],
                root_status,
                "red" if "detected" in root_status else "green",
            )
            set_status(
                status_labels["secure_boot"],
                secure_boot_value,
                "green" if secure_boot_value == "Enabled" else "red",
            )

            append_text_safe(details_text, "=== Boot Verification Details ===")
            append_text_safe(details_text, f"• Boot State: {boot_status}")
            append_text_safe(details_text, f"• Verified Boot: {boot_verified}")
            append_text_safe(details_text, f"• Verified State: {boot_verified_bootstate}")
            append_text_safe(details_text, f"• AVB State: {boot_vbmeta}")
            append_text_safe(details_text, f"• Bootloader Locked: {'Yes' if boot_flash == '1' else 'No'}")
            append_text_safe(details_text, f"• DM-Verity: {verity_mode}")
            append_text_safe(details_text, f"• SELinux: {selinux_mode}")
            append_text_safe(details_text, f"• Root Status: {root_status}")
            append_text_safe(details_text, f"• Secure Boot: {secure_boot_value}\n")

            security_issues = []
            if bootloader_unlocked:
                security_issues.append("• Bootloader is unlocked. This reduces security.")
            if selinux_mode == "Permissive":
                security_issues.append("• SELinux is in Permissive mode. This reduces security.")
            if "detected" in root_status:
                security_issues.append("• Root access detected. This significantly reduces security.")
            if secure_boot_value == "Disabled":
                security_issues.append("• Secure Boot is disabled. This reduces security.")

            if security_issues:
                append_text_safe(details_text, "=== Security Issues ===\n")
                for issue in security_issues:
                    append_text_safe(details_text, issue)
            else:
                append_text_safe(details_text, "✅ No major security issues detected.\n")

            append_text_safe(details_text, "=== Recommendations ===\n")
            if bootloader_unlocked:
                append_text_safe(details_text, "• Consider locking the bootloader if you don't need custom ROMs.")
            if selinux_mode == "Permissive":
                append_text_safe(details_text, "• Set SELinux to Enforcing mode for better security.")
            if "detected" in root_status:
                append_text_safe(details_text, "• Consider unrooting your device for better security.")
            if secure_boot_value == "Disabled":
                append_text_safe(details_text, "• Enable Secure Boot in your device settings if available.")

        except Exception as exc:
            clear_text(details_text)
            append_text_safe(details_text, f"Error updating boot integrity information: {exc}")

    def _check_appops_dialog(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Check AppOps")
        dialog.resize(750, 600)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        main_layout.addWidget(QtWidgets.QLabel("Package Name:"))
        pkg_entry = QtWidgets.QLineEdit()
        main_layout.addWidget(pkg_entry)

        main_layout.addWidget(QtWidgets.QLabel("AppOps Status:"))
        output_text = QtWidgets.QPlainTextEdit()
        output_text.setReadOnly(True)
        main_layout.addWidget(output_text)

        button_layout = QtWidgets.QHBoxLayout()
        check_btn = QtWidgets.QPushButton("Check")
        close_btn = QtWidgets.QPushButton("Close")
        button_layout.addWidget(check_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        def check_appops():
            pkg = pkg_entry.text().strip()
            if not pkg:
                QtWidgets.QMessageBox.critical(
                    dialog, "Error", "Please enter a package name"
                )
                return

            result = self._run_adb_shell(f"appops get {pkg}")
            clear_text(output_text)
            if result[0]:
                append_text_safe(output_text, f"AppOps for {pkg}:")
                append_text_safe(output_text, result[1])
            else:
                append_text_safe(output_text, f"Error: {result[2]}")

        check_btn.clicked.connect(check_appops)
        close_btn.clicked.connect(dialog.close)

        pkg_entry.setFocus()
        dialog.exec()

    def _change_appops_dialog(self):
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Change AppOps Permission")
        dialog.resize(750, 650)
        dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(dialog)

        main_layout.addWidget(QtWidgets.QLabel("Package Name:"))
        pkg_entry = QtWidgets.QLineEdit()
        main_layout.addWidget(pkg_entry)

        main_layout.addWidget(
            QtWidgets.QLabel("Permission (e.g., WAKE_LOCK, GPS, etc.):")
        )
        perm_entry = QtWidgets.QLineEdit()
        main_layout.addWidget(perm_entry)

        main_layout.addWidget(QtWidgets.QLabel("Mode:"))
        mode_group = QtWidgets.QButtonGroup(dialog)
        mode_layout = QtWidgets.QHBoxLayout()
        modes = [("Allow", "allow"), ("Deny", "deny"), ("Ignore", "ignore"), ("Default", "default")]
        for idx, (label, value) in enumerate(modes):
            radio = QtWidgets.QRadioButton(label)
            if idx == 0:
                radio.setChecked(True)
            radio.setProperty("mode_value", value)
            mode_group.addButton(radio)
            mode_layout.addWidget(radio)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        main_layout.addWidget(QtWidgets.QLabel("Command Output:"))
        output_text = QtWidgets.QPlainTextEdit()
        output_text.setReadOnly(True)
        main_layout.addWidget(output_text)

        button_layout = QtWidgets.QHBoxLayout()
        change_btn = QtWidgets.QPushButton("Change Permission")
        close_btn = QtWidgets.QPushButton("Close")
        button_layout.addWidget(change_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        def change_permission():
            pkg = pkg_entry.text().strip()
            perm = perm_entry.text().strip()
            selected_button = mode_group.checkedButton()
            mode = selected_button.property("mode_value") if selected_button else "allow"

            if not pkg or not perm:
                QtWidgets.QMessageBox.critical(
                    dialog, "Error", "Please enter both package name and permission"
                )
                return

            clear_text(output_text)
            append_text_safe(output_text, f"Executing: appops set {pkg} {perm} {mode}\n")

            result = self._run_adb_shell(f"appops set {pkg} {perm} {mode}")
            if result[0]:
                append_text_safe(
                    output_text, f"Successfully set {perm} to {mode} for {pkg}"
                )
            else:
                append_text_safe(output_text, f"Error: {result[2] or result[1]}")

        change_btn.clicked.connect(change_permission)
        close_btn.clicked.connect(dialog.close)

        pkg_entry.setFocus()
        dialog.exec()
