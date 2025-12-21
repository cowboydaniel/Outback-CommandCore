"""
DROIDCOM - Backup Feature Module
Handles device backup and restore functionality.
"""

from ..ui.qt_compat import tk
from ..ui.qt_compat import ttk, messagebox, filedialog
import subprocess
import os
import json
import time

from ..constants import IS_WINDOWS


class BackupMixin:
    """Mixin class providing backup functionality."""

    def backup_device(self):
        """Backup the connected Android device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        # Ask for backup directory
        backup_path = filedialog.askdirectory(title="Select Backup Directory")

        if not backup_path:
            return

        # Show backup options dialog
        backup_dialog = tk.Toplevel(self)
        backup_dialog.title("Backup Options")
        backup_dialog.geometry("750x850")
        backup_dialog.resizable(False, False)

        # Center the dialog
        x_pos = (self.winfo_screenwidth() - 400) // 2
        y_pos = (self.winfo_screenheight() - 450) // 2
        backup_dialog.geometry(f"+{x_pos}+{y_pos}")

        backup_dialog.transient(self)
        backup_dialog.grab_set()

        # Main frame
        main_frame = ttk.Frame(backup_dialog, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main_frame, text="Android Backup Options", font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        # Backup options frame
        options_frame = ttk.LabelFrame(main_frame, text="Backup Content", padding=10)
        options_frame.pack(fill="x", pady=5)

        # Checkboxes
        backup_options = {}

        backup_options['apps'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Apps and App Data",
            variable=backup_options['apps']
        ).pack(anchor="w", pady=2)

        backup_options['system'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="System Settings",
            variable=backup_options['system']
        ).pack(anchor="w", pady=2)

        backup_options['media'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, text="Media (Photos, Videos, Music)",
            variable=backup_options['media']
        ).pack(anchor="w", pady=2)

        backup_options['documents'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, text="Documents and Downloads",
            variable=backup_options['documents']
        ).pack(anchor="w", pady=2)

        backup_options['shared'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, text="Shared Storage",
            variable=backup_options['shared']
        ).pack(anchor="w", pady=2)

        # Advanced options
        adv_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding=10)
        adv_frame.pack(fill="x", pady=5)

        backup_options['encrypt'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            adv_frame, text="Encrypt Backup (Password Protected)",
            variable=backup_options['encrypt']
        ).pack(anchor="w", pady=2)

        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=15)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=10)

        btn_container = ttk.Frame(buttons_frame)
        btn_container.pack(fill="x")

        cancel_btn = ttk.Button(
            btn_container, text="Cancel", width=15,
            command=backup_dialog.destroy
        )
        cancel_btn.pack(side="right", padx=5)

        start_btn = ttk.Button(
            btn_container, text="Start Backup", width=15,
            command=lambda: self._start_backup(backup_dialog, backup_path, backup_options)
        )
        start_btn.pack(side="right", padx=5)

        self.wait_window(backup_dialog)

    def _start_backup(self, dialog, backup_path, options):
        """Start the backup process"""
        dialog.destroy()
        self._run_in_thread(lambda: self._backup_task(backup_path, options))

    def _backup_task(self, backup_path, options):
        """Worker thread to perform the Android device backup"""
        try:
            self.update_status("Backing up device...")
            self.log_message("Starting Android device backup...")

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
                self.update_status("Backup failed")
                return

            # Create backup directory
            device_model = self.device_info.get('model', 'Android').replace(' ', '_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(backup_path, f"{device_model}_{timestamp}_backup")
            os.makedirs(backup_folder, exist_ok=True)

            self.log_message(f"Saving backup to: {backup_folder}")

            # Build backup command
            backup_flags = []

            if options['apps'].get():
                backup_flags.append("-apk")
                backup_flags.append("-all")

            if options['system'].get():
                backup_flags.append("-system")

            if options['shared'].get():
                backup_flags.append("-shared")

            backup_file = os.path.join(backup_folder, "backup.ab")

            cmd = [adb_cmd, '-s', serial, 'backup']
            cmd.extend(backup_flags)
            cmd.extend(["-f", backup_file])

            self.log_message("Starting ADB backup (you may need to confirm on your device)")
            self.update_status("Backup in progress...")

            self.after(0, lambda: messagebox.showinfo(
                "Backup Started",
                "The backup process has started. You may need to unlock your device and confirm the backup.\n\n"
                "Please DO NOT disconnect your device until the backup is complete."
            ))

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.log_message(f"Backup failed: {result.stderr.strip()}")
                self.update_status("Backup failed")
                messagebox.showerror("Backup Error", f"Failed to backup device: {result.stderr.strip()}")
                return

            # Backup files if selected
            if options['media'].get() or options['documents'].get():
                self._backup_files(adb_cmd, serial, backup_folder, options)

            # Create backup info file
            self._create_backup_info(backup_folder, options)

            self.log_message("Device backup completed successfully")
            self.update_status("Backup completed")

            messagebox.showinfo(
                "Backup Complete",
                f"Your device has been successfully backed up to:\n{backup_folder}"
            )

        except subprocess.TimeoutExpired:
            self.log_message("Backup timeout - this may be normal if the backup is large")
            self.update_status("Backup in progress on device")
            messagebox.showinfo(
                "Backup In Progress",
                "The backup is being processed on your device. This may take some time.\n\n"
                "You will need to confirm the backup on your device and wait for it to complete."
            )
        except Exception as e:
            self.log_message(f"Error during backup: {str(e)}")
            self.update_status("Backup failed")
            messagebox.showerror("Backup Error", f"Failed to backup device: {str(e)}")

    def _backup_files(self, adb_cmd, serial, backup_folder, options):
        """Backup files from the device"""
        try:
            if options['media'].get():
                media_folder = os.path.join(backup_folder, "Media")
                os.makedirs(os.path.join(media_folder, "Pictures"), exist_ok=True)
                os.makedirs(os.path.join(media_folder, "Videos"), exist_ok=True)
                os.makedirs(os.path.join(media_folder, "Music"), exist_ok=True)

                self.log_message("Backing up photos...")
                self.update_status("Backing up photos...")

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/DCIM', os.path.join(media_folder, "Pictures")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Movies', os.path.join(media_folder, "Videos")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Music', os.path.join(media_folder, "Music")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            if options['documents'].get():
                docs_folder = os.path.join(backup_folder, "Documents")
                os.makedirs(docs_folder, exist_ok=True)

                self.log_message("Backing up documents...")
                self.update_status("Backing up documents...")

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Documents', docs_folder],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                subprocess.run(
                    [adb_cmd, '-s', serial, 'pull', '/sdcard/Download', docs_folder],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

        except Exception as e:
            self.log_message(f"Error backing up files: {str(e)}")

    def _create_backup_info(self, backup_folder, options):
        """Create a backup info file with details about the backup"""
        try:
            backup_info = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'device_info': self.device_info,
                'backup_options': {k: v.get() for k, v in options.items() if hasattr(v, 'get')}
            }

            info_file = os.path.join(backup_folder, "backup_info.json")
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=4)

        except Exception as e:
            self.log_message(f"Error creating backup info: {str(e)}")
