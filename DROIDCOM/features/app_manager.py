"""
DROIDCOM - App Manager Feature Module
Handles app installation, uninstallation, and management.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import os
import threading

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui


class AppManagerMixin:
    """Mixin class providing app management functionality."""

    def install_apk(self):
        """Install an APK on the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        apk_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select APK file to install",
            "",
            "Android Package (*.apk);;All files (*.*)",
        )

        if not apk_path:
            return

        self._run_in_thread(lambda: self._install_apk_task(apk_path))

    def _install_apk_task(self, apk_path):
        """Worker thread to install an APK"""
        try:
            self.update_status(f"Installing {os.path.basename(apk_path)}...")
            self.log_message(f"Installing APK: {apk_path}")

            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    self.update_status("ADB not found")
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            serial = self.device_info.get('serial')
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Installation failed")
                return

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'install', '-r', apk_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            if result.returncode != 0 or 'Failure' in result.stdout:
                self.log_message(f"Failed to install APK: {result.stderr.strip() or result.stdout.strip()}")
                self.update_status("Installation failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Installation Error",
                    f"Failed to install APK:\n{result.stderr.strip() or result.stdout.strip()}",
                )
                return

            self.log_message("APK installed successfully")
            self.update_status("APK installed")
            QtWidgets.QMessageBox.information(
                self,
                "Installation Complete",
                f"{os.path.basename(apk_path)} was installed successfully.",
            )

        except Exception as e:
            self.log_message(f"Error installing APK: {str(e)}")
            self.update_status("Installation failed")
            QtWidgets.QMessageBox.critical(
                self, "Installation Error", f"Failed to install APK: {str(e)}"
            )

    def app_manager(self):
        """Manage apps on the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        self._run_in_thread(self._app_manager_task)

    def _app_manager_task(self):
        """Worker thread to load app list and show app manager"""
        try:
            self.update_status("Loading app list...")
            self.log_message("Loading list of installed applications...")

            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    self.update_status("ADB not found")
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            serial = self.device_info.get('serial')
            if not serial:
                self.log_message("Device serial not found")
                self.update_status("Failed to load app list")
                return

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'list', 'packages', '-3'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20
            )

            if result.returncode != 0:
                self.log_message(f"Failed to get app list: {result.stderr.strip()}")
                self.update_status("Failed to load app list")
                return

            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('package:'):
                    package_name = line[8:].strip()
                    packages.append(package_name)

            packages.sort()

            self.update_status(f"Found {len(packages)} apps")
            self.log_message(f"Found {len(packages)} user-installed applications")

            emit_ui(self, lambda: self._show_app_manager(packages, serial, adb_cmd))

        except Exception as e:
            self.log_message(f"Error loading app list: {str(e)}")
            self.update_status("Failed to load app list")

    def _show_app_manager(self, packages, serial, adb_cmd):
        """Show the app manager window"""
        try:
            app_window = QtWidgets.QDialog(self)
            app_window.setWindowTitle("Android App Manager")
            app_window.resize(500, 600)
            app_window.setMinimumSize(400, 400)

            main_layout = QtWidgets.QVBoxLayout(app_window)
            title = QtWidgets.QLabel(f"Installed Apps ({len(packages)})")
            title.setStyleSheet("font-weight: bold;")
            main_layout.addWidget(title)

            search_layout = QtWidgets.QHBoxLayout()
            search_layout.addWidget(QtWidgets.QLabel("Search:"))
            search_entry = QtWidgets.QLineEdit()
            search_layout.addWidget(search_entry)
            main_layout.addLayout(search_layout)

            app_listbox = QtWidgets.QListWidget()
            for package in packages:
                app_listbox.addItem(package)
            main_layout.addWidget(app_listbox)

            def filter_apps(text):
                self._filter_app_list(text, packages, app_listbox)

            search_entry.textChanged.connect(filter_apps)

            buttons_layout = QtWidgets.QHBoxLayout()
            uninstall_btn = QtWidgets.QPushButton("Uninstall")
            uninstall_btn.clicked.connect(
                lambda: self._uninstall_app(app_listbox, packages, serial, adb_cmd, app_window)
            )
            clear_btn = QtWidgets.QPushButton("Clear Data")
            clear_btn.clicked.connect(
                lambda: self._clear_app_data(app_listbox, packages, serial, adb_cmd)
            )
            force_btn = QtWidgets.QPushButton("Force Stop")
            force_btn.clicked.connect(
                lambda: self._force_stop_app(app_listbox, packages, serial, adb_cmd)
            )
            perm_btn = QtWidgets.QPushButton("Permissions")
            perm_btn.clicked.connect(
                lambda: self._view_app_permissions(app_listbox, packages, serial, adb_cmd)
            )
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(app_window.close)
            buttons_layout.addWidget(uninstall_btn)
            buttons_layout.addWidget(clear_btn)
            buttons_layout.addWidget(force_btn)
            buttons_layout.addWidget(perm_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            main_layout.addLayout(buttons_layout)

            app_window.show()

        except Exception as e:
            self.log_message(f"Error showing app manager: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "App Manager Error", f"Failed to show app manager: {str(e)}"
            )

    def _view_app_permissions(self, listbox, packages, serial, adb_cmd):
        """View permissions for the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to view permissions."
            )
            return

        package_name = selection[0].text()

        # Create permissions window
        perm_window = QtWidgets.QDialog(self)
        perm_window.setWindowTitle(f"Permissions - {package_name}")
        perm_window.resize(500, 400)

        main_layout = QtWidgets.QVBoxLayout(perm_window)
        main_layout.addWidget(QtWidgets.QLabel("Loading permissions..."))

        text_widget = QtWidgets.QPlainTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        main_layout.addWidget(text_widget)

        status_label = QtWidgets.QLabel("Loading...")
        main_layout.addWidget(status_label)

        def load_permissions():
            try:
                result = subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'dumpsys', 'package', package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    permissions = []
                    in_permissions = False
                    for line in result.stdout.split('\n'):
                        if 'requested permissions:' in line.lower() or 'install permissions:' in line.lower():
                            in_permissions = True
                            continue
                        if in_permissions:
                            if line.strip().startswith('android.permission'):
                                permissions.append(line.strip())
                            elif line.strip() and not line.startswith(' '):
                                in_permissions = False

                    emit_ui(self, lambda: self._display_permissions(
                        text_widget, status_label, package_name, permissions
                    ))
                else:
                    emit_ui(self, lambda: self._show_permission_error(status_label, result.stderr))

            except Exception as e:
                emit_ui(self, lambda: self._show_permission_error(status_label, str(e)))

        threading.Thread(target=load_permissions, daemon=True).start()
        perm_window.show()

    def _display_permissions(self, text_widget, status_label, package_name, permissions):
        """Display permissions in the text widget"""
        text_widget.clear()
        text_widget.appendPlainText(f"Permissions for {package_name}:\n")

        if permissions:
            for perm in permissions:
                text_widget.appendPlainText(f"  • {perm}")
            status_label.setText(f"Found {len(permissions)} permissions")
        else:
            text_widget.appendPlainText("No permissions found or unable to retrieve permissions.")
            status_label.setText("No permissions found")

    def _show_permission_error(self, status_label, error_msg):
        """Show error message for permission retrieval"""
        status_label.setText(f"Error: {error_msg}")

    def _uninstall_app(self, listbox, packages, serial, adb_cmd, parent_window):
        """Uninstall the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to uninstall."
            )
            return

        package_name = selection[0].text()

        confirm = (
            QtWidgets.QMessageBox.question(
                self,
                "Confirm Uninstall",
                f"Are you sure you want to uninstall {package_name}?\n\nThis action cannot be undone.",
            )
            == QtWidgets.QMessageBox.Yes
        )

        if not confirm:
            return

        try:
            self.log_message(f"Uninstalling {package_name}...")
            self.update_status(f"Uninstalling {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'uninstall', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and 'Success' in result.stdout:
                self.log_message(f"{package_name} uninstalled successfully")
                self.update_status("App uninstalled")
                QtWidgets.QMessageBox.information(
                    self,
                    "Uninstall Complete",
                    f"{package_name} was uninstalled successfully.",
                )

                # Remove from list
                listbox.takeItem(listbox.row(selection[0]))
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to uninstall {package_name}: {error_msg}")
                self.update_status("Uninstall failed")
                QtWidgets.QMessageBox.critical(
                    self, "Uninstall Error", f"Failed to uninstall {package_name}:\n{error_msg}"
                )

        except Exception as e:
            self.log_message(f"Error uninstalling app: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Uninstall Error", f"Failed to uninstall app: {str(e)}"
            )

    def _clear_app_data(self, listbox, packages, serial, adb_cmd):
        """Clear data for the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to clear data."
            )
            return

        package_name = selection[0].text()

        confirm = (
            QtWidgets.QMessageBox.question(
                self,
                "Confirm Clear Data",
                f"Are you sure you want to clear all data for {package_name}?\n\n"
                "This will delete all app settings, accounts, and cached data.",
            )
            == QtWidgets.QMessageBox.Yes
        )

        if not confirm:
            return

        try:
            self.log_message(f"Clearing data for {package_name}...")
            self.update_status(f"Clearing data for {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'clear', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and 'Success' in result.stdout:
                self.log_message(f"Data cleared for {package_name}")
                self.update_status("App data cleared")
                QtWidgets.QMessageBox.information(
                    self,
                    "Clear Data Complete",
                    f"Data for {package_name} was cleared successfully.",
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to clear data for {package_name}: {error_msg}")
                self.update_status("Clear data failed")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Clear Data Error",
                    f"Failed to clear data for {package_name}:\n{error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error clearing app data: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Clear Data Error", f"Failed to clear app data: {str(e)}"
            )

    def _force_stop_app(self, listbox, packages, serial, adb_cmd):
        """Force stop the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to force stop."
            )
            return

        package_name = selection[0].text()

        try:
            self.log_message(f"Force stopping {package_name}...")
            self.update_status(f"Force stopping {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'am', 'force-stop', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.log_message(f"{package_name} force stopped")
                self.update_status("App force stopped")
                QtWidgets.QMessageBox.information(
                    self,
                    "Force Stop Complete",
                    f"{package_name} was force stopped successfully.",
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to force stop {package_name}: {error_msg}")
                self.update_status("Force stop failed")

        except Exception as e:
            self.log_message(f"Error force stopping app: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Force Stop Error", f"Failed to force stop app: {str(e)}"
            )

    def _toggle_app_freeze(self, listbox, packages, serial, adb_cmd):
        """Toggle freeze/unfreeze for the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to freeze/unfreeze."
            )
            return

        package_name = selection[0].text()

        try:
            # Check if app is currently disabled
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'list', 'packages', '-d'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            is_disabled = package_name in result.stdout

            if is_disabled:
                # Enable the app
                action = "enable"
                action_msg = "unfreezing"
            else:
                # Disable the app
                action = "disable-user"
                action_msg = "freezing"

            self.log_message(f"{action_msg.capitalize()} {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', action, '--user', '0', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                status = "frozen" if action == "disable-user" else "unfrozen"
                self.log_message(f"{package_name} has been {status}")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"{package_name} has been {status}."
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to {action_msg} {package_name}: {error_msg}")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to {action_msg} {package_name}:\n{error_msg}",
                )

        except Exception as e:
            self.log_message(f"Error toggling app freeze: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to toggle app freeze: {str(e)}"
            )

    def _extract_apk(self, listbox, packages, serial, adb_cmd):
        """Extract APK for the selected app"""
        selection = listbox.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No App Selected", "Please select an app to extract APK."
            )
            return

        package_name = selection[0].text()

        # Ask where to save
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save APK As",
            f"{package_name}.apk",
            "Android Package (*.apk)",
        )

        if not save_path:
            return

        try:
            self.log_message(f"Extracting APK for {package_name}...")
            self.update_status(f"Extracting {package_name}...")

            # Get APK path
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'path', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to find APK path: {result.stderr}"
                )
                return

            apk_path = result.stdout.strip().replace('package:', '')

            # Pull APK
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'pull', apk_path, save_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.log_message(f"APK extracted to {save_path}")
                self.update_status("APK extracted")
                QtWidgets.QMessageBox.information(
                    self, "Success", f"APK extracted to:\n{save_path}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to extract APK: {result.stderr}"
                )

        except Exception as e:
            self.log_message(f"Error extracting APK: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to extract APK: {str(e)}"
            )

    def _filter_app_list(self, search_text, packages, listbox):
        """Filter the app list based on search text"""
        listbox.clear()
        search_lower = search_text.lower()
        for package in packages:
            if search_lower in package.lower():
                listbox.addItem(package)
