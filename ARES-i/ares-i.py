import sys
import os
import subprocess
import json
import time
import platform
import logging
import shutil
import tempfile
import requests
import zipfile
import re
import base64
from pathlib import Path
import urllib.request
from urllib.parse import urljoin
import webbrowser
import threading
import array
import random

# PySide6 imports
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTabWidget, QScrollArea, QMessageBox, QFileDialog,
                              QTextEdit, QGroupBox, QSizePolicy, QScrollBar, QGridLayout, QProgressDialog,
                              QInputDialog, QDialog, QVBoxLayout as QVBoxLayout2, QLabel as QLabel2,
                              QLineEdit, QComboBox, QDialogButtonBox, QTextEdit, QScrollArea, QStatusBar,
                              QTextBrowser)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG, QSize, QThread, QObject, Signal as PySideSignal, QTimer, Slot
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

# Set up logging for iOS Tools Module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Custom signal class for thread-safe UI updates
class SignalEmitter(QObject):
    update_signal = PySideSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def update_status(self, message):
        self.update_signal.emit(message)

# Check if required iOS tools are installed
def check_ios_tools_installed():
    """
    Check if required iOS tools are installed.
    Returns True if all required tools are available, False otherwise.
    """
    required_tools = ['idevice_id', 'ideviceinfo', 'idevicebackup2', 'ifuse']
    missing_tools = []
    
    for tool in required_tools:
        if shutil.which(tool) is None:
            missing_tools.append(tool)
    
    if not missing_tools:
        logging.info("All required iOS tools are installed")
        return True
        
    logging.warning(f"Missing iOS tools: {', '.join(missing_tools)}")
    return False

