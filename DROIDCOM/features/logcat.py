"""
DROIDCOM - Logcat Feature Module
Handles logcat viewing and filtering.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import threading
import re
import time

from ..app.config import IS_WINDOWS
from ..utils.qt_dispatcher import append_text, clear_text, emit_ui


class LogcatMixin:
    """Mixin class providing logcat viewing functionality."""

    def view_logcat(self):
        """View logcat from the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        self._run_in_thread(self._view_logcat_task)

    def _view_logcat_task(self):
        """Worker thread to open a logcat viewer"""
        try:
            emit_ui(self, lambda: self.update_status("Opening logcat viewer..."))
            emit_ui(self, lambda: self.log_message("Opening logcat viewer..."))

            if IS_WINDOWS:
                adb_path = self._find_adb_path()
                if not adb_path:
                    emit_ui(self, lambda: self.update_status("ADB not found"))
                    return
                adb_cmd = adb_path
            else:
                adb_cmd = 'adb'

            serial = self.device_info.get('serial')
            if not serial:
                emit_ui(self, lambda: self.log_message("Device serial not found"))
                emit_ui(self, lambda: self.update_status("Failed to open logcat"))
                return

            emit_ui(self, lambda: self._show_logcat_window(serial, adb_cmd))

        except Exception as e:
            emit_ui(self, lambda: self.log_message(f"Error opening logcat: {str(e)}"))
            emit_ui(self, lambda: self.update_status("Failed to open logcat"))

    def _show_logcat_window(self, serial, adb_cmd):
        """Show the logcat window"""
        try:
            logcat_window = QtWidgets.QDialog(self)
            logcat_window.setWindowTitle("Android Logcat Viewer")
            logcat_window.resize(800, 600)
            logcat_window.setMinimumSize(600, 400)

            main_layout = QtWidgets.QVBoxLayout(logcat_window)

            filter_layout = QtWidgets.QHBoxLayout()
            filter_layout.addWidget(QtWidgets.QLabel("Filter:"))

            filter_entry = QtWidgets.QLineEdit()
            filter_layout.addWidget(filter_entry)

            filter_layout.addWidget(QtWidgets.QLabel("Log Level:"))
            level_combo = QtWidgets.QComboBox()
            level_combo.addItems(["VERBOSE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"])
            filter_layout.addWidget(level_combo)

            apply_btn = QtWidgets.QPushButton("Apply Filter")
            clear_btn = QtWidgets.QPushButton("Clear")
            filter_layout.addWidget(apply_btn)
            filter_layout.addWidget(clear_btn)

            main_layout.addLayout(filter_layout)

            log_text = QtWidgets.QPlainTextEdit()
            log_text.setReadOnly(True)
            log_text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            main_layout.addWidget(log_text)

            button_layout = QtWidgets.QHBoxLayout()
            save_btn = QtWidgets.QPushButton("Save Log")
            close_btn = QtWidgets.QPushButton("Close")
            button_layout.addWidget(save_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            main_layout.addLayout(button_layout)

            log_text.appendPlainText("Loading logcat... Please wait.")

            logcat_window.log_text = log_text
            logcat_window.filter_entry = filter_entry
            logcat_window.level_combo = level_combo

            # Start logcat thread
            logcat_thread = threading.Thread(
                target=self._run_logcat,
                args=(serial, adb_cmd, logcat_window, log_text, filter_entry, level_combo)
            )
            logcat_thread.daemon = True
            logcat_window.logcat_thread = logcat_thread
            logcat_thread.start()

            # Configure buttons
            clear_btn.clicked.connect(lambda: self._clear_logcat(log_text))
            apply_btn.clicked.connect(lambda: self._apply_logcat_filter(serial, adb_cmd, logcat_window))
            save_btn.clicked.connect(lambda: self._save_logcat(log_text))
            close_btn.clicked.connect(lambda: self._close_logcat(logcat_window, serial, adb_cmd))

            # Update title with device info
            model = self.device_info.get('model', 'Unknown')
            logcat_window.setWindowTitle(f"Android Logcat - {model} ({serial})")
            logcat_window.finished.connect(lambda _: self._close_logcat(logcat_window, serial, adb_cmd))
            logcat_window.show()

        except Exception as e:
            self.log_message(f"Error showing logcat window: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Logcat Error", f"Failed to show logcat window: {str(e)}"
            )

    def _run_logcat(self, serial, adb_cmd, window, log_text, filter_entry, level_combo):
        """Run logcat in a separate thread"""
        try:
            process = None

            current_filter = filter_entry.text()
            current_level = level_combo.currentText()

            level_map = {
                "VERBOSE": "V",
                "DEBUG": "D",
                "INFO": "I",
                "WARN": "W",
                "ERROR": "E",
                "FATAL": "F"
            }

            cmd = [adb_cmd, '-s', serial, 'logcat', '*:' + level_map[current_level]]

            if current_filter:
                cmd.extend(["|", "grep", current_filter])

            log_level_pattern = re.compile(r'\b([VDIWEAF])/')

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=True if '|' in cmd else False
            )

            window.logcat_process = process

            emit_ui(self, lambda: self._clear_logcat(log_text))

            for line in iter(process.stdout.readline, ''):
                if not window.isVisible():
                    break

                tag = "DEBUG"

                match = log_level_pattern.search(line)
                if match:
                    level_char = match.group(1)
                    if level_char == 'V':
                        tag = "VERBOSE"
                    elif level_char == 'D':
                        tag = "DEBUG"
                    elif level_char == 'I':
                        tag = "INFO"
                    elif level_char == 'W':
                        tag = "WARN"
                    elif level_char == 'E':
                        tag = "ERROR"
                    elif level_char == 'F' or level_char == 'A':
                        tag = "FATAL"

                if window.isVisible():
                    emit_ui(
                        self, lambda l=line, t=tag: self._append_logcat_line(log_text, l, t)
                    )

            if process.poll() is not None:
                status = process.poll()
                if window.isVisible():
                    emit_ui(
                        self,
                        lambda: self._append_logcat_line(
                            log_text,
                            f"\nLogcat process ended (status {status}). Please close and reopen the viewer.\n",
                            "ERROR",
                        ),
                    )

        except Exception as e:
            emit_ui(self, lambda: self.log_message(f"Error in logcat thread: {str(e)}"))

            if window.isVisible():
                emit_ui(
                    self, lambda: self._append_logcat_line(log_text, f"\nError: {str(e)}\n", "ERROR")
                )

        finally:
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception as e:
                    emit_ui(
                        self,
                        lambda: self.log_message(
                            f"Warning: failed to terminate logcat process: {str(e)}"
                        ),
                    )
                    if window.isVisible():
                        emit_ui(
                            self,
                            lambda: self._append_logcat_line(
                                log_text,
                                f"\nWarning: failed to terminate logcat process: {str(e)}\n",
                                "WARN",
                            ),
                        )
                    try:
                        process.kill()
                    except Exception as kill_error:
                        emit_ui(
                            self,
                            lambda: self.log_message(
                                "Warning: failed to kill logcat process: "
                                f"{str(kill_error)}"
                            ),
                        )
                        if window.isVisible():
                            emit_ui(
                                self,
                                lambda: self._append_logcat_line(
                                    log_text,
                                    "\nWarning: failed to kill logcat process: "
                                    f"{str(kill_error)}\n",
                                    "WARN",
                                ),
                            )

    def _append_logcat_line(self, log_text, line, tag):
        """Append a line to the logcat text widget"""
        try:
            if not log_text.isVisible():
                return
            log_text.appendPlainText(line.rstrip("\n"))
            log_text.verticalScrollBar().setValue(log_text.verticalScrollBar().maximum())

        except Exception as e:
            self.log_message(f"Error appending to logcat: {str(e)}")

    def _clear_logcat(self, log_text):
        """Clear the logcat display"""
        try:
            log_text.clear()
        except Exception as e:
            self.log_message(f"Error clearing logcat: {str(e)}")

    def _apply_logcat_filter(self, serial, adb_cmd, window):
        """Apply a new filter to the logcat"""
        try:
            if hasattr(window, 'logcat_process') and window.logcat_process:
                if window.logcat_process.poll() is None:
                    window.logcat_process.terminate()

            new_thread = threading.Thread(
                target=self._run_logcat,
                args=(serial, adb_cmd, window, window.log_text, window.filter_entry, window.level_combo)
            )
            new_thread.daemon = True

            if hasattr(window, 'logcat_thread'):
                window.logcat_thread = new_thread

            new_thread.start()

        except Exception as e:
            self.log_message(f"Error applying logcat filter: {str(e)}")

    def _save_logcat(self, log_text):
        """Save logcat contents to a file"""
        try:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Logcat Output",
                "",
                "Text files (*.txt);;All files (*.*)",
            )

            if not file_path:
                return

            contents = log_text.toPlainText()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(contents)

            self.log_message(f"Logcat saved to {file_path}")
            QtWidgets.QMessageBox.information(
                self, "Save Complete", f"Logcat output saved to:\n{file_path}"
            )

        except Exception as e:
            self.log_message(f"Error saving logcat: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Save Error", f"Failed to save logcat: {str(e)}"
            )

    def _close_logcat(self, window, serial, adb_cmd):
        """Close the logcat window and terminate the logcat process"""
        try:
            if hasattr(window, 'logcat_process') and window.logcat_process:
                if window.logcat_process.poll() is None:
                    window.logcat_process.terminate()
            window.close()
        except Exception as e:
            self.log_message(f"Error closing logcat: {str(e)}")
