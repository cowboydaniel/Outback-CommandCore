"""
Settings tab for the CommandCore Launcher.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QCheckBox, QPushButton, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal


class SettingRow(QWidget):
    def __init__(self, label, control, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #ECF0F1; font-size: 13px; background: transparent;")
        lbl.setFixedWidth(220)

        layout.addWidget(lbl)
        layout.addWidget(control, 1)


class SectionHeader(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #ECF0F1; font-size: 15px; font-weight: bold; margin-top: 12px; background: transparent;")


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ECF0F1; background: transparent;")
        subtitle = QLabel("Configure application preferences, themes, and system settings.")
        subtitle.setStyleSheet("font-size: 14px; color: #B0B0B0; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("settingsCard")
        card.setStyleSheet("""
            #settingsCard {
                background-color: #3A3A3A;
                border: 1px solid #4A4A4A;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(4)

        # Appearance
        card_layout.addWidget(SectionHeader("Appearance"))
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #4A4A4A;"); card_layout.addWidget(sep)

        theme_combo = QComboBox()
        theme_combo.addItems(["Dark (default)", "Light", "System"])
        theme_combo.setStyleSheet("""
            QComboBox {
                background: #2A2D2E; color: #ECF0F1;
                border: 1px solid #4A4A4A; border-radius: 4px;
                padding: 4px 8px; min-height: 28px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #2A2D2E; color: #ECF0F1;
                selection-background-color: #00a8ff;
            }
        """)
        card_layout.addWidget(SettingRow("Theme", theme_combo))

        font_combo = QComboBox()
        font_combo.addItems(["Segoe UI", "Arial", "Consolas", "Monospace"])
        font_combo.setStyleSheet(theme_combo.styleSheet())
        card_layout.addWidget(SettingRow("UI Font", font_combo))

        # Behaviour
        card_layout.addWidget(SectionHeader("Behaviour"))
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #4A4A4A;"); card_layout.addWidget(sep2)

        chk_style = "color: #ECF0F1; font-size: 13px;"
        auto_refresh = QCheckBox()
        auto_refresh.setChecked(True)
        auto_refresh.setStyleSheet(chk_style)
        card_layout.addWidget(SettingRow("Auto-refresh App Manager", auto_refresh))

        skip_deps = QCheckBox()
        skip_deps.setChecked(False)
        skip_deps.setStyleSheet(chk_style)
        card_layout.addWidget(SettingRow("Skip dependency check on start", skip_deps))

        # About
        card_layout.addWidget(SectionHeader("About"))
        sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("color: #4A4A4A;"); card_layout.addWidget(sep3)

        for label, value in [("Version", "v1.0.0"), ("Author", "CommandCore Team"), ("License", "MIT")]:
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet("color: #B0B0B0; font-size: 13px; background: transparent;")
            card_layout.addWidget(SettingRow(label, val_lbl))

        card_layout.addStretch()
        layout.addWidget(card, 1)
