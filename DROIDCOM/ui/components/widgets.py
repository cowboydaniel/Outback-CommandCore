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
from ..styles import (
    get_main_stylesheet,
    get_card_button_style,
    get_action_button_style,
    get_primary_button_style,
    get_log_text_style,
    COLORS,
    EMOJI_ICONS,
)
from ...tabs import tab_device_info, tab_tools


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
        """Create the main UI widgets with modern styling"""
        # Apply the main stylesheet
        self.setStyleSheet(get_main_stylesheet())

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main container widget
        main_container = QtWidgets.QWidget(self)
        main_layout.addWidget(main_container, 1)

        content_layout = QtWidgets.QVBoxLayout(main_container)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # === HEADER SECTION ===
        self._create_header(content_layout, main_container)

        # === TOOLS STATUS SECTION ===
        self._create_tools_status(content_layout, main_container)

        # === MAIN TAB WIDGET ===
        self._create_main_tabs(content_layout, main_container)

        # === LOG SECTION ===
        self._create_log_section(content_layout, main_container)

        # === STATUS BAR ===
        self._create_status_bar(main_layout)

        # Initialize log with a welcome message
        self.log_message("DroidCom initialized - Ready for device connection")

    def _create_header(self, content_layout, parent):
        """Create the modern header section"""
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
                padding: 10px;
            }}
        """)
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)

        # Left side - Icon and Title
        title_container = QtWidgets.QWidget(header_frame)
        title_layout = QtWidgets.QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(16)

        # Android Robot Icon (using emoji as fallback)
        icon_label = QtWidgets.QLabel("\U0001F4F1", title_container)  # 📱
        icon_label.setStyleSheet(f"""
            font-size: 36px;
            background: transparent;
        """)
        title_layout.addWidget(icon_label)

        # Title and subtitle
        text_container = QtWidgets.QWidget(title_container)
        text_layout = QtWidgets.QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        header_label = QtWidgets.QLabel("DROIDCOM", text_container)
        header_label.setStyleSheet(f"""
            font-size: 26px;
            font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
            letter-spacing: 2px;
        """)
        text_layout.addWidget(header_label)

        subtitle_label = QtWidgets.QLabel("Android Device Management & Control", text_container)
        subtitle_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        text_layout.addWidget(subtitle_label)

        title_layout.addWidget(text_container)
        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Right side - Version badge
        version_badge = QtWidgets.QLabel("v2.0", header_frame)
        version_badge.setStyleSheet(f"""
            background-color: {COLORS['accent_muted']};
            color: {COLORS['accent_primary']};
            padding: 6px 14px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        """)
        header_layout.addWidget(version_badge)

        content_layout.addWidget(header_frame)

    def _create_tools_status(self, content_layout, parent):
        """Create the tools status section"""
        self.setup_status_frame = QtWidgets.QFrame(parent)
        self.setup_status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 10px;
            }}
        """)
        setup_layout = QtWidgets.QHBoxLayout(self.setup_status_frame)
        setup_layout.setContentsMargins(16, 12, 16, 12)
        setup_layout.setSpacing(16)

        # Status icon
        status_icon = "\u2705" if self.platform_tools_installed else "\u274C"
        icon_label = QtWidgets.QLabel(status_icon, self.setup_status_frame)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
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
            font-size: 13px;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        setup_layout.addWidget(self.tools_label)
        setup_layout.addStretch()

        if not self.platform_tools_installed:
            tools_btn = QtWidgets.QPushButton("\U0001F4E5 Install Platform Tools", self.setup_status_frame)
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
        if icon:
            button = QtWidgets.QPushButton(f"{icon} {text}")
        else:
            button = QtWidgets.QPushButton(text)
        button.setStyleSheet(get_card_button_style())
        button.setMinimumWidth(145)
        button.setMinimumHeight(42)
        button.setCursor(QtCore.Qt.PointingHandCursor)
        button.clicked.connect(callback)
        layout.addWidget(button, row, col)

    def _populate_category_buttons(self, category_name, layout):
        """Populate buttons for a given category"""
        if category_name == "Device Control":
            self._add_tool_button(layout, 0, 0, "Reboot Device", lambda: self._run_in_thread(self._reboot_device_normal), "\U0001F504")
            self._add_tool_button(layout, 1, 0, "Reboot Recovery", lambda: self._run_in_thread(self._reboot_device_recovery), "\U0001F501")
            self._add_tool_button(layout, 2, 0, "Reboot Bootloader", lambda: self._run_in_thread(self._reboot_device_bootloader), "\U0001F4BB")
            self._add_tool_button(layout, 3, 0, "WiFi Toggle", lambda: self._run_in_thread(self._toggle_wifi), "\U0001F4F6")
            self._add_tool_button(layout, 4, 0, "Airplane Mode", lambda: self._run_in_thread(self._toggle_airplane_mode), "\u2708\ufe0f")
            self._add_tool_button(layout, 5, 0, "Screen Toggle", lambda: self._run_in_thread(self._toggle_screen), "\U0001F4F1")
            self._add_tool_button(layout, 0, 1, "Reboot EDL", lambda: self._run_in_thread(self._reboot_device_edl), "\u26A1")
            self._add_tool_button(layout, 1, 1, "Mobile Data", lambda: self._run_in_thread(self._toggle_mobile_data), "\U0001F4E1")
            self._add_tool_button(layout, 2, 1, "Bluetooth", lambda: self._run_in_thread(self._toggle_bluetooth), "\U0001F4F6")
            self._add_tool_button(layout, 3, 1, "Brightness", lambda: self._run_in_thread(self._set_brightness_dialog), "\U0001F506")
            self._add_tool_button(layout, 4, 1, "Screen Timeout", lambda: self._run_in_thread(self._set_screen_timeout_dialog), "\u23F1")
            self._add_tool_button(layout, 5, 1, "Screenshot", lambda: self._run_in_thread(self.take_screenshot), "\U0001F4F8")
            self._add_tool_button(layout, 0, 2, "DND Toggle", lambda: self._run_in_thread(self._toggle_do_not_disturb), "\U0001F515")
            self._add_tool_button(layout, 1, 2, "Power Button", lambda: self._run_in_thread(self._simulate_power_button), "\u23FB")
            self._add_tool_button(layout, 2, 2, "Flashlight", lambda: self._run_in_thread(self._toggle_flashlight), "\U0001F526")

        elif category_name == "App Management":
            self._add_tool_button(layout, 0, 0, "Install APK", self.install_apk, "\U0001F4E5")
            self._add_tool_button(layout, 1, 0, "Uninstall App", lambda: self._run_in_thread(self._uninstall_app_dialog), "\U0001F5D1")
            self._add_tool_button(layout, 2, 0, "Clear App Data", lambda: self._run_in_thread(self._clear_app_data_dialog), "\U0001F9F9")
            self._add_tool_button(layout, 3, 0, "Force Stop App", lambda: self._run_in_thread(self._force_stop_app_dialog), "\U0001F6D1")
            self._add_tool_button(layout, 4, 0, "List Installed", lambda: self._run_in_thread(self._list_installed_apps), "\U0001F4CB")
            self._add_tool_button(layout, 5, 0, "Open App", lambda: self._run_in_thread(self._open_app_dialog), "\U0001F680")
            self._add_tool_button(layout, 0, 1, "Extract APK", lambda: self._run_in_thread(self._extract_apk_dialog), "\U0001F4E4")
            self._add_tool_button(layout, 1, 1, "Freeze/Unfreeze", lambda: self._run_in_thread(self._toggle_freeze_dialog), "\u2744\ufe0f")
            self._add_tool_button(layout, 2, 1, "View Permissions", lambda: self._run_in_thread(self._view_permissions_dialog), "\U0001F512")
            self._add_tool_button(layout, 3, 1, "App Usage Stats", lambda: self._run_in_thread(self._show_app_usage_stats), "\U0001F4CA")
            self._add_tool_button(layout, 4, 1, "Battery Usage", lambda: self._run_in_thread(self._show_battery_usage), "\U0001F50B")

        elif category_name == "System Tools":
            self._add_tool_button(layout, 0, 0, "Device Info", lambda: self._run_in_thread(self._show_detailed_device_info), "\U0001F4F1")
            self._add_tool_button(layout, 1, 0, "Battery Stats", lambda: self._run_in_thread(self._show_battery_stats), "\U0001F50B")
            self._add_tool_button(layout, 2, 0, "Running Services", lambda: self._run_in_thread(self._show_running_services), "\u2699\ufe0f")
            self._add_tool_button(layout, 3, 0, "Network Stats", lambda: self._run_in_thread(self._show_network_stats), "\U0001F310")
            self._add_tool_button(layout, 4, 0, "Thermal Stats", lambda: self._run_in_thread(self._show_thermal_stats), "\U0001F321")
            self._add_tool_button(layout, 5, 0, "Sensor Status", lambda: self._run_in_thread(self._show_sensor_status), "\U0001F4E1")
            self._add_tool_button(layout, 0, 1, "Power Profile", lambda: self._run_in_thread(self._show_power_profile), "\u26A1")
            self._add_tool_button(layout, 1, 1, "Location Settings", lambda: self._run_in_thread(self._show_location_settings), "\U0001F4CD")
            self._add_tool_button(layout, 2, 1, "Doze Mode", lambda: self._run_in_thread(self._show_doze_mode_status), "\U0001F4A4")
            self._add_tool_button(layout, 3, 1, "SELinux Status", lambda: self._run_in_thread(self._show_selinux_status), "\U0001F6E1")
            self._add_tool_button(layout, 4, 1, "Time and Date", lambda: self._run_in_thread(self._show_time_date_info), "\U0001F552")
            self._add_tool_button(layout, 5, 1, "CPU Governor", lambda: self._run_in_thread(self._show_cpu_governor_info), "\U0001F4BB")

        elif category_name == "Debugging":
            self._add_tool_button(layout, 0, 2, "ANR Traces", lambda: self._run_in_thread(self._show_anr_traces), "\U0001F41E")
            self._add_tool_button(layout, 1, 2, "Crash Dumps", lambda: self._run_in_thread(self._show_crash_dumps), "\U0001F4A5")
            self._add_tool_button(layout, 2, 2, "Bug Report", lambda: self._run_in_thread(self._generate_bug_report), "\U0001F4DD")
            self._add_tool_button(layout, 3, 2, "Screen Record", lambda: self._run_in_thread(self._start_screen_recording), "\U0001F3AC")

        elif category_name == "File Operations":
            self._add_tool_button(layout, 0, 0, "File Manager", self.manage_files, "\U0001F4C2")
            self._add_tool_button(layout, 1, 0, "Pull from Device", lambda: self._run_in_thread(self._pull_from_device), "\U0001F4E4")
            self._add_tool_button(layout, 2, 0, "Push to Device", lambda: self._run_in_thread(self._push_to_device), "\U0001F4E5")
            self._add_tool_button(layout, 3, 0, "Backup Device", lambda: self._run_in_thread(self.backup_device), "\U0001F4BE")
            self._add_tool_button(layout, 4, 0, "View Storage", lambda: self._run_in_thread(self._show_storage_info), "\U0001F4CA")
            self._add_tool_button(layout, 5, 0, "Clean Caches", lambda: self._run_in_thread(self._clean_app_caches), "\U0001F9F9")
            self._add_tool_button(layout, 0, 1, "Explore Protected", lambda: self._run_in_thread(self._explore_protected_storage), "\U0001F510")
            self._add_tool_button(layout, 1, 1, "Search Files", lambda: self._run_in_thread(self._search_files_on_device), "\U0001F50D")
            self._add_tool_button(layout, 2, 1, "Export SQLite", lambda: self._run_in_thread(self._export_sqlite_databases), "\U0001F4BE")
            self._add_tool_button(layout, 3, 1, "Dir Size Calc", lambda: self._run_in_thread(self._calculate_directory_size), "\U0001F4C8")
            self._add_tool_button(layout, 4, 1, "File Checksum", lambda: self._run_in_thread(self._calculate_file_checksum), "\U0001F510")
            self._add_tool_button(layout, 5, 1, "Edit Text File", lambda: self._run_in_thread(self._edit_text_file_on_device), "\U0001F4DD")
            self._add_tool_button(layout, 0, 2, "Mount Info", lambda: self._run_in_thread(self._show_mount_info), "\U0001F4BE")
            self._add_tool_button(layout, 1, 2, "Recent Files", lambda: self._run_in_thread(self._list_recent_files), "\U0001F4C4")

        elif category_name == "Security & Permissions":
            self._add_tool_button(layout, 0, 0, "Check Root", lambda: self._run_in_thread(self._check_root_status), "\U0001F510")
            self._add_tool_button(layout, 1, 0, "Check AppOps", self._check_appops_dialog, "\U0001F50D")
            self._add_tool_button(layout, 2, 0, "Change AppOps", self._change_appops_dialog, "\u2699\ufe0f")
            self._add_tool_button(layout, 3, 0, "Check Encryption", lambda: self._run_in_thread(self._check_encryption_status), "\U0001F512")
            self._add_tool_button(layout, 4, 0, "Lock Screen", lambda: self._run_in_thread(self._check_lock_screen_status), "\U0001F513")
            self._add_tool_button(layout, 5, 0, "Verify Boot", lambda: self._run_in_thread(self._verify_boot_integrity), "\U0001F6E1")
            self._add_tool_button(layout, 0, 1, "Keystore Info", lambda: self._run_in_thread(self._show_keystore_info), "\U0001F511")
            self._add_tool_button(layout, 1, 1, "Cert Checker", lambda: self._run_in_thread(self._check_certificates), "\U0001F4DC")
            self._add_tool_button(layout, 2, 1, "Security Patch", lambda: self._run_in_thread(self._check_security_patch_level), "\U0001F6E1")
            self._add_tool_button(layout, 3, 1, "Perm Scanner", lambda: self._run_in_thread(self._scan_dangerous_permissions), "\u26A0")

        elif category_name == "Automation & Scripting":
            self._add_tool_button(layout, 0, 0, "Run Shell Script", lambda: self._run_in_thread(self._run_shell_script_dialog), "\U0001F4BB")
            self._add_tool_button(layout, 1, 0, "Batch App Manager", lambda: self._run_in_thread(self._batch_app_manager_dialog), "\U0001F4E6")
            self._add_tool_button(layout, 2, 0, "Scheduled Tasks", lambda: self._run_in_thread(self._scheduled_tasks_dialog), "\U0001F4C5")
            self._add_tool_button(layout, 3, 0, "Logcat + Screencap", lambda: self._run_in_thread(self._logcat_screencap_dialog), "\U0001F4F8")
            self._add_tool_button(layout, 4, 0, "Monkey Testing", lambda: self._run_in_thread(self._monkey_testing_dialog), "\U0001F412")

        elif category_name == "Advanced Tests":
            self._add_tool_button(layout, 0, 0, "Lock Brute Force", self.run_screen_lock_brute_forcer, "\U0001F510")
            self._add_tool_button(layout, 1, 0, "Lock Duplicator", self.run_screen_lock_duplicator, "\U0001F5DD")
            self._add_tool_button(layout, 2, 0, "Hardware Stress", self.run_hardware_stress_test, "\U0001F4AA")
            self._add_tool_button(layout, 3, 0, "Looped Benchmark", self.run_looped_benchmarking, "\U0001F3C3")
            self._add_tool_button(layout, 4, 0, "Screen Mirror", self.run_scrcpy_mirror, "\U0001F4FA")
            self._add_tool_button(layout, 5, 0, "I/O Spike Gen", self.run_io_spike_generator, "\u26A1")
            self._add_tool_button(layout, 0, 1, "App Crash Forcer", self.run_app_crash_forcer, "\U0001F4A5")
            self._add_tool_button(layout, 1, 1, "Dalvik Cache Test", self.run_dalvik_cache_stress_test, "\U0001F4BE")
            self._add_tool_button(layout, 2, 1, "RAM Fill Test", self.run_ram_fill_test, "\U0001F9E0")
            self._add_tool_button(layout, 3, 1, "GPU Stress Test", self.run_gpu_stress_test, "\U0001F3AE")
            self._add_tool_button(layout, 4, 1, "CPU Max Load", self.run_cpu_max_load_test, "\U0001F4BB")
            self._add_tool_button(layout, 5, 1, "Battery Drain", self.run_battery_drain_test, "\U0001F50B")

    def _create_log_section(self, content_layout, parent):
        """Create the log section with modern styling"""
        self.log_frame = QtWidgets.QGroupBox("Console Output", parent)
        log_layout = QtWidgets.QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(12, 20, 12, 12)

        self.log_text = QtWidgets.QTextEdit(self.log_frame)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(140)
        self.log_text.setMaximumHeight(180)
        self.log_text.setStyleSheet(get_log_text_style())
        log_layout.addWidget(self.log_text)
        content_layout.addWidget(self.log_frame)

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

        # Branding
        brand_label = QtWidgets.QLabel("CommandCore Suite", status_frame)
        brand_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            background: transparent;
        """)
        status_layout.addWidget(brand_label)

        main_layout.addWidget(status_frame)

    def log_message(self, message):
        """Add a message to the log console with timestamp"""
        logging.info(f"[AndroidTools] {message}")

        if self.log_text is not None:
            try:
                timestamp = time.strftime('%H:%M:%S')
                # Add colored timestamp
                formatted_msg = f'<span style="color: {COLORS["accent_primary"]};">[{timestamp}]</span> <span style="color: {COLORS["text_primary"]};">{message}</span>'
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
