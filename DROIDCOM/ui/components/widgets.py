"""
DROIDCOM - Widgets Module
Contains widget creation and UI-related functionality.
Modern dark theme with sleek design.
"""

import threading
import time
import logging

from PySide6 import QtCore, QtGui, QtWidgets

from ...utils.qt_dispatcher import emit_ui
from ..icon_utils import get_status_icon, create_icon_label
from ..styles import (
    get_main_stylesheet,
    get_card_button_style,
    get_action_button_style,
    get_secondary_button_style,
    get_primary_button_style,
    get_log_text_style,
    COLORS,
    EMOJI_ICONS,
)
from ...tabs import tab_device_info, tab_tools
from ...app.config import APP_VERSION, BUILD_DATE

LOG_LEVEL_COLORS = {
    "info": COLORS["text_primary"],
    "warning": COLORS["warning"],
    "error": COLORS["error"],
    "success": COLORS["success"],
}


class GlowButton(QtWidgets.QPushButton):
    """A button with hover glow effect"""

    def __init__(self, text, parent=None, icon_text=None):
        if icon_text:
            super().__init__(f"{icon_text}  {text}", parent)
        else:
            super().__init__(text, parent)

    def enterEvent(self, event):
        # Add subtle glow effect via style
        self.setGraphicsEffect(None)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setGraphicsEffect(None)
        super().leaveEvent(event)


class ModernCard(QtWidgets.QFrame):
    """A modern card widget with rounded corners and subtle shadow"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 12px;
            }}
        """)


