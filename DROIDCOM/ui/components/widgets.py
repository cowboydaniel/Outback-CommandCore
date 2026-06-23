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
from ..icon_utils import get_status_icon, create_icon_label, load_svg_pixmap
from ..styles import (
    get_main_stylesheet,
    get_card_button_style,
    get_action_button_style,
    get_secondary_button_style,
    get_primary_button_style,
    get_log_text_style,
    get_value_style_for,
    get_value_style,
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
        split_layout.setContentsMargins(12, 12, 12, 12)
        split_layout.setSpacing(12)

        # === LEFT PANEL ===
        left_panel = QtWidgets.QWidget(main_container)
        content_layout = QtWidgets.QVBoxLayout(left_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
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
        header_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
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
        header_layout.setContentsMargins(14, 8, 14, 8)
        header_layout.setSpacing(8)

        # Left side - Icon and Title
        title_container = QtWidgets.QWidget(header_frame)
        title_layout = QtWidgets.QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        # Android Robot Icon (using SVG)
        icon_label = create_icon_label('android-robot', size=28)
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_label.setFrameShape(QtWidgets.QFrame.NoFrame)
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
            border: none;
            letter-spacing: 1px;
        """)
        header_label.setFrameShape(QtWidgets.QFrame.NoFrame)
        header_label.setWordWrap(False)
        text_layout.addWidget(header_label)

        subtitle_label = QtWidgets.QLabel("Android Device Management & Control", text_container)
        subtitle_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {COLORS['text_secondary']};
            background: transparent;
            border: none;
        """)
        subtitle_label.setFrameShape(QtWidgets.QFrame.NoFrame)
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

        # Forensic Mode toggle - same icon-above/label-below component as
        # Settings/Help for visual consistency; shield icon, turns red when active.
        self.forensic_mode_btn, self.forensic_mode_icon, self.forensic_mode_label = \
            self._create_icon_text_header_button(
                header_frame, "shield", "Forensic",
                "Forensic Mode - click to toggle", self.toggle_forensic_mode,
                checkable=True, return_widgets=True,
            )
        header_layout.addWidget(self.forensic_mode_btn)

        # Settings button - icon with a visible text label beneath it
        settings_btn = self._create_icon_text_header_button(
            header_frame, EMOJI_ICONS['settings'], "Settings",
            "Settings / Preferences", self.open_settings_dialog
        )
        header_layout.addWidget(settings_btn)

        # Help button - icon with a visible text label beneath it
        help_btn = self._create_icon_text_header_button(
            header_frame, EMOJI_ICONS.get('help', 'file'), "Help",
            "Help / Documentation", self.open_help_dialog
        )
        header_layout.addWidget(help_btn)

        # Connection status pill with a coloured status dot
        self.connection_indicator = QtWidgets.QLabel(header_frame)
        self.connection_indicator.setTextFormat(QtCore.Qt.RichText)
        header_layout.addWidget(self.connection_indicator)
        self.set_connection_indicator(connected=False)

        content_layout.addWidget(header_frame)

    def _create_icon_text_header_button(self, parent, icon_name, label_text, tooltip, callback,
                                         checkable=False, return_widgets=False):
        """A small header button: icon on top, a visible text label beneath it.

        Used for Settings, Help, and Forensic Mode so all three header
        buttons share identical sizing/styling.
        """
        container = QtWidgets.QPushButton(parent)
        container.setToolTip(tooltip)
        container.setCheckable(checkable)
        container.setStyleSheet(self._flat_header_button_style())
        container.setCursor(QtCore.Qt.PointingHandCursor)
        container.setFixedSize(70, 60)
        container.clicked.connect(callback)

        btn_layout = QtWidgets.QVBoxLayout(container)
        btn_layout.setContentsMargins(4, 8, 4, 6)
        btn_layout.setSpacing(4)
        btn_layout.setAlignment(QtCore.Qt.AlignCenter)

        icon_widget = create_icon_label(icon_name, size=18)
        icon_widget.setFixedSize(18, 18)
        icon_widget.setAlignment(QtCore.Qt.AlignCenter)
        btn_layout.addWidget(icon_widget, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel(label_text, container)
        label.setStyleSheet(f"""
            font-size: 9px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setWordWrap(True)
        btn_layout.addWidget(label, 0, QtCore.Qt.AlignCenter)

        if return_widgets:
            return container, icon_widget, label
        return container

    def _flat_header_button_style(self):
        """No visible box in the default state -- just a subtle hover background.

        Shared by the Settings, Help, and (when inactive) Forensic Mode
        header buttons so none of them show a bounding box against the
        header.
        """
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['background_hover']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['background_hover']};
            }}
        """

    def _forensic_button_style(self, active):
        """Flat/borderless when inactive; unmistakeable red/glow when active.

        Matches the fixed 70x60 icon-above/label-below layout shared with
        the Settings and Help header buttons.
        """
        if not active:
            return self._flat_header_button_style()
        return f"""
            QPushButton {{
                background-color: {COLORS['error_bg']};
                border: 2px solid {COLORS['error']};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                border-color: white;
            }}
        """

    def set_connection_indicator(self, connected, device_name=None):
        """Update the persistent connection status pill, including its status dot."""
        if not hasattr(self, 'connection_indicator'):
            return
        if connected:
            dot_color = COLORS['success']
            text = f"Connected — {device_name}" if device_name else "Connected"
            bg = COLORS['success_bg']
            text_color = "white"
        else:
            dot_color = COLORS['error']
            text = "Disconnected"
            bg = COLORS['background_hover']
            text_color = COLORS['text_secondary']

        self.connection_indicator.setText(
            f'<span style="color:{dot_color};">●</span> '
            f'<span style="color:{text_color};">{text}</span>'
        )
        self.connection_indicator.setStyleSheet(f"""
            background-color: {bg};
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
            self.forensic_mode_btn.setStyleSheet(self._forensic_button_style(active=True))
            self.forensic_mode_icon.setPixmap(load_svg_pixmap('warning', 16))
            self.forensic_mode_label.setText("FORENSIC\nMODE ACTIVE")
            self.forensic_mode_label.setStyleSheet("""
                font-size: 8px;
                font-weight: 700;
                color: white;
                background: transparent;
            """)
            self.log_message("Forensic Mode enabled - write operations disabled", level="warning")
        else:
            self.forensic_mode = False
            self.forensic_indicator.setVisible(False)
            self.forensic_mode_btn.setStyleSheet(self._forensic_button_style(active=False))
            self.forensic_mode_icon.setPixmap(load_svg_pixmap('shield', 16))
            self.forensic_mode_label.setText("Forensic")
            self.forensic_mode_label.setStyleSheet(f"""
                font-size: 9px;
                font-weight: 600;
                color: {COLORS['text_secondary']};
                background: transparent;
            """)
            self.log_message("Forensic Mode disabled", level="info")
        if hasattr(self, "update_forensic_lock_state"):
            self.update_forensic_lock_state()

    def open_settings_dialog(self):
        """Show a custom-styled (frameless, dark-themed) settings dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 12px;
            }}
        """)

        outer_layout = QtWidgets.QVBoxLayout(dialog)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # --- Custom dark title bar (the dialog is frameless, so the native
        # OS title bar -- which renders light/white regardless of our
        # stylesheet -- never appears) ---
        title_bar = QtWidgets.QFrame(dialog)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_dark']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        title_bar.setFixedHeight(40)
        title_bar_layout = QtWidgets.QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(14, 0, 10, 0)

        title_label = QtWidgets.QLabel("Settings", title_bar)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        close_btn = QtWidgets.QPushButton("✕", title_bar)
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
                border-radius: 13px;
            }}
        """)
        close_btn.clicked.connect(dialog.reject)
        title_bar_layout.addWidget(close_btn)

        outer_layout.addWidget(title_bar)

        # Allow dragging the frameless dialog by its custom title bar.
        def _title_mouse_press(event):
            dialog._drag_pos = event.globalPosition().toPoint() - dialog.frameGeometry().topLeft()

        def _title_mouse_move(event):
            if hasattr(dialog, '_drag_pos') and event.buttons() & QtCore.Qt.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog._drag_pos)

        title_bar.mousePressEvent = _title_mouse_press
        title_bar.mouseMoveEvent = _title_mouse_move

        # --- Content ---
        content = QtWidgets.QWidget(dialog)
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(14)
        outer_layout.addWidget(content)

        # Theme selector
        theme_label = QtWidgets.QLabel("Theme", content)
        theme_label.setStyleSheet(get_subheader_style())
        content_layout.addWidget(theme_label)

        theme_row = QtWidgets.QHBoxLayout()
        theme_combo = QtWidgets.QComboBox(content)
        theme_combo.addItem("Dark (default)")
        theme_combo.setEnabled(False)
        theme_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
        """)
        theme_row.addWidget(theme_combo)
        theme_row.addStretch()
        content_layout.addLayout(theme_row)

        # Console font size
        font_label = QtWidgets.QLabel("Console Font Size", content)
        font_label.setStyleSheet(get_subheader_style())
        content_layout.addWidget(font_label)

        font_size_row = QtWidgets.QHBoxLayout()
        font_size_group = QtWidgets.QButtonGroup(dialog)
        current_font_size = getattr(self, 'console_font_size', 'medium')
        for key, text in (("small", "Small"), ("medium", "Medium"), ("large", "Large")):
            radio = QtWidgets.QRadioButton(text, content)
            radio.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            if key == current_font_size:
                radio.setChecked(True)
            font_size_group.addButton(radio)
            font_size_row.addWidget(radio)
            radio.toggled.connect(lambda checked, k=key: self._set_console_font_size(k) if checked else None)
        font_size_row.addStretch()
        content_layout.addLayout(font_size_row)

        # Auto-connect on startup
        auto_connect_check = QtWidgets.QCheckBox("Auto-connect on startup", content)
        auto_connect_check.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        auto_connect_check.setChecked(getattr(self, 'auto_connect_on_startup', True))
        auto_connect_check.toggled.connect(lambda checked: setattr(self, 'auto_connect_on_startup', checked))
        content_layout.addWidget(auto_connect_check)

        # Default case export directory
        export_label = QtWidgets.QLabel("Default Case Export Directory", content)
        export_label.setStyleSheet(get_subheader_style())
        content_layout.addWidget(export_label)

        export_row = QtWidgets.QHBoxLayout()
        export_path_edit = QtWidgets.QLineEdit(content)
        export_path_edit.setText(getattr(self, 'default_export_dir', '') or '')
        export_path_edit.setPlaceholderText("No directory selected")
        export_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['surface_border']};
                border-radius: 6px;
                padding: 6px 10px;
            }}
        """)
        export_row.addWidget(export_path_edit)

        def _browse_export_dir():
            chosen = QtWidgets.QFileDialog.getExistingDirectory(
                dialog, "Select Default Case Export Directory", export_path_edit.text()
            )
            if chosen:
                export_path_edit.setText(chosen)
                self.default_export_dir = chosen

        browse_btn = QtWidgets.QPushButton("Browse...", content)
        browse_btn.setIcon(QtGui.QIcon())
        browse_btn.setStyleSheet(get_secondary_button_style())
        browse_btn.setCursor(QtCore.Qt.PointingHandCursor)
        browse_btn.clicked.connect(_browse_export_dir)
        export_row.addWidget(browse_btn)
        content_layout.addLayout(export_row)

        # Divider
        divider = QtWidgets.QFrame(content)
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['surface_border']}; max-height: 1px; border: none;")
        content_layout.addWidget(divider)

        # About section
        about_label = QtWidgets.QLabel("About", content)
        about_label.setStyleSheet(get_subheader_style())
        content_layout.addWidget(about_label)

        about_text = QtWidgets.QLabel(
            f"DROIDCOM v{APP_VERSION}\n"
            f"Part of the CommandCore Suite\n"
            f"by Outback Electronics",
            content,
        )
        about_text.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        content_layout.addWidget(about_text)

        # OK button -- text only, no icon, styled like other secondary buttons.
        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()
        ok_btn = QtWidgets.QPushButton("OK", content)
        ok_btn.setIcon(QtGui.QIcon())
        ok_btn.setStyleSheet(get_secondary_button_style())
        ok_btn.setCursor(QtCore.Qt.PointingHandCursor)
        ok_btn.setMinimumWidth(90)
        ok_btn.clicked.connect(dialog.accept)
        button_row.addWidget(ok_btn)
        content_layout.addLayout(button_row)

        dialog.exec()

    CONSOLE_FONT_SIZES_PX = {"small": 10, "medium": 12, "large": 15}

    def apply_console_font_size(self, size):
        """Apply the given console font size ('small'/'medium'/'large') to the log console."""
        font_px = self.CONSOLE_FONT_SIZES_PX.get(size, self.CONSOLE_FONT_SIZES_PX["medium"])
        if hasattr(self, 'log_text') and self.log_text is not None:
            self.log_text.setStyleSheet(get_log_text_style(font_px))

    def _set_console_font_size(self, size):
        """Store and immediately apply the selected console font size preference."""
        self.console_font_size = size
        self.apply_console_font_size(size)

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

        ``self.platform_tools_installed`` is only known for certain *after*
        ``app/module.py`` finishes its post-construction detection (it is a
        placeholder ``False`` while ``create_widgets`` runs). The frame is
        therefore built empty here and fully populated by
        ``refresh_tools_status()``, which module.py calls once detection is
        complete -- and which can also be re-called any time the install
        state changes (e.g. after Install/Reinstall finishes).
        """
        self.setup_status_frame = QtWidgets.QFrame(parent)
        self.setup_status_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setup_status_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        content_layout.addWidget(self.setup_status_frame)
        self.refresh_tools_status()

    def refresh_tools_status(self):
        """(Re)build the platform-tools status bar from the current
        ``self.platform_tools_installed`` value.

        Rebuilding (rather than just relabeling) is the fix for the
        Install button reappearing: previously only ``tools_label.setText``
        was updated after detection, so the Install button -- added while
        the flag was still the placeholder ``False`` -- was never removed.
        """
        old_layout = self.setup_status_frame.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)  # detach so a fresh layout can be set

        setup_layout = QtWidgets.QHBoxLayout(self.setup_status_frame)
        setup_layout.setContentsMargins(12, 7, 12, 7)
        setup_layout.setSpacing(10)

        installed = self.platform_tools_installed
        self.log_message(
            f"Platform tools status check: {'INSTALLED' if installed else 'NOT INSTALLED'} "
            f"(adb_path={getattr(self, 'adb_path', None)}) - "
            f"{'hiding Install button, showing green checkmark' if installed else 'showing Install button'}",
            level="info",
        )

        # Status icon - green checkmark when installed, otherwise nothing alarming
        if installed:
            icon_label = create_icon_label('success', size=14)
            icon_label.setStyleSheet("background: transparent;")
            setup_layout.addWidget(icon_label)

        # Status text - fully green when installed, neutral otherwise
        if installed:
            self.tools_label = QtWidgets.QLabel(
                "Android Platform Tools: Installed", self.setup_status_frame
            )
            self.tools_label.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {COLORS['success']};
                background: transparent;
            """)
        else:
            self.tools_label = QtWidgets.QLabel(
                f"Android Platform Tools: <span style='color: {COLORS['text_secondary']}; font-weight: 600;'>Not Installed</span>",
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

        if not installed:
            tools_btn = QtWidgets.QPushButton("Install Platform Tools", self.setup_status_frame)
            tools_btn.setStyleSheet(get_primary_button_style())
            tools_btn.clicked.connect(self.install_platform_tools)
            tools_btn.setCursor(QtCore.Qt.PointingHandCursor)
            setup_layout.addWidget(tools_btn)
        else:
            reinstall_link = QtWidgets.QPushButton("Reinstall", self.setup_status_frame)
            reinstall_link.setFlat(True)
            reinstall_link.setCursor(QtCore.Qt.PointingHandCursor)
            reinstall_link.setStyleSheet(f"""
                QPushButton {{
                    color: {COLORS['text_secondary']};
                    background: transparent;
                    border: none;
                    text-decoration: underline;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    color: {COLORS['text_primary']};
                }}
            """)
            reinstall_link.clicked.connect(self.install_platform_tools)
            setup_layout.addWidget(reinstall_link)

        # Subtle dark-green tint on the whole bar reinforces the confirmed status
        if installed:
            self.setup_status_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['success']}1a;
                    border: 1px solid {COLORS['success']}55;
                    border-radius: 10px;
                }}
            """)
        else:
            self.setup_status_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['surface']};
                    border: 1px solid {COLORS['surface_border']};
                    border-radius: 10px;
                }}
            """)

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
        self.log_frame.setFixedWidth(420)
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
        self.log_text.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.log_text.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.apply_console_font_size(getattr(self, 'console_font_size', 'medium'))
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
        self.screenshot_btn.setToolTip("")
        self.backup_btn.setEnabled(True)
        self.backup_btn.setToolTip("")
        self.files_btn.setEnabled(True)
        self.files_btn.setToolTip("")
        self.app_manager_btn.setEnabled(True)
        self.app_manager_btn.setToolTip("")
        self.logcat_btn.setEnabled(True)
        self.logcat_btn.setToolTip("")
        self.install_apk_btn.setEnabled(True)
        self.install_apk_btn.setToolTip("")
        self.update_forensic_lock_state()

    def disable_device_actions(self):
        """Disable device action buttons when no device is connected"""
        connect_tip = "Connect a device to use this feature"
        for btn in (self.screenshot_btn, self.backup_btn, self.files_btn,
                    self.install_apk_btn, self.app_manager_btn, self.logcat_btn):
            btn.setEnabled(False)
            btn.setToolTip(connect_tip)

    def update_forensic_lock_state(self):
        """In Forensic Mode, disable and visually lock the Install APK action."""
        if not hasattr(self, 'install_apk_btn'):
            return
        if getattr(self, 'forensic_mode', False):
            self.install_apk_btn.setEnabled(False)
            self.install_apk_btn.setToolTip("Disabled in Forensic Mode")
            self.install_apk_btn.setText("\U0001F512 Install APK")
        else:
            self.install_apk_btn.setText("Install APK")
            if self.device_connected:
                self.install_apk_btn.setEnabled(True)
                self.install_apk_btn.setToolTip("")
            else:
                self.install_apk_btn.setEnabled(False)
                self.install_apk_btn.setToolTip("Connect a device to use this feature")

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

    def _apply_value_label_color(self, value_label):
        """Force the value label's text colour directly on the instance.

        Set explicitly (not just via a shared stylesheet string) so nothing
        else in the cascade -- app-level stylesheet, QGroupBox styling, etc
        -- can silently override it.
        """
        text = value_label.text().strip()
        if text.upper() in ("N/A", "UNKNOWN", ""):
            value_label.setStyleSheet(get_value_style_for(text))
            value_label.setProperty("_value_na", True)
        else:
            value_label.setStyleSheet(get_value_style())
            value_label.setProperty("_value_na", False)
        # Belt-and-braces: re-assert directly via QPalette too, in case some
        # other stylesheet application happens after this call.
        palette = value_label.palette()
        color = QtGui.QColor("#6b6b6b" if text.upper() in ("N/A", "UNKNOWN", "") else COLORS['text_primary'])
        palette.setColor(QtGui.QPalette.WindowText, color)
        value_label.setPalette(palette)

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

        if 'bootloader_status' in self.device_info:
            self.adv_info_fields['Bootloader Status'].setText(self.device_info['bootloader_status'])

        for value_label in list(self.info_fields.values()) + list(self.adv_info_fields.values()):
            self._apply_value_label_color(value_label)
