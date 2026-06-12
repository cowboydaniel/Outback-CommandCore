"""
DROIDCOM - File Manager Feature Module
Handles file management dialogs in PySide6.
"""

from PySide6 import QtWidgets, QtCore
import os
import subprocess
import time

from ..app.config import IS_WINDOWS
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

    def _get_adb_serial(self):
        serial = self.device_info.get("serial") or getattr(self, "device_serial", "")
        if isinstance(serial, str) and "\n" in serial:
            serial = serial.split("\n")[0].strip()
        return serial

    def _get_adb_cmd(self):
        return self.adb_path if IS_WINDOWS and getattr(self, "adb_path", None) else "adb"

    def _show_text_dialog(self, title, content, width=800, height=600):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(width, height)
        layout = QtWidgets.QVBoxLayout(dialog)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(content)
        layout.addWidget(text)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        dialog.exec()

    def _clean_app_caches(self):
        """Clear cached data for all installed apps."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        confirm = QtWidgets.QMessageBox.question(
            self, "Clean App Caches",
            "This will clear cached data for all third-party apps.\n\nContinue?",
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Cleaning App Caches")
        dialog.resize(500, 350)
        layout = QtWidgets.QVBoxLayout(dialog)
        log = QtWidgets.QPlainTextEdit()
        log.setReadOnly(True)
        layout.addWidget(log)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        def worker():
            emit_ui(self, lambda: log.appendPlainText("Getting package list..."))
            try:
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm list packages -3"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15,
                )
                packages = [
                    l[len("package:"):].strip()
                    for l in result.stdout.splitlines()
                    if l.startswith("package:")
                ]
                emit_ui(self, lambda: log.appendPlainText(f"Found {len(packages)} apps. Clearing caches..."))
                cleared = 0
                for pkg in packages:
                    r = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "pm", "clear", "--cache-only", pkg],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                    )
                    if r.returncode != 0:
                        # fallback: clear all (requires root or some Android versions)
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "pm", "clear", pkg],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                        )
                    cleared += 1
                    if cleared % 5 == 0:
                        emit_ui(self, lambda n=cleared: log.appendPlainText(f"Cleared {n}/{len(packages)}..."))
                emit_ui(self, lambda: log.appendPlainText(f"\nDone. Cleared caches for {cleared} apps."))
            except Exception as exc:
                emit_ui(self, lambda e=exc: log.appendPlainText(f"Error: {e}"))

        import threading
        threading.Thread(target=worker, daemon=True).start()
        dialog.exec()

    def _explore_protected_storage(self):
        """Browse protected /data/data storage (requires root)."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "su -c 'ls /data/data' 2>/dev/null || ls /data/data"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15,
            )
            content = result.stdout.strip() or result.stderr.strip() or "(empty or no access)"
            self._show_text_dialog(
                "Protected Storage (/data/data)",
                f"Contents of /data/data:\n\n{content}\n\n"
                "Note: Full access requires root. Non-root ADB may only see some directories.",
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    def _search_files_on_device(self):
        """Search for files on the device by name pattern."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Search Files on Device")
        dialog.resize(700, 500)
        layout = QtWidgets.QVBoxLayout(dialog)

        form = QtWidgets.QHBoxLayout()
        form.addWidget(QtWidgets.QLabel("Search path:"))
        path_edit = QtWidgets.QLineEdit("/sdcard")
        form.addWidget(path_edit)
        form.addWidget(QtWidgets.QLabel("Pattern:"))
        pattern_edit = QtWidgets.QLineEdit("*.pdf")
        form.addWidget(pattern_edit)
        search_btn = QtWidgets.QPushButton("Search")
        form.addWidget(search_btn)
        layout.addLayout(form)

        results = QtWidgets.QPlainTextEdit()
        results.setReadOnly(True)
        layout.addWidget(results)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        def do_search():
            path = path_edit.text().strip() or "/sdcard"
            pattern = pattern_edit.text().strip() or "*"
            results.setPlainText(f"Searching {path} for '{pattern}'...")

            def worker():
                try:
                    r = subprocess.run(
                        [adb_cmd, "-s", serial, "shell",
                         f"find {path} -name '{pattern}' 2>/dev/null | head -200"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
                    )
                    output = r.stdout.strip() or "(no results)"
                    emit_ui(self, lambda o=output: results.setPlainText(o))
                except Exception as exc:
                    emit_ui(self, lambda e=exc: results.setPlainText(f"Error: {e}"))

            import threading
            threading.Thread(target=worker, daemon=True).start()

        search_btn.clicked.connect(do_search)
        dialog.exec()

    def _export_sqlite_databases(self):
        """Find and pull SQLite databases from the device."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        save_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select destination folder for SQLite databases"
        )
        if not save_dir:
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Export SQLite Databases")
        dialog.resize(600, 350)
        layout = QtWidgets.QVBoxLayout(dialog)
        log = QtWidgets.QPlainTextEdit()
        log.setReadOnly(True)
        layout.addWidget(log)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        def worker():
            emit_ui(self, lambda: log.appendPlainText("Finding .db files on /sdcard..."))
            try:
                r = subprocess.run(
                    [adb_cmd, "-s", serial, "shell",
                     "find /sdcard -name '*.db' 2>/dev/null"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
                )
                db_files = [l.strip() for l in r.stdout.splitlines() if l.strip()]
                emit_ui(self, lambda n=len(db_files): log.appendPlainText(f"Found {n} database(s). Pulling..."))
                for db in db_files:
                    dest = os.path.join(save_dir, os.path.basename(db))
                    pull = subprocess.run(
                        [adb_cmd, "-s", serial, "pull", db, dest],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
                    )
                    msg = f"{'OK' if pull.returncode == 0 else 'FAIL'}: {db}"
                    emit_ui(self, lambda m=msg: log.appendPlainText(m))
                emit_ui(self, lambda: log.appendPlainText("\nExport complete."))
            except Exception as exc:
                emit_ui(self, lambda e=exc: log.appendPlainText(f"Error: {e}"))

        import threading
        threading.Thread(target=worker, daemon=True).start()
        dialog.exec()

    def _calculate_directory_size(self):
        """Calculate the size of a directory on the device."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        path, ok = QtWidgets.QInputDialog.getText(
            self, "Directory Size", "Enter path on device:", text="/sdcard"
        )
        if not ok or not path.strip():
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()
        try:
            r = subprocess.run(
                [adb_cmd, "-s", serial, "shell", f"du -sh {path.strip()} 2>/dev/null"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
            )
            result = r.stdout.strip() or r.stderr.strip() or "Could not determine size."
            QtWidgets.QMessageBox.information(self, "Directory Size", result)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    def _calculate_file_checksum(self):
        """Calculate SHA-256 checksum of a file on the device."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        path, ok = QtWidgets.QInputDialog.getText(
            self, "File Checksum", "Enter file path on device:"
        )
        if not ok or not path.strip():
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()
        try:
            # Try sha256sum first, fall back to md5sum
            r = subprocess.run(
                [adb_cmd, "-s", serial, "shell",
                 f"sha256sum {path.strip()} 2>/dev/null || md5sum {path.strip()} 2>/dev/null"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
            )
            result = r.stdout.strip() or r.stderr.strip() or "Could not compute checksum."
            QtWidgets.QMessageBox.information(self, "File Checksum", result)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    def _edit_text_file_on_device(self):
        """Pull a text file from device, edit it locally, and push it back."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        remote_path, ok = QtWidgets.QInputDialog.getText(
            self, "Edit File on Device", "Enter file path on device:"
        )
        if not ok or not remote_path.strip():
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tmp_path = tmp.name
        tmp.close()

        try:
            pull = subprocess.run(
                [adb_cmd, "-s", serial, "pull", remote_path.strip(), tmp_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
            )
            if pull.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to pull file:\n{pull.stderr.strip()}"
                )
                return

            with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"Edit: {remote_path.strip()}")
            dialog.resize(800, 600)
            layout = QtWidgets.QVBoxLayout(dialog)
            editor = QtWidgets.QPlainTextEdit()
            editor.setPlainText(content)
            layout.addWidget(editor)

            btn_layout = QtWidgets.QHBoxLayout()
            save_btn = QtWidgets.QPushButton("Save to Device")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            cancel_btn.clicked.connect(dialog.reject)

            def save_file():
                new_content = editor.toPlainText()
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                push = subprocess.run(
                    [adb_cmd, "-s", serial, "push", tmp_path, remote_path.strip()],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
                )
                if push.returncode == 0:
                    QtWidgets.QMessageBox.information(dialog, "Saved", "File saved to device.")
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.critical(
                        dialog, "Error", f"Push failed:\n{push.stderr.strip()}"
                    )

            save_btn.clicked.connect(save_file)
            dialog.exec()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _show_mount_info(self):
        """Show current mount points on the device."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()
        try:
            r = subprocess.run(
                [adb_cmd, "-s", serial, "shell",
                 "cat /proc/mounts 2>/dev/null || mount"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15,
            )
            content = r.stdout.strip() or r.stderr.strip() or "(no output)"
            self._show_text_dialog("Mount Points", content)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    def _list_recent_files(self):
        """List recently modified files on the device."""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        adb_cmd = self._get_adb_cmd()
        serial = self._get_adb_serial()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Recent Files")
        dialog.resize(750, 500)
        layout = QtWidgets.QVBoxLayout(dialog)

        opts_layout = QtWidgets.QHBoxLayout()
        opts_layout.addWidget(QtWidgets.QLabel("Path:"))
        path_edit = QtWidgets.QLineEdit("/sdcard")
        opts_layout.addWidget(path_edit)
        opts_layout.addWidget(QtWidgets.QLabel("Days:"))
        days_spin = QtWidgets.QSpinBox()
        days_spin.setRange(1, 365)
        days_spin.setValue(7)
        opts_layout.addWidget(days_spin)
        refresh_btn = QtWidgets.QPushButton("List")
        opts_layout.addWidget(refresh_btn)
        layout.addLayout(opts_layout)

        output = QtWidgets.QPlainTextEdit()
        output.setReadOnly(True)
        layout.addWidget(output)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        def load():
            path = path_edit.text().strip() or "/sdcard"
            days = days_spin.value()
            output.setPlainText(f"Listing files modified in last {days} day(s) under {path}...")

            def worker():
                try:
                    r = subprocess.run(
                        [adb_cmd, "-s", serial, "shell",
                         f"find {path} -type f -mtime -{days} 2>/dev/null | sort | head -200"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
                    )
                    content = r.stdout.strip() or "(no files found)"
                    emit_ui(self, lambda c=content: output.setPlainText(c))
                except Exception as exc:
                    emit_ui(self, lambda e=exc: output.setPlainText(f"Error: {e}"))

            import threading
            threading.Thread(target=worker, daemon=True).start()

        refresh_btn.clicked.connect(load)
        load()
        dialog.exec()
