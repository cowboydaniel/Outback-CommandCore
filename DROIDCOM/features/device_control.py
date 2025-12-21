"""
DROIDCOM - Device Control Feature Module
Handles device control operations like reboot, toggles, etc.
"""

from ..ui.qt_compat import tk
from ..ui.qt_compat import ttk, messagebox
import subprocess
import logging

from ..constants import IS_WINDOWS


class DeviceControlMixin:
    """Mixin class providing device control functionality."""

    def _reboot_device_normal(self):
        """Reboot device normally"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            self.update_status("Rebooting device...")
            self.log_message("Rebooting device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'

            serial = self.device_info.get('serial')
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Reboot failed")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'reboot'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot initiated.")
                self.update_status("Device rebooting")
                self.device_connected = False
                self.disable_device_actions()
                messagebox.showinfo("Reboot Initiated", "The device has been instructed to reboot.")
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot failed: {error_msg}")
                self.update_status("Reboot failed")
                messagebox.showerror("Reboot Failed", f"Failed to reboot the device: {error_msg}")

        except Exception as e:
            self.log_message(f"Error during reboot: {str(e)}")
            self.update_status("Reboot error")
            messagebox.showerror("Reboot Error", f"An error occurred: {str(e)}")

    def _reboot_device_recovery(self):
        """Reboot device to recovery mode"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Reboot to Recovery",
            "Are you sure you want to reboot the device to recovery mode?"
        )

        if not confirm:
            return

        try:
            self.update_status("Rebooting to recovery...")
            self.log_message("Rebooting device to recovery mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'reboot', 'recovery'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot to recovery initiated.")
                self.update_status("Device rebooting to recovery")
                self.device_connected = False
                self.disable_device_actions()
                messagebox.showinfo("Reboot Initiated", "The device is rebooting into recovery mode.")
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to recovery failed: {error_msg}")
                messagebox.showerror("Reboot Failed", f"Failed to reboot to recovery: {error_msg}")

        except Exception as e:
            self.log_message(f"Error during reboot to recovery: {str(e)}")
            messagebox.showerror("Reboot Error", f"An error occurred: {str(e)}")

    def _reboot_device_bootloader(self):
        """Reboot device to bootloader/fastboot mode"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Reboot to Bootloader",
            "Are you sure you want to reboot the device to bootloader mode?"
        )

        if not confirm:
            return

        try:
            self.update_status("Rebooting to bootloader...")
            self.log_message("Rebooting device to bootloader mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'reboot', 'bootloader'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot to bootloader initiated.")
                self.update_status("Device rebooting to bootloader")
                self.device_connected = False
                self.disable_device_actions()
                messagebox.showinfo("Reboot Initiated", "The device is rebooting into bootloader mode.")
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to bootloader failed: {error_msg}")
                messagebox.showerror("Reboot Failed", f"Failed to reboot to bootloader: {error_msg}")

        except Exception as e:
            self.log_message(f"Error during reboot to bootloader: {str(e)}")
            messagebox.showerror("Reboot Error", f"An error occurred: {str(e)}")

    def _reboot_device_edl(self):
        """Reboot device to EDL (Emergency Download) mode"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Reboot to EDL",
            "WARNING: Rebooting to EDL mode is an advanced operation.\n\nAre you sure you want to continue?"
        )

        if not confirm:
            return

        try:
            self.update_status("Rebooting to EDL mode...")
            self.log_message("Rebooting device to EDL mode...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'reboot', 'edl'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if cmd.returncode == 0:
                self.log_message("Device reboot to EDL mode initiated.")
                self.update_status("Device rebooting to EDL mode")
                self.device_connected = False
                self.disable_device_actions()
                messagebox.showinfo("EDL Mode Initiated", "The device is rebooting into EDL mode.")
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Reboot to EDL failed: {error_msg}")
                messagebox.showerror("EDL Reboot Failed", f"Failed to reboot to EDL mode: {error_msg}")

        except Exception as e:
            self.log_message(f"Error during EDL reboot: {str(e)}")
            messagebox.showerror("EDL Reboot Error", f"An error occurred: {str(e)}")

    def _toggle_mobile_data(self):
        """Toggle mobile data on/off on the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            self.update_status("Toggling mobile data...")
            self.log_message("Toggling mobile data state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            # Check current state
            get_state_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'get', 'global', 'mobile_data'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            current_state = get_state_cmd.stdout.strip()
            new_state = '0' if current_state == '1' else '1'

            cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'put', 'global', 'mobile_data', new_state],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if cmd.returncode == 0:
                state_text = "enabled" if new_state == '1' else "disabled"
                self.log_message(f"Mobile data {state_text}")
                self.update_status(f"Mobile data {state_text}")
                messagebox.showinfo("Success", f"Mobile data has been {state_text}.")
            else:
                error_msg = cmd.stderr.strip() or "Unknown error"
                self.log_message(f"Failed to toggle mobile data: {error_msg}")
                messagebox.showerror("Error", f"Failed to toggle mobile data: {error_msg}")

        except Exception as e:
            self.log_message(f"Error toggling mobile data: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _toggle_wifi(self):
        """Toggle WiFi on/off on the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            self.update_status("Toggling WiFi...")
            self.log_message("Toggling WiFi state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            # Check current state
            get_state_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'get', 'global', 'wifi_on'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if get_state_cmd.returncode == 0:
                current_state = get_state_cmd.stdout.strip()
                new_state = '0' if current_state == '1' else '1'
                action = 'disable' if new_state == '0' else 'enable'

                toggle_cmd = subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'svc', 'wifi', action],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )

                if toggle_cmd.returncode == 0:
                    state_text = "enabled" if new_state == '1' else "disabled"
                    self.log_message(f"WiFi {state_text}")
                    self.update_status(f"WiFi {state_text}")
                    messagebox.showinfo("Success", f"WiFi has been {state_text}.")
                else:
                    error_msg = toggle_cmd.stderr.strip() or "Unknown error"
                    self.log_message(f"Failed to toggle WiFi: {error_msg}")
                    messagebox.showerror("Error", f"Failed to toggle WiFi: {error_msg}")

        except Exception as e:
            self.log_message(f"Error toggling WiFi: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _toggle_bluetooth(self):
        """Toggle Bluetooth on/off on the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            self.update_status("Toggling Bluetooth...")
            self.log_message("Toggling Bluetooth state on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            # Check current state
            get_state_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'get', 'global', 'bluetooth_on'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if get_state_cmd.returncode == 0:
                current_state = get_state_cmd.stdout.strip()
                new_state = '0' if current_state == '1' else '1'
                action = 'disable' if new_state == '0' else 'enable'

                toggle_cmd = subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'svc', 'bluetooth', action],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )

                if toggle_cmd.returncode == 0:
                    state_text = "enabled" if new_state == '1' else "disabled"
                    self.log_message(f"Bluetooth {state_text}")
                    self.update_status(f"Bluetooth {state_text}")
                    messagebox.showinfo("Success", f"Bluetooth has been {state_text}.")
                else:
                    error_msg = toggle_cmd.stderr.strip() or "Unknown error"
                    self.log_message(f"Failed to toggle Bluetooth: {error_msg}")
                    messagebox.showerror("Error", f"Failed to toggle Bluetooth: {error_msg}")

        except Exception as e:
            self.log_message(f"Error toggling Bluetooth: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _toggle_airplane_mode(self):
        """Toggle Airplane mode on/off on the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            self.update_status("Toggling Airplane mode...")
            self.log_message("Toggling Airplane mode on device...")

            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                self.log_message("Device serial not found")
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            # Check current state
            get_state_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'get', 'global', 'airplane_mode_on'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            current_state = get_state_cmd.stdout.strip()
            new_state = '0' if current_state == '1' else '1'

            # Set airplane mode
            subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'settings', 'put', 'global', 'airplane_mode_on', new_state],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            # Broadcast the change
            subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'am', 'broadcast', '-a',
                 'android.intent.action.AIRPLANE_MODE', '--ez', 'state', 'true' if new_state == '1' else 'false'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            state_text = "enabled" if new_state == '1' else "disabled"
            self.log_message(f"Airplane mode {state_text}")
            self.update_status(f"Airplane mode {state_text}")
            messagebox.showinfo("Success", f"Airplane mode has been {state_text}.")

        except Exception as e:
            self.log_message(f"Error toggling Airplane mode: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _simulate_power_button(self):
        """Simulate pressing the power button"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
            serial = self.device_info.get('serial')

            if not serial:
                return

            if isinstance(serial, str) and '\n' in serial:
                serial = serial.split('\n')[0].strip()

            subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_POWER'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            self.log_message("Power button simulated")
            self.update_status("Power button pressed")

        except Exception as e:
            self.log_message(f"Error simulating power button: {str(e)}")

    def _toggle_screen(self):
        """Toggle screen on/off"""
        self._simulate_power_button()

    def _set_brightness_dialog(self):
        """Show dialog to set screen brightness"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Set Brightness")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        x_pos = (self.winfo_screenwidth() - 300) // 2
        y_pos = (self.winfo_screenheight() - 150) // 2
        dialog.geometry(f"+{x_pos}+{y_pos}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Brightness Level:").pack(pady=(0, 10))

        brightness_var = tk.IntVar(value=128)
        brightness_scale = ttk.Scale(
            main_frame, from_=0, to=255,
            variable=brightness_var, orient="horizontal"
        )
        brightness_scale.pack(fill="x", pady=5)

        value_label = ttk.Label(main_frame, text="128")
        value_label.pack()

        def update_value(val):
            value_label.config(text=str(int(float(val))))

        brightness_scale.config(command=update_value)

        def apply_brightness():
            try:
                value = brightness_var.get()
                adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
                serial = self.device_info.get('serial')

                if isinstance(serial, str) and '\n' in serial:
                    serial = serial.split('\n')[0].strip()

                # Set manual brightness mode
                subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'settings', 'put', 'system', 'screen_brightness_mode', '0'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
                )

                # Set brightness
                subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'settings', 'put', 'system', 'screen_brightness', str(value)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
                )

                self.log_message(f"Brightness set to {value}")
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to set brightness: {str(e)}")

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons_frame, text="Apply", command=apply_brightness).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

    def _set_screen_timeout_dialog(self):
        """Show dialog to set screen timeout"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Set Screen Timeout")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()

        x_pos = (self.winfo_screenwidth() - 300) // 2
        y_pos = (self.winfo_screenheight() - 200) // 2
        dialog.geometry(f"+{x_pos}+{y_pos}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Screen Timeout:").pack(pady=(0, 10))

        timeouts = [
            ("15 seconds", 15000),
            ("30 seconds", 30000),
            ("1 minute", 60000),
            ("2 minutes", 120000),
            ("5 minutes", 300000),
            ("10 minutes", 600000),
            ("30 minutes", 1800000),
            ("Never", 2147483647)
        ]

        timeout_var = tk.StringVar(value="30 seconds")

        for text, value in timeouts:
            ttk.Radiobutton(main_frame, text=text, value=text, variable=timeout_var).pack(anchor="w")

        def apply_timeout():
            try:
                selected = timeout_var.get()
                timeout_ms = next(v for t, v in timeouts if t == selected)

                adb_cmd = self.adb_path if IS_WINDOWS and hasattr(self, 'adb_path') else 'adb'
                serial = self.device_info.get('serial')

                if isinstance(serial, str) and '\n' in serial:
                    serial = serial.split('\n')[0].strip()

                subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'settings', 'put', 'system', 'screen_off_timeout', str(timeout_ms)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
                )

                self.log_message(f"Screen timeout set to {selected}")
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to set screen timeout: {str(e)}")

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons_frame, text="Apply", command=apply_timeout).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
