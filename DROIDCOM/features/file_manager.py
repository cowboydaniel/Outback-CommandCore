"""
DROIDCOM - File Manager Feature Module
Handles file operations between PC and Android device.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import time

from ..constants import IS_WINDOWS


class FileManagerMixin:
    """Mixin class providing file management functionality."""

    def manage_files(self):
        """Manage files on the connected Android device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        # Create file manager window
        file_manager = tk.Toplevel(self)
        file_manager.title("Android File Manager")
        file_manager.geometry("950x600")
        file_manager.minsize(800, 500)

        # Center the window
        x_pos = (self.winfo_screenwidth() - 950) // 2
        y_pos = (self.winfo_screenheight() - 600) // 2
        file_manager.geometry(f"+{x_pos}+{y_pos}")

        # Initialize variables
        self.android_path = tk.StringVar(value="/sdcard")
        self.local_path = tk.StringVar(value=os.path.expanduser("~"))
        self.fm_status = tk.StringVar(value="Ready")

        # Main frame
        main_frame = ttk.Frame(file_manager, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Device info bar
        device_frame = ttk.Frame(main_frame)
        device_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            device_frame,
            text=f"Device: {self.device_info.get('model')} ({self.device_info.get('serial')})",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        ttk.Label(
            device_frame,
            textvariable=self.fm_status
        ).pack(side="right")

        # Create paned window
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # LOCAL FILES FRAME
        local_frame = ttk.LabelFrame(paned, text="Local Files", padding=10)
        paned.add(local_frame, weight=1)

        # Local path navigation
        local_nav = ttk.Frame(local_frame)
        local_nav.pack(fill="x", pady=(0, 5))

        ttk.Label(local_nav, text="Location:").pack(side="left", padx=(0, 5))
        local_path_entry = ttk.Entry(local_nav, textvariable=self.local_path, width=40)
        local_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            local_nav, text="Go", width=5,
            command=lambda: self._refresh_local_files(local_files_tree)
        ).pack(side="left")

        ttk.Button(
            local_nav, text="Home", width=8,
            command=lambda: [self.local_path.set(os.path.expanduser("~")), self._refresh_local_files(local_files_tree)]
        ).pack(side="left", padx=5)

        ttk.Button(
            local_nav, text="Up", width=5,
            command=lambda: [self.local_path.set(os.path.dirname(self.local_path.get())), self._refresh_local_files(local_files_tree)]
        ).pack(side="left")

        # Local files tree
        local_files_frame = ttk.Frame(local_frame)
        local_files_frame.pack(fill="both", expand=True)

        local_scrollbar = ttk.Scrollbar(local_files_frame)
        local_scrollbar.pack(side="right", fill="y")

        local_files_tree = ttk.Treeview(
            local_files_frame,
            columns=("size", "date"),
            yscrollcommand=local_scrollbar.set
        )
        local_files_tree.pack(side="left", fill="both", expand=True)

        local_scrollbar.config(command=local_files_tree.yview)

        local_files_tree.column("#0", width=250, minwidth=150)
        local_files_tree.column("size", width=100, minwidth=80, anchor="e")
        local_files_tree.column("date", width=150, minwidth=100)

        local_files_tree.heading("#0", text="Name")
        local_files_tree.heading("size", text="Size")
        local_files_tree.heading("date", text="Date Modified")

        # Local button bar
        local_btn_frame = ttk.Frame(local_frame)
        local_btn_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(
            local_btn_frame, text="Refresh",
            command=lambda: self._refresh_local_files(local_files_tree)
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            local_btn_frame, text="Upload to Device",
            command=lambda: self._upload_to_device(local_files_tree, android_files_tree)
        ).pack(side="left")

        # ANDROID FILES FRAME
        android_frame = ttk.LabelFrame(paned, text="Android Device Files", padding=10)
        paned.add(android_frame, weight=1)

        # Android path navigation
        android_nav = ttk.Frame(android_frame)
        android_nav.pack(fill="x", pady=(0, 5))

        ttk.Label(android_nav, text="Location:").pack(side="left", padx=(0, 5))
        android_path_entry = ttk.Entry(android_nav, textvariable=self.android_path, width=40)
        android_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            android_nav, text="Go", width=5,
            command=lambda: self._refresh_android_files(android_files_tree)
        ).pack(side="left")

        # Standard locations dropdown
        locations = [
            "/sdcard",
            "/sdcard/DCIM",
            "/sdcard/Download",
            "/sdcard/Pictures",
            "/sdcard/Movies",
            "/sdcard/Music",
            "/sdcard/Documents"
        ]

        location_var = tk.StringVar()
        location_dropdown = ttk.Combobox(
            android_nav, textvariable=location_var,
            values=locations, width=15, state="readonly"
        )
        location_dropdown.pack(side="left", padx=5)

        location_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda e: [self.android_path.set(location_var.get()), self._refresh_android_files(android_files_tree)]
        )

        ttk.Button(
            android_nav, text="Up", width=5,
            command=lambda: [
                self.android_path.set(os.path.dirname(self.android_path.get()) or "/"),
                self._refresh_android_files(android_files_tree)
            ]
        ).pack(side="left")

        # Android files tree
        android_files_frame = ttk.Frame(android_frame)
        android_files_frame.pack(fill="both", expand=True)

        android_scrollbar = ttk.Scrollbar(android_files_frame)
        android_scrollbar.pack(side="right", fill="y")

        android_files_tree = ttk.Treeview(
            android_files_frame,
            columns=("size", "date"),
            yscrollcommand=android_scrollbar.set
        )
        android_files_tree.pack(side="left", fill="both", expand=True)

        android_scrollbar.config(command=android_files_tree.yview)

        android_files_tree.column("#0", width=250, minwidth=150)
        android_files_tree.column("size", width=100, minwidth=80, anchor="e")
        android_files_tree.column("date", width=150, minwidth=100)

        android_files_tree.heading("#0", text="Name")
        android_files_tree.heading("size", text="Size")
        android_files_tree.heading("date", text="Date Modified")

        # Android button bar
        android_btn_frame = ttk.Frame(android_frame)
        android_btn_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(
            android_btn_frame, text="Refresh",
            command=lambda: self._refresh_android_files(android_files_tree)
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            android_btn_frame, text="Download to PC",
            command=lambda: self._download_from_device(android_files_tree, local_files_tree)
        ).pack(side="left")

        # Initialize file listings
        self._refresh_local_files(local_files_tree)
        self._refresh_android_files(android_files_tree)

        # Set up double-click navigation
        local_files_tree.bind("<Double-1>", lambda e: self._on_local_double_click(e, local_files_tree))
        android_files_tree.bind("<Double-1>", lambda e: self._on_android_double_click(e, android_files_tree))

    def _refresh_local_files(self, tree):
        """Refresh the local files tree"""
        for item in tree.get_children():
            tree.delete(item)

        current_path = self.local_path.get()

        if not os.path.exists(current_path):
            messagebox.showerror("Invalid Path", f"The path {current_path} does not exist.")
            self.local_path.set(os.path.expanduser("~"))
            current_path = self.local_path.get()

        try:
            tree.insert("", "end", text="..", values=("<DIR>", ""), tags=("dir",))

            dirs = []
            files = []

            for item in os.listdir(current_path):
                full_path = os.path.join(current_path, item)

                try:
                    stats = os.stat(full_path)
                    size = stats.st_size
                    modified = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_mtime))

                    if os.path.isdir(full_path):
                        dirs.append((item, "<DIR>", modified))
                    else:
                        size_str = self._format_size(size)
                        files.append((item, size_str, modified))
                except Exception:
                    pass

            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())

            for name, size, date in dirs:
                tree.insert("", "end", text=name, values=(size, date), tags=("dir",))

            for name, size, date in files:
                tree.insert("", "end", text=name, values=(size, date), tags=("file",))

            self.fm_status.set(f"Local: {len(dirs)} dirs, {len(files)} files")

        except Exception as e:
            messagebox.showerror("Error", f"Error reading directory: {str(e)}")

    def _refresh_android_files(self, tree):
        """Refresh the Android files tree"""
        for item in tree.get_children():
            tree.delete(item)

        try:
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
                return

            current_path = self.android_path.get()

            tree.insert("", "end", text="..", values=("<DIR>", ""), tags=("dir",))

            dirs = []
            files = []

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', f"ls -la {current_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.log_message(f"Error listing files: {result.stderr.strip()}")
                self.fm_status.set("Error listing files")
                return

            lines = result.stdout.strip().split("\n")

            if lines and lines[0].startswith("total"):
                lines = lines[1:]

            for line in lines:
                parts = line.split()
                if len(parts) >= 8:
                    perms = parts[0]

                    if len(parts) > 8:
                        name = " ".join(parts[8:])
                    else:
                        name = parts[8]

                    if name == "." or name == "..":
                        continue

                    size = parts[4]
                    date = " ".join(parts[5:8])

                    if perms.startswith("d"):
                        dirs.append((name, "<DIR>", date))
                    else:
                        try:
                            size_str = self._format_size(int(size))
                        except ValueError:
                            size_str = size
                        files.append((name, size_str, date))

            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())

            for name, size, date in dirs:
                tree.insert("", "end", text=name, values=(size, date), tags=("dir",))

            for name, size, date in files:
                tree.insert("", "end", text=name, values=(size, date), tags=("file",))

            self.fm_status.set(f"Android: {len(dirs)} dirs, {len(files)} files")

        except Exception as e:
            self.log_message(f"Error refreshing Android files: {str(e)}")
            self.fm_status.set("Error listing files")

    def _on_local_double_click(self, event, tree):
        """Handle double-click on local files tree"""
        selection = tree.selection()
        if not selection:
            return

        item_id = selection[0]
        item_text = tree.item(item_id, "text")
        item_tags = tree.item(item_id, "tags")

        if "dir" not in item_tags:
            return

        if item_text == "..":
            new_path = os.path.dirname(self.local_path.get())
            self.local_path.set(new_path)
        else:
            new_path = os.path.join(self.local_path.get(), item_text)
            self.local_path.set(new_path)

        self._refresh_local_files(tree)

    def _on_android_double_click(self, event, tree):
        """Handle double-click on Android files tree"""
        selection = tree.selection()
        if not selection:
            return

        item_id = selection[0]
        item_text = tree.item(item_id, "text")
        item_tags = tree.item(item_id, "tags")

        if "dir" not in item_tags:
            return

        if item_text == "..":
            current_path = self.android_path.get()
            if current_path == "/":
                return

            new_path = os.path.dirname(current_path)
            if not new_path:
                new_path = "/"

            self.android_path.set(new_path)
        else:
            new_path = os.path.join(self.android_path.get(), item_text)
            self.android_path.set(new_path)

        self._refresh_android_files(tree)

    def _upload_to_device(self, local_tree, android_tree):
        """Upload selected file from PC to Android device"""
        selection = local_tree.selection()
        if not selection:
            messagebox.showinfo("No File Selected", "Please select a file to upload.")
            return

        item_ids = local_tree.selection()

        for item_id in item_ids:
            item_text = local_tree.item(item_id, "text")

            if item_text == "..":
                continue

            item_tags = local_tree.item(item_id, "tags")
            source_path = os.path.join(self.local_path.get(), item_text)
            target_path = self.android_path.get()

            self._run_in_thread(lambda src=source_path, tgt=target_path, is_dir="dir" in item_tags:
                               self._upload_file_task(src, tgt, is_dir, android_tree))

    def _upload_file_task(self, source_path, target_path, is_directory, tree):
        """Worker thread to upload file/directory to device"""
        try:
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
                return

            name = os.path.basename(source_path)

            self.fm_status.set(f"Uploading {name}...")
            self.log_message(f"Uploading {name} to {target_path}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'push', source_path, target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.log_message(f"Upload failed: {result.stderr.strip()}")
                self.fm_status.set("Upload failed")
                messagebox.showerror("Upload Error", f"Failed to upload {name}: {result.stderr.strip()}")
                return

            self.log_message(f"Upload of {name} completed successfully")
            self.fm_status.set("Upload complete")

            self.after(0, lambda: self._refresh_android_files(tree))

        except Exception as e:
            self.log_message(f"Error during upload: {str(e)}")
            self.fm_status.set("Upload failed")
            messagebox.showerror("Upload Error", f"Failed to upload file: {str(e)}")

    def _download_from_device(self, android_tree, local_tree):
        """Download selected file from Android device to PC"""
        selection = android_tree.selection()
        if not selection:
            messagebox.showinfo("No File Selected", "Please select a file to download.")
            return

        item_ids = android_tree.selection()

        for item_id in item_ids:
            item_text = android_tree.item(item_id, "text")

            if item_text == "..":
                continue

            item_tags = android_tree.item(item_id, "tags")
            source_path = os.path.join(self.android_path.get(), item_text)
            target_path = self.local_path.get()

            self._run_in_thread(lambda src=source_path, tgt=target_path, is_dir="dir" in item_tags:
                               self._download_file_task(src, tgt, is_dir, local_tree))

    def _download_file_task(self, source_path, target_path, is_directory, tree):
        """Worker thread to download file/directory from device"""
        try:
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
                return

            name = os.path.basename(source_path)

            self.fm_status.set(f"Downloading {name}...")
            self.log_message(f"Downloading {name} to {target_path}...")

            result = subprocess.run(
                [adb_cmd, '-s', serial, 'pull', source_path, target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.log_message(f"Download failed: {result.stderr.strip()}")
                self.fm_status.set("Download failed")
                messagebox.showerror("Download Error", f"Failed to download {name}: {result.stderr.strip()}")
                return

            self.log_message(f"Download of {name} completed successfully")
            self.fm_status.set("Download complete")

            self.after(0, lambda: self._refresh_local_files(tree))

        except Exception as e:
            self.log_message(f"Error during download: {str(e)}")
            self.fm_status.set("Download failed")
            messagebox.showerror("Download Error", f"Failed to download file: {str(e)}")

    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']

        if size_bytes == 0:
            return "0 B"

        i = 0
        size = float(size_bytes)
        while size >= 1024.0 and i < len(units) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.2f} {units[i]}"

    def _pull_from_device(self):
        """Pull a file from device to PC"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return
        # This opens the file manager for download
        self.manage_files()

    def _push_to_device(self):
        """Push a file from PC to device"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return
        # This opens the file manager for upload
        self.manage_files()
