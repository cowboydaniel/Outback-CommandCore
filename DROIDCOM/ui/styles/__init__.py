"""
DROIDCOM - Modern Dark Theme Styles
A sleek, modern dark theme with cyan/teal accents for the Android Tools module.
"""

# Color Palette - Modern Dark Theme with Cyan Accents
COLORS = {
    # Base colors
    'background_dark': '#0a0e14',
    'background': '#0d1117',
    'background_light': '#161b22',
    'background_elevated': '#1c2128',
    'background_hover': '#21262d',

    # Surface colors
    'surface': '#161b22',
    'surface_light': '#1c2128',
    'surface_border': '#30363d',

    # Text colors
    'text_primary': '#e6edf3',
    'text_secondary': '#8b949e',
    'text_muted': '#6e7681',
    'text_disabled': '#484f58',

    # Accent colors - Cyan/Teal theme
    'accent_primary': '#00d4aa',
    'accent_secondary': '#00b894',
    'accent_hover': '#00f5c4',
    'accent_muted': '#00d4aa40',

    # Status colors
    'success': '#3fb950',
    'success_bg': '#238636',
    'warning': '#d29922',
    'warning_bg': '#9e6a03',
    'error': '#f85149',
    'error_bg': '#da3633',
    'info': '#58a6ff',
    'info_bg': '#1f6feb',

    # Android brand colors
    'android_green': '#3ddc84',
    'android_dark': '#073042',

    # Gradients (for reference)
    'gradient_start': '#00d4aa',
    'gradient_end': '#00b4d8',
}


