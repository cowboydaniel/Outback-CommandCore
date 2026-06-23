"""Device info tab layout for DROIDCOM."""

from PySide6 import QtCore, QtWidgets

from ..ui.components.listbox import ListBox
from ..ui.styles import (
    EMOJI_ICONS,
    COLORS,
    get_action_button_style,
    get_primary_button_style,
    get_secondary_button_style,
    get_label_style,
    get_log_text_style,
)
from ..ui.icon_utils import create_icon_label
from ..ui.styles import (
    get_subheader_style,
    get_value_style,
    get_value_style_for,
)


def create_device_info_tab(ui):
    """Create the Device Info tab with modern styling and scrollable content."""
    # Create main container widget and layout
    ui.device_frame = QtWidgets.QWidget(ui.notebook)
    main_layout = QtWidgets.QVBoxLayout(ui.device_frame)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Create scroll area
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

    # Create content widget and layout
    content_widget = QtWidgets.QWidget()
    device_layout = QtWidgets.QVBoxLayout(content_widget)
    device_layout.setContentsMargins(8, 8, 8, 8)
    device_layout.setSpacing(10)

    # Set up the scroll area
    scroll_area.setWidget(content_widget)
    main_layout.addWidget(scroll_area)

    # Add the tab to the notebook
    ui.notebook.addTab(ui.device_frame, "Device Info")

    # === CONNECTION SECTION ===
    connection_frame = QtWidgets.QGroupBox("Device Connection", ui.device_frame)
    connection_layout = QtWidgets.QVBoxLayout(connection_frame)
    connection_layout.setSpacing(8)
    connection_layout.setContentsMargins(14, 20, 14, 12)
    device_layout.addWidget(connection_frame)

    # Connection buttons
    conn_buttons_frame = QtWidgets.QWidget(connection_frame)
    conn_buttons_layout = QtWidgets.QHBoxLayout(conn_buttons_frame)
    conn_buttons_layout.setContentsMargins(0, 0, 0, 0)
    conn_buttons_layout.setSpacing(10)

    secondary_style = get_secondary_button_style()

    # "Connect Device" is the primary call-to-action: accent colour, slightly larger.
    ui.connect_btn = QtWidgets.QPushButton("Connect Device", conn_buttons_frame)
    ui.connect_btn.setStyleSheet(get_primary_button_style())
    ui.connect_btn.clicked.connect(ui.connect_device)
    ui.connect_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.connect_btn.setMinimumWidth(190)
    icon_widget = create_icon_label(EMOJI_ICONS['connect'], size=18)
    btn_layout = QtWidgets.QHBoxLayout(ui.connect_btn)
    btn_layout.addWidget(icon_widget)
    btn_layout.addStretch()
    btn_layout.setSpacing(8)
    btn_layout.setContentsMargins(14, 0, 14, 0)
    conn_buttons_layout.addWidget(ui.connect_btn)

    # WiFi ADB / Refresh / Remove Offline are secondary actions.
    ui.wifi_adb_btn = QtWidgets.QPushButton("WiFi ADB", conn_buttons_frame)
    ui.wifi_adb_btn.setStyleSheet(secondary_style)
    ui.wifi_adb_btn.clicked.connect(ui.setup_wifi_adb)
    ui.wifi_adb_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.wifi_adb_btn.setMinimumWidth(140)
    icon_widget = create_icon_label(EMOJI_ICONS['wifi'], size=14)
    btn_layout = QtWidgets.QHBoxLayout(ui.wifi_adb_btn)
    btn_layout.addWidget(icon_widget)
    btn_layout.addStretch()
    btn_layout.setSpacing(8)
    btn_layout.setContentsMargins(12, 0, 12, 0)
    conn_buttons_layout.addWidget(ui.wifi_adb_btn)

    ui.refresh_btn = QtWidgets.QPushButton("Refresh", conn_buttons_frame)
    ui.refresh_btn.setStyleSheet(secondary_style)
    ui.refresh_btn.clicked.connect(ui.refresh_device_list)
    ui.refresh_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.refresh_btn.setMinimumWidth(130)
    icon_widget = create_icon_label(EMOJI_ICONS['refresh'], size=14)
    btn_layout = QtWidgets.QHBoxLayout(ui.refresh_btn)
    btn_layout.addWidget(icon_widget)
    btn_layout.addStretch()
    btn_layout.setSpacing(8)
    btn_layout.setContentsMargins(12, 0, 12, 0)
    conn_buttons_layout.addWidget(ui.refresh_btn)

    ui.remove_offline_btn = QtWidgets.QPushButton("Remove Offline", conn_buttons_frame)
    ui.remove_offline_btn.setStyleSheet(secondary_style)
    ui.remove_offline_btn.clicked.connect(ui.remove_offline_devices)
    ui.remove_offline_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.remove_offline_btn.setMinimumWidth(150)
    icon_widget = create_icon_label(EMOJI_ICONS['remove'], size=14)
    btn_layout = QtWidgets.QHBoxLayout(ui.remove_offline_btn)
    btn_layout.addWidget(icon_widget)
    btn_layout.addStretch()
    btn_layout.setSpacing(8)
    btn_layout.setContentsMargins(12, 0, 12, 0)
    conn_buttons_layout.addWidget(ui.remove_offline_btn)

    conn_buttons_layout.addStretch()
    connection_layout.addWidget(conn_buttons_frame)

    # Device list
    list_frame = QtWidgets.QWidget(connection_frame)
    list_layout = QtWidgets.QVBoxLayout(list_frame)
    list_layout.setContentsMargins(0, 0, 0, 0)
    list_layout.setSpacing(8)

    list_label = QtWidgets.QLabel("Available Devices", list_frame)
    list_label.setStyleSheet(get_subheader_style())
    list_layout.addWidget(list_label)

    ui.device_listbox = ListBox(list_frame)
    ui.device_listbox.setMinimumHeight(90)
    ui.device_listbox.setMaximumHeight(120)
    ui.device_listbox.show_placeholder("No devices connected — enable USB debugging and connect via USB")
    list_layout.addWidget(ui.device_listbox)

    connection_layout.addWidget(list_frame)

    # === ONBOARDING / GETTING STARTED PANEL (shown until a device connects) ===
    create_onboarding_panel(ui, device_layout)

    # === DEVICE INFO SECTION ===
    create_device_info_display(ui, device_layout)

    # === DEVICE ACTIONS SECTION ===
    create_device_actions(ui, device_layout)