class StatusIndicator(QtWidgets.QWidget):
    """A status indicator with icon and text"""

    def __init__(self, text, is_active=False, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Status dot
        self.dot = QtWidgets.QLabel(self)
        self.dot.setFixedSize(10, 10)
        self.update_status(is_active)

        # Status text
        self.text_label = QtWidgets.QLabel(text, self)

        layout.addWidget(self.dot)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def update_status(self, is_active):
        color = COLORS['success'] if is_active else COLORS['error']
        self.dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 5px;
        """)


class WidgetsMixin:
    """Mixin class providing widget creation and UI utility methods."""

    def create_widgets(self):
        """Create the main UI widgets with modern styling.

        Layout: a two-panel horizontal split. The left panel holds the
        header, platform-tools status, and the tabbed device/tools UI.
        The right panel is a fixed-width console that stays visible
        regardless of which left-hand tab is active.
        """
        # Apply the main stylesheet
        self.setStyleSheet(get_main_stylesheet())

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main container widget
        main_container = QtWidgets.QWidget(self)
        main_layout.addWidget(main_container, 1)

        split_layout = QtWidgets.QHBoxLayout(main_container)
        split_layout.setContentsMargins(16, 16, 16, 16)
        split_layout.setSpacing(16)

        # === LEFT PANEL ===
        left_panel = QtWidgets.QWidget(main_container)
        content_layout = QtWidgets.QVBoxLayout(left_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        split_layout.addWidget(left_panel, 1)

        # === HEADER SECTION ===
        self._create_header(content_layout, left_panel)

        # === TOOLS STATUS SECTION ===
        self._create_tools_status(content_layout, left_panel)

        # === MAIN TAB WIDGET ===
        self._create_main_tabs(content_layout, left_panel)

        # === RIGHT PANEL (always-visible console) ===
        self._create_log_section(split_layout, main_container)

        # === STATUS BAR ===
        self._create_status_bar(main_layout)

        # Initialize log with a welcome message
        self.log_message("DroidCom initialized - Ready for device connection", level="info")

    def _create_header(self, content_layout, parent):
        """Create the modern header section.

        Sized to its content via the layout's own size hints rather than a
        hard ``setMaximumHeight`` clamp, so the logo/title can never be
        clipped regardless of font/DPI.
        """
        header_frame = QtWidgets.QFrame(parent)
        header_frame.setProperty("headerFrame", True)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_primary']}15,
                    stop:0.5 {COLORS['accent_secondary']}08,
                    stop:1 transparent);
                border: 1px solid {COLORS['surface_border']};
                border-radius: 14px;
            }}
        """)
        header_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        # Left side - Icon and Title
        title_container = QtWidgets.QWidget(header_frame)
        title_layout = QtWidgets.QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        # Android Robot Icon (using SVG)
        icon_label = create_icon_label('android-robot', size=28)
        icon_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(icon_label)

        # Title and subtitle
        text_container = QtWidgets.QWidget(title_container)
        text_layout = QtWidgets.QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        header_label = QtWidgets.QLabel("DROIDCOM", text_container)
        header_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            background: transparent;
            letter-spacing: 1px;
        """)
        header_label.setWordWrap(False)
        text_layout.addWidget(header_label)

        subtitle_label = QtWidgets.QLabel("Android Device Management & Control", text_container)
        subtitle_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        subtitle_label.setWordWrap(False)
        text_layout.addWidget(subtitle_label)

        title_layout.addWidget(text_container)
        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Forensic Mode active indicator (hidden until toggled on)
        self.forensic_indicator = QtWidgets.QLabel("FORENSIC MODE ACTIVE", header_frame)
        self.forensic_indicator.setStyleSheet(f"""
            background-color: {COLORS['error_bg']};
            color: white;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
        """)
        self.forensic_indicator.setVisible(False)
        header_layout.addWidget(self.forensic_indicator)

        # Forensic Mode toggle
        self.forensic_mode_btn = QtWidgets.QPushButton("Forensic Mode", header_frame)
        self.forensic_mode_btn.setCheckable(True)
        self.forensic_mode_btn.setStyleSheet(get_secondary_button_style())
        self.forensic_mode_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.forensic_mode_btn.clicked.connect(self.toggle_forensic_mode)
        header_layout.addWidget(self.forensic_mode_btn)

        # Settings button
        settings_btn = QtWidgets.QPushButton(header_frame)
        settings_btn.setToolTip("Settings / Preferences")
        settings_icon = create_icon_label(EMOJI_ICONS['settings'], size=16)
        settings_layout = QtWidgets.QHBoxLayout(settings_btn)
        settings_layout.addWidget(settings_icon)
        settings_layout.setContentsMargins(8, 0, 8, 0)
        settings_btn.setStyleSheet(get_secondary_button_style())
        settings_btn.setCursor(QtCore.Qt.PointingHandCursor)
        settings_btn.setFixedSize(36, 32)
        settings_btn.clicked.connect(self.open_settings_dialog)
        header_layout.addWidget(settings_btn)

        # Help button
        help_btn = QtWidgets.QPushButton("?", header_frame)
        help_btn.setToolTip("Help / Documentation")
        help_btn.setStyleSheet(get_secondary_button_style())
        help_btn.setCursor(QtCore.Qt.PointingHandCursor)
        help_btn.setFixedSize(32, 32)
        help_btn.clicked.connect(self.open_help_dialog)
        header_layout.addWidget(help_btn)

        # Connection status indicator
        self.connection_indicator = QtWidgets.QLabel("Disconnected", header_frame)
        self.connection_indicator.setStyleSheet(f"""
            background-color: {COLORS['background_hover']};
            color: {COLORS['text_secondary']};
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.connection_indicator)

        content_layout.addWidget(header_frame)

    def set_connection_indicator(self, connected, device_name=None):
        """Update the persistent connection status indicator."""
        if not hasattr(self, 'connection_indicator'):
            return
        if connected:
            label = f"Connected: {device_name}" if device_name else "Connected"
            self.connection_indicator.setText(label)
            self.connection_indicator.setStyleSheet(f"""
                background-color: {COLORS['success_bg']};
                color: white;
                padding: 4px 10px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            """)
        else:
            self.connection_indicator.setText("Disconnected")
            self.connection_indicator.setStyleSheet(f"""
                background-color: {COLORS['background_hover']};
                color: {COLORS['text_secondary']};
                padding: 4px 10px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            """)

    def toggle_forensic_mode(self):
        """Enable/disable Forensic Mode: gates write operations and enforces
        case metadata entry while active."""
        enabling = self.forensic_mode_btn.isChecked()
        if enabling:
            if not self.case_metadata and not self.prompt_case_metadata():
                self.forensic_mode_btn.setChecked(False)
                return
            self.forensic_mode = True
            if self.write_blocker is not None:
                self.write_blocker.enabled = True
            self.forensic_indicator.setVisible(True)
            self.log_message("Forensic Mode enabled - write operations disabled", level="warning")
        else:
            self.forensic_mode = False
            self.forensic_indicator.setVisible(False)
            self.log_message("Forensic Mode disabled", level="info")

    def open_settings_dialog(self):
        """Show a basic settings/preferences dialog."""
        QtWidgets.QMessageBox.information(
            self, "Settings",
            f"DROIDCOM v{APP_VERSION}\n\nSettings/preferences are not yet configurable from this dialog."
        )

    def open_help_dialog(self):
        """Show a basic help/documentation dialog."""
        QtWidgets.QMessageBox.information(
            self, "Help & Documentation",
            "See DROIDCOM/README.md in the repository for full usage documentation, "
            "feature descriptions, and setup instructions."
        )

    def _create_tools_status(self, content_layout, parent):
        """Create the tools status section.

        No hard max-height clamp is applied here, so the "Install Platform
        Tools" button (and its padding) is never clipped by the frame.
        """
        self.setup_status_frame = QtWidgets.QFrame(parent)
        self.setup_status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 10px;
            }}
        """)
        self.setup_status_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        setup_layout = QtWidgets.QHBoxLayout(self.setup_status_frame)
        setup_layout.setContentsMargins(14, 10, 14, 10)
        setup_layout.setSpacing(10)

        # Status icon
        icon_label = create_icon_label('success' if self.platform_tools_installed else 'error', size=14)
        icon_label.setStyleSheet("background: transparent;")
        setup_layout.addWidget(icon_label)

        # Status text
        tools_status = "Installed" if self.platform_tools_installed else "Not Installed"
        status_color = COLORS['success'] if self.platform_tools_installed else COLORS['error']
        self.tools_label = QtWidgets.QLabel(
            f"Android Platform Tools: <span style='color: {status_color}; font-weight: 600;'>{tools_status}</span>",
            self.setup_status_frame
        )
        self.tools_label.setTextFormat(QtCore.Qt.RichText)
        self.tools_label.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        setup_layout.addWidget(self.tools_label)
        setup_layout.addStretch()

        if not self.platform_tools_installed:
            tools_btn = QtWidgets.QPushButton("Install Platform Tools", self.setup_status_frame)
            tools_btn.setStyleSheet(get_primary_button_style())
            tools_btn.clicked.connect(self.install_platform_tools)
            tools_btn.setCursor(QtCore.Qt.PointingHandCursor)
            setup_layout.addWidget(tools_btn)

        content_layout.addWidget(self.setup_status_frame)

    def _create_main_tabs(self, content_layout, parent):
        """Create the main tabbed interface"""
        self.notebook = QtWidgets.QTabWidget(parent)
        self.notebook.setDocumentMode(True)
        content_layout.addWidget(self.notebook, 1)

        # Device Info Tab
        self._create_device_info_tab()

        # Android Tools Tab
        self._create_tools_tab()

    def _create_device_info_tab(self):
        """Create the Device Info tab with modern styling and scrollable content"""
        tab_device_info.create_device_info_tab(self)

    def _create_device_info_display(self, parent_layout):
        """Create the device information display section"""
        tab_device_info.create_device_info_display(self, parent_layout)

    def _create_device_actions(self, parent_layout):
        """Create the device actions section"""
        tab_device_info.create_device_actions(self, parent_layout)

    def _create_tools_tab(self):
        """Create the Android Tools tab with all tool categories"""
        tab_tools.create_tools_tab(self)

    def _add_tool_button(self, layout, row, col, text, callback, icon=None):
        """Add a styled tool button to the layout"""
        button = QtWidgets.QPushButton(text)
        button.setStyleSheet(get_card_button_style())
        button.setMinimumWidth(145)
        button.setMinimumHeight(42)
        button.setCursor(QtCore.Qt.PointingHandCursor)
        button.clicked.connect(callback)
        
        if icon:
            icon_widget = create_icon_label(icon, size=16)
            text_label = QtWidgets.QLabel(text)
            button.setText("")
            button_layout = QtWidgets.QHBoxLayout(button)
            button_layout.addWidget(icon_widget)
            button_layout.addWidget(text_label)
            button_layout.addStretch()
            button_layout.setSpacing(8)
            button_layout.setContentsMargins(12, 0, 12, 0)
        
        layout.addWidget(button, row, col)

    def _populate_category_buttons(self, category_name, layout):
        """Populate buttons for a given category"""
        if category_name == "Device Control":
            self._add_tool_button(layout, 0, 0, "Reboot Device", self._reboot_device_normal, "reboot")
            self._add_tool_button(layout, 1, 0, "Reboot Recovery", self._reboot_device_recovery, "refresh")
            self._add_tool_button(layout, 2, 0, "Reboot Bootloader", self._reboot_device_bootloader, "cpu")
            self._add_tool_button(layout, 3, 0, "WiFi Toggle", self._toggle_wifi, "wifi")
            self._add_tool_button(layout, 4, 0, "Airplane Mode", self._toggle_airplane_mode, "airplane")
            self._add_tool_button(layout, 5, 0, "Screen Toggle", self._toggle_screen, "screen")
            self._add_tool_button(layout, 0, 1, "Reboot EDL", self._reboot_device_edl, "lightning")
            self._add_tool_button(layout, 1, 1, "Mobile Data", self._toggle_mobile_data, "mobile-data")
            self._add_tool_button(layout, 2, 1, "Bluetooth", self._toggle_bluetooth, "bluetooth")
            self._add_tool_button(layout, 3, 1, "Brightness", self._set_brightness_dialog, "brightness")
            self._add_tool_button(layout, 4, 1, "Screen Timeout", self._set_screen_timeout_dialog, "timer")
            self._add_tool_button(layout, 5, 1, "Screenshot", lambda: self._run_in_thread(self.take_screenshot), "camera")
            self._add_tool_button(layout, 0, 2, "DND Toggle", self._toggle_do_not_disturb, "bell-slash")
            self._add_tool_button(layout, 1, 2, "Power Button", self._simulate_power_button, "power")
            self._add_tool_button(layout, 2, 2, "Flashlight", self._toggle_flashlight, "flashlight")
            self._add_tool_button(layout, 3, 2, "Blind Setup", self._blind_setup_dialog, "screen")

        elif category_name == "App Management":
            self._add_tool_button(layout, 0, 0, "Install APK", self.install_apk, "download")
            self._add_tool_button(layout, 1, 0, "Uninstall App", self._uninstall_app_dialog, "trash")
            self._add_tool_button(layout, 2, 0, "Clear App Data", self._clear_app_data_dialog, "clean")
            self._add_tool_button(layout, 3, 0, "Force Stop App", self._force_stop_app_dialog, "power")
            self._add_tool_button(layout, 4, 0, "List Installed", self._list_installed_apps, "clipboard")
            self._add_tool_button(layout, 5, 0, "Open App", self._open_app_dialog, "rocket")
            self._add_tool_button(layout, 0, 1, "Extract APK", self._extract_apk_dialog, "upload")
            self._add_tool_button(layout, 1, 1, "Freeze/Unfreeze", self._toggle_freeze_dialog, "snowflake")
            self._add_tool_button(layout, 2, 1, "View Permissions", self._view_permissions_dialog, "lock")
            self._add_tool_button(layout, 3, 1, "App Usage Stats", self._show_app_usage_stats, "chart")
            self._add_tool_button(layout, 4, 1, "Battery Usage", self._show_battery_usage, "battery")

        elif category_name == "System Tools":
            self._add_tool_button(layout, 0, 0, "Device Info", self._show_detailed_device_info, "screen")
            self._add_tool_button(layout, 1, 0, "Battery Stats", self._show_battery_stats, "battery")
            self._add_tool_button(layout, 2, 0, "Running Services", self._show_running_services, "settings")
            self._add_tool_button(layout, 3, 0, "Network Stats", self._show_network_stats, "globe")
            self._add_tool_button(layout, 4, 0, "Thermal Stats", self._show_thermal_stats, "thermometer")
            self._add_tool_button(layout, 5, 0, "Sensor Status", self._show_sensor_status, "sensor")
            self._add_tool_button(layout, 0, 1, "Power Profile", self._show_power_profile, "lightning")
            self._add_tool_button(layout, 1, 1, "Location Settings", self._show_location_settings, "location")
            self._add_tool_button(layout, 2, 1, "Doze Mode", self._show_doze_mode_status, "sleep")
            self._add_tool_button(layout, 3, 1, "SELinux Status", self._show_selinux_status, "shield")
            self._add_tool_button(layout, 4, 1, "Time and Date", self._show_time_date_info, "clock")
            self._add_tool_button(layout, 5, 1, "CPU Governor", self._show_cpu_governor_info, "cpu")

        elif category_name == "Debugging":
            self._add_tool_button(layout, 0, 2, "ANR Traces", self._show_anr_traces, "bug")
            self._add_tool_button(layout, 1, 2, "Crash Dumps", self._show_crash_dumps, "fire")
            self._add_tool_button(layout, 2, 2, "Bug Report", self._generate_bug_report, "pencil")
            self._add_tool_button(layout, 3, 2, "Screen Record", self._start_screen_recording, "video")

        elif category_name == "File Operations":
            self._add_tool_button(layout, 0, 0, "File Manager", self.manage_files, "folder")
            self._add_tool_button(layout, 1, 0, "Pull from Device", self._pull_from_device, "download")
            self._add_tool_button(layout, 2, 0, "Push to Device", self._push_to_device, "upload")
            self._add_tool_button(layout, 3, 0, "Backup Device", self.backup_device, "database")
            self._add_tool_button(layout, 4, 0, "View Storage", self._show_storage_info, "chart")
            self._add_tool_button(layout, 5, 0, "Clean Caches", self._clean_app_caches, "clean")
            self._add_tool_button(layout, 0, 1, "Explore Protected", self._explore_protected_storage, "lock-open")
            self._add_tool_button(layout, 1, 1, "Search Files", self._search_files_on_device, "search")
            self._add_tool_button(layout, 2, 1, "Export SQLite", self._export_sqlite_databases, "database")
            self._add_tool_button(layout, 3, 1, "Dir Size Calc", self._calculate_directory_size, "chart")
            self._add_tool_button(layout, 4, 1, "File Checksum", self._calculate_file_checksum, "lock")
            self._add_tool_button(layout, 5, 1, "Edit Text File", self._edit_text_file_on_device, "pencil")
            self._add_tool_button(layout, 0, 2, "Mount Info", self._show_mount_info, "database")
            self._add_tool_button(layout, 1, 2, "Recent Files", self._list_recent_files, "file")

        elif category_name == "Security & Permissions":
            self._add_tool_button(layout, 0, 0, "Check Root", self._check_root_status, "lock")
            self._add_tool_button(layout, 1, 0, "Check AppOps", self._check_appops_dialog, "search")
            self._add_tool_button(layout, 2, 0, "Change AppOps", self._change_appops_dialog, "settings")
            self._add_tool_button(layout, 3, 0, "Check Encryption", self._check_encryption_status, "lock")
            self._add_tool_button(layout, 4, 0, "Lock Screen", self._check_lock_screen_status, "lock-open")
            self._add_tool_button(layout, 5, 0, "Verify Boot", self._verify_boot_integrity, "shield")
            self._add_tool_button(layout, 0, 1, "Keystore Info", self._show_keystore_info, "lock")
            self._add_tool_button(layout, 1, 1, "Cert Checker", self._check_certificates, "file")
            self._add_tool_button(layout, 2, 1, "Security Patch", self._check_security_patch_level, "shield")
            self._add_tool_button(layout, 3, 1, "Perm Scanner", self._scan_dangerous_permissions, "warning")

        elif category_name == "Automation & Scripting":
            self._add_tool_button(layout, 0, 0, "Run Shell Script", self._run_shell_script_dialog, "terminal")
            self._add_tool_button(layout, 1, 0, "Batch App Manager", self._batch_app_manager_dialog, "package")
            self._add_tool_button(layout, 2, 0, "Scheduled Tasks", self._scheduled_tasks_dialog, "clock")
            self._add_tool_button(layout, 3, 0, "Logcat + Screencap", self._logcat_screencap_dialog, "camera")
            self._add_tool_button(layout, 4, 0, "Monkey Testing", self._monkey_testing_dialog, "refresh")

        elif category_name == "Advanced Tests":
            self._add_tool_button(layout, 0, 0, "Lock Brute Force", self.run_screen_lock_brute_forcer, "lock")
            self._add_tool_button(layout, 1, 0, "Lock Duplicator", self.run_screen_lock_duplicator, "clipboard")
            self._add_tool_button(layout, 2, 0, "Hardware Stress", self.run_hardware_stress_test, "sensor")
            self._add_tool_button(layout, 3, 0, "Looped Benchmark", self.run_looped_benchmarking, "refresh")
            self._add_tool_button(layout, 4, 0, "Screen Mirror", self.run_scrcpy_mirror, "wifi-tethering")
            self._add_tool_button(layout, 5, 0, "I/O Spike Gen", self.run_io_spike_generator, "lightning")
            self._add_tool_button(layout, 0, 1, "App Crash Forcer", self.run_app_crash_forcer, "fire")
            self._add_tool_button(layout, 1, 1, "Dalvik Cache Test", self.run_dalvik_cache_stress_test, "database")
            self._add_tool_button(layout, 2, 1, "RAM Fill Test", self.run_ram_fill_test, "cpu")
            self._add_tool_button(layout, 3, 1, "GPU Stress Test", self.run_gpu_stress_test, "cpu")
            self._add_tool_button(layout, 4, 1, "CPU Max Load", self.run_cpu_max_load_test, "cpu")
            self._add_tool_button(layout, 5, 1, "Battery Drain", self.run_battery_drain_test, "battery")

        elif category_name == "Forensics":
            self._add_tool_button(layout, 0, 0, "Andriller", self.run_andriller, "search")
            self._add_tool_button(layout, 1, 0, "ALEAPP Parser", self.run_aleapp, "clipboard")
            self._add_tool_button(layout, 2, 0, "MVT Check", self.run_mvt_check, "shield")
            self._add_tool_button(layout, 3, 0, "Autopsy", self.launch_autopsy, "rocket")

        elif category_name == "Evidence & Custody":
            self._add_tool_button(layout, 0, 0, "New Case", self.new_case_dialog, "file")
            self._add_tool_button(layout, 1, 0, "Toggle Write Blocker", self.toggle_write_blocker, "lock")
            self._add_tool_button(layout, 2, 0, "Acquire Image", self.run_device_acquisition, "download")
            self._add_tool_button(layout, 3, 0, "Verify Image", self.verify_acquisition_image, "shield")
            self._add_tool_button(layout, 0, 1, "Evidence Log", self.view_evidence_log, "clipboard")
            self._add_tool_button(layout, 1, 1, "Custody Report", self.generate_chain_of_custody_report, "file")

    def _create_log_section(self, split_layout, parent):
        """Create the right-hand console panel: fixed width, full window
        height, always visible regardless of the active left-hand tab."""
        self.log_frame = QtWidgets.QFrame(parent)
        self.log_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 12px;
            }}
        """)
        self.log_frame.setFixedWidth(400)
        log_layout = QtWidgets.QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(14, 14, 14, 14)
        log_layout.setSpacing(10)

        # Header row: "Session Log" title + Clear/Copy/Export buttons
        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(8)

        session_log_label = QtWidgets.QLabel("Session Log", self.log_frame)
        session_log_label.setStyleSheet(f"""
            color: {COLORS['accent_primary']};
            font-size: 16px;
            font-weight: 700;
            background: transparent;
        """)
        header_row.addWidget(session_log_label)
        header_row.addStretch()

        console_btn_style = get_secondary_button_style()

        clear_btn = QtWidgets.QPushButton("Clear", self.log_frame)
        clear_btn.setStyleSheet(console_btn_style)
        clear_btn.setCursor(QtCore.Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_console)
        header_row.addWidget(clear_btn)

        copy_btn = QtWidgets.QPushButton("Copy", self.log_frame)
        copy_btn.setStyleSheet(console_btn_style)
        copy_btn.setCursor(QtCore.Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_console)
        header_row.addWidget(copy_btn)

        export_btn = QtWidgets.QPushButton("Export", self.log_frame)
        export_btn.setStyleSheet(console_btn_style)
        export_btn.setCursor(QtCore.Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_console)
        header_row.addWidget(export_btn)

        log_layout.addLayout(header_row)

        self.log_text = QtWidgets.QTextEdit(self.log_frame)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(400)
        self.log_text.setStyleSheet(get_log_text_style())
        log_layout.addWidget(self.log_text, 1)
        split_layout.addWidget(self.log_frame)

    def _clear_console(self):
        self.log_text.clear()

    def _copy_console(self):
        QtWidgets.QApplication.clipboard().setText(self.log_text.toPlainText())
        self.update_status("Console output copied to clipboard")

    def _export_console(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Console Output", "droidcom_session_log.txt", "Text Files (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
            self.update_status(f"Console output exported to {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Could not export console output: {str(e)}")

    def _create_status_bar(self, main_layout):
        """Create the modern status bar"""
        status_frame = QtWidgets.QFrame(self)
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_dark']};
                border-top: 1px solid {COLORS['surface_border']};
            }}
        """)
        status_layout = QtWidgets.QHBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 10, 16, 10)

        # Status dot
        status_dot = QtWidgets.QLabel("\u25CF", status_frame)
        status_dot.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px; background: transparent;")
        status_layout.addWidget(status_dot)

        self.status_label = QtWidgets.QLabel("Ready", status_frame)
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            background: transparent;
        """)
        self.status_var = self.status_label
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # Version + build date
        version_label = QtWidgets.QLabel(f"v{APP_VERSION} ({BUILD_DATE})", status_frame)
        version_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            background: transparent;
        """)
        status_layout.addWidget(version_label)

        separator = QtWidgets.QLabel("|", status_frame)
        separator.setStyleSheet(f"color: {COLORS['surface_border']}; background: transparent;")
        status_layout.addWidget(separator)

        # Branding
        brand_label = QtWidgets.QLabel("CommandCore Suite", status_frame)
        brand_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            background: transparent;
        """)
        status_layout.addWidget(brand_label)

        main_layout.addWidget(status_frame)

    def log_message(self, message, level="info"):
        """Add a message to the log console with timestamp, colour-coded by severity.

        level: one of "info" (white), "warning" (yellow), "error" (red), "success" (green).
        """
        logging.info(f"[AndroidTools] {message}")

        if self.log_text is not None:
            try:
                timestamp = time.strftime('%H:%M:%S')
                color = LOG_LEVEL_COLORS.get(level, LOG_LEVEL_COLORS["info"])
                formatted_msg = (
                    f'<span style="color: {COLORS["accent_primary"]};">[{timestamp}]</span> '
                    f'<span style="color: {color};">{message}</span>'
                )
                self.log_text.append(formatted_msg)
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
                    emit_ui(self, lambda: self.log_message(f"Error in thread: {str(e)}"))

        thread = threading.Thread(target=thread_wrapper)
        thread.daemon = True
        self.threads.append(thread)
        thread.start()
        return thread

    def update_device_info(self):
        """Update the device info display with the connected device information"""
        if hasattr(self, 'onboarding_frame'):
            self.onboarding_frame.setVisible(not self.device_info)
        if hasattr(self, 'set_connection_indicator'):
            self.set_connection_indicator(
                connected=bool(self.device_info),
                device_name=(self.device_info or {}).get('model') if self.device_info else None,
            )

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

        if 'build_number' in self.device_info:
            self.info_fields['Build Number'].setText(self.device_info['build_number'])

        if 'security_patch' in self.device_info:
            self.adv_info_fields['Security Patch Level'].setText(self.device_info['security_patch'])

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