def get_main_stylesheet():
    """Return the main application stylesheet"""
    return f"""
    /* ===== GLOBAL STYLES ===== */
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'SF Pro Display', 'Roboto', sans-serif;
        font-size: 13px;
    }}

    /* ===== MAIN WINDOW ===== */
    QMainWindow {{
        background-color: {COLORS['background_dark']};
    }}

    /* ===== LABELS ===== */
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
        padding: 2px;
    }}

    QLabel[heading="true"] {{
        font-size: 18px;
        font-weight: bold;
        color: {COLORS['accent_primary']};
    }}

    QLabel[subheading="true"] {{
        font-size: 14px;
        font-weight: 600;
        color: {COLORS['text_secondary']};
    }}

    /* ===== PUSH BUTTONS ===== */
    QPushButton {{
        background-color: {COLORS['surface_light']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['background_hover']};
        border-color: {COLORS['accent_primary']};
        color: {COLORS['accent_primary']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['accent_muted']};
        border-color: {COLORS['accent_secondary']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['background_light']};
        color: {COLORS['text_disabled']};
        border-color: {COLORS['background_hover']};
    }}

    QPushButton:focus {{
        outline: none;
        border-color: {COLORS['accent_primary']};
    }}

    /* Primary action buttons */
    QPushButton[primary="true"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_primary']},
            stop:1 {COLORS['accent_secondary']});
        color: {COLORS['background_dark']};
        border: none;
        font-weight: 600;
    }}

    QPushButton[primary="true"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_hover']},
            stop:1 {COLORS['accent_primary']});
        color: {COLORS['background_dark']};
    }}

    /* Danger buttons */
    QPushButton[danger="true"] {{
        background-color: {COLORS['error_bg']};
        color: white;
        border: none;
    }}

    QPushButton[danger="true"]:hover {{
        background-color: {COLORS['error']};
    }}

    /* ===== GROUP BOXES ===== */
    QGroupBox {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 12px;
        margin-top: 20px;
        padding: 20px 15px 15px 15px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        top: 8px;
        padding: 0 10px;
        background-color: {COLORS['surface']};
        color: {COLORS['accent_primary']};
        font-size: 14px;
        font-weight: 600;
    }}

    /* ===== TAB WIDGET ===== */
    QTabWidget::pane {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 12px;
        border-top-left-radius: 0px;
        padding: 10px;
    }}

    QTabBar {{
        background-color: transparent;
    }}

    QTabBar::tab {{
        background-color: {COLORS['background_light']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['surface_border']};
        border-bottom: none;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 12px 24px;
        margin-right: 4px;
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['surface']},
            stop:1 {COLORS['background_light']});
        color: {COLORS['accent_primary']};
        border-color: {COLORS['accent_primary']};
        border-bottom: 2px solid {COLORS['accent_primary']};
        margin-bottom: -2px;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['background_hover']};
        color: {COLORS['text_primary']};
    }}

    /* ===== LIST WIDGET ===== */
    QListWidget {{
        background-color: {COLORS['background_light']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 5px;
        outline: none;
    }}

    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 6px;
        margin: 2px 4px;
    }}

    QListWidget::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_muted']},
            stop:1 transparent);
        color: {COLORS['accent_primary']};
        border-left: 3px solid {COLORS['accent_primary']};
    }}

    QListWidget::item:hover:!selected {{
        background-color: {COLORS['background_hover']};
    }}

    /* ===== TEXT EDIT / LOG ===== */
    QTextEdit {{
        background-color: {COLORS['background_dark']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 10px;
        font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
        font-size: 12px;
        line-height: 1.5;
    }}

    QTextEdit:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* ===== LINE EDIT ===== */
    QLineEdit {{
        background-color: {COLORS['background_light']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        selection-background-color: {COLORS['accent_muted']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['accent_primary']};
        background-color: {COLORS['background_elevated']};
    }}

    QLineEdit:disabled {{
        background-color: {COLORS['background']};
        color: {COLORS['text_disabled']};
    }}

    /* ===== COMBO BOX ===== */
    QComboBox {{
        background-color: {COLORS['background_light']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 30px;
        font-size: 13px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['accent_primary']};
    }}

    QComboBox:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text_secondary']};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 5px;
        selection-background-color: {COLORS['accent_muted']};
        selection-color: {COLORS['accent_primary']};
    }}

    /* ===== SCROLL BARS ===== */
    QScrollBar:vertical {{
        background-color: {COLORS['background_light']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['surface_border']};
        border-radius: 6px;
        min-height: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_secondary']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {COLORS['background_light']};
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['surface_border']};
        border-radius: 6px;
        min-width: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['accent_secondary']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ===== SCROLL AREA ===== */
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* ===== PROGRESS BAR ===== */
    QProgressBar {{
        background-color: {COLORS['background_light']};
        border: none;
        border-radius: 6px;
        height: 10px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_primary']},
            stop:1 {COLORS['accent_secondary']});
        border-radius: 6px;
    }}

    /* ===== CHECK BOX ===== */
    QCheckBox {{
        spacing: 10px;
        color: {COLORS['text_primary']};
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid {COLORS['surface_border']};
        background-color: {COLORS['background_light']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent_primary']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_primary']};
        border-color: {COLORS['accent_primary']};
    }}

    /* ===== RADIO BUTTON ===== */
    QRadioButton {{
        spacing: 10px;
        color: {COLORS['text_primary']};
    }}

    QRadioButton::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 10px;
        border: 2px solid {COLORS['surface_border']};
        background-color: {COLORS['background_light']};
    }}

    QRadioButton::indicator:hover {{
        border-color: {COLORS['accent_primary']};
    }}

    QRadioButton::indicator:checked {{
        background-color: {COLORS['accent_primary']};
        border: 5px solid {COLORS['background_light']};
    }}

    /* ===== SPIN BOX ===== */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['background_light']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 8px 12px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* ===== SLIDER ===== */
    QSlider::groove:horizontal {{
        background-color: {COLORS['surface_border']};
        height: 6px;
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background-color: {COLORS['accent_primary']};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {COLORS['accent_hover']};
    }}

    /* ===== MENU ===== */
    QMenu {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 5px;
    }}

    QMenu::item {{
        padding: 10px 30px 10px 20px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent_muted']};
        color: {COLORS['accent_primary']};
    }}

    /* ===== MESSAGE BOX ===== */
    QMessageBox {{
        background-color: {COLORS['surface']};
    }}

    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
    }}

    /* ===== TOOL TIP ===== */
    QToolTip {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}

    /* ===== STATUS BAR ===== */
    QStatusBar {{
        background-color: {COLORS['background_dark']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['surface_border']};
    }}

    /* ===== DIALOG ===== */
    QDialog {{
        background-color: {COLORS['surface']};
        border-radius: 12px;
    }}

    /* ===== HEADER FRAME ===== */
    QFrame[headerFrame="true"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent_primary']}20,
            stop:0.5 {COLORS['accent_secondary']}10,
            stop:1 transparent);
        border-radius: 10px;
        padding: 15px;
    }}

    /* ===== SPLITTER ===== */
    QSplitter::handle {{
        background-color: {COLORS['surface_border']};
    }}

    QSplitter::handle:horizontal {{
        width: 2px;
    }}

    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* ===== TREE VIEW ===== */
    QTreeView {{
        background-color: {COLORS['background_light']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        padding: 5px;
    }}

    QTreeView::item {{
        padding: 6px;
        border-radius: 4px;
    }}

    QTreeView::item:selected {{
        background-color: {COLORS['accent_muted']};
        color: {COLORS['accent_primary']};
    }}

    QTreeView::item:hover:!selected {{
        background-color: {COLORS['background_hover']};
    }}

    /* ===== TABLE VIEW ===== */
    QTableView, QTableWidget {{
        background-color: {COLORS['background_light']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 8px;
        gridline-color: {COLORS['surface_border']};
    }}

    QTableView::item, QTableWidget::item {{
        padding: 8px;
    }}

    QTableView::item:selected, QTableWidget::item:selected {{
        background-color: {COLORS['accent_muted']};
        color: {COLORS['accent_primary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_secondary']};
        padding: 10px;
        border: none;
        border-bottom: 2px solid {COLORS['surface_border']};
        font-weight: 600;
    }}
    """


