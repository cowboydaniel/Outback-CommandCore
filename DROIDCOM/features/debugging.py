"""
DROIDCOM - Debugging Feature Module
Handles debugging features like bug reports, crash dumps, ANR traces.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import threading
import os
import time

from ..constants import IS_WINDOWS


class DebuggingMixin:
    """Mixin class providing debugging functionality."""

    def _generate_bug_report(self):
        """Generate a bug report from the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Generate Bug Report")
            dialog.resize(500, 300)
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            title = QtWidgets.QLabel("Bug Report Generation")
            title.setStyleSheet("font-weight: bold;")
            main_layout.addWidget(title)
            main_layout.addWidget(
                QtWidgets.QLabel(
                    "This will generate a full bug report from the device.\n"
                    "The report may take several minutes to generate."
                )
            )

            output_layout = QtWidgets.QHBoxLayout()
            output_layout.addWidget(QtWidgets.QLabel("Save to:"))
            output_entry = QtWidgets.QLineEdit(os.path.expanduser("~/Desktop"))
            output_layout.addWidget(output_entry)

            def browse_directory():
                directory = QtWidgets.QFileDialog.getExistingDirectory(
                    self, "Select Output Directory"
                )
                if directory:
                    output_entry.setText(directory)

            browse_btn = QtWidgets.QPushButton("Browse")
            browse_btn.clicked.connect(browse_directory)
            output_layout.addWidget(browse_btn)
            main_layout.addLayout(output_layout)

            # Progress
            status_label = QtWidgets.QLabel("Ready to generate")
            main_layout.addWidget(status_label)
            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setRange(0, 0)
            progress_bar.setVisible(False)
            main_layout.addWidget(progress_bar)

            def generate_report():
                output_dir = output_entry.text()
                if not os.path.exists(output_dir):
                    QtWidgets.QMessageBox.critical(
                        self, "Error", "Output directory does not exist"
                    )
                    return

                status_label.setText("Generating bug report...")
                progress_bar.setVisible(True)

                def report_thread():
                    try:
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = os.path.join(output_dir, f"bugreport_{timestamp}.zip")

                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "bugreport", filename],
                            capture_output=True, text=True, timeout=600
                        )

                        QtCore.QTimer.singleShot(0, lambda: progress_bar.setVisible(False))

                        if result.returncode == 0:
                            def on_success():
                                status_label.setText("Bug report generated successfully!")
                                QtWidgets.QMessageBox.information(
                                    self, "Success", f"Bug report saved to:\n{filename}"
                                )

                            QtCore.QTimer.singleShot(0, on_success)
                        else:
                            def on_failure():
                                status_label.setText("Failed to generate bug report")
                                QtWidgets.QMessageBox.critical(
                                    self,
                                    "Error",
                                    f"Failed to generate bug report:\n{result.stderr}",
                                )

                            QtCore.QTimer.singleShot(0, on_failure)

                    except subprocess.TimeoutExpired:
                        def on_timeout():
                            progress_bar.setVisible(False)
                            status_label.setText("Timeout")
                            QtWidgets.QMessageBox.critical(
                                self, "Timeout", "Bug report generation timed out"
                            )

                        QtCore.QTimer.singleShot(0, on_timeout)
                    except Exception as e:
                        def on_error():
                            progress_bar.setVisible(False)
                            status_label.setText(f"Error: {str(e)}")
                            QtWidgets.QMessageBox.critical(self, "Error", str(e))

                        QtCore.QTimer.singleShot(0, on_error)

                threading.Thread(target=report_thread, daemon=True).start()

            buttons_layout = QtWidgets.QHBoxLayout()
            generate_btn = QtWidgets.QPushButton("Generate")
            generate_btn.clicked.connect(generate_report)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addWidget(generate_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            main_layout.addLayout(buttons_layout)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open bug report dialog: {str(e)}"
            )

    def _show_anr_traces(self):
        """Show ANR traces from the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("ANR Traces")
            dialog.resize(800, 600)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            text_widget = QtWidgets.QPlainTextEdit()
            text_widget.setReadOnly(True)
            text_widget.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            main_layout.addWidget(text_widget)

            status_label = QtWidgets.QLabel("Loading...")
            main_layout.addWidget(status_label)

            def load_traces():
                try:
                    # Try to get ANR traces
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "cat /data/anr/traces.txt 2>/dev/null"],
                        capture_output=True, text=True, timeout=30
                    )

                    QtCore.QTimer.singleShot(0, lambda: text_widget.clear())

                    if result.returncode == 0 and result.stdout.strip():
                        def set_traces():
                            text_widget.appendPlainText("===== ANR Traces =====\n")
                            text_widget.appendPlainText(result.stdout[:50000])
                            status_label.setText("ANR traces loaded")

                        QtCore.QTimer.singleShot(0, set_traces)
                    else:
                        # Try alternative location
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "ls /data/anr/ 2>/dev/null"],
                            capture_output=True, text=True, timeout=10
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            def set_files():
                                text_widget.appendPlainText("===== ANR Files =====\n")
                                text_widget.appendPlainText(result.stdout)
                                status_label.setText("ANR files found")

                            QtCore.QTimer.singleShot(0, set_files)
                        else:
                            def set_none():
                                text_widget.appendPlainText(
                                    "No ANR traces found.\n\n"
                                    "ANR traces may not be accessible without root access."
                                )
                                status_label.setText("No traces found")

                            QtCore.QTimer.singleShot(0, set_none)

                except Exception as e:
                    def set_error():
                        text_widget.appendPlainText(f"Error: {str(e)}")
                        status_label.setText("Error loading traces")

                    QtCore.QTimer.singleShot(0, set_error)

            threading.Thread(target=load_traces, daemon=True).start()

            buttons_layout = QtWidgets.QHBoxLayout()
            refresh_btn = QtWidgets.QPushButton("Refresh")
            refresh_btn.clicked.connect(
                lambda: threading.Thread(target=load_traces, daemon=True).start()
            )
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addWidget(refresh_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            main_layout.addLayout(buttons_layout)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to show ANR traces: {str(e)}"
            )

    def _refresh_anr_traces(self, text_widget, serial, adb_cmd, status_var=None):
        """Refresh ANR traces"""
        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cat /data/anr/traces.txt"],
                capture_output=True, text=True, timeout=30
            )

            text_widget.clear()

            if result.returncode == 0 and result.stdout.strip():
                text_widget.appendPlainText("===== ANR Traces =====\n")
                text_widget.appendPlainText(result.stdout[:50000])
                if status_var:
                    status_var.setText("ANR traces loaded")
            else:
                text_widget.appendPlainText("No ANR traces available")
                if status_var:
                    status_var.setText("No traces")

        except Exception as e:
            text_widget.appendPlainText(f"Error: {str(e)}")

    def _show_crash_dumps(self):
        """Show crash dumps from the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Crash Dumps")
            dialog.resize(900, 600)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
            main_layout.addWidget(splitter)

            list_frame = QtWidgets.QWidget()
            list_layout = QtWidgets.QVBoxLayout(list_frame)
            list_layout.addWidget(QtWidgets.QLabel("Crash Files:"))
            crash_listbox = QtWidgets.QListWidget()
            list_layout.addWidget(crash_listbox)
            splitter.addWidget(list_frame)

            detail_frame = QtWidgets.QWidget()
            detail_layout = QtWidgets.QVBoxLayout(detail_frame)
            detail_layout.addWidget(QtWidgets.QLabel("Crash Details:"))
            detail_widget = QtWidgets.QPlainTextEdit()
            detail_widget.setReadOnly(True)
            detail_widget.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            detail_layout.addWidget(detail_widget)
            splitter.addWidget(detail_frame)

            status_label = QtWidgets.QLabel("Loading...")
            main_layout.addWidget(status_label)

            def load_crash_list():
                try:
                    # Check for dropbox crashes
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "ls /data/system/dropbox/ 2>/dev/null | head -50"],
                        capture_output=True, text=True, timeout=10
                    )

                    QtCore.QTimer.singleShot(0, lambda: crash_listbox.clear())

                    if result.returncode == 0 and result.stdout.strip():
                        files = result.stdout.strip().split('\n')
                        for f in files:
                            QtCore.QTimer.singleShot(
                                0, lambda file=f: crash_listbox.addItem(file)
                            )
                        QtCore.QTimer.singleShot(
                            0, lambda: status_label.setText(f"Found {len(files)} crash files")
                        )
                    else:
                        # Try tombstones
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "ls /data/tombstones/ 2>/dev/null"],
                            capture_output=True, text=True, timeout=10
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            files = result.stdout.strip().split('\n')
                            for f in files:
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda file=f: crash_listbox.addItem(f"tombstones/{file}"),
                                )
                            QtCore.QTimer.singleShot(
                                0, lambda: status_label.setText(f"Found {len(files)} tombstone files")
                            )
                        else:
                            QtCore.QTimer.singleShot(0, lambda: status_label.setText("No crash files found"))

                except Exception as e:
                    QtCore.QTimer.singleShot(
                        0, lambda: status_label.setText(f"Error: {str(e)}")
                    )

            def on_crash_select():
                selection = crash_listbox.selectedItems()
                if not selection:
                    return

                filename = selection[0].text()

                def load_detail():
                    try:
                        if filename.startswith("tombstones/"):
                            path = f"/data/tombstones/{filename[11:]}"
                        else:
                            path = f"/data/system/dropbox/{filename}"

                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", f"cat {path} 2>/dev/null | head -500"],
                            capture_output=True, text=True, timeout=15
                        )

                        def set_detail():
                            detail_widget.clear()
                            detail_widget.appendPlainText(
                                result.stdout if result.stdout else "Unable to read file"
                            )

                        QtCore.QTimer.singleShot(0, set_detail)

                    except Exception as e:
                        QtCore.QTimer.singleShot(
                            0, lambda: detail_widget.appendPlainText(f"Error: {str(e)}")
                        )

                threading.Thread(target=load_detail, daemon=True).start()

            crash_listbox.itemSelectionChanged.connect(on_crash_select)

            threading.Thread(target=load_crash_list, daemon=True).start()

            buttons_layout = QtWidgets.QHBoxLayout()
            refresh_btn = QtWidgets.QPushButton("Refresh")
            refresh_btn.clicked.connect(
                lambda: threading.Thread(target=load_crash_list, daemon=True).start()
            )
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addWidget(refresh_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            main_layout.addLayout(buttons_layout)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to show crash dumps: {str(e)}"
            )

    def _show_system_log(self):
        """Show system log (dmesg)"""
        QtWidgets.QMessageBox.information(
            self,
            "System Log",
            "System log viewer is being migrated to PySide6 and will be restored shortly.",
        )

    def _start_screen_recording(self):
        """Start screen recording on the device"""
        QtWidgets.QMessageBox.information(
            self,
            "Screen Recording",
            "Screen recording UI is being migrated to PySide6 and will be restored shortly.",
        )
