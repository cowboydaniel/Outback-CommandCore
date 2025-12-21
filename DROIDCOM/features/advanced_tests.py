"""
DROIDCOM - Advanced Tests Feature Module
Handles advanced testing features like stress tests, benchmarks, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time

from ..constants import IS_WINDOWS


class AdvancedTestsMixin:
    """Mixin class providing advanced testing functionality."""

    def run_hardware_stress_test(self):
        """Run a comprehensive hardware stress test"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        self.log_message("Starting comprehensive Hardware Stress Test...")
        threading.Thread(target=self._hardware_stress_test_task, daemon=True).start()

    def _hardware_stress_test_task(self):
        """Background task for running the hardware stress test"""
        try:
            self.log_message("Running CPU stress test...")
            cpu_script = "for i in $(seq 1 8); do while : ; do : ; done & done; sleep 15; killall sh"
            success, output = self.run_adb_command(['shell', 'sh', '-c', cpu_script], device_serial=self.device_serial, timeout=20)

            if success:
                self.log_message("CPU stress test completed")
            else:
                self.log_message("CPU stress test failed or was interrupted")

            self.log_message("Running memory allocation test...")
            mem_script = "dd if=/dev/zero of=/data/local/tmp/memtest bs=1M count=100; rm /data/local/tmp/memtest"
            success, output = self.run_adb_command(['shell', 'sh', '-c', mem_script], device_serial=self.device_serial)

            if success:
                self.log_message("Memory allocation test completed")
            else:
                self.log_message(f"Memory allocation test failed: {output}")

            self.log_message("Running storage I/O test...")
            io_script = "dd if=/dev/zero of=/data/local/tmp/iotest bs=4k count=25000; sync; rm /data/local/tmp/iotest"
            success, output = self.run_adb_command(['shell', 'sh', '-c', io_script], device_serial=self.device_serial)

            if success:
                self.log_message("Storage I/O test completed")
            else:
                self.log_message(f"Storage I/O test failed: {output}")

            self.log_message("Running UI rendering test...")
            self.run_adb_command(['shell', 'am', 'start', '-a', 'android.settings.SETTINGS'], device_serial=self.device_serial)
            time.sleep(2)

            for i in range(5):
                self.run_adb_command(['shell', 'input', 'swipe', '500', '1000', '500', '300'], device_serial=self.device_serial)
                time.sleep(0.5)

            self.run_adb_command(['shell', 'input', 'keyevent', 'KEYCODE_HOME'], device_serial=self.device_serial)

            self.log_message("Hardware stress test completed successfully")

        except Exception as e:
            self.log_message(f"Hardware stress test failed: {str(e)}")

    def _monkey_testing_dialog(self):
        """Show dialog for Monkey testing"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Monkey Testing")
            dialog.geometry("600x500")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Monkey Testing", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            ttk.Label(main_frame, text="Monkey is a program that generates random events on your device.").pack(pady=5)

            # Package selection
            pkg_frame = ttk.LabelFrame(main_frame, text="Target Package", padding=10)
            pkg_frame.pack(fill="x", pady=10)

            pkg_var = tk.StringVar()
            pkg_combo = ttk.Combobox(pkg_frame, textvariable=pkg_var, width=50)
            pkg_combo.pack(fill="x")

            # Load packages
            def load_packages():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=20
                )
                if result.returncode == 0:
                    packages = [line[8:] for line in result.stdout.strip().split('\n') if line.startswith('package:')]
                    dialog.after(0, lambda: pkg_combo.configure(values=packages))

            threading.Thread(target=load_packages, daemon=True).start()

            # Event count
            count_frame = ttk.Frame(main_frame)
            count_frame.pack(fill="x", pady=5)

            ttk.Label(count_frame, text="Number of events:").pack(side="left")
            count_var = tk.IntVar(value=1000)
            count_spinbox = ttk.Spinbox(count_frame, from_=100, to=100000, textvariable=count_var, width=15)
            count_spinbox.pack(side="left", padx=10)

            # Delay between events
            delay_frame = ttk.Frame(main_frame)
            delay_frame.pack(fill="x", pady=5)

            ttk.Label(delay_frame, text="Delay between events (ms):").pack(side="left")
            delay_var = tk.IntVar(value=500)
            delay_spinbox = ttk.Spinbox(delay_frame, from_=0, to=5000, textvariable=delay_var, width=15)
            delay_spinbox.pack(side="left", padx=10)

            # Seed
            seed_frame = ttk.Frame(main_frame)
            seed_frame.pack(fill="x", pady=5)

            ttk.Label(seed_frame, text="Random seed (0 = random):").pack(side="left")
            seed_var = tk.IntVar(value=0)
            seed_spinbox = ttk.Spinbox(seed_frame, from_=0, to=999999, textvariable=seed_var, width=15)
            seed_spinbox.pack(side="left", padx=10)

            # Output
            output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=60)
            output_text.pack(fill="both", expand=True, pady=10)

            # Status
            status_var = tk.StringVar(value="Ready")
            status_label = ttk.Label(main_frame, textvariable=status_var)
            status_label.pack(pady=5)

            running = {'value': False}

            def run_test():
                if running['value']:
                    return

                package = pkg_var.get()
                if not package:
                    messagebox.showerror("Error", "Please select a package")
                    return

                running['value'] = True
                status_var.set("Running...")
                output_text.delete(1.0, tk.END)

                def run_monkey():
                    try:
                        count = count_var.get()
                        delay = delay_var.get()
                        seed = seed_var.get()

                        cmd = [adb_cmd, "-s", serial, "shell", "monkey",
                               "-p", package,
                               "-v",
                               "--throttle", str(delay),
                               str(count)]

                        if seed > 0:
                            cmd.insert(-1, "-s")
                            cmd.insert(-1, str(seed))

                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )

                        for line in iter(process.stdout.readline, ''):
                            if not running['value']:
                                process.terminate()
                                break
                            dialog.after(0, lambda l=line: [
                                output_text.insert(tk.END, l),
                                output_text.see(tk.END)
                            ])

                        process.wait()
                        dialog.after(0, lambda: status_var.set("Completed"))

                    except Exception as e:
                        dialog.after(0, lambda: [
                            output_text.insert(tk.END, f"\nError: {str(e)}"),
                            status_var.set("Error")
                        ])
                    finally:
                        running['value'] = False

                threading.Thread(target=run_monkey, daemon=True).start()

            def stop_test():
                running['value'] = False
                status_var.set("Stopped")

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Run Test", command=run_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Stop", command=stop_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open monkey testing dialog: {str(e)}")

    def run_io_spike_generator(self):
        """Run I/O spike generator test"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("I/O Spike Generator")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 500) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="I/O Spike Generator", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            # File size
            size_frame = ttk.Frame(main_frame)
            size_frame.pack(fill="x", pady=5)

            ttk.Label(size_frame, text="File size (MB):").pack(side="left")
            size_var = tk.IntVar(value=100)
            size_spinbox = ttk.Spinbox(size_frame, from_=10, to=1000, textvariable=size_var, width=10)
            size_spinbox.pack(side="left", padx=10)

            # Block size
            block_frame = ttk.Frame(main_frame)
            block_frame.pack(fill="x", pady=5)

            ttk.Label(block_frame, text="Block size (KB):").pack(side="left")
            block_var = tk.IntVar(value=4)
            block_combo = ttk.Combobox(block_frame, textvariable=block_var, values=[1, 4, 16, 64, 256, 1024], width=10)
            block_combo.pack(side="left", padx=10)

            # Test type
            type_frame = ttk.Frame(main_frame)
            type_frame.pack(fill="x", pady=5)

            ttk.Label(type_frame, text="Test type:").pack(side="left")
            type_var = tk.StringVar(value="write")
            ttk.Radiobutton(type_frame, text="Write", variable=type_var, value="write").pack(side="left", padx=5)
            ttk.Radiobutton(type_frame, text="Read", variable=type_var, value="read").pack(side="left", padx=5)
            ttk.Radiobutton(type_frame, text="Both", variable=type_var, value="both").pack(side="left", padx=5)

            # Output
            output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=50)
            output_text.pack(fill="both", expand=True, pady=10)

            # Progress
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill="x", pady=5)

            running = {'value': False}

            def run_io_test():
                if running['value']:
                    return

                running['value'] = True
                output_text.delete(1.0, tk.END)

                def io_thread():
                    try:
                        size_mb = size_var.get()
                        block_kb = block_var.get()
                        test_type = type_var.get()

                        block_count = (size_mb * 1024) // block_kb

                        output_text.insert(tk.END, f"Starting I/O test...\n")
                        output_text.insert(tk.END, f"File size: {size_mb} MB\n")
                        output_text.insert(tk.END, f"Block size: {block_kb} KB\n\n")

                        if test_type in ["write", "both"]:
                            output_text.insert(tk.END, "Running write test...\n")

                            cmd = f"dd if=/dev/zero of=/data/local/tmp/iotest bs={block_kb}k count={block_count}"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            dialog.after(0, lambda: [
                                output_text.insert(tk.END, result.stderr),
                                output_text.insert(tk.END, "\n")
                            ])

                        if test_type in ["read", "both"]:
                            output_text.insert(tk.END, "Running read test...\n")

                            cmd = f"dd if=/data/local/tmp/iotest of=/dev/null bs={block_kb}k"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            dialog.after(0, lambda: [
                                output_text.insert(tk.END, result.stderr),
                                output_text.insert(tk.END, "\n")
                            ])

                        # Cleanup
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                            capture_output=True, text=True, timeout=10
                        )

                        dialog.after(0, lambda: output_text.insert(tk.END, "\nTest completed!\n"))

                    except Exception as e:
                        dialog.after(0, lambda: output_text.insert(tk.END, f"\nError: {str(e)}\n"))
                    finally:
                        running['value'] = False

                threading.Thread(target=io_thread, daemon=True).start()

            def cancel_test():
                running['value'] = False
                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                    capture_output=True, text=True, timeout=10
                )

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Run Test", command=run_io_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=cancel_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open I/O spike generator: {str(e)}")

    def run_scrcpy_mirror(self):
        """Run scrcpy screen mirroring"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial

            # Check if scrcpy is installed
            result = subprocess.run(
                ["which", "scrcpy"] if not IS_WINDOWS else ["where", "scrcpy"],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                messagebox.showinfo(
                    "scrcpy Not Found",
                    "scrcpy is not installed on your system.\n\n"
                    "Please install scrcpy to use screen mirroring:\n"
                    "- Linux: sudo apt install scrcpy\n"
                    "- Mac: brew install scrcpy\n"
                    "- Windows: Download from GitHub"
                )
                return

            # Launch scrcpy
            self.log_message("Launching scrcpy for screen mirroring...")

            def launch_scrcpy():
                try:
                    subprocess.run(
                        ["scrcpy", "-s", serial],
                        capture_output=True, text=True
                    )
                except Exception as e:
                    self.after(0, lambda: self.log_message(f"scrcpy error: {str(e)}"))

            threading.Thread(target=launch_scrcpy, daemon=True).start()

            messagebox.showinfo("scrcpy Launched", "scrcpy screen mirroring has been launched.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch scrcpy: {str(e)}")

    def run_adb_command(self, command, device_serial=None, timeout=60):
        """Run an ADB command and return the result"""
        try:
            adb_cmd = self.adb_path if self.adb_path else 'adb'

            cmd = [adb_cmd]

            if device_serial:
                cmd.extend(['-s', device_serial])

            cmd.extend(command)

            self.log_message(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                self.log_message(f"Command failed: {result.stderr.strip()}")
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            self.log_message(f"Command timed out after {timeout} seconds")
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            self.log_message(f"Error running command: {str(e)}")
            return False, str(e)
