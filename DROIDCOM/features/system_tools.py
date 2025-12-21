"""
DROIDCOM - System Tools Feature Module
Handles system monitoring and information display.
"""

from ..ui.qt_compat import tk
from ..ui.qt_compat import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import logging

from ..constants import IS_WINDOWS


class SystemToolsMixin:
    """Mixin class providing system monitoring functionality."""

    def _show_battery_stats(self):
        """Show detailed battery statistics"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Battery Statistics")
            dialog.geometry("750x850")
            dialog.transient(self.parent)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 650) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            notebook = ttk.Notebook(dialog)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)

            # Status tab
            status_frame = ttk.Frame(notebook)
            notebook.add(status_frame, text="Status")
            status_widget = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=20, width=70)
            status_widget.pack(fill="both", expand=True, padx=5, pady=5)

            # History tab
            history_frame = ttk.Frame(notebook)
            notebook.add(history_frame, text="History")
            history_widget = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, height=20, width=70)
            history_widget.pack(fill="both", expand=True, padx=5, pady=5)

            # Usage tab
            usage_frame = ttk.Frame(notebook)
            notebook.add(usage_frame, text="Usage")
            usage_widget = scrolledtext.ScrolledText(usage_frame, wrap=tk.WORD, height=20, width=70)
            usage_widget.pack(fill="both", expand=True, padx=5, pady=5)

            # Buttons
            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            auto_refresh_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                buttons_frame, text="Auto Refresh (5s)",
                variable=auto_refresh_var
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_battery_stats(status_widget, history_widget, usage_widget, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            # Initial refresh
            self._refresh_battery_stats(status_widget, history_widget, usage_widget, serial, adb_cmd)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show battery stats: {str(e)}")
            logging.error(f"Error in _show_battery_stats: {e}", exc_info=True)

    def _refresh_battery_stats(self, status_widget, history_widget, usage_widget, serial, adb_cmd):
        """Refresh battery statistics"""
        def get_battery_status():
            try:
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "dumpsys", "battery"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    status_widget.delete(1.0, tk.END)
                    status_widget.insert(tk.END, "===== Battery Status =====\n\n")
                    status_widget.insert(tk.END, result.stdout)
            except Exception as e:
                status_widget.insert(tk.END, f"Error: {str(e)}")

        def get_battery_history():
            try:
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "dumpsys", "batterystats", "--history"],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    history_widget.delete(1.0, tk.END)
                    history_widget.insert(tk.END, "===== Battery History =====\n\n")
                    # Limit output to prevent UI slowdown
                    lines = result.stdout.split('\n')[:200]
                    history_widget.insert(tk.END, '\n'.join(lines))
            except Exception as e:
                history_widget.insert(tk.END, f"Error: {str(e)}")

        def get_battery_stats():
            try:
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "dumpsys", "batterystats"],
                    capture_output=True, text=True, timeout=20
                )
                if result.returncode == 0:
                    usage_widget.delete(1.0, tk.END)
                    usage_widget.insert(tk.END, "===== Battery Usage =====\n\n")
                    # Limit output
                    lines = result.stdout.split('\n')[:300]
                    usage_widget.insert(tk.END, '\n'.join(lines))
            except Exception as e:
                usage_widget.insert(tk.END, f"Error: {str(e)}")

        threading.Thread(target=get_battery_status, daemon=True).start()
        threading.Thread(target=get_battery_history, daemon=True).start()
        threading.Thread(target=get_battery_stats, daemon=True).start()

    def _show_memory_usage(self):
        """Show memory usage information"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Memory Usage")
            dialog.geometry("750x850")

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=25, width=70)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_memory_stats(text_widget, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            self._refresh_memory_stats(text_widget, serial, adb_cmd)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show memory usage: {str(e)}")

    def _refresh_memory_stats(self, text_widget, serial, adb_cmd):
        """Refresh memory statistics"""
        try:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, "===== Memory Information =====\n\n")

            # Get meminfo
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cat", "/proc/meminfo"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                text_widget.insert(tk.END, "Kernel Memory Info:\n")
                text_widget.insert(tk.END, result.stdout[:2000])
                text_widget.insert(tk.END, "\n\n")

            # Get dumpsys meminfo
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "meminfo"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                text_widget.insert(tk.END, "Process Memory Info:\n")
                lines = result.stdout.split('\n')[:100]
                text_widget.insert(tk.END, '\n'.join(lines))

        except Exception as e:
            text_widget.insert(tk.END, f"Error: {str(e)}")

    def _show_cpu_usage(self):
        """Show CPU usage information"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("CPU Usage")
            dialog.geometry("750x850")

            x_pos = (self.winfo_screenwidth() - 650) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=25, width=75)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            # Options frame
            options_frame = ttk.Frame(dialog)
            options_frame.pack(fill="x", padx=10, pady=5)

            sort_var = tk.StringVar(value="cpu")
            ttk.Label(options_frame, text="Sort by:").pack(side="left", padx=5)
            sort_combo = ttk.Combobox(options_frame, textvariable=sort_var, values=["cpu", "mem", "pid"])
            sort_combo.pack(side="left", padx=5)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            auto_refresh_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(buttons_frame, text="Auto Refresh (3s)", variable=auto_refresh_var).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_cpu_stats(text_widget, serial, adb_cmd, sort_var.get())
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            self._refresh_cpu_stats(text_widget, serial, adb_cmd)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show CPU usage: {str(e)}")

    def _refresh_cpu_stats(self, text_widget, serial, adb_cmd, sort_by="cpu"):
        """Refresh CPU statistics"""
        try:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, "===== CPU Usage =====\n\n")

            # Get top output
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "top", "-n", "1", "-d", "1"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')[:50]
                text_widget.insert(tk.END, '\n'.join(lines))

            text_widget.insert(tk.END, "\n\n===== CPU Info =====\n\n")

            # Get CPU info
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "cat", "/proc/cpuinfo"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')[:40]
                text_widget.insert(tk.END, '\n'.join(lines))

        except Exception as e:
            text_widget.insert(tk.END, f"Error: {str(e)}")

    def _show_network_stats(self):
        """Show network statistics"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Network Statistics")
            dialog.geometry("750x850")

            x_pos = (self.winfo_screenwidth() - 700) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            notebook = ttk.Notebook(dialog)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)

            # Interfaces tab
            ifaces_frame = ttk.Frame(notebook)
            notebook.add(ifaces_frame, text="Interfaces")
            ifaces_text = scrolledtext.ScrolledText(ifaces_frame, wrap=tk.WORD, height=20, width=70)
            ifaces_text.pack(fill="both", expand=True, padx=5, pady=5)

            # Connections tab
            conn_frame = ttk.Frame(notebook)
            notebook.add(conn_frame, text="Connections")
            conn_text = scrolledtext.ScrolledText(conn_frame, wrap=tk.WORD, height=20, width=70)
            conn_text.pack(fill="both", expand=True, padx=5, pady=5)

            # Usage tab
            usage_frame = ttk.Frame(notebook)
            notebook.add(usage_frame, text="Data Usage")
            usage_text = scrolledtext.ScrolledText(usage_frame, wrap=tk.WORD, height=20, width=70)
            usage_text.pack(fill="both", expand=True, padx=5, pady=5)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_network_stats(ifaces_text, conn_text, usage_text, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            self._refresh_network_stats(ifaces_text, conn_text, usage_text, serial, adb_cmd)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show network stats: {str(e)}")

    def _refresh_network_stats(self, ifaces_text, conn_text, usage_text, serial, adb_cmd):
        """Refresh network statistics"""
        try:
            # Network interfaces
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "ip", "addr"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                ifaces_text.delete(1.0, tk.END)
                ifaces_text.insert(tk.END, "===== Network Interfaces =====\n\n")
                ifaces_text.insert(tk.END, result.stdout)

            # Network connections
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "netstat", "-tuln"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                conn_text.delete(1.0, tk.END)
                conn_text.insert(tk.END, "===== Active Connections =====\n\n")
                conn_text.insert(tk.END, result.stdout)

            # Data usage
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "netstats"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                usage_text.delete(1.0, tk.END)
                usage_text.insert(tk.END, "===== Data Usage =====\n\n")
                lines = result.stdout.split('\n')[:150]
                usage_text.insert(tk.END, '\n'.join(lines))

        except Exception as e:
            ifaces_text.insert(tk.END, f"Error: {str(e)}")

    def _show_thermal_stats(self):
        """Show thermal statistics"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Thermal Information")
            dialog.geometry("600x400")

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=20, width=70)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            def refresh_thermal_stats():
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, "===== Thermal Information =====\n\n")

                try:
                    # Get thermal zone types
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "cat /sys/class/thermal/thermal_zone*/type"],
                        capture_output=True, text=True, timeout=10
                    )
                    types = result.stdout.strip().split('\n') if result.returncode == 0 else []

                    # Get thermal zone temperatures
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "cat /sys/class/thermal/thermal_zone*/temp"],
                        capture_output=True, text=True, timeout=10
                    )
                    temps = result.stdout.strip().split('\n') if result.returncode == 0 else []

                    for i, (zone_type, temp) in enumerate(zip(types, temps)):
                        try:
                            temp_value = int(temp.strip())
                            if temp_value > 1000:
                                temp_celsius = temp_value / 1000
                            else:
                                temp_celsius = temp_value
                            text_widget.insert(tk.END, f"Zone {i} ({zone_type}): {temp_celsius:.1f}°C\n")
                        except ValueError:
                            text_widget.insert(tk.END, f"Zone {i} ({zone_type}): {temp}\n")

                    # Get battery temperature
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "dumpsys", "battery"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'temperature' in line.lower():
                                text_widget.insert(tk.END, f"\n{line.strip()}\n")

                except Exception as e:
                    text_widget.insert(tk.END, f"\nError: {str(e)}")

            ttk.Button(buttons_frame, text="Refresh", command=refresh_thermal_stats).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            refresh_thermal_stats()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show thermal stats: {str(e)}")

    def _show_storage_info(self):
        """Show storage information"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Storage Information")
            dialog.geometry("600x500")

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=25, width=70)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_storage_info(text_widget, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            self._refresh_storage_info(text_widget, serial, adb_cmd)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show storage info: {str(e)}")

    def _refresh_storage_info(self, text_widget, serial, adb_cmd):
        """Refresh storage information"""
        try:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, "===== Storage Information =====\n\n")

            # Get df output
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "df", "-h"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                text_widget.insert(tk.END, "Disk Usage:\n\n")
                text_widget.insert(tk.END, result.stdout)

            text_widget.insert(tk.END, "\n\n===== Mount Points =====\n\n")

            # Get mount points
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "mount"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')[:30]
                text_widget.insert(tk.END, '\n'.join(lines))

        except Exception as e:
            text_widget.insert(tk.END, f"Error: {str(e)}")

    def _show_running_services(self):
        """Show running services"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Running Services")
            dialog.geometry("800x600")

            x_pos = (self.winfo_screenwidth() - 800) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            # Filter frame
            filter_frame = ttk.Frame(dialog)
            filter_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)
            filter_var = tk.StringVar()
            filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=40)
            filter_entry.pack(side="left", fill="x", expand=True, padx=5)

            # Tree view
            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

            tree_scroll = ttk.Scrollbar(tree_frame)
            tree_scroll.pack(side="right", fill="y")

            tree = ttk.Treeview(tree_frame, columns=("pid", "name"), yscrollcommand=tree_scroll.set)
            tree.pack(fill="both", expand=True)
            tree_scroll.config(command=tree.yview)

            tree.heading("#0", text="Service")
            tree.heading("pid", text="PID")
            tree.heading("name", text="Process Name")

            tree.column("#0", width=400)
            tree.column("pid", width=100)
            tree.column("name", width=250)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_running_services(tree)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            self._refresh_running_services(tree)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show running services: {str(e)}")

    def _refresh_running_services(self, tree_widget, filter_text=""):
        """Refresh running services list"""
        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            # Clear tree
            for item in tree_widget.get_children():
                tree_widget.delete(item)

            # Get running services
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys", "activity", "services"],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                current_service = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('* ServiceRecord'):
                        # Extract service info
                        parts = line.split()
                        if len(parts) >= 3:
                            service_name = parts[2] if len(parts) > 2 else "Unknown"
                            if filter_text.lower() in service_name.lower():
                                tree_widget.insert("", "end", text=service_name, values=("", ""))

        except Exception as e:
            self.log_message(f"Error refreshing services: {str(e)}")

    def _show_detailed_device_info(self):
        """Show detailed device information"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Detailed Device Information")
            dialog.geometry("750x600")

            x_pos = (self.winfo_screenwidth() - 700) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            notebook = ttk.Notebook(dialog)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)

            # Properties tab
            props_frame = ttk.Frame(notebook)
            notebook.add(props_frame, text="System Properties")
            props_widget = scrolledtext.ScrolledText(props_frame, wrap=tk.WORD, height=25, width=80)
            props_widget.pack(fill="both", expand=True, padx=5, pady=5)

            # System tab
            sys_frame = ttk.Frame(notebook)
            notebook.add(sys_frame, text="System Info")
            sys_widget = scrolledtext.ScrolledText(sys_frame, wrap=tk.WORD, height=25, width=80)
            sys_widget.pack(fill="both", expand=True, padx=5, pady=5)

            # Hardware tab
            hw_frame = ttk.Frame(notebook)
            notebook.add(hw_frame, text="Hardware")
            hw_widget = scrolledtext.ScrolledText(hw_frame, wrap=tk.WORD, height=25, width=80)
            hw_widget.pack(fill="both", expand=True, padx=5, pady=5)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            ttk.Button(
                buttons_frame, text="Refresh",
                command=lambda: self._refresh_device_info(props_widget, sys_widget, hw_widget, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

            # Load data
            def get_device_properties():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "getprop"],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    self.after(0, lambda: [props_widget.delete(1.0, tk.END), props_widget.insert(tk.END, result.stdout)])

            def get_system_info():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "uname", "-a"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.after(0, lambda: [
                        sys_widget.delete(1.0, tk.END),
                        sys_widget.insert(tk.END, "Kernel: " + result.stdout + "\n\n")
                    ])

            def get_hardware_info():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "cat", "/proc/cpuinfo"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.after(0, lambda: [
                        hw_widget.delete(1.0, tk.END),
                        hw_widget.insert(tk.END, "===== CPU Info =====\n\n"),
                        hw_widget.insert(tk.END, result.stdout[:2000])
                    ])

            threading.Thread(target=get_device_properties, daemon=True).start()
            threading.Thread(target=get_system_info, daemon=True).start()
            threading.Thread(target=get_hardware_info, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show device info: {str(e)}")
