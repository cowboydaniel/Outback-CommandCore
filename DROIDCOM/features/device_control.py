"""
DROIDCOM - Device Control Feature Module
PySide6 migration stubs for device control dialogs.
"""

from PySide6 import QtWidgets


class DeviceControlMixin:
    """Mixin class providing device control functionality."""

    def _reboot_device_normal(self):
        QtWidgets.QMessageBox.information(
            self, "Reboot", "Reboot controls are being migrated to PySide6."
        )

    def _reboot_device_recovery(self):
        QtWidgets.QMessageBox.information(
            self, "Reboot Recovery", "Reboot controls are being migrated to PySide6."
        )

    def _reboot_device_bootloader(self):
        QtWidgets.QMessageBox.information(
            self, "Reboot Bootloader", "Reboot controls are being migrated to PySide6."
        )

    def _reboot_device_edl(self):
        QtWidgets.QMessageBox.information(
            self, "Reboot EDL", "Reboot controls are being migrated to PySide6."
        )

    def _toggle_mobile_data(self):
        QtWidgets.QMessageBox.information(
            self, "Mobile Data", "Device control UI is being migrated to PySide6."
        )

    def _toggle_wifi(self):
        QtWidgets.QMessageBox.information(
            self, "Wi-Fi", "Device control UI is being migrated to PySide6."
        )

    def _toggle_bluetooth(self):
        QtWidgets.QMessageBox.information(
            self, "Bluetooth", "Device control UI is being migrated to PySide6."
        )

    def _toggle_airplane_mode(self):
        QtWidgets.QMessageBox.information(
            self, "Airplane Mode", "Device control UI is being migrated to PySide6."
        )

    def _simulate_power_button(self):
        QtWidgets.QMessageBox.information(
            self, "Power Button", "Device control UI is being migrated to PySide6."
        )

    def _toggle_screen(self):
        QtWidgets.QMessageBox.information(
            self, "Screen Toggle", "Device control UI is being migrated to PySide6."
        )

    def _set_brightness_dialog(self):
        QtWidgets.QMessageBox.information(
            self, "Brightness", "Screen controls are being migrated to PySide6."
        )

    def _set_screen_timeout_dialog(self):
        QtWidgets.QMessageBox.information(
            self, "Screen Timeout", "Screen controls are being migrated to PySide6."
        )
