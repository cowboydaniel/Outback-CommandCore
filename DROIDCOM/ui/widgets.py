"""
DROIDCOM - Widgets Module
Contains widget creation and UI-related functionality.
"""

import threading
import time
import logging

from PySide6 import QtCore, QtGui, QtWidgets



class ListBox(QtWidgets.QListWidget):
    """QListWidget adapter with Tkinter-like listbox methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def curselection(self):
        return [self.row(item) for item in self.selectedItems()]

    def get(self, index):
        index = self._normalize_index(index)
        if index is None:
            return ""
        item = self.item(index)
        return item.text() if item else ""

    def delete(self, first, last=None):
        if last is None:
            last = first
        first_index = self._normalize_index(first)
        last_index = self._normalize_index(last)
        if first_index is None:
            return
        if last_index is None:
            last_index = first_index
        for index in range(last_index, first_index - 1, -1):
            self.takeItem(index)

    def insert(self, index, text):
        text = str(text)
        if isinstance(index, str) and index.lower() == "end":
            self.addItem(text)
            return
        normalized = self._normalize_index(index)
        if normalized is None:
            self.addItem(text)
            return
        self.insertItem(normalized, text)

    def size(self):
        return self.count()

    def selection_set(self, first, last=None):
        first_index = self._normalize_index(first)
        last_index = self._normalize_index(last) if last is not None else first_index
        if first_index is None:
            return
        if last_index is None:
            last_index = first_index
        for index in range(first_index, last_index + 1):
            item = self.item(index)
            if item:
                item.setSelected(True)
        self.setCurrentRow(first_index)

    def selection_clear(self, first=None, last=None):
        self.clearSelection()

    def see(self, index):
        normalized = self._normalize_index(index)
        if normalized is None:
            return
        item = self.item(normalized)
        if item:
            self.scrollToItem(item)

    def _normalize_index(self, index):
        if isinstance(index, (list, tuple)):
            if not index:
                return None
            index = index[0]
        if isinstance(index, str):
            if index.lower() == "end":
                return max(self.count() - 1, 0)
            try:
                return int(index)
            except ValueError:
                return None
        try:
            return int(index)
        except (TypeError, ValueError):
            return None


class WidgetsMixin:
    """Mixin class providing widget creation and UI utility methods."""

    def create_widgets(self):
        """Create the main UI widgets"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Create main container widget
        main_container = QtWidgets.QWidget(self)
        main_layout.addWidget(main_container, 1)

        content_layout = QtWidgets.QVBoxLayout(main_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)

        # Main header with logo
        header_frame = QtWidgets.QWidget(main_container)
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_label = QtWidgets.QLabel("Android Device Management", header_frame)
        header_font = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        content_layout.addWidget(header_frame)

        # Setup status frame for tools
        self.setup_status_frame = QtWidgets.QGroupBox("Tools Status", main_container)
        setup_layout = QtWidgets.QVBoxLayout(self.setup_status_frame)
        setup_layout.setContentsMargins(8, 8, 8, 8)

        tools_status = "✅ Installed" if self.platform_tools_installed else "❌ Not Installed"
        self.tools_label = QtWidgets.QLabel(
            f"Android Platform Tools: {tools_status}", self.setup_status_frame
        )
        tools_label_font = QtGui.QFont("Arial", 10)
        self.tools_label.setFont(tools_label_font)
        setup_layout.addWidget(self.tools_label)

        if not self.platform_tools_installed:
            tools_frame = QtWidgets.QWidget(self.setup_status_frame)
            tools_frame_layout = QtWidgets.QHBoxLayout(tools_frame)
            tools_frame_layout.setContentsMargins(0, 0, 0, 0)

            tools_btn = QtWidgets.QPushButton("Install Android Platform Tools", tools_frame)
            tools_btn.clicked.connect(self.install_platform_tools)
            tools_btn.setMinimumWidth(260)
            tools_frame_layout.addWidget(tools_btn)
            tools_frame_layout.addStretch()
            setup_layout.addWidget(tools_frame)

        content_layout.addWidget(self.setup_status_frame)

        # Main content area with tabs
        self.notebook = QtWidgets.QTabWidget(main_container)
        content_layout.addWidget(self.notebook, 1)

        # Device Info Tab
        self.device_frame = QtWidgets.QWidget(self.notebook)
        device_layout = QtWidgets.QVBoxLayout(self.device_frame)
        device_layout.setContentsMargins(10, 10, 10, 10)
        device_layout.setSpacing(10)
        self.notebook.addTab(self.device_frame, "Device Info")

        # Device connection frame
        connection_frame = QtWidgets.QGroupBox("Device Connection", self.device_frame)
        connection_layout = QtWidgets.QVBoxLayout(connection_frame)
        connection_layout.setSpacing(8)
        device_layout.addWidget(connection_frame)

        # Connection buttons frame
        conn_buttons_frame = QtWidgets.QWidget(connection_frame)
        conn_buttons_layout = QtWidgets.QHBoxLayout(conn_buttons_frame)
        conn_buttons_layout.setContentsMargins(0, 0, 0, 0)
        conn_buttons_layout.setSpacing(6)

        self.connect_btn = QtWidgets.QPushButton("Connect Device", conn_buttons_frame)
        self.connect_btn.clicked.connect(self.connect_device)
        self.connect_btn.setMinimumWidth(160)
        conn_buttons_layout.addWidget(self.connect_btn)

        self.wifi_adb_btn = QtWidgets.QPushButton("WiFi ADB", conn_buttons_frame)
        self.wifi_adb_btn.clicked.connect(self.setup_wifi_adb)
        self.wifi_adb_btn.setMinimumWidth(160)
        conn_buttons_layout.addWidget(self.wifi_adb_btn)

        self.refresh_btn = QtWidgets.QPushButton("Refresh Devices", conn_buttons_frame)
        self.refresh_btn.clicked.connect(self.refresh_device_list)
        self.refresh_btn.setMinimumWidth(160)
        conn_buttons_layout.addWidget(self.refresh_btn)

        self.remove_offline_btn = QtWidgets.QPushButton("Remove Offline", conn_buttons_frame)
        self.remove_offline_btn.clicked.connect(self.remove_offline_devices)
        self.remove_offline_btn.setMinimumWidth(160)
        conn_buttons_layout.addWidget(self.remove_offline_btn)

        conn_buttons_layout.addStretch()
        connection_layout.addWidget(conn_buttons_frame)

        # Device list frame
        list_frame = QtWidgets.QWidget(connection_frame)
        list_layout = QtWidgets.QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        list_label = QtWidgets.QLabel("Available Devices:", list_frame)
        list_layout.addWidget(list_label)

        list_subframe = QtWidgets.QWidget(list_frame)
        list_sub_layout = QtWidgets.QHBoxLayout(list_subframe)
        list_sub_layout.setContentsMargins(0, 0, 0, 0)

        self.device_listbox = ListBox(list_subframe)
        self.device_listbox.setMinimumHeight(80)
        list_sub_layout.addWidget(self.device_listbox)
        list_layout.addWidget(list_subframe)

        connection_layout.addWidget(list_frame)

        # Device info display
        device_info_frame = QtWidgets.QGroupBox("Device Information", self.device_frame)
        device_info_layout = QtWidgets.QVBoxLayout(device_info_frame)
        device_layout.addWidget(device_info_frame, 1)

        info_content = QtWidgets.QWidget(device_info_frame)
        info_layout = QtWidgets.QGridLayout(info_content)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setHorizontalSpacing(12)
        info_layout.setVerticalSpacing(6)
        device_info_layout.addWidget(info_content)

        # Basic device info fields (left column)
        self.info_fields = {
            "Model": QtWidgets.QLabel("N/A", info_content),
            "Manufacturer": QtWidgets.QLabel("N/A", info_content),
            "Android Version": QtWidgets.QLabel("N/A", info_content),
            "Serial Number": QtWidgets.QLabel("N/A", info_content),
            "IMEI": QtWidgets.QLabel("N/A", info_content),
            "Battery Level": QtWidgets.QLabel("N/A", info_content),
        }

        # Advanced device info fields (right column)
        self.adv_info_fields = {
            "Storage": QtWidgets.QLabel("N/A", info_content),
            "RAM": QtWidgets.QLabel("N/A", info_content),
            "Screen Resolution": QtWidgets.QLabel("N/A", info_content),
            "CPU": QtWidgets.QLabel("N/A", info_content),
            "Kernel": QtWidgets.QLabel("N/A", info_content),
        }

        info_layout.setColumnMinimumWidth(0, 150)
        info_layout.setColumnMinimumWidth(1, 150)
        info_layout.setColumnMinimumWidth(2, 150)
        info_layout.setColumnMinimumWidth(3, 150)

        heading_font = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
        basic_heading = QtWidgets.QLabel("Basic Information", info_content)
        basic_heading.setFont(heading_font)
        info_layout.addWidget(basic_heading, 0, 0, 1, 2, QtCore.Qt.AlignLeft)

        advanced_heading = QtWidgets.QLabel("Advanced Information", info_content)
        advanced_heading.setFont(heading_font)
        info_layout.addWidget(advanced_heading, 0, 2, 1, 2, QtCore.Qt.AlignLeft)

        max_rows = max(len(self.info_fields), len(self.adv_info_fields)) + 2
        debug_heading = QtWidgets.QLabel("Debug Information", info_content)
        debug_heading.setFont(heading_font)
        info_layout.addWidget(debug_heading, max_rows, 0, 1, 4, QtCore.Qt.AlignLeft)

        debug_frame = QtWidgets.QWidget(info_content)
        debug_layout = QtWidgets.QVBoxLayout(debug_frame)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        self.debug_text = QtWidgets.QTextEdit(debug_frame)
        self.debug_text.setReadOnly(True)
        self.debug_text.setMinimumHeight(110)
        debug_layout.addWidget(self.debug_text)
        info_layout.addWidget(debug_frame, max_rows + 1, 0, 1, 4)

        label_font = QtGui.QFont("Arial", 9, QtGui.QFont.Bold)
        row = 1
        for label_text, value_label in self.info_fields.items():
            label = QtWidgets.QLabel(f"{label_text}:", info_content)
            label.setFont(label_font)
            info_layout.addWidget(label, row, 0, QtCore.Qt.AlignLeft)
            info_layout.addWidget(value_label, row, 1, QtCore.Qt.AlignLeft)
            row += 1

        row = 1
        for label_text, value_label in self.adv_info_fields.items():
            label = QtWidgets.QLabel(f"{label_text}:", info_content)
            label.setFont(label_font)
            info_layout.addWidget(label, row, 2, QtCore.Qt.AlignLeft)
            info_layout.addWidget(value_label, row, 3, QtCore.Qt.AlignLeft)
            row += 1

        # Device actions frame
        actions_frame = QtWidgets.QGroupBox("Device Actions", self.device_frame)
        actions_layout = QtWidgets.QGridLayout(actions_frame)
        actions_layout.setHorizontalSpacing(8)
        actions_layout.setVerticalSpacing(8)
        device_layout.addWidget(actions_frame)

        self.screenshot_btn = QtWidgets.QPushButton("Take Screenshot", actions_frame)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.screenshot_btn.setEnabled(False)
        actions_layout.addWidget(self.screenshot_btn, 0, 0)

        self.backup_btn = QtWidgets.QPushButton("Backup Device", actions_frame)
        self.backup_btn.clicked.connect(self.backup_device)
        self.backup_btn.setEnabled(False)
        actions_layout.addWidget(self.backup_btn, 0, 1)

        self.files_btn = QtWidgets.QPushButton("Manage Files", actions_frame)
        self.files_btn.clicked.connect(self.manage_files)
        self.files_btn.setEnabled(False)
        actions_layout.addWidget(self.files_btn, 0, 2)

        self.install_apk_btn = QtWidgets.QPushButton("Install APK", actions_frame)
        self.install_apk_btn.clicked.connect(self.install_apk)
        self.install_apk_btn.setEnabled(False)
        actions_layout.addWidget(self.install_apk_btn, 1, 0)

        self.app_manager_btn = QtWidgets.QPushButton("App Manager", actions_frame)
        self.app_manager_btn.clicked.connect(self.app_manager)
        self.app_manager_btn.setEnabled(False)
        actions_layout.addWidget(self.app_manager_btn, 1, 1)

        self.logcat_btn = QtWidgets.QPushButton("View Logcat", actions_frame)
        self.logcat_btn.clicked.connect(self.view_logcat)
        self.logcat_btn.setEnabled(False)
        actions_layout.addWidget(self.logcat_btn, 1, 2)

        # Create the Android Tools tab
        self._create_tools_tab()

        # Add log frame
        self.log_frame = QtWidgets.QGroupBox("Log", main_container)
        log_layout = QtWidgets.QVBoxLayout(self.log_frame)
        self.log_text = QtWidgets.QTextEdit(self.log_frame)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(130)
        log_layout.addWidget(self.log_text)
        content_layout.addWidget(self.log_frame)

        # Status bar
        self.status_label = QtWidgets.QLabel("Ready", self)
        self.status_label.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.status_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.status_var = self.status_label
        main_layout.addWidget(self.status_label)

        # Initialize log with a welcome message
        self.log_message("Android Tools module initialized")

    def _create_tools_tab(self):
        """Create the Android Tools tab with all tool categories"""
        self.tools_frame = QtWidgets.QWidget(self.notebook)
        tools_layout = QtWidgets.QVBoxLayout(self.tools_frame)
        tools_layout.setContentsMargins(5, 5, 5, 5)
        self.notebook.addTab(self.tools_frame, "Android Tools")

        scroll_area = QtWidgets.QScrollArea(self.tools_frame)
        scroll_area.setWidgetResizable(True)
        tools_layout.addWidget(scroll_area)

        categories_frame = QtWidgets.QWidget(scroll_area)
        scroll_area.setWidget(categories_frame)

        categories_layout = QtWidgets.QVBoxLayout(categories_frame)
        categories_layout.setContentsMargins(5, 5, 5, 5)
        categories_layout.setSpacing(8)

        instruction_label = QtWidgets.QLabel("Scroll down to see all tools", categories_frame)
        instruction_font = QtGui.QFont("Arial", 10)
        instruction_font.setItalic(True)
        instruction_label.setFont(instruction_font)
        categories_layout.addWidget(instruction_label)

        categories_container = QtWidgets.QWidget(categories_frame)
        categories_grid = QtWidgets.QGridLayout(categories_container)
        categories_grid.setHorizontalSpacing(8)
        categories_grid.setVerticalSpacing(8)
        categories_layout.addWidget(categories_container)

        categories = [
            {"name": "Device Control", "icon": "🔄"},
            {"name": "App Management", "icon": "📱"},
            {"name": "System Tools", "icon": "⚙️"},
            {"name": "Debugging", "icon": "🐞"},
            {"name": "File Operations", "icon": "📁"},
            {"name": "Security & Permissions", "icon": "🔒"},
            {"name": "Automation & Scripting", "icon": "🤖"},
            {"name": "Advanced Tests", "icon": "🧪"},
        ]

        for idx, category in enumerate(categories):
            row = idx // 2
            col = idx % 2

            category_frame = QtWidgets.QGroupBox(
                f"{category['icon']} {category['name']}", categories_container
            )
            category_frame.setMinimumHeight(360)
            category_frame.setMinimumWidth(440)
            category_layout = QtWidgets.QVBoxLayout(category_frame)
            content_frame = QtWidgets.QWidget(category_frame)
            content_layout = QtWidgets.QGridLayout(content_frame)
            content_layout.setHorizontalSpacing(6)
            content_layout.setVerticalSpacing(6)
            category_layout.addWidget(content_frame)
            categories_grid.addWidget(category_frame, row, col)

            self._populate_category_buttons(category["name"], content_layout)

        categories_grid.setColumnStretch(0, 1)
        categories_grid.setColumnStretch(1, 1)

    def _add_tool_button(self, layout, row, col, text, callback):
        button = QtWidgets.QPushButton(text)
        button.setMinimumWidth(160)
        button.clicked.connect(callback)
        layout.addWidget(button, row, col)

    def _populate_category_buttons(self, category_name, layout):
        """Populate buttons for a given category"""
        if category_name == "Device Control":
            self._add_tool_button(
                layout, 0, 0, "Reboot Device",
                lambda: self._run_in_thread(self._reboot_device_normal),
            )
            self._add_tool_button(
                layout, 1, 0, "Reboot Recovery",
                lambda: self._run_in_thread(self._reboot_device_recovery),
            )
            self._add_tool_button(
                layout, 2, 0, "Reboot Bootloader",
                lambda: self._run_in_thread(self._reboot_device_bootloader),
            )
            self._add_tool_button(
                layout, 3, 0, "WiFi Toggle",
                lambda: self._run_in_thread(self._toggle_wifi),
            )
            self._add_tool_button(
                layout, 4, 0, "Airplane Mode",
                lambda: self._run_in_thread(self._toggle_airplane_mode),
            )
            self._add_tool_button(
                layout, 5, 0, "Screen Toggle",
                lambda: self._run_in_thread(self._toggle_screen),
            )
            self._add_tool_button(
                layout, 0, 1, "Reboot EDL",
                lambda: self._run_in_thread(self._reboot_device_edl),
            )
            self._add_tool_button(
                layout, 1, 1, "Mobile Data",
                lambda: self._run_in_thread(self._toggle_mobile_data),
            )
            self._add_tool_button(
                layout, 2, 1, "Bluetooth",
                lambda: self._run_in_thread(self._toggle_bluetooth),
            )
            self._add_tool_button(
                layout, 3, 1, "Brightness",
                lambda: self._run_in_thread(self._set_brightness_dialog),
            )
            self._add_tool_button(
                layout, 4, 1, "Screen Timeout",
                lambda: self._run_in_thread(self._set_screen_timeout_dialog),
            )
            self._add_tool_button(
                layout, 5, 1, "Screenshot",
                lambda: self._run_in_thread(self.take_screenshot),
            )
            self._add_tool_button(
                layout, 0, 2, "DND Toggle",
                lambda: self._run_in_thread(self._toggle_do_not_disturb),
            )
            self._add_tool_button(
                layout, 1, 2, "Power Button",
                lambda: self._run_in_thread(self._simulate_power_button),
            )
            self._add_tool_button(
                layout, 2, 2, "Flashlight",
                lambda: self._run_in_thread(self._toggle_flashlight),
            )

        elif category_name == "App Management":
            self._add_tool_button(layout, 0, 0, "Install APK", self.install_apk)
            self._add_tool_button(
                layout, 1, 0, "Uninstall App",
                lambda: self._run_in_thread(self._uninstall_app_dialog),
            )
            self._add_tool_button(
                layout, 2, 0, "Clear App Data",
                lambda: self._run_in_thread(self._clear_app_data_dialog),
            )
            self._add_tool_button(
                layout, 3, 0, "Force Stop App",
                lambda: self._run_in_thread(self._force_stop_app_dialog),
            )
            self._add_tool_button(
                layout, 4, 0, "List Installed Apps",
                lambda: self._run_in_thread(self._list_installed_apps),
            )
            self._add_tool_button(
                layout, 5, 0, "Open App",
                lambda: self._run_in_thread(self._open_app_dialog),
            )
            self._add_tool_button(
                layout, 0, 1, "Extract APK",
                lambda: self._run_in_thread(self._extract_apk_dialog),
            )
            self._add_tool_button(
                layout, 1, 1, "Freeze/Unfreeze",
                lambda: self._run_in_thread(self._toggle_freeze_dialog),
            )
            self._add_tool_button(
                layout, 2, 1, "View Permissions",
                lambda: self._run_in_thread(self._view_permissions_dialog),
            )
            self._add_tool_button(
                layout, 3, 1, "App Usage Stats",
                lambda: self._run_in_thread(self._show_app_usage_stats),
            )
            self._add_tool_button(
                layout, 4, 1, "App Battery Usage",
                lambda: self._run_in_thread(self._show_battery_usage),
            )

        elif category_name == "System Tools":
            self._add_tool_button(
                layout, 0, 0, "Device Info",
                lambda: self._run_in_thread(self._show_detailed_device_info),
            )
            self._add_tool_button(
                layout, 1, 0, "Battery Stats",
                lambda: self._run_in_thread(self._show_battery_stats),
            )
            self._add_tool_button(
                layout, 2, 0, "Running Services",
                lambda: self._run_in_thread(self._show_running_services),
            )
            self._add_tool_button(
                layout, 3, 0, "Network Stats",
                lambda: self._run_in_thread(self._show_network_stats),
            )
            self._add_tool_button(
                layout, 4, 0, "Thermal Stats",
                lambda: self._run_in_thread(self._show_thermal_stats),
            )
            self._add_tool_button(
                layout, 5, 0, "Sensor Status",
                lambda: self._run_in_thread(self._show_sensor_status),
            )
            self._add_tool_button(
                layout, 0, 1, "Power Profile",
                lambda: self._run_in_thread(self._show_power_profile),
            )
            self._add_tool_button(
                layout, 1, 1, "Location Settings",
                lambda: self._run_in_thread(self._show_location_settings),
            )
            self._add_tool_button(
                layout, 2, 1, "Doze Mode Status",
                lambda: self._run_in_thread(self._show_doze_mode_status),
            )
            self._add_tool_button(
                layout, 3, 1, "SELinux Status",
                lambda: self._run_in_thread(self._show_selinux_status),
            )
            self._add_tool_button(
                layout, 4, 1, "Time and Date",
                lambda: self._run_in_thread(self._show_time_date_info),
            )
            self._add_tool_button(
                layout, 5, 1, "CPU Governor",
                lambda: self._run_in_thread(self._show_cpu_governor_info),
            )

        elif category_name == "Debugging":
            self._add_tool_button(
                layout, 0, 2, "ANR Traces",
                lambda: self._run_in_thread(self._show_anr_traces),
            )
            self._add_tool_button(
                layout, 1, 2, "Crash Dumps",
                lambda: self._run_in_thread(self._show_crash_dumps),
            )
            self._add_tool_button(
                layout, 2, 2, "Bug Report",
                lambda: self._run_in_thread(self._generate_bug_report),
            )
            self._add_tool_button(
                layout, 3, 2, "Screen Record",
                lambda: self._run_in_thread(self._start_screen_recording),
            )

        elif category_name == "File Operations":
            self._add_tool_button(layout, 0, 0, "File Manager", self.manage_files)
            self._add_tool_button(
                layout, 1, 0, "Pull from Device",
                lambda: self._run_in_thread(self._pull_from_device),
            )
            self._add_tool_button(
                layout, 2, 0, "Push to Device",
                lambda: self._run_in_thread(self._push_to_device),
            )
            self._add_tool_button(
                layout, 3, 0, "Backup Device",
                lambda: self._run_in_thread(self.backup_device),
            )
            self._add_tool_button(
                layout, 4, 0, "View Storage",
                lambda: self._run_in_thread(self._show_storage_info),
            )
            self._add_tool_button(
                layout, 5, 0, "Clean Caches",
                lambda: self._run_in_thread(self._clean_app_caches),
            )
            self._add_tool_button(
                layout, 0, 1, "Explore Protected",
                lambda: self._run_in_thread(self._explore_protected_storage),
            )
            self._add_tool_button(
                layout, 1, 1, "Search Files",
                lambda: self._run_in_thread(self._search_files_on_device),
            )
            self._add_tool_button(
                layout, 2, 1, "Export SQLite DBs",
                lambda: self._run_in_thread(self._export_sqlite_databases),
            )
            self._add_tool_button(
                layout, 3, 1, "Dir Size Calc",
                lambda: self._run_in_thread(self._calculate_directory_size),
            )
            self._add_tool_button(
                layout, 4, 1, "File Checksum",
                lambda: self._run_in_thread(self._calculate_file_checksum),
            )
            self._add_tool_button(
                layout, 5, 1, "Edit Text File",
                lambda: self._run_in_thread(self._edit_text_file_on_device),
            )
            self._add_tool_button(
                layout, 0, 2, "Mount Info",
                lambda: self._run_in_thread(self._show_mount_info),
            )
            self._add_tool_button(
                layout, 1, 2, "Recent Files",
                lambda: self._run_in_thread(self._list_recent_files),
            )

        elif category_name == "Security & Permissions":
            self._add_tool_button(
                layout, 0, 0, "Check Root Status",
                lambda: self._run_in_thread(self._check_root_status),
            )
            self._add_tool_button(
                layout, 1, 0, "Check AppOps",
                self._check_appops_dialog,
            )
            self._add_tool_button(
                layout, 2, 0, "Change AppOps Permission",
                self._change_appops_dialog,
            )
            self._add_tool_button(
                layout, 3, 0, "Check Encryption",
                lambda: self._run_in_thread(self._check_encryption_status),
            )
            self._add_tool_button(
                layout, 4, 0, "Check Lock Screen",
                lambda: self._run_in_thread(self._check_lock_screen_status),
            )
            self._add_tool_button(
                layout, 5, 0, "Verify Boot",
                lambda: self._run_in_thread(self._verify_boot_integrity),
            )
            self._add_tool_button(
                layout, 0, 1, "Keystore Info",
                lambda: self._run_in_thread(self._show_keystore_info),
            )
            self._add_tool_button(
                layout, 1, 1, "Certificate Checker",
                lambda: self._run_in_thread(self._check_certificates),
            )
            self._add_tool_button(
                layout, 2, 1, "Security Patch Level",
                lambda: self._run_in_thread(self._check_security_patch_level),
            )
            self._add_tool_button(
                layout, 3, 1, "Permission Scanner",
                lambda: self._run_in_thread(self._scan_dangerous_permissions),
            )

        elif category_name == "Automation & Scripting":
            self._add_tool_button(
                layout, 0, 0, "Run Shell Script",
                lambda: self._run_in_thread(self._run_shell_script_dialog),
            )
            self._add_tool_button(
                layout, 1, 0, "Batch App Manager",
                lambda: self._run_in_thread(self._batch_app_manager_dialog),
            )
            self._add_tool_button(
                layout, 2, 0, "Scheduled Tasks",
                lambda: self._run_in_thread(self._scheduled_tasks_dialog),
            )
            self._add_tool_button(
                layout, 3, 0, "Logcat + Screencap",
                lambda: self._run_in_thread(self._logcat_screencap_dialog),
            )
            self._add_tool_button(
                layout, 4, 0, "Monkey Testing",
                lambda: self._run_in_thread(self._monkey_testing_dialog),
            )

        elif category_name == "Advanced Tests":
            self._add_tool_button(
                layout, 0, 0, "Screen Lock Brute",
                self.run_screen_lock_brute_forcer,
            )
            self._add_tool_button(
                layout, 1, 0, "Screen Lock Duplicator",
                self.run_screen_lock_duplicator,
            )
            self._add_tool_button(
                layout, 2, 0, "Hardware Stress Test",
                self.run_hardware_stress_test,
            )
            self._add_tool_button(
                layout, 3, 0, "Looped Benchmarking",
                self.run_looped_benchmarking,
            )
            self._add_tool_button(
                layout, 4, 0, "Screen Mirror (scrcpy)",
                self.run_scrcpy_mirror,
            )
            self._add_tool_button(
                layout, 5, 0, "I/O Spike Generator",
                self.run_io_spike_generator,
            )
            self._add_tool_button(
                layout, 0, 1, "App Crash Forcer",
                self.run_app_crash_forcer,
            )
            self._add_tool_button(
                layout, 1, 1, "Dalvik Cache Stress",
                self.run_dalvik_cache_stress_test,
            )
            self._add_tool_button(
                layout, 2, 1, "RAM Fill Test",
                self.run_ram_fill_test,
            )
            self._add_tool_button(
                layout, 3, 1, "GPU Stress Test",
                self.run_gpu_stress_test,
            )
            self._add_tool_button(
                layout, 4, 1, "CPU Max Load Test",
                self.run_cpu_max_load_test,
            )
            self._add_tool_button(
                layout, 5, 1, "Battery Drain Test",
                self.run_battery_drain_test,
            )

    def log_message(self, message):
        """Add a message to the log console"""
        logging.info(f"[AndroidTools] {message}")

        if self.log_text is not None:
            try:
                timestamp = time.strftime('%H:%M:%S')
                self.log_text.append(f"[{timestamp}] {message}")
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                logging.error(f"Error updating log display: {str(e)}")

    def update_status(self, status_text):
        """Update the status bar text"""
        try:
            if hasattr(self, 'status_var') and hasattr(self.status_var, 'setText'):
                self.status_var.setText(status_text)
            elif hasattr(self, 'status_label'):
                self.status_label.setText(status_text)
        except Exception as e:
            logging.error(f"Error updating status: {str(e)}")

    def enable_device_actions(self):
        """Enable device action buttons when a device is connected"""
        self.screenshot_btn.setEnabled(True)
        self.backup_btn.setEnabled(True)
        self.files_btn.setEnabled(True)
        self.install_apk_btn.setEnabled(True)
        self.app_manager_btn.setEnabled(True)
        self.logcat_btn.setEnabled(True)

    def disable_device_actions(self):
        """Disable device action buttons when no device is connected"""
        self.screenshot_btn.setEnabled(False)
        self.backup_btn.setEnabled(False)
        self.files_btn.setEnabled(False)
        self.install_apk_btn.setEnabled(False)
        self.app_manager_btn.setEnabled(False)
        self.logcat_btn.setEnabled(False)

    def _run_in_thread(self, target_function, *args, **kwargs):
        """Run a function in a separate thread with error handling"""
        def thread_wrapper():
            try:
                target_function(*args, **kwargs)
            except Exception as e:
                import traceback
                traceback.print_exc()
                if hasattr(self, 'log_message'):
                    QtCore.QTimer.singleShot(0, lambda: self.log_message(f"Error in thread: {str(e)}"))

        thread = threading.Thread(target=thread_wrapper)
        thread.daemon = True
        self.threads.append(thread)
        thread.start()
        return thread

    def update_device_info(self):
        """Update the device info display with the connected device information"""
        if not self.device_info:
            return

        if 'model' in self.device_info:
            self.info_fields['Model'].setText(self.device_info['model'])

        if 'manufacturer' in self.device_info:
            self.info_fields['Manufacturer'].setText(self.device_info['manufacturer'])

        if 'android_version' in self.device_info:
            self.info_fields['Android Version'].setText(self.device_info['android_version'])

        if 'serial' in self.device_info:
            serial = str(self.device_info['serial']).strip()
            if '\n' in serial:
                serial = serial.split('\n')[0].strip()
            self.info_fields['Serial Number'].setText(serial)

        if 'battery' in self.device_info:
            self.info_fields['Battery Level'].setText(self.device_info['battery'])

        if 'imei' in self.device_info:
            self.info_fields['IMEI'].setText(self.device_info['imei'])
        elif 'device_id' in self.device_info:
            self.info_fields['IMEI'].setText(f"{self.device_info['device_id']} (Android ID)")

        if 'storage' in self.device_info:
            self.adv_info_fields['Storage'].setText(self.device_info['storage'])

        if 'ram' in self.device_info:
            self.adv_info_fields['RAM'].setText(self.device_info['ram'])

        if 'resolution' in self.device_info:
            self.adv_info_fields['Screen Resolution'].setText(self.device_info['resolution'])

        if 'cpu' in self.device_info:
            self.adv_info_fields['CPU'].setText(self.device_info['cpu'])

        if 'kernel' in self.device_info:
            self.adv_info_fields['Kernel'].setText(self.device_info['kernel'])
