"""
DROIDCOM - System Tools Feature Module
PySide6 migration stubs for system tools dialogs.
"""

from PySide6 import QtWidgets


class SystemToolsMixin:
    """Mixin class providing system tools functionality."""

    def _show_battery_stats(self):
        QtWidgets.QMessageBox.information(
            self,
            "Battery Stats",
            "Battery stats UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_battery_stats(self, status_widget, history_widget, usage_widget, serial, adb_cmd):
        return

    def _show_memory_usage(self):
        QtWidgets.QMessageBox.information(
            self,
            "Memory Usage",
            "Memory usage UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_memory_stats(self, text_widget, serial, adb_cmd):
        return

    def _show_cpu_usage(self):
        QtWidgets.QMessageBox.information(
            self,
            "CPU Usage",
            "CPU usage UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_cpu_stats(self, text_widget, serial, adb_cmd, sort_by="cpu"):
        return

    def _show_network_stats(self):
        QtWidgets.QMessageBox.information(
            self,
            "Network Stats",
            "Network stats UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_network_stats(self, ifaces_text, conn_text, usage_text, serial, adb_cmd):
        return

    def _show_thermal_stats(self):
        QtWidgets.QMessageBox.information(
            self,
            "Thermal Stats",
            "Thermal stats UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _show_storage_info(self):
        QtWidgets.QMessageBox.information(
            self,
            "Storage Info",
            "Storage info UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_storage_info(self, text_widget, serial, adb_cmd):
        return

    def _show_running_services(self):
        QtWidgets.QMessageBox.information(
            self,
            "Running Services",
            "Running services UI is being migrated to PySide6 and will be restored shortly.",
        )

    def _refresh_running_services(self, tree_widget, filter_text=""):
        return

    def _show_detailed_device_info(self):
        QtWidgets.QMessageBox.information(
            self,
            "Device Info",
            "Detailed device info UI is being migrated to PySide6 and will be restored shortly.",
        )
