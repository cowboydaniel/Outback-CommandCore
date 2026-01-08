"""Device info tab layout for DROIDCOM."""

from PySide6 import QtCore, QtWidgets

from ..ui.components.listbox import ListBox
from ..ui.styles import (
    EMOJI_ICONS,
    get_action_button_style,
    get_label_style,
    get_log_text_style,
    get_subheader_style,
    get_value_style,
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
    device_layout.setContentsMargins(12, 12, 12, 12)
    device_layout.setSpacing(14)

    # Set up the scroll area
    scroll_area.setWidget(content_widget)
    main_layout.addWidget(scroll_area)

    # Add the tab to the notebook
    ui.notebook.addTab(ui.device_frame, "📱 Device Info")

    # === CONNECTION SECTION ===
    connection_frame = QtWidgets.QGroupBox("Device Connection", ui.device_frame)
    connection_layout = QtWidgets.QVBoxLayout(connection_frame)
    connection_layout.setSpacing(12)
    connection_layout.setContentsMargins(16, 24, 16, 16)
    device_layout.addWidget(connection_frame)

    # Connection buttons
    conn_buttons_frame = QtWidgets.QWidget(connection_frame)
    conn_buttons_layout = QtWidgets.QHBoxLayout(conn_buttons_frame)
    conn_buttons_layout.setContentsMargins(0, 0, 0, 0)
    conn_buttons_layout.setSpacing(10)

    button_style = get_action_button_style()

    ui.connect_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['connect']} Connect Device", conn_buttons_frame)
    ui.connect_btn.setStyleSheet(button_style)
    ui.connect_btn.clicked.connect(ui.connect_device)
    ui.connect_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.connect_btn.setMinimumWidth(170)
    conn_buttons_layout.addWidget(ui.connect_btn)

    ui.wifi_adb_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['wifi']} WiFi ADB", conn_buttons_frame)
    ui.wifi_adb_btn.setStyleSheet(button_style)
    ui.wifi_adb_btn.clicked.connect(ui.setup_wifi_adb)
    ui.wifi_adb_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.wifi_adb_btn.setMinimumWidth(150)
    conn_buttons_layout.addWidget(ui.wifi_adb_btn)

    ui.refresh_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['refresh']} Refresh", conn_buttons_frame)
    ui.refresh_btn.setStyleSheet(button_style)
    ui.refresh_btn.clicked.connect(ui.refresh_device_list)
    ui.refresh_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.refresh_btn.setMinimumWidth(140)
    conn_buttons_layout.addWidget(ui.refresh_btn)

    ui.remove_offline_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['remove']} Remove Offline", conn_buttons_frame)
    ui.remove_offline_btn.setStyleSheet(button_style)
    ui.remove_offline_btn.clicked.connect(ui.remove_offline_devices)
    ui.remove_offline_btn.setCursor(QtCore.Qt.PointingHandCursor)
    ui.remove_offline_btn.setMinimumWidth(160)
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
    list_layout.addWidget(ui.device_listbox)

    connection_layout.addWidget(list_frame)

    # === DEVICE INFO SECTION ===
    create_device_info_display(ui, device_layout)

    # === DEVICE ACTIONS SECTION ===
    create_device_actions(ui, device_layout)


