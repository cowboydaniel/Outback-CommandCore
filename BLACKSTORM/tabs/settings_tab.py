"""
Settings tab for BLACKSTORM - Application configuration.
"""
import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QSpinBox, QColorDialog, QSlider, QFontComboBox, QApplication
)
from PySide6.QtGui import QFont, QPalette, QColor, QAction
from PySide6.QtCore import Qt, Signal, QSize

from BLACKSTORM.app.config import (
    CONFIG_DIR,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_SETTINGS,
    SETTINGS_FILE,
)
from BLACKSTORM.core.base import BaseTab
from BLACKSTORM.core.utils import deep_merge
from BLACKSTORM.ui.styles.buttons import SAVE_BUTTON_STYLE

class SettingsTab(BaseTab):
    """Tab for application settings and configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = deep_merge(DEFAULT_SETTINGS, {})
        self.setup_ui()
        
    def set_settings(self, settings):
        """Update UI elements with the provided settings.
        Does NOT apply any settings to the application.
        
        Args:
            settings (dict): Dictionary containing settings to display
        """
        if not settings:
            return
            
        self.settings = settings
        
        # Make sure UI is fully initialized before updating
        if not hasattr(self, 'tabs') or not self.tabs:
            return
            
        # Update UI elements if they exist
        self._update_ui_from_settings()
        
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Main content area
        self.tabs = QTabWidget()
        
        # Setup all tabs
        self.setup_general_tab()
        
        # Appearance tab
        appearance_tab = QWidget()
        self.setup_appearance_tab(appearance_tab)
        self.tabs.addTab(appearance_tab, "Appearance")
        
        # Wipe settings tab
        wipe_tab = QWidget()
        self.setup_wipe_tab(wipe_tab)
        self.tabs.addTab(wipe_tab, "Wipe Settings")
        
        layout.addWidget(self.tabs)
        
        # Save button
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet(SAVE_BUTTON_STYLE)
        btn_save.clicked.connect(self.save_settings)
        
        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
    def setup_appearance_tab(self, parent):
        """Set up the Appearance settings tab with text size controls."""
        layout = QVBoxLayout(parent)
        
        # Load saved settings
        self.load_settings()
        
        # Text Size Group
        text_group = QGroupBox("Text Size")
        text_layout = QVBoxLayout(text_group)
        
        # Font size slider with preview
        size_slider_layout = QHBoxLayout()
        
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 24)
        self.font_size_slider.setValue(10)
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_slider.setTickInterval(2)
        self.font_size_slider.setFixedWidth(200)
        
        self.font_size_label = QLabel("10")
        self.font_size_label.setFixedWidth(30)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Connect slider to update label and preview
        self.font_size_slider.valueChanged.connect(self._update_font_size_preview)
        
        # Font family selection
        self.font_family = QFontComboBox()
        self.font_family.setCurrentFont(QFont(DEFAULT_FONT_FAMILY))
        self.font_family.currentFontChanged.connect(self._update_font_preview)
        
        # Font preview
        self.font_preview = QLabel("Sample Text: AaBbCcDdEeFfGg 0123456789")
        self.font_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.font_preview.setFrameStyle(1)  # Sunken panel
        self.font_preview.setMinimumHeight(60)
        self.font_preview.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 10px;
                color: #333333;
            }
        """)
        
        # Add widgets to layouts
        size_controls = QHBoxLayout()
        size_controls.addWidget(QLabel("Size:"))
        size_controls.addWidget(self.font_size_slider)
        size_controls.addWidget(self.font_size_label)
        size_controls.addStretch()
        
        text_layout.addLayout(size_controls)
        text_layout.addWidget(QLabel("Font:"))
        text_layout.addWidget(self.font_family)
        text_layout.addSpacing(10)
        text_layout.addWidget(QLabel("Preview:"))
        text_layout.addWidget(self.font_preview)
        
        # Theme selection (minimal for now, will be expanded)
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        theme_layout.addWidget(self.theme_combo)
        
        # Add all groups to main layout
        layout.addWidget(text_group)
        layout.addWidget(theme_group)
        layout.addStretch()
        
        # Initial preview update
        self._update_font_preview()
        
        # Connect save button
        for btn in self.findChildren(QPushButton):
            if btn.text() == "Save Settings":
                btn.clicked.connect(self.save_settings)
                break
    
    def _update_font_size_preview(self, size=None):
        """Update the font size preview when the slider changes."""
        if size is None:
            size = self.font_size_slider.value()
        self.font_size_label.setText(str(size))
        self._update_font_preview()
    
    def _update_font_preview(self):
        """Update the font preview with current settings."""
        font = self.font_family.currentFont()
        font.setPointSize(self.font_size_slider.value())
        self.font_preview.setFont(font)
    
    def setup_wipe_tab(self, parent):
        """Set up the Wipe Settings tab."""
        layout = QFormLayout(parent)
        
        # Wipe method
        self.wipe_method = QComboBox()
        self.wipe_method.addItems([
            "Quick (1-pass zero)",
            "DoD 5220.22-M (3-pass)",
            "Gutmann (35-pass)",
            "NIST 800-88 (1-pass)"
        ])
        
        # Verification
        self.verify_wipe = QCheckBox("Verify after wipe")
        
        # Add to form
        layout.addRow("Default Wipe Method:", self.wipe_method)
        layout.addRow(self.verify_wipe)
    
    def browse_save_location(self):
        """Open dialog to select save location."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Location",
            self.save_location.text() or "/"
        )
        
        if dir_path:
            self.save_location.setText(dir_path)
    
    def load_settings(self):
        """Load settings from configuration."""
        try:
            # Get the application instance
            app = QApplication.instance()
            
            # Try to load settings from the main application first
            if app and hasattr(app, 'settings'):
                # Deep merge the settings
                # Merge the application settings with our defaults
                self.settings = deep_merge(self.settings.copy(), app.settings)
            
            # Load language if the widget exists
            if hasattr(self, 'language'):
                self.language.setCurrentText(self.settings.get('language', DEFAULT_SETTINGS['language']))
            
            # Load save location if the widget exists
            if hasattr(self, 'save_location'):
                self.save_location.setText(self.settings.get('save_location', DEFAULT_SETTINGS['save_location']))
            
            # Load auto-update setting if the widget exists
            if hasattr(self, 'auto_update'):
                self.auto_update.setChecked(self.settings.get('auto_update', DEFAULT_SETTINGS['auto_update']))
            
            # Load theme if the widget exists
            if hasattr(self, 'theme_combo'):
                theme = self.settings.get('theme', DEFAULT_SETTINGS['ui_theme'])
                if theme.lower() in ['dark', 'light', 'system']:
                    self.theme_combo.setCurrentText(theme.capitalize())
            
            # Load font settings if widgets exist
            if hasattr(self, 'font_family') and hasattr(self, 'font_size_slider'):
                font_settings = self.settings.get('font', {})
                font_family = font_settings.get('family', DEFAULT_FONT_FAMILY)
                font_size = font_settings.get('size', DEFAULT_FONT_SIZE)
                
                # Create and set the font
                font = QFont(font_family)
                font.setPointSize(font_size)
                self.font_family.setCurrentFont(font)
                self.font_size_slider.setValue(font_size)
                
                # Update the preview
                self._update_font_preview()
                
                # If we have an app instance, apply the font
                if app:
                    app.setFont(font)
            
            # Load wipe method if the widget exists
            if hasattr(self, 'wipe_method'):
                wipe_method = self.settings.get('wipe_method', DEFAULT_SETTINGS['wipe_method'])
                index = self.wipe_method.findText(wipe_method)
                if index >= 0:
                    self.wipe_method.setCurrentIndex(index)
            
            # Load verify_wipe if the widget exists
            if hasattr(self, 'verify_wipe'):
                self.verify_wipe.setChecked(self.settings.get('verify_wipe', True))
                
            # Update the UI with the loaded settings
            # Font settings will be applied by the launcher
            self._update_ui_from_settings()
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            print(f"Error loading settings: {error_details}")
            
            # If there was an error, apply default settings
            self._update_ui_from_settings()
    
    def save_settings(self):
        """Save settings to configuration file."""
        try:
            # Update settings with current UI values
            settings = {
                'language': self.language.currentText(),
                'save_location': self.save_location.text(),
                'auto_update': self.auto_update.isChecked(),
                'ui_theme': self.theme_combo.currentText().lower(),
                'font': {
                    'family': self.font_family.currentFont().family(),
                    'size': self.font_size_slider.value()
                },
                'wipe_method': self.wipe_method.currentText(),
                'verify_wipe': self.verify_wipe.isChecked()
            }
            
            # Ensure config directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Save to file
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "Your settings have been saved successfully.\n\n"
                "Please restart the application for all changes to take effect."
            )
            
            return True
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {str(e)}\n\n{error_details}"
            )
            return False

    def _update_ui_from_settings(self):
        """Update UI elements from settings."""
        try:
            if not hasattr(self, 'settings') or not self.settings:
                print("No settings to update UI")
                return
                
            print("Updating UI from settings:", self.settings)  # Debug
            
            # Helper function to safely set widget values
            def safe_set(widget_attr, setter, value, default=None):
                if not hasattr(self, widget_attr):
                    print(f"Widget {widget_attr} not found")
                    return
                widget = getattr(self, widget_attr)
                try:
                    if widget is not None:
                        setter(widget, value)
                except Exception as e:
                    print(f"Error setting {widget_attr}: {e}")
        
            # Update font settings
            if hasattr(self, 'font_family'):
                font_settings = self.settings.get('font', {})
                font_family = font_settings.get('family', 
                            'Segoe UI' if sys.platform == 'win32' else 'Noto Sans')
                
                # Set font family
                try:
                    font = QFont(font_family)
                    font.setPointSize(10)  # Default size for the dropdown
                    self.font_family.blockSignals(True)
                    self.font_family.setCurrentFont(font)
                    self.font_family.blockSignals(False)
                except Exception as e:
                    print(f"Error setting font family: {e}")
            
            # Set font size
            if hasattr(self, 'font_size_slider') and hasattr(self, 'font_size_label'):
                font_size = self.settings.get('font', {}).get('size', 10)
                try:
                    self.font_size_slider.blockSignals(True)
                    self.font_size_slider.setValue(font_size)
                    self.font_size_slider.blockSignals(False)
                    self.font_size_label.setText(str(font_size))
                except Exception as e:
                    print(f"Error setting font size: {e}")
            
            # Update font preview if possible
            if hasattr(self, '_update_font_preview'):
                try:
                    self._update_font_preview()
                except Exception as e:
                    print(f"Error updating font preview: {e}")
            
            # Update theme
            safe_set('theme_combo', 
                    lambda w, v: w.setCurrentText(v.capitalize()) if w.findText(v, Qt.MatchFixedString) >= 0 else None,
                    self.settings.get('ui_theme', 'dark'))
            
            # Update general settings
            safe_set('language', 
                    lambda w, v: w.setCurrentText(v) if w.findText(v, Qt.MatchFixedString) >= 0 else None,
                    self.settings.get('language', 'English'))
            
            safe_set('save_location', 
                    lambda w, v: w.setText(str(v) if v else ''),
                    self.settings.get('save_location', ''))
            
            safe_set('auto_update', 
                    lambda w, v: w.setChecked(bool(v)),
                    self.settings.get('auto_update', True))
            
            # Update wipe settings
            safe_set('wipe_method',
                    lambda w, v: w.setCurrentText(str(v)) if w.findText(str(v), Qt.MatchFixedString) >= 0 else None,
                    self.settings.get('wipe_method', 'DoD 5220.22-M (3-pass)'))
            
            safe_set('verify_wipe',
                    lambda w, v: w.setChecked(bool(v)),
                    self.settings.get('verify_wipe', True))
            
        except Exception as e:
            import traceback
            print(f"Error in _update_ui_from_settings: {e}")
            traceback.print_exc()
    
    # Font settings are applied by the launcher, not this tab
    
    def setup_general_tab(self):
        """Set up the General settings tab."""
        general_tab = QWidget()
        layout = QVBoxLayout(general_tab)
        
        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Language selection
        self.language = QComboBox()
        self.language.addItems(["English", "Spanish", "French", "German"])
        
        # Save location
        save_layout = QHBoxLayout()
        self.save_location = QLineEdit()
        self.save_location.setReadOnly(True)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_save_location)
        save_layout.addWidget(self.save_location)
        save_layout.addWidget(btn_browse)
        
        # Auto-update
        self.auto_update = QCheckBox("Check for updates automatically")
        
        # Add to form
        form_layout.addRow("Language:", self.language)
        form_layout.addRow("Save Location:", save_layout)
        form_layout.addRow(self.auto_update)
        
        # Add form to layout with some margins
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Add the general tab to the main tabs
        self.tabs.addTab(general_tab, "General")