class IOSToolsModule(QMainWindow):
    def apply_styles(self):
        """Apply BLACKSTORM theme to the application"""
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }

            /* Tab Widget */
            QTabWidget::pane {
                border: none;
                background: #181825;
            }
            
            QTabBar::tab {
                background: #181825;
                color: #a6adc8;
                border: none;
                padding: 15px 20px;
                margin-right: 2px;
                font-size: 14px;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background: #313244;
                color: #89b4fa;
                border-bottom: 2px solid #89b4fa;
            }
            
            QTabBar::tab:hover:!selected {
                background: #313244;
            }
            
            /* Group Boxes */
            QGroupBox {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                margin-top: 1em;
                padding: 15px;
                color: #89b4fa;
                font-size: 14px;
                font-weight: bold;
            }
            
            /* Labels */
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background-color: #45475a;
            }
            
            QPushButton:pressed {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            
            /* Scroll Bars */
            QScrollBar:vertical {
                border: none;
                background: #181825;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 5px;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #181825;
                color: #a6adc8;
                font-size: 12px;
                border-top: 1px solid #313244;
                padding: 3px 10px;
            }
            
            QStatusBar::item {
                border: none;
                padding: 0 5px;
            }
            
            QStatusBar QLabel {
                color: #a6adc8;
                background: transparent;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px 8px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)

    def __init__(self, parent=None):
        """Initialize the iOS Tools module for Linux"""
        super().__init__(parent)
        self.apply_styles()  # Apply BLACKSTORM theme
        
        # Initialize instance variables
        self.device_connected = False
        self.device_info = {}
        self.status_message = "Ready"
        
        # Signal emitter for thread-safe UI updates
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.update_signal.connect(self.update_status)
        
        # Set window properties
        self.setWindowTitle("iOS Tools")
        
        # Get available screen geometry (accounts for taskbar)
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # Set window size and position
        self.setGeometry(screen_rect)
        self.setMinimumSize(screen_rect.width(), screen_rect.height())
        self.setMaximumSize(screen_rect.width(), screen_rect.height())
        
        # Initialize UI
        self.setup_ui()
        
        # Check for required tools
        self.check_dependencies()
        
    def update_status(self, message):
        """Update status bar message"""
        if hasattr(self, 'status_bar'):
            self.status_bar.setText(message)
            QApplication.processEvents()

    def _decode_base64_if_needed(self, value):
        """Helper to decode base64 values if they appear to be base64"""
        import base64
        import re
        
        # Skip if not a typical base64 string
        if not re.match(r'^[A-Za-z0-9+/=]+$', value):
            return value
            
        try:
            # Try to decode as base64
            decoded = base64.b64decode(value).decode('utf-8', errors='ignore')
            # If it decodes to something readable, return both
            if len(decoded) > 0 and all(32 <= ord(c) <= 126 for c in decoded):
                return f"{value} (decoded: {decoded})"
        except Exception:
            pass
            
        return value
        
    def _decode_base64(self, value):
        """Safely decode base64 values"""
        import base64
        try:
            # Skip if not actually base64
            if not value or not isinstance(value, str):
                return value
                
            # Remove any whitespace
            value = value.strip()
            
            # Try standard base64 first
            decoded_bytes = base64.b64decode(value)
            decoded = decoded_bytes.decode('utf-8', errors='ignore')
            
            # If it's just a few characters, it's probably a simple string
            if len(decoded) < 20 and all(32 <= ord(c) <= 126 for c in decoded):
                return f"{decoded}"
                
            # For longer binary data, show size and type
            return f"[Binary data: {len(decoded_bytes)} bytes]"
            
        except Exception as e:
            # If we can't decode it, just return the original
            return value

    def _format_system_value(self, key, value):
        """Format system information values for better readability"""
        import base64
        import datetime
        import re
        
        # Skip empty values and numeric keys (array indices)
        if not value or value == '(null)' or (isinstance(key, str) and re.match(r'^\d+$', key)):
            return None
            
        # Handle array values
        if isinstance(value, list):
            # Clean up the list by removing empty strings
            cleaned = [str(v).strip() for v in value if str(v).strip()]
            if not cleaned:
                return None
                
            # Special handling for device families
            if 'DeviceFamilies' in key:
                family_map = {
                    '1': 'iPhone/iPod Touch',
                    '2': 'iPad',
                    '3': 'Apple TV',
                    '4': 'Apple Watch',
                    '5': 'HomePod',
                    '6': 'iPod Touch',
                    '7': 'Apple Vision Pro'
                }
                families = [family_map.get(v, f'Unknown ({v})') for v in cleaned if v in family_map or v.isdigit()]
                return ', '.join(families) if families else None
                
            return ', '.join(cleaned)
            
        # Handle boolean values first - these should always be consistent
        if key in ['ActivationStateAcknowledged', 'ProductionSOC', 'TrustedHostAttached',
                  'TelephonyCapability', 'UseRaptorCerts', 'HasSiDP', 'HostAttached']:
            return "✅ Yes" if value.lower() == 'true' else "❌ No"
        elif key == 'BrickState':
            # BrickState is a negative state, so we invert the logic
            return "❌ Bricked" if value.lower() == 'true' else "✅ Not Bricked"
        elif key == 'PasswordProtected':
            return "🔒 Yes" if value.lower() == 'true' else "🔓 No"
            
        # Handle specific known fields with direct mappings
        field_handlers = {
            'SoftwareBehavior': lambda v: self._decode_software_behavior(v) if isinstance(v, str) else f"[Unhandled type: {type(v).__name__}]",
            'ProximitySensorCalibration': lambda v: self._decode_proximity_sensor_data(v) if isinstance(v, str) else f"[Unhandled type: {type(v).__name__}]",
            'SupportedDeviceFamilies': lambda v: f"Supports: {v}" if v else None,
            'RegionInfo': lambda v: v if v != 'LL/A' else 'Australia',
            'fm-activation-locked': lambda v: "🔒 Locked" if v == 'Tk8=' else "🔓 Unlocked",
            'bootdelay': lambda v: "0 (immediate)" if v == 'MA==' else v,
            'auto-boot': lambda v: "✅ Enabled" if v == 'dHJ1ZQ==' else "⏹ Disabled",
            'fm-spstatus': lambda v: "📶 " + {
                'WUVT': 'Wi-Fi and Cellular',
                'WUVTQ0Y=': 'Wi-Fi, Cell, GPS',
                'WQ==': 'Wi-Fi only',
                'UQ==': 'Cellular only'
            }.get(v, v),
            'usbcfwflasherResult': lambda v: "✅ Success" if v == 'Tm8gZXJyb3Jz' else f"❌ {v}",
            'DeviceColor': lambda v: self._get_color_name(v),
            'Uses24HourClock': lambda v: "🕒 24-hour" if v.lower() == 'true' else "🕒 12-hour",
            'TimeZoneOffsetFromUTC': lambda v: f"UTC{int(v)/3600:+.1f} hours"
        }
        
        # Apply specific handler if exists
        if key in field_handlers:
            return field_handlers[key](value)
            
        # Handle base64 encoded values
        if any(x in key.lower() for x in ['hash', 'key', 'token', 'cert', 'calibration', 'serial']) or \
           any(key.lower().endswith(x) for x in ['status', 'state', 'result', 'locked', 'level', 'args', 'delay']):
            if isinstance(value, str) and value.endswith('=='):
                return self._decode_base64(value)
        
        # Handle hex values (long hex strings)
        if isinstance(value, str) and all(c in '0123456789abcdefABCDEF' for c in value) and len(value) > 8:
            return f"0x{value} (hex, {len(value)//2} bytes)"
            
        # Handle potential base64 values
        if isinstance(value, str) and any(c in '+/=' for c in value) and len(value) % 4 == 0:
            if len(value) < 50:  # Only decode short base64 strings
                return self._decode_base64(value)
            return f"{value[:20]}... (binary data, {len(value)} chars)"
            
        # Handle generic boolean-like values (only if not already handled)
        if isinstance(value, str):
            if value.lower() in ('true', 'yes', '1'):
                return "✅ Yes"
            if value.lower() in ('false', 'no', '0', 'none', 'null'):
                return "❌ No"
            
        # Handle timestamps
        if key.endswith('Since1970') and value.replace('.', '').isdigit():
            try:
                timestamp = float(value)
                dt = datetime.datetime.fromtimestamp(timestamp)
                return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}"
            except (ValueError, OSError):
                pass
                
        return value  # Return original value if no special handling applies
                
    def _decode_software_behavior(self, value):
        """Decode and interpret SoftwareBehavior binary data"""
        try:
            # Decode the base64 value
            decoded = base64.b64decode(value)
            if not decoded:
                return "No behavior flags set"
                
            # Interpret the first 4 bytes as bitfields (little-endian)
            flags = []
            if len(decoded) >= 4:
                # First byte (0x11 in the example)
                byte1 = decoded[0]
                if byte1 & 0x01: flags.append("Auto-Lock enabled")
                if byte1 & 0x10: flags.append("Unknown flag (0x10)")
                
                # Second byte (0x00 in the example)
                byte2 = decoded[1]
                if byte2 & 0x01: flags.append("Unknown flag (0x0100)")
                
                # Third and fourth bytes (0x0000 in the example)
                # These are often used for version or additional flags
                
                # Check if all bytes after the first are zero
                if any(decoded[1:]):
                    hex_str = decoded.hex()
                    flags.append(f"Additional data: {hex_str[2:]}")
            else:
                # If we don't have 4 bytes, just show the hex
                return f"[Raw data: {decoded.hex()}]"
                
            return ", ".join(flags) if flags else "No behavior flags set"
            
        except Exception as e:
            return f"[Error decoding: {str(e)}]"

    def _decode_proximity_sensor_data(self, value):
        """Decode and format proximity sensor calibration data"""
        try:
            # Check if it's base64 encoded
            if not value.endswith('==') and len(value) % 4 != 0:
                # Not base64, might be raw hex
                if len(value) > 32:  # If it's long, truncate for display
                    return f"[Proximity Sensor Data: {len(value)} bytes]"
                return value
                
            # Try to decode base64
            decoded = base64.b64decode(value)
            if not decoded:
                return "No calibration data"
                
            # Format the decoded data
            hex_str = decoded.hex()
            if len(hex_str) > 40:  # Truncate long hex strings
                hex_str = f"{hex_str[:40]}..."
                
            return f"[Calibration Data: {len(decoded)} bytes] {hex_str}"
            
        except Exception as e:
            return f"[Sensor Data: {len(value)} bytes]"

    def _get_color_name(self, color_code):
        """Convert numeric color code to human-readable name"""
        color_map = {
            '1': 'Space Gray',
            '2': 'White',
            '3': 'Gold',
            '4': 'Rose Gold',
            '5': 'Silver',
            '6': 'Black',
            '7': 'Red',
            '8': 'Blue',
            '9': 'Green',
            '10': 'Purple',
            '11': 'Midnight Green',
            '12': 'Pink',
            '13': 'Yellow',
            '14': 'Coral',
            '15': 'Sierra Blue',
            '16': 'Alpine Green',
            '17': 'Purple',
            '18': 'Deep Purple',
            '19': 'Titanium',
            '20': 'Natural Titanium',
            '21': 'Blue Titanium',
            '22': 'White Titanium',
            '23': 'Black Titanium',
            '24': 'Pink',
            '25': 'Yellow'
        }
        return color_map.get(color_code, f"Color #{color_code}")
                
        # Handle hex values
        if all(c in '0123456789abcdefABCDEF' for c in value) and len(value) > 8:
            return f"0x{value} (hex, {len(value)//2} bytes)"
                
        # Handle potential base64 values
        if any(c in '+/=' for c in value) and len(value) % 4 == 0:
            if len(value) < 50:  # Only decode short base64 strings
                return self._decode_base64(value)
            return f"{value[:20]}... (binary data, {len(value)} chars)"
                
        return value
        
    def _parse_system_info(self, info_text):
        """Parse raw system info into categorized sections"""
        # First, clean up the HTML formatting
        import re
        from bs4 import BeautifulSoup
        
        # If it's HTML, extract just the text
        if '<' in info_text and '>' in info_text:
            try:
                soup = BeautifulSoup(info_text, 'html.parser')
                # Remove all <br> tags and replace with newlines
                for br in soup.find_all('br'):
                    br.replace_with('\n')
                # Get the clean text
                clean_text = soup.get_text()
            except Exception as e:
                print(f"Error parsing HTML: {e}")
                clean_text = info_text
        else:
            clean_text = info_text
            
        print("\n=== CLEANED TEXT ===")
        print(clean_text[:500] + "..." if len(clean_text) > 500 else clean_text)
        print("====================\n")
        
        # Parse the clean text into a dictionary
        info_dict = {}
        current_key = None
        
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Handle multiline values (lines that don't contain a colon or are array items)
            if (':' not in line or re.match(r'^\s*\d+\s*:', line)) and current_key is not None:
                if ':' in line:
                    # Handle array items by appending to a list
                    idx, val = line.split(':', 1)
                    if not hasattr(info_dict[current_key], 'append'):
                        info_dict[current_key] = [info_dict[current_key]]
                    info_dict[current_key].append(val.strip())
                else:
                    # Continue the current value
                    info_dict[current_key] += ' ' + line
                continue
                
            # Split into key and value if it's a new key-value pair
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Skip empty values and array indices without values
                if value or (not re.match(r'^\d+$', key) and not re.match(r'^\d+?:$', key)):
                    info_dict[key] = value
                    current_key = key if not key.endswith(':') else None
        
        print("\n=== PARSED DICT ===")
        for k, v in list(info_dict.items())[:20]:  # Print first 20 items
            print(f"{k}: {v}")
        if len(info_dict) > 20:
            print(f"... and {len(info_dict) - 20} more items")
        print("==================\n")
        
        # Define categories and their corresponding keys
        categories = {
            'Device Information': [
                'DeviceName', 'DeviceClass', 'DeviceColor',
                'ProductType', 'ProductName', 'ProductVersion',
                'BuildVersion', 'SerialNumber', 'UniqueDeviceID',
                'HardwareModel', 'HardwarePlatform', 'CPUArchitecture'
            ],
            'Network': [
                'WiFiAddress', 'BluetoothAddress', 'EthernetAddress',
                'MobileEquipmentIdentifier', 'InternationalMobileEquipmentIdentity',
                'SIMStatus', 'SIMTrayStatus'
            ],
            'Hardware': [
                'ModelNumber', 'MLBSerialNumber', 'ChipID',
                'BasebandVersion', 'BasebandStatus', 'BasebandChipID',
                'BasebandSerialNumber', 'BasebandRegionSKU'
            ],
            'System': [
                'ActivationState', 'ActivationStateAcknowledged',
                'BrickState', 'ProductionSOC', 'TrustedHostAttached',
                'PasswordProtected', 'Uses24HourClock', 'TimeZone',
                'TimeZoneOffsetFromUTC', 'TimeIntervalSince1970'
            ]
        }
        
        # Generate HTML for each category
        html = ""
        for category, keys in categories.items():
            section_html = f"<h3>{category}</h3><table>"
            added_items = False
            
            for key in keys:
                if key in info_dict and info_dict[key]:
                    # Get and format the value
                    value = self._format_system_value(key, info_dict[key])
                    if value is None:
                        continue
                        
                    # Add tooltip with raw value if different
                    tooltip = f" title=\"{info_dict[key]}\"" if str(value) != info_dict[key] else ""
                    
                    # Special handling only for ActivationState color
                    if key == 'ActivationState':
                        value = f"<span style='color:#4CAF50;'>{value}" if value == 'Activated' else f"<span style='color:#F44336;'>{value}"
                    
                    section_html += f"""
                        <tr>
                            <td style='padding: 4px 10px 4px 0; vertical-align: top;'><b>{key}:</b></td>
                            <td style='padding: 4px 0;'{tooltip}>{value}</td>
                        </tr>
                    """
                    added_items = True
            
            section_html += "</table>"
            if added_items:
                html += section_html
        
        # Add any remaining items to 'Technical Details' category
        remaining_keys = set(info_dict.keys()) - set(k for keys in categories.values() for k in keys)
        if remaining_keys:
            html += "<h3>Technical Details</h3>"
            html += "<p style='color:#a0a0a0; font-style: italic; margin: 5px 0 10px 0;'>"
            html += "Advanced technical information. Most users won't need these details."
            html += "</p><table>"
            
            for key in sorted(remaining_keys):
                if info_dict[key]:  # Only show non-empty values
                    value = self._format_system_value(key, info_dict[key])
                    if value is None:
                        continue
                        
                    # Skip very long binary data in the main view
                    if len(str(value)) > 100 and any(x in key.lower() for x in ['key', 'hash', 'cert']):
                        value = f"<i>binary data ({len(str(value))} chars)</i>"
                    
                    tooltip = f" title=\"{info_dict[key]}\"" if str(value) != info_dict[key] else ""
                    
                    html += f"""
                        <tr>
                            <td style='padding: 3px 10px 3px 0; vertical-align: top;'><b>{key}:</b></td>
                            <td style='padding: 3px 0; color:#b0b0b0;'{tooltip}>{value}</td>
                        </tr>
                    """
            html += "</table>"
        
        return f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    font-size: 12px;
                    color: #e0e0e0;
                    line-height: 1.4;
                    background-color: #2d2d2d;
                    padding: 0 10px;
                }}
                h3 {{
                    color: #ffffff;
                    padding: 6px 10px;
                    margin: 15px 0 8px 0;
                    font-size: 13px;
                    border-left: 3px solid #4a90e2;
                    background-color: #3a3a3a;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 15px;
                }}
                tr:nth-child(even) {{
                    background-color: #383838;
                }}
                tr:hover {{
                    background-color: #454545;
                }}
                td {{
                    padding: 6px 10px;
                    border-bottom: 1px solid #444;
                }}
                td:first-child {{
                    color: #a0a0a0;
                    white-space: nowrap;
                    padding-right: 20px;
                }}
                td:last-child {{
                    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                    color: #ffffff;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """

    @Slot(QDialog)
    def exec_dialog(self, dialog):
        """Helper method to execute a dialog from the main thread"""
        dialog.exec()
        
    @Slot(str, str)
    def show_info(self, title, message):
        """Show an information dialog with the given title and message"""
        # For system information, use a custom dialog
        if title in ["System Information", "Battery Diagnostics"]:
            # Create a custom dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setMinimumSize(800, 600)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #1e1e2e;
                    color: #cdd6f4;
                }
                QPushButton {
                    background-color: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45475a;
                }
                QTabBar::tab {
                    background: #1e1e2e;
                    color: #a6adc8;
                    padding: 8px 16px;
                    border: none;
                }
                QTabBar::tab:selected {
                    color: #89b4fa;
                    border-bottom: 2px solid #89b4fa;
                }
                QTabWidget::pane {
                    border: 1px solid #313244;
                    background: #181825;
                }
            """)
            
            # Create main layout
            layout = QVBoxLayout(dialog)
            
            if title == "System Information":
                # Create tab widget for different categories
                tab_widget = QTabWidget()
                
                # Parse the raw info into a dictionary
                info_dict = {}
                for line in message.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info_dict[key.strip()] = value.strip()
                
                # Create tabs for each category
                categories = {
                    'Overview': self._parse_system_info(message),
                    'Raw Data': f"<pre>{message}</pre>"
                }
                
                # Add tabs
                for name, content in categories.items():
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)
                    
                    content_widget = QTextEdit()
                    content_widget.setReadOnly(True)
                    content_widget.setStyleSheet("""
                        QTextEdit {
                            background-color: #181825;
                            color: #cdd6f4;
                            border: none;
                            font-family: monospace;
                        }
                    """)
                    content_widget.setHtml(content)
                    
                    scroll.setWidget(content_widget)
                    tab_widget.addTab(scroll, name)
                
                # Add tab widget to layout
                layout.addWidget(tab_widget)
            else:
                # For Battery Diagnostics
                text_browser = QTextBrowser()
                text_browser.setOpenExternalLinks(True)
                text_browser.setStyleSheet("""
                    QTextBrowser {
                        background-color: #181825;
                        color: #cdd6f4;
                        border: none;
                        font-family: monospace;
                        font-size: 12px;
                    }
                    h3 {
                        color: #89b4fa;
                    }
                    b {
                        color: #a6adc8;
                    }
                """)
                text_browser.setHtml(message)
                layout.addWidget(text_browser)
            
            # Add OK button
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(button_box)
            layout.addLayout(button_layout)
            
            # Show the dialog
            dialog.exec()
        else:
            # Regular message box for other dialogs
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def setup_ui(self):
        """Set up the UI for the iOS Tools module"""
        # Create a central widget and set it as the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Main header with logo
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_label = QLabel("iOS Device Management")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        main_layout.addWidget(header_frame)
        
        # Setup status frame at the top
        self.setup_status_frame = QFrame()
        self.setup_status_frame.setFrameShape(QFrame.StyledPanel)
        self.setup_status_frame.setFrameShadow(QFrame.Sunken)
        self.setup_status_frame.setStyleSheet("""
            background-color: #181825;
            border-top: 1px solid #313244;
            padding: 8px 15px;
        """)
        
        status_frame_layout = QHBoxLayout(self.setup_status_frame)
        status_frame_layout.setContentsMargins(5, 5, 5, 5)
        status_frame_layout.setSpacing(10)
        
        # Status label
        self.status_label = QLabel("Status:")
        self.status_label.setStyleSheet("""
            color: #a6adc8;
            font-weight: bold;
            font-size: 13px;
        """)
        status_frame_layout.addWidget(self.status_label)
        
        # Status text
        self.status_var = QLineEdit("Ready")
        self.status_var.setReadOnly(True)
        self.status_var.setFrame(False)
        self.status_var.setStyleSheet("""
            background: transparent;
            color: #cdd6f4;
            font-size: 13px;
            border: none;
            padding: 0;
        """)
        status_frame_layout.addWidget(self.status_var, 1)  # Stretch factor 1
        
        # Tools frame
        tools_frame = QFrame()
        tools_frame.setFrameShape(QFrame.NoFrame)
        tools_layout = QHBoxLayout(tools_frame)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(5)
        
        # Add a button to install libimobiledevice if not installed
        if not check_ios_tools_installed():
            self.libmd_btn = QPushButton("Install libimobiledevice")
            self.libmd_btn.setFixedWidth(200)
            self.libmd_btn.clicked.connect(self.install_libimobiledevice)
            tools_layout.addWidget(self.libmd_btn)
            tools_layout.addStretch()
            status_frame_layout.addWidget(tools_frame)
        
        main_layout.addWidget(self.setup_status_frame)
        
        # Main content area with tabs
        self.notebook = QTabWidget()
        self.notebook.setDocumentMode(True)
        self.notebook.setStyleSheet("""
            QTabBar::tab {
                background: #1e1e2e;
                color: #a6adc8;
                border: none;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 13px;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background: #313244;
                color: #89b4fa;
                border-bottom: 2px solid #89b4fa;
            }
            
            QTabBar::tab:hover:!selected {
                background: #313244;
            }
            
            QTabWidget::pane {
                border: 1px solid #313244;
                background: #181825;
                padding: 10px;
            }
            
            QTabBar::tab-bar {
                left: 0; /* Move tabs to the left */
            }
        """)
        
        # Device Info Tab
        self.device_frame = QWidget()
        self.device_frame.setStyleSheet("background: #181825;")
        self.device_layout = QVBoxLayout(self.device_frame)
        self.device_layout.setContentsMargins(10, 10, 10, 10)
        self.notebook.addTab(self.device_frame, "Device Info")
        
        # Tools Tab
        self.tools_frame = QWidget()
        self.tools_frame.setStyleSheet("background: #181825;")
        self.tools_layout = QVBoxLayout(self.tools_frame)
        self.tools_layout.setContentsMargins(10, 10, 10, 10)
        self.notebook.addTab(self.tools_frame, "iOS Tools")
        
        # Log Console Tab
        self.log_frame = QWidget()
        self.log_frame.setStyleSheet("background: #181825;")
        self.log_layout = QVBoxLayout(self.log_frame)
        self.log_layout.setContentsMargins(10, 10, 10, 10)
        self.notebook.addTab(self.log_frame, "Log Console")
        
        main_layout.addWidget(self.notebook)
        
        # Status bar
        self.status_bar = QLabel(self.status_message)
        self.status_bar.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.status_bar.setStyleSheet("padding: 2px;")
        main_layout.addWidget(self.status_bar)
        
        # Setup the tabs
        self.setup_device_info_tab()
        self.setup_tools_tab()
        self.setup_log_console_tab()
        
        # Update status message when status_var changes
        def update_status_message():
            self.status_bar.setText(self.status_var.text())
            
        self.status_var.textChanged.connect(update_status_message)

    def setup_device_info_tab(self):
        """Set up the device info tab"""
        # Create main layout for device info tab
        layout = self.device_layout  # Use the existing layout
        
        # Device connection frame
        connection_frame = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout(connection_frame)
        
        # Connection buttons
        conn_buttons_frame = QHBoxLayout()
        
        # Connect button
        self.connect_button = QPushButton("Connect iPhone")
        self.connect_button.clicked.connect(self.connect_device)
        conn_buttons_frame.addWidget(self.connect_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Devices")
        self.refresh_button.clicked.connect(self.refresh_device_list)
        conn_buttons_frame.addWidget(self.refresh_button)
        
        # Add stretch to push buttons to the left
        conn_buttons_frame.addStretch()
        
        connection_layout.addLayout(conn_buttons_frame)
        
        # Connection instructions
        instructions = QLabel(
            "1. Make sure your iPhone is unlocked\n"
            "2. Connect your iPhone via USB cable\n"
            "3. On your iPhone, tap 'Trust' when prompted\n"
            "4. Click 'Connect iPhone' above"
        )
        connection_layout.addWidget(instructions)
        
        # Add connection frame to main layout
        layout.addWidget(connection_frame)
        
        # Device information display
        info_frame = QGroupBox("Device Information")
        info_layout = QGridLayout(info_frame)
        
        # Create info field labels and values
        self.info_fields = {}
        basic_fields = ["Model", "Manufacturer", "iOS Version", "Serial Number", "UDID", "Battery Level"]
        
        for i, field in enumerate(basic_fields):
            label = QLabel(f"{field}:")
            label.setStyleSheet("font-weight: bold;")
            value = QLabel("N/A")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            info_layout.addWidget(label, i, 0)
            info_layout.addWidget(value, i, 1)
            
            # Add to the dictionary inside the loop
            self.info_fields[field] = value
        
        # Debug info section
        debug_label = QLabel("Debug Information")
        debug_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(debug_label, len(basic_fields) + 1, 0, 1, 2)
        
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMaximumHeight(100)
        info_layout.addWidget(self.debug_text, len(basic_fields) + 2, 0, 1, 2)
        
        layout.addWidget(info_frame)
        layout.addStretch()

    def setup_log_console_tab(self):
        """Set up the log console tab"""
        # Create a layout for the log console tab
        layout = self.log_layout  # Use the existing layout
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        controls_layout.addWidget(clear_btn)
        
        # Save button
        save_btn = QPushButton("Save Log...")
        save_btn.clicked.connect(self.save_log)
        controls_layout.addWidget(save_btn)
        
        # Add stretch to push controls to the left
        controls_layout.addStretch()
        
        # Add controls layout to main layout
        layout.addLayout(controls_layout)
        
        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 10))
        
        # Add log text to main layout
        layout.addWidget(self.log_text)
        
        # Add initial message
        self.log_message("Log console initialized")

    @Slot(str)
    def log_message(self, message):
        """Add a message to the log console"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        # If we have a log text widget, add the message
        if hasattr(self, 'log_text'):
            self.log_text.append(formatted_msg)
            # Scroll to bottom
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Always log to the console as well
        logging.info(message)

    def save_log(self):
        """Save the log contents to a file"""
        if not hasattr(self, 'log_text'):
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Log File", 
            "", 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.toPlainText())
                self.show_info("Success", f"Log saved to {file_path}")
            except Exception as e:
                self.show_info("Error", f"Failed to save log: {str(e)}")
        
    def _add_device_control_widgets(self, layout):
        """Add device control widgets to the layout"""
        # Reboot button
        reboot_btn = QPushButton("Reboot Device")
        reboot_btn.clicked.connect(self.reboot_device)
        layout.addWidget(reboot_btn)
        
        # Enter Recovery button
        recovery_btn = QPushButton("Enter Recovery")
        recovery_btn.clicked.connect(self.enter_recovery)
        layout.addWidget(recovery_btn)
        
        # Shutdown button
        shutdown_btn = QPushButton("Shutdown Device")
        shutdown_btn.clicked.connect(self.shutdown_device)
        layout.addWidget(shutdown_btn)
    
    def reboot_device(self):
        """Reboot the connected iOS device"""
        try:
            result = subprocess.run(["idevicediagnostics", "restart"], capture_output=True, text=True)
            if result.returncode == 0:
                self.show_info("Success", "Device reboot command sent successfully.")
            else:
                self.show_info("Error", f"Failed to reboot device: {result.stderr}")
        except Exception as e:
            self.show_info("Error", f"Error rebooting device: {str(e)}")
    
    def enter_recovery(self):
        """Put the device into recovery mode"""
        try:
            result = subprocess.run(["ideviceenterrecovery"], capture_output=True, text=True)
            if result.returncode == 0:
                self.show_info("Success", "Device entering recovery mode.")
            else:
                self.show_info("Error", f"Failed to enter recovery mode: {result.stderr}")
        except Exception as e:
            self.show_info("Error", f"Error entering recovery mode: {str(e)}")
    
    def shutdown_device(self):
        """Shutdown the connected iOS device"""
        try:
            result = subprocess.run(["idevicediagnostics", "shutdown"], capture_output=True, text=True)
            if result.returncode == 0:
                self.show_info("Success", "Device shutdown command sent successfully.")
            else:
                self.show_info("Error", f"Failed to shutdown device: {result.stderr}")
        except Exception as e:
            self.show_info("Error", f"Error shutting down device: {str(e)}")
    
    def _add_app_management_widgets(self, layout):
        """Add app management widgets to the layout"""
        # Install App button
        install_btn = QPushButton("Install App")
        install_btn.clicked.connect(self.install_app)
        layout.addWidget(install_btn)
        
        # Uninstall App button
        uninstall_btn = QPushButton("Uninstall App")
        uninstall_btn.clicked.connect(self.uninstall_app)
        layout.addWidget(uninstall_btn)
    
    def install_app(self):
        """Handle app installation"""
        try:
            # Show file dialog to select IPA file
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select IPA File", "", "iOS App Files (*.ipa)")
            
            if file_path:
                # Show progress dialog
                progress = QProgressDialog("Installing application...", "Cancel", 0, 0, self)
                progress.setWindowTitle("Installing App")
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                # Run installation in a separate thread
                def install_thread():
                    try:
                        result = subprocess.run(
                            ["ideviceinstaller", "-i", file_path],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            self.signal_emitter.update_signal.emit("App installed successfully")
                            QMetaObject.invokeMethod(progress, "close")
                            QMetaObject.invokeMethod(
                                self, 
                                "show_info", 
                                Qt.QueuedConnection,
                                Q_ARG(str, "Success"),
                                Q_ARG(str, "Application installed successfully.")
                            )
                        else:
                            error_msg = f"Failed to install app: {result.stderr}"
                            self.signal_emitter.update_signal.emit(error_msg)
                            QMetaObject.invokeMethod(progress, "close")
                            QMetaObject.invokeMethod(
                                self, 
                                "show_info", 
                                Qt.QueuedConnection,
                                Q_ARG(str, "Error"),
                                Q_ARG(str, error_msg)
                            )
                    except Exception as e:
                        error_msg = f"Error installing app: {str(e)}"
                        self.signal_emitter.update_signal.emit(error_msg)
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self, 
                            "show_info", 
                            Qt.QueuedConnection,
                            Q_ARG(str, "Error"),
                            Q_ARG(str, error_msg)
                        )
                
                # Start the installation in a separate thread
                thread = threading.Thread(target=install_thread, daemon=True)
                thread.start()
        except Exception as e:
            self.show_info("Error", f"Error selecting app for installation: {str(e)}")
    
    def uninstall_app(self):
        """Handle app uninstallation"""
        try:
            # Get list of installed apps
            result = subprocess.run(
                ["ideviceinstaller", "-l"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.show_info("Error", f"Failed to get list of installed apps: {result.stderr}")
                return
            
            # Parse app list and show selection dialog
            apps = [line.split('\t')[0] for line in result.stdout.split('\n') if line.strip() and not line.startswith('Total:')]
            
            if not apps:
                self.show_info("Info", "No apps found on the device.")
                return
            
            app, ok = QInputDialog.getItem(
                self, 
                "Select App to Uninstall", 
                "Installed Apps:", 
                apps, 
                0, 
                False
            )
            
            if ok and app:
                # Get bundle identifier
                bundle_id = app.split(' - ')[0].strip()
                
                # Show progress dialog
                progress = QProgressDialog("Uninstalling application...", "Cancel", 0, 0, self)
                progress.setWindowTitle("Uninstalling App")
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                # Run uninstallation in a separate thread
                def uninstall_thread():
                    try:
                        result = subprocess.run(
                            ["ideviceinstaller", "-U", bundle_id],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            self.signal_emitter.update_signal.emit("App uninstalled successfully")
                            QMetaObject.invokeMethod(progress, "close")
                            QMetaObject.invokeMethod(
                                self, 
                                "show_info", 
                                Qt.QueuedConnection,
                                Q_ARG(str, "Success"),
                                Q_ARG(str, f"Application '{app}' uninstalled successfully.")
                            )
                        else:
                            error_msg = f"Failed to uninstall app: {result.stderr}"
                            self.signal_emitter.update_signal.emit(error_msg)
                            QMetaObject.invokeMethod(progress, "close")
                            QMetaObject.invokeMethod(
                                self, 
                                "show_info", 
                                Qt.QueuedConnection,
                                Q_ARG(str, "Error"),
                                Q_ARG(str, error_msg)
                            )
                    except Exception as e:
                        error_msg = f"Error uninstalling app: {str(e)}"
                        self.signal_emitter.update_signal.emit(error_msg)
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self, 
                            "show_info", 
                            Qt.QueuedConnection,
                            Q_ARG(str, "Error"),
                            Q_ARG(str, error_msg)
                        )
                
                # Start the uninstallation in a separate thread
                thread = threading.Thread(target=uninstall_thread, daemon=True)
                thread.start()
        except Exception as e:
            self.show_info("Error", f"Error during app uninstallation: {str(e)}")
    
    def battery_diagnostics(self):
        """Run battery diagnostics on the connected iOS device"""
        try:
            # Show progress dialog
            progress = QProgressDialog("Running battery diagnostics...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Battery Diagnostics")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            def battery_thread():
                try:
                    # First check if device is connected
                    print("\n=== Starting Battery Diagnostics ===")
                    print("1. Checking if device is connected...")
                    check_device = subprocess.run(
                        ["idevice_id", "-l"],
                        capture_output=True,
                        text=True
                    )
                    
                    print(f"Device check output: {check_device.stdout.strip()}")
                    print(f"Device check error: {check_device.stderr.strip()}")
                    
                    if not check_device.stdout.strip():
                        error_msg = "No device connected. Please connect an iOS device and try again."
                        print(f"Error: {error_msg}")
                        return error_msg
                    
                    print("2. Device found, running battery diagnostics...")
                    self.signal_emitter.update_signal.emit("Running battery diagnostics...")
                    
                    # Get battery information using ideviceinfo
                    print("3. Running ideviceinfo -q com.apple.mobile.battery...")
                    result = subprocess.run(
                        ["ideviceinfo", "-q", "com.apple.mobile.battery"],
                        capture_output=True,
                        text=True
                    )
                    
                    print(f"Command output:\n{result.stdout}")
                    print(f"Command error: {result.stderr}")
                    print(f"Return code: {result.returncode}")
                    
                    self.signal_emitter.update_signal.emit(f"Command output: {result.stdout}")
                    self.signal_emitter.update_signal.emit(f"Command error: {result.stderr}")
                    self.signal_emitter.update_signal.emit(f"Return code: {result.returncode}")
                    
                    if result.returncode == 0:
                        # Parse battery information
                        battery_info = {}
                        for line in result.stdout.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                battery_info[key.strip()] = value.strip()
                        
                        print(f"Parsed battery info: {battery_info}")
                        
                        # Format the battery information for display
                        info_text = "<h3>Battery Information</h3><br><table style='border-collapse: collapse; width: 100%;'>"
                        
                        # Add battery level
                        current_capacity = int(battery_info.get('BatteryCurrentCapacity', '0'))
                        max_capacity = int(battery_info.get('BatteryMaxCapacity', '100'))
                        is_charging = battery_info.get('BatteryIsCharging', 'false').lower() == 'true'
                        is_plugged = battery_info.get('ExternalConnected', 'false').lower() == 'true'
                        fully_charged = battery_info.get('FullyCharged', 'false').lower() == 'true'
                        
                        # Add battery status summary
                        status = []
                        if is_charging:
                            status.append("Charging")
                        if is_plugged and not is_charging and not fully_charged:
                            status.append("Plugged in, not charging")
                        if fully_charged:
                            status.append("Fully charged")
                        
                        info_text += f"""
                        <tr>
                            <td style='padding: 8px; border-bottom: 1px solid #313244;'><b>Current Level:</b></td>
                            <td style='padding: 8px; border-bottom: 1px solid #313244;'>{current_capacity}%</td>
                        </tr>
                        <tr>
                            <td style='padding: 8px; border-bottom: 1px solid #313244;'><b>Status:</b></td>
                            <td style='padding: 8px; border-bottom: 1px solid #313244;'>{', '.join(status) if status else 'Discharging'}</td>
                        </tr>
                        """
                        
                        # Add detailed battery info
                        for key, value in battery_info.items():
                            if key not in ['BatteryCurrentCapacity', 'BatteryIsCharging', 'ExternalConnected', 'FullyCharged']:
                                info_text += f"""
                                <tr>
                                    <td style='padding: 8px; border-bottom: 1px solid #313244;'><b>{key}:</b></td>
                                    <td style='padding: 8px; border-bottom: 1px solid #313244;'>{value}</td>
                                </tr>
                                """
                        
                        info_text += "</table>"
                        
                        # Add battery health if max capacity is available
                        if 'BatteryMaxCapacity' in battery_info:
                            health = (current_capacity / max_capacity) * 100
                            info_text += f"<p><b>Battery Health:</b> {health:.1f}% of original capacity</p>"
                        
                        # If we got no data but the command succeeded, try alternative method
                        if not info_text.strip():
                            print("4. No battery data received, trying alternative method...")
                            self.signal_emitter.update_signal.emit("No battery data received, trying alternative method...")
                            # Try multiple commands to get battery info
                            print("5. Trying idevicediagnostics diagnostics...")
                            alt_commands = [
                                ("ideviceinfo -x", ["ideviceinfo", "-x"]),
                                ("ideviceinfo -u $(idevice_id -l) -q com.apple.mobile.battery", 
                                 ["ideviceinfo", "-u", check_device.stdout.strip(), "-q", "com.apple.mobile.battery"]),
                                ("idevicediagnostics diagnostics", ["idevicediagnostics", "diagnostics"]),
                                ("idevicediagnostics mobilegestalt BatteryCurrentCapacity BatteryIsCharging BatteryVoltage",
                                 ["idevicediagnostics", "mobilegestalt", "BatteryCurrentCapacity", "BatteryIsCharging", "BatteryVoltage"])
                            ]
                            
                            for cmd_name, cmd in alt_commands:
                                print(f"\nTrying command: {cmd_name}")
                                alt_result = subprocess.run(
                                    cmd,
                                    capture_output=True,
                                    text=True
                                )
                                print(f"Output: {alt_result.stdout}")
                                print(f"Error: {alt_result.stderr}")
                                print(f"Return code: {alt_result.returncode}")
                                
                                if alt_result.returncode == 0 and alt_result.stdout.strip():
                                    print(f"Success with command: {cmd_name}")
                                    info_text = f"<h3>Battery Information (from {cmd_name})</h3><br>"
                                    info_text += f"<pre>{alt_result.stdout}</pre>"
                                    break
                            else:
                                # If no command worked
                                print("All battery info commands failed")
                            
                            if not info_text.strip():
                                info_text = "<h3>Error</h3>"
                                info_text += "<p>Could not retrieve battery information. Please ensure:</p>"
                                info_text += "<ul>"
                                info_text += "<li>Device is connected and trusted</li>"
                                info_text += "<li>libimobiledevice tools are properly installed</li>"
                                info_text += "<li>Try unlocking your device and accepting any trust prompts</li>"
                                info_text += "<li>Make sure you have the latest version of libimobiledevice</li>"
                                info_text += "</ul>"
                                info_text += f"<p>Debug info has been printed to the terminal for troubleshooting.</p>"
                                
                                # Print all environment variables that might be useful
                                print("\n=== Environment Variables ===")
                                for key, value in os.environ.items():
                                    if 'USB' in key or 'DEV' in key or 'IDEVICE' in key:
                                        print(f"{key}: {value}")
                                        
                                # Try to get device info using different methods
                                print("\n=== Additional Device Info ===")
                                for cmd in ["ideviceinfo -s", "ideviceinfo -k ProductVersion", "ideviceinfo -k DeviceName"]:
                                    print(f"Running: {cmd}")
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                    print(f"Output: {result.stdout.strip()}")
                                    print(f"Error: {result.stderr.strip()}")
                                    print(f"Return code: {result.returncode}")
                                    print("---")
                        
                        # Prepare the HTML content for the dialog with better styling
                        # Using a raw string (r""") to avoid issues with backslashes
                        # and doubled curly braces for literal braces in CSS
                        html_template = r"""
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <style>
                                body {{
                                    background-color: #181825;
                                    color: #cdd6f4;
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                                    padding: 20px;
                                    line-height: 1.6;
                                    margin: 0;
                                }}
                                h3 {{
                                    color: #89b4fa;
                                    margin: 0 0 15px 0;
                                    padding-bottom: 10px;
                                    border-bottom: 1px solid #313244;
                                }}
                                table {{
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin: 15px 0;
                                }}
                                th {{
                                    text-align: left;
                                    padding: 10px;
                                    background-color: #1e1e2e;
                                    color: #89b4fa;
                                }}
                                td {{
                                    padding: 8px 10px;
                                    border-bottom: 1px solid #313244;
                                }}
                                tr:last-child td {{
                                    border-bottom: none;
                                }}
                                .status-ok {{
                                    color: #a6e3a1;
                                }}
                                .status-warning {{
                                    color: #f9e2af;
                                }}
                                .status-error {{
                                    color: #f38ba8;
                                }}
                                .battery-level {{
                                    display: flex;
                                    align-items: center;
                                    margin: 15px 0;
                                }}
                                .battery-bar {{
                                    flex-grow: 1;
                                    height: 20px;
                                    background-color: #313244;
                                    border-radius: 10px;
                                    overflow: hidden;
                                    margin: 0 10px;
                                }}
                                .battery-fill {{
                                    height: 100%;
                                    background: linear-gradient(90deg, #89b4fa, #74c7ec);
                                    transition: width 0.3s ease;
                                    border-radius: 10px;
                                }}
                            </style>
                        </head>
                        <body>
                            <div style='max-width: 600px; margin: 0 auto;'>
                                {battery_info}
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Determine status display based on charging and plugged in states
                        if is_charging:
                            status_text = 'Charging'
                            status_color = '#a6e3a1'  # Green for charging
                        elif is_plugged:
                            status_text = 'Plugged In (Not Charging)'
                            status_color = '#f9e2af'  # Yellow for plugged in but not charging
                        else:
                            status_text = 'Discharging'
                            status_color = '#f38ba8'  # Red for discharging
                        
                        # Get detailed battery diagnostics
                        battery_health = {}
                        try:
                            # First try the detailed diagnostics command
                            device_udid = check_device.stdout.strip()
                            diag_cmd = f"idevicediagnostics -u {device_udid} diagnostics"
                            result = subprocess.run(diag_cmd, shell=True, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                # Parse the XML output
                                import plistlib
                                from io import BytesIO
                                import xml.parsers.expat
                                
                                try:
                                    # Clean up the XML if needed (remove any null bytes or invalid characters)
                                    clean_xml = result.stdout.encode('utf-8', 'ignore').decode('utf-8')
                                    plist_data = plistlib.loads(clean_xml.encode('utf-8'))
                                    
                                    # Extract battery info from GasGauge section
                                    if 'GasGauge' in plist_data:
                                        gas_gauge = plist_data['GasGauge']
                                        battery_health.update({
                                            'CycleCount': str(gas_gauge.get('CycleCount', 'N/A')),
                                            'DesignCapacity': str(gas_gauge.get('DesignCapacity', 'N/A')),
                                            'FullChargeCapacity': str(gas_gauge.get('FullChargeCapacity', 'N/A')),
                                            'Status': gas_gauge.get('Status', 'Unknown')
                                        })
                                except (plistlib.InvalidFileException, xml.parsers.expat.ExpatError) as e:
                                    print(f"Error parsing diagnostics XML: {e}")
                                    
                                    # Fallback to mobilegestalt if XML parsing fails
                                    fallback_cmd = "idevicediagnostics mobilegestalt BatteryCycleCount BatteryDesignCapacity BatteryMaxCapacity BatteryTemperature"
                                    result = subprocess.run(fallback_cmd, shell=True, capture_output=True, text=True)
                                    if result.returncode == 0:
                                        for line in result.stdout.split('\n'):
                                            if '=' in line:
                                                key, value = line.split('=', 1)
                                                battery_health[key.strip()] = value.strip()
                        except Exception as e:
                            print(f"Error getting battery health: {e}")
                        
                        # Calculate battery health percentage if we have the data
                        health_percent = None
                        design_cap = None
                        max_cap = None
                        
                        # Try to get capacities from diagnostics first
                        if 'DesignCapacity' in battery_health and 'FullChargeCapacity' in battery_health:
                            try:
                                design_cap = int(battery_health['DesignCapacity'])
                                max_cap = int(battery_health['FullChargeCapacity'])
                                if design_cap > 0:
                                    health_percent = min(100, int((max_cap / design_cap) * 100))
                            except (ValueError, ZeroDivisionError):
                                pass
                                
                        # Fallback to mobilegestalt values if needed
                        if health_percent is None and 'BatteryDesignCapacity' in battery_health and 'BatteryMaxCapacity' in battery_health:
                            try:
                                design_cap = int(battery_health['BatteryDesignCapacity'])
                                max_cap = int(battery_health['BatteryMaxCapacity'])
                                if design_cap > 0:
                                    health_percent = min(100, int((max_cap / design_cap) * 100))
                            except (ValueError, ZeroDivisionError):
                                pass
                        
                        # Set colors based on levels
                        battery_color = (
                            '#f38ba8' if current_capacity < 20 else  # Red for low
                            '#f9e2af' if current_capacity < 40 else  # Yellow for medium
                            '#a6e3a1'                                # Green for good
                        )
                        
                        health_color = (
                            '#f38ba8' if health_percent and health_percent < 80 else  # Red for poor
                            '#f9e2af' if health_percent and health_percent < 90 else  # Yellow for fair
                            '#a6e3a1' if health_percent else '#a6adc8'  # Green for good, gray if unknown
                        )
                        
                        # Format capacity values with thousands separators
                        def format_mah(value):
                            try:
                                return f"{int(value):,} mAh"
                            except (ValueError, TypeError):
                                return 'N/A'
                        
                        # Get cycle count with fallback
                        cycle_count = battery_health.get('CycleCount', battery_health.get('BatteryCycleCount', 'N/A'))
                        
                        battery_content = f"""
                        <div style="max-width: 480px; margin: 0 auto; padding: 20px; background: #1e1e2e; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="font-size: 2em; font-weight: bold; color: #89b4fa;">
                                    {current_capacity}%
                                </div>
                                <div style="color: {status_color}; font-weight: 500;">
                                    {status_text}
                                </div>
                            </div>
                            
                            <div style="height: 12px; background: #313244; border-radius: 6px; overflow: hidden; margin-bottom: 20px;">
                                <div style="height: 100%; width: {current_capacity}%; background: {battery_color}; transition: width 0.5s ease;"></div>
                            </div>
                            
                            <div style="background: #181825; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px;">
                                    <div style="margin-bottom: 8px;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Power Source</div>
                                        <div style="color: #89b4fa; font-weight: 500;">{'Charger Connected' if is_plugged else 'On Battery'}</div>
                                    </div>
                                    
                                    <div style="margin-bottom: 8px;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Health Status</div>
                                        <div style="color: {health_color}; font-weight: 500;">
                                            {f'{health_percent}%' if health_percent is not None else 'N/A'}
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 8px;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Cycle Count</div>
                                        <div style="color: #89b4fa; font-weight: 500;">{cycle_count}</div>
                                    </div>
                                    
                                    <div style="margin-bottom: 8px;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Full Charge</div>
                                        <div style="color: #89b4fa; font-weight: 500;">
                                            {format_mah(battery_health.get('FullChargeCapacity', battery_health.get('BatteryMaxCapacity')))}
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 0;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Design Capacity</div>
                                        <div style="color: #89b4fa; font-weight: 500;">
                                            {format_mah(battery_health.get('DesignCapacity', battery_health.get('BatteryDesignCapacity')))}
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 0;">
                                        <div style="color: #a6adc8; font-size: 0.9em;">Diagnostic Status</div>
                                        <div style="color: #89b4fa; font-weight: 500;">
                                            {battery_health.get('Status', 'N/A')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="color: #a6adc8; font-size: 0.85em; text-align: center; margin-top: 10px;">
                                {f"Temperature: {battery_health.get('BatteryTemperature', 'N/A')}°C" if 'BatteryTemperature' in battery_health else ''}
                            </div>
                        </div>
                        """
                        
                        # Format the final HTML
                        html_content = html_template.format(battery_info=battery_content)
                        
                        # Use show_info to display the battery info
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self,
                            "show_info",
                            Qt.QueuedConnection,
                            Q_ARG(str, "Battery Diagnostics"),
                            Q_ARG(str, html_content)
                        )
                    else:
                        error_msg = f"Failed to get battery info: {result.stderr}"
                        self.signal_emitter.update_signal.emit(error_msg)
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self,
                            "show_info",
                            Qt.QueuedConnection,
                            Q_ARG(str, "Error"),
                            Q_ARG(str, error_msg)
                        )
                except Exception as e:
                    error_msg = f"Error getting battery info: {str(e)}"
                    self.signal_emitter.update_signal.emit(error_msg)
                    QMetaObject.invokeMethod(progress, "close")
                    QMetaObject.invokeMethod(
                        self,
                        "show_info",
                        Qt.QueuedConnection,
                        Q_ARG(str, "Error"),
                        Q_ARG(str, error_msg)
                    )
            
            # Start the battery diagnostics in a separate thread
            thread = threading.Thread(target=battery_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.show_info("Error", f"Error running battery diagnostics: {str(e)}")
    
    def show_system_info(self):
        """Show system information about the connected iOS device"""
        try:
            # Show progress dialog
            progress = QProgressDialog("Gathering system information...", "Cancel", 0, 0, self)
            progress.setWindowTitle("System Information")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            def system_info_thread():
                try:
                    # Get system information using ideviceinfo
                    result = subprocess.run(
                        ["ideviceinfo"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        # Parse system information
                        sys_info = {}
                        for line in result.stdout.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                sys_info[key.strip()] = value.strip()
                        
                        # Format the system information for display
                        info_text = "<h3>System Information</h3><br>"
                        for key, value in sys_info.items():
                            info_text += f"<b>{key}:</b> {value}<br>"
                        
                        # Update UI on the main thread
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self,
                            "show_info",
                            Qt.QueuedConnection,
                            Q_ARG(str, "System Information"),
                            Q_ARG(str, info_text)
                        )
                    else:
                        error_msg = f"Failed to get system info: {result.stderr}"
                        self.signal_emitter.update_signal.emit(error_msg)
                        QMetaObject.invokeMethod(progress, "close")
                        QMetaObject.invokeMethod(
                            self,
                            "show_info",
                            Qt.QueuedConnection,
                            Q_ARG(str, "Error"),
                            Q_ARG(str, error_msg)
                        )
                except Exception as e:
                    error_msg = f"Error getting system info: {str(e)}"
                    self.signal_emitter.update_signal.emit(error_msg)
                    QMetaObject.invokeMethod(progress, "close")
                    QMetaObject.invokeMethod(
                        self,
                        "show_info",
                        Qt.QueuedConnection,
                        Q_ARG(str, "Error"),
                        Q_ARG(str, error_msg)
                    )
            
            # Start the system info gathering in a separate thread
            thread = threading.Thread(target=system_info_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.show_info("Error", f"Error gathering system information: {str(e)}")
    
    def _add_system_tools_widgets(self, layout):
        """Add system tools widgets to the layout"""
        # Battery Diagnostics button
        battery_btn = QPushButton("Battery Diagnostics")
        battery_btn.clicked.connect(self.battery_diagnostics)
        layout.addWidget(battery_btn)
        
        # System Info button
        sysinfo_btn = QPushButton("System Information")
        sysinfo_btn.clicked.connect(self.show_system_info)
        layout.addWidget(sysinfo_btn)
    
    def view_device_logs(self):
        """View device system logs in a dialog"""
        try:
            # Create a dialog to display logs
            log_dialog = QDialog(self)
            log_dialog.setWindowTitle("Device Logs")
            log_dialog.setMinimumSize(800, 600)
            
            # Create layout
            layout = QVBoxLayout(log_dialog)
            
            # Add filter controls
            filter_layout = QHBoxLayout()
            
            # Filter input
            filter_label = QLabel("Filter:")
            filter_input = QLineEdit()
            filter_input.setPlaceholderText("Enter text to filter logs...")
            
            # Level filter
            level_label = QLabel("Level:")
            level_combo = QComboBox()
            level_combo.addItems(["All", "Error", "Warning", "Info", "Debug"])
            
            # Apply filter button
            apply_btn = QPushButton("Apply Filter")
            
            filter_layout.addWidget(filter_label)
            filter_layout.addWidget(filter_input)
            filter_layout.addWidget(level_label)
            filter_layout.addWidget(level_combo)
            filter_layout.addWidget(apply_btn)
            filter_layout.addStretch()
            
            # Add clear button
            clear_btn = QPushButton("Clear")
            filter_layout.addWidget(clear_btn)
            
            # Add filter layout to main layout
            layout.addLayout(filter_layout)
            
            # Create text area for logs
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setFont(QFont("Monospace", 10))
            layout.addWidget(log_text)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(log_dialog.reject)
            
            # Add save button
            save_btn = QPushButton("Save to File...")
            save_btn.clicked.connect(lambda: self._save_logs_to_file(log_text.toPlainText()))
            button_box.addButton(save_btn, QDialogButtonBox.ActionRole)
            
            # Add pause/resume button
            self.log_paused = False
            pause_btn = QPushButton("Pause")
            pause_btn.clicked.connect(lambda: self._toggle_log_pause(pause_btn))
            button_box.addButton(pause_btn, QDialogButtonBox.ActionRole)
            
            layout.addWidget(button_box)
            
            # Function to update logs
            def update_logs():
                if not self.log_paused:
                    try:
                        # Get logs from device
                        result = subprocess.run(
                            ["idevicesyslog"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            log_text.setPlainText(result.stdout)
                            # Auto-scroll to bottom
                            log_text.verticalScrollBar().setValue(
                                log_text.verticalScrollBar().maximum()
                            )
                    except Exception as e:
                        log_text.append(f"Error getting logs: {str(e)}")
                
                # Schedule next update
                QTimer.singleShot(2000, update_logs)
            
            # Start log updates
            update_logs()
            
            # Show the dialog
            log_dialog.exec()
            
        except Exception as e:
            self.show_info("Error", f"Error viewing device logs: {str(e)}")
    
    def _toggle_log_pause(self, button):
        """Toggle log pausing"""
        self.log_paused = not self.log_paused
        button.setText("Resume" if self.log_paused else "Pause")
    
    def _save_logs_to_file(self, log_text):
        """Save logs to a file"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self,
                "Save Logs",
                "device_logs.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(log_text)
                self.show_info("Success", f"Logs saved to {file_path}")
        except Exception as e:
            self.show_info("Error", f"Error saving logs: {str(e)}")
    
    def _add_debugging_widgets(self, layout):
        """Add debugging widgets to the layout"""
        # Take Screenshot button
        screenshot_btn = QPushButton("Take Screenshot")
        screenshot_btn.clicked.connect(self.take_screenshot)
        layout.addWidget(screenshot_btn)
        
        # View Logs button
        logs_btn = QPushButton("View Device Logs")
        logs_btn.clicked.connect(self.view_device_logs)
        layout.addWidget(logs_btn)
    
    def _add_file_operations_widgets(self, layout):
        """Add file operation widgets to the layout"""
        # Quick Backup button
        quick_backup_btn = QPushButton("Quick Backup")
        quick_backup_btn.clicked.connect(lambda: self._perform_backup("quick"))
        layout.addWidget(quick_backup_btn)
        
        # Full Backup button
        full_backup_btn = QPushButton("Full Backup")
        full_backup_btn.clicked.connect(lambda: self._perform_backup("full"))
        layout.addWidget(full_backup_btn)
        
        # Restore Backup button
        restore_btn = QPushButton("Restore Backup")
        restore_btn.clicked.connect(self._restore_backup)
        layout.addWidget(restore_btn)
    
    def check_encryption(self):
        """Check if the device's data is encrypted"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        try:
            # Check if device is encrypted using ideviceinfo
            result = subprocess.run(
                ["ideviceinfo", "-k", "DataProtectionEnabled"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                encrypted = result.stdout.strip() == "true"
                status = "Encrypted" if encrypted else "Not Encrypted"
                self.show_info("Encryption Status", 
                              f"Device encryption status: {status}")
            else:
                # Try alternative method if the first one fails
                result = subprocess.run(
                    ["ideviceinfo", "-k", "DeviceName"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.show_info("Encryption Status", 
                                  "Could not determine encryption status. This device may not support encryption checking.")
                else:
                    self.show_info("Error", "Failed to check encryption status. Make sure the device is connected and trusted.")
        except Exception as e:
            self.show_info("Error", f"Error checking encryption: {str(e)}")
    
    def view_certificates(self):
        """View device certificates and provisioning profiles"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        try:
            # Create a dialog to display certificates
            cert_dialog = QDialog(self)
            cert_dialog.setWindowTitle("Device Certificates")
            cert_dialog.setMinimumSize(800, 600)
            
            # Create layout
            layout = QVBoxLayout(cert_dialog)
            
            # Add tab widget for different certificate types
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)
            
            # Tab for provisioning profiles
            profiles_widget = QWidget()
            profiles_layout = QVBoxLayout(profiles_widget)
            
            # Tab for device certificates
            device_certs_widget = QWidget()
            device_certs_layout = QVBoxLayout(device_certs_widget)
            
            # Create text areas for each tab
            profiles_text = QTextEdit()
            profiles_text.setReadOnly(True)
            profiles_text.setFont(QFont("Monospace", 10))
            profiles_layout.addWidget(profiles_text)
            
            device_certs_text = QTextEdit()
            device_certs_text.setReadOnly(True)
            device_certs_text.setFont(QFont("Monospace", 10))
            device_certs_layout.addWidget(device_certs_text)
            
            # Add tabs
            tab_widget.addTab(profiles_widget, "Provisioning Profiles")
            tab_widget.addTab(device_certs_widget, "Device Certificates")
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(cert_dialog.reject)
            
            # Add save button
            save_btn = QPushButton("Save to File...")
            save_btn.clicked.connect(lambda: self._save_certificates_to_file(
                profiles_text.toPlainText(), device_certs_text.toPlainText())
            )
            button_box.addButton(save_btn, QDialogButtonBox.ActionRole)
            
            layout.addWidget(button_box)
            
            # Show progress dialog while fetching certificates
            progress = QProgressDialog("Retrieving certificates...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Fetching Certificates")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Function to fetch certificates in a separate thread
            def fetch_certificates():
                try:
                    # Get device UDID
                    udid = self.device_info.get('udid', '')
                    
                    # Get provisioning profiles
                    profiles_result = subprocess.run(
                        ['ideviceprovision', '-u', udid, 'list'],
                        capture_output=True,
                        text=True
                    )
                    
                    if profiles_result.returncode == 0:
                        profiles_text.setText(profiles_result.stdout)
                        
                        # Try to get more detailed info for each profile
                        try:
                            # Parse profile IDs
                            profile_ids = []
                            for line in profiles_result.stdout.split('\n'):
                                if line.strip():
                                    parts = line.split(': ')
                                    if len(parts) > 1:
                                        profile_ids.append(parts[1].strip())
                            
                            # Get details for each profile
                            for profile_id in profile_ids:
                                detail_result = subprocess.run(
                                    ['ideviceprovision', '-u', udid, 'dump', profile_id],
                                    capture_output=True,
                                    text=True
                                )
                                if detail_result.returncode == 0:
                                    profiles_text.append("\n\n--- PROFILE DETAILS ---\n")
                                    profiles_text.append(detail_result.stdout)
                        except Exception as e:
                            profiles_text.append(f"\nError getting profile details: {str(e)}")
                    else:
                        profiles_text.setText(f"Error getting provisioning profiles: {profiles_result.stderr}")
                    
                    # Get device certificates
                    certs_result = subprocess.run(
                        ['ideviceinfo', '-u', udid, '-q', 'com.apple.mobilesigner'],
                        capture_output=True,
                        text=True
                    )
                    
                    if certs_result.returncode == 0:
                        device_certs_text.setText(certs_result.stdout)
                    else:
                        # Try alternative certificate method
                        alt_certs_result = subprocess.run(
                            ['ideviceinfo', '-u', udid, '-x'],
                            capture_output=True,
                            text=True
                        )
                        
                        if alt_certs_result.returncode == 0:
                            # Find certificate sections in the XML output
                            cert_sections = []
                            lines = alt_certs_result.stdout.split('\n')
                            in_cert_section = False
                            current_section = []
                            
                            for line in lines:
                                if "<key>CertificateInfo</key>" in line or "<key>ProvisioningProfiles</key>" in line:
                                    in_cert_section = True
                                    current_section = [line]
                                elif in_cert_section:
                                    current_section.append(line)
                                    if "</dict>" in line:
                                        in_cert_section = False
                                        cert_sections.append("\n".join(current_section))
                            
                            if cert_sections:
                                device_certs_text.setText("\n\n".join(cert_sections))
                            else:
                                device_certs_text.setText("No certificate information found in device info.")
                        else:
                            device_certs_text.setText(f"Error getting device certificates: {alt_certs_result.stderr}")
                    
                except Exception as e:
                    profiles_text.setText(f"Error retrieving certificates: {str(e)}")
                    device_certs_text.setText("Certificate retrieval failed. See provisioning profiles tab for details.")
                finally:
                    # Close progress dialog
                    QMetaObject.invokeMethod(progress, "cancel")
            
            # Start fetching certificates in a separate thread
            thread = threading.Thread(target=fetch_certificates, daemon=True)
            thread.start()
            
            # Show the dialog
            cert_dialog.exec()
            
        except Exception as e:
            self.show_info("Error", f"Failed to view certificates: {str(e)}")

    def _save_certificates_to_file(self, profiles_text, certs_text):
        """Save certificates to a file"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self,
                "Save Certificates",
                "device_certificates.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write("=== PROVISIONING PROFILES ===\n\n")
                    f.write(profiles_text)
                    f.write("\n\n=== DEVICE CERTIFICATES ===\n\n")
                    f.write(certs_text)
                self.show_info("Success", f"Certificates saved to {file_path}")
        except Exception as e:
            self.show_info("Error", f"Error saving certificates: {str(e)}")

    def _add_security_widgets(self, layout):
        """Add security widgets to the layout"""
        # Check Encryption button
        encrypt_btn = QPushButton("Check Encryption")
        encrypt_btn.clicked.connect(self.check_encryption)
        layout.addWidget(encrypt_btn)
        
        # View Certificates button
        certs_btn = QPushButton("View Certificates")
        certs_btn.clicked.connect(self.view_certificates)
        layout.addWidget(certs_btn)
    
    def run_script(self):
        """Run a custom script on the connected device"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        # Open file dialog to select script
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Script to Run",
            "",
            "Shell Scripts (*.sh);;Python Scripts (*.py);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
            
        try:
            # Make script executable if it's a shell script
            if file_path.endswith('.sh'):
                os.chmod(file_path, 0o755)
            
            # Show progress dialog
            progress = QProgressDialog("Running script...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Running Script")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Run the script in a separate thread
            self.script_thread = threading.Thread(
                target=self._run_script_task,
                args=(file_path, progress)
            )
            self.script_thread.daemon = True
            self.script_thread.start()
            
        except Exception as e:
            self.show_info("Error", f"Failed to run script: {str(e)}")
    
    def _run_script_task(self, script_path, progress_dialog):
        """Worker thread to run the selected script"""
        try:
            # Run the script
            if script_path.endswith('.py'):
                result = subprocess.run(
                    ["python3", script_path],
                    capture_output=True,
                    text=True
                )
            else:  # Shell script
                result = subprocess.run(
                    [script_path],
                    shell=True,
                    capture_output=True,
                    text=True
                )
            
            # Show results
            output = result.stdout if result.stdout else "No output"
            error = result.stderr if result.stderr else "No errors"
            
            # Update UI on main thread
            QMetaObject.invokeMethod(self, "_show_script_results", 
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Script Completed"),
                                   Q_ARG(str, f"Output:\n{output}\n\nErrors:\n{error}"))
            
        except Exception as e:
            QMetaObject.invokeMethod(self, "_show_script_results",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Script Error"),
                                   Q_ARG(str, f"Failed to run script: {str(e)}"))
        finally:
            progress_dialog.cancel()
    
    def _show_script_results(self, title, message):
        """Show script execution results in a dialog"""
        self.show_info(title, message)

    def record_actions(self):
        """Start/stop recording user actions on the iOS device"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        if not hasattr(self, 'is_recording'):
            self.is_recording = False
            self.recorded_actions = []
        
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.recorded_actions = []
            self.record_start_time = time.time()
            
            # Update UI in the main thread
            QMetaObject.invokeMethod(
                self.record_button, "setText",
                Qt.QueuedConnection,
                Q_ARG(str, "Stop Recording")
            )
            
            # Start the recording thread
            self.recording_thread = threading.Thread(target=self._record_actions_thread, daemon=True)
            self.recording_thread.start()
            
            self.show_info("Recording Started", 
                         "Recording device actions. Perform the actions you want to automate on your device.")
        else:
            # Stop recording
            self.is_recording = False
            
            # Update UI in the main thread
            QMetaObject.invokeMethod(
                self.record_button, "setText",
                Qt.QueuedConnection,
                Q_ARG(str, "Record Actions")
            )
            
            if not self.recorded_actions:
                self.show_info("Recording Complete", "No actions were recorded.")
                return
                
            # Ask user if they want to save the recording
            reply = QMessageBox.question(
                self,
                "Save Recording",
                f"Recorded {len(self.recorded_actions)} actions. Save as script?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self._save_recorded_actions()
    
    def _record_actions_thread(self):
        """Background thread to record iOS device actions"""
        try:
            # Set up idevicelistener (using CLI tool for libimobiledevice)
            cmd = ['idevicedebug', 'run', '--debug']
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Process events while recording
            while self.is_recording:
                # Read a line from the process output
                line = process.stdout.readline()
                if not line:
                    # Check if process is still alive
                    if process.poll() is not None:
                        break
                    continue
                
                # Process the line and extract action
                action = self._parse_device_action(line)
                if action:
                    # Add the action to our list
                    self.recorded_actions.append(action)
                    
                    # Log the action in the main thread
                    QMetaObject.invokeMethod(
                        self,
                        "log_message",
                        Qt.QueuedConnection,
                        Q_ARG(str, f"Recorded action: {action['type']}")
                    )
            
            # Clean up the process
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                
        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Error in recording thread: {str(e)}")
            )
        
        def _parse_device_action(self, log_line):
            """Parse device debug output and convert to actionable events"""
            try:
                # This is a simplified example - actual implementation would be more complex
                # and depends on the output format of idevicedebug
                
                # Sample patterns to look for
                action = None
                timestamp = time.time() - self.record_start_time
                
                # Touch events
                if "TouchEvent" in log_line:
                    match = re.search(r'TouchEvent\s+at\s+\((\d+),(\d+)\)', log_line)
                    if match:
                        x, y = match.groups()
                        action = {
                            'type': 'touch',
                            'timestamp': timestamp,
                            'details': {'x': int(x), 'y': int(y)},
                            'command': f"tap_screen({x}, {y})"
                        }
                
                # App launch events
                elif "ApplicationDidFinishLaunching" in log_line:
                    match = re.search(r'Bundle identifier: ([\w\.]+)', log_line)
                    if match:
                        bundle_id = match.group(1)
                        action = {
                            'type': 'app_launch',
                            'timestamp': timestamp,
                            'details': {'bundle_id': bundle_id},
                            'command': f"launch_app('{bundle_id}')"
                        }
                
                # Rotation events
                elif "DeviceOrientationDidChange" in log_line:
                    orientations = {
                        "UIDeviceOrientationPortrait": "portrait",
                        "UIDeviceOrientationLandscapeLeft": "landscape_left",
                        "UIDeviceOrientationLandscapeRight": "landscape_right",
                        "UIDeviceOrientationPortraitUpsideDown": "portrait_upside_down"
                    }
                    
                    for orientation_key, orientation_value in orientations.items():
                        if orientation_key in log_line:
                            action = {
                                'type': 'rotation',
                                'timestamp': timestamp,
                                'details': {'orientation': orientation_value},
                                'command': f"set_orientation('{orientation_value}')"
                            }
                            break
                
                # Button press events
                elif "UIButton pressed" in log_line:
                    match = re.search(r'Button: "([^"]+)"', log_line)
                    if match:
                        button_text = match.group(1)
                        action = {
                            'type': 'button_press',
                            'timestamp': timestamp,
                            'details': {'text': button_text},
                            'command': f"press_button_with_text('{button_text}')"
                        }
                
                # Text input events
                elif "UITextField" in log_line and "text changed" in log_line:
                    match = re.search(r'Text: "([^"]*)"', log_line)
                    if match:
                        text = match.group(1)
                        action = {
                            'type': 'text_input',
                            'timestamp': timestamp,
                            'details': {'text': text},
                            'command': f"input_text('{text}')"
                        }
                
                return action
            except Exception as e:
                self.log_message(f"Error parsing action: {str(e)}")
                return None
        
        def _save_recorded_actions(self):
            """Save the recorded actions to a script file"""
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self,
                "Save Recorded Actions",
                f"ios_actions_{int(time.time())}.py",
                "Python Scripts (*.py);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
                
            try:
                with open(file_path, 'w') as f:
                    f.write("#!/usr/bin/env python3\n")
                    f.write("# iOS Actions Recording\n")
                    f.write(f"# Generated on: {time.ctime()}\n")
                    f.write(f"# Total actions: {len(self.recorded_actions)}\n\n")
                    
                    f.write("import time\n")
                    f.write("import subprocess\n\n")
                    
                    # Write helper functions
                    f.write("def tap_screen(x, y):\n")
                    f.write("    \"\"\"Tap at coordinates on the screen\"\"\"\n")
                    f.write("    subprocess.run(['idevicesimulate', 'touch', str(x), str(y)])\n\n")
                    
                    f.write("def launch_app(bundle_id):\n")
                    f.write("    \"\"\"Launch an app by bundle ID\"\"\"\n")
                    f.write("    subprocess.run(['idevicedebug', 'run', bundle_id])\n\n")
                    
                    f.write("def set_orientation(orientation):\n")
                    f.write("    \"\"\"Set device orientation\"\"\"\n")
                    f.write("    subprocess.run(['idevicesimulate', 'orientation', orientation])\n\n")
                    
                    f.write("def press_button_with_text(text):\n")
                    f.write("    \"\"\"Press a button by its text\"\"\"\n")
                    f.write("    subprocess.run(['idevicesimulate', 'button', f\"text={text}\"])\n\n")
                    
                    f.write("def input_text(text):\n")
                    f.write("    \"\"\"Input text into the focused field\"\"\"\n")
                    f.write("    subprocess.run(['idevicesimulate', 'input', text])\n\n")
                    
                    f.write("def run_actions():\n")
                    f.write("    \"\"\"Run the recorded actions\"\"\"\n")
                    
                    # Write each action
                    last_timestamp = 0
                    for i, action in enumerate(self.recorded_actions, 1):
                        f.write(f"    # Action {i}: {action['type']}\n")
                        
                        # Calculate delay between actions
                        if i > 1:
                            delay = action['timestamp'] - last_timestamp
                            f.write(f"    time.sleep({delay:.2f})  # Wait {delay:.2f} seconds\n")
                        
                        # Write the command for this action
                        f.write(f"    print(\"Executing: {action['type']}\")\n")
                        f.write(f"    {action['command']}\n\n")
                        
                        last_timestamp = action['timestamp']
                    
                    f.write("if __name__ == \"__main__\":\n")
                    f.write("    print(\"Running iOS device action script\")\n")
                    f.write("    run_actions()\n")
                    f.write("    print(\"Script completed\")\n")
                
                # Make the file executable
                os.chmod(file_path, 0o755)
                self.show_info("Success", f"Actions saved to:\n{file_path}")
                
            except Exception as e:
                self.show_info("Error", f"Failed to save actions: {str(e)}")
                
    def _add_automation_widgets(self, layout):
        """Add automation widgets to the layout"""
        # Run Script button
        script_btn = QPushButton("Run Script")
        script_btn.clicked.connect(self.run_script)
        layout.addWidget(script_btn)
        
        # Record Actions button
        self.record_button = QPushButton("Record Actions")
        self.record_button.clicked.connect(self.record_actions)
        layout.addWidget(self.record_button)
    
    def run_diagnostics(self):
        """Run comprehensive diagnostics on the connected iOS device"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        # Show progress dialog
        progress = QProgressDialog("Running diagnostics...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Device Diagnostics")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Run diagnostics in a separate thread
        self.diag_thread = threading.Thread(
            target=self._run_diagnostics_task,
            args=(progress,)
        )
        self.diag_thread.daemon = True
        self.diag_thread.start()
    
    def _run_diagnostics_task(self, progress_dialog):
        """Worker thread to run device diagnostics"""
        try:
            results = []
            
            # 1. Check basic device info
            QMetaObject.invokeMethod(self, "_update_diagnostic_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Checking device information..."))
            
            device_info = self._get_device_info()
            results.append(("Device Information", "Success" if device_info else "Failed"))
            
            # 2. Check battery status
            QMetaObject.invokeMethod(self, "_update_diagnostic_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Checking battery status..."))
            
            battery_ok = self._check_battery_status()
            results.append(("Battery Status", "OK" if battery_ok else "Issues found"))
            
            # 3. Check storage
            QMetaObject.invokeMethod(self, "_update_diagnostic_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Checking storage..."))
            
            storage_ok = self._check_storage()
            results.append(("Storage", "OK" if storage_ok else "Issues found"))
            
            # 4. Run basic connectivity tests
            QMetaObject.invokeMethod(self, "_update_diagnostic_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Testing connectivity..."))
            
            connectivity_ok = self._test_connectivity()
            results.append(("Connectivity", "OK" if connectivity_ok else "Issues found"))
            
            # Prepare results summary
            summary = "\n".join([f"{test}: {result}" for test, result in results])
            
            # Show results
            QMetaObject.invokeMethod(self, "_show_diagnostic_results",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Diagnostics Complete"),
                                   Q_ARG(str, summary))
            
        except Exception as e:
            QMetaObject.invokeMethod(self, "_show_diagnostic_results",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Diagnostics Error"),
                                   Q_ARG(str, f"Error running diagnostics: {str(e)}"))
        finally:
            progress_dialog.cancel()
    
    def _get_device_info(self):
        """Get basic device information"""
        try:
            result = subprocess.run(
                ["ideviceinfo"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            return False
    
    def _check_battery_status(self):
        """Check battery status and health"""
        try:
            result = subprocess.run(
                ["idevicediagnostics", "diagnostics"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_storage(self):
        """Check device storage status"""
        try:
            result = subprocess.run(
                ["ideviceinfo", "-k", "TotalDataCapacity"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            return False
    
    def _test_connectivity(self):
        """Test basic device connectivity"""
        try:
            # Test basic device connection
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            return False
    
    @Slot(str)
    def _update_diagnostic_status(self, message):
        """Update the diagnostic status message (runs in main thread)"""
        # This method is called via invokeMethod to update the UI from the worker thread
        self.log_message(message)
    
    @Slot(str, str)
    def _show_diagnostic_results(self, title, message):
        """Show diagnostic results in a dialog"""
        self.show_info(title, message)

    def run_performance_test(self):
        """Run performance tests on the connected iOS device"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
            
        # Show progress dialog
        progress = QProgressDialog("Running performance tests...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Performance Test")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Run performance test in a separate thread
        self.perf_thread = threading.Thread(
            target=self._run_performance_test_task,
            args=(progress,)
        )
        self.perf_thread.daemon = True
        self.perf_thread.start()
    
    def _run_performance_test_task(self, progress_dialog):
        """Worker thread to run performance tests"""
        try:
            results = []
            
            # Update progress
            QMetaObject.invokeMethod(progress_dialog, "setValue",
                                   Qt.QueuedConnection,
                                   Q_ARG(int, 10))
            
            # 1. Test CPU performance
            QMetaObject.invokeMethod(self, "_update_performance_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Testing CPU performance..."))
            
            cpu_score = self._test_cpu_performance()
            results.append(("CPU Performance", f"{cpu_score:.1f} ops/sec"))
            
            # Update progress
            QMetaObject.invokeMethod(progress_dialog, "setValue",
                                   Qt.QueuedConnection,
                                   Q_ARG(int, 40))
            
            # 2. Test I/O performance
            QMetaObject.invokeMethod(self, "_update_performance_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Testing I/O performance..."))
            
            io_score = self._test_io_performance()
            results.append(("I/O Performance", f"{io_score:.1f} MB/s"))
            
            # Update progress
            QMetaObject.invokeMethod(progress_dialog, "setValue",
                                   Qt.QueuedConnection,
                                   Q_ARG(int, 70))
            
            # 3. Test memory performance
            QMetaObject.invokeMethod(self, "_update_performance_status",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Testing memory performance..."))
            
            mem_score = self._test_memory_performance()
            results.append(("Memory Performance", f"{mem_score:.1f} MB/s"))
            
            # Calculate overall score (weighted average)
            overall_score = (cpu_score * 0.4) + (io_score * 0.3) + (mem_score * 0.3)
            results.append(("Overall Score", f"{overall_score:.1f}/100"))
            
            # Prepare results summary
            summary = "Performance Test Results:\n\n"
            summary += "\n".join([f"{test}: {result}" for test, result in results])
            
            # Show results
            QMetaObject.invokeMethod(self, "_show_performance_results",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Performance Test Complete"),
                                   Q_ARG(str, summary))
            
        except Exception as e:
            QMetaObject.invokeMethod(self, "_show_performance_results",
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "Performance Test Error"),
                                   Q_ARG(str, f"Error running performance test: {str(e)}"))
        finally:
            progress_dialog.setValue(100)
            progress_dialog.cancel()
    
    def _test_cpu_performance(self):
        """Test CPU performance with a simple calculation"""
        try:
            # This is a simple CPU benchmark - in a real app, you'd use a more sophisticated test
            start_time = time.time()
            count = 0
            while time.time() - start_time < 2:  # Run for 2 seconds
                # Perform some CPU-intensive calculations
                _ = [i * i for i in range(10000)]
                count += 1
            
            # Score is based on operations per second (higher is better)
            return min(100, count * 10)  # Cap at 100
            
        except Exception:
            return 0
    
    def _test_io_performance(self):
        """Test I/O performance with file operations"""
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            test_file = os.path.join(temp_dir, "io_test.bin")
            
            # Write test data (1MB)
            data = b'0' * (1024 * 1024)
            
            start_time = time.time()
            
            # Write test
            with open(test_file, 'wb') as f:
                for _ in range(10):  # Write 10MB total
                    f.write(data)
            
            # Read test
            with open(test_file, 'rb') as f:
                while f.read(1024 * 1024):  # Read in 1MB chunks
                    pass
            
            elapsed = time.time() - start_time
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            # Score is based on MB/s (higher is better)
            mb_per_sec = 20.0 / elapsed if elapsed > 0 else 0
            return min(100, mb_per_sec * 5)  # Cap at 100
            
        except Exception:
            return 0
    
    def _test_memory_performance(self):
        """Test memory performance with allocation and access"""
        try:
            # Allocate and manipulate a large array
            size = 5_000_000  # 5 million elements
            arr = array.array('i', range(size))
            
            start_time = time.time()
            
            # Perform some memory operations
            for _ in range(10):
                # Random access
                for _ in range(1000):
                    idx = random.randint(0, size - 1)
                    arr[idx] = arr[(idx + 1) % size]
                
                # Sequential access
                for i in range(1, size):
                    arr[i-1] = arr[i]
            
            elapsed = time.time() - start_time
            
            # Score is based on operations per second (higher is better)
            ops_per_sec = (size * 11) / elapsed if elapsed > 0 else 0
            return min(100, ops_per_sec / 100000)  # Scale to 0-100 range
            
        except Exception:
            return 0
    
    def _update_performance_status(self, message):
        """Update the performance test status message"""
        # This method is called via invokeMethod to update the UI from the worker thread
        self.log_message(message)
    
    def _show_performance_results(self, title, message):
        """Show performance test results in a dialog"""
        self.show_info(title, message)

    def _add_advanced_tests_widgets(self, layout):
        """Add advanced test widgets to the layout"""
        # Run Diagnostics button
        diag_btn = QPushButton("Run Diagnostics")
        diag_btn.clicked.connect(self.run_diagnostics)
        layout.addWidget(diag_btn)
        
        # Performance Test button
        perf_btn = QPushButton("Performance Test")
        perf_btn.clicked.connect(self.run_performance_test)
        layout.addWidget(perf_btn)
    
    def _add_ios_tools_widgets(self, layout):
        """Add iOS-specific tools to the layout"""
        # Create a grid layout for better organization
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row counter
        row = 0
        
        # ===== Section: Device Management =====
        dev_group = QGroupBox("Device Management")
        dev_layout = QVBoxLayout()
        
        # Device Date
        date_btn = QPushButton("Get/Set Device Date")
        date_btn.setToolTip("View or modify device date and time")
        date_btn.clicked.connect(self._manage_device_date)
        dev_layout.addWidget(date_btn)
        
        # Device Name
        name_btn = QPushButton("Get/Set Device Name")
        name_btn.setToolTip("View or modify device name")
        name_btn.clicked.connect(self._manage_device_name)
        dev_layout.addWidget(name_btn)
        
        # Check for Updates
        update_btn = QPushButton("Check for iOS Updates")
        update_btn.setToolTip("Check for available iOS updates")
        update_btn.clicked.connect(self._check_ios_updates)
        dev_layout.addWidget(update_btn)
        
        dev_group.setLayout(dev_layout)
        grid.addWidget(dev_group, row, 0)
        
        # ===== Section: Developer Tools =====
        dev_tools_group = QGroupBox("Developer Tools")
        dev_tools_layout = QVBoxLayout()
        
        # Developer Mode Toggle
        dev_mode_btn = QPushButton("Toggle Developer Mode")
        dev_mode_btn.setToolTip("Enable/Disable developer mode on the device")
        dev_mode_btn.clicked.connect(self._toggle_developer_mode)
        dev_tools_layout.addWidget(dev_mode_btn)
        
        # Process List
        proc_btn = QPushButton("View Process List")
        proc_btn.setToolTip("List running processes (requires developer mode)")
        proc_btn.clicked.connect(self._show_process_list)
        dev_tools_layout.addWidget(proc_btn)
        
        # Device Capabilities
        caps_btn = QPushButton("View Device Capabilities")
        caps_btn.setToolTip("View detailed device capabilities")
        caps_btn.clicked.connect(self._show_device_capabilities)
        dev_tools_layout.addWidget(caps_btn)
        
        dev_tools_group.setLayout(dev_tools_layout)
        grid.addWidget(dev_tools_group, row, 1)
        row += 1
        
        # ===== Section: File Operations =====
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        # Mount/Unmount Filesystem
        mount_btn = QPushButton("Mount/Unmount Filesystem")
        mount_btn.setToolTip("Mount or unmount iOS filesystem")
        mount_btn.clicked.connect(self._toggle_mount)
        file_layout.addWidget(mount_btn)
        
        # Developer Disk Image
        disk_image_btn = QPushButton("Manage Disk Images")
        disk_image_btn.setToolTip("Mount/Unmount developer disk images")
        disk_image_btn.clicked.connect(self._manage_disk_images)
        file_layout.addWidget(disk_image_btn)
        
        # AFC Check
        afc_btn = QPushButton("Test AFC Connection")
        afc_btn.setToolTip("Test Apple File Conduit connection")
        afc_btn.clicked.connect(self._test_afc_connection)
        file_layout.addWidget(afc_btn)
        
        file_group.setLayout(file_layout)
        grid.addWidget(file_group, row, 0)
        
        # ===== Section: Backup & Restore =====
        backup_group = QGroupBox("Backup & Restore")
        backup_layout = QVBoxLayout()
        
        # Backup/Restore
        backup_btn = QPushButton("Backup/Restore Device")
        backup_btn.setToolTip("Create or restore device backups")
        backup_btn.clicked.connect(self._manage_backups)
        backup_layout.addWidget(backup_btn)
        
        # Save SHSH Blobs
        shsh_btn = QPushButton("Save SHSH Blobs")
        shsh_btn.setToolTip("Save SHSH blobs for downgrading (if possible)")
        shsh_btn.clicked.connect(self._save_shsh_blobs)
        backup_layout.addWidget(shsh_btn)
        
        backup_group.setLayout(backup_layout)
        grid.addWidget(backup_group, row, 1)
        row += 1
        
        # ===== Section: Diagnostics =====
        diag_group = QGroupBox("Diagnostics")
        diag_layout = QVBoxLayout()
        
        # Crash Reports
        crash_btn = QPushButton("Get Crash Reports")
        crash_btn.setToolTip("Retrieve crash reports from the device")
        crash_btn.clicked.connect(self._get_crash_reports)
        diag_layout.addWidget(crash_btn)
        
        # Syslog Viewer
        syslog_btn = QPushButton("View System Logs")
        syslog_btn.setToolTip("View device system logs")
        syslog_btn.clicked.connect(self._view_system_logs)
        diag_layout.addWidget(syslog_btn)
        
        diag_group.setLayout(diag_layout)
        grid.addWidget(diag_group, row, 0)
        
        # ===== Section: Notifications =====
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout()
        
        # Monitor Notifications
        monitor_btn = QPushButton("Monitor Notifications")
        monitor_btn.setToolTip("Monitor device notifications")
        monitor_btn.clicked.connect(lambda: self._monitor_notification(""))
        notif_layout.addWidget(monitor_btn)
        
        # Post Notification
        post_btn = QPushButton("Post Notification")
        post_btn.setToolTip("Post a notification to the device")
        post_btn.clicked.connect(self._post_notification)
        notif_layout.addWidget(post_btn)
        
        notif_group.setLayout(notif_layout)
        grid.addWidget(notif_group, row, 1)
        
        # Add the grid to the main layout
        layout.addLayout(grid)
        layout.addStretch()
    
    def _manage_device_date(self):
        """View or modify device date and time"""
        try:
            # Get current device date
            result = subprocess.run(
                ["idevicedate"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(self, "Error", "Failed to get device date")
                return
                
            current_date = result.stdout.strip()
            
            # Show current date and ask for new date
            new_date, ok = QInputDialog.getText(
                self,
                "Device Date",
                f"Current device date: {current_date}\n\nEnter new date (YYYY-MM-DD HH:MM:SS):",
                text=current_date
            )
            
            if ok and new_date and new_date != current_date:
                # Set new date on device
                result = subprocess.run(
                    ["idevicedate", "-s", new_date],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", f"Device date set to: {new_date}")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to set device date: {result.stderr}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _test_afc_connection(self):
        """Test Apple File Conduit connection"""
        try:
            self.status_var.setText("Testing AFC connection...")
            
            # Create a temporary directory for testing
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Try to list root directory via AFC
                result = subprocess.run(
                    ["ifuse", "--list-apps"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Try to access a test directory
                    test_result = subprocess.run(
                        ["ideviceinfo", "-k", "DeviceName"],
                        capture_output=True,
                        text=True
                    )
                    
                    if test_result.returncode == 0:
                        device_name = test_result.stdout.strip()
                        QMessageBox.information(
                            self,
                            "AFC Test",
                            f"AFC connection successful!\nDevice Name: {device_name}"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "AFC Test",
                            "AFC connection established but couldn't read device info"
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "AFC Test Failed",
                        "Could not establish AFC connection.\n\n"
                        "Make sure the device is trusted and unlocked.\n"
                        f"Error: {result.stderr}"
                    )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while testing AFC connection: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _toggle_mount(self):
        """Mount or unmount iOS filesystem"""
        try:
            # Check if already mounted
            mount_points = []
            try:
                with open("/proc/mounts", "r") as f:
                    for line in f:
                        if "/var/run/user/" in line and "ifuse" in line:
                            mount_points.append(line.split()[1])
            except Exception:
                pass
                
            if mount_points:
                # Unmount all ifuse mounts
                reply = QMessageBox.question(
                    self,
                    "Unmount Filesystem",
                    f"The iOS filesystem is currently mounted at:\n" + 
                    "\n".join(mount_points) + 
                    "\n\nDo you want to unmount it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    for mount_point in mount_points:
                        result = subprocess.run(
                            ["fusermount", "-u", mount_point],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            QMessageBox.information(
                                self,
                                "Success",
                                f"Successfully unmounted {mount_point}"
                            )
                        else:
                            QMessageBox.warning(
                                self,
                                "Error",
                                f"Failed to unmount {mount_point}: {result.stderr}"
                            )
            else:
                # Mount filesystem
                mount_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Mount Directory",
                    os.path.expanduser("~/")
                )
                
                if not mount_dir:
                    return
                    
                # Create mount directory if it doesn't exist
                os.makedirs(mount_dir, exist_ok=True)
                
                # Mount using ifuse
                self.status_var.setText("Mounting iOS filesystem...")
                result = subprocess.run(
                    ["ifuse", mount_dir],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Successfully mounted iOS filesystem at {mount_dir}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to mount iOS filesystem: {result.stderr}"
                    )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while mounting/unmounting filesystem: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _manage_device_name(self):
        """View or modify device name"""
        try:
            # Get current device name
            result = subprocess.run(
                ["ideviceinfo", "-k", "DeviceName"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(self, "Error", "Failed to get device name")
                return
                
            current_name = result.stdout.strip()
            
            # Show current name and ask for new name
            new_name, ok = QInputDialog.getText(
                self,
                "Device Name",
                f"Current device name: {current_name}\n\nEnter new device name:",
                text=current_name
            )
            
            if ok and new_name and new_name != current_name:
                # Set new device name
                result = subprocess.run(
                    ["ideviceinfo", "-s", f"DeviceName:{new_name}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", f"Device name set to: {new_name}")
                    self.update_device_info()  # Refresh device info
                else:
                    QMessageBox.warning(self, "Error", f"Failed to set device name: {result.stderr}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _check_ios_updates(self):
        """Check for available iOS updates"""
        try:
            self.status_var.setText("Checking for iOS updates...")
            
            # Create a dialog to show progress
            progress = QProgressDialog("Checking for iOS updates...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Checking Updates")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Run idevicerestore in a separate thread
            def check_updates():
                try:
                    result = subprocess.run(
                        ["idevicerestore", "-l", "-n"],
                        capture_output=True,
                        text=True,
                        timeout=30  # 30 seconds timeout
                    )
                    return result
                except subprocess.TimeoutExpired:
                    return None
                except Exception as e:
                    return str(e)
            
            # Start the thread
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(check_updates)
                
                # Wait for the thread to complete or be cancelled
                while not future.done():
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        future.cancel()
                        break
                    time.sleep(0.1)
                
                if future.done() and not future.cancelled():
                    result = future.result()
                    progress.cancel()
                    
                    if isinstance(result, str):
                        # Error occurred
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Failed to check for updates: {result}"
                        )
                    elif result is None:
                        QMessageBox.warning(
                            self,
                            "Timeout",
                            "The update check timed out. Please try again."
                        )
                    else:
                        # Show update information
                        dialog = QDialog(self)
                        dialog.setWindowTitle("Available iOS Updates")
                        dialog.setMinimumSize(600, 400)
                        
                        layout = QVBoxLayout()
                        
                        # Add text area for update info
                        text_edit = QTextEdit()
                        text_edit.setReadOnly(True)
                        text_edit.setFont(QFont("Monospace"))
                        text_edit.setText(result.stdout or "No updates available")
                        
                        # Add buttons
                        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
                        button_box.accepted.connect(dialog.accept)
                        
                        layout.addWidget(QLabel("Available iOS Updates:"))
                        layout.addWidget(text_edit)
                        layout.addWidget(button_box)
                        
                        dialog.setLayout(layout)
                        dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while checking for updates: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _toggle_developer_mode(self):
        """Toggle developer mode on the device"""
        try:
            # Check current developer mode status
            result = subprocess.run(
                ["idevicedebug", "help"],  # Just a test command to check if developer mode is enabled
                capture_output=True,
                text=True
            )
            
            # If the command fails, developer mode might be disabled
            if result.returncode != 0 and "Developer mode is not enabled" in result.stderr:
                # Developer mode is disabled, prompt to enable it
                reply = QMessageBox.question(
                    self,
                    "Developer Mode Disabled",
                    "Developer mode is currently disabled. Would you like to enable it?\n\n"
                    "Note: You may need to trust this computer on your device.",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Try to enable developer mode
                    self.status_var.setText("Enabling developer mode...")
                    result = subprocess.run(
                        ["idevicedebug", "enable-developer-mode"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(
                            self,
                            "Success",
                            "Developer mode has been enabled.\n\n"
                            "Please check your device to trust this computer "
                            "if prompted, then restart any developer tools."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Failed to enable developer mode:\n{result.stderr}"
                        )
            else:
                # Developer mode is enabled, offer to disable it
                reply = QMessageBox.question(
                    self,
                    "Developer Mode Enabled",
                    "Developer mode is currently enabled. Would you like to disable it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.status_var.setText("Disabling developer mode...")
                    result = subprocess.run(
                        ["idevicedebug", "disable-developer-mode"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(
                            self,
                            "Success",
                            "Developer mode has been disabled."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Failed to disable developer mode:\n{result.stderr}"
                        )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while toggling developer mode: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _show_process_list(self):
        """Show list of running processes on the device"""
        try:
            self.status_var.setText("Fetching process list...")
            
            # Create a dialog to show the process list
            dialog = QDialog(self)
            dialog.setWindowTitle("Running Processes")
            dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout()
            
            # Add a search box
            search_box = QLineEdit()
            search_box.setPlaceholderText("Search processes...")
            
            # Add a table to display processes
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Memory"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.horizontalHeader().setStretchLastSection(True)
            table.setSortingEnabled(True)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            
            # Add a refresh button
            refresh_btn = QPushButton("Refresh")
            
            # Add widgets to layout
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("Search:"))
            search_layout.addWidget(search_box)
            search_layout.addWidget(refresh_btn)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            
            layout.addLayout(search_layout)
            layout.addWidget(table)
            layout.addWidget(button_box)
            
            def update_process_list():
                try:
                    # Get process list using idevicedebug
                    result = subprocess.run(
                        ["idevicedebug", "run", "ps", "aux"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Failed to get process list: {result.stderr}"
                        )
                        return
                    
                    # Parse the output
                    processes = []
                    lines = result.stdout.splitlines()
                    if len(lines) > 1:  # Skip header line
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 11:
                                user = parts[0]
                                pid = parts[1]
                                cpu = parts[2]
                                mem = parts[3]
                                vsz = parts[4]
                                rss = parts[5]
                                name = ' '.join(parts[10:])
                                processes.append((pid, name, cpu, f"{mem}%"))
                    
                    # Update the table
                    table.setRowCount(len(processes))
                    for row, (pid, name, cpu, mem) in enumerate(processes):
                        table.setItem(row, 0, QTableWidgetItem(pid))
                        table.setItem(row, 1, QTableWidgetItem(name))
                        table.setItem(row, 2, QTableWidgetItem(cpu))
                        table.setItem(row, 3, QTableWidgetItem(mem))
                    
                    # Sort by PID by default
                    table.sortItems(0)
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"An error occurred while fetching process list: {str(e)}"
                    )
            
            # Connect search box
            def filter_processes():
                search_text = search_box.text().lower()
                for row in range(table.rowCount()):
                    match = False
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item and search_text in item.text().lower():
                            match = True
                            break
                    table.setRowHidden(row, not match)
            
            search_box.textChanged.connect(filter_processes)
            refresh_btn.clicked.connect(update_process_list)
            
            # Initial load
            update_process_list()
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while showing process list: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _show_device_capabilities(self):
        """Show detailed device capabilities"""
        try:
            self.status_var.setText("Fetching device capabilities...")
            
            # Get device capabilities using ideviceinfo
            result = subprocess.run(
                ["ideviceinfo", "-x"],  # -x for XML output
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to get device capabilities: {result.stderr}"
                )
                return
            
            # Create a dialog to display the capabilities
            dialog = QDialog(self)
            dialog.setWindowTitle("Device Capabilities")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # Add a text edit to display the XML
            text_edit = QTextEdit()
            text_edit.setFont(QFont("Monospace"))
            text_edit.setReadOnly(True)
            
            # Try to pretty-print the XML if possible
            try:
                from xml.dom import minidom
                xml_str = result.stdout
                xml = minidom.parseString(xml_str)
                pretty_xml = xml.toprettyxml(indent="  ")
                text_edit.setPlainText(pretty_xml)
            except Exception:
                # If pretty-printing fails, just show the raw XML
                text_edit.setPlainText(result.stdout)
            
            # Add a save button
            button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
            button_box.accepted.connect(lambda: self._save_text_to_file(text_edit.toPlainText(), "device_capabilities.xml"))
            button_box.rejected.connect(dialog.reject)
            
            # Add widgets to layout
            layout.addWidget(QLabel("Device Capabilities (XML):"))
            layout.addWidget(text_edit)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while showing device capabilities: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _save_shsh_blobs(self):
        """Save SHSH blobs for downgrade"""
        try:
            # Ask for save directory
            save_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Directory to Save SHSH Blobs",
                os.path.expanduser("~/SHSH_Blobs")
            )
            
            if not save_dir:
                return
                
            # Create save directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Show progress dialog
            progress = QProgressDialog("Saving SHSH blobs...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Saving SHSH Blobs")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Run in a separate thread to avoid freezing the UI
            def save_blobs():
                try:
                    # Use idevicerestore to save SHSH blobs
                    result = subprocess.run(
                        ["idevicerestore", "-t", "-s"],
                        cwd=save_dir,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    return result
                except subprocess.TimeoutExpired:
                    return "Operation timed out after 5 minutes"
                except Exception as e:
                    return str(e)
            
            # Start the thread
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(save_blobs)
                
                # Wait for the thread to complete or be cancelled
                while not future.done():
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        future.cancel()
                        break
                    time.sleep(0.1)
                
                if future.done() and not future.cancelled():
                    result = future.result()
                    progress.cancel()
                    
                    if isinstance(result, str):
                        # Error occurred
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Failed to save SHSH blobs: {result}"
                        )
                    else:
                        # Check if any blobs were saved
                        blob_files = [f for f in os.listdir(save_dir) if f.endswith('.shsh') or f.endswith('.shsh2')]
                        if blob_files:
                            QMessageBox.information(
                                self,
                                "Success",
                                f"SHSH blobs saved successfully to:\n{save_dir}\n\n"
                                f"Saved blobs: {', '.join(blob_files)}"
                            )
                        else:
                            QMessageBox.warning(
                                self,
                                "Warning",
                                "No SHSH blobs were saved. This could be because the server is not signing "
                                "firmware for your device or the device is not in the correct mode."
                            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while saving SHSH blobs: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _monitor_notification(self, notification):
        """Monitor a specific notification"""
        try:
            if hasattr(self, '_notification_monitor_thread') and self._notification_monitor_thread.is_alive():
                # Stop monitoring if already running
                self._stop_notification_monitor()
                return
                
            # Create a dialog to display notifications
            if not hasattr(self, '_notification_dialog'):
                self._notification_dialog = QDialog(self)
                self._notification_dialog.setWindowTitle("Notification Monitor")
                self._notification_dialog.setMinimumSize(500, 300)
                
                layout = QVBoxLayout()
                
                # Add a text edit to display notifications
                self._notification_text = QTextEdit()
                self._notification_text.setReadOnly(True)
                self._notification_text.setFont(QFont("Monospace"))
                
                # Add a clear button
                clear_btn = QPushButton("Clear")
                clear_btn.clicked.connect(self._notification_text.clear)
                
                # Add a stop button
                self._stop_btn = QPushButton("Stop Monitoring")
                self._stop_btn.clicked.connect(lambda: self._stop_notification_monitor())
                
                # Add buttons to layout
                button_box = QDialogButtonBox()
                button_box.addButton(clear_btn, QDialogButtonBox.ActionRole)
                button_box.addButton(self._stop_btn, QDialogButtonBox.ActionRole)
                button_box.addButton(QDialogButtonBox.Close)
                button_box.rejected.connect(self._notification_dialog.reject)
                
                layout.addWidget(QLabel("Received Notifications:"))
                layout.addWidget(self._notification_text)
                layout.addWidget(button_box)
                
                self._notification_dialog.setLayout(layout)
                self._notification_dialog.finished.connect(self._stop_notification_monitor)
            
            # Start monitoring in a separate thread
            self._notification_monitor_running = True
            self._notification_monitor_thread = threading.Thread(
                target=self._notification_monitor_loop,
                daemon=True
            )
            self._notification_monitor_thread.start()
            
            # Show the dialog
            self._notification_dialog.show()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while starting notification monitor: {str(e)}"
            )
    
    def _stop_notification_monitor(self):
        """Stop the notification monitor"""
        if hasattr(self, '_notification_monitor_running'):
            self._notification_monitor_running = False
        if hasattr(self, '_notification_monitor_process') and self._notification_monitor_process:
            try:
                self._notification_monitor_process.terminate()
                self._notification_monitor_process = None
            except:
                pass
    
    def _notification_monitor_loop(self):
        """Monitor notifications in a loop"""
        try:
            # Start idevicenotificationproxy in monitor mode
            self._notification_monitor_process = subprocess.Popen(
                ["idevicenotificationproxy", "monitor"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(self._notification_monitor_process.stdout.readline, ''):
                if not hasattr(self, '_notification_monitor_running') or not self._notification_monitor_running:
                    break
                    
                # Update the UI on the main thread
                if hasattr(self, '_notification_text'):
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    self._notification_text.append(f"[{timestamp}] {line.strip()}")
                    
                    # Auto-scroll to bottom
                    scrollbar = self._notification_text.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                    
                    # Process events to keep the UI responsive
                    QApplication.processEvents()
            
            # Clean up
            self._stop_notification_monitor()
            
        except Exception as e:
            if hasattr(self, '_notification_monitor_running') and self._notification_monitor_running:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Notification monitor error: {str(e)}"
                )
    
    def _post_notification(self, notification=None):
        """Post a notification to the device"""
        try:
            # If no notification is provided, show a dialog to enter one
            if not notification:
                notification, ok = QInputDialog.getText(
                    self,
                    "Post Notification",
                    "Enter the notification to post (e.g., com.apple.springboard.whatever):"
                )
                
                if not ok or not notification.strip():
                    return
            
            # Post the notification
            self.status_var.setText(f"Posting notification: {notification}...")
            
            result = subprocess.run(
                ["idevicenotificationproxy", "post", notification],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Notification posted successfully: {notification}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to post notification: {result.stderr}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while posting notification: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _view_system_logs(self):
        """View system logs from the device"""
        try:
            # Create a dialog to display logs
            dialog = QDialog(self)
            dialog.setWindowTitle("System Logs")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # Add filter controls
            filter_layout = QHBoxLayout()
            
            filter_label = QLabel("Filter:")
            filter_edit = QLineEdit()
            filter_edit.setPlaceholderText("Filter logs...")
            
            case_sensitive = QCheckBox("Case Sensitive")
            regex_check = QCheckBox("Use Regex")
            
            filter_layout.addWidget(filter_label)
            filter_layout.addWidget(filter_edit)
            filter_layout.addWidget(case_sensitive)
            filter_layout.addWidget(regex_check)
            
            # Add log display
            log_display = QTextEdit()
            log_display.setReadOnly(True)
            log_display.setFont(QFont("Monospace"))
            
            # Add buttons
            button_box = QDialogButtonBox()
            refresh_btn = button_box.addButton("Refresh", QDialogButtonBox.ActionRole)
            save_btn = button_box.addButton("Save...", QDialogButtonBox.ActionRole)
            button_box.addButton(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            
            # Add widgets to layout
            layout.addLayout(filter_layout)
            layout.addWidget(log_display)
            layout.addWidget(button_box)
            
            # Function to load logs
            def load_logs():
                try:
                    log_display.clear()
                    log_display.setPlainText("Loading logs...")
                    QApplication.processEvents()
                    
                    # Run idevicesyslog to get logs
                    process = subprocess.Popen(
                        ["idevicesyslog"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Read a limited number of lines to avoid freezing
                    max_lines = 1000
                    lines = []
                    
                    for _ in range(max_lines):
                        line = process.stdout.readline()
                        if not line:
                            break
                        lines.append(line)
                    
                    # Kill the process if it's still running
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except:
                        pass
                    
                    # Apply filters
                    filter_text = filter_edit.text()
                    if filter_text:
                        flags = 0 if case_sensitive.isChecked() else re.IGNORECASE
                        try:
                            if regex_check.isChecked():
                                pattern = re.compile(filter_text, flags)
                                lines = [line for line in lines if pattern.search(line)]
                            else:
                                if case_sensitive.isChecked():
                                    lines = [line for line in lines if filter_text in line]
                                else:
                                    filter_text = filter_text.lower()
                                    lines = [line for line in lines if filter_text in line.lower()]
                        except re.error:
                            log_display.setPlainText("Invalid regex pattern")
                            return
                    
                    # Display the logs
                    log_display.setPlainText(''.join(lines[-1000:]))  # Limit to last 1000 lines
                    
                    # Auto-scroll to bottom
                    scrollbar = log_display.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                    
                except Exception as e:
                    log_display.setPlainText(f"Error loading logs: {str(e)}")
            
            # Function to save logs
            def save_logs():
                try:
                    file_path, _ = QFileDialog.getSaveFileName(
                        dialog,
                        "Save Logs",
                        os.path.join(os.path.expanduser("~"), f"device_logs_{time.strftime('%Y%m%d_%H%M%S')}.log"),
                        "Log Files (*.log);;All Files (*)"
                    )
                    
                    if file_path:
                        with open(file_path, 'w') as f:
                            f.write(log_display.toPlainText())
                        QMessageBox.information(
                            dialog,
                            "Success",
                            f"Logs saved to:\n{file_path}"
                        )
                except Exception as e:
                    QMessageBox.critical(
                        dialog,
                        "Error",
                        f"Failed to save logs: {str(e)}"
                    )
            
            # Connect signals
            refresh_btn.clicked.connect(load_logs)
            save_btn.clicked.connect(save_logs)
            
            # Apply filter when Enter is pressed in the filter box
            def on_filter_return_pressed():
                load_logs()
            
            filter_edit.returnPressed.connect(on_filter_return_pressed)
            
            # Initial load
            load_logs()
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while viewing system logs: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _save_text_to_file(self, text, default_name):
        """Helper method to save text content to a file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                os.path.join(os.path.expanduser("~"), default_name),
                "All Files (*);;XML Files (*.xml);;Text Files (*.txt)"
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(text)
                QMessageBox.information(
                    self,
                    "Success",
                    f"File saved successfully to:\n{file_path}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save file: {str(e)}"
            )
    
    def _manage_backups(self):
        """Create or restore device backups"""
        try:
            # Ask user what they want to do
            action = QMessageBox.question(
                self,
                "Backup or Restore",
                "Would you like to create a backup or restore from a backup?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if action == QMessageBox.Cancel:
                return
                
            if action == QMessageBox.Yes:  # Create backup
                # Ask for backup location
                backup_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Backup Location",
                    os.path.expanduser("~/iPhone_Backups")
                )
                
                if not backup_dir:
                    return
                    
                # Ask for backup type
                backup_type, ok = QInputDialog.getItem(
                    self,
                    "Backup Type",
                    "Select backup type:",
                    ["Full", "Incremental", "Apps Only", "Media Only"],
                    0,  # Default to Full
                    False  # Not editable
                )
                
                if not ok:
                    return
                    
                # Map backup type to idevicebackup2 options
                backup_type_map = {
                    "Full": "full",
                    "Incremental": "incremental",
                    "Apps Only": "apps",
                    "Media Only": "media"
                }
                
                # Create backup directory if it doesn't exist
                backup_path = os.path.join(backup_dir, time.strftime("%Y-%m-%d_%H-%M-%S"))
                os.makedirs(backup_path, exist_ok=True)
                
                # Show progress dialog
                progress = QProgressDialog("Creating backup...", "Cancel", 0, 0, self)
                progress.setWindowTitle("Creating Backup")
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                
                # Run backup in a separate thread
                def run_backup():
                    try:
                        cmd = ["idevicebackup2", "backup", f"--{backup_type_map[backup_type]}", backup_path]
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=3600  # 1 hour timeout
                        )
                        return result
                    except subprocess.TimeoutExpired:
                        return "Backup timed out after 1 hour"
                    except Exception as e:
                        return str(e)
                
                # Start the thread
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_backup)
                    
                    # Wait for the thread to complete or be cancelled
                    while not future.done():
                        QApplication.processEvents()
                        if progress.wasCanceled():
                            future.cancel()
                            break
                        time.sleep(0.1)
                    
                    if future.done() and not future.cancelled():
                        result = future.result()
                        progress.cancel()
                        
                        if isinstance(result, str):
                            # Error occurred
                            QMessageBox.critical(
                                self,
                                "Error",
                                f"Backup failed: {result}"
                            )
                        else:
                            QMessageBox.information(
                                self,
                                "Success",
                                f"Backup completed successfully!\n\nLocation: {backup_path}"
                            )
            
            else:  # Restore from backup
                backup_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Backup Directory",
                    os.path.expanduser("~/iPhone_Backups")
                )
                
                if not backup_dir:
                    return
                    
                # Confirm restore
                reply = QMessageBox.warning(
                    self,
                    "Confirm Restore",
                    "WARNING: This will erase all data on your device and restore it from the selected backup.\n\n"
                    "Are you sure you want to continue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Show progress dialog
                    progress = QProgressDialog("Restoring from backup...", "Cancel", 0, 0, self)
                    progress.setWindowTitle("Restoring Backup")
                    progress.setWindowModality(Qt.WindowModal)
                    progress.setMinimumDuration(0)
                    progress.setValue(0)
                    
                    # Run restore in a separate thread
                    def run_restore():
                        try:
                            cmd = ["idevicebackup2", "restore", backup_dir, "--system", "--settings"]
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=7200  # 2 hour timeout
                            )
                            return result
                        except subprocess.TimeoutExpired:
                            return "Restore timed out after 2 hours"
                        except Exception as e:
                            return str(e)
                    
                    # Start the thread
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(run_restore)
                        
                        # Wait for the thread to complete or be cancelled
                        while not future.done():
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                future.cancel()
                                break
                            time.sleep(0.1)
                        
                        if future.done() and not future.cancelled():
                            result = future.result()
                            progress.cancel()
                            
                            if isinstance(result, str):
                                # Error occurred
                                QMessageBox.critical(
                                    self,
                                    "Error",
                                    f"Restore failed: {result}"
                                )
                            else:
                                QMessageBox.information(
                                    self,
                                    "Success",
                                    "Restore completed successfully!\n\nYour device will now reboot."
                                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during backup/restore: {str(e)}"
            )
        finally:
            self.status_var.setText("Ready")
    
    def _manage_disk_images(self):
        """Mount/Unmount developer disk images"""
        try:
            # Check if device is in recovery/DFU mode
            recovery_result = subprocess.run(
                ["idevicediagnostics", "diagnostics", "All"],
                capture_output=True,
                text=True
            )
            
            if "RecoveryMode" in recovery_result.stdout:
                # Device is in recovery mode, mount recovery image
                image_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Developer Disk Image (.dmg)",
                    "",
                    "Disk Images (*.dmg)"
                )
                
                if not image_path:
                    return
                    
                self.status_var.setText("Mounting developer disk image...")
                
                # Check for signature file
                sig_path = image_path + ".signature"
                if os.path.exists(sig_path):
                    result = subprocess.run(
                        ["ideviceimagemounter", image_path, sig_path],
                        capture_output=True,
                        text=True
                    )
                else:
                    result = subprocess.run(
                        ["ideviceimagemounter", image_path],
                        capture_output=True,
                        text=True
                    )
                
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Developer disk image mounted successfully")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to mount disk image: {result.stderr}")
            else:
                # Device is in normal mode, check if developer image is mounted
                result = subprocess.run(
                    ["ideviceimagemounter", "--list"],
                    capture_output=True,
                    text=True
                )
                
                if "ImageSignature" in result.stdout:
                    # Image is mounted, ask to unmount
                    reply = QMessageBox.question(
                        self,
                        "Unmount Image",
                        "A developer disk image is currently mounted. Do you want to unmount it?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.status_var.setText("Unmounting developer disk image...")
                        result = subprocess.run(
                            ["ideviceimagemounter", "--unmount"],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            QMessageBox.information(self, "Success", "Developer disk image unmounted successfully")
                        else:
                            QMessageBox.warning(self, "Error", f"Failed to unmount disk image: {result.stderr}")
                else:
                    QMessageBox.information(self, "Info", "No developer disk image is currently mounted")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _get_crash_reports(self):
        """Retrieve crash reports from the device"""
        try:
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not output_dir:
                return
                
            self.status_var.setText("Retrieving crash reports...")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get device UDID
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                QMessageBox.warning(self, "Error", "No device found or error getting device UDID")
                return
                
            udid = result.stdout.splitlines()[0].strip()
            
            # Get crash reports
            cmd = ["idevicecrashreport", "-e", output_dir]
            if udid:
                cmd.extend(["-u", udid])
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", f"Crash reports saved to: {output_dir}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to get crash reports: {result.stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _manage_disk_images(self):
        """Mount/Unmount developer disk images"""
        try:
            # Check current status
            result = subprocess.run(
                ["ideviceimagemounter", "-l"],
                capture_output=True,
                text=True
            )
            
            if "is mounted" in result.stdout:
                # Unmount if already mounted
                reply = QMessageBox.question(
                    self,
                    "Unmount Disk Image",
                    "A disk image is already mounted. Unmount it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    subprocess.run(["ideviceimagemounter", "-u"])
                    QMessageBox.information(self, "Success", "Disk image unmounted successfully")
            else:
                # Mount disk image
                image_path = QFileDialog.getOpenFileName(
                    self,
                    "Select Developer Disk Image",
                    "",
                    "Disk Images (*.dmg)"
                )[0]
                
                if image_path:
                    self.status_var.setText("Mounting disk image...")
                    
                    # Look for signature file
                    sig_path = image_path + ".signature"
                    if not os.path.exists(sig_path):
                        sig_path = ""
                    
                    cmd = ["ideviceimagemounter", image_path]
                    if sig_path:
                        cmd.append(sig_path)
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(self, "Success", "Disk image mounted successfully")
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to mount disk image: {result.stderr}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _manage_device_date(self):
        """View or modify device date and time"""
        try:
            # Get current device date
            result = subprocess.run(
                ["idevicedate"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(self, "Error", "Failed to get device date")
                return
                
            current_date = result.stdout.strip()
            
            # Show current date and ask if user wants to set a new one
            reply = QMessageBox.question(
                self,
                "Device Date",
                f"Current device date: {current_date}\n\nDo you want to set a new date?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Show date/time picker dialog
                from PySide6.QtWidgets import QDateTimeEdit, QDialog, QDialogButtonBox, QVBoxLayout
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Set Device Date/Time")
                
                layout = QVBoxLayout(dialog)
                
                date_edit = QDateTimeEdit()
                date_edit.setDateTime(datetime.now())
                date_edit.setCalendarPopup(True)
                layout.addWidget(date_edit)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                if dialog.exec() == QDialog.Accepted:
                    selected_date = date_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
                    
                    # Set the device date
                    result = subprocess.run(
                        ["idevicedate", "--set", selected_date],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(self, "Success", "Device date updated successfully")
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to set device date: {result.stderr}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _manage_device_name(self):
        """View or modify device name"""
        try:
            # Get current device name
            result = subprocess.run(
                ["idevicename"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(self, "Error", "Failed to get device name")
                return
                
            current_name = result.stdout.strip()
            
            # Show current name and ask if user wants to set a new one
            new_name, ok = QInputDialog.getText(
                self,
                "Device Name",
                f"Current device name: {current_name}\n\nEnter new device name:",
                text=current_name
            )
            
            if ok and new_name and new_name != current_name:
                # Set the new device name
                result = subprocess.run(
                    ["idevicename", new_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Device name updated successfully")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to set device name: {result.stderr}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _test_afc_connection(self):
        """Test Apple File Conduit connection"""
        try:
            self.status_var.setText("Testing AFC connection...")
            
            result = subprocess.run(
                ["afccheck"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", "AFC connection test passed!")
            else:
                QMessageBox.warning(self, "Error", f"AFC connection test failed: {result.stderr}")
                
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "afccheck command not found. Make sure libimobiledevice-utils is installed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _toggle_mount(self):
        """Mount or unmount iOS filesystem"""
        try:
            # Check if already mounted
            mount_point = "/mnt/ios"  # Default mount point
            
            if os.path.ismount(mount_point):
                # Unmount
                reply = QMessageBox.question(
                    self,
                    "Unmount Filesystem",
                    "The iOS filesystem is currently mounted. Unmount it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    subprocess.run(["fusermount", "-u", mount_point], check=True)
                    QMessageBox.information(self, "Success", "Filesystem unmounted successfully")
            else:
                # Mount
                mount_point = QFileDialog.getExistingDirectory(
                    self,
                    "Select Mount Point",
                    "/mnt",
                    QFileDialog.ShowDirsOnly
                )
                
                if mount_point:
                    # Create mount point if it doesn't exist
                    os.makedirs(mount_point, exist_ok=True)
                    
                    # Mount using ifuse
                    result = subprocess.run(
                        ["ifuse", mount_point],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(self, "Success", f"Filesystem mounted successfully at {mount_point}")
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to mount filesystem: {result.stderr}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _check_ios_updates(self):
        """Check for available iOS updates"""
        try:
            self.status_var.setText("Checking for iOS updates...")
            
            # Run idevicerestore with -l -n flags to check for updates
            process = subprocess.Popen(
                ["idevicerestore", "-l", "-n"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Show progress dialog
            progress = QProgressDialog("Checking for iOS updates...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Checking for Updates")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Read output in a separate thread
            def read_output():
                output = []
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output.append(line)
                        QApplication.processEvents()  # Keep UI responsive
                
                # Get any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    output.append(stdout)
                if stderr:
                    output.append("\nError:\n" + stderr)
                
                # Show results
                QMetaObject.invokeMethod(progress, "close")
                QMetaObject.invokeMethod(
                    self,
                    "_show_command_results",
                    Qt.QueuedConnection,
                    Q_ARG(str, "iOS Update Check"),
                    Q_ARG(str, ''.join(output) if output else "No update information available")
                )
            
            # Start the thread
            thread = threading.Thread(target=read_output, daemon=True)
            thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check for updates: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _manage_backups(self):
        """Create or restore device backups"""
        try:
            # Ask user if they want to create or restore a backup
            reply = QMessageBox.question(
                self,
                "Backup/Restore",
                "Would you like to create a new backup or restore from an existing one?",
                QMessageBox.Save | QMessageBox.Restore | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                # Create backup
                backup_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Backup Directory"
                )
                
                if backup_dir:
                    self.status_var.setText("Creating backup (this may take a while)...")
                    
                    result = subprocess.run(
                        ["idevicebackup2", "backup", backup_dir],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        QMessageBox.information(self, "Success", f"Backup created successfully in {backup_dir}")
                    else:
                        QMessageBox.warning(self, "Error", f"Backup failed: {result.stderr}")
                        
            elif reply == QMessageBox.Restore:
                # Restore backup
                backup_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Backup Directory"
                )
                
                if backup_dir:
                    reply = QMessageBox.warning(
                        self,
                        "Warning",
                        "Restoring will erase all data on the device. Continue?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.status_var.setText("Restoring backup (this may take a while)...")
                        
                        result = subprocess.run(
                            ["idevicebackup2", "restore", backup_dir, "--system", "--reboot"],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            QMessageBox.information(self, "Success", "Backup restored successfully")
                        else:
                            QMessageBox.warning(self, "Error", f"Restore failed: {result.stderr}")
                            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
            
    def _toggle_developer_mode(self):
        """Toggle developer mode on the device"""
        try:
            # Check current status
            result = subprocess.run(
                ["idevicedebug", "enable"],
                capture_output=True,
                text=True
            )
            
            if "already enabled" in result.stderr.lower():
                # Developer mode is already enabled, ask to disable
                reply = QMessageBox.question(
                    self,
                    "Disable Developer Mode",
                    "Developer mode is currently enabled. Disable it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    subprocess.run(["idevicedebug", "disable"])
                    QMessageBox.information(self, "Success", "Developer mode disabled")
            elif result.returncode == 0:
                QMessageBox.information(self, "Success", "Developer mode enabled")
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle developer mode: {result.stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _show_process_list(self):
        """Show list of running processes on the device"""
        try:
            self.status_var.setText("Fetching process list...")
            
            result = subprocess.run(
                ["idevicedebug", "proclist"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Display in a dialog
                dialog = QDialog(self)
                dialog.setWindowTitle("Running Processes")
                dialog.resize(400, 500)
                
                layout = QVBoxLayout(dialog)
                
                text_edit = QTextEdit()
                text_edit.setPlainText(result.stdout)
                text_edit.setReadOnly(True)
                text_edit.setFont(QFont("Monospace", 9))
                
                layout.addWidget(text_edit)
                
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec()
            else:
                QMessageBox.warning(self, "Error", f"Failed to get process list: {result.stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _show_device_capabilities(self):
        """Show detailed device capabilities"""
        try:
            self.status_var.setText("Fetching device capabilities...")
            
            result = subprocess.run(
                ["ideviceinfo", "-x"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse XML to find DeviceCapabilities
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(result.stdout)
                    capabilities = root.find(".//key[.='DeviceCapabilities']/following-sibling::dict[1]")
                    
                    if capabilities is not None:
                        # Format the capabilities for display
                        from xml.dom import minidom
                        xml_str = ET.tostring(capabilities, encoding='unicode')
                        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
                        
                        # Display in a dialog
                        dialog = QDialog(self)
                        dialog.setWindowTitle("Device Capabilities")
                        dialog.resize(600, 700)
                        
                        layout = QVBoxLayout(dialog)
                        
                        text_edit = QTextEdit()
                        text_edit.setPlainText(pretty_xml)
                        text_edit.setReadOnly(True)
                        text_edit.setFont(QFont("Monospace", 9))
                        
                        layout.addWidget(text_edit)
                        
                        close_btn = QPushButton("Close")
                        close_btn.clicked.connect(dialog.accept)
                        layout.addWidget(close_btn)
                        
                        dialog.exec()
                        return
                except Exception as e:
                    print(f"Error parsing XML: {e}")
                    # Fall through to show raw output
            
            # If we get here, show raw output
            QMessageBox.information(self, "Device Capabilities", 
                                 "Could not parse capabilities. Showing raw output.\n\n" + 
                                 result.stdout if result.returncode == 0 else result.stderr)
                                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _save_shsh_blobs(self):
        """Save SHSH blobs for downgrade"""
        try:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Output Directory"
            )
            
            if not output_dir:
                return
                
            self.status_var.setText("Saving SHSH blobs...")
            
            result = subprocess.run(
                ["idevicerestore", "-t"],
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", "SHSH blobs saved successfully")
            else:
                QMessageBox.warning(self, "Error", f"Failed to save SHSH blobs: {result.stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _toggle_syslog(self, checked):
        """Start or stop syslog monitoring"""
        if checked:
            self._start_syslog()
        else:
            self._stop_syslog()
    
    def _start_syslog(self):
        """Start monitoring syslog"""
        if self.syslog_process and self.syslog_process.poll() is None:
            return  # Already running
            
        try:
            filter_text = self.syslog_filter.text().strip()
            cmd = ["idevicesyslog"]
            
            if filter_text:
                cmd.extend(["-m", filter_text])
            
            self.syslog_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start a thread to read the output
            self.syslog_thread = threading.Thread(
                target=self._read_syslog_output,
                daemon=True
            )
            self.syslog_thread.start()
            
            self.syslog_btn.setText("Stop Syslog")
            self.syslog_running = True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start syslog: {str(e)}")
            self.syslog_btn.setChecked(False)
    
    def _stop_syslog(self):
        """Stop monitoring syslog"""
        if self.syslog_process:
            try:
                self.syslog_process.terminate()
                self.syslog_process.wait(timeout=2)
            except:
                self.syslog_process.kill()
            
        self.syslog_btn.setText("Start Syslog")
        self.syslog_running = False
    
    def _read_syslog_output(self):
        """Read output from syslog process"""
        while self.syslog_running and self.syslog_process and self.syslog_process.poll() is None:
            line = self.syslog_process.stdout.readline()
            if line:
                self._append_syslog_line(line.strip())
    
    def _append_syslog_line(self, line):
        """Append a line to the syslog output widget"""
        def update():
            cursor = self.syslog_output.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText(line + "\n")
            self.syslog_output.ensureCursorVisible()
            
        QMetaObject.invokeMethod(self.syslog_output, "setPlainText", 
                               Qt.QueuedConnection,
                               Q_ARG(str, self.syslog_output.toPlainText() + line + "\n"))
    
    def _filter_syslog(self, filter_text):
        """Filter syslog by text"""
        self.syslog_filter.setText(filter_text)
        if self.syslog_running:
            self._stop_syslog()
            self._start_syslog()
    
    def _monitor_notification(self, notification):
        """Monitor a specific notification"""
        try:
            self.status_var.setText(f"Monitoring notification: {notification}")
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Monitoring: {notification}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            output = QTextEdit()
            output.setReadOnly(True)
            output.setFont(QFont("Monospace", 9))
            layout.addWidget(output)
            
            stop_btn = QPushButton("Stop Monitoring")
            layout.addWidget(stop_btn)
            
            # Start monitoring in a separate thread
            self.notification_running = True
            
            def monitor():
                process = subprocess.Popen(
                    ["idevicenotificationproxy", "observe", notification],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                while self.notification_running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        output.append(line.strip())
                        
                process.terminate()
            
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            
            def stop():
                self.notification_running = False
                dialog.accept()
                
            stop_btn.clicked.connect(stop)
            dialog.finished.connect(lambda: setattr(self, 'notification_running', False))
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to monitor notification: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def _post_notification(self, notification):
        """Post a notification to the device"""
        try:
            self.status_var.setText(f"Posting notification: {notification}")
            
            result = subprocess.run(
                ["idevicenotificationproxy", "post", notification],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", f"Notification posted: {notification}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to post notification: {result.stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.status_var.setText("Ready")
    
    def setup_tools_tab(self):
        """Set up the tools tab with scrollable categories"""
        # Create main layout for tools tab
        tools_layout = self.tools_layout  # Use the existing layout
        tools_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create widget that will contain the scrollable content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)
        
        # Create a grid layout for the tool categories
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(15)
        
        # Define tool categories and their corresponding methods
        tool_categories = [
            ("Device Control", self._add_device_control_widgets, 0, 0),
            ("App Management", self._add_app_management_widgets, 0, 1),
            ("System Tools", self._add_system_tools_widgets, 1, 0),
            ("iOS Tools", self._add_ios_tools_widgets, 1, 1),
            ("Debugging", self._add_debugging_widgets, 2, 0),
            ("File Operations", self._add_file_operations_widgets, 2, 1),
            ("Security", self._add_security_widgets, 3, 0),
            ("Automation", self._add_automation_widgets, 3, 1),
            ("Advanced Tests", self._add_advanced_tests_widgets, 4, 0)
        ]
        
        # Add each category as a group box
        for title, method, row, col in tool_categories:
            group_box = QGroupBox(title)
            group_box.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    margin-top: 12px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
            """)
            
            content_layout = QVBoxLayout()
            content_layout.setContentsMargins(10, 20, 10, 10)
            content_layout.setSpacing(8)
            
            # Call the appropriate method to add widgets
            method(content_layout)
            
            group_box.setLayout(content_layout)
            grid_layout.addWidget(group_box, row, col)
        
        # Add the grid to the scroll layout
        scroll_layout.addLayout(grid_layout)
        scroll_layout.addStretch()
        
        # Set the scroll content widget
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the tools layout
        tools_layout.addWidget(scroll_area)

    def check_dependencies(self):
        """Check for required tools"""
        if not check_ios_tools_installed():
            self.show_info(
                "Required Tools Missing",
                "libimobiledevice is required to connect to iOS devices. Please install it first."
            )

    def connect_device(self):
        """Connect to an iOS device"""
        self._run_in_thread(self._connect_device_task)

    def _connect_device_task(self):
        """Worker thread to connect to an iOS device"""
        try:
            # Update UI on the main thread
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, "Attempting to connect to iOS device...")
            )
            QMetaObject.invokeMethod(
                self.status_var,
                "setText",
                Qt.QueuedConnection,
                Q_ARG(str, "Connecting...")
            )
            
            # Get list of devices
            devices = self._get_connected_devices()
            
            # Use the first device if multiple are found
            if devices:
                udid = devices[0]['udid']
                QMetaObject.invokeMethod(
                    self,
                    "log_message",
                    Qt.QueuedConnection,
                    Q_ARG(str, f"Found device with UDID: {udid}")
                )
                
                # Get device info
                device_info = self._get_device_info_from_libimobiledevice(udid)
                if not device_info:
                    QMetaObject.invokeMethod(
                        self.status_var,
                        "setText",
                        Qt.QueuedConnection,
                        Q_ARG(str, "Connection failed")
                    )
                    return
                
                # Update device info on the main thread
                # Convert device_info to a JSON string for thread-safe passing
                device_info_json = json.dumps(device_info)
                QMetaObject.invokeMethod(
                    self,
                    "_update_device_state",
                    Qt.QueuedConnection,
                    Q_ARG(str, device_info_json)
                )
            else:
                QMetaObject.invokeMethod(
                    self,
                    "log_message",
                    Qt.QueuedConnection,
                    Q_ARG(str, "No iOS device detected")
                )
                QMetaObject.invokeMethod(
                    self.status_var,
                    "setText",
                    Qt.QueuedConnection,
                    Q_ARG(str, "Not connected")
                )
                
                # Show message on the main thread
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "No Device Detected"),
                    Q_ARG(str, "No iOS device was detected. Please make sure:\n\n"
                          "1. Your iPhone is connected via USB\n"
                          "2. Your iPhone is unlocked\n"
                          "3. You've trusted this computer on your iPhone")
                )
                
        except Exception as e:
            error_msg = f"Error connecting to device: {str(e)}"
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, error_msg)
            )
            QMetaObject.invokeMethod(
                self.status_var,
                "setText",
                Qt.QueuedConnection,
                Q_ARG(str, "Connection failed")
            )
            
            # Show error on the main thread
            QMetaObject.invokeMethod(
                self, 
                "show_info", 
                Qt.QueuedConnection,
                Q_ARG(str, "Connection Error"),
                Q_ARG(str, f"Could not connect to iOS device: {str(e)}")
            )
    
    @Slot(str)
    def _update_device_state(self, device_info_json):
        """Update device state on the main thread"""
        try:
            # Convert JSON string back to dictionary
            device_info = json.loads(device_info_json)
            self.device_info = device_info
            self.device_connected = True
            device_name = device_info.get('device_name', 'iOS device')
            self.log_message(f"Connected to {device_name}")
            self.status_var.setText(f"Connected: {device_name}")
            self.update_device_info()
        except json.JSONDecodeError as e:
            self.log_message(f"Error parsing device info: {str(e)}")

    def _get_connected_devices(self):
        """Get list of connected iOS devices using libimobiledevice"""
        devices = []
        
        # Linux device detection using libimobiledevice
        try:
            result = subprocess.run(
                ['idevice_id', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                udids = result.stdout.strip().split('\n')
                for udid in udids:
                    if udid.strip():
                        # Get device name
                        name = f"iOS Device ({udid[:8]}...)"
                        try:
                            name_result = subprocess.run(
                                ['ideviceinfo', '-u', udid, '-k', 'DeviceName'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if name_result.returncode == 0 and name_result.stdout.strip():
                                name = name_result.stdout.strip()
                        except Exception:
                            pass
                            
                        # Get device model
                        model = "Unknown"
                        try:
                            model_result = subprocess.run(
                                ['ideviceinfo', '-u', udid, '-k', 'ProductType'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if model_result.returncode == 0 and model_result.stdout.strip():
                                model = self._get_device_model_name(model_result.stdout.strip())
                        except Exception:
                            pass
                        
                        # Get iOS version
                        ios_version = "Unknown"
                        try:
                            ios_result = subprocess.run(
                                ['ideviceinfo', '-u', udid, '-k', 'ProductVersion'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if ios_result.returncode == 0 and ios_result.stdout.strip():
                                ios_version = ios_result.stdout.strip()
                        except Exception:
                            pass
                        
                        devices.append({
                            'udid': udid,
                            'name': name,
                            'model': model,
                            'ios_version': ios_version,
                            'connection_type': 'USB'
                        })
            
        except Exception as e:
            logging.error(f"Error detecting iOS devices: {e}")
            
        return devices

    def _get_device_model_name(self, identifier):
        """
        Convert Apple model identifier to human-readable name.
        Maps the Apple product identifiers to their marketing names.
        """
        # iPhone models
        iphone_models = {
            # iPhone 1-4
            "iPhone1,1": "iPhone",
            "iPhone1,2": "iPhone 3G",
            "iPhone2,1": "iPhone 3GS",
            "iPhone3,1": "iPhone 4",
            "iPhone3,2": "iPhone 4 GSM Rev A",
            "iPhone3,3": "iPhone 4 CDMA",
            # iPhone 4S-5C
            "iPhone4,1": "iPhone 4S",
            "iPhone5,1": "iPhone 5 (GSM)",
            "iPhone5,2": "iPhone 5 (GSM+CDMA)",
            "iPhone5,3": "iPhone 5C (GSM)",
            "iPhone5,4": "iPhone 5C (Global)",
            # iPhone 5S-6+
            "iPhone6,1": "iPhone 5S (GSM)",
            "iPhone6,2": "iPhone 5S (Global)",
            "iPhone7,1": "iPhone 6 Plus",
            "iPhone7,2": "iPhone 6",
            # iPhone 6S-SE
            "iPhone8,1": "iPhone 6S",
            "iPhone8,2": "iPhone 6S Plus",
            "iPhone8,4": "iPhone SE (1st gen)",
            # iPhone 7-X
            "iPhone9,1": "iPhone 7",
            "iPhone9,2": "iPhone 7 Plus",
            "iPhone9,3": "iPhone 7",
            "iPhone9,4": "iPhone 7 Plus",
            "iPhone10,1": "iPhone 8",
            "iPhone10,2": "iPhone 8 Plus",
            "iPhone10,3": "iPhone X",
            "iPhone10,4": "iPhone 8",
            "iPhone10,5": "iPhone 8 Plus",
            "iPhone10,6": "iPhone X",
            # iPhone XS-XR
            "iPhone11,2": "iPhone XS",
            "iPhone11,4": "iPhone XS Max",
            "iPhone11,6": "iPhone XS Max",
            "iPhone11,8": "iPhone XR",
            # iPhone 11 series
            "iPhone12,1": "iPhone 11",
            "iPhone12,3": "iPhone 11 Pro",
            "iPhone12,5": "iPhone 11 Pro Max",
            # iPhone SE 2-12 Mini
            "iPhone12,8": "iPhone SE (2nd gen)",
            "iPhone13,1": "iPhone 12 Mini",
            "iPhone13,2": "iPhone 12",
            "iPhone13,3": "iPhone 12 Pro",
            "iPhone13,4": "iPhone 12 Pro Max",
            # iPhone 13 series
            "iPhone14,2": "iPhone 13 Pro",
            "iPhone14,3": "iPhone 13 Pro Max",
            "iPhone14,4": "iPhone 13 Mini",
            "iPhone14,5": "iPhone 13",
            # iPhone SE 3-14 series
            "iPhone14,6": "iPhone SE (3rd gen)",
            "iPhone14,7": "iPhone 14",
            "iPhone14,8": "iPhone 14 Plus",
            "iPhone15,2": "iPhone 14 Pro",
            "iPhone15,3": "iPhone 14 Pro Max",
            # iPhone 15 series
            "iPhone15,4": "iPhone 15",
            "iPhone15,5": "iPhone 15 Plus",
            "iPhone16,1": "iPhone 15 Pro",
            "iPhone16,2": "iPhone 15 Pro Max",
            # iPhone 16 series (released September 2024)
            "iPhone17,3": "iPhone 16",
            "iPhone17,4": "iPhone 16 Plus",
            "iPhone17,1": "iPhone 16 Pro",
            "iPhone17,2": "iPhone 16 Pro Max",
        }
        
        # iPad models
        ipad_models = {
            # iPad 1st-4th gen
            "iPad1,1": "iPad",
            "iPad2,1": "iPad 2 (Wi-Fi)",
            "iPad2,2": "iPad 2 (GSM)",
            "iPad2,3": "iPad 2 (CDMA)",
            "iPad2,4": "iPad 2 (Wi-Fi, Rev A)",
            "iPad3,1": "iPad (3rd gen, Wi-Fi)",
            "iPad3,2": "iPad (3rd gen, CDMA)",
            "iPad3,3": "iPad (3rd gen, GSM)",
            "iPad3,4": "iPad (4th gen, Wi-Fi)",
            "iPad3,5": "iPad (4th gen, GSM)",
            "iPad3,6": "iPad (4th gen, CDMA)",
            # iPad Air
            "iPad4,1": "iPad Air (Wi-Fi)",
            "iPad4,2": "iPad Air (Cellular)",
            "iPad4,3": "iPad Air (China)",
            "iPad5,3": "iPad Air 2 (Wi-Fi)",
            "iPad5,4": "iPad Air 2 (Cellular)",
            "iPad11,3": "iPad Air (3rd gen, Wi-Fi)",
            "iPad11,4": "iPad Air (3rd gen, Cellular)",
            "iPad13,1": "iPad Air (4th gen, Wi-Fi)",
            "iPad13,2": "iPad Air (4th gen, Cellular)",
            "iPad13,16": "iPad Air (5th gen, Wi-Fi)",
            "iPad13,17": "iPad Air (5th gen, Cellular)",
            # iPad Mini
            "iPad2,5": "iPad Mini (Wi-Fi)",
            "iPad2,6": "iPad Mini (GSM)",
            "iPad2,7": "iPad Mini (CDMA)",
            "iPad4,4": "iPad Mini 2 (Wi-Fi)",
            "iPad4,5": "iPad Mini 2 (Cellular)",
            "iPad4,6": "iPad Mini 2 (China)",
            "iPad4,7": "iPad Mini 3 (Wi-Fi)",
            "iPad4,8": "iPad Mini 3 (Cellular)",
            "iPad4,9": "iPad Mini 3 (China)",
            "iPad5,1": "iPad Mini 4 (Wi-Fi)",
            "iPad5,2": "iPad Mini 4 (Cellular)",
            "iPad11,1": "iPad Mini 5 (Wi-Fi)",
            "iPad11,2": "iPad Mini 5 (Cellular)",
            "iPad14,1": "iPad Mini 6 (Wi-Fi)",
            "iPad14,2": "iPad Mini 6 (Cellular)",
            # iPad Pro
            "iPad6,3": "iPad Pro (9.7\", Wi-Fi)",
            "iPad6,4": "iPad Pro (9.7\", Cellular)",
            "iPad6,7": "iPad Pro (12.9\", Wi-Fi)",
            "iPad6,8": "iPad Pro (12.9\", Cellular)",
            "iPad7,1": "iPad Pro (12.9\", 2nd gen, Wi-Fi)",
            "iPad7,2": "iPad Pro (12.9\", 2nd gen, Cellular)",
            "iPad7,3": "iPad Pro (10.5\", Wi-Fi)",
            "iPad7,4": "iPad Pro (10.5\", Cellular)",
            "iPad8,1": "iPad Pro (11\", Wi-Fi)",
            "iPad8,2": "iPad Pro (11\", Wi-Fi, 1TB)",
            "iPad8,3": "iPad Pro (11\", Cellular)",
            "iPad8,4": "iPad Pro (11\", Cellular, 1TB)",
            "iPad8,5": "iPad Pro (12.9\", 3rd gen, Wi-Fi)",
            "iPad8,6": "iPad Pro (12.9\", 3rd gen, Wi-Fi, 1TB)",
            "iPad8,7": "iPad Pro (12.9\", 3rd gen, Cellular)",
            "iPad8,8": "iPad Pro (12.9\", 3rd gen, Cellular, 1TB)",
            "iPad8,9": "iPad Pro (11\", 2nd gen, Wi-Fi)",
            "iPad8,10": "iPad Pro (11\", 2nd gen, Cellular)",
            "iPad8,11": "iPad Pro (12.9\", 4th gen, Wi-Fi)",
            "iPad8,12": "iPad Pro (12.9\", 4th gen, Cellular)",
            "iPad13,4": "iPad Pro (11\", 3rd gen, Wi-Fi)",
            "iPad13,5": "iPad Pro (11\", 3rd gen, Wi-Fi, 2TB)",
            "iPad13,6": "iPad Pro (11\", 3rd gen, Cellular)",
            "iPad13,7": "iPad Pro (11\", 3rd gen, Cellular, 2TB)",
            "iPad13,8": "iPad Pro (12.9\", 5th gen, Wi-Fi)",
            "iPad13,9": "iPad Pro (12.9\", 5th gen, Wi-Fi, 2TB)",
            "iPad13,10": "iPad Pro (12.9\", 5th gen, Cellular)",
            "iPad13,11": "iPad Pro (12.9\", 5th gen, Cellular, 2TB)",
            "iPad14,3": "iPad Pro (11\", 4th gen, Wi-Fi)",
            "iPad14,4": "iPad Pro (11\", 4th gen, Cellular)",
            "iPad14,5": "iPad Pro (12.9\", 6th gen, Wi-Fi)",
            "iPad14,6": "iPad Pro (12.9\", 6th gen, Cellular)",
            # Regular iPad (5th-9th gen)
            "iPad6,11": "iPad (5th gen, Wi-Fi)",
            "iPad6,12": "iPad (5th gen, Cellular)",
            "iPad7,5": "iPad (6th gen, Wi-Fi)",
            "iPad7,6": "iPad (6th gen, Cellular)",
            "iPad7,11": "iPad (7th gen, Wi-Fi)",
            "iPad7,12": "iPad (7th gen, Cellular)",
            "iPad11,6": "iPad (8th gen, Wi-Fi)",
            "iPad11,7": "iPad (8th gen, Cellular)",
            "iPad12,1": "iPad (9th gen, Wi-Fi)",
            "iPad12,2": "iPad (9th gen, Cellular)",
            "iPad13,18": "iPad (10th gen, Wi-Fi)",
            "iPad13,19": "iPad (10th gen, Cellular)",
        }
        
        # iPod models
        ipod_models = {
            "iPod1,1": "iPod Touch",
            "iPod2,1": "iPod Touch (2nd gen)",
            "iPod3,1": "iPod Touch (3rd gen)",
            "iPod4,1": "iPod Touch (4th gen)",
            "iPod5,1": "iPod Touch (5th gen)",
            "iPod7,1": "iPod Touch (6th gen)",
            "iPod9,1": "iPod Touch (7th gen)",
        }
        
        # Combine all device dictionaries
        all_devices = {**iphone_models, **ipad_models, **ipod_models}
        
        # Return the friendly name if found, otherwise return the identifier
        return all_devices.get(identifier, identifier)

    def _get_device_info_from_libimobiledevice(self, udid):
        """Get device information using libimobiledevice tools"""
        try:
            self.log_message(f"Getting device info for UDID: {udid}")
            device_info = {}
            
            # Run ideviceinfo to get device details
            result = subprocess.run(
                ['ideviceinfo', '-u', udid],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                self.log_message(f"Error getting device info: {result.stderr}")
                return None
                
            # Parse the output - it comes as key:value pairs
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    device_info[key.strip()] = value.strip()
            
            # Get RAM and CPU info from the specs JSON file if available
            ram = "N/A"
            cpu = "N/A"
            friendly_name = "N/A"
            model_identifier = device_info.get('ProductType', '')
            
            # Create a standardized device info dictionary
            # Use friendly name for model if available, otherwise use technical identifier
            model_display = friendly_name if friendly_name != "N/A" else self._get_device_model_name(model_identifier)
            
            standardized_info = {
                "device_name": device_info.get('DeviceName', 'Unknown iPhone'),
                "model": model_display,
                "model_identifier": device_info.get('ProductType', 'Unknown'),  # Keep raw identifier for reference
                "capacity": self._get_device_capacity(udid),
                "serial": device_info.get('SerialNumber', 'Unknown'),
                "ios_version": f"{device_info.get('ProductVersion', 'Unknown')}",
                "udid": udid,
                "imei": device_info.get('InternationalMobileEquipmentIdentity', 'Unknown'),
                "battery_health": self._get_battery_health(udid),
                "activation_status": device_info.get('ActivationState', 'Unknown'),
                "jailbroken": "Unknown",
                "ram": ram,
                "cpu": cpu
            }
            
            self.log_message(f"Device info retrieved: {standardized_info['device_name']} running iOS {standardized_info['ios_version']}")
            return standardized_info
            
        except Exception as e:
            self.log_message(f"Error getting device info: {str(e)}")
            logging.error(f"Error getting device info from libimobiledevice: {e}")
            return None
            
    def _get_device_capacity(self, udid):
        """Get device storage capacity"""
        try:
            # Try to get device capacity using ideviceinfo with the DiskSize domain
            result = subprocess.run(
                ['ideviceinfo', '-u', udid, '-q', 'com.apple.disk_usage', '-k', 'TotalDiskCapacity'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0 and result.stdout.strip().isdigit():
                # Convert bytes to GB
                capacity_bytes = int(result.stdout.strip())
                capacity_gb = capacity_bytes / (1024 * 1024 * 1024)
                return f"{capacity_gb:.0f} GB"
                
            return "Unknown"
            
        except Exception as e:
            logging.error(f"Error getting device capacity: {e}")
            return "Unknown"
            
    def _get_battery_health(self, udid):
        """Get battery health info if available"""
        try:
            # Try to get battery health info
            result = subprocess.run(
                ['ideviceinfo', '-u', udid, '-q', 'com.apple.mobile.battery'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                battery_info = {}
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_info[key.strip()] = value.strip()
                        
                if 'BatteryCurrentCapacity' in battery_info:
                    return f"{battery_info['BatteryCurrentCapacity']}%"
                    
            return "Unknown"
            
        except Exception as e:
            logging.error(f"Error getting battery health: {e}")
            return "Unknown"

    def update_device_info(self):
        """Update the device info display with the connected device information"""
        if not hasattr(self, 'info_fields') or not self.device_connected:
            return
        
        # Update basic info fields
        if 'model' in self.device_info:
            self.info_fields['Model'].setText(self.device_info.get('model', 'N/A'))
        elif 'device_name' in self.device_info:
            self.info_fields['Model'].setText(self.device_info.get('device_name', 'N/A'))
        
        # Always Apple for iOS devices
        self.info_fields['Manufacturer'].setText('Apple')
        
        # iOS Version
        if 'ios_version' in self.device_info:
            self.info_fields['iOS Version'].setText(self.device_info.get('ios_version', 'N/A'))
        elif 'product_version' in self.device_info:
            self.info_fields['iOS Version'].setText(self.device_info.get('product_version', 'N/A'))
        
        # Serial Number
        if 'serial' in self.device_info:
            self.info_fields['Serial Number'].setText(self.device_info.get('serial', 'N/A'))
        elif 'serial_number' in self.device_info:
            self.info_fields['Serial Number'].setText(self.device_info.get('serial_number', 'N/A'))
        
        # UDID
        if 'udid' in self.device_info:
            self.info_fields['UDID'].setText(self.device_info.get('udid', 'N/A'))
        
        # Battery Level
        if 'battery_health' in self.device_info:
            self.info_fields['Battery Level'].setText(self.device_info.get('battery_health', 'N/A'))
        elif 'battery_level' in self.device_info:
            self.info_fields['Battery Level'].setText(self.device_info.get('battery_level', 'N/A'))
        
        # Update debug text with additional info
        if hasattr(self, 'debug_text'):
            self.debug_text.clear()
            self.debug_text.append("Additional Device Information:")
            for key, value in self.device_info.items():
                if key not in ['model', 'device_name', 'manufacturer', 'ios_version', 'product_version', 
                              'serial', 'serial_number', 'udid', 'battery_health', 'battery_level']:
                    self.debug_text.append(f"{key}: {value}")

    def _run_in_thread(self, target_function):
        """Run a function in a separate thread"""
        try:
            thread = threading.Thread(target=target_function)
            thread.daemon = True
            thread.start()
        except Exception as e:
            logging.error(f"Error starting thread: {e}")
            self.log_message(f"ERROR: Could not start operation: {str(e)}")
            
    def take_screenshot(self):
        """Take a screenshot of the connected iOS device using idevicescreenshot"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return

        self._run_in_thread(self._take_screenshot_task)
        
    def _take_screenshot_task(self):
        """Worker thread to take a screenshot"""
        try:
            self.log_message("Taking screenshot...")
            self.status_var.setText("Taking screenshot...")
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.path.expanduser("~"), "iPhone_Screenshots")
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
                
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshots_dir, f"iphone_screenshot_{timestamp}.png")
            
            # Take screenshot using idevicescreenshot
            result = subprocess.run(
                ['idevicescreenshot', '-u', self.device_info.get('udid', ''), screenshot_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log_message(f"Screenshot saved to: {screenshot_path}")
                self.status_var.setText("Screenshot taken")
                
                # Show message on the main thread
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Screenshot Taken"),
                    Q_ARG(str, f"Screenshot saved to: {screenshot_path}")
                )
                
                # Try to open with default viewer
                try:
                    subprocess.Popen(['xdg-open', screenshot_path])
                except Exception:
                    pass  # Silently fail if opening fails
            else:
                self.log_message(f"Error taking screenshot: {result.stderr}")
                self.status_var.setText("Screenshot failed")
                
                # Show error on the main thread
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Screenshot Error"),
                    Q_ARG(str, f"Failed to take screenshot: {result.stderr}")
                )
                
        except Exception as e:
            self.log_message(f"Error taking screenshot: {str(e)}")
            self.status_var.setText("Screenshot failed")
            
            # Show error on the main thread
            QMetaObject.invokeMethod(
                self, 
                "show_info", 
                Qt.QueuedConnection,
                Q_ARG(str, "Screenshot Error"),
                Q_ARG(str, f"Failed to take screenshot: {str(e)}")
            )
    
    def refresh_device_list(self):
        """Refresh the list of connected iOS devices"""
        self.status_var.setText("Refreshing device list...")
        self._run_in_thread(self._refresh_device_list_task)
    
    def _refresh_device_list_task(self):
        """Worker thread to refresh the device list"""
        try:
            # Clear current device info
            self.device_connected = False
            self.device_info = {}
            
            # Get list of connected devices
            devices = self._get_connected_devices()
            
            if devices:
                # Connect to the first device
                udid = devices[0]['udid']
                device_info = self._get_device_info_from_libimobiledevice(udid)
                
                if device_info:
                    self.device_info = device_info
                    self.device_connected = True
                    self.log_message(f"Connected to {device_info.get('device_name', 'iOS device')}")
                    
                    # Update status on the main thread
                    QMetaObject.invokeMethod(
                        self, 
                        "update_status_ui", 
                        Qt.QueuedConnection,
                        Q_ARG(str, f"Connected: {device_info.get('device_name', 'iOS device')}")
                    )
                    
                    # Update device info on the main thread
                    QMetaObject.invokeMethod(
                        self, 
                        "update_device_info", 
                        Qt.QueuedConnection
                    )
                else:
                    self.log_message("Failed to get device info")
                    
                    # Update status on the main thread
                    QMetaObject.invokeMethod(
                        self, 
                        "update_status_ui", 
                        Qt.QueuedConnection,
                        Q_ARG(str, "No device connected")
                    )
            else:
                self.log_message("No iOS devices found")
                
                # Update status on the main thread
                QMetaObject.invokeMethod(
                    self, 
                    "update_status_ui", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "No iOS devices found")
                )
            
        except Exception as e:
            self.log_message(f"Error refreshing devices: {str(e)}")
            
            # Update status on the main thread
            QMetaObject.invokeMethod(
                self, 
                "update_status_ui", 
                Qt.QueuedConnection,
                Q_ARG(str, f"Error: {str(e)}")
            )
    
    def update_status_ui(self, message):
        """Update the status UI (to be called from other threads)"""
        self.status_var.setText(message)

    def _perform_backup(self, backup_type):
        """Perform device backup based on specified type"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
        
        # Get backup location
        backup_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Backup Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not backup_dir:
            return  # User cancelled
            
        # Show progress dialog
        progress = QProgressDialog(f"Creating {backup_type} backup...", "Cancel", 0, 0, self)
        progress.setWindowTitle(f"iOS {backup_type.title()} Backup")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # Start the backup in a separate thread
        self._run_in_thread(lambda: self._perform_backup_task(backup_type, backup_dir, progress))
    
    def _perform_backup_task(self, backup_type, backup_dir, progress_dialog):
        """Worker thread to perform a backup"""
        try:
            self.log_message(f"Starting {backup_type} backup to {backup_dir}")
            
            # Get device UDID
            udid = self.device_info.get('udid', '')
            if not udid:
                self.log_message("Error: Device UDID not found")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Backup Error"),
                    Q_ARG(str, "Device UDID not found")
                )
                return
                
            # Build backup command
            cmd = ['idevicebackup2', '-u', udid, 'backup']
            
            if backup_type == "full":
                cmd.append('--full')
                self.log_message("Starting full backup (backs up all files)")
            elif backup_type == "quick":
                # Default is a quick backup
                self.log_message("Starting quick backup (backs up only new/changed files)")
            else:  # custom
                cmd.append('--full')
                self.log_message("Starting custom backup")
                
            # Add the backup directory
            cmd.append(backup_dir)
            
            self.log_message(f"Running: {' '.join(cmd)}")
            
            # Run the backup command
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1  # Line buffered
            )
            
            # Monitor output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_message(line.strip())
                    
            # Process is done
            returncode = process.poll()
            if returncode == 0:
                self.log_message("Backup completed successfully!")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Backup Complete"),
                    Q_ARG(str, f"Backup completed successfully to:\n{backup_dir}")
                )
            else:
                error = process.stderr.read()
                self.log_message(f"Backup failed with error: {error}")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Backup Failed"),
                    Q_ARG(str, f"Backup failed with error: {error}")
                )
        except Exception as e:
            self.log_message(f"Error during backup: {str(e)}")
            QMetaObject.invokeMethod(progress_dialog, "cancel")
            QMetaObject.invokeMethod(
                self, 
                "show_info", 
                Qt.QueuedConnection,
                Q_ARG(str, "Backup Error"),
                Q_ARG(str, f"Error during backup: {str(e)}")
            )
    
    def _restore_backup(self):
        """Restore a backup to the connected device"""
        if not self.device_connected:
            self.show_info("Error", "No device connected")
            return
        
        # Get backup location
        backup_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Backup Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not backup_dir:
            return  # User cancelled
        
        # Confirm restore
        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            "WARNING: Restoring a backup will erase all data on the device.\n\n"
            "Make sure the device is unlocked and connected.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Show progress dialog
        progress = QProgressDialog("Restoring backup...", "Cancel", 0, 0, self)
        progress.setWindowTitle("iOS Backup Restore")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # Start the restore in a separate thread
        self._run_in_thread(lambda: self._restore_backup_task(backup_dir, progress))
    
    def _restore_backup_task(self, backup_dir, progress_dialog):
        """Worker thread to restore a backup"""
        try:
            self.log_message(f"Starting restore from {backup_dir}")
            
            # Get device UDID
            udid = self.device_info.get('udid', '')
            if not udid:
                self.log_message("Error: Device UDID not found")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Restore Error"),
                    Q_ARG(str, "Device UDID not found")
                )
                return
                
            # Build restore command
            cmd = ['idevicebackup2', '-u', udid, 'restore', '--system', '--settings', '--reboot', backup_dir]
            self.log_message(f"Running: {' '.join(cmd)}")
            
            # Run the restore command
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1  # Line buffered
            )
            
            # Monitor output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_message(line.strip())
                    
            # Process is done
            returncode = process.poll()
            if returncode == 0:
                self.log_message("Restore completed successfully!")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Restore Complete"),
                    Q_ARG(str, "Restore completed successfully. The device will now reboot.")
                )
            else:
                error = process.stderr.read()
                self.log_message(f"Restore failed with error: {error}")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Restore Failed"),
                    Q_ARG(str, f"Restore failed with error: {error}")
                )
        except Exception as e:
            self.log_message(f"Error during restore: {str(e)}")
            QMetaObject.invokeMethod(progress_dialog, "cancel")
            QMetaObject.invokeMethod(
                self, 
                "show_info", 
                Qt.QueuedConnection,
                Q_ARG(str, "Restore Error"),
                Q_ARG(str, f"Error during restore: {str(e)}")
            )

    def install_libimobiledevice(self):
        """Install libimobiledevice and related tools"""
        reply = QMessageBox.question(
            self,
            "Install libimobiledevice",
            "This will install libimobiledevice and related tools using your system package manager.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Show progress dialog
        progress = QProgressDialog("Installing libimobiledevice...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Installing Tools")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # Start the installation in a separate thread
        self._run_in_thread(lambda: self._install_libimobiledevice_task(progress))
    
    def _install_libimobiledevice_task(self, progress_dialog):
        """Worker thread to install libimobiledevice"""
        try:
            self.log_message("Installing libimobiledevice and related tools...")
            
            # Detect the system and use the appropriate package manager
            if shutil.which('apt'):
                # Debian-based systems (Ubuntu, Debian, etc.)
                cmd = ['pkexec', 'apt', 'install', '-y', 'libimobiledevice-utils', 'ifuse', 'usbmuxd']
            elif shutil.which('dnf'):
                # Red Hat-based systems (Fedora, CentOS, etc.)
                cmd = ['pkexec', 'dnf', 'install', '-y', 'libimobiledevice', 'ifuse', 'usbmuxd']
            elif shutil.which('pacman'):
                # Arch Linux
                cmd = ['pkexec', 'pacman', '-S', '--noconfirm', 'libimobiledevice', 'ifuse', 'usbmuxd']
            elif shutil.which('zypper'):
                # openSUSE
                cmd = ['pkexec', 'zypper', 'install', '-y', 'libimobiledevice', 'ifuse', 'usbmuxd']
            else:
                raise Exception("Could not detect package manager. Please install libimobiledevice manually.")
                
            self.log_message(f"Running: {' '.join(cmd)}")
            
            # Run the installation command
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1  # Line buffered
            )
            
            # Monitor output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_message(line.strip())
                    
            # Process is done
            returncode = process.poll()
            if returncode == 0:
                self.log_message("Installation completed successfully!")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Installation Complete"),
                    Q_ARG(str, "libimobiledevice and related tools have been installed successfully.\n\n"
                         "Please restart the application to use the new tools.")
                )
                
                # Check if tools are now installed
                if check_ios_tools_installed():
                    self.log_message("All required tools are now installed")
                    
                    # Remove the install button if present
                    if hasattr(self, 'libmd_btn'):
                        QMetaObject.invokeMethod(
                            self.libmd_btn, 
                            "setVisible", 
                            Qt.QueuedConnection,
                            Q_ARG(bool, False)
                        )
            else:
                error = process.stderr.read()
                self.log_message(f"Installation failed with error: {error}")
                QMetaObject.invokeMethod(progress_dialog, "cancel")
                QMetaObject.invokeMethod(
                    self, 
                    "show_info", 
                    Qt.QueuedConnection,
                    Q_ARG(str, "Installation Failed"),
                    Q_ARG(str, f"Installation failed with error: {error}")
                )
        except Exception as e:
            self.log_message(f"Error during installation: {str(e)}")
            QMetaObject.invokeMethod(progress_dialog, "cancel")
            QMetaObject.invokeMethod(
                self, 
                "show_info", 
                Qt.QueuedConnection,
                Q_ARG(str, "Installation Error"),
                Q_ARG(str, f"Error during installation: {str(e)}")
            )

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationVersion("1.0.0")
    
    # Create and show the main window
    window = IOSToolsModule()
    window.show()
    
    sys.exit(app.exec())