def create_device_info_display(ui, parent_layout):
    """Create the device information display section."""
    device_info_frame = QtWidgets.QGroupBox("Device Information", ui.device_frame)
    device_info_layout = QtWidgets.QVBoxLayout(device_info_frame)
    device_info_layout.setContentsMargins(16, 24, 16, 16)
    parent_layout.addWidget(device_info_frame, 1)

    # Info content with grid layout
    info_content = QtWidgets.QWidget(device_info_frame)
    info_layout = QtWidgets.QGridLayout(info_content)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setHorizontalSpacing(20)
    info_layout.setVerticalSpacing(12)
    device_info_layout.addWidget(info_content)

    # Basic device info fields (left column)
    ui.info_fields = {
        "Model": QtWidgets.QLabel("N/A", info_content),
        "Manufacturer": QtWidgets.QLabel("N/A", info_content),
        "Android Version": QtWidgets.QLabel("N/A", info_content),
        "Serial Number": QtWidgets.QLabel("N/A", info_content),
        "IMEI": QtWidgets.QLabel("N/A", info_content),
        "Battery Level": QtWidgets.QLabel("N/A", info_content),
    }

    # Advanced device info fields (right column)
    ui.adv_info_fields = {
        "Storage": QtWidgets.QLabel("N/A", info_content),
        "RAM": QtWidgets.QLabel("N/A", info_content),
        "Screen Resolution": QtWidgets.QLabel("N/A", info_content),
        "CPU": QtWidgets.QLabel("N/A", info_content),
        "Kernel": QtWidgets.QLabel("N/A", info_content),
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
    value_style = get_value_style()

    for label_text, value_label in ui.info_fields.items():
        label = QtWidgets.QLabel(f"{label_text}:", info_content)
        label.setStyleSheet(label_style)
        value_label.setStyleSheet(value_style)
        info_layout.addWidget(label, row, 0, QtCore.Qt.AlignLeft)
        info_layout.addWidget(value_label, row, 1, QtCore.Qt.AlignLeft)
        row += 1

    row = 1
    for label_text, value_label in ui.adv_info_fields.items():
        label = QtWidgets.QLabel(f"{label_text}:", info_content)
        label.setStyleSheet(label_style)
        value_label.setStyleSheet(value_style)
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
    ui.debug_text.setMinimumHeight(100)
    ui.debug_text.setMaximumHeight(140)
    ui.debug_text.setStyleSheet(get_log_text_style())
    debug_layout.addWidget(ui.debug_text)
    info_layout.addWidget(debug_frame, max_rows + 1, 0, 1, 4)


def create_device_actions(ui, parent_layout):
    """Create the device actions section."""
    actions_frame = QtWidgets.QGroupBox("Quick Actions", ui.device_frame)
    actions_layout = QtWidgets.QGridLayout(actions_frame)
    actions_layout.setHorizontalSpacing(12)
    actions_layout.setVerticalSpacing(12)
    actions_layout.setContentsMargins(16, 24, 16, 16)
    parent_layout.addWidget(actions_frame)

    action_btn_style = get_action_button_style()

    # Row 1
    ui.screenshot_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['screenshot']} Screenshot", actions_frame)
    ui.screenshot_btn.setStyleSheet(action_btn_style)
    ui.screenshot_btn.clicked.connect(ui.take_screenshot)
    ui.screenshot_btn.setEnabled(False)
    ui.screenshot_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.screenshot_btn, 0, 0)

    ui.backup_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['backup']} Backup", actions_frame)
    ui.backup_btn.setStyleSheet(action_btn_style)
    ui.backup_btn.clicked.connect(ui.backup_device)
    ui.backup_btn.setEnabled(False)
    ui.backup_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.backup_btn, 0, 1)

    ui.files_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['files']} Files", actions_frame)
    ui.files_btn.setStyleSheet(action_btn_style)
    ui.files_btn.clicked.connect(ui.manage_files)
    ui.files_btn.setEnabled(False)
    ui.files_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.files_btn, 0, 2)

    # Row 2
    ui.install_apk_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['install']} Install APK", actions_frame)
    ui.install_apk_btn.setStyleSheet(action_btn_style)
    ui.install_apk_btn.clicked.connect(ui.install_apk)
    ui.install_apk_btn.setEnabled(False)
    ui.install_apk_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.install_apk_btn, 1, 0)

    ui.app_manager_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['apps']} App Manager", actions_frame)
    ui.app_manager_btn.setStyleSheet(action_btn_style)
    ui.app_manager_btn.clicked.connect(ui.app_manager)
    ui.app_manager_btn.setEnabled(False)
    ui.app_manager_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.app_manager_btn, 1, 1)

    ui.logcat_btn = QtWidgets.QPushButton(f"{EMOJI_ICONS['log']} Logcat", actions_frame)
    ui.logcat_btn.setStyleSheet(action_btn_style)
    ui.logcat_btn.clicked.connect(ui.view_logcat)
    ui.logcat_btn.setEnabled(False)
    ui.logcat_btn.setCursor(QtCore.Qt.PointingHandCursor)
    actions_layout.addWidget(ui.logcat_btn, 1, 2)
