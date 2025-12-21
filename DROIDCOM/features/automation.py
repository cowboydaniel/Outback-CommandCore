"""
DROIDCOM - Automation Feature Module
Handles automation features like shell scripts, batch operations, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
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
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Run Shell Script")
            dialog.geometry("700x500")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 700) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Run Shell Script", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            # Script file selection
            file_frame = ttk.Frame(main_frame)
            file_frame.pack(fill="x", pady=5)

            ttk.Label(file_frame, text="Script file:").pack(side="left")
            file_var = tk.StringVar()
            file_entry = ttk.Entry(file_frame, textvariable=file_var, width=50)
            file_entry.pack(side="left", padx=5, fill="x", expand=True)

            def browse_script():
                file_path = filedialog.askopenfilename(
                    title="Select Script",
                    filetypes=[("Shell scripts", "*.sh"), ("All files", "*.*")]
                )
                if file_path:
                    file_var.set(file_path)
                    # Load script content
                    try:
                        with open(file_path, 'r') as f:
                            script_text.delete(1.0, tk.END)
                            script_text.insert(tk.END, f.read())
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to read script: {str(e)}")

            ttk.Button(file_frame, text="Browse", command=browse_script).pack(side="left")

            # Script content
            ttk.Label(main_frame, text="Script content:").pack(anchor="w", pady=(10, 5))

            script_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=70)
            script_text.pack(fill="both", expand=True, pady=5)

            # Output
            ttk.Label(main_frame, text="Output:").pack(anchor="w", pady=(10, 5))

            output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=8, width=70)
            output_text.pack(fill="both", expand=True, pady=5)

            def run_script():
                script = script_text.get(1.0, tk.END).strip()
                if not script:
                    messagebox.showerror("Error", "Please enter a script")
                    return

                output_text.delete(1.0, tk.END)

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

                        emit_ui(self, lambda: [
                            append_text(output_text, "=== STDOUT ===\n"),
                            append_text(output_text, result.stdout or "(empty)\n"),
                            append_text(output_text, "\n=== STDERR ===\n"),
                            append_text(output_text, result.stderr or "(empty)\n"),
                            append_text(output_text, f"\n=== Return code: {result.returncode} ===\n")
                        ])

                    except Exception as e:
                        emit_ui(self, lambda: append_text(output_text, f"Error: {str(e)}"))

                threading.Thread(target=execute_script, daemon=True).start()

            def save_script():
                script = script_text.get(1.0, tk.END).strip()
                if not script:
                    return

                file_path = filedialog.asksaveasfilename(
                    defaultextension=".sh",
                    filetypes=[("Shell scripts", "*.sh"), ("All files", "*.*")]
                )
                if file_path:
                    with open(file_path, 'w') as f:
                        f.write(script)
                    messagebox.showinfo("Saved", f"Script saved to:\n{file_path}")

            def clear_script():
                script_text.delete(1.0, tk.END)
                clear_text(output_text)

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Run", command=run_script).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Save", command=save_script).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Clear", command=clear_script).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open shell script dialog: {str(e)}")

    def _batch_app_manager_dialog(self):
        """Show dialog for batch app management"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Batch App Manager")
            dialog.geometry("700x600")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 700) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill="both", expand=True)

            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill="both", expand=True)

            # Install tab
            install_frame = ttk.Frame(notebook, padding=10)
            notebook.add(install_frame, text="Batch Install")

            ttk.Label(install_frame, text="APK Files to Install:").pack(anchor="w")

            install_list_frame = ttk.Frame(install_frame)
            install_list_frame.pack(fill="both", expand=True, pady=5)

            install_scrollbar = ttk.Scrollbar(install_list_frame)
            install_scrollbar.pack(side="right", fill="y")

            install_listbox = tk.Listbox(install_list_frame, yscrollcommand=install_scrollbar.set)
            install_listbox.pack(fill="both", expand=True)
            install_scrollbar.config(command=install_listbox.yview)

            install_btn_frame = ttk.Frame(install_frame)
            install_btn_frame.pack(fill="x", pady=5)

            def add_apks():
                files = filedialog.askopenfilenames(
                    title="Select APK files",
                    filetypes=[("Android Package", "*.apk")]
                )
                for f in files:
                    install_listbox.insert(tk.END, f)

            def remove_apks():
                selection = install_listbox.curselection()
                for i in reversed(selection):
                    install_listbox.delete(i)

            def clear_apks():
                install_listbox.delete(0, tk.END)

            ttk.Button(install_btn_frame, text="Add APKs", command=add_apks).pack(side="left", padx=5)
            ttk.Button(install_btn_frame, text="Remove", command=remove_apks).pack(side="left", padx=5)
            ttk.Button(install_btn_frame, text="Clear", command=clear_apks).pack(side="left", padx=5)

            install_output = scrolledtext.ScrolledText(install_frame, wrap=tk.WORD, height=8)
            install_output.pack(fill="both", expand=True, pady=5)

            install_progress = ttk.Progressbar(install_frame, mode='determinate')
            install_progress.pack(fill="x", pady=5)

            def install_apks():
                apks = list(install_listbox.get(0, tk.END))
                if not apks:
                    messagebox.showerror("Error", "No APKs selected")
                    return

                install_output.delete(1.0, tk.END)
                total = len(apks)

                def run_installation():
                    for i, apk in enumerate(apks):
                        progress = ((i + 1) / total) * 100
                        emit_ui(self, lambda p=progress: set_progress(install_progress, p))

                        filename = os.path.basename(apk)
                        emit_ui(self, lambda f=filename: append_text(
                            install_output, f"Installing {f}...\n"
                        ))

                        try:
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "install", "-r", apk],
                                capture_output=True, text=True, timeout=120
                            )

                            if "Success" in result.stdout:
                                emit_ui(self, lambda f=filename: append_text(
                                    install_output, f"  ✓ {f} installed\n"
                                ))
                            else:
                                emit_ui(self, lambda f=filename, e=result.stderr: append_text(
                                    install_output, f"  ✗ {f} failed: {e}\n"
                                ))

                        except Exception as e:
                            emit_ui(self, lambda f=filename, err=str(e): append_text(
                                install_output, f"  ✗ {f} error: {err}\n"
                            ))

                    emit_ui(self, lambda: append_text(
                        install_output, "\nBatch installation complete!\n"
                    ))

                threading.Thread(target=run_installation, daemon=True).start()

            ttk.Button(install_frame, text="Install All", command=install_apks).pack(pady=5)

            # Uninstall tab
            uninstall_frame = ttk.Frame(notebook, padding=10)
            notebook.add(uninstall_frame, text="Batch Uninstall")

            ttk.Label(uninstall_frame, text="Installed Packages:").pack(anchor="w")

            uninstall_list_frame = ttk.Frame(uninstall_frame)
            uninstall_list_frame.pack(fill="both", expand=True, pady=5)

            uninstall_scrollbar = ttk.Scrollbar(uninstall_list_frame)
            uninstall_scrollbar.pack(side="right", fill="y")

            uninstall_listbox = tk.Listbox(uninstall_list_frame, selectmode=tk.MULTIPLE, yscrollcommand=uninstall_scrollbar.set)
            uninstall_listbox.pack(fill="both", expand=True)
            uninstall_scrollbar.config(command=uninstall_listbox.yview)

            def load_installed_packages():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    packages = sorted([
                        line[8:] for line in result.stdout.strip().split('\n')
                        if line.startswith('package:')
                    ])

                    def update_packages():
                        uninstall_listbox.delete(0, tk.END)
                        for package in packages:
                            uninstall_listbox.insert(tk.END, package)

                    emit_ui(self, update_packages)

            threading.Thread(target=load_installed_packages, daemon=True).start()

            uninstall_output = scrolledtext.ScrolledText(uninstall_frame, wrap=tk.WORD, height=8)
            uninstall_output.pack(fill="both", expand=True, pady=5)

            uninstall_progress = ttk.Progressbar(uninstall_frame, mode='determinate')
            uninstall_progress.pack(fill="x", pady=5)

            def uninstall_packages():
                selection = uninstall_listbox.curselection()
                if not selection:
                    messagebox.showerror("Error", "No packages selected")
                    return

                packages = [uninstall_listbox.get(i) for i in selection]
                total = len(packages)

                def run_uninstallation():
                    for i, pkg in enumerate(packages):
                        progress = ((i + 1) / total) * 100
                        emit_ui(self, lambda p=progress: set_progress(uninstall_progress, p))

                        emit_ui(self, lambda p=pkg: append_text(
                            uninstall_output, f"Uninstalling {p}...\n"
                        ))

                        try:
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "uninstall", pkg],
                                capture_output=True, text=True, timeout=60
                            )

                            if "Success" in result.stdout:
                                emit_ui(self, lambda p=pkg: append_text(
                                    uninstall_output, f"  ✓ {p} uninstalled\n"
                                ))
                            else:
                                emit_ui(self, lambda p=pkg, e=result.stderr: append_text(
                                    uninstall_output, f"  ✗ {p} failed: {e}\n"
                                ))

                        except Exception as e:
                            emit_ui(self, lambda p=pkg, err=str(e): append_text(
                                uninstall_output, f"  ✗ {p} error: {err}\n"
                            ))

                    emit_ui(self, load_installed_packages)
                    emit_ui(self, lambda: append_text(
                        uninstall_output, "\nBatch uninstallation complete!\n"
                    ))

                threading.Thread(target=run_uninstallation, daemon=True).start()

            uninstall_btn_frame = ttk.Frame(uninstall_frame)
            uninstall_btn_frame.pack(fill="x", pady=5)

            ttk.Button(uninstall_btn_frame, text="Refresh", command=lambda: threading.Thread(target=load_installed_packages, daemon=True).start()).pack(side="left", padx=5)
            ttk.Button(uninstall_btn_frame, text="Uninstall Selected", command=uninstall_packages).pack(side="left", padx=5)

            # Close button
            ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open batch app manager: {str(e)}")

    def _logcat_screencap_dialog(self):
        """Combined logcat and screenshot/recording dialog"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Live Monitor")
            dialog.geometry("900x700")

            x_pos = (self.winfo_screenwidth() - 900) // 2
            y_pos = (self.winfo_screenheight() - 700) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill="both", expand=True)

            # Paned window
            paned = ttk.PanedWindow(main_frame, orient="vertical")
            paned.pack(fill="both", expand=True)

            # Logcat frame
            logcat_frame = ttk.LabelFrame(paned, text="Live Logcat", padding=10)
            paned.add(logcat_frame, weight=2)

            logcat_controls = ttk.Frame(logcat_frame)
            logcat_controls.pack(fill="x", pady=(0, 5))

            filter_var = tk.StringVar()
            ttk.Label(logcat_controls, text="Filter:").pack(side="left", padx=(0, 5))
            ttk.Entry(logcat_controls, textvariable=filter_var, width=30).pack(side="left", padx=5)

            level_var = tk.StringVar(value="V")
            ttk.Label(logcat_controls, text="Level:").pack(side="left", padx=(10, 5))
            ttk.Combobox(logcat_controls, textvariable=level_var, values=["V", "D", "I", "W", "E"], width=5).pack(side="left")

            logcat_text = scrolledtext.ScrolledText(logcat_frame, wrap=tk.NONE, height=15)
            logcat_text.pack(fill="both", expand=True)

            logcat_text.tag_configure("V", foreground="gray")
            logcat_text.tag_configure("D", foreground="black")
            logcat_text.tag_configure("I", foreground="green")
            logcat_text.tag_configure("W", foreground="orange")
            logcat_text.tag_configure("E", foreground="red")

            logcat_running = {'value': False, 'process': None}

            def start_logcat():
                if logcat_running['value']:
                    return

                logcat_running['value'] = True
                logcat_text.delete(1.0, tk.END)

                def read_logcat():
                    try:
                        cmd = [adb_cmd, "-s", serial, "logcat", f"*:{level_var.get()}"]
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

                            # Determine tag
                            tag = "D"
                            if "/V " in line:
                                tag = "V"
                            elif "/D " in line:
                                tag = "D"
                            elif "/I " in line:
                                tag = "I"
                            elif "/W " in line:
                                tag = "W"
                            elif "/E " in line:
                                tag = "E"

                            # Apply filter
                            filter_text = filter_var.get().lower()
                            if not filter_text or filter_text in line.lower():
                                emit_ui(self, lambda l=line, t=tag: [
                                    append_text(logcat_text, l, tag=t),
                                    logcat_text.see(tk.END)
                                ])

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
                logcat_text.delete(1.0, tk.END)

            logcat_btn_frame = ttk.Frame(logcat_frame)
            logcat_btn_frame.pack(fill="x", pady=5)

            ttk.Button(logcat_btn_frame, text="Start", command=start_logcat).pack(side="left", padx=5)
            ttk.Button(logcat_btn_frame, text="Stop", command=stop_logcat).pack(side="left", padx=5)
            ttk.Button(logcat_btn_frame, text="Clear", command=clear_logcat).pack(side="left", padx=5)

            # Screenshot frame
            capture_frame = ttk.LabelFrame(paned, text="Capture", padding=10)
            paned.add(capture_frame, weight=1)

            capture_controls = ttk.Frame(capture_frame)
            capture_controls.pack(fill="x")

            def capture_screenshot():
                try:
                    import tempfile
                    import time

                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.png"
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".png",
                        initialfile=filename,
                        filetypes=[("PNG files", "*.png")]
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

                    messagebox.showinfo("Saved", f"Screenshot saved to:\n{save_path}")

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")

            ttk.Button(capture_controls, text="Screenshot", command=capture_screenshot).pack(side="left", padx=5)

            def on_closing():
                stop_logcat()
                dialog.destroy()

            dialog.protocol("WM_DELETE_WINDOW", on_closing)

            ttk.Button(main_frame, text="Close", command=on_closing).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open live monitor: {str(e)}")
