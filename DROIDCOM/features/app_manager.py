"""
DROIDCOM - App Manager Feature Module
Handles app installation, uninstallation, and management.
"""

from ..ui.qt_compat import tk
from ..ui.qt_compat import ttk, messagebox, filedialog
import subprocess
import os
import threading

from ..constants import IS_WINDOWS


class AppManagerMixin:
    """Mixin class providing app management functionality."""

    def install_apk(self):
        """Install an APK on the connected Android device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        apk_path = filedialog.askopenfilename(
            title="Select APK file to install",
            filetypes=[("Android Package", "*.apk"), ("All files", "*.*")]
        )

        if not apk_path:
            return

        self._run_in_thread(lambda: self._install_apk_task(apk_path))

    def _install_apk_task(self, apk_path):
        """Worker thread to install an APK"""
        try:
            self.update_status(f"Installing {os.path.basename(apk_path)}...")
            self.log_message(f"Installing APK: {apk_path}")

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
                self.update_status("Installation failed")
                return

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'install', '-r', apk_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            if result.returncode != 0 or 'Failure' in result.stdout:
                self.log_message(f"Failed to install APK: {result.stderr.strip() or result.stdout.strip()}")
                self.update_status("Installation failed")
                messagebox.showerror("Installation Error",
                                  f"Failed to install APK:\n{result.stderr.strip() or result.stdout.strip()}")
                return

            self.log_message("APK installed successfully")
            self.update_status("APK installed")
            messagebox.showinfo("Installation Complete", f"{os.path.basename(apk_path)} was installed successfully.")

        except Exception as e:
            self.log_message(f"Error installing APK: {str(e)}")
            self.update_status("Installation failed")
            messagebox.showerror("Installation Error", f"Failed to install APK: {str(e)}")

    def app_manager(self):
        """Manage apps on the connected Android device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        self._run_in_thread(self._app_manager_task)

    def _app_manager_task(self):
        """Worker thread to load app list and show app manager"""
        try:
            self.update_status("Loading app list...")
            self.log_message("Loading list of installed applications...")

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
                self.update_status("Failed to load app list")
                return

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'list', 'packages', '-3'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20
            )

            if result.returncode != 0:
                self.log_message(f"Failed to get app list: {result.stderr.strip()}")
                self.update_status("Failed to load app list")
                return

            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('package:'):
                    package_name = line[8:].strip()
                    packages.append(package_name)

            packages.sort()

            self.update_status(f"Found {len(packages)} apps")
            self.log_message(f"Found {len(packages)} user-installed applications")

            self.after(0, lambda: self._show_app_manager(packages, serial, adb_cmd))

        except Exception as e:
            self.log_message(f"Error loading app list: {str(e)}")
            self.update_status("Failed to load app list")

    def _show_app_manager(self, packages, serial, adb_cmd):
        """Show the app manager window"""
        try:
            app_window = tk.Toplevel(self)
            app_window.title("Android App Manager")
            app_window.geometry("500x600")
            app_window.minsize(400, 400)

            x_pos = (self.winfo_screenwidth() - 500) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            app_window.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(app_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            ttk.Label(
                main_frame, text=f"Installed Apps ({len(packages)})", font=("Arial", 12, "bold")
            ).pack(pady=(0, 10))

            # Search frame
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill="x", pady=(0, 10))

            ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
            search_entry.pack(side="left", fill="x", expand=True)

            # App list frame
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill="both", expand=True)

            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            app_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            app_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=app_listbox.yview)

            for package in packages:
                app_listbox.insert(tk.END, package)

            # Bind search
            def filter_apps(*args):
                search_text = search_var.get().lower()
                app_listbox.delete(0, tk.END)
                for package in packages:
                    if search_text in package.lower():
                        app_listbox.insert(tk.END, package)

            search_var.trace('w', filter_apps)

            # Buttons frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=(10, 0))

            ttk.Button(
                buttons_frame, text="Uninstall",
                command=lambda: self._uninstall_app(app_listbox, packages, serial, adb_cmd, app_window)
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Clear Data",
                command=lambda: self._clear_app_data(app_listbox, packages, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Force Stop",
                command=lambda: self._force_stop_app(app_listbox, packages, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Permissions",
                command=lambda: self._view_app_permissions(app_listbox, packages, serial, adb_cmd)
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons_frame, text="Close",
                command=app_window.destroy
            ).pack(side="right", padx=5)

        except Exception as e:
            self.log_message(f"Error showing app manager: {str(e)}")
            messagebox.showerror("App Manager Error", f"Failed to show app manager: {str(e)}")

    def _view_app_permissions(self, listbox, packages, serial, adb_cmd):
        """View permissions for the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to view permissions.")
            return

        package_name = listbox.get(selection[0])

        # Create permissions window
        perm_window = tk.Toplevel(self)
        perm_window.title(f"Permissions - {package_name}")
        perm_window.geometry("500x400")

        main_frame = ttk.Frame(perm_window, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Loading permissions...").pack()

        text_widget = tk.Text(main_frame, wrap=tk.WORD)
        text_widget.pack(fill="both", expand=True)

        status_var = tk.StringVar(value="Loading...")

        def load_permissions():
            try:
                result = subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'dumpsys', 'package', package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    permissions = []
                    in_permissions = False
                    for line in result.stdout.split('\n'):
                        if 'requested permissions:' in line.lower() or 'install permissions:' in line.lower():
                            in_permissions = True
                            continue
                        if in_permissions:
                            if line.strip().startswith('android.permission'):
                                permissions.append(line.strip())
                            elif line.strip() and not line.startswith(' '):
                                in_permissions = False

                    self.after(0, lambda: self._display_permissions(text_widget, status_var, package_name, permissions))
                else:
                    self.after(0, lambda: self._show_permission_error(status_var, result.stderr))

            except Exception as e:
                self.after(0, lambda: self._show_permission_error(status_var, str(e)))

        threading.Thread(target=load_permissions, daemon=True).start()

    def _display_permissions(self, text_widget, status_var, package_name, permissions):
        """Display permissions in the text widget"""
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, f"Permissions for {package_name}:\n\n")

        if permissions:
            for perm in permissions:
                text_widget.insert(tk.END, f"  • {perm}\n")
            status_var.set(f"Found {len(permissions)} permissions")
        else:
            text_widget.insert(tk.END, "No permissions found or unable to retrieve permissions.")
            status_var.set("No permissions found")

    def _show_permission_error(self, status_var, error_msg):
        """Show error message for permission retrieval"""
        status_var.set(f"Error: {error_msg}")

    def _uninstall_app(self, listbox, packages, serial, adb_cmd, parent_window):
        """Uninstall the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to uninstall.")
            return

        package_name = listbox.get(selection[0])

        confirm = messagebox.askyesno(
            "Confirm Uninstall",
            f"Are you sure you want to uninstall {package_name}?\n\nThis action cannot be undone."
        )

        if not confirm:
            return

        try:
            self.log_message(f"Uninstalling {package_name}...")
            self.update_status(f"Uninstalling {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'uninstall', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and 'Success' in result.stdout:
                self.log_message(f"{package_name} uninstalled successfully")
                self.update_status("App uninstalled")
                messagebox.showinfo("Uninstall Complete", f"{package_name} was uninstalled successfully.")

                # Remove from list
                listbox.delete(selection[0])
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to uninstall {package_name}: {error_msg}")
                self.update_status("Uninstall failed")
                messagebox.showerror("Uninstall Error", f"Failed to uninstall {package_name}:\n{error_msg}")

        except Exception as e:
            self.log_message(f"Error uninstalling app: {str(e)}")
            messagebox.showerror("Uninstall Error", f"Failed to uninstall app: {str(e)}")

    def _clear_app_data(self, listbox, packages, serial, adb_cmd):
        """Clear data for the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to clear data.")
            return

        package_name = listbox.get(selection[0])

        confirm = messagebox.askyesno(
            "Confirm Clear Data",
            f"Are you sure you want to clear all data for {package_name}?\n\n"
            "This will delete all app settings, accounts, and cached data."
        )

        if not confirm:
            return

        try:
            self.log_message(f"Clearing data for {package_name}...")
            self.update_status(f"Clearing data for {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'clear', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and 'Success' in result.stdout:
                self.log_message(f"Data cleared for {package_name}")
                self.update_status("App data cleared")
                messagebox.showinfo("Clear Data Complete", f"Data for {package_name} was cleared successfully.")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to clear data for {package_name}: {error_msg}")
                self.update_status("Clear data failed")
                messagebox.showerror("Clear Data Error", f"Failed to clear data for {package_name}:\n{error_msg}")

        except Exception as e:
            self.log_message(f"Error clearing app data: {str(e)}")
            messagebox.showerror("Clear Data Error", f"Failed to clear app data: {str(e)}")

    def _force_stop_app(self, listbox, packages, serial, adb_cmd):
        """Force stop the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to force stop.")
            return

        package_name = listbox.get(selection[0])

        try:
            self.log_message(f"Force stopping {package_name}...")
            self.update_status(f"Force stopping {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'am', 'force-stop', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.log_message(f"{package_name} force stopped")
                self.update_status("App force stopped")
                messagebox.showinfo("Force Stop Complete", f"{package_name} was force stopped successfully.")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to force stop {package_name}: {error_msg}")
                self.update_status("Force stop failed")

        except Exception as e:
            self.log_message(f"Error force stopping app: {str(e)}")
            messagebox.showerror("Force Stop Error", f"Failed to force stop app: {str(e)}")

    def _toggle_app_freeze(self, listbox, packages, serial, adb_cmd):
        """Toggle freeze/unfreeze for the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to freeze/unfreeze.")
            return

        package_name = listbox.get(selection[0])

        try:
            # Check if app is currently disabled
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'list', 'packages', '-d'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            is_disabled = package_name in result.stdout

            if is_disabled:
                # Enable the app
                action = "enable"
                action_msg = "unfreezing"
            else:
                # Disable the app
                action = "disable-user"
                action_msg = "freezing"

            self.log_message(f"{action_msg.capitalize()} {package_name}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', action, '--user', '0', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                status = "frozen" if action == "disable-user" else "unfrozen"
                self.log_message(f"{package_name} has been {status}")
                messagebox.showinfo("Success", f"{package_name} has been {status}.")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_message(f"Failed to {action_msg} {package_name}: {error_msg}")
                messagebox.showerror("Error", f"Failed to {action_msg} {package_name}:\n{error_msg}")

        except Exception as e:
            self.log_message(f"Error toggling app freeze: {str(e)}")
            messagebox.showerror("Error", f"Failed to toggle app freeze: {str(e)}")

    def _extract_apk(self, listbox, packages, serial, adb_cmd):
        """Extract APK for the selected app"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No App Selected", "Please select an app to extract APK.")
            return

        package_name = listbox.get(selection[0])

        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            title="Save APK As",
            defaultextension=".apk",
            filetypes=[("Android Package", "*.apk")],
            initialfile=f"{package_name}.apk"
        )

        if not save_path:
            return

        try:
            self.log_message(f"Extracting APK for {package_name}...")
            self.update_status(f"Extracting {package_name}...")

            # Get APK path
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'pm', 'path', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                messagebox.showerror("Error", f"Failed to find APK path: {result.stderr}")
                return

            apk_path = result.stdout.strip().replace('package:', '')

            # Pull APK
            result = subprocess.run(
                [adb_cmd, '-s', serial, 'pull', apk_path, save_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.log_message(f"APK extracted to {save_path}")
                self.update_status("APK extracted")
                messagebox.showinfo("Success", f"APK extracted to:\n{save_path}")
            else:
                messagebox.showerror("Error", f"Failed to extract APK: {result.stderr}")

        except Exception as e:
            self.log_message(f"Error extracting APK: {str(e)}")
            messagebox.showerror("Error", f"Failed to extract APK: {str(e)}")

    def _filter_app_list(self, search_text, packages, listbox):
        """Filter the app list based on search text"""
        listbox.delete(0, tk.END)
        search_lower = search_text.lower()
        for package in packages:
            if search_lower in package.lower():
                listbox.insert(tk.END, package)
