"""
DROIDCOM - Screenshot Feature Module
Handles screenshot capture and display functionality.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import subprocess
import os
import shutil
import time
import platform

from ..constants import IS_WINDOWS


class ScreenshotMixin:
    """Mixin class providing screenshot functionality."""

    def take_screenshot(self):
        """Take a screenshot of the connected Android device"""
        if not self.device_connected:
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return

        self._run_in_thread(self._take_screenshot_task)

    def _take_screenshot_task(self):
        """Worker thread to take a screenshot"""
        try:
            self.update_status("Taking screenshot...")
            self.log_message("Taking screenshot of the connected Android device...")

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
                self.update_status("Screenshot failed")
                return

            # Create screenshots directory
            screenshots_dir = os.path.join(os.path.expanduser("~"), "Nest", "Screenshots", "Android")
            os.makedirs(screenshots_dir, exist_ok=True)

            # Generate filename
            device_model = self.device_info.get('model', 'Android').replace(' ', '_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_file = os.path.join(screenshots_dir, f"{device_model}_{timestamp}.png")

            self.log_message(f"Saving screenshot to: {screenshot_file}")

            # Take screenshot on device
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.log_message(f"Failed to take screenshot: {result.stderr.strip()}")
                self.update_status("Screenshot failed")
                return

            # Pull screenshot from device
            pull_result = subprocess.run(
                [adb_cmd, '-s', serial, 'pull', '/sdcard/screenshot.png', screenshot_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if pull_result.returncode != 0:
                self.log_message(f"Failed to transfer screenshot: {pull_result.stderr.strip()}")
                self.update_status("Screenshot transfer failed")
                return

            # Clean up temporary file on device
            subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'rm', '/sdcard/screenshot.png'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.log_message("Screenshot captured successfully")
            self.update_status("Screenshot saved")

            # Show the screenshot
            QtCore.QTimer.singleShot(0, lambda: self._show_screenshot(screenshot_file))

        except Exception as e:
            self.log_message(f"Error taking screenshot: {str(e)}")
            self.update_status("Screenshot failed")
            QtWidgets.QMessageBox.critical(
                self, "Screenshot Error", f"Failed to take screenshot: {str(e)}"
            )

    def _show_screenshot(self, screenshot_path):
        """Show the screenshot in a new window"""
        try:
            screenshot_window = QtWidgets.QDialog(self)
            screenshot_window.setWindowTitle(
                f"Android Screenshot - {os.path.basename(screenshot_path)}"
            )

            pixmap = QtGui.QPixmap(screenshot_path)
            if pixmap.isNull():
                raise ValueError("Failed to load screenshot image.")

            screen_geom = QtWidgets.QApplication.primaryScreen().availableGeometry()
            max_width = int(screen_geom.width() * 0.8)
            max_height = int(screen_geom.height() * 0.8)

            window_width = min(pixmap.width(), max_width)
            window_height = min(pixmap.height(), max_height)
            screenshot_window.resize(window_width, window_height)

            main_layout = QtWidgets.QVBoxLayout(screenshot_window)

            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidgetResizable(True)
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(QtCore.Qt.AlignCenter)
            scroll_area.setWidget(image_label)
            main_layout.addWidget(scroll_area)

            button_layout = QtWidgets.QHBoxLayout()
            screenshots_dir = os.path.dirname(screenshot_path)
            open_btn = QtWidgets.QPushButton("Open Folder")
            open_btn.clicked.connect(lambda: self._open_screenshots_folder(screenshots_dir))
            save_btn = QtWidgets.QPushButton("Save As")
            save_btn.clicked.connect(lambda: self._save_screenshot_as(screenshot_path))
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(screenshot_window.close)
            button_layout.addWidget(open_btn)
            button_layout.addWidget(save_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            main_layout.addLayout(button_layout)

            screenshot_window.show()

        except Exception as e:
            self.log_message(f"Error displaying screenshot: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Display Error", f"Failed to display screenshot: {str(e)}"
            )

    def _open_screenshots_folder(self, folder_path):
        """Open the screenshots folder in the file explorer"""
        try:
            if IS_WINDOWS:
                os.startfile(folder_path)
            else:
                if platform.system().lower() == 'darwin':
                    subprocess.run(['open', folder_path])
                else:
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            self.log_message(f"Error opening screenshots folder: {str(e)}")

    def _save_screenshot_as(self, source_path):
        """Save the screenshot to another location"""
        try:
            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Screenshot",
                os.path.basename(source_path),
                "PNG files (*.png);;All files (*.*)",
            )

            if save_path:
                shutil.copy2(source_path, save_path)
                self.log_message(f"Screenshot saved to: {save_path}")
        except Exception as e:
            self.log_message(f"Error saving screenshot: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Save Error", f"Failed to save screenshot: {str(e)}"
            )
