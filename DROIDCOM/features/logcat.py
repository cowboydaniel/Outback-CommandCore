"""
DROIDCOM - Logcat Feature Module
Handles logcat viewing and filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import re
import time

from ..constants import IS_WINDOWS


class LogcatMixin:
    """Mixin class providing logcat viewing functionality."""

    def view_logcat(self):
        """View logcat from the connected Android device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        self._run_in_thread(self._view_logcat_task)

    def _view_logcat_task(self):
        """Worker thread to open a logcat viewer"""
        try:
            self.update_status("Opening logcat viewer...")
            self.log_message("Opening logcat viewer...")

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
                self.update_status("Failed to open logcat")
                return

            self.after(0, lambda: self._show_logcat_window(serial, adb_cmd))

        except Exception as e:
            self.log_message(f"Error opening logcat: {str(e)}")
            self.update_status("Failed to open logcat")

    def _show_logcat_window(self, serial, adb_cmd):
        """Show the logcat window"""
        try:
            logcat_window = tk.Toplevel(self)
            logcat_window.title("Android Logcat Viewer")
            logcat_window.geometry("800x600")
            logcat_window.minsize(600, 400)

            x_pos = (self.winfo_screenwidth() - 800) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            logcat_window.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(logcat_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Filter frame
            filter_frame = ttk.Frame(main_frame)
            filter_frame.pack(fill="x", pady=(0, 10))

            ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=(0, 5))

            filter_var = tk.StringVar()
            filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=30)
            filter_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

            ttk.Label(filter_frame, text="Log Level:").pack(side="left", padx=(10, 5))

            level_var = tk.StringVar(value="VERBOSE")
            level_combo = ttk.Combobox(filter_frame, textvariable=level_var, width=10)
            level_combo['values'] = ("VERBOSE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL")
            level_combo.pack(side="left", padx=(0, 10))

            clear_btn = ttk.Button(filter_frame, text="Clear", width=8)
            clear_btn.pack(side="right", padx=5)

            apply_btn = ttk.Button(filter_frame, text="Apply Filter", width=12)
            apply_btn.pack(side="right", padx=5)

            # Log frame
            log_frame = ttk.Frame(main_frame)
            log_frame.pack(fill="both", expand=True, pady=(0, 10))

            log_text = tk.Text(log_frame, wrap=tk.NONE, width=80, height=20)
            log_text.pack(side="left", fill="both", expand=True)

            v_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
            v_scrollbar.pack(side="right", fill="y")
            log_text.config(yscrollcommand=v_scrollbar.set)

            h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=log_text.xview)
            h_scrollbar.pack(side="bottom", fill="x", before=log_frame)
            log_text.config(xscrollcommand=h_scrollbar.set)

            # Configure tags for log levels
            log_text.tag_configure("VERBOSE", foreground="gray")
            log_text.tag_configure("DEBUG", foreground="black")
            log_text.tag_configure("INFO", foreground="green")
            log_text.tag_configure("WARN", foreground="orange")
            log_text.tag_configure("ERROR", foreground="red")
            log_text.tag_configure("FATAL", foreground="purple", font=("Arial", 10, "bold"))
            log_text.tag_configure("timestamp", foreground="blue")

            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(0, 5))

            save_btn = ttk.Button(
                button_frame, text="Save Log",
                command=lambda: self._save_logcat(log_text)
            )
            save_btn.pack(side="left", padx=5)

            close_btn = ttk.Button(
                button_frame, text="Close",
                command=lambda: self._close_logcat(logcat_window, serial, adb_cmd)
            )
            close_btn.pack(side="right", padx=5)

            # Initial state
            log_text.insert(tk.END, "Loading logcat... Please wait.\n")
            log_text.config(state="disabled")

            # Store references
            logcat_window.log_text = log_text
            logcat_window.filter_var = filter_var
            logcat_window.level_var = level_var

            # Start logcat thread
            logcat_thread = threading.Thread(
                target=self._run_logcat,
                args=(serial, adb_cmd, logcat_window, log_text, filter_var, level_var)
            )
            logcat_thread.daemon = True
            logcat_window.logcat_thread = logcat_thread
            logcat_thread.start()

            # Configure buttons
            clear_btn.config(command=lambda: self._clear_logcat(log_text))
            apply_btn.config(command=lambda: self._apply_logcat_filter(serial, adb_cmd, logcat_window))

            # Update title with device info
            model = self.device_info.get('model', 'Unknown')
            logcat_window.title(f"Android Logcat - {model} ({serial})")

            logcat_window.protocol("WM_DELETE_WINDOW", lambda: self._close_logcat(logcat_window, serial, adb_cmd))

        except Exception as e:
            self.log_message(f"Error showing logcat window: {str(e)}")
            messagebox.showerror("Logcat Error", f"Failed to show logcat window: {str(e)}")

    def _run_logcat(self, serial, adb_cmd, window, log_text, filter_var, level_var):
        """Run logcat in a separate thread"""
        try:
            process = None

            current_filter = filter_var.get()
            current_level = level_var.get()

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

            self.after(0, lambda: self._clear_logcat(log_text))

            for line in iter(process.stdout.readline, ''):
                if not hasattr(window, 'winfo_exists') or not window.winfo_exists():
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

                if hasattr(window, 'winfo_exists') and window.winfo_exists():
                    window.after(0, lambda l=line, t=tag: self._append_logcat_line(log_text, l, t))

            if process.poll() is not None:
                status = process.poll()
                if hasattr(window, 'winfo_exists') and window.winfo_exists():
                    window.after(0, lambda: self._append_logcat_line(
                        log_text, f"\nLogcat process ended (status {status}). Please close and reopen the viewer.\n", "ERROR"
                    ))

        except Exception as e:
            self.log_message(f"Error in logcat thread: {str(e)}")

            if hasattr(window, 'winfo_exists') and window.winfo_exists():
                window.after(0, lambda: self._append_logcat_line(
                    log_text, f"\nError: {str(e)}\n", "ERROR"
                ))

        finally:
            if process and process.poll() is None:
                try:
                    process.terminate()
                except:
                    pass

    def _append_logcat_line(self, log_text, line, tag):
        """Append a line to the logcat text widget"""
        try:
            if not log_text.winfo_exists():
                return

            log_text.config(state="normal")
            log_text.insert(tk.END, line, tag)
            log_text.see(tk.END)
            log_text.config(state="disabled")

        except Exception as e:
            self.log_message(f"Error appending to logcat: {str(e)}")

    def _clear_logcat(self, log_text):
        """Clear the logcat display"""
        try:
            log_text.config(state="normal")
            log_text.delete(1.0, tk.END)
            log_text.config(state="disabled")
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
                args=(serial, adb_cmd, window, window.log_text, window.filter_var, window.level_var)
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
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Logcat Output"
            )

            if not file_path:
                return

            log_text.config(state="normal")
            contents = log_text.get(1.0, tk.END)
            log_text.config(state="disabled")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(contents)

            self.log_message(f"Logcat saved to {file_path}")
            messagebox.showinfo("Save Complete", f"Logcat output saved to:\n{file_path}")

        except Exception as e:
            self.log_message(f"Error saving logcat: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save logcat: {str(e)}")

    def _close_logcat(self, window, serial, adb_cmd):
        """Close the logcat window and terminate the logcat process"""
        try:
            if hasattr(window, 'logcat_process') and window.logcat_process:
                if window.logcat_process.poll() is None:
                    window.logcat_process.terminate()
            window.destroy()
        except Exception as e:
            self.log_message(f"Error closing logcat: {str(e)}")
