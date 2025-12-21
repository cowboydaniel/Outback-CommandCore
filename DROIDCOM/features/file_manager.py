"""
DROIDCOM - File Manager Feature Module
PySide6 migration stubs for file manager dialogs.
"""

from PySide6 import QtWidgets


class FileManagerMixin:
    """Mixin class providing file management functionality."""

    def manage_files(self):
        QtWidgets.QMessageBox.information(
            self, "File Manager", "File manager UI is being migrated to PySide6."
        )

    def _refresh_local_files(self, tree):
        return

    def _refresh_android_files(self, tree):
        return

    def _on_local_double_click(self, event, tree):
        return

    def _on_android_double_click(self, event, tree):
        return

    def _upload_to_device(self, local_tree, android_tree):
        return

    def _upload_file_task(self, source_path, target_path, is_directory, tree):
        return

    def _download_from_device(self, android_tree, local_tree):
        return

    def _download_file_task(self, source_path, target_path, is_directory, tree):
        return

    def _format_size(self, size_bytes):
        return "0 B"

    def _pull_from_device(self):
        QtWidgets.QMessageBox.information(
            self, "Pull Files", "File pull UI is being migrated to PySide6."
        )

    def _push_to_device(self):
        QtWidgets.QMessageBox.information(
            self, "Push Files", "File push UI is being migrated to PySide6."
        )