def get_status_installed_style():
    """Style for installed status indicators"""
    return f"""
        color: {COLORS['success']};
        font-weight: 600;
    """


def get_status_not_installed_style():
    """Style for not installed status indicators"""
    return f"""
        color: {COLORS['error']};
        font-weight: 600;
    """


def get_card_button_style():
    """Style for card-like buttons in tool categories"""
    return f"""
        QPushButton {{
            background-color: {COLORS['background_light']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['surface_border']};
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 12px;
            font-weight: 500;
            text-align: left;
            min-height: 24px;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_muted']},
                stop:1 {COLORS['background_hover']});
            border-color: {COLORS['accent_primary']};
            color: {COLORS['accent_primary']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['accent_muted']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['background']};
            color: {COLORS['text_disabled']};
            border-color: {COLORS['background_hover']};
        }}
    """


def get_action_button_style():
    """Style for main action buttons"""
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['surface_light']},
                stop:1 {COLORS['background_hover']});
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['surface_border']};
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 600;
            min-height: 28px;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_primary']},
                stop:1 {COLORS['accent_secondary']});
            color: {COLORS['background_dark']};
            border: none;
        }}

        QPushButton:pressed {{
            background-color: {COLORS['accent_secondary']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['background_light']};
            color: {COLORS['text_disabled']};
            border-color: {COLORS['background_hover']};
        }}
    """


def get_primary_button_style():
    """Style for primary CTA buttons"""
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_primary']},
                stop:1 {COLORS['accent_secondary']});
            color: {COLORS['background_dark']};
            border: none;
            border-radius: 10px;
            padding: 14px 28px;
            font-size: 14px;
            font-weight: 700;
            min-height: 32px;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_hover']},
                stop:1 {COLORS['accent_primary']});
        }}

        QPushButton:pressed {{
            background-color: {COLORS['accent_secondary']};
        }}
    """


