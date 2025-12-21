"""
DROIDCOM - File Manager Feature Module
Handles file management dialogs in PySide6.
"""

from PySide6 import QtWidgets, QtCore
import os
import subprocess
import time

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui


class FileManagerMixin:
    """Mixin class providing file management functionality."""

    def manage_files(self):
        """Manage files on the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        file_manager = QtWidgets.QDialog(self)
        file_manager.setWindowTitle("Android File Manager")
        file_manager.resize(950, 600)
        file_manager.setMinimumSize(800, 500)

        self.android_path = "/sdcard"
        self.local_path = os.path.expanduser("~")

        main_layout = QtWidgets.QVBoxLayout(file_manager)

        device_frame = QtWidgets.QWidget()
        device_layout = QtWidgets.QHBoxLayout(device_frame)
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.addWidget(
            QtWidgets.QLabel(
                f"Device: {self.device_info.get('model')} ({self.device_info.get('serial')})"
            )
        )
        self.fm_status_label = QtWidgets.QLabel("Ready")
        device_layout.addStretch()
        device_layout.addWidget(self.fm_status_label)
        main_layout.addWidget(device_frame)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(splitter)

        local_group = QtWidgets.QGroupBox("Local Files")
        local_layout = QtWidgets.QVBoxLayout(local_group)

        local_nav = QtWidgets.QHBoxLayout()
        local_nav.addWidget(QtWidgets.QLabel("Location:"))
        self.local_path_entry = QtWidgets.QLineEdit(self.local_path)
        local_nav.addWidget(self.local_path_entry, 1)

        go_btn = QtWidgets.QPushButton("Go")
        go_btn.clicked.connect(lambda: self._refresh_local_files(local_files_tree))
        local_nav.addWidget(go_btn)

        home_btn = QtWidgets.QPushButton("Home")
        home_btn.clicked.connect(lambda: self._go_home_directory(local_files_tree))
        local_nav.addWidget(home_btn)

        up_btn = QtWidgets.QPushButton("Up")
        up_btn.clicked.connect(
            lambda: self._go_up_directory(self.local_path_entry, local_files_tree, os.path.sep)
        )
        local_nav.addWidget(up_btn)

        local_layout.addLayout(local_nav)

        local_files_tree = QtWidgets.QTreeWidget()
        local_files_tree.setColumnCount(3)
        local_files_tree.setHeaderLabels(["Name", "Size", "Date Modified"])
        local_files_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        local_files_tree.itemDoubleClicked.connect(
            lambda item, column: self._on_local_double_click(item, local_files_tree)
        )
        local_layout.addWidget(local_files_tree)

        local_btn_frame = QtWidgets.QHBoxLayout()
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: self._refresh_local_files(local_files_tree))
        local_btn_frame.addWidget(refresh_btn)

        upload_btn = QtWidgets.QPushButton("Upload to Device")
        upload_btn.clicked.connect(
            lambda: self._upload_to_device(local_files_tree, android_files_tree)
        )
        local_btn_frame.addWidget(upload_btn)
        local_btn_frame.addStretch()
        local_layout.addLayout(local_btn_frame)

        android_group = QtWidgets.QGroupBox("Android Device Files")
        android_layout = QtWidgets.QVBoxLayout(android_group)

        android_nav = QtWidgets.QHBoxLayout()
        android_nav.addWidget(QtWidgets.QLabel("Location:"))
        self.android_path_entry = QtWidgets.QLineEdit(self.android_path)
        android_nav.addWidget(self.android_path_entry, 1)

        android_go_btn = QtWidgets.QPushButton("Go")
        android_go_btn.clicked.connect(lambda: self._refresh_android_files(android_files_tree))
        android_nav.addWidget(android_go_btn)

        locations = [
            "/sdcard",
            "/sdcard/DCIM",
            "/sdcard/Download",
            "/sdcard/Pictures",
            "/sdcard/Movies",
            "/sdcard/Music",
            "/sdcard/Documents",
        ]
        location_dropdown = QtWidgets.QComboBox()
        location_dropdown.addItems(locations)
        location_dropdown.currentTextChanged.connect(
            lambda value: self._set_android_path(value, android_files_tree)
        )
        android_nav.addWidget(location_dropdown)

        android_up_btn = QtWidgets.QPushButton("Up")
        android_up_btn.clicked.connect(
            lambda: self._go_up_directory(self.android_path_entry, android_files_tree, "/")
        )
        android_nav.addWidget(android_up_btn)

        android_layout.addLayout(android_nav)

        android_files_tree = QtWidgets.QTreeWidget()
        android_files_tree.setColumnCount(3)
        android_files_tree.setHeaderLabels(["Name", "Size", "Date Modified"])
        android_files_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        android_files_tree.itemDoubleClicked.connect(
            lambda item, column: self._on_android_double_click(item, android_files_tree)
        )
        android_layout.addWidget(android_files_tree)

        android_btn_frame = QtWidgets.QHBoxLayout()
        android_refresh_btn = QtWidgets.QPushButton("Refresh")
        android_refresh_btn.clicked.connect(lambda: self._refresh_android_files(android_files_tree))
        android_btn_frame.addWidget(android_refresh_btn)

        download_btn = QtWidgets.QPushButton("Download to PC")
        download_btn.clicked.connect(
            lambda: self._download_from_device(android_files_tree, local_files_tree)
        )
        android_btn_frame.addWidget(download_btn)
        android_btn_frame.addStretch()
        android_layout.addLayout(android_btn_frame)

        splitter.addWidget(local_group)
        splitter.addWidget(android_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self._refresh_local_files(local_files_tree)
        self._refresh_android_files(android_files_tree)

        file_manager.exec()

    def _go_home_directory(self, tree):
        self.local_path_entry.setText(os.path.expanduser("~"))
        self._refresh_local_files(tree)

    def _refresh_local_files(self, tree):
        """Refresh the local files tree"""
        tree.clear()

        current_path = self.local_path_entry.text()

        if not os.path.exists(current_path):
            QtWidgets.QMessageBox.critical(
                self, "Invalid Path", f"The path {current_path} does not exist."
            )
            self.local_path_entry.setText(os.path.expanduser("~"))
            current_path = self.local_path_entry.text()

        try:
            parent_item = QtWidgets.QTreeWidgetItem(["..", "<DIR>", ""])
            parent_item.setData(0, QtCore.Qt.UserRole, "dir")
            tree.addTopLevelItem(parent_item)

            dirs = []
            files = []

            for item in os.listdir(current_path):
                full_path = os.path.join(current_path, item)

                try:
                    stats = os.stat(full_path)
                    size = stats.st_size
                    modified = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(stats.st_mtime)
                    )

                    if os.path.isdir(full_path):
                        dirs.append((item, "<DIR>", modified))
                    else:
                        size_str = self._format_size(size)
                        files.append((item, size_str, modified))
                except Exception:
                    continue

            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())

            for name, size, date in dirs:
                item = QtWidgets.QTreeWidgetItem([name, size, date])
                item.setData(0, QtCore.Qt.UserRole, "dir")
                tree.addTopLevelItem(item)

            for name, size, date in files:
                item = QtWidgets.QTreeWidgetItem([name, size, date])
                item.setData(0, QtCore.Qt.UserRole, "file")
                tree.addTopLevelItem(item)

            self._set_file_manager_status(f"Local: {len(dirs)} dirs, {len(files)} files")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error reading directory: {str(e)}")

    def _refresh_android_files(self, tree):
        """Refresh the Android files tree"""
        tree.clear()

        try:
            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    self.update_status("ADB not found")
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = "adb"

            serial = self.device_info.get("serial")
            if not serial:
                self.log_message("Device serial not found")
                return

            current_path = self.android_path_entry.text()

            parent_item = QtWidgets.QTreeWidgetItem(["..", "<DIR>", ""])
            parent_item.setData(0, QtCore.Qt.UserRole, "dir")
            tree.addTopLevelItem(parent_item)

            dirs = []
            files = []

            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", f"ls -la {current_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                self.log_message(f"Error listing files: {result.stderr.strip()}")
                self._set_file_manager_status("Error listing files")
                return

            lines = result.stdout.strip().split("\n")
            if lines and lines[0].startswith("total"):
                lines = lines[1:]

            for line in lines:
                parts = line.split()
                if len(parts) >= 8:
                    perms = parts[0]
                    if len(parts) > 8:
                        name = " ".join(parts[8:])
                    else:
                        name = parts[8]

                    if name in {".", ".."}:
                        continue

                    size = parts[4]
                    date = " ".join(parts[5:8])

                    if perms.startswith("d"):
                        dirs.append((name, "<DIR>", date))
                    else:
                        size_str = self._format_size(int(size))
                        files.append((name, size_str, date))

            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())

            for name, size, date in dirs:
                item = QtWidgets.QTreeWidgetItem([name, size, date])
                item.setData(0, QtCore.Qt.UserRole, "dir")
                tree.addTopLevelItem(item)

            for name, size, date in files:
                item = QtWidgets.QTreeWidgetItem([name, size, date])
                item.setData(0, QtCore.Qt.UserRole, "file")
                tree.addTopLevelItem(item)

            self._set_file_manager_status(f"Android: {len(dirs)} dirs, {len(files)} files")

        except Exception as e:
            self.log_message(f"Error refreshing Android files: {str(e)}")
            self._set_file_manager_status("Error listing files")

    def _on_local_double_click(self, event, tree):
        """Handle double-click on local files tree"""
        item = event if isinstance(event, QtWidgets.QTreeWidgetItem) else tree.currentItem()
        if not item:
            return

        if item.data(0, QtCore.Qt.UserRole) != "dir":
            return

        item_text = item.text(0)

        if item_text == "..":
            new_path = os.path.dirname(self.local_path_entry.text())
            if not new_path:
                new_path = os.path.sep
            self.local_path_entry.setText(new_path)
        else:
            new_path = os.path.join(self.local_path_entry.text(), item_text)
            self.local_path_entry.setText(new_path)

        self._refresh_local_files(tree)

    def _on_android_double_click(self, event, tree):
        """Handle double-click on Android files tree"""
        item = event if isinstance(event, QtWidgets.QTreeWidgetItem) else tree.currentItem()
        if not item:
            return

        if item.data(0, QtCore.Qt.UserRole) != "dir":
            return

        item_text = item.text(0)

        if item_text == "..":
            current_path = self.android_path_entry.text()
            if current_path == "/":
                return

            new_path = os.path.dirname(current_path)
            if not new_path:
                new_path = "/"
            self.android_path_entry.setText(new_path)
        else:
            new_path = os.path.join(self.android_path_entry.text(), item_text)
            self.android_path_entry.setText(new_path)

        self._refresh_android_files(tree)

    def _upload_to_device(self, local_tree, android_tree):
        """Upload selected file from PC to Android device"""
        selection = local_tree.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No File Selected", "Please select a file to upload."
            )
            return

        for item in selection:
            item_text = item.text(0)

            if item_text == "..":
                continue

            is_dir = item.data(0, QtCore.Qt.UserRole) == "dir"
            source_path = os.path.join(self.local_path_entry.text(), item_text)
            target_path = self.android_path_entry.text()

            self._run_in_thread(
                lambda src=source_path, tgt=target_path, is_dir=is_dir: self._upload_file_task(
                    src, tgt, is_dir, android_tree
                )
            )

    def _upload_file_task(self, source_path, target_path, is_directory, tree):
        """Worker thread to upload file/directory to device"""
        try:
            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = "adb"

            serial = self.device_info.get("serial")
            if not serial:
                emit_ui(self, lambda: self.log_message("Device serial not found"))
                return

            name = os.path.basename(source_path)

            emit_ui(self, lambda: self._set_file_manager_status(f"Uploading {name}..."))
            self.log_message(f"Uploading {name} to {target_path}...")

            result = subprocess.run(
                [adb_cmd, "-s", serial, "push", source_path, target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                error = result.stderr.strip()
                self.log_message(f"Upload failed: {error}")
                emit_ui(self, lambda: self._set_file_manager_status("Upload failed"))
                emit_ui(
                    self,
                    lambda err=error, name=name: QtWidgets.QMessageBox.critical(
                        self, "Upload Error", f"Failed to upload {name}: {err}"
                    ),
                )
                return

            self.log_message(f"Upload of {name} completed successfully")
            emit_ui(self, lambda: self._set_file_manager_status("Upload complete"))
            emit_ui(self, lambda: self._refresh_android_files(tree))

        except Exception as e:
            self.log_message(f"Error during upload: {str(e)}")
            emit_ui(self, lambda: self._set_file_manager_status("Upload failed"))
            emit_ui(
                self,
                lambda err=str(e): QtWidgets.QMessageBox.critical(
                    self, "Upload Error", f"Failed to upload file: {err}"
                ),
            )

    def _download_from_device(self, android_tree, local_tree):
        """Download selected file from Android device to PC"""
        selection = android_tree.selectedItems()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "No File Selected", "Please select a file to download."
            )
            return

        for item in selection:
            item_text = item.text(0)

            if item_text == "..":
                continue

            is_dir = item.data(0, QtCore.Qt.UserRole) == "dir"
            source_path = os.path.join(self.android_path_entry.text(), item_text)
            target_path = self.local_path_entry.text()

            self._run_in_thread(
                lambda src=source_path, tgt=target_path, is_dir=is_dir: self._download_file_task(
                    src, tgt, is_dir, local_tree
                )
            )

    def _download_file_task(self, source_path, target_path, is_directory, tree):
        """Worker thread to download file/directory from device"""
        try:
            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = "adb"

            serial = self.device_info.get("serial")
            if not serial:
                emit_ui(self, lambda: self.log_message("Device serial not found"))
                return

            name = os.path.basename(source_path)

            emit_ui(self, lambda: self._set_file_manager_status(f"Downloading {name}..."))
            self.log_message(f"Downloading {name} to {target_path}...")

            result = subprocess.run(
                [adb_cmd, "-s", serial, "pull", source_path, target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                error = result.stderr.strip()
                self.log_message(f"Download failed: {error}")
                emit_ui(self, lambda: self._set_file_manager_status("Download failed"))
                emit_ui(
                    self,
                    lambda err=error, name=name: QtWidgets.QMessageBox.critical(
                        self, "Download Error", f"Failed to download {name}: {err}"
                    ),
                )
                return

            self.log_message(f"Download of {name} completed successfully")
            emit_ui(self, lambda: self._set_file_manager_status("Download complete"))
            emit_ui(self, lambda: self._refresh_local_files(tree))

        except Exception as e:
            self.log_message(f"Error during download: {str(e)}")
            emit_ui(self, lambda: self._set_file_manager_status("Download failed"))
            emit_ui(
                self,
                lambda err=str(e): QtWidgets.QMessageBox.critical(
                    self, "Download Error", f"Failed to download file: {err}"
                ),
            )

    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        units = ["B", "KB", "MB", "GB", "TB"]

        if size_bytes == 0:
            return "0 B"

        i = 0
        size = float(size_bytes)
        while size >= 1024.0 and i < len(units) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.2f} {units[i]}"

    def _pull_from_device(self):
        """Pull a file or folder from the device to the computer"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        device_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select File or Folder on Device", "/sdcard"
        )

        if not device_path:
            return

        local_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Destination Folder on Computer"
        )

        if not local_path:
            return

        serial = self.device_info.get("serial", "")
        adb_cmd = self.adb_path if IS_WINDOWS else "adb"

        progress = QtWidgets.QProgressDialog(
            "Pulling files from device...", None, 0, 0, self
        )
        progress.setWindowTitle("Pulling Files")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        def pull_task():
            try:
                cmd = [adb_cmd, "-s", serial, "pull", device_path, local_path]
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.returncode == 0:
                    emit_ui(
                        self,
                        lambda: QtWidgets.QMessageBox.information(
                            self, "Success", f"Successfully pulled to {local_path}"
                        ),
                    )
                else:
                    emit_ui(
                        self,
                        lambda err=result.stderr: QtWidgets.QMessageBox.critical(
                            self, "Error", f"Failed to pull file/folder: {err}"
                        ),
                    )
            except Exception as e:
                emit_ui(
                    self,
                    lambda err=str(e): QtWidgets.QMessageBox.critical(
                        self, "Error", f"An error occurred: {err}"
                    ),
                )
            finally:
                emit_ui(self, progress.close)

        self._run_in_thread(pull_task)

    def _push_to_device(self):
        """Push a file or folder from the computer to the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        local_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select File or Folder to Push", os.path.expanduser("~")
        )

        if not local_path:
            return

        device_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Destination Folder on Device", "/sdcard"
        )

        if not device_path:
            return

        serial = self.device_info.get("serial", "")
        adb_cmd = self.adb_path if IS_WINDOWS else "adb"

        progress = QtWidgets.QProgressDialog(
            "Pushing files to device...", None, 0, 0, self
        )
        progress.setWindowTitle("Pushing Files")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        def push_task():
            try:
                cmd = [adb_cmd, "-s", serial, "push", local_path, device_path]
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.returncode == 0:
                    emit_ui(
                        self,
                        lambda: QtWidgets.QMessageBox.information(
                            self, "Success", f"Successfully pushed to {device_path}"
                        ),
                    )
                else:
                    emit_ui(
                        self,
                        lambda err=result.stderr: QtWidgets.QMessageBox.critical(
                            self, "Error", f"Failed to push file/folder: {err}"
                        ),
                    )
            except Exception as e:
                emit_ui(
                    self,
                    lambda err=str(e): QtWidgets.QMessageBox.critical(
                        self, "Error", f"An error occurred: {err}"
                    ),
                )
            finally:
                emit_ui(self, progress.close)

        self._run_in_thread(push_task)

    def _go_up_directory(self, entry, tree=None, root_fallback=None):
        current_path = entry.text()
        new_path = os.path.dirname(current_path)
        if root_fallback is not None and not new_path:
            new_path = root_fallback
        entry.setText(new_path)
        if tree is not None:
            if entry is self.android_path_entry:
                self._refresh_android_files(tree)
            else:
                self._refresh_local_files(tree)

    def _set_android_path(self, value, tree):
        if value:
            self.android_path_entry.setText(value)
            self._refresh_android_files(tree)

    def _set_file_manager_status(self, text):
        if hasattr(self, "fm_status_label") and self.fm_status_label:
            self.fm_status_label.setText(text)
