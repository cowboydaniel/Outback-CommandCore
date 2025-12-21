"""
DROIDCOM - Backup Feature Module
Handles device backup and restore functionality.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import os
import json
import time

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui


class BackupMixin:
    """Mixin class providing backup functionality."""

    def backup_device(self):
        """Backup the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        # Ask for backup directory
        backup_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Backup Directory"
        )

        if not backup_path:
            return

        # Show backup options dialog
        backup_dialog = QtWidgets.QDialog(self)
        backup_dialog.setWindowTitle("Backup Options")
        backup_dialog.resize(750, 850)
        backup_dialog.setModal(True)

        main_layout = QtWidgets.QVBoxLayout(backup_dialog)
        title = QtWidgets.QLabel("Android Backup Options")
        title.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(title)

        options_group = QtWidgets.QGroupBox("Backup Content")
        options_layout = QtWidgets.QVBoxLayout(options_group)

        backup_options = {
            "apps": QtWidgets.QCheckBox("Apps and App Data"),
            "system": QtWidgets.QCheckBox("System Settings"),
            "media": QtWidgets.QCheckBox("Media (Photos, Videos, Music)"),
            "documents": QtWidgets.QCheckBox("Documents and Downloads"),
            "shared": QtWidgets.QCheckBox("Shared Storage"),
        }
        backup_options["apps"].setChecked(True)
        backup_options["system"].setChecked(True)
        for key in ("apps", "system", "media", "documents", "shared"):
            options_layout.addWidget(backup_options[key])

        main_layout.addWidget(options_group)

        adv_group = QtWidgets.QGroupBox("Advanced Options")
        adv_layout = QtWidgets.QVBoxLayout(adv_group)
        backup_options["encrypt"] = QtWidgets.QCheckBox("Encrypt Backup (Password Protected)")
        adv_layout.addWidget(backup_options["encrypt"])
        main_layout.addWidget(adv_group)

        button_layout = QtWidgets.QHBoxLayout()
        start_btn = QtWidgets.QPushButton("Start Backup")
        start_btn.clicked.connect(
            lambda: self._start_backup(backup_dialog, backup_path, backup_options)
        )
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(backup_dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(start_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        backup_dialog.exec()

    def _start_backup(self, dialog, backup_path, options):
        """Start the backup process"""
        dialog.destroy()
        self._run_in_thread(lambda: self._backup_task(backup_path, options))

    def _backup_task(self, backup_path, options):
        """Worker thread to perform the Android device backup"""
        try:
            self.update_status("Backing up device...")
            self.log_message("Starting Android device backup...")

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
                self.update_status("Backup failed")
                return

            # Create backup directory
            device_model = self.device_info.get('model', 'Android').replace(' ', '_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(backup_path, f"{device_model}_{timestamp}_backup")
            os.makedirs(backup_folder, exist_ok=True)

            self.log_message(f"Saving backup to: {backup_folder}")

            # Build backup command
            backup_flags = []

            if options['apps'].isChecked():
                backup_flags.append("-apk")
                backup_flags.append("-all")

            if options['system'].isChecked():
                backup_flags.append("-system")

            if options['shared'].isChecked():
                backup_flags.append("-shared")

            backup_file = os.path.join(backup_folder, "backup.ab")

            cmd = [adb_cmd, '-s', serial, 'backup']
            cmd.extend(backup_flags)
            cmd.extend(["-f", backup_file])

            self.log_message("Starting ADB backup (you may need to confirm on your device)")
            self.update_status("Backup in progress...")

            emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                self,
                "Backup Started",
                "The backup process has started. You may need to unlock your device and confirm the backup.\n\n"
                "Please DO NOT disconnect your device until the backup is complete.",
            ))

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.log_message(f"Backup failed: {result.stderr.strip()}")
                self.update_status("Backup failed")
                QtWidgets.QMessageBox.critical(
                    self, "Backup Error", f"Failed to backup device: {result.stderr.strip()}"
                )
                return

            # Backup files if selected
            if options['media'].isChecked() or options['documents'].isChecked():
                self._backup_files(adb_cmd, serial, backup_folder, options)

            # Create backup info file
            self._create_backup_info(backup_folder, options)

            self.log_message("Device backup completed successfully")
            self.update_status("Backup completed")

            QtWidgets.QMessageBox.information(
                self,
                "Backup Complete",
                f"Your device has been successfully backed up to:\n{backup_folder}",
            )

        except subprocess.TimeoutExpired:
            self.log_message("Backup timeout - this may be normal if the backup is large")
            self.update_status("Backup in progress on device")
            QtWidgets.QMessageBox.information(
                self,
                "Backup In Progress",
                "The backup is being processed on your device. This may take some time.\n\n"
                "You will need to confirm the backup on your device and wait for it to complete.",
            )
        except Exception as e:
            self.log_message(f"Error during backup: {str(e)}")
            self.update_status("Backup failed")
            QtWidgets.QMessageBox.critical(
                self, "Backup Error", f"Failed to backup device: {str(e)}"
            )

    def _backup_files(self, adb_cmd, serial, backup_folder, options):
        """Backup files from the device"""
        try:
            if options['media'].isChecked():
                media_folder = os.path.join(backup_folder, "Media")
                os.makedirs(os.path.join(media_folder, "Pictures"), exist_ok=True)
                os.makedirs(os.path.join(media_folder, "Videos"), exist_ok=True)
                os.makedirs(os.path.join(media_folder, "Music"), exist_ok=True)

                self.log_message("Backing up photos...")
                self.update_status("Backing up photos...")

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/DCIM', os.path.join(media_folder, "Pictures")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Movies', os.path.join(media_folder, "Videos")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Music', os.path.join(media_folder, "Music")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            if options['documents'].isChecked():
                docs_folder = os.path.join(backup_folder, "Documents")
                os.makedirs(docs_folder, exist_ok=True)

                self.log_message("Backing up documents...")
                self.update_status("Backing up documents...")

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Documents', docs_folder],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Download', docs_folder],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

        except Exception as e:
            self.log_message(f"Error backing up files: {str(e)}")

    def _create_backup_info(self, backup_folder, options):
        """Create a backup info file with details about the backup"""
        try:
            backup_info = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'device_info': self.device_info,
                'backup_options': {k: v.get() for k, v in options.items() if hasattr(v, 'get')}
            }

            info_file = os.path.join(backup_folder, "backup_info.json")
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=4)

        except Exception as e:
            self.log_message(f"Error creating backup info: {str(e)}")
