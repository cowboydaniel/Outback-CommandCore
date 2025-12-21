"""
DROIDCOM - Security Feature Module
Handles security-related features like root check, encryption status, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import logging

from ..constants import IS_WINDOWS


class SecurityMixin:
    """Mixin class providing security functionality."""

    def _check_root_status(self):
        """Check if the device is rooted"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            self.log_message("Checking root status...")

            # Method 1: Check for su binary
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "which su"],
                capture_output=True, text=True, timeout=10
            )
            su_found = result.returncode == 0 and result.stdout.strip()

            # Method 2: Check for Superuser app
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "pm list packages | grep -E 'supersu|magisk|kingroot|kingoroot'"],
                capture_output=True, text=True, timeout=10
            )
            root_app_found = bool(result.stdout.strip())

            # Method 3: Try to run su
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "su -c id"],
                capture_output=True, text=True, timeout=5
            )
            su_works = "uid=0" in result.stdout

            if su_works:
                status = "ROOTED (su access available)"
                color = "red"
            elif su_found or root_app_found:
                status = "POSSIBLY ROOTED (root traces found)"
                color = "orange"
            else:
                status = "NOT ROOTED (no root traces found)"
                color = "green"

            self.log_message(f"Root status: {status}")
            messagebox.showinfo("Root Status", f"Device root status:\n\n{status}")

        except Exception as e:
            self.log_message(f"Error checking root status: {str(e)}")
            messagebox.showerror("Error", f"Failed to check root status: {str(e)}")

    def _check_encryption_status(self):
        """Check device encryption status"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            self.log_message("Checking encryption status...")

            # Check encryption state
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.crypto.state"],
                capture_output=True, text=True, timeout=10
            )
            crypto_state = result.stdout.strip()

            # Check encryption type
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.crypto.type"],
                capture_output=True, text=True, timeout=10
            )
            crypto_type = result.stdout.strip()

            if crypto_state == "encrypted":
                status = f"ENCRYPTED\nEncryption Type: {crypto_type or 'Unknown'}"
                color = "green"
            elif crypto_state == "unencrypted":
                status = "NOT ENCRYPTED\nDevice data is not encrypted"
                color = "red"
            else:
                status = f"UNKNOWN\nCrypto State: {crypto_state or 'Not available'}"
                color = "orange"

            self.log_message(f"Encryption status: {status}")
            messagebox.showinfo("Encryption Status", f"Device encryption status:\n\n{status}")

        except Exception as e:
            self.log_message(f"Error checking encryption status: {str(e)}")
            messagebox.showerror("Error", f"Failed to check encryption status: {str(e)}")

    def _check_lock_screen_status(self):
        """Check lock screen status and type"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            self.log_message("Checking lock screen status...")

            lock_type = self._detect_lock_screen_type(serial)

            messagebox.showinfo("Lock Screen Status", f"Lock screen type:\n\n{lock_type}")

        except Exception as e:
            self.log_message(f"Error checking lock screen status: {str(e)}")
            messagebox.showerror("Error", f"Failed to check lock screen status: {str(e)}")

    def _detect_lock_screen_type(self, serial):
        """Detect the type of lock screen"""
        adb_cmd = self.adb_path if IS_WINDOWS else "adb"

        try:
            # Check locksettings
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "dumpsys trust"],
                capture_output=True, text=True, timeout=10
            )

            # Check for pattern
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "ls /data/system/gesture.key 2>/dev/null"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return "Pattern Lock"

            # Check for password/PIN
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "ls /data/system/password.key 2>/dev/null"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return "PIN/Password Lock"

            # Check secure setting
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "settings get secure lockscreen.password_type"],
                capture_output=True, text=True, timeout=10
            )
            password_type = result.stdout.strip()

            if password_type == "0" or password_type == "65536":
                return "None/Swipe"
            elif password_type == "65792":
                return "PIN"
            elif password_type == "327680":
                return "Password"
            elif password_type == "131072":
                return "Pattern"

            return "Unknown (Secure lock may be enabled)"

        except Exception:
            return "Unable to determine"

    def _check_security_patch_level(self):
        """Check security patch level"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Security Patch Level")
            dialog.geometry("600x400")

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=20, width=70)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            text_widget.insert(tk.END, "===== Security Information =====\n\n")

            # Get security patch level
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.build.version.security_patch"],
                capture_output=True, text=True, timeout=10
            )
            patch_level = result.stdout.strip()
            text_widget.insert(tk.END, f"Security Patch Level: {patch_level or 'Unknown'}\n\n")

            # Get Android version
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.build.version.release"],
                capture_output=True, text=True, timeout=10
            )
            android_version = result.stdout.strip()
            text_widget.insert(tk.END, f"Android Version: {android_version or 'Unknown'}\n\n")

            # Get build ID
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.build.id"],
                capture_output=True, text=True, timeout=10
            )
            build_id = result.stdout.strip()
            text_widget.insert(tk.END, f"Build ID: {build_id or 'Unknown'}\n\n")

            # Get vendor security patch
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getprop ro.vendor.build.security_patch"],
                capture_output=True, text=True, timeout=10
            )
            vendor_patch = result.stdout.strip()
            if vendor_patch:
                text_widget.insert(tk.END, f"Vendor Security Patch: {vendor_patch}\n\n")

            # Get SELinux status
            result = subprocess.run(
                [adb_cmd, "-s", serial, "shell", "getenforce"],
                capture_output=True, text=True, timeout=10
            )
            selinux = result.stdout.strip()
            text_widget.insert(tk.END, f"SELinux Status: {selinux or 'Unknown'}\n\n")

            text_widget.configure(state="disabled")

            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get security info: {str(e)}")

    def _scan_dangerous_permissions(self):
        """Scan for apps with dangerous permissions"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Dangerous Permissions Scan")
            dialog.geometry("800x600")

            x_pos = (self.winfo_screenwidth() - 800) // 2
            y_pos = (self.winfo_screenheight() - 600) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            # Tree view
            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

            tree_scroll = ttk.Scrollbar(tree_frame)
            tree_scroll.pack(side="right", fill="y")

            tree = ttk.Treeview(tree_frame, columns=("permissions",), yscrollcommand=tree_scroll.set)
            tree.pack(fill="both", expand=True)
            tree_scroll.config(command=tree.yview)

            tree.heading("#0", text="Package")
            tree.heading("permissions", text="Dangerous Permissions")

            tree.column("#0", width=300)
            tree.column("permissions", width=450)

            # Details text
            details_frame = ttk.LabelFrame(dialog, text="Permission Details")
            details_frame.pack(fill="x", padx=10, pady=5)

            details_text = tk.Text(details_frame, height=6, wrap=tk.WORD)
            details_text.pack(fill="x", padx=5, pady=5)

            status_label = ttk.Label(dialog, text="Ready to scan")
            status_label.pack(pady=5)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(dialog, variable=progress_var, maximum=100)
            progress_bar.pack(fill="x", padx=10, pady=5)

            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill="x", padx=10, pady=10)

            scan_btn = ttk.Button(
                buttons_frame, text="Start Scan",
                command=lambda: self._start_permission_scan(dialog, tree, details_text, status_label, progress_var, scan_btn)
            )
            scan_btn.pack(side="left", padx=5)

            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open scan dialog: {str(e)}")

    def _start_permission_scan(self, dialog, tree, details_text, status_label, progress_var, scan_btn):
        """Start scanning for dangerous permissions"""
        scan_btn.config(state="disabled")

        def update_status(message, progress=None):
            dialog.after(0, lambda: status_label.config(text=message))
            if progress is not None:
                dialog.after(0, lambda: progress_var.set(progress))

        def scan_complete():
            dialog.after(0, lambda: scan_btn.config(state="normal"))

        def scan_thread():
            try:
                serial = self.device_serial
                adb_cmd = self.adb_path if IS_WINDOWS else "adb"

                # Dangerous permissions to check
                dangerous_permissions = [
                    "android.permission.READ_CONTACTS",
                    "android.permission.WRITE_CONTACTS",
                    "android.permission.READ_CALL_LOG",
                    "android.permission.WRITE_CALL_LOG",
                    "android.permission.READ_CALENDAR",
                    "android.permission.WRITE_CALENDAR",
                    "android.permission.CAMERA",
                    "android.permission.RECORD_AUDIO",
                    "android.permission.ACCESS_FINE_LOCATION",
                    "android.permission.ACCESS_COARSE_LOCATION",
                    "android.permission.READ_PHONE_STATE",
                    "android.permission.READ_SMS",
                    "android.permission.SEND_SMS",
                    "android.permission.READ_EXTERNAL_STORAGE",
                    "android.permission.WRITE_EXTERNAL_STORAGE",
                ]

                update_status("Getting package list...", 0)

                # Get all packages
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=30
                )

                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        packages.append(line[8:].strip())

                total = len(packages)

                for i, package in enumerate(packages):
                    progress = (i / total) * 100
                    update_status(f"Scanning {package}...", progress)

                    # Get permissions for package
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "dumpsys", "package", package],
                        capture_output=True, text=True, timeout=10
                    )

                    found_permissions = []
                    for perm in dangerous_permissions:
                        if perm in result.stdout:
                            found_permissions.append(perm.split('.')[-1])

                    if found_permissions:
                        dialog.after(0, lambda p=package, perms=found_permissions:
                            tree.insert("", "end", text=p, values=(", ".join(perms),))
                        )

                update_status("Scan complete!", 100)
                scan_complete()

            except Exception as e:
                update_status(f"Error: {str(e)}", 0)
                scan_complete()

        threading.Thread(target=scan_thread, daemon=True).start()

    def _check_certificates(self):
        """Check installed certificates"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Installed Certificates")
            dialog.geometry("700x500")

            x_pos = (self.winfo_screenwidth() - 700) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=25, width=80)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            text_widget.insert(tk.END, "===== Installed Certificates =====\n\n")
            text_widget.insert(tk.END, "Loading...\n")

            def load_certs():
                try:
                    # Get system certificates
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "ls /system/etc/security/cacerts/"],
                        capture_output=True, text=True, timeout=10
                    )

                    dialog.after(0, lambda: [
                        text_widget.delete(1.0, tk.END),
                        text_widget.insert(tk.END, "===== System CA Certificates =====\n\n")
                    ])

                    if result.returncode == 0:
                        certs = result.stdout.strip().split('\n')
                        dialog.after(0, lambda: text_widget.insert(tk.END, f"Found {len(certs)} system certificates\n\n"))

                        # Show first few certificates
                        for cert in certs[:20]:
                            dialog.after(0, lambda c=cert: text_widget.insert(tk.END, f"  {c}\n"))

                        if len(certs) > 20:
                            dialog.after(0, lambda: text_widget.insert(tk.END, f"\n... and {len(certs) - 20} more\n"))

                    # Get user certificates
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "ls /data/misc/user/0/cacerts-added/ 2>/dev/null"],
                        capture_output=True, text=True, timeout=10
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        user_certs = result.stdout.strip().split('\n')
                        dialog.after(0, lambda: [
                            text_widget.insert(tk.END, "\n\n===== User-Installed CA Certificates =====\n\n"),
                            text_widget.insert(tk.END, f"Found {len(user_certs)} user certificates\n\n")
                        ])
                        for cert in user_certs:
                            dialog.after(0, lambda c=cert: text_widget.insert(tk.END, f"  {c}\n"))
                    else:
                        dialog.after(0, lambda: text_widget.insert(tk.END,
                            "\n\n===== User-Installed CA Certificates =====\n\nNo user certificates installed\n"))

                except Exception as e:
                    dialog.after(0, lambda: text_widget.insert(tk.END, f"\nError: {str(e)}"))

            threading.Thread(target=load_certs, daemon=True).start()

            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to check certificates: {str(e)}")

    def _verify_boot_integrity(self):
        """Verify boot integrity status"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Boot Integrity")
            dialog.geometry("500x400")

            x_pos = (self.winfo_screenwidth() - 500) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Boot Integrity Check", font=("Arial", 12, "bold")).pack(pady=(0, 20))

            status_labels = {}

            checks = [
                ("Verified Boot", "ro.boot.verifiedbootstate"),
                ("Boot Mode", "ro.boot.mode"),
                ("Secure Boot", "ro.boot.secureboot"),
                ("Device State", "ro.boot.device_state"),
                ("Warranty Bit", "ro.warranty_bit"),
            ]

            for label, prop in checks:
                frame = ttk.Frame(main_frame)
                frame.pack(fill="x", pady=5)
                ttk.Label(frame, text=f"{label}:", width=20, anchor="w").pack(side="left")
                status_var = tk.StringVar(value="Checking...")
                status_labels[prop] = status_var
                ttk.Label(frame, textvariable=status_var).pack(side="left")

            details_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=8, width=50)
            details_text.pack(fill="both", expand=True, pady=10)

            def check_integrity():
                for label, prop in checks:
                    try:
                        result = subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "getprop", prop],
                            capture_output=True, text=True, timeout=5
                        )
                        value = result.stdout.strip() or "Not available"
                        dialog.after(0, lambda p=prop, v=value: status_labels[p].set(v))
                    except Exception as e:
                        dialog.after(0, lambda p=prop: status_labels[p].set("Error"))

                # Get additional info
                try:
                    result = subprocess.run(
                        [adb_cmd, "-s", serial, "shell", "getprop | grep boot"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        dialog.after(0, lambda: [
                            details_text.delete(1.0, tk.END),
                            details_text.insert(tk.END, "All boot-related properties:\n\n"),
                            details_text.insert(tk.END, result.stdout)
                        ])
                except Exception as e:
                    dialog.after(0, lambda: details_text.insert(tk.END, f"Error: {str(e)}"))

            threading.Thread(target=check_integrity, daemon=True).start()

            ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to verify boot integrity: {str(e)}")

    def _check_appops_dialog(self):
        """Show dialog to check AppOps for a package"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Check AppOps")
        dialog.geometry("750x850")

        x_pos = (self.winfo_screenwidth() - 600) // 2
        y_pos = (self.winfo_screenheight() - 400) // 2
        dialog.geometry(f"+{x_pos}+{y_pos}")

        ttk.Label(dialog, text="Package Name:").pack(pady=(10, 5), padx=10, anchor="w")
        pkg_entry = ttk.Entry(dialog)
        pkg_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(dialog, text="AppOps Status:").pack(pady=(10, 5), padx=10, anchor="w")
        output_text = tk.Text(dialog, height=15)
        output_text.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def check_appops():
            pkg = pkg_entry.get().strip()
            if not pkg:
                messagebox.showerror("Error", "Please enter a package name")
                return

            serial = self.device_info.get("serial", "")
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            try:
                cmd = [adb_cmd, "-s", serial, "shell", "appops", "get", pkg]
                process = subprocess.run(cmd, capture_output=True, text=True)

                output_text.delete(1.0, tk.END)
                if process.returncode == 0:
                    output_text.insert(tk.END, f"AppOps for {pkg}:\n")
                    output_text.insert(tk.END, process.stdout)
                else:
                    output_text.insert(tk.END, f"Error: {process.stderr}")
            except Exception as e:
                output_text.insert(tk.END, f"Error: {str(e)}")

        ttk.Button(btn_frame, text="Check", command=check_appops).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        pkg_entry.focus_set()

    def _change_appops_dialog(self):
        """Show dialog to change AppOps for a package"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Change AppOps")
        dialog.geometry("400x300")

        x_pos = (self.winfo_screenwidth() - 400) // 2
        y_pos = (self.winfo_screenheight() - 300) // 2
        dialog.geometry(f"+{x_pos}+{y_pos}")

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Package Name:").pack(anchor="w", pady=(0, 5))
        pkg_entry = ttk.Entry(main_frame)
        pkg_entry.pack(fill="x", pady=(0, 10))

        ttk.Label(main_frame, text="Operation:").pack(anchor="w", pady=(0, 5))
        op_combo = ttk.Combobox(main_frame, values=[
            "READ_CONTACTS", "WRITE_CONTACTS", "READ_CALL_LOG", "WRITE_CALL_LOG",
            "READ_CALENDAR", "WRITE_CALENDAR", "READ_SMS", "RECEIVE_SMS",
            "SEND_SMS", "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE",
            "CAMERA", "RECORD_AUDIO", "COARSE_LOCATION", "FINE_LOCATION"
        ])
        op_combo.pack(fill="x", pady=(0, 10))

        ttk.Label(main_frame, text="Mode:").pack(anchor="w", pady=(0, 5))
        mode_combo = ttk.Combobox(main_frame, values=["allow", "deny", "ignore", "default"])
        mode_combo.pack(fill="x", pady=(0, 10))

        status_label = ttk.Label(main_frame, text="")
        status_label.pack(pady=5)

        def change_permission():
            pkg = pkg_entry.get().strip()
            op = op_combo.get().strip()
            mode = mode_combo.get().strip()

            if not pkg or not op or not mode:
                messagebox.showerror("Error", "Please fill all fields")
                return

            serial = self.device_info.get("serial", "")
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            try:
                cmd = [adb_cmd, "-s", serial, "shell", "appops", "set", pkg, op, mode]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    status_label.config(text=f"Successfully set {op} to {mode} for {pkg}")
                else:
                    status_label.config(text=f"Error: {result.stderr}")

            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_frame, text="Apply", command=change_permission).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)
