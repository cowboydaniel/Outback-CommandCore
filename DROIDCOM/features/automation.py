"""
DROIDCOM - Automation Feature Module
Handles automation features like shell scripts, batch operations, etc.
"""

from PySide6 import QtWidgets, QtCore
import subprocess
import threading
import os

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import append_text, clear_text, emit_ui, set_progress


class AutomationMixin:
    """Mixin class providing automation functionality."""

    def _run_shell_script_dialog(self):
        """Show dialog to run a shell script on the device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Run Shell Script")
            dialog.resize(700, 500)
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            title = QtWidgets.QLabel("Run Shell Script")
            title.setStyleSheet("font-weight: bold;")
            main_layout.addWidget(title)

            file_layout = QtWidgets.QHBoxLayout()
            file_layout.addWidget(QtWidgets.QLabel("Script file:"))
            file_entry = QtWidgets.QLineEdit()
            file_layout.addWidget(file_entry)

            def browse_script():
                file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Select Script",
                    "",
                    "Shell scripts (*.sh);;All files (*.*)",
                )
                if file_path:
                    file_entry.setText(file_path)
                    # Load script content
                    try:
                        with open(file_path, 'r') as f:
                            script_text.setPlainText(f.read())
                    except Exception as e:
                        QtWidgets.QMessageBox.critical(
                            self, "Error", f"Failed to read script: {str(e)}"
                        )

            browse_btn = QtWidgets.QPushButton("Browse")
            browse_btn.clicked.connect(browse_script)
            file_layout.addWidget(browse_btn)
            main_layout.addLayout(file_layout)

            main_layout.addWidget(QtWidgets.QLabel("Script content:"))
            script_text = QtWidgets.QPlainTextEdit()
            script_text.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            main_layout.addWidget(script_text)

            main_layout.addWidget(QtWidgets.QLabel("Output:"))
            output_text = QtWidgets.QPlainTextEdit()
            output_text.setReadOnly(True)
            output_text.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            main_layout.addWidget(output_text)

            def run_script():
                script = script_text.toPlainText().strip()
                if not script:
                    QtWidgets.QMessageBox.critical(self, "Error", "Please enter a script")
                    return

                output_text.clear()

                def execute_script():
                    try:
                        # Write script to temp file on device
                        temp_script = "/data/local/tmp/temp_script.sh"

                        # Push script content to device
                        process = subprocess.Popen(
                            [adb_cmd, "-s", serial, "shell", f"cat > {temp_script}"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        process.communicate(input=script)

                        # Make executable
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", f"chmod +x {temp_script}"],
                            capture_output=True, text=True, timeout=10
                        )

                        # Run script
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", f"sh {temp_script}"],
                            capture_output=True, text=True, timeout=300
                        )

                        # Cleanup
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", f"rm {temp_script}"],
                            capture_output=True, text=True, timeout=10
                        )

                        def append_output():
                            output_text.appendPlainText("=== STDOUT ===")
                            output_text.appendPlainText(result.stdout or "(empty)")
                            output_text.appendPlainText("\n=== STDERR ===")
                            output_text.appendPlainText(result.stderr or "(empty)")
                            output_text.appendPlainText(
                                f"\n=== Return code: {result.returncode} ==="
                            )

                        QtCore.QTimer.singleShot(0, append_output)

                    except Exception as e:
                        QtCore.QTimer.singleShot(
                            0, lambda: output_text.appendPlainText(f"Error: {str(e)}")
                        )

                threading.Thread(target=execute_script, daemon=True).start()

            def save_script():
                script = script_text.toPlainText().strip()
                if not script:
                    return

                file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    "Save Script",
                    "",
                    "Shell scripts (*.sh);;All files (*.*)",
                )
                if file_path:
                    with open(file_path, 'w') as f:
                        f.write(script)
                    QtWidgets.QMessageBox.information(
                        self, "Saved", f"Script saved to:\n{file_path}"
                    )

            def clear_script():
                script_text.clear()
                output_text.clear()

            buttons_layout = QtWidgets.QHBoxLayout()
            run_btn = QtWidgets.QPushButton("Run")
            run_btn.clicked.connect(run_script)
            save_btn = QtWidgets.QPushButton("Save")
            save_btn.clicked.connect(save_script)
            clear_btn = QtWidgets.QPushButton("Clear")
            clear_btn.clicked.connect(clear_script)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addWidget(run_btn)
            buttons_layout.addWidget(save_btn)
            buttons_layout.addWidget(clear_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            main_layout.addLayout(buttons_layout)

            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open shell script dialog: {str(e)}"
            )

    def _batch_app_manager_dialog(self):
        """Show dialog for batch app management"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Batch App Manager")
            dialog.resize(700, 600)
            dialog.setModal(True)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            notebook = QtWidgets.QTabWidget()
            main_layout.addWidget(notebook)

            install_frame = QtWidgets.QWidget()
            install_layout = QtWidgets.QVBoxLayout(install_frame)
            install_layout.addWidget(QtWidgets.QLabel("APK Files to Install:"))

            install_listbox = QtWidgets.QListWidget()
            install_layout.addWidget(install_listbox)

            install_btn_layout = QtWidgets.QHBoxLayout()
            install_layout.addLayout(install_btn_layout)

            def add_apks():
                files, _ = QtWidgets.QFileDialog.getOpenFileNames(
                    self,
                    "Select APK files",
                    "",
                    "Android Package (*.apk)",
                )
                for f in files:
                    install_listbox.addItem(f)

            def remove_apks():
                for item in install_listbox.selectedItems():
                    install_listbox.takeItem(install_listbox.row(item))

            def clear_apks():
                install_listbox.clear()

            add_btn = QtWidgets.QPushButton("Add APKs")
            remove_btn = QtWidgets.QPushButton("Remove")
            clear_btn = QtWidgets.QPushButton("Clear")
            add_btn.clicked.connect(add_apks)
            remove_btn.clicked.connect(remove_apks)
            clear_btn.clicked.connect(clear_apks)
            install_btn_layout.addWidget(add_btn)
            install_btn_layout.addWidget(remove_btn)
            install_btn_layout.addWidget(clear_btn)

            install_output = QtWidgets.QPlainTextEdit()
            install_output.setReadOnly(True)
            install_output.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            install_layout.addWidget(install_output)

            install_progress = QtWidgets.QProgressBar()
            install_layout.addWidget(install_progress)

            def install_apks():
                apks = [install_listbox.item(i).text() for i in range(install_listbox.count())]
                if not apks:
                    QtWidgets.QMessageBox.critical(self, "Error", "No APKs selected")
                    return

                install_output.clear()
                total = len(apks)

                def run_installation():
                    for i, apk in enumerate(apks):
                        progress = ((i + 1) / total) * 100
                        QtCore.QTimer.singleShot(
                            0, lambda p=progress: install_progress.setValue(int(p))
                        )

                        filename = os.path.basename(apk)
                        QtCore.QTimer.singleShot(
                            0, lambda f=filename: install_output.appendPlainText(f"Installing {f}...")
                        )

                        try:
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "install", "-r", apk],
                                capture_output=True, text=True, timeout=120
                            )

                            if "Success" in result.stdout:
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda f=filename: install_output.appendPlainText(
                                        f"  ✓ {f} installed"
                                    ),
                                )
                            else:
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda f=filename, e=result.stderr: install_output.appendPlainText(
                                        f"  ✗ {f} failed: {e}"
                                    ),
                                )

                        except Exception as e:
                            QtCore.QTimer.singleShot(
                                0,
                                lambda f=filename, err=str(e): install_output.appendPlainText(
                                    f"  ✗ {f} error: {err}"
                                ),
                            )

                    QtCore.QTimer.singleShot(
                        0, lambda: install_output.appendPlainText("\nBatch installation complete!")
                    )

                threading.Thread(target=run_installation, daemon=True).start()

            install_all_btn = QtWidgets.QPushButton("Install All")
            install_all_btn.clicked.connect(install_apks)
            install_layout.addWidget(install_all_btn)

            # Uninstall tab
            uninstall_frame = QtWidgets.QWidget()
            uninstall_layout = QtWidgets.QVBoxLayout(uninstall_frame)
            uninstall_layout.addWidget(QtWidgets.QLabel("Installed Packages:"))

            uninstall_listbox = QtWidgets.QListWidget()
            uninstall_listbox.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            uninstall_layout.addWidget(uninstall_listbox)

            def load_installed_packages():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    packages = sorted([line[8:] for line in result.stdout.strip().split('\n') if line.startswith('package:')])
                    def update_packages():
                        uninstall_listbox.clear()
                        for pkg in packages:
                            uninstall_listbox.addItem(pkg)

                    QtCore.QTimer.singleShot(0, update_packages)

            threading.Thread(target=load_installed_packages, daemon=True).start()

            uninstall_output = QtWidgets.QPlainTextEdit()
            uninstall_output.setReadOnly(True)
            uninstall_output.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            uninstall_layout.addWidget(uninstall_output)

            uninstall_progress = QtWidgets.QProgressBar()
            uninstall_layout.addWidget(uninstall_progress)

            def uninstall_packages():
                selection = uninstall_listbox.selectedItems()
                if not selection:
                    QtWidgets.QMessageBox.critical(self, "Error", "No packages selected")
                    return

                packages = [item.text() for item in selection]
                total = len(packages)

                def run_uninstallation():
                    for i, pkg in enumerate(packages):
                        progress = ((i + 1) / total) * 100
                        QtCore.QTimer.singleShot(
                            0, lambda p=progress: uninstall_progress.setValue(int(p))
                        )

                        QtCore.QTimer.singleShot(
                            0, lambda p=pkg: uninstall_output.appendPlainText(f"Uninstalling {p}...")
                        )

                        try:
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "uninstall", pkg],
                                capture_output=True, text=True, timeout=60
                            )

                            if "Success" in result.stdout:
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda p=pkg: uninstall_output.appendPlainText(
                                        f"  ✓ {p} uninstalled"
                                    ),
                                )
                            else:
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda p=pkg, e=result.stderr: uninstall_output.appendPlainText(
                                        f"  ✗ {p} failed: {e}"
                                    ),
                                )

                        except Exception as e:
                            QtCore.QTimer.singleShot(
                                0,
                                lambda p=pkg, err=str(e): uninstall_output.appendPlainText(
                                    f"  ✗ {p} error: {err}"
                                ),
                            )

                    QtCore.QTimer.singleShot(0, load_installed_packages)
                    QtCore.QTimer.singleShot(
                        0, lambda: uninstall_output.appendPlainText("\nBatch uninstallation complete!")
                    )

                threading.Thread(target=run_uninstallation, daemon=True).start()

            uninstall_btn_layout = QtWidgets.QHBoxLayout()
            refresh_btn = QtWidgets.QPushButton("Refresh")
            refresh_btn.clicked.connect(
                lambda: threading.Thread(target=load_installed_packages, daemon=True).start()
            )
            uninstall_btn = QtWidgets.QPushButton("Uninstall Selected")
            uninstall_btn.clicked.connect(uninstall_packages)
            uninstall_btn_layout.addWidget(refresh_btn)
            uninstall_btn_layout.addWidget(uninstall_btn)
            uninstall_layout.addLayout(uninstall_btn_layout)

            notebook.addTab(install_frame, "Batch Install")
            notebook.addTab(uninstall_frame, "Batch Uninstall")

            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            main_layout.addWidget(close_btn)

            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open batch app manager: {str(e)}"
            )

    def _logcat_screencap_dialog(self):
        """Combined logcat and screenshot/recording dialog"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Live Monitor")
            dialog.resize(900, 700)

            main_layout = QtWidgets.QVBoxLayout(dialog)
            splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
            main_layout.addWidget(splitter)

            logcat_frame = QtWidgets.QGroupBox("Live Logcat")
            logcat_layout = QtWidgets.QVBoxLayout(logcat_frame)

            logcat_controls = QtWidgets.QHBoxLayout()
            logcat_controls.addWidget(QtWidgets.QLabel("Filter:"))
            filter_entry = QtWidgets.QLineEdit()
            logcat_controls.addWidget(filter_entry)
            logcat_controls.addWidget(QtWidgets.QLabel("Level:"))
            level_combo = QtWidgets.QComboBox()
            level_combo.addItems(["V", "D", "I", "W", "E"])
            logcat_controls.addWidget(level_combo)
            logcat_layout.addLayout(logcat_controls)

            logcat_text = QtWidgets.QPlainTextEdit()
            logcat_text.setReadOnly(True)
            logcat_text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            logcat_layout.addWidget(logcat_text)

            logcat_running = {'value': False, 'process': None}

            def start_logcat():
                if logcat_running['value']:
                    return

                logcat_running['value'] = True
                logcat_text.clear()

                def read_logcat():
                    try:
                        cmd = [adb_cmd, "-s", serial, "logcat", f"*:{level_combo.currentText()}"]
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        logcat_running['process'] = process

                        for line in iter(process.stdout.readline, ''):
                            if not logcat_running['value']:
                                break

                            # Apply filter
                            filter_text = filter_entry.text().lower()
                            if not filter_text or filter_text in line.lower():
                                QtCore.QTimer.singleShot(
                                    0,
                                    lambda l=line: logcat_text.appendPlainText(l.rstrip("\n")),
                                )

                    except Exception as e:
                        pass

                threading.Thread(target=read_logcat, daemon=True).start()

            def stop_logcat():
                logcat_running['value'] = False
                if logcat_running['process']:
                    try:
                        logcat_running['process'].terminate()
                    except:
                        pass

            def clear_logcat():
                logcat_text.clear()

            logcat_btn_layout = QtWidgets.QHBoxLayout()
            start_btn = QtWidgets.QPushButton("Start")
            stop_btn = QtWidgets.QPushButton("Stop")
            clear_btn = QtWidgets.QPushButton("Clear")
            start_btn.clicked.connect(start_logcat)
            stop_btn.clicked.connect(stop_logcat)
            clear_btn.clicked.connect(clear_logcat)
            logcat_btn_layout.addWidget(start_btn)
            logcat_btn_layout.addWidget(stop_btn)
            logcat_btn_layout.addWidget(clear_btn)
            logcat_layout.addLayout(logcat_btn_layout)

            capture_frame = QtWidgets.QGroupBox("Capture")
            capture_layout = QtWidgets.QVBoxLayout(capture_frame)
            capture_controls = QtWidgets.QHBoxLayout()
            capture_layout.addLayout(capture_controls)

            def capture_screenshot():
                try:
                    import tempfile
                    import time

                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.png"
                    save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                        self,
                        "Save Screenshot",
                        filename,
                        "PNG files (*.png)",
                    )

                    if not save_path:
                        return

                    # Take screenshot
                    subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "screencap", "-p", "/sdcard/temp_screenshot.png"],
                        capture_output=True, timeout=10
                    )

                    # Pull to local
                    subprocess.run(
                        [adb_cmd, "-s", serial, "pull", "/sdcard/temp_screenshot.png", save_path],
                        capture_output=True, timeout=10
                    )

                    # Cleanup
                    subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "rm", "/sdcard/temp_screenshot.png"],
                        capture_output=True, timeout=5
                    )

                    QtWidgets.QMessageBox.information(
                        self, "Saved", f"Screenshot saved to:\n{save_path}"
                    )

                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self, "Error", f"Failed to capture screenshot: {str(e)}"
                    )

            screenshot_btn = QtWidgets.QPushButton("Screenshot")
            screenshot_btn.clicked.connect(capture_screenshot)
            capture_controls.addWidget(screenshot_btn)

            def on_closing():
                stop_logcat()
                dialog.close()

            dialog.finished.connect(lambda _: on_closing())

            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(on_closing)
            main_layout.addWidget(close_btn)

            splitter.addWidget(logcat_frame)
            splitter.addWidget(capture_frame)
            dialog.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to open live monitor: {str(e)}"
            )
