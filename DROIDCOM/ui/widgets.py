"""
DROIDCOM - Widgets Module
Contains widget creation and UI-related functionality.
"""

from .qt_compat import tk, ttk
import threading
import time
import logging

from ..constants import IS_WINDOWS


class WidgetsMixin:
    """Mixin class providing widget creation and UI utility methods."""

    def create_widgets(self):
        """Create the main UI widgets"""
        # Create main container frame that fills the entire window
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True)

        # Ensure the main container uses all available space
        self.pack_propagate(False)

        # Create a simple frame for content (no scrolling)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill="both", expand=True)

        # Set minimum size for the container
        self.update_idletasks()  # Force geometry update
        min_width = max(1024, main_container.winfo_width())  # Ensure minimum width

        # Main header with logo
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill="x", padx=10, pady=5)

        header_label = ttk.Label(
            header_frame, text="Android Device Management", font=("Arial", 14, "bold")
        )
        header_label.pack(side="left", pady=10)

        # Setup status frame for tools
        self.setup_status_frame = ttk.LabelFrame(content_frame, text="Tools Status")
        self.setup_status_frame.pack(fill="x", padx=10, pady=5, expand=False)

        # Check Platform Tools (ADB)
        tools_status = "✅ Installed" if self.platform_tools_installed else "❌ Not Installed"
        self.tools_label = ttk.Label(
            self.setup_status_frame, text=f"Android Platform Tools: {tools_status}", font=("Arial", 10)
        )
        self.tools_label.pack(anchor="w", padx=5, pady=2)

        # Tools installation button
        if not self.platform_tools_installed:
            tools_frame = ttk.Frame(self.setup_status_frame)
            tools_frame.pack(fill="x", padx=5, pady=5)

            tools_btn = ttk.Button(
                tools_frame, text="Install Android Platform Tools", command=self.install_platform_tools,
                width=30  # Explicitly set width to ensure text fits
            )
            tools_btn.pack(side="left", padx=5, pady=5)

        # Main content area with tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Device Info Tab
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="Device Info")

        # Device connection frame
        connection_frame = ttk.LabelFrame(self.device_frame, text="Device Connection")
        connection_frame.pack(fill="x", padx=10, pady=10, expand=False)

        # Connection buttons frame
        conn_buttons_frame = ttk.Frame(connection_frame)
        conn_buttons_frame.pack(fill="x", padx=5, pady=5)

        # Connect button
        self.connect_btn = ttk.Button(
            conn_buttons_frame, text="Connect Device", command=self.connect_device,
            width=20  # Explicitly set width to ensure text fits
        )
        self.connect_btn.pack(side="left", padx=5, pady=5)

        # WiFi ADB button
        self.wifi_adb_btn = ttk.Button(
            conn_buttons_frame, text="WiFi ADB", command=self.setup_wifi_adb,
            width=20  # Explicitly set width to ensure text fits
        )
        self.wifi_adb_btn.pack(side="left", padx=5, pady=5)

        # Refresh button
        self.refresh_btn = ttk.Button(
            conn_buttons_frame, text="Refresh Devices", command=self.refresh_device_list,
            width=20  # Explicitly set width to ensure text fits
        )
        self.refresh_btn.pack(side="left", padx=5, pady=5)

        # Remove Offline Devices button
        self.remove_offline_btn = ttk.Button(
            conn_buttons_frame, text="Remove Offline", command=self.remove_offline_devices,
            width=20  # Explicitly set width to ensure text fits
        )
        self.remove_offline_btn.pack(side="left", padx=5, pady=5)

        # Device list frame
        list_frame = ttk.Frame(connection_frame)
        list_frame.pack(fill="x", padx=5, pady=5)

        # Device list label
        list_label = ttk.Label(list_frame, text="Available Devices:")
        list_label.pack(anchor="w", padx=5, pady=2)

        # Device listbox without scrollbar
        list_subframe = ttk.Frame(list_frame)
        list_subframe.pack(fill="x", padx=5, pady=2)

        self.device_listbox = tk.Listbox(list_subframe, height=3)
        self.device_listbox.pack(side="left", fill="x", expand=True)

        # Device info display
        device_info_frame = ttk.LabelFrame(self.device_frame, text="Device Information")
        device_info_frame.pack(fill="both", padx=10, pady=10, expand=True)

        # Device info content - simple grid layout instead of columns
        info_content = ttk.Frame(device_info_frame)
        info_content.pack(fill="both", expand=True, padx=10, pady=10)

        # Basic device info fields (left column)
        self.info_fields = {
            "Model": tk.StringVar(value="N/A"),
            "Manufacturer": tk.StringVar(value="N/A"),
            "Android Version": tk.StringVar(value="N/A"),
            "Serial Number": tk.StringVar(value="N/A"),
            "IMEI": tk.StringVar(value="N/A"),
            "Battery Level": tk.StringVar(value="N/A"),
        }

        # Advanced device info fields (right column)
        self.adv_info_fields = {
            "Storage": tk.StringVar(value="N/A"),
            "RAM": tk.StringVar(value="N/A"),
            "Screen Resolution": tk.StringVar(value="N/A"),
            "CPU": tk.StringVar(value="N/A"),
            "Kernel": tk.StringVar(value="N/A"),
        }

        # Create a simple grid layout with 2 columns for all fields
        # Configure grid columns to have consistent width
        info_content.columnconfigure(0, minsize=150)  # Label column
        info_content.columnconfigure(1, minsize=150)  # Value column
        info_content.columnconfigure(2, minsize=150)  # Label column 2
        info_content.columnconfigure(3, minsize=150)  # Value column 2

        # Add a heading for basic info
        ttk.Label(
            info_content, text="Basic Information", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))

        # Add a heading for advanced info
        ttk.Label(
            info_content, text="Advanced Information", font=("Arial", 10, "bold")
        ).grid(row=0, column=2, columnspan=2, sticky="w", padx=5, pady=(5, 10))

        # Add a heading for debug info (at the bottom of the grid)
        max_rows = max(len(self.info_fields), len(self.adv_info_fields)) + 2
        ttk.Label(
            info_content, text="Debug Information", font=("Arial", 10, "bold")
        ).grid(row=max_rows, column=0, columnspan=4, sticky="w", padx=5, pady=(15, 5))

        # Add the debug text area
        debug_frame = ttk.Frame(info_content)
        debug_frame.grid(row=max_rows+1, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

        # Create a text widget for debug info (no scrollbar)
        self.debug_text = tk.Text(debug_frame, height=5, width=80, wrap=tk.WORD)
        self.debug_text.pack(fill="both", expand=True)

        # Make text read-only
        self.debug_text.config(state="disabled")

        # Add basic info fields - first column
        row = 1
        for label_text, var in self.info_fields.items():
            ttk.Label(
                info_content, text=f"{label_text}:", font=("Arial", 9, "bold")
            ).grid(row=row, column=0, sticky="w", padx=5, pady=5)

            ttk.Label(
                info_content, textvariable=var
            ).grid(row=row, column=1, sticky="w", padx=5, pady=5)

            row += 1

        # Add advanced info fields - second column
        row = 1
        for label_text, var in self.adv_info_fields.items():
            ttk.Label(
                info_content, text=f"{label_text}:", font=("Arial", 9, "bold")
            ).grid(row=row, column=2, sticky="w", padx=5, pady=5)

            ttk.Label(
                info_content, textvariable=var
            ).grid(row=row, column=3, sticky="w", padx=5, pady=5)

            row += 1

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

        # Device actions frame
        actions_frame = ttk.LabelFrame(self.device_frame, text="Device Actions")
        actions_frame.pack(fill="x", padx=10, pady=(5, 10), expand=False)

        # Action buttons
        actions_buttons_frame = ttk.Frame(actions_frame)
        actions_buttons_frame.pack(fill="x", padx=5, pady=5)

        # Row 1 of buttons
        self.screenshot_btn = ttk.Button(
            actions_buttons_frame, text="Take Screenshot", command=self.take_screenshot, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.screenshot_btn.grid(row=0, column=0, padx=5, pady=5)

        self.backup_btn = ttk.Button(
            actions_buttons_frame, text="Backup Device", command=self.backup_device, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.backup_btn.grid(row=0, column=1, padx=5, pady=5)

        self.files_btn = ttk.Button(
            actions_buttons_frame, text="Manage Files", command=self.manage_files, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.files_btn.grid(row=0, column=2, padx=5, pady=5)

        # Row 2 of buttons
        self.install_apk_btn = ttk.Button(
            actions_buttons_frame, text="Install APK", command=self.install_apk, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.install_apk_btn.grid(row=1, column=0, padx=5, pady=5)

        self.app_manager_btn = ttk.Button(
            actions_buttons_frame, text="App Manager", command=self.app_manager, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.app_manager_btn.grid(row=1, column=1, padx=5, pady=5)

        self.logcat_btn = ttk.Button(
            actions_buttons_frame, text="View Logcat", command=self.view_logcat, state="disabled",
            width=18  # Explicitly set width to ensure text fits
        )
        self.logcat_btn.grid(row=1, column=2, padx=5, pady=5)

        # Create the Android Tools tab
        self._create_tools_tab(content_frame)

        # Add log frame
        self.log_frame = ttk.LabelFrame(self, text="Log")
        self.log_frame.pack(fill="x", padx=10, pady=5, expand=False)

        # Create the log text widget
        self.log_text = tk.Text(self.log_frame, height=6, width=80, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Initialize log with a welcome message
        self.log_message("Android Tools module initialized")

    def _create_tools_tab(self, content_frame):
        """Create the Android Tools tab with all tool categories"""
        # Android Tools Tab
        self.tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tools_frame, text="Android Tools")

        # Create a scrollable frame for the entire tools tab
        # Ensure the tools frame itself has fixed dimensions
        self.tools_frame.configure(width=1024, height=600)
        self.tools_frame.pack_propagate(False)

        # Main container with scrollbar
        container_frame = ttk.Frame(self.tools_frame)
        container_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create canvas with fixed size for full-page scrolling
        canvas = tk.Canvas(container_frame, borderwidth=0, highlightthickness=0, width=1000, height=580)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)

        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Create frame inside canvas for content with fixed width
        categories_frame = ttk.Frame(canvas, width=980)
        canvas_window = canvas.create_window((0, 0), window=categories_frame, anchor="nw")

        # Update scroll region when content size changes
        def update_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Update canvas window width when canvas resizes
        def update_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        # Bind events
        categories_frame.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", update_canvas_width)

        # Add mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # For Linux/Mac compatibility
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Main tool categories section - will be arranged in a responsive grid
        categories = [
            {"name": "Device Control", "icon": "🔄"},
            {"name": "App Management", "icon": "📱"},
            {"name": "System Tools", "icon": "⚙️"},
            {"name": "Debugging", "icon": "🐞"},
            {"name": "File Operations", "icon": "📁"},
            {"name": "Security & Permissions", "icon": "🔒"},
            {"name": "Automation & Scripting", "icon": "🤖"},
            {"name": "Advanced Tests", "icon": "🧪"}
        ]

        # Create a vertical layout for categories - each category gets its own row
        categories_container = ttk.Frame(categories_frame)
        categories_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Set the layout for categories to be in a grid with 2 columns
        categories_container.columnconfigure(0, weight=1)
        categories_container.columnconfigure(1, weight=1)

        # Base width for each category
        category_width = 480  # Wider categories for better visibility

        # Add an instruction label at the top
        ttk.Label(categories_frame, text="Scroll down to see all tools", font=("Arial", 10, "italic")).pack(pady=(0, 5), anchor="w", fill="x")

        # Add categories in a grid layout - 2 columns, 4 rows
        for idx, category in enumerate(categories):
            # Calculate row and column position
            row = idx // 2  # Integer division for row number
            col = idx % 2   # Remainder for column (0 or 1)

            # Create the category frame with grid placement
            category_frame = ttk.LabelFrame(categories_container, text=f"{category['icon']} {category['name']}",
                                            padding=3, relief="groove", borderwidth=1)
            # Use grid layout to position categories in 2 columns
            category_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            # Set fixed dimensions for each category frame
            category_frame.configure(height=360, width=130)
            category_frame.pack_propagate(False)  # Prevent shrinking to content

            # Simple content frame for buttons (no scrolling needed since we have page-level scrolling)
            content_frame = ttk.Frame(category_frame)
            content_frame.pack(fill="both", expand=True, padx=1, pady=1)

            # Add tools based on category
            self._populate_category_buttons(category["name"], content_frame)

    def _populate_category_buttons(self, category_name, content_frame):
        """Populate buttons for a given category"""
        if category_name == "Device Control":
            # Device reboot options - single column layout
            ttk.Button(
                content_frame, text="Reboot Device",
                command=lambda: self._run_in_thread(self._reboot_device_normal),
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Reboot Recovery",
                command=lambda: self._run_in_thread(self._reboot_device_recovery),
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Reboot Bootloader",
                command=lambda: self._run_in_thread(self._reboot_device_bootloader),
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="WiFi Toggle",
                command=lambda: self._run_in_thread(self._toggle_wifi),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Airplane Mode",
                command=lambda: self._run_in_thread(self._toggle_airplane_mode),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screen Toggle",
                command=lambda: self._run_in_thread(self._toggle_screen),
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Reboot EDL",
                command=lambda: self._run_in_thread(self._reboot_device_edl),
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Mobile Data",
                command=lambda: self._run_in_thread(self._toggle_mobile_data),
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Bluetooth",
                command=lambda: self._run_in_thread(self._toggle_bluetooth),
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Brightness",
                command=lambda: self._run_in_thread(self._set_brightness_dialog),
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screen Timeout",
                command=lambda: self._run_in_thread(self._set_screen_timeout_dialog),
                width=18
            ).grid(row=4, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screenshot",
                command=lambda: self._run_in_thread(self.take_screenshot),
                width=18
            ).grid(row=5, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="DND Toggle",
                command=lambda: self._run_in_thread(self._toggle_do_not_disturb),
                width=18
            ).grid(row=0, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Power Button",
                command=lambda: self._run_in_thread(self._simulate_power_button),
                width=18
            ).grid(row=1, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Flashlight",
                command=lambda: self._run_in_thread(self._toggle_flashlight),
                width=18
            ).grid(row=2, column=2, padx=1, pady=1, sticky="ew")

        elif category_name == "App Management":
            ttk.Button(
                content_frame, text="Install APK",
                command=self.install_apk,
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Uninstall App",
                command=lambda: self._run_in_thread(self._uninstall_app_dialog),
                width=18
            ).grid(row=1, column=0, padx=2, pady=2)

            ttk.Button(
                content_frame, text="Clear App Data",
                command=lambda: self._run_in_thread(self._clear_app_data_dialog),
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Force Stop App",
                command=lambda: self._run_in_thread(self._force_stop_app_dialog),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="List Installed Apps",
                command=lambda: self._run_in_thread(self._list_installed_apps),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Open App",
                command=lambda: self._run_in_thread(self._open_app_dialog),
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Extract APK",
                command=lambda: self._run_in_thread(self._extract_apk_dialog),
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Freeze/Unfreeze",
                command=lambda: self._run_in_thread(self._toggle_freeze_dialog),
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="View Permissions",
                command=lambda: self._run_in_thread(self._view_permissions_dialog),
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="App Usage Stats",
                command=lambda: self._run_in_thread(self._show_app_usage_stats),
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="App Battery Usage",
                command=lambda: self._run_in_thread(self._show_battery_usage),
                width=18
            ).grid(row=4, column=1, padx=1, pady=1, sticky="ew")

        elif category_name == "System Tools":
            ttk.Button(
                content_frame, text="Device Info",
                command=lambda: self._run_in_thread(self._show_detailed_device_info),
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Battery Stats",
                command=lambda: self._run_in_thread(self._show_battery_stats),
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Running Services",
                command=lambda: self._run_in_thread(self._show_running_services),
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Network Stats",
                command=lambda: self._run_in_thread(self._show_network_stats),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Thermal Stats",
                command=lambda: self._run_in_thread(self._show_thermal_stats),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Sensor Status",
                command=lambda: self._run_in_thread(self._show_sensor_status),
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Power Profile",
                command=lambda: self._run_in_thread(self._show_power_profile),
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Location Settings",
                command=lambda: self._run_in_thread(self._show_location_settings),
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Doze Mode Status",
                command=lambda: self._run_in_thread(self._show_doze_mode_status),
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="SELinux Status",
                command=lambda: self._run_in_thread(self._show_selinux_status),
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Time and Date",
                command=lambda: self._run_in_thread(self._show_time_date_info),
                width=18
            ).grid(row=4, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="CPU Governor",
                command=lambda: self._run_in_thread(self._show_cpu_governor_info),
                width=18
            ).grid(row=5, column=1, padx=1, pady=1, sticky="ew")

        elif category_name == "Debugging":
            ttk.Button(
                content_frame, text="ANR Traces",
                command=lambda: self._run_in_thread(self._show_anr_traces),
                width=18
            ).grid(row=0, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Crash Dumps",
                command=lambda: self._run_in_thread(self._show_crash_dumps),
                width=18
            ).grid(row=1, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Bug Report",
                command=lambda: self._run_in_thread(self._generate_bug_report),
                width=18
            ).grid(row=2, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screen Record",
                command=lambda: self._run_in_thread(self._start_screen_recording),
                width=18
            ).grid(row=3, column=2, padx=1, pady=1, sticky="ew")

        elif category_name == "File Operations":
            ttk.Button(
                content_frame, text="File Manager",
                command=self.manage_files,
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Pull from Device",
                command=lambda: self._run_in_thread(self._pull_from_device),
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Push to Device",
                command=lambda: self._run_in_thread(self._push_to_device),
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Backup Device",
                command=lambda: self._run_in_thread(self.backup_device),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="View Storage",
                command=lambda: self._run_in_thread(self._show_storage_info),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Clean Caches",
                command=lambda: self._run_in_thread(self._clean_app_caches),
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Explore Protected",
                command=lambda: self._run_in_thread(self._explore_protected_storage),
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Search Files",
                command=lambda: self._run_in_thread(self._search_files_on_device),
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Export SQLite DBs",
                command=lambda: self._run_in_thread(self._export_sqlite_databases),
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Dir Size Calc",
                command=lambda: self._run_in_thread(self._calculate_directory_size),
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="File Checksum",
                command=lambda: self._run_in_thread(self._calculate_file_checksum),
                width=18
            ).grid(row=4, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Edit Text File",
                command=lambda: self._run_in_thread(self._edit_text_file_on_device),
                width=18
            ).grid(row=5, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Mount Info",
                command=lambda: self._run_in_thread(self._show_mount_info),
                width=18
            ).grid(row=0, column=2, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Recent Files",
                command=lambda: self._run_in_thread(self._list_recent_files),
                width=18
            ).grid(row=1, column=2, padx=1, pady=1, sticky="ew")

        elif category_name == "Security & Permissions":
            ttk.Button(
                content_frame, text="Check Root Status",
                command=lambda: self._run_in_thread(self._check_root_status),
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Check AppOps",
                command=self._check_appops_dialog,
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Change AppOps Permission",
                command=self._change_appops_dialog,
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Check Encryption",
                command=lambda: self._run_in_thread(self._check_encryption_status),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Check Lock Screen",
                command=lambda: self._run_in_thread(self._check_lock_screen_status),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Verify Boot",
                command=lambda: self._run_in_thread(self._verify_boot_integrity),
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Keystore Info",
                command=lambda: self._run_in_thread(self._show_keystore_info),
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Certificate Checker",
                command=lambda: self._run_in_thread(self._check_certificates),
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Security Patch Level",
                command=lambda: self._run_in_thread(self._check_security_patch_level),
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Permission Scanner",
                command=lambda: self._run_in_thread(self._scan_dangerous_permissions),
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

        elif category_name == "Automation & Scripting":
            ttk.Button(
                content_frame, text="Run Shell Script",
                command=lambda: self._run_in_thread(self._run_shell_script_dialog),
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Batch App Manager",
                command=lambda: self._run_in_thread(self._batch_app_manager_dialog),
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Scheduled Tasks",
                command=lambda: self._run_in_thread(self._scheduled_tasks_dialog),
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Logcat + Screencap",
                command=lambda: self._run_in_thread(self._logcat_screencap_dialog),
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Monkey Testing",
                command=lambda: self._run_in_thread(self._monkey_testing_dialog),
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

        elif category_name == "Advanced Tests":
            ttk.Button(
                content_frame, text="Screen Lock Brute",
                command=self.run_screen_lock_brute_forcer,
                width=18
            ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screen Lock Duplicator",
                command=self.run_screen_lock_duplicator,
                width=18
            ).grid(row=1, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Hardware Stress Test",
                command=self.run_hardware_stress_test,
                width=18
            ).grid(row=2, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Looped Benchmarking",
                command=self.run_looped_benchmarking,
                width=18
            ).grid(row=3, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Screen Mirror (scrcpy)",
                command=self.run_scrcpy_mirror,
                width=18
            ).grid(row=4, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="I/O Spike Generator",
                command=self.run_io_spike_generator,
                width=18
            ).grid(row=5, column=0, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="App Crash Forcer",
                command=self.run_app_crash_forcer,
                width=18
            ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Dalvik Cache Stress",
                command=self.run_dalvik_cache_stress_test,
                width=18
            ).grid(row=1, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="RAM Fill Test",
                command=self.run_ram_fill_test,
                width=18
            ).grid(row=2, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="GPU Stress Test",
                command=self.run_gpu_stress_test,
                width=18
            ).grid(row=3, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="CPU Max Load Test",
                command=self.run_cpu_max_load_test,
                width=18
            ).grid(row=4, column=1, padx=1, pady=1, sticky="ew")

            ttk.Button(
                content_frame, text="Battery Drain Test",
                command=self.run_battery_drain_test,
                width=18
            ).grid(row=5, column=1, padx=1, pady=1, sticky="ew")

    def log_message(self, message):
        """Add a message to the log console"""
        # Log to console even if the UI element doesn't exist yet
        logging.info(f"[AndroidTools] {message}")

        # Only update the UI if the log_text widget exists
        if self.log_text is not None:
            try:
                self.log_text.configure(state="normal")
                self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state="disabled")
            except Exception as e:
                logging.error(f"Error updating log display: {str(e)}")

    def update_status(self, status_text):
        """Update the status bar text"""
        try:
            if hasattr(self, 'status_var'):
                self.status_var.set(status_text)
        except Exception as e:
            logging.error(f"Error updating status: {str(e)}")

    def enable_device_actions(self):
        """Enable device action buttons when a device is connected"""
        self.screenshot_btn.configure(state="normal")
        self.backup_btn.configure(state="normal")
        self.files_btn.configure(state="normal")
        self.install_apk_btn.configure(state="normal")
        self.app_manager_btn.configure(state="normal")
        self.logcat_btn.configure(state="normal")

    def disable_device_actions(self):
        """Disable device action buttons when no device is connected"""
        self.screenshot_btn.configure(state="disabled")
        self.backup_btn.configure(state="disabled")
        self.files_btn.configure(state="disabled")
        self.install_apk_btn.configure(state="disabled")
        self.app_manager_btn.configure(state="disabled")
        self.logcat_btn.configure(state="disabled")

    def _run_in_thread(self, target_function, *args, **kwargs):
        """Run a function in a separate thread with error handling"""
        def thread_wrapper():
            try:
                target_function(*args, **kwargs)
            except Exception as e:
                # Log the full traceback to the console
                import traceback
                traceback.print_exc()
                # Also log to the GUI if available
                if hasattr(self, 'log_message'):
                    self.after(0, lambda: self.log_message(f"Error in thread: {str(e)}"))

        thread = threading.Thread(target=thread_wrapper)
        thread.daemon = True  # Thread will close when main app closes
        self.threads.append(thread)
        thread.start()
        return thread

    def update_device_info(self):
        """Update the device info display with the connected device information"""
        if not self.device_info:
            return

        # Update basic info fields
        if 'model' in self.device_info:
            self.info_fields['Model'].set(self.device_info['model'])

        if 'manufacturer' in self.device_info:
            self.info_fields['Manufacturer'].set(self.device_info['manufacturer'])

        if 'android_version' in self.device_info:
            self.info_fields['Android Version'].set(self.device_info['android_version'])

        # Make sure we only show the serial number, not the debug info
        if 'serial' in self.device_info:
            # Get just the serial number without any extra text
            serial = str(self.device_info['serial']).strip()
            # Remove any ADB debug text that might be associated with it
            if '\n' in serial:
                serial = serial.split('\n')[0].strip()
            self.info_fields['Serial Number'].set(serial)

        if 'battery' in self.device_info:
            self.info_fields['Battery Level'].set(self.device_info['battery'])

        # Display IMEI if available
        if 'imei' in self.device_info:
            self.info_fields['IMEI'].set(self.device_info['imei'])
        # Fallback to Android ID if IMEI not available
        elif 'device_id' in self.device_info:
            self.info_fields['IMEI'].set(f"{self.device_info['device_id']} (Android ID)")

        # Update advanced info fields
        if 'storage' in self.device_info:
            self.adv_info_fields['Storage'].set(self.device_info['storage'])

        if 'ram' in self.device_info:
            self.adv_info_fields['RAM'].set(self.device_info['ram'])

        if 'resolution' in self.device_info:
            self.adv_info_fields['Screen Resolution'].set(self.device_info['resolution'])

        if 'cpu' in self.device_info:
            self.adv_info_fields['CPU'].set(self.device_info['cpu'])

        if 'kernel' in self.device_info:
            self.adv_info_fields['Kernel'].set(self.device_info['kernel'])