def get_log_text_style():
    """Style for log/console text areas"""
    return f"""
        QTextEdit {{
            background-color: {COLORS['background_dark']};
            color: {COLORS['android_green']};
            border: 1px solid {COLORS['surface_border']};
            border-radius: 10px;
            padding: 12px;
            font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.6;
        }}

        QTextEdit:focus {{
            border-color: {COLORS['accent_primary']};
        }}
    """


def get_info_card_style():
    """Style for device info cards"""
    return f"""
        background-color: {COLORS['background_light']};
        border: 1px solid {COLORS['surface_border']};
        border-radius: 10px;
        padding: 15px;
    """


def get_header_style():
    """Style for main headers"""
    return f"""
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: 24px;
            font-weight: 700;
            background: transparent;
            padding: 5px 0;
        }}
    """


def get_subheader_style():
    """Style for section subheaders"""
    return f"""
        QLabel {{
            color: {COLORS['accent_primary']};
            font-size: 15px;
            font-weight: 600;
            background: transparent;
            padding: 3px 0;
        }}
    """


def get_label_style():
    """Style for info labels"""
    return f"""
        QLabel {{
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
        }}
    """


def get_value_style():
    """Style for info values"""
    return f"""
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: 13px;
            font-weight: 400;
            background: transparent;
        }}
    """


def get_category_frame_style():
    """Style for tool category frames"""
    return f"""
        QGroupBox {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['surface_border']};
            border-radius: 14px;
            margin-top: 24px;
            padding: 24px 16px 16px 16px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 16px;
            top: 8px;
            padding: 2px 12px;
            background-color: {COLORS['surface']};
            color: {COLORS['accent_primary']};
            font-size: 15px;
            font-weight: 700;
            border-radius: 6px;
        }}
    """


# Icon mappings using Unicode symbols for a cleaner look
ICONS = {
    'device': '\uf10a',  # smartphone
    'connect': '\uf0c1',  # link
    'wifi': '\uf1eb',  # wifi
    'refresh': '\uf021',  # refresh
    'remove': '\uf00d',  # times
    'screenshot': '\uf030',  # camera
    'backup': '\uf0c7',  # save
    'files': '\uf07b',  # folder
    'install': '\uf019',  # download
    'apps': '\uf3a5',  # mobile
    'log': '\uf022',  # list-alt
    'reboot': '\uf01e',  # refresh
    'settings': '\uf013',  # cog
    'security': '\uf023',  # lock
    'debug': '\uf188',  # bug
    'test': '\uf0c3',  # flask
    'automation': '\uf544',  # robot
    'control': '\uf074',  # random
}


# Emoji icons for categories (fallback if font icons not available)
EMOJI_ICONS = {
    'Device Control': '\U0001F504',      # 🔄
    'App Management': '\U0001F4F1',       # 📱
    'System Tools': '\u2699\ufe0f',       # ⚙️
    'Debugging': '\U0001F41E',            # 🐞
    'File Operations': '\U0001F4C1',      # 📁
    'Security & Permissions': '\U0001F512',  # 🔒
    'Automation & Scripting': '\U0001F916',  # 🤖
    'Advanced Tests': '\U0001F9EA',       # 🧪

    # Action button icons
    'connect': '\U0001F517',              # 🔗
    'wifi': '\U0001F4F6',                 # 📶
    'refresh': '\U0001F504',              # 🔄
    'remove': '\U0001F5D1',               # 🗑️
    'screenshot': '\U0001F4F8',           # 📸
    'backup': '\U0001F4BE',               # 💾
    'files': '\U0001F4C2',                # 📂
    'install': '\U0001F4E5',              # 📥
    'apps': '\U0001F4F2',                 # 📲
    'log': '\U0001F4CB',                  # 📋
}