def create_onboarding_panel(ui, parent_layout):
    """Create a step-by-step getting-started panel shown when no device is connected."""
    ui.onboarding_frame = QtWidgets.QGroupBox("Getting Started", ui.device_frame)
    onboarding_layout = QtWidgets.QVBoxLayout(ui.onboarding_frame)
    onboarding_layout.setContentsMargins(14, 20, 14, 12)
    onboarding_layout.setSpacing(4)
    parent_layout.addWidget(ui.onboarding_frame)

    steps = [
        "1. Enable Developer Options on the Android device",
        "2. Enable USB Debugging in Developer Options",
        "3. Connect the device via USB",
        "4. Accept the RSA key fingerprint prompt on the device",
    ]
    for step in steps:
        step_label = QtWidgets.QLabel(step, ui.onboarding_frame)
        step_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 13px;
            padding: 2px 0;
        """)
        onboarding_layout.addWidget(step_label)


def create_device_info_display(ui, parent_layout):
    """Create the device information display section."""
    device_info_frame = QtWidgets.QGroupBox("Device Information", ui.device_frame)
    device_info_layout = QtWidgets.QVBoxLayout(device_info_frame)
    device_info_layout.setContentsMargins(14, 20, 14, 12)
    parent_layout.addWidget(device_info_frame, 1)

    # Info content with grid layout
    info_content = QtWidgets.QWidget(device_info_frame)
    info_layout = QtWidgets.QGridLayout(info_content)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setHorizontalSpacing(16)
    info_layout.setVerticalSpacing(8)
    device_info_layout.addWidget(info_content)

    # Basic device info fields (left column)
    ui.info_fields = {
        "Model": QtWidgets.QLabel("N/A", info_content),
        "Manufacturer": QtWidgets.QLabel("N/A", info_content),
        "Android Version": QtWidgets.QLabel("N/A", info_content),
        "Serial Number": QtWidgets.QLabel("N/A", info_content),
        "IMEI": QtWidgets.QLabel("N/A", info_content),
        "Build Number": QtWidgets.QLabel("N/A", info_content),
        "Battery Level": QtWidgets.QLabel("N/A", info_content),
    }

    # Advanced device info fields (right column)
    ui.adv_info_fields = {
        "Storage": QtWidgets.QLabel("N/A", info_content),
        "RAM": QtWidgets.QLabel("N/A", info_content),
        "Screen Resolution": QtWidgets.QLabel("N/A", info_content),
        "CPU": QtWidgets.QLabel("N/A", info_content),
        "Kernel": QtWidgets.QLabel("N/A", info_content),
        "Security Patch Level": QtWidgets.QLabel("N/A", info_content),
        "Bootloader Status": QtWidgets.QLabel("N/A", info_content),
    }

    # Set column widths
    info_layout.setColumnMinimumWidth(0, 140)
    info_layout.setColumnMinimumWidth(1, 180)
    info_layout.setColumnMinimumWidth(2, 140)
    info_layout.setColumnMinimumWidth(3, 180)

    # Section headers
    basic_heading = QtWidgets.QLabel("Basic Information", info_content)
    basic_heading.setStyleSheet(get_subheader_style())
    info_layout.addWidget(basic_heading, 0, 0, 1, 2, QtCore.Qt.AlignLeft)

    advanced_heading = QtWidgets.QLabel("Advanced Information", info_content)
    advanced_heading.setStyleSheet(get_subheader_style())
    info_layout.addWidget(advanced_heading, 0, 2, 1, 2, QtCore.Qt.AlignLeft)

    # Add info fields with modern styling
    row = 1
    label_style = get_label_style()

    for label_text, value_label in ui.info_fields.items():
        label = QtWidgets.QLabel(f"{label_text}:", info_content)
        label.setStyleSheet(label_style)
        value_label.setStyleSheet(get_value_style_for(value_label.text()))
        info_layout.addWidget(label, row, 0, QtCore.Qt.AlignLeft)
        info_layout.addWidget(value_label, row, 1, QtCore.Qt.AlignLeft)
        row += 1

    row = 1
    for label_text, value_label in ui.adv_info_fields.items():
        label = QtWidgets.QLabel(f"{label_text}:", info_content)
        label.setStyleSheet(label_style)
        value_label.setStyleSheet(get_value_style_for(value_label.text()))
        info_layout.addWidget(label, row, 2, QtCore.Qt.AlignLeft)
        info_layout.addWidget(value_label, row, 3, QtCore.Qt.AlignLeft)
        row += 1

    # Debug information section
    max_rows = max(len(ui.info_fields), len(ui.adv_info_fields)) + 2
    debug_heading = QtWidgets.QLabel("Debug Information", info_content)
    debug_heading.setStyleSheet(get_subheader_style())
    info_layout.addWidget(debug_heading, max_rows, 0, 1, 4, QtCore.Qt.AlignLeft)

    debug_frame = QtWidgets.QWidget(info_content)
    debug_layout = QtWidgets.QVBoxLayout(debug_frame)
    debug_layout.setContentsMargins(0, 0, 0, 0)
    ui.debug_text = QtWidgets.QTextEdit(debug_frame)
    ui.debug_text.setReadOnly(True)
    ui.debug_text.setPlaceholderText("Connect a device to view debug output")
    ui.debug_text.setMinimumHeight(80)
    ui.debug_text.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
    ui.debug_text.setStyleSheet(get_log_text_style())
    debug_layout.addWidget(ui.debug_text)
    info_layout.addWidget(debug_frame, max_rows + 1, 0, 1, 4)


def create_device_actions(ui, parent_layout):
    """Create the device actions section."""
    actions_frame = QtWidgets.QGroupBox("Quick Actions", ui.device_frame)
    actions_layout = QtWidgets.QGridLayout(actions_frame)
    actions_layout.setHorizontalSpacing(10)
    actions_layout.setVerticalSpacing(8)
    actions_layout.setContentsMargins(14, 20, 14, 12)
    parent_layout.addWidget(actions_frame)

    action_btn_style = get_action_button_style()
    teal = COLORS['accent_primary']
    connect_tip = "Connect a device to use this feature"

    def _add_action_button(text, callback, icon_key, row, col):
        btn = QtWidgets.QPushButton(text, actions_frame)
        btn.setStyleSheet(action_btn_style)
        btn.clicked.connect(callback)
        btn.setEnabled(False)
        btn.setToolTip(connect_tip)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        icon_widget = create_icon_label(EMOJI_ICONS[icon_key], size=16, color=teal)
        btn_layout = QtWidgets.QHBoxLayout(btn)
        btn_layout.addWidget(icon_widget)
        btn_layout.addStretch()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(12, 0, 12, 0)
        actions_layout.addWidget(btn, row, col)
        return btn

    # Row 1
    ui.screenshot_btn = _add_action_button("Screenshot", ui.take_screenshot, 'screenshot', 0, 0)
    ui.backup_btn = _add_action_button("Backup", ui.backup_device, 'backup', 0, 1)
    ui.files_btn = _add_action_button("Files", ui.manage_files, 'files', 0, 2)

    # Divider between the two rows of Quick Actions buttons
    divider = QtWidgets.QFrame(actions_frame)
    divider.setFrameShape(QtWidgets.QFrame.HLine)
    divider.setStyleSheet(f"background-color: {COLORS['surface_border']}; max-height: 1px; border: none;")
    actions_layout.addWidget(divider, 1, 0, 1, 3)

    # Row 2
    ui.install_apk_btn = _add_action_button("Install APK", ui.install_apk, 'install', 2, 0)
    ui.app_manager_btn = _add_action_button("App Manager", ui.app_manager, 'apps', 2, 1)
    ui.logcat_btn = _add_action_button("Logcat", ui.view_logcat, 'log', 2, 2)
