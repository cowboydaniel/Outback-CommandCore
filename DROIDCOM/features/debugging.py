"""
DROIDCOM - Debugging Feature Module
Handles debugging features like bug reports, crash dumps, ANR traces.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
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
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Generate Bug Report")
            dialog.geometry("500x300")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 500) // 2
            y_pos = (self.winfo_screenheight() - 300) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Bug Report Generation", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            ttk.Label(main_frame, text="This will generate a full bug report from the device.\n"
                     "The report may take several minutes to generate.").pack(pady=10)

            # Output directory
            output_frame = ttk.Frame(main_frame)
            output_frame.pack(fill="x", pady=10)

            ttk.Label(output_frame, text="Save to:").pack(side="left", padx=(0, 5))
            output_var = tk.StringVar(value=os.path.expanduser("~/Desktop"))
            output_entry = ttk.Entry(output_frame, textvariable=output_var, width=40)
            output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

            def browse_directory():
                directory = filedialog.askdirectory()
                if directory:
                    output_var.set(directory)

            ttk.Button(output_frame, text="Browse", command=browse_directory).pack(side="left")

            # Progress
            status_var = tk.StringVar(value="Ready to generate")
            status_label = ttk.Label(main_frame, textvariable=status_var)
            status_label.pack(pady=5)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, mode='indeterminate')
            progress_bar.pack(fill="x", pady=10)

            def generate_report():
                output_dir = output_var.get()
                if not os.path.exists(output_dir):
                    messagebox.showerror("Error", "Output directory does not exist")
                    return

                status_var.set("Generating bug report...")
                progress_bar.start()

                def report_thread():
                    try:
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = os.path.join(output_dir, f"bugreport_{timestamp}.zip")

                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "bugreport", filename],
                            capture_output=True, text=True, timeout=600
                        )

                        dialog.after(0, lambda: progress_bar.stop())

                        if result.returncode == 0:
                            dialog.after(0, lambda: [
                                status_var.set("Bug report generated successfully!"),
                                messagebox.showinfo("Success", f"Bug report saved to:\n{filename}")
                            ])
                        else:
                            dialog.after(0, lambda: [
                                status_var.set("Failed to generate bug report"),
                                messagebox.showerror("Error", f"Failed to generate bug report:\n{result.stderr}")
                            ])

                    except subprocess.TimeoutExpired:
                        dialog.after(0, lambda: [
                            progress_bar.stop(),
                            status_var.set("Timeout"),
                            messagebox.showerror("Timeout", "Bug report generation timed out")
                        ])
                    except Exception as e:
                        dialog.after(0, lambda: [
                            progress_bar.stop(),
                            status_var.set(f"Error: {str(e)}"),
                            messagebox.showerror("Error", str(e))
                        ])

                threading.Thread(target=report_thread, daemon=True).start()

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Generate", command=generate_report).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open bug report dialog: {str(e)}")

    def _show_anr_traces(self):
        """Show ANR traces from the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("ANR Traces")
            dialog.geometry("800x600")

            x_pos = (self.winfo_screenwidth() - 800) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=30, width=95)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            status_var = tk.StringVar(value="Loading...")
            status_label = ttk.Label(dialog, textvariable=status_var)
            status_label.pack(pady=5)

            def load_traces():
                try:
                    # Try to get ANR traces
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "cat /data/anr/traces.txt 2>/dev/null"],
                        capture_output=True, text=True, timeout=30
                    )

                    dialog.after(0, lambda: text_widget.delete(1.0, tk.END))

                    if result.returncode == 0 and result.stdout.strip():
                        dialog.after(0, lambda: [
                            text_widget.insert(tk.END, "===== ANR Traces =====\n\n"),
                            text_widget.insert(tk.END, result.stdout[:50000]),
                            status_var.set("ANR traces loaded")
                        ])
                    else:
                        # Try alternative location
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "ls /data/anr/ 2>/dev/null"],
                            capture_output=True, text=True, timeout=10
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            dialog.after(0, lambda: [
                                text_widget.insert(tk.END, "===== ANR Files =====\n\n"),
                                text_widget.insert(tk.END, result.stdout),
                                status_var.set("ANR files found")
                            ])
                        else:
                            dialog.after(0, lambda: [
                                text_widget.insert(tk.END, "No ANR traces found.\n\n"
                                                  "ANR traces may not be accessible without root access."),
                                status_var.set("No traces found")
                            ])

                except Exception as e:
                    dialog.after(0, lambda: [
                        text_widget.insert(tk.END, f"Error: {str(e)}"),
                        status_var.set("Error loading traces")
                    ])

            threading.Thread(target=load_traces, daemon=True).start()

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: threading.Thread(target=load_traces, daemon=True).start()
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show ANR traces: {str(e)}")

    def _refresh_anr_traces(self, text_widget, serial, adb_cmd, status_var=None):
        """Refresh ANR traces"""
        try:
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cat /data/anr/traces.txt"],
                capture_output=True, text=True, timeout=30
            )

            text_widget.delete(1.0, tk.END)

            if result.returncode == 0 and result.stdout.strip():
                text_widget.insert(tk.END, "===== ANR Traces =====\n\n")
                text_widget.insert(tk.END, result.stdout[:50000])
                if status_var:
                    status_var.set("ANR traces loaded")
            else:
                text_widget.insert(tk.END, "No ANR traces available")
                if status_var:
                    status_var.set("No traces")

        except Exception as e:
            text_widget.insert(tk.END, f"Error: {str(e)}")

    def _show_crash_dumps(self):
        """Show crash dumps from the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Crash Dumps")
            dialog.geometry("900x600")

            x_pos = (self.winfo_screenwidth() - 900) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            # Paned window
            paned = ttk.PanedWindow(dialog, orient="horizontal")
            paned.pack(fill="both", expand=True, padx=10, pady=10)

            # List frame
            list_frame = ttk.Frame(paned)
            paned.add(list_frame, weight=1)

            ttk.Label(list_frame, text="Crash Files:").pack(anchor="w")

            list_scrollbar = ttk.Scrollbar(list_frame)
            list_scrollbar.pack(side="right", fill="y")

            crash_listbox = tk.Listbox(list_frame, yscrollcommand=list_scrollbar.set)
            crash_listbox.pack(fill="both", expand=True)
            list_scrollbar.config(command=crash_listbox.yview)

            # Detail frame
            detail_frame = ttk.Frame(paned)
            paned.add(detail_frame, weight=2)

            ttk.Label(detail_frame, text="Crash Details:").pack(anchor="w")

            detail_widget = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=25, width=60)
            detail_widget.pack(fill="both", expand=True)

            status_var = tk.StringVar(value="Loading...")
            status_label = ttk.Label(dialog, textvariable=status_var)
            status_label.pack(pady=5)

            def load_crash_list():
                try:
                    # Check for dropbox crashes
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "ls /data/system/dropbox/ 2>/dev/null | head -50"],
                        capture_output=True, text=True, timeout=10
                    )

                    dialog.after(0, lambda: crash_listbox.delete(0, tk.END))

                    if result.returncode == 0 and result.stdout.strip():
                        files = result.stdout.strip().split('\n')
                        for f in files:
                            dialog.after(0, lambda file=f: crash_listbox.insert(tk.END, file))
                        dialog.after(0, lambda: status_var.set(f"Found {len(files)} crash files"))
                    else:
                        # Try tombstones
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "ls /data/tombstones/ 2>/dev/null"],
                            capture_output=True, text=True, timeout=10
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            files = result.stdout.strip().split('\n')
                            for f in files:
                                dialog.after(0, lambda file=f: crash_listbox.insert(tk.END, f"tombstones/{file}"))
                            dialog.after(0, lambda: status_var.set(f"Found {len(files)} tombstone files"))
                        else:
                            dialog.after(0, lambda: status_var.set("No crash files found"))

                except Exception as e:
                    dialog.after(0, lambda: status_var.set(f"Error: {str(e)}"))

            def on_crash_select(event):
                selection = crash_listbox.curselection()
                if not selection:
                    return

                filename = crash_listbox.get(selection[0])

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

                        dialog.after(0, lambda: [
                            detail_widget.delete(1.0, tk.END),
                            detail_widget.insert(tk.END, result.stdout if result.stdout else "Unable to read file")
                        ])

                    except Exception as e:
                        dialog.after(0, lambda: detail_widget.insert(tk.END, f"Error: {str(e)}"))

                threading.Thread(target=load_detail, daemon=True).start()

            crash_listbox.bind('<<ListboxSelect>>', on_crash_select)

            threading.Thread(target=load_crash_list, daemon=True).start()

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: threading.Thread(target=load_crash_list, daemon=True).start()
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show crash dumps: {str(e)}")

    def _show_system_log(self):
        """Show system log (dmesg)"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("System Log")
            dialog.geometry("900x600")

            x_pos = (self.winfo_screenwidth() - 900) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            # Filter frame
            filter_frame = ttk.Frame(dialog)
            filter_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(filter_frame, text="Log Type:").pack(side="left", padx=(0, 5))

            log_type_var = tk.StringVar(value="dmesg")
            log_type_combo = ttk.Combobox(filter_frame, textvariable=log_type_var, values=[
                "dmesg", "kernel", "main", "system", "crash", "events"
            ], width=15)
            log_type_combo.pack(side="left", padx=5)

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.NONE, height=30, width=110)
            text_widget.pack(fill="both", expand=True, padx=10, pady=5)

            # Add horizontal scrollbar
            h_scroll = ttk.Scrollbar(dialog, orient="horizontal", command=text_widget.xview)
            h_scroll.pack(fill="x", padx=10)
            text_widget.config(xscrollcommand=h_scroll.set)

            def load_log():
                log_type = log_type_var.get()

                try:
                    if log_type == "dmesg":
                        cmd = [adb_cmd, "-s", serial, "shell", "dmesg"]
                    elif log_type == "kernel":
                        cmd = [adb_cmd, "-s", serial, "shell", "cat /proc/kmsg 2>/dev/null || dmesg"]
                    else:
                        cmd = [adb_cmd, "-s", serial, "logcat", "-b", log_type, "-d"]

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    dialog.after(0, lambda: [
                        text_widget.delete(1.0, tk.END),
                        text_widget.insert(tk.END, result.stdout if result.stdout else "No log data available")
                    ])

                except Exception as e:
                    dialog.after(0, lambda: text_widget.insert(tk.END, f"Error: {str(e)}"))

            ttk.Button(filter_frame, text="Load", command=lambda: threading.Thread(target=load_log, daemon=True).start()).pack(side="left", padx=5)

            def save_log():
                content = text_widget.get(1.0, tk.END)
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")]
                )
                if file_path:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    messagebox.showinfo("Saved", f"Log saved to:\n{file_path}")

            ttk.Button(filter_frame, text="Save", command=save_log).pack(side="left", padx=5)
            ttk.Button(filter_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            # Auto-load dmesg
            threading.Thread(target=load_log, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show system log: {str(e)}")

    def _start_screen_recording(self):
        """Start screen recording on the device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Screen Recording")
            dialog.geometry("400x300")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 400) // 2
            y_pos = (self.winfo_screenheight() - 300) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Screen Recording", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            # Time limit
            time_frame = ttk.Frame(main_frame)
            time_frame.pack(fill="x", pady=5)

            ttk.Label(time_frame, text="Time Limit (seconds):").pack(side="left")
            time_var = tk.IntVar(value=60)
            time_spinbox = ttk.Spinbox(time_frame, from_=10, to=180, textvariable=time_var, width=10)
            time_spinbox.pack(side="left", padx=10)

            # Output path
            output_frame = ttk.Frame(main_frame)
            output_frame.pack(fill="x", pady=5)

            ttk.Label(output_frame, text="Save to:").pack(side="left")
            output_var = tk.StringVar(value=os.path.expanduser("~/Desktop"))
            output_entry = ttk.Entry(output_frame, textvariable=output_var, width=30)
            output_entry.pack(side="left", padx=5, fill="x", expand=True)

            def browse():
                directory = filedialog.askdirectory()
                if directory:
                    output_var.set(directory)

            ttk.Button(output_frame, text="Browse", command=browse).pack(side="left")

            # Status
            status_var = tk.StringVar(value="Ready")
            status_label = ttk.Label(main_frame, textvariable=status_var)
            status_label.pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, mode='indeterminate')
            progress_bar.pack(fill="x", pady=5)

            def start_recording():
                output_dir = output_var.get()
                time_limit = time_var.get()

                if not os.path.exists(output_dir):
                    messagebox.showerror("Error", "Output directory does not exist")
                    return

                status_var.set("Recording...")
                progress_bar.start()

                def record_thread():
                    try:
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        device_path = f"/sdcard/recording_{timestamp}.mp4"
                        local_path = os.path.join(output_dir, f"recording_{timestamp}.mp4")

                        # Start recording
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "screenrecord", "--time-limit", str(time_limit), device_path],
                            capture_output=True, text=True, timeout=time_limit + 10
                        )

                        # Pull the file
                        subprocess.run(
                            [adb_cmd, "-s", serial, "pull", device_path, local_path],
                            capture_output=True, text=True, timeout=60
                        )

                        # Clean up
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "rm", device_path],
                            capture_output=True, text=True, timeout=5
                        )

                        dialog.after(0, lambda: [
                            progress_bar.stop(),
                            status_var.set("Recording saved!"),
                            messagebox.showinfo("Success", f"Recording saved to:\n{local_path}")
                        ])

                    except subprocess.TimeoutExpired:
                        dialog.after(0, lambda: [
                            progress_bar.stop(),
                            status_var.set("Recording complete")
                        ])
                    except Exception as e:
                        dialog.after(0, lambda: [
                            progress_bar.stop(),
                            status_var.set(f"Error: {str(e)}")
                        ])

                threading.Thread(target=record_thread, daemon=True).start()

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Start Recording", command=start_recording).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open screen recording dialog: {str(e)}")
