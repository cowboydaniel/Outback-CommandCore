"""
DROIDCOM - Debugging Feature Module
Handles debugging features like bug reports, crash dumps, ANR traces.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import subprocess
import threading
import os
import time

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui


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

                        emit_ui(self, lambda: progress_bar.setVisible(False))

                        if result.returncode == 0:
                            def on_success():
                                status_label.setText("Bug report generated successfully!")
                                QtWidgets.QMessageBox.information(
                                    self, "Success", f"Bug report saved to:\n{filename}"
                                )

                            emit_ui(self, on_success)
                        else:
                            def on_failure():
                                status_label.setText("Failed to generate bug report")
                                QtWidgets.QMessageBox.critical(
                                    self,
                                    "Error",
                                    f"Failed to generate bug report:\n{result.stderr}",
                                )

                            emit_ui(self, on_failure)

                    except subprocess.TimeoutExpired:
                        def on_timeout():
                            progress_bar.setVisible(False)
                            status_label.setText("Timeout")
                            QtWidgets.QMessageBox.critical(
                                self, "Timeout", "Bug report generation timed out"
                            )

                        emit_ui(self, on_timeout)
                    except Exception as e:
                        def on_error():
                            progress_bar.setVisible(False)
                            status_label.setText(f"Error: {str(e)}")
                            QtWidgets.QMessageBox.critical(self, "Error", str(e))

                        emit_ui(self, on_error)

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

                    emit_ui(self, lambda: text_widget.clear())

                    if result.returncode == 0 and result.stdout.strip():
                        def set_traces():
                            text_widget.appendPlainText("===== ANR Traces =====\n")
                            text_widget.appendPlainText(result.stdout[:50000])
                            status_label.setText("ANR traces loaded")

                        emit_ui(self, set_traces)
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

                            emit_ui(self, set_files)
                        else:
                            def set_none():
                                text_widget.appendPlainText(
                                    "No ANR traces found.\n\n"
                                    "ANR traces may not be accessible without root access."
                                )
                                status_label.setText("No traces found")

                            emit_ui(self, set_none)

                except Exception as e:
                    def set_error():
                        text_widget.appendPlainText(f"Error: {str(e)}")
                        status_label.setText("Error loading traces")

                    emit_ui(self, set_error)

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

                    emit_ui(self, lambda: crash_listbox.clear())

                    if result.returncode == 0 and result.stdout.strip():
                        files = result.stdout.strip().split('\n')
                        for f in files:
                            emit_ui(
                                self, lambda file=f: crash_listbox.addItem(file)
                            )
                        emit_ui(
                            self, lambda: status_label.setText(f"Found {len(files)} crash files")
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
                                emit_ui(
                                    self,
                                    lambda file=f: crash_listbox.addItem(f"tombstones/{file}"),
                                )
                            emit_ui(
                                self, lambda: status_label.setText(f"Found {len(files)} tombstone files")
                            )
                        else:
                            emit_ui(self, lambda: status_label.setText("No crash files found"))

                except Exception as e:
                    emit_ui(
                        self, lambda: status_label.setText(f"Error: {str(e)}")
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

                        emit_ui(self, set_detail)

                    except Exception as e:
                        emit_ui(
                            self, lambda: detail_widget.appendPlainText(f"Error: {str(e)}")
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
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        serial = self.device_serial
        adb_cmd = self.adb_path if IS_WINDOWS else "adb"

        try:
            device_model = "Android Device"
            if hasattr(self, "device_info"):
                device_model = self.device_info.get("model", device_model)

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"System Log - {device_model}")
            dialog.resize(900, 600)

            main_layout = QtWidgets.QVBoxLayout(dialog)

            control_frame = QtWidgets.QHBoxLayout()
            main_layout.addLayout(control_frame)

            log_type_group = QtWidgets.QGroupBox("Log Type")
            log_type_layout = QtWidgets.QHBoxLayout(log_type_group)
            log_type_buttons = QtWidgets.QButtonGroup(dialog)

            dmesg_radio = QtWidgets.QRadioButton("Kernel (dmesg)")
            logcat_radio = QtWidgets.QRadioButton("Logcat")
            events_radio = QtWidgets.QRadioButton("Events")
            dmesg_radio.setChecked(True)

            log_type_buttons.addButton(dmesg_radio)
            log_type_buttons.addButton(logcat_radio)
            log_type_buttons.addButton(events_radio)

            log_type_layout.addWidget(dmesg_radio)
            log_type_layout.addWidget(logcat_radio)
            log_type_layout.addWidget(events_radio)
            control_frame.addWidget(log_type_group)

            filter_group = QtWidgets.QGroupBox("Filter")
            filter_layout = QtWidgets.QHBoxLayout(filter_group)
            filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
            filter_entry = QtWidgets.QLineEdit()
            filter_layout.addWidget(filter_entry)
            control_frame.addWidget(filter_group)

            level_frame = QtWidgets.QGroupBox("Level")
            level_layout = QtWidgets.QHBoxLayout(level_frame)
            level_layout.addWidget(QtWidgets.QLabel("Level:"))
            level_combo = QtWidgets.QComboBox()
            level_combo.addItems(["V", "D", "I", "W", "E"])
            level_layout.addWidget(level_combo)
            control_frame.addWidget(level_frame)

            button_layout = QtWidgets.QHBoxLayout()
            refresh_btn = QtWidgets.QPushButton("Refresh")
            clear_btn = QtWidgets.QPushButton("Clear")
            save_btn = QtWidgets.QPushButton("Save Log")
            button_layout.addWidget(refresh_btn)
            button_layout.addWidget(clear_btn)
            button_layout.addWidget(save_btn)
            control_frame.addLayout(button_layout)

            auto_refresh_check = QtWidgets.QCheckBox("Auto-refresh")
            control_frame.addWidget(auto_refresh_check)
            control_frame.addStretch()

            log_text = QtWidgets.QTextEdit()
            log_text.setReadOnly(True)
            log_text.setFont(QtGui.QFont("Consolas", 10))
            main_layout.addWidget(log_text)

            status_layout = QtWidgets.QHBoxLayout()
            status_label = QtWidgets.QLabel("Ready")
            line_count_label = QtWidgets.QLabel("Lines: 0")
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            status_layout.addWidget(line_count_label)
            main_layout.addLayout(status_layout)

            def current_log_type():
                if logcat_radio.isChecked():
                    return "logcat"
                if events_radio.isChecked():
                    return "events"
                return "dmesg"

            def refresh_logs(append_mode=False):
                threading.Thread(
                    target=self._refresh_system_log,
                    args=(
                        log_text,
                        serial,
                        adb_cmd,
                        current_log_type(),
                        filter_entry.text(),
                        level_combo.currentText(),
                        status_label,
                        line_count_label,
                        append_mode,
                    ),
                    daemon=True,
                ).start()

            refresh_btn.clicked.connect(lambda: refresh_logs(append_mode=False))
            clear_btn.clicked.connect(lambda: log_text.clear())
            save_btn.clicked.connect(lambda: self._save_log_to_file(log_text.toPlainText()))

            def on_filter_enter():
                refresh_logs(append_mode=False)

            filter_entry.returnPressed.connect(on_filter_enter)
            dmesg_radio.toggled.connect(lambda checked: checked and refresh_logs(False))
            logcat_radio.toggled.connect(lambda checked: checked and refresh_logs(False))
            events_radio.toggled.connect(lambda checked: checked and refresh_logs(False))
            level_combo.currentIndexChanged.connect(lambda _: refresh_logs(False))

            auto_refresh_timer = QtCore.QTimer(dialog)
            auto_refresh_timer.setInterval(3000)
            auto_refresh_timer.timeout.connect(lambda: refresh_logs(append_mode=True))

            def toggle_auto_refresh(state):
                if state == QtCore.Qt.Checked:
                    refresh_logs(append_mode=True)
                    auto_refresh_timer.start()
                else:
                    auto_refresh_timer.stop()

            auto_refresh_check.stateChanged.connect(toggle_auto_refresh)

            refresh_logs(append_mode=False)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to display system log: {str(e)}"
            )

    def _refresh_system_log(
        self,
        text_widget,
        serial,
        adb_cmd,
        log_type="dmesg",
        filter_text="",
        log_level="V",
        status_label=None,
        line_count_label=None,
        append_mode=False,
    ):
        """Refresh system log in the text widget"""
        if not append_mode:
            emit_ui(
                self, lambda: text_widget.setPlainText(f"Loading {log_type} logs...\n\n")
            )

        try:
            if log_type == "dmesg":
                cmd = [adb_cmd, "-s", serial, "shell", "dmesg"]
            elif log_type == "logcat":
                cmd = [
                    adb_cmd,
                    "-s",
                    serial,
                    "shell",
                    "logcat",
                    "-d",
                    "-v",
                    "threadtime",
                    f"*:{log_level}",
                ]
            elif log_type == "events":
                cmd = [adb_cmd, "-s", serial, "shell", "dumpsys", "events"]
            else:
                if status_label:
                    emit_ui(
                        self, lambda: status_label.setText(f"Unknown log type: {log_type}")
                    )
                return

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                def set_error():
                    if not append_mode:
                        text_widget.clear()
                    text_widget.setPlainText(f"Error retrieving logs:\n{result.stderr}")
                    if status_label:
                        status_label.setText("Error retrieving logs")

                emit_ui(self, set_error)
                return

            output = result.stdout or ""
            if filter_text:
                filter_lower = filter_text.lower()
                output = "\n".join(
                    line for line in output.splitlines() if filter_lower in line.lower()
                )

            def set_logs():
                cursor = text_widget.textCursor()
                if not append_mode:
                    text_widget.clear()
                elif text_widget.toPlainText().strip():
                    cursor.movePosition(QtGui.QTextCursor.End)
                    cursor.insertText(
                        f"\n--- Updated at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                    )

                self._insert_colorized_logs(text_widget, output, log_type)

                if line_count_label:
                    line_count_label.setText(
                        f"Lines: {text_widget.document().blockCount()}"
                    )
                if status_label:
                    status_label.setText(
                        f"Loaded {log_type} logs at {time.strftime('%H:%M:%S')}"
                    )

            emit_ui(self, set_logs)

        except subprocess.TimeoutExpired:
            def set_timeout():
                if not append_mode:
                    text_widget.clear()
                text_widget.setPlainText("Command timed out. Device may be unresponsive.")
                if status_label:
                    status_label.setText("Command timed out")

            emit_ui(self, set_timeout)
        except Exception as e:
            def set_error():
                if not append_mode:
                    text_widget.clear()
                text_widget.setPlainText(f"Error: {str(e)}")
                if status_label:
                    status_label.setText(f"Error: {str(e)}")

            emit_ui(self, set_error)

    def _insert_colorized_logs(self, text_widget, log_output, log_type):
        """Insert logs with proper colorization based on log type"""
        cursor = text_widget.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        formats = {
            "debug": QtGui.QTextCharFormat(),
            "info": QtGui.QTextCharFormat(),
            "warning": QtGui.QTextCharFormat(),
            "error": QtGui.QTextCharFormat(),
            "timestamp": QtGui.QTextCharFormat(),
            "process": QtGui.QTextCharFormat(),
        }
        formats["debug"].setForeground(QtGui.QColor("#0000FF"))
        formats["info"].setForeground(QtGui.QColor("#000000"))
        formats["warning"].setForeground(QtGui.QColor("#FF8800"))
        formats["error"].setForeground(QtGui.QColor("#FF0000"))
        formats["timestamp"].setForeground(QtGui.QColor("#008800"))
        formats["process"].setForeground(QtGui.QColor("#880088"))

        lines = log_output.splitlines()
        if not lines:
            cursor.insertText("No log entries found.\n")
            return

        for line in lines:
            if not line.strip():
                continue

            if log_type == "logcat":
                parts = line.split(None, 5) if len(line.split()) > 5 else []
                if len(parts) >= 6:
                    date_time = f"{parts[0]} {parts[1]}"
                    pid_tid = parts[2]
                    level = parts[4]
                    message = parts[5]

                    cursor.insertText(date_time + " ", formats["timestamp"])
                    cursor.insertText(pid_tid + " ", formats["process"])

                    if level == "D":
                        cursor.insertText(message + "\n", formats["debug"])
                    elif level == "I":
                        cursor.insertText(message + "\n", formats["info"])
                    elif level == "W":
                        cursor.insertText(message + "\n", formats["warning"])
                    elif level in {"E", "F"}:
                        cursor.insertText(message + "\n", formats["error"])
                    else:
                        cursor.insertText(message + "\n")
                else:
                    cursor.insertText(line + "\n")
            elif log_type == "dmesg":
                lower_line = line.lower()
                if "error" in lower_line or "fail" in lower_line:
                    cursor.insertText(line + "\n", formats["error"])
                elif "warn" in lower_line:
                    cursor.insertText(line + "\n", formats["warning"])
                elif "info" in lower_line:
                    cursor.insertText(line + "\n", formats["info"])
                elif "debug" in lower_line:
                    cursor.insertText(line + "\n", formats["debug"])
                else:
                    if "[" in line and "]" in line:
                        timestamp_end = line.find("]") + 1
                        cursor.insertText(line[:timestamp_end], formats["timestamp"])
                        cursor.insertText(line[timestamp_end:] + "\n")
                    else:
                        cursor.insertText(line + "\n")
            else:
                cursor.insertText(line + "\n")

        text_widget.setTextCursor(cursor)

    def _save_log_to_file(self, log_content):
        """Save log content to a file"""
        if not log_content.strip():
            QtWidgets.QMessageBox.information(
                self, "Empty Log", "There is no log content to save."
            )
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Log As",
            "",
            "Log files (*.log);;Text files (*.txt);;All files (*.*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            QtWidgets.QMessageBox.information(
                self, "Success", f"Log saved to {file_path}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to save log: {e}"
            )

    def _start_screen_recording(self):
        """Start screen recording on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        serial = self.device_serial
        adb_cmd = self.adb_path if IS_WINDOWS else "adb"

        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Screen Recording")
            dialog.resize(750, 850)
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)

            header_label = QtWidgets.QLabel("Android Screen Recording")
            header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            main_layout.addWidget(header_label)

            config_group = QtWidgets.QGroupBox("Recording Settings")
            config_layout = QtWidgets.QVBoxLayout(config_group)

            folder_layout = QtWidgets.QHBoxLayout()
            folder_layout.addWidget(QtWidgets.QLabel("Save to folder:"))
            screenshots_dir = os.path.join(
                os.path.expanduser("~"), "AndroidScreenRecordings"
            )
            os.makedirs(screenshots_dir, exist_ok=True)
            folder_entry = QtWidgets.QLineEdit(screenshots_dir)
            folder_layout.addWidget(folder_entry)

            def browse_folder():
                directory = QtWidgets.QFileDialog.getExistingDirectory(
                    self, "Select Output Directory", folder_entry.text()
                )
                if directory:
                    folder_entry.setText(directory)

            browse_btn = QtWidgets.QPushButton("Browse")
            browse_btn.clicked.connect(browse_folder)
            folder_layout.addWidget(browse_btn)
            config_layout.addLayout(folder_layout)

            filename_layout = QtWidgets.QHBoxLayout()
            filename_layout.addWidget(QtWidgets.QLabel("Filename:"))
            default_filename = f"recording_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
            filename_entry = QtWidgets.QLineEdit(default_filename)
            filename_layout.addWidget(filename_entry)
            config_layout.addLayout(filename_layout)

            time_layout = QtWidgets.QHBoxLayout()
            time_layout.addWidget(QtWidgets.QLabel("Time limit:"))
            time_spin = QtWidgets.QSpinBox()
            time_spin.setRange(1, 180)
            time_spin.setValue(30)
            time_layout.addWidget(time_spin)
            time_layout.addWidget(QtWidgets.QLabel("seconds"))
            config_layout.addLayout(time_layout)

            res_layout = QtWidgets.QHBoxLayout()
            res_layout.addWidget(QtWidgets.QLabel("Resolution:"))
            res_combo = QtWidgets.QComboBox()
            res_combo.addItems(["Default", "1920x1080", "1280x720", "800x600"])
            res_layout.addWidget(res_combo)
            config_layout.addLayout(res_layout)

            bitrate_layout = QtWidgets.QHBoxLayout()
            bitrate_layout.addWidget(QtWidgets.QLabel("Bitrate:"))
            bitrate_combo = QtWidgets.QComboBox()
            bitrate_combo.addItems(["2Mbps", "4Mbps", "6Mbps", "8Mbps", "12Mbps"])
            bitrate_combo.setCurrentText("6Mbps")
            bitrate_layout.addWidget(bitrate_combo)
            config_layout.addLayout(bitrate_layout)

            main_layout.addWidget(config_group)

            options_group = QtWidgets.QGroupBox("Options")
            options_layout = QtWidgets.QVBoxLayout(options_group)

            audio_check = QtWidgets.QCheckBox(
                "Record audio (if supported by device)"
            )
            touch_check = QtWidgets.QCheckBox("Show touch indicators")
            touch_check.setChecked(True)
            progress_check = QtWidgets.QCheckBox("Show progress indicator")
            progress_check.setChecked(True)
            open_check = QtWidgets.QCheckBox("Open after recording")
            open_check.setChecked(True)

            options_layout.addWidget(audio_check)
            options_layout.addWidget(touch_check)
            options_layout.addWidget(progress_check)
            options_layout.addWidget(open_check)
            main_layout.addWidget(options_group)

            button_layout = QtWidgets.QHBoxLayout()
            cancel_btn = QtWidgets.QPushButton("Cancel")
            start_btn = QtWidgets.QPushButton("Start Recording")
            button_layout.addWidget(cancel_btn)
            button_layout.addStretch()
            button_layout.addWidget(start_btn)
            main_layout.addLayout(button_layout)

            cancel_btn.clicked.connect(dialog.reject)

            def start_recording():
                output_path = os.path.join(
                    folder_entry.text(), filename_entry.text()
                )
                bitrate_text = bitrate_combo.currentText()
                bitrate_bps = None
                if bitrate_text:
                    bitrate_value = bitrate_text.lower().replace("mbps", "").strip()
                    try:
                        parsed_bitrate = float(bitrate_value)
                        if parsed_bitrate <= 0:
                            raise ValueError("Bitrate must be positive")
                        bitrate_bps = int(parsed_bitrate * 1000000)
                    except ValueError:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Invalid Bitrate",
                            (
                                f"Invalid bitrate '{bitrate_text}'. "
                                "Default bitrate will be used."
                            ),
                        )
                self._do_screen_recording(
                    dialog,
                    serial,
                    adb_cmd,
                    output_path,
                    int(time_spin.value()),
                    res_combo.currentText(),
                    bitrate_bps,
                    audio_check.isChecked(),
                    touch_check.isChecked(),
                    progress_check.isChecked(),
                    open_check.isChecked(),
                )

            start_btn.clicked.connect(start_recording)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to setup screen recording: {e}"
            )

    def _do_screen_recording(
        self,
        dialog,
        serial,
        adb_cmd,
        output_path,
        time_limit,
        resolution,
        bitrate_bps,
        record_audio,
        show_touches,
        show_progress,
        open_after,
    ):
        """Start the actual screen recording process"""
        try:
            dialog.close()

            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            cmd = [adb_cmd, "-s", serial, "shell", "screenrecord"]

            if resolution != "Default":
                cmd.extend(["--size", resolution])

            if bitrate_bps:
                cmd.extend(["--bit-rate", str(bitrate_bps)])

            cmd.extend(["--time-limit", str(time_limit)])

            if record_audio:
                cmd.append("--mic")
            if show_touches:
                cmd.append("--show-touch")

            device_path = "/sdcard/screen_recording_temp.mp4"
            cmd.append(device_path)

            progress_dialog = None
            progress_timer = None

            if show_progress:
                progress_dialog = QtWidgets.QDialog(self)
                progress_dialog.setWindowTitle("Screen Recording")
                progress_dialog.resize(400, 200)
                progress_layout = QtWidgets.QVBoxLayout(progress_dialog)

                progress_label = QtWidgets.QLabel("Recording in progress...")
                progress_layout.addWidget(progress_label)

                progress_bar = QtWidgets.QProgressBar()
                progress_bar.setRange(0, time_limit)
                progress_bar.setValue(0)
                progress_layout.addWidget(progress_bar)

                time_label = QtWidgets.QLabel(
                    f"Time remaining: {time_limit} seconds"
                )
                progress_layout.addWidget(time_label)

                stop_btn = QtWidgets.QPushButton("Stop Recording")
                progress_layout.addWidget(stop_btn)

                def stop_recording():
                    self._stop_recording(
                        serial,
                        adb_cmd,
                        device_path,
                        output_path,
                        open_after,
                        progress_dialog,
                    )

                stop_btn.clicked.connect(stop_recording)

                progress_dialog.show()

                progress_timer = QtCore.QTimer(progress_dialog)
                progress_state = {"current": 0}

                def update_progress():
                    progress_state["current"] += 1
                    progress_bar.setValue(progress_state["current"])
                    remaining = max(time_limit - progress_state["current"], 0)
                    time_label.setText(
                        f"Time remaining: {remaining} seconds"
                    )
                    if progress_state["current"] >= time_limit:
                        progress_timer.stop()

                progress_timer.timeout.connect(update_progress)
                progress_timer.start(1000)

            threading.Thread(
                target=self._recording_thread,
                args=(
                    cmd,
                    serial,
                    adb_cmd,
                    device_path,
                    output_path,
                    open_after,
                    progress_dialog,
                ),
                daemon=True,
            ).start()

            if not show_progress:
                QtWidgets.QMessageBox.information(
                    self,
                    "Recording Started",
                    f"Screen recording started for {time_limit} seconds. Please wait...",
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to start screen recording: {e}"
            )

    def _recording_thread(
        self,
        cmd,
        serial,
        adb_cmd,
        device_path,
        output_path,
        open_after,
        progress_dialog,
    ):
        """Thread for screen recording process"""
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, error = process.communicate()

            if process.returncode == 0:
                self._finish_recording(
                    serial,
                    adb_cmd,
                    device_path,
                    output_path,
                    open_after,
                    progress_dialog,
                )
            else:
                def show_error():
                    if progress_dialog:
                        progress_dialog.close()
                    QtWidgets.QMessageBox.critical(
                        self, "Error", f"Screen recording failed: {error}"
                    )

                emit_ui(self, show_error)

        except Exception as e:
            def show_error():
                if progress_dialog:
                    progress_dialog.close()
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Recording error: {e}"
                )

            emit_ui(self, show_error)

    def _stop_recording(
        self,
        serial,
        adb_cmd,
        device_path,
        output_path,
        open_after,
        progress_dialog=None,
    ):
        """Stop the ongoing screen recording"""
        try:
            subprocess.run(
                [adb_cmd, "-s", serial, "shell", "killall", "-SIGINT", "screenrecord"],
                timeout=10,
            )
            time.sleep(1)
            self._finish_recording(
                serial,
                adb_cmd,
                device_path,
                output_path,
                open_after,
                progress_dialog,
            )
        except Exception as e:
            emit_ui(
                self,
                lambda: QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to stop recording: {e}"
                ),
            )

    def _finish_recording(
        self,
        serial,
        adb_cmd,
        device_path,
        output_path,
        open_after,
        progress_dialog=None,
    ):
        """Finish the recording by pulling the file and cleaning up"""
        try:
            pull_cmd = [adb_cmd, "-s", serial, "pull", device_path, output_path]
            process = subprocess.Popen(
                pull_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, error = process.communicate()

            def finalize():
                if progress_dialog:
                    progress_dialog.close()

                if process.returncode == 0:
                    subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "rm", device_path],
                        timeout=10,
                    )
                    QtWidgets.QMessageBox.information(
                        self,
                        "Recording Complete",
                        f"Screen recording saved to:\n{output_path}",
                    )
                    if open_after:
                        if IS_WINDOWS:
                            os.startfile(output_path)
                        else:
                            subprocess.run(["xdg-open", output_path])
                else:
                    QtWidgets.QMessageBox.critical(
                        self, "Error", f"Failed to save recording: {error}"
                    )

            emit_ui(self, finalize)

        except Exception as e:
            emit_ui(
                self,
                lambda: QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to finish recording: {e}"
                ),
            )
