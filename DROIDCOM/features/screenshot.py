"""
DROIDCOM - Screenshot Feature Module
Handles screenshot capture and display functionality.
"""

from ..ui.qt_compat import tk
from ..ui.qt_compat import ttk, messagebox, filedialog
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
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
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
            self.after(0, lambda: self._show_screenshot(screenshot_file))

        except Exception as e:
            self.log_message(f"Error taking screenshot: {str(e)}")
            self.update_status("Screenshot failed")
            messagebox.showerror("Screenshot Error", f"Failed to take screenshot: {str(e)}")

    def _show_screenshot(self, screenshot_path):
        """Show the screenshot in a new window"""
        try:
            screenshot_window = tk.Toplevel(self)
            screenshot_window.title(f"Android Screenshot - {os.path.basename(screenshot_path)}")

            # Load the image
            img = tk.PhotoImage(file=screenshot_path)

            # Calculate window size
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)

            window_width = min(img.width(), max_width)
            window_height = min(img.height(), max_height)

            screenshot_window.geometry(f"{window_width}x{window_height}")

            # Center the window
            x_pos = (screen_width - window_width) // 2
            y_pos = (screen_height - window_height) // 2
            screenshot_window.geometry(f"+{x_pos}+{y_pos}")

            # Create canvas
            canvas = tk.Canvas(screenshot_window, width=window_width, height=window_height)
            canvas.pack(side="left", fill="both", expand=True)

            # Add scrollbars if needed
            if img.width() > window_width or img.height() > window_height:
                h_scrollbar = tk.Scrollbar(screenshot_window, orient="horizontal", command=canvas.xview)
                h_scrollbar.pack(side="bottom", fill="x")

                v_scrollbar = tk.Scrollbar(screenshot_window, orient="vertical", command=canvas.yview)
                v_scrollbar.pack(side="right", fill="y")

                canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

            # Display the image
            canvas.create_image(0, 0, anchor="nw", image=img)
            canvas.config(scrollregion=canvas.bbox("all"))
            canvas.image = img

            # Button frame
            button_frame = ttk.Frame(screenshot_window)
            button_frame.pack(side="bottom", fill="x", padx=10, pady=5)

            # Open folder button
            screenshots_dir = os.path.dirname(screenshot_path)
            open_btn = ttk.Button(
                button_frame, text="Open Folder",
                command=lambda: self._open_screenshots_folder(screenshots_dir)
            )
            open_btn.pack(side="left", padx=5)

            # Save as button
            save_btn = ttk.Button(
                button_frame, text="Save As",
                command=lambda: self._save_screenshot_as(screenshot_path)
            )
            save_btn.pack(side="left", padx=5)

            # Close button
            close_btn = ttk.Button(
                button_frame, text="Close",
                command=screenshot_window.destroy
            )
            close_btn.pack(side="right", padx=5)

        except Exception as e:
            self.log_message(f"Error displaying screenshot: {str(e)}")
            messagebox.showerror("Display Error", f"Failed to display screenshot: {str(e)}")

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
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=os.path.basename(source_path)
            )

            if save_path:
                shutil.copy2(source_path, save_path)
                self.log_message(f"Screenshot saved to: {save_path}")
        except Exception as e:
            self.log_message(f"Error saving screenshot: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save screenshot: {str(e)}")
