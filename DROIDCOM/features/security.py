"""
DROIDCOM - Security Feature Module
PySide6 migration stubs for security dialogs.
"""

from PySide6 import QtWidgets


class SecurityMixin:
    """Mixin class providing security functionality."""

    def _check_root_status(self):
        QtWidgets.QMessageBox.information(
            self, "Root Status", "Root status UI is being migrated to PySide6."
        )

    def _check_encryption_status(self):
        QtWidgets.QMessageBox.information(
            self, "Encryption Status", "Encryption status UI is being migrated to PySide6."
        )

    def _check_lock_screen_status(self):
        QtWidgets.QMessageBox.information(
            self, "Lock Screen Status", "Lock screen status UI is being migrated to PySide6."
        )

    def run_screen_lock_brute_forcer(self):
        QtWidgets.QMessageBox.information(
            self,
            "Screen Lock Brute Forcer",
            "Screen lock brute forcer UI is being migrated to PySide6.",
        )

    def _run_screen_lock_brute_force(
        self, lock_type, pin_length, start_value, delay_ms, log_callback, should_continue, on_complete
    ):
        return

    def _detect_lock_screen_type(self, serial):
        return "Unknown"

    def _check_security_patch_level(self):
        QtWidgets.QMessageBox.information(
            self, "Security Patch Level", "Security patch UI is being migrated to PySide6."
        )

    def _scan_dangerous_permissions(self):
        QtWidgets.QMessageBox.information(
            self, "Permission Scan", "Permission scan UI is being migrated to PySide6."
        )

    def _start_permission_scan(
        self, dialog, tree, details_text, status_label, progress_var, scan_btn
    ):
        return

    def _check_certificates(self):
        QtWidgets.QMessageBox.information(
            self, "Certificates", "Certificate checks UI is being migrated to PySide6."
        )

    def _verify_boot_integrity(self):
        QtWidgets.QMessageBox.information(
            self, "Boot Integrity", "Boot integrity UI is being migrated to PySide6."
        )

    def _check_appops_dialog(self):
        QtWidgets.QMessageBox.information(
            self, "AppOps", "AppOps UI is being migrated to PySide6."
        )

    def _change_appops_dialog(self):
        QtWidgets.QMessageBox.information(
            self, "AppOps", "AppOps editor UI is being migrated to PySide6."
        )
