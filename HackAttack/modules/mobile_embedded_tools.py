#!/usr/bin/env python3
"""
Mobile & Embedded Tools Module for Hack Attack

This module provides tools for security testing of mobile and embedded devices.
It includes a PyQt6-based GUI and can be used both as an importable module
and as a standalone application.

Features:
- Mobile device security analysis
- Embedded device communication testing
- Protocol analysis for IoT devices
- Common vulnerability checks for mobile/embedded systems
- Interactive GUI with progress tracking
- Results visualization
"""

import logging
import os
import socket
import sys
import subprocess
import platform
import time
from typing import Dict, List, Optional, Any, Callable, Union, Tuple

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

# Check if GUI is available
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTabWidget, QGroupBox,
        QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar,
        QStatusBar, QComboBox, QHeaderView, QMessageBox, QFileDialog, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject
    from PyQt6.QtGui import QColor, QTextCursor, QFont, QIcon
    
    # Set up high DPI scaling for better display on high-resolution screens
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    
    # Create dummy classes for type hinting when PyQt6 is not available
    class QObject:
        pass
    
    class QThread:
        pass
    
    class pyqtSignal:
        def __init__(self, *args, **kwargs):
            pass
            
        def emit(self, *args):
            pass
            
        def connect(self, *args):
            pass
            
    class Qt:
        # Alignment flags
        AlignRight = None
        
        # Application attributes
        AA_EnableHighDpiScaling = None
        AA_UseHighDpiPixmaps = None
        
        # Other commonly used Qt enums
        class AlignmentFlag:
            AlignRight = None
            
        class ApplicationAttribute:
            AA_EnableHighDpiScaling = None
            AA_UseHighDpiPixmaps = None
            
    class QColor:
        def __init__(self, *args, **kwargs):
            pass
            
    class QApplication:
        @staticmethod
        def setAttribute(*args, **kwargs):
            pass
            
    class QMainWindow:
        pass
        
    class QWidget:
        pass
        
    class QVBoxLayout:
        pass
        
    class QHBoxLayout:
        pass
        
    class QLabel:
        pass
        
    class QLineEdit:
        pass
        
    class QPushButton:
        pass
        
    class QTabWidget:
        pass
        
    class QGroupBox:
        pass
        
    class QTableWidget:
        pass
        
    class QTableWidgetItem:
        pass
        
    class QTextEdit:
        pass
        
    class QProgressBar:
        pass
        
    class QStatusBar:
        pass
        
    class QComboBox:
        pass
        
    class QHeaderView:
        pass
        
    class QMessageBox:
        pass
        
    class QFileDialog:
        pass
        
    class QSplitter:
        def __init__(self, *args, **kwargs):
            pass
            
        def addWidget(self, *args, **kwargs):
            pass
            
        def setSizes(self, *args, **kwargs):
            pass
            
        class Orientation:
            Vertical = None
    
    logger = logging.getLogger(__name__)
    logger.warning("PyQt6 not available. GUI features will be disabled.")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mobile_embedded_tools.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mobile_embedded_tools')

class USBAnalyzer(QObject if GUI_AVAILABLE else object):
    """Class for analyzing USB devices with support for Android, iOS, and embedded devices."""
    
    def __init__(self):
        super().__init__()
        self.vendor_db = {}
        self.device_db = {}
        self._load_databases()
    
    def _load_databases(self):
        """Load vendor and device databases from JSON files."""
        import json
        import os
        
        try:
            # Get the directory of the current module
            module_dir = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Loading databases from: {module_dir}")
            
            # Load vendor database
            vendor_db_path = os.path.join(module_dir, 'vendor_database.json')
            logger.info(f"Loading vendor database from: {vendor_db_path}")
            
            if not os.path.exists(vendor_db_path):
                logger.error(f"Vendor database not found at: {vendor_db_path}")
            else:
                with open(vendor_db_path, 'r', encoding='utf-8') as f:
                    vendor_data = json.load(f)
                    self.vendor_db = vendor_data.get('vendors', {})
                    logger.info(f"Loaded {len(self.vendor_db)} vendors")
            
            # Load device database
            device_db_path = os.path.join(module_dir, 'device_database.json')
            logger.info(f"Loading device database from: {device_db_path}")
            
            if not os.path.exists(device_db_path):
                logger.error(f"Device database not found at: {device_db_path}")
            else:
                with open(device_db_path, 'r', encoding='utf-8') as f:
                    device_data = json.load(f)
                    self.device_db = device_data.get('devices', {})
                    logger.info(f"Loaded {len(self.device_db)} device categories")
            
            # Log sample data for debugging
            if self.vendor_db:
                sample_vendor = next(iter(self.vendor_db.items()))
                logger.debug(f"Sample vendor data: {sample_vendor[0]} = {sample_vendor[1]}")
            
            if self.device_db:
                sample_vendor = next(iter(self.device_db.items()))
                sample_device = next(iter(sample_vendor[1].items())) if sample_vendor[1] else (None, None)
                logger.debug(f"Sample device data: {sample_vendor[0]}/{sample_device[0]} = {sample_device[1]}")
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error: {str(je)}")
            self.vendor_db = {}
            self.device_db = {}
        except Exception as e:
            logger.error(f"Error loading device databases: {str(e)}", exc_info=True)
            # Fallback to minimal database
            self.vendor_db = {}
            self.device_db = {}
    
    def get_vendor_name(self, vendor_id: str) -> str:
        """Get vendor name from vendor ID.
        
        Args:
            vendor_id: Vendor ID in hex string format (e.g., '04e8')
            
        Returns:
            Vendor name or 'Unknown Vendor' if not found
        """
        # Normalize the vendor ID (remove 0x prefix and convert to lowercase)
        vendor_key = vendor_id.lower().replace('0x', '')
        
        # Try exact match first
        if vendor_key in self.vendor_db:
            return self.vendor_db[vendor_key]
            
        # Try with '0x' prefix (some databases might have this format)
        prefixed_key = f"0x{vendor_key}"
        if prefixed_key in self.vendor_db:
            return self.vendor_db[prefixed_key]
            
        # Try with '0x' prefix in the database keys (some keys might have it)
        for db_key, name in self.vendor_db.items():
            if db_key.lower().replace('0x', '') == vendor_key:
                return name
                
        # Log debug info if not found
        self.log_message(f"Vendor not found for ID: 0x{vendor_key}", 'debug')
        sample_keys = list(self.vendor_db.keys())[:5]
        self.log_message(f"Sample vendor keys in database: {sample_keys}", 'debug')
        
        return 'Unknown Vendor'
    
    def get_device_info(self, vendor_id: str, product_id: str) -> dict:
        """Get device information from vendor and product IDs.
        
        Args:
            vendor_id: Vendor ID in hex string format (e.g., '04e8')
            product_id: Product ID in hex string format (e.g., '6860')
            
        Returns:
            Dictionary containing device information
        """
        # Normalize the IDs (remove 0x prefix and convert to uppercase for database lookup)
        vendor_key = vendor_id.upper().replace('0X', '')
        product_key = product_id.upper().replace('0X', '')
        
        self.log_message(f"Looking up device: vendor=0x{vendor_key}, product=0x{product_key}", 'debug')
        
        # Try different key combinations for both vendor and product
        vendor_keys_to_try = [
            f"0x{vendor_key}",  # Database format is '0x1D6B'
            vendor_key,           # Also try without 0x
            vendor_key.lower(),   # Try lowercase
            f"0x{vendor_key.lower()}"  # Try lowercase with 0x
        ]
        
        product_keys_to_try = [
            f"0x{product_key}",  # Database format is '0x0002'
            product_key,          # Also try without 0x
            product_key.lower(),  # Try lowercase
            f"0x{product_key.lower()}"  # Try lowercase with 0x
        ]
        
        # First try to find the vendor in the device database
        for vk in vendor_keys_to_try:
            if vk in self.device_db:
                vendor_devices = self.device_db[vk]
                self.log_message(f"Found vendor 0x{vendor_key} (as '{vk}') with {len(vendor_devices)} devices", 'debug')
                
                # Try to find the product
                for pk in product_keys_to_try:
                    if pk in vendor_devices:
                        device_info = vendor_devices[pk].copy()  # Make a copy to avoid modifying the original
                        self.log_message(f"Found device 0x{product_key} (as '{pk}'): {device_info}", 'debug')
                        return device_info
                
                # If we got here, product not found for this vendor
                self.log_message(f"Product 0x{product_key} not found for vendor 0x{vendor_key}", 'debug')
                self.log_message(f"Available products for this vendor: {list(vendor_devices.keys())}", 'debug')
                break
        else:
            # If we got here, vendor not found
            self.log_message(f"Vendor 0x{vendor_key} not found in device database", 'debug')
            sample_vendors = list(self.device_db.keys())[:5]
            self.log_message(f"Sample vendors in database: {sample_vendors}", 'debug')
        
        # Return default unknown device if not found
        return {
            'name': 'Unknown Device',
            'type': 'unknown',
            'category': 'unknown'
        }
    
    def __init__(self, callback: Callable = None):
        """Initialize the USB analyzer.
        
        Args:
            callback: Optional callback function for progress updates
        """
        if GUI_AVAILABLE:
            super().__init__()
        self.callback = callback
        self._stop_requested = False
        self.vendor_db = {}
        self.device_db = {}
        self._load_databases()
        
    def update_progress(self, message: str, progress: int = None):
        """Update progress through the callback."""
        if self.callback:
            self.callback({
                'type': 'progress',
                'message': message,
                'progress': progress
            })
    
    def log_message(self, message: str, level: str = 'info'):
        """Log a message through the callback."""
        if self.callback:
            self.callback({
                'type': 'log',
                'level': level,
                'message': message
            })
    
    def stop(self):
        """Stop the current scan."""
        self._stop_requested = True
        self.log_message("USB analysis stopped by user", 'warning')
    
    def _get_device_info(self, device):
        """Get detailed information about a USB device.
        
        Args:
            device: The USB device object from pyusb
            
        Returns:
            Dictionary containing device information with all required fields
        """
        # Initialize default values
        device_info = {
            'vendor_id': '0x0000',
            'product_id': '0x0000',
            'vendor_name': 'Unknown',
            'product_name': 'Unknown',
            'serial_number': '',
            'class_code': '0x00',
            'subclass': '0x00',
            'protocol': '0x00',
            'speed': 'Unknown',
            'device_address': '0',
            'port_numbers': '',
            'bus_number': '0',
            'device_speed': 'Unknown',
            'device_version': '',
            'manufacturer': 'Unknown',
            'max_packet_size': '0',
            'configurations': '0',
            'type': 'unknown',
            'category': 'unknown',
            'interfaces': []
        }
        
        try:
            # Get basic device info that should always be available
            device_info['vendor_id'] = f"0x{device.idVendor:04x}"
            device_info['product_id'] = f"0x{device.idProduct:04x}"
            
            # Get device class information if available
            device_class = getattr(device, 'bDeviceClass', None)
            device_subclass = getattr(device, 'bDeviceSubClass', None)
            device_protocol = getattr(device, 'bDeviceProtocol', None)
            
            # Get device info from database first
            device_data = self.get_device_info(device_info['vendor_id'], device_info['product_id'])
            if device_data:
                device_info.update(device_data)
            
            # Get vendor name from our database
            vendor_name = self.get_vendor_name(device_info['vendor_id'])
            device_info['vendor_name'] = vendor_name
            
            # Set a default name if not found in device data
            if 'name' not in device_info or device_info['name'] == 'Unknown Device':
                device_info['name'] = f"Unknown (Vendor: {device_info['vendor_id']}, Product: {device_info['product_id']})"
            
            # If we don't have detailed device info, try to identify by class
            if not device_data or device_info.get('type') == 'unknown':
                class_info = self._identify_device(
                    device_info['vendor_id'], 
                    device_info['product_id'],
                    device_class,
                    device_subclass,
                    device_protocol
                )
                if class_info and class_info.get('type') != 'unknown':
                    device_info.update(class_info)
            
            # Only try to get string descriptors if they exist
            try:
                # Check if string descriptors exist before trying to access them
                if hasattr(device, 'iManufacturer') and device.iManufacturer > 0:
                    device_info['manufacturer'] = usb.util.get_string(device, device.iManufacturer) or 'Unknown'
                
                if hasattr(device, 'iProduct') and device.iProduct > 0:
                    product_name = usb.util.get_string(device, device.iProduct)
                    if product_name:
                        device_info['product_name'] = product_name
                        device_info['product'] = product_name  # Ensure 'product' key is set
                
                # Try to get serial number with multiple fallback methods
                serial = None
                
                # Method 1: Standard way using iSerialNumber
                if hasattr(device, 'iSerialNumber') and device.iSerialNumber > 0:
                    try:
                        serial = usb.util.get_string(device, device.iSerialNumber)
                    except (usb.core.USBError, ValueError, IndexError, AttributeError):
                        pass
                
                # Method 2: Try to get serial from device descriptor
                if not serial and hasattr(device, 'serial_number'):
                    serial = device.serial_number
                
                # Method 3: Try to get serial from device's _serial_number attribute
                if not serial and hasattr(device, '_serial_number'):
                    serial = device._serial_number
                
                # Clean up the serial number if we got one
                if serial:
                    serial = str(serial).strip()
                    if serial and serial != '0' and serial.lower() != 'none':
                        device_info['serial_number'] = serial
                
                # If no serial number was found, set to N/A
                if 'serial_number' not in device_info:
                    device_info['serial_number'] = 'N/A'
                        
            except (usb.core.USBError, ValueError, IndexError, AttributeError) as e:
                # Skip string descriptor errors - they're not critical
                pass
                
            # Set the product name from available information
            if 'product_name' in device_info:
                device_info['product'] = device_info['product_name']
            elif 'name' in device_info:
                device_info['product'] = device_info['name']
                
            # Create a descriptive name for the device
            if device_info.get('vendor_name', '').lower() != 'unknown vendor':
                device_info['description'] = f"{device_info['vendor_name']} {device_info.get('name', '')}".strip()
            else:
                device_info['description'] = device_info.get('name', 'Unknown Device')
            
            # Get device class info if available
            # Map device class codes to human-readable names
            class_names = {
                0x00: 'Defined at Interface',
                0x01: 'Audio',
                0x02: 'CDC Control',
                0x03: 'HID',
                0x05: 'Physical',
                0x06: 'Image',
                0x07: 'Printer',
                0x08: 'Mass Storage',
                0x09: 'Hub',
                0x0A: 'CDC Data',
                0x0B: 'Smart Card',
                0x0D: 'Content Security',
                0x0E: 'Video',
                0x0F: 'Personal Healthcare',
                0x10: 'Audio/Video',
                0xDC: 'Diagnostic Device',
                0xE0: 'Wireless Controller',
                0xEF: 'Miscellaneous',
                0xFE: 'Application Specific',
                0xFF: 'Vendor Specific'
            }
            
            try:
                if hasattr(device, 'bDeviceClass'):
                    device_class = device.bDeviceClass
                    device_info['class_code'] = f"0x{device_class:02x}"
                    device_info['class_name'] = class_names.get(device_class, 'Unknown')
                    
                if hasattr(device, 'bDeviceSubClass'):
                    device_info['subclass'] = f"0x{device.bDeviceSubClass:02x}"
                    
                if hasattr(device, 'bDeviceProtocol'):
                    device_info['protocol'] = f"0x{device.bDeviceProtocol:02x}"
                    
            except Exception as e:
                self.log_message(f"Error getting device class info: {str(e)}", 'debug')
                if 'device_class' in locals():
                    device_info['class_code'] = f"0x{device_class:02x}"
                    device_info['class_name'] = class_names.get(device_class, f"Unknown (0x{device_class:02x})")
            
            # Get bus and address information
            try:
                device_info['bus'] = str(device.bus) if hasattr(device, 'bus') else ""
                device_info['address'] = str(device.address) if hasattr(device, 'address') else ""
                if hasattr(device, 'port_numbers') and device.port_numbers:
                    device_info['port_numbers'] = ",".join(str(p) for p in device.port_numbers)
            except Exception as e:
                self.log_message(f"Error getting device location info: {str(e)}", 'debug')
            
        except Exception as e:
            self.log_message(f"Unexpected error in _get_device_info: {str(e)}", 'error')
            import traceback
            self.log_message(traceback.format_exc(), 'debug')
        
        return device_info
    
    def _identify_device(self, vendor_id: str, product_id: str, device_class: int = None, 
                        device_subclass: int = None, device_protocol: int = None) -> Dict[str, str]:
        """Identify a USB device based on vendor and product IDs.
        
        Args:
            vendor_id: Vendor ID in hex (e.g., '0x04e8')
            product_id: Product ID in hex (e.g., '0x6860')
            device_class: USB device class code (0x00-0xFF)
            device_subclass: USB device subclass code
            device_protocol: USB device protocol code
            
        Returns:
            Dictionary with device type information containing:
            - name: Display name of the device
            - type: Device type (e.g., 'phone', 'hub', 'security')
            - category: General category (e.g., 'mobile', 'usb', 'embedded')
            - description: Detailed description of the device
        """
        # Define a default unknown device response
        unknown_device = {
            'name': 'Unknown Device',
            'type': 'unknown',
            'category': 'unknown',
            'description': f'Unknown device (Vendor: {vendor_id}, Product: {product_id})'
        }
        
        # Normalize IDs for comparison (case-insensitive lookup)
        try:
            # Remove '0x' prefix if present and normalize case
            vendor_id_str = vendor_id.lower().replace('0x', '')
            product_id_str = product_id.lower().replace('0x', '')
        except AttributeError:
            return unknown_device
            
        try:
            # First try to get vendor name from vendor database
            vendor_name = self.get_vendor_name(vendor_id_str)
            
            # Try to get device info from device database
            device_info = self.get_device_info(vendor_id_str, product_id_str)
            
            if device_info and device_info.get('name') != 'Unknown Device':
                # We found a matching device
                return {
                    'name': device_info['name'],
                    'product': device_info.get('name'),  # Ensure product is set
                    'type': device_info.get('type', 'unknown'),
                    'category': device_info.get('category', 'unknown'),
                    'description': f"{vendor_name} {device_info['name']}",
                    'confidence': 'high'  # High confidence when we have an exact match
                }
            
            # Try to identify by device class if available
            if device_class is not None:
                class_info = self._identify_by_class(device_class, device_subclass, device_protocol)
                if class_info:
                    return {
                        'name': f"{vendor_name} {class_info['name']}" if vendor_name != 'Unknown Vendor' else class_info['name'],
                        'type': class_info.get('type', 'unknown'),
                        'category': class_info.get('category', 'unknown'),
                        'description': f"{vendor_name} {class_info.get('description', 'USB Device')}" if vendor_name != 'Unknown Vendor' \
                                      else class_info.get('description', 'USB Device'),
                        'confidence': 'medium'  # Medium confidence when identified by class
                    }
            
            # If we know the vendor but not the specific product
            if vendor_name != 'Unknown Vendor':
                return {
                    'name': f"{vendor_name} Device",
                    'type': 'unknown',
                    'category': 'unknown',
                    'description': f'Unknown {vendor_name} device (0x{product_id.upper()})',
                    'confidence': 'low'  # Low confidence when we only know the vendor
                }
                
            # If we don't know the vendor or product
            return unknown_device
            
        except Exception as e:
            self.log_message(f"Error identifying device {vendor_id}:{product_id}: {str(e)}", 'error')
            return unknown_device
    
    def _identify_by_class(self, device_class: int, subclass: int = None, protocol: int = None) -> Dict[str, str]:
        """Identify a USB device by its class, subclass, and protocol codes.
        
        Args:
            device_class: USB device class code (0x00-0xFF)
            subclass: USB device subclass code
            protocol: USB device protocol code
            
        Returns:
            Dictionary with device type information or None if not identified
        """
        # USB class codes from USB specification
        class_info = {
            0x00: {
                'name': 'Interface Specific',
                'type': 'interface_defined',
                'category': 'usb',
                'description': 'Interface-specific device'
            },
            0x01: {
                'name': 'Audio Device',
                'type': 'audio',
                'category': 'audio',
                'description': 'USB Audio Device'
            },
            0x02: {
                'name': 'CDC Control',
                'type': 'communication',
                'category': 'network',
                'description': 'Communication Device Class (CDC)'
            },
            0x03: {
                'name': 'HID Device',
                'type': 'input',
                'category': 'hid',
                'description': 'Human Interface Device (HID)'
            },
            0x05: {
                'name': 'Physical Device',
                'type': 'physical',
                'category': 'usb',
                'description': 'Physical Interface Device'
            },
            0x06: {
                'name': 'Imaging Device',
                'type': 'camera',
                'category': 'imaging',
                'description': 'Still Imaging Device (e.g., camera)'
            },
            0x07: {
                'name': 'Printer',
                'type': 'printer',
                'category': 'printer',
                'description': 'USB Printer'
            },
            0x08: {
                'name': 'Mass Storage',
                'type': 'storage',
                'category': 'storage',
                'description': 'Mass Storage Device (e.g., flash drive, HDD)'
            },
            0x09: {
                'name': 'USB Hub',
                'type': 'hub',
                'category': 'usb_hub',
                'description': 'USB Hub'
            },
            0x0A: {
                'name': 'CDC Data',
                'type': 'communication',
                'category': 'network',
                'description': 'CDC Data Interface'
            },
            0x0B: {
                'name': 'Smart Card',
                'type': 'smartcard',
                'category': 'security',
                'description': 'Smart Card Reader'
            },
            0x0D: {
                'name': 'Content Security',
                'type': 'security',
                'category': 'security',
                'description': 'Content Security Device'
            },
            0x0E: {
                'name': 'Video Device',
                'type': 'video',
                'category': 'video',
                'description': 'Video Device (e.g., webcam)'
            },
            0x0F: {
                'name': 'Personal Healthcare',
                'type': 'healthcare',
                'category': 'medical',
                'description': 'Personal Healthcare Device'
            },
            0x10: {
                'name': 'Audio/Video Device',
                'type': 'av',
                'category': 'multimedia',
                'description': 'Audio/Video Device'
            },
            0xDC: {
                'name': 'Diagnostic Device',
                'type': 'diagnostic',
                'category': 'diagnostic',
                'description': 'Diagnostic Device'
            },
            0xE0: {
                'name': 'Wireless Controller',
                'type': 'wireless',
                'category': 'wireless',
                'description': 'Wireless Controller (e.g., Bluetooth, WiFi)'
            },
            0xEF: {
                'name': 'Miscellaneous',
                'type': 'misc',
                'category': 'misc',
                'description': 'Miscellaneous Device'
            },
            0xFE: {
                'name': 'Application Specific',
                'type': 'application',
                'category': 'application',
                'description': 'Application-Specific Device'
            },
            0xFF: {
                'name': 'Vendor Specific',
                'type': 'vendor',
                'category': 'vendor',
                'description': 'Vendor-Specific Device'
            }
        }
        
        # Handle specific subclasses or protocols if needed
        if device_class == 0x09 and subclass == 0x00 and protocol == 0x02:
            return {
                'name': 'USB 2.0 Hub',
                'type': 'hub',
                'category': 'usb_hub',
                'description': 'USB 2.0 Hub'
            }
        elif device_class == 0x09 and subclass == 0x00 and protocol == 0x03:
            return {
                'name': 'USB 3.0 Hub',
                'type': 'hub',
                'category': 'usb_hub',
                'description': 'USB 3.0 Hub'
            }
        
        # Return the class info if found
        return class_info.get(device_class, None)
    
    def get_usb_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected USB devices with detailed information.
        
        Returns:
            List of dictionaries containing USB device information
        """
        devices = []
        error_occurred = False
        error_msg = None
        
        try:
            self.update_progress("Scanning for USB devices...", 10)
            
            if not USB_AVAILABLE:
                self.log_message("pyusb not available. Install with: pip install pyusb", 'error')
                return devices
                
            self.update_progress("Enumerating USB devices...", 30)
            all_devices = list(usb.core.find(find_all=True))
            total_devices = len(all_devices)
            
            if total_devices == 0:
                self.log_message("No USB devices found", 'info')
                return devices
                
            self.log_message(f"Found {total_devices} USB device(s)", 'info')
            
            # Process each device
            for i, device in enumerate(all_devices):
                if self._stop_requested:
                    self.log_message("Scan stopped by user", 'warning')
                    break
                    
                try:
                    # Get device info
                    device_info = self._get_device_info(device)
                    
                    # Skip if we don't have valid vendor and product IDs
                    if not device_info.get('vendor_id') or not device_info.get('product_id'):
                        self.log_message("Skipping device with invalid vendor/product IDs", 'debug')
                        continue
                        
                    try:
                        # Identify device type
                        vendor_id = device_info['vendor_id'].lower().replace('0x', '')
                        product_id = device_info['product_id'].lower().replace('0x', '')
                        device_type = self._identify_device(vendor_id, product_id)
                    except Exception as e:
                        self.log_message(f"Error identifying device type: {str(e)}", 'debug')
                        device_type = {
                            'type': 'unknown',
                            'category': 'unknown',
                            'description': 'Unknown Device'
                        }
                    
                    # Create device data with all available information
                    device_data = {
                        'vendor_id': device_info.get('vendor_id', '0x0000'),
                        'product_id': device_info.get('product_id', '0x0000'),
                        'manufacturer': device_info.get('vendor_name', 'Unknown'),
                        'product': device_info.get('product_name', 'Unknown'),
                        'class_code': device_info.get('class_code', '0x00'),
                        'class_name': device_info.get('class_name', 'Unknown'),
                        'type': device_type.get('type', 'unknown'),
                        'category': device_type.get('category', 'unknown'),
                        'description': device_type.get('description', 'Unknown Device'),
                        'serial_number': device_info.get('serial_number', ''),
                        'bus': device_info.get('bus', ''),
                        'address': device_info.get('address', ''),
                        'port_numbers': device_info.get('port_numbers', '')
                    }
                    
                    # Log the device we found
                    self.log_message(
                        f"Found device: {device_data['manufacturer']} {device_data['product']} "
                        f"(Vendor: {device_data['vendor_id']}, Product: {device_data['product_id']})",
                        'info'
                    )
                    
                    devices.append(device_data)
                    
                except usb.core.USBError as e:
                    error_msg = f"USB error accessing device: {str(e)}"
                    self.log_message(error_msg, 'error')
                    continue
                    
                except Exception as e:
                    error_msg = f"Unexpected error processing device: {str(e)}"
                    self.log_message(error_msg, 'error')
                    import traceback
                    self.log_message(traceback.format_exc(), 'debug')
                    continue
                    
                    # Update progress
                    progress = 30 + int((i + 1) / total_devices * 70)
                    self.update_progress(
                        f"Found {device_info['vendor_name']} {device_info['product_name']}",
                        progress
                    )
                    
                except usb.core.USBError as e:
                    error_msg = f"USB error accessing device: {str(e)}"
                    self.log_message(error_msg, 'error')
                    continue
                    
                except Exception as e:
                    error_msg = f"Error processing device: {str(e)}"
                    self.log_message(error_msg, 'error')
                    import traceback
                    self.log_message(traceback.format_exc(), 'debug')
                    continue
            
            self.update_progress("USB device scan completed", 100)
            self.log_message(f"Successfully processed {len(devices)} of {total_devices} devices", 'info')
            
        except Exception as e:
            error_msg = f"Error scanning USB devices: {str(e)}"
            error_occurred = True
            self.log_message(error_msg, 'error')
            import traceback
            self.log_message(traceback.format_exc(), 'debug')
        
        # Always send the devices we found, even if there was an error
        try:
            if self.callback:
                self.callback({
                    'type': 'devices',
                    'devices': devices,
                    'error': error_msg if error_occurred else None
                })
        except Exception as e:
            self.log_message(f"Error in callback: {str(e)}", 'error')
        
        return devices


class MobileDeviceAnalyzer:
    """Class for analyzing mobile device security."""
    
    def __init__(self, target: str, connection_type: str = 'network', output_dir: str = 'reports', 
                 callback: Callable = None):
        """Initialize the mobile device analyzer.
        
        Args:
            target: IP address for network or device ID for USB
            connection_type: Type of connection ('network' or 'usb')
            output_dir: Directory to store analysis reports
            callback: Optional callback function for progress updates
        """
        self.target = target
        self.connection_type = connection_type
        self.output_dir = output_dir
        self.callback = callback
        self._stop_requested = False
        os.makedirs(output_dir, exist_ok=True)
    
    def update_progress(self, message: str, progress: int = None):
        """Update progress through the callback."""
        if self.callback:
            self.callback({
                'type': 'progress',
                'message': message,
                'progress': progress
            })
    
    def log_message(self, message: str, level: str = 'info'):
        """Log a message through the callback."""
        if self.callback:
            self.callback({
                'type': 'log',
                'level': level,
                'message': message
            })
    
    def stop(self):
        """Stop the current scan."""
        self._stop_requested = True
        self.log_message("Mobile device analysis stopped by user", 'warning')
    
    def check_common_ports(self) -> Dict[int, Dict[str, str]]:
        """Check common mobile device ports for open services."""
        common_ports = {
            8080: 'HTTP Proxy',
            8443: 'HTTPS',
            22: 'SSH',
            23: 'Telnet',
            5555: 'ADB',
            62078: 'iPhone Sync',
            62087: 'iPhone USB',
            3000: 'Node.js',
            9000: 'ADB Control',
            9999: 'ADB Shell',
            8081: 'HTTP Alt',
            8444: 'HTTPS Alt',
            8088: 'HTTP Alt',
            8888: 'HTTP Alt',
            8089: 'HTTP Alt',
            9090: 'HTTP Alt',
            10000: 'NDMP',
            10001: 'SCP Configuration',
            10002: 'Documentation',
            10003: 'FileMaker'
        }
        
        results = {}
        total_ports = len(common_ports)
        
        for i, (port, service) in enumerate(common_ports.items(), 1):
            if self._stop_requested:
                self.log_message("Port scanning stopped by user", 'warning')
                break
                
            self.update_progress(f"Scanning port {port} ({service})...", int((i/total_ports)*100))
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target_ip, port))
                if result == 0:
                    results[port] = {
                        'service': service,
                        'status': 'open',
                        'description': f"{service} service detected"
                    }
                    self.log_message(f"Port {port} ({service}) is open", 'success')
                else:
                    self.log_message(f"Port {port} ({service}) is closed", 'info')
                sock.close()
            except Exception as e:
                error_msg = f"Error scanning port {port}: {str(e)}"
                results[port] = {
                    'service': service,
                    'status': 'error',
                    'description': f"Error: {str(e)}"
                }
                self.log_message(error_msg, 'error')
        
        return results
    
    def scan_device_info(self) -> Dict[str, Any]:
        """Gather basic device information using various techniques."""
        info = {
            'http_services': {},
            'device_type': 'unknown',
            'platform': 'unknown',
            'services': []
        }
        
        self.update_progress("Starting device information scan...", 0)
        
        try:
            # Check for common HTTP services
            try:
                import requests
                from requests.exceptions import RequestException
                
                urls_to_check = [
                    (f"http://{self.target_ip}:8080", 8080, 'http'),
                    (f"https://{self.target_ip}:8443", 8443, 'https'),
                    (f"http://{self.target_ip}:80", 80, 'http'),
                    (f"https://{self.target_ip}:443", 443, 'https'),
                    (f"http://{self.target_ip}:8000", 8000, 'http'),
                    (f"http://{self.target_ip}:8888", 8888, 'http')
                ]
                
                total_urls = len(urls_to_check)
                
                for i, (url, port, scheme) in enumerate(urls_to_check, 1):
                    if self._stop_requested:
                        break
                        
                    self.update_progress(f"Checking {url}...", int((i/total_urls)*100))
                    
                    try:
                        response = requests.get(url, timeout=3, verify=False, allow_redirects=True)
                        url_info = {
                            'url': url,
                            'status': response.status_code,
                            'server': response.headers.get('Server', 'Unknown'),
                            'content_type': response.headers.get('Content-Type', ''),
                            'redirects': len(response.history) > 0
                        }
                        
                        info['http_services'][str(port)] = url_info
                        self.log_message(f"Found HTTP service at {url} (Status: {response.status_code})", 'success')
                        
                        # Try to identify device type based on response
                        if 'Android' in response.text or 'android' in response.text.lower():
                            info['platform'] = 'Android'
                        elif 'iPhone' in response.text or 'iPad' in response.text or 'iOS' in response.text:
                            info['platform'] = 'iOS'
                            
                    except RequestException as e:
                        self.log_message(f"Could not connect to {url}: {str(e)}", 'debug')
                        continue
                        
            except ImportError:
                self.log_message("Requests module not available. Some features may be limited.", 'warning')
                
            # Try to identify device using other techniques
            self._identify_device(info)
                
        except Exception as e:
            error_msg = f"Error scanning device info: {str(e)}"
            self.log_message(error_msg, 'error')
            info['error'] = error_msg
            
        return info
    
    def _identify_device(self, info: Dict[str, Any]):
        """Try to identify the device type based on various characteristics."""
        self.update_progress("Identifying device type...", 90)
        
        # Check for common mobile/embedded device signatures
        try:
            # Check for common IoT device ports
            common_iot_ports = [
                (1883, 'MQTT'),
                (5683, 'CoAP'),
                (5684, 'CoAPS'),
                (8883, 'MQTT over SSL'),
                (4840, 'OPC UA'),
                (4843, 'OPC UA over HTTPS'),
                (5683, 'CoAP'),
                (5684, 'CoAPS'),
                (1900, 'UPnP'),
                (49152, 'UPnP')
            ]
            
            for port, service in common_iot_ports:
                if self._stop_requested:
                    break
                    
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((self.target_ip, port))
                    if result == 0:
                        info['services'].append({
                            'port': port,
                            'service': service,
                            'status': 'open'
                        })
                        self.log_message(f"Found {service} service on port {port}", 'success')
                    sock.close()
                except:
                    continue
            
            # Check for common embedded device signatures
            if info.get('http_services'):
                for port, service in info['http_services'].items():
                    server = service.get('server', '').lower()
                    content_type = service.get('content_type', '').lower()
                    
                    # Check for common embedded web servers
                    if 'lighttpd' in server:
                        info['device_type'] = 'embedded_web_server'
                        info['web_server'] = 'lighttpd'
                    elif 'nginx' in server:
                        info['device_type'] = 'embedded_web_server'
                        info['web_server'] = 'nginx'
                    elif 'apache' in server:
                        info['device_type'] = 'embedded_web_server'
                        info['web_server'] = 'apache'
                    
                    # Check for specific device types based on content
                    if 'sonos' in server or 'sonos' in str(service).lower():
                        info['device_type'] = 'sonos_speaker'
                    elif 'philips-hue' in server or 'hue' in str(service).lower():
                        info['device_type'] = 'philips_hue'
                    elif 'samsung' in server or 'smarttv' in str(service).lower():
                        info['device_type'] = 'samsung_smart_tv'
                    
        except Exception as e:
            self.log_message(f"Error during device identification: {str(e)}", 'error')
        
        # Default to mobile if we couldn't identify anything else
        if info['device_type'] == 'unknown' and info['platform'] != 'unknown':
            info['device_type'] = 'mobile_device'


class EmbeddedDeviceTester:
    """Class for testing embedded device security."""
    
    def __init__(self, target_ip: str, protocols: List[str] = None, callback: Callable = None):
        """Initialize the embedded device tester.
        
        Args:
            target_ip: IP address of the target embedded device
            protocols: List of protocols to test (e.g., ['http', 'coap', 'mqtt'])
            callback: Optional callback function for progress updates
        """
        self.target_ip = target_ip
        self.protocols = protocols or ['http']
        self.callback = callback
        self._stop_requested = False
    
    def update_progress(self, message: str, progress: int = None):
        """Update progress through the callback."""
        if self.callback:
            self.callback({
                'type': 'progress',
                'message': message,
                'progress': progress
            })
    
    def log_message(self, message: str, level: str = 'info'):
        """Log a message through the callback."""
        if self.callback:
            self.callback({
                'type': 'log',
                'level': level,
                'message': message
            })
    
    def stop(self):
        """Stop the current scan."""
        self._stop_requested = True
        self.log_message("Embedded device testing stopped by user", 'warning')
    
    def test_http_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Test common HTTP endpoints on embedded devices."""
        common_endpoints = [
            '/',
            '/admin',
            '/login',
            '/status',
            '/api/v1/status',
            '/config',
            '/firmware',
            '/backup',
            '/debug',
            '/console',
            '/shell',
            '/cmd',
            '/cgi-bin/status',
            '/cgi-bin/test.cgi',
            '/cgi-bin/luci',
            '/cgi-bin/luci/'
        ]
        
        results = {}
        
        try:
            import requests
            from requests.exceptions import RequestException
            
            total_endpoints = len(common_endpoints)
            
            for i, endpoint in enumerate(common_endpoints, 1):
                if self._stop_requested:
                    self.log_message("HTTP endpoint testing stopped by user", 'warning')
                    break
                
                url = f"http://{self.target_ip}{endpoint}"
                self.update_progress(f"Testing endpoint: {url}", int((i/total_endpoints)*100))
                
                try:
                    response = requests.get(url, timeout=3, verify=False, allow_redirects=True)
                    results[url] = {
                        'status': response.status_code,
                        'content_type': response.headers.get('Content-Type', ''),
                        'server': response.headers.get('Server', ''),
                        'redirects': len(response.history) > 0,
                        'content_length': len(response.content) if response.content else 0
                    }
                    
                    if response.status_code == 200:
                        self.log_message(f"Found accessible endpoint: {url}", 'success')
                    elif response.status_code == 401 or response.status_code == 403:
                        self.log_message(f"Authentication required at: {url}", 'warning')
                    else:
                        self.log_message(f"Endpoint {url} returned status: {response.status_code}", 'info')
                        
                except RequestException as e:
                    results[url] = {
                        'error': str(e),
                        'status': 'error'
                    }
                    self.log_message(f"Error accessing {url}: {str(e)}", 'error')
                    
        except ImportError:
            error_msg = "HTTP testing requires the 'requests' module."
            self.log_message(error_msg, 'error')
            results["error"] = error_msg
            
        return results
    
    def check_common_vulnerabilities(self) -> Dict[str, Dict[str, str]]:
        """Check for common vulnerabilities in embedded devices."""
        self.update_progress("Checking for common vulnerabilities...", 0)
        
        vulns = {}
        
        # Check for default credentials
        default_creds = [
            {'username': 'admin', 'password': 'admin'},
            {'username': 'admin', 'password': 'password'},
            {'username': 'root', 'password': 'root'},
            {'username': 'user', 'password': 'user'},
            {'username': 'admin', 'password': '1234'},
            {'username': 'admin', 'password': '12345'},
            {'username': 'admin', 'password': '123456'},
            {'username': 'admin', 'password': 'password123'},
            {'username': 'admin', 'password': 'admin123'},
            {'username': 'admin', 'password': 'pass'}
        ]
        
        # Common vulnerabilities to check for
        vuln_checks = [
            {
                'id': 'default_credentials',
                'name': 'Default Credentials',
                'description': 'Device is using default credentials',
                'severity': 'High',
                'remediation': 'Change all default credentials immediately',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'firmware_updates',
                'name': 'Outdated Firmware',
                'description': 'Device is running outdated firmware',
                'severity': 'High',
                'remediation': 'Update to the latest firmware version',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'encryption',
                'name': 'Insecure Communication',
                'description': 'Device uses unencrypted communication',
                'severity': 'High',
                'remediation': 'Enable TLS/SSL for all communications',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'debug_endpoints',
                'name': 'Debug Endpoints',
                'description': 'Debug endpoints are exposed',
                'severity': 'Medium',
                'remediation': 'Disable debug endpoints in production',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'cors',
                'name': 'Insecure CORS',
                'description': 'Insecure CORS policy',
                'severity': 'Medium',
                'remediation': 'Implement proper CORS headers',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'directory_listing',
                'name': 'Directory Listing',
                'description': 'Directory listing is enabled',
                'severity': 'Low',
                'remediation': 'Disable directory listing',
                'status': 'Not Tested',
                'details': {}
            },
            {
                'id': 'http_methods',
                'name': 'Unsafe HTTP Methods',
                'description': 'Unsafe HTTP methods are enabled',
                'severity': 'Medium',
                'remediation': 'Disable unsafe HTTP methods (e.g., TRACE, TRACK, OPTIONS)',
                'status': 'Not Tested',
                'details': {}
            }
        ]
        
        # Convert to dictionary for easier access
        for vuln in vuln_checks:
            vulns[vuln['id']] = vuln
        
        # Test for default credentials if HTTP server is running
        try:
            import requests
            
            # Check if port 80 or 443 is open
            try:
                # Check HTTP
                response = requests.get(f"http://{self.target_ip}", timeout=3, verify=False)
                if response.status_code == 200 or response.status_code == 401:
                    self.log_message("HTTP server detected, checking for default credentials...", 'info')
                    
                    # Test a few common endpoints with default credentials
                    test_endpoints = ['/admin', '/login', '/', '/cgi-bin/luci']
                    
                    for endpoint in test_endpoints:
                        if self._stop_requested:
                            break
                            
                        url = f"http://{self.target_ip}{endpoint}"
                        self.update_progress(f"Testing default credentials on {url}...", 30)
                        
                        # Skip if we've already found credentials
                        if vulns['default_credentials']['status'] == 'Vulnerable':
                            continue
                            
                        for cred in default_creds:
                            if self._stop_requested:
                                break
                                
                            try:
                                # Try basic auth
                                response = requests.get(
                                    url,
                                    auth=(cred['username'], cred['password']),
                                    timeout=3,
                                    verify=False,
                                    allow_redirects=True
                                )
                                
                                # If we get a 200, credentials might be valid
                                if response.status_code == 200:
                                    vulns['default_credentials'].update({
                                        'status': 'Vulnerable',
                                        'details': {
                                            'url': url,
                                            'username': cred['username'],
                                            'password': cred['password'],
                                            'status_code': response.status_code
                                        }
                                    })
                                    self.log_message(
                                        f"Possible default credentials found: {cred['username']}:{cred['password']} at {url}",
                                        'high'
                                    )
                                    break
                                    
                            except RequestException:
                                continue
                                
                    if vulns['default_credentials']['status'] == 'Not Tested':
                        vulns['default_credentials']['status'] = 'Not Vulnerable'
                        
            except RequestException:
                self.log_message("Could not connect to HTTP server for credential testing", 'debug')
                vulns['default_credentials']['status'] = 'Test Skipped'
                vulns['default_credentials']['details'] = {'reason': 'Could not connect to HTTP server'}
                
        except ImportError:
            self.log_message("Skipping default credential check: requests module not available", 'warning')
            vulns['default_credentials']['status'] = 'Test Skipped'
            vulns['default_credentials']['details'] = {'reason': 'requests module not available'}
        
        self.update_progress("Vulnerability scan completed", 100)
        return vulns


class USBTab(QWidget):
    """Tab for USB device management and analysis."""
    
    # Define a signal for device updates
    devices_updated = pyqtSignal(list, str)
    
    def __init__(self, parent=None):
        """Initialize the USB tab."""
        super().__init__(parent)
        self.usb_analyzer = None
        self.scan_thread = None
        self._devices = []
        self.setup_ui()
        
        # Connect the signal to the update method
        self.devices_updated.connect(self._update_device_list, Qt.ConnectionType.QueuedConnection)
    
    def setup_ui(self):
        """Set up the USB tab UI."""
        layout = QVBoxLayout(self)
        
        # USB Device List
        self.device_table = QTableWidget()
        
        # Set column headers
        headers = [
            "Type", "Category", "Vendor ID", "Product ID", 
            "Manufacturer", "Product", "Description", "Serial"
        ]
        self.device_table.setColumnCount(len(headers))
        self.device_table.setHorizontalHeaderLabels(headers)
        
        # Set resize mode - let the columns size to contents but allow user to resize
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("Scan USB Devices")
        self.scan_button.clicked.connect(self.scan_usb_devices)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.scan_usb_devices)
        
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        
        # Add widgets to layout
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Connected USB Devices:"))
        layout.addWidget(self.device_table)
        
        # Add USB device info section
        self.device_info = QTextEdit()
        self.device_info.setReadOnly(True)
        layout.addWidget(QLabel("Device Details:"))
        layout.addWidget(self.device_info)
        
        # Connect device selection change
        self.device_table.itemSelectionChanged.connect(self.show_device_details)
    
    def scan_usb_devices(self):
        """Start scanning for USB devices."""
        try:
            if not USB_AVAILABLE:
                self.device_info.append("USB support not available. Please install pyusb (pip install pyusb).")
                self.scan_finished()
                return
                
            # Disable buttons during scan
            self.scan_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            
            # Clear previous results
            self.device_table.setRowCount(0)
            self.device_info.clear()
            
            # Create analyzer
            self.usb_analyzer = USBAnalyzer(self.update_status)
            
            if GUI_AVAILABLE:
                # Clean up any existing thread
                if hasattr(self, 'scan_thread') and self.scan_thread is not None:
                    if self.scan_thread.isRunning():
                        self.scan_thread.quit()
                        self.scan_thread.wait()
                
                # Create new thread
                self.scan_thread = QThread()
                self.usb_analyzer.moveToThread(self.scan_thread)
                
                # Connect signals
                self.scan_thread.started.connect(self.usb_analyzer.get_usb_devices)
                self.scan_thread.finished.connect(self.scan_thread.deleteLater)
                self.scan_thread.finished.connect(self.scan_finished)
                
                # Store devices for later access
                self._devices = []
                
                # Start the thread
                self.scan_thread.start()
                
                # Ensure thread is cleaned up if the tab is closed
                self.destroyed.connect(lambda: self.cleanup_scan_thread())
                
            else:
                # Fallback for non-GUI mode
                try:
                    devices = self.usb_analyzer.get_usb_devices()
                    self._update_device_list(devices, None)
                except Exception as e:
                    self.device_info.append(f"Error scanning USB devices: {str(e)}")
                finally:
                    self.scan_finished()
                    
        except Exception as e:
            self.device_info.append(f"Unexpected error starting scan: {str(e)}")
            import traceback
            self.device_info.append(traceback.format_exc())
            self.scan_finished()
            
    def cleanup_scan_thread(self):
        """Clean up the scan thread when the tab is closed."""
        if hasattr(self, 'scan_thread') and self.scan_thread is not None:
            if self.scan_thread.isRunning():
                self.scan_thread.quit()
                self.scan_thread.wait()
    
    @pyqtSlot(list, str)
    def _update_device_list(self, devices, error=''):
        """Update the device list with found USB devices (thread-safe).
        
        Args:
            devices: List of device dictionaries
            error: Optional error message
        """
        if error:
            self.device_info.append(f"Error: {error}")
            
        if not devices:
            self.device_info.append("No USB devices found")
            return
            
        try:
            self._devices = devices  # Store devices for selection
            self.device_table.setRowCount(len(devices))
            
            # Set column headers
            headers = [
                "Type", "Category", "Vendor ID", "Product ID", 
                "Manufacturer", "Description", "Serial"
            ]
            self.device_table.setColumnCount(len(headers))
            self.device_table.setHorizontalHeaderLabels(headers)
            
            # Set row data
            for row, device in enumerate(devices):
                # Get device information with defaults
                device_type = device.get('type', 'unknown').capitalize()
                category = device.get('category', 'unknown').capitalize()
                vendor_id = device.get('vendor_id', '0x0000')
                product_id = device.get('product_id', '0x0000')
                manufacturer = device.get('manufacturer', 'Unknown')
                product = device.get('product', 'Unknown')
                description = device.get('description', 'No description available')
                serial = device.get('serial_number', 'N/A')
                
                # Create and set items for each column
                items = [
                    QTableWidgetItem(device_type),
                    QTableWidgetItem(category),
                    QTableWidgetItem(vendor_id),
                    QTableWidgetItem(product_id),
                    QTableWidgetItem(manufacturer),
                    QTableWidgetItem(description),
                    QTableWidgetItem(serial)
                ]
                
                # Set background and text color based on device type
                bg_color = {
                    'phone': QColor(220, 240, 255),  # Light blue
                    'hub': QColor(255, 240, 220),    # Light orange
                    'security': QColor(255, 220, 220), # Light red
                    'unknown': QColor(240, 240, 240)  # Light gray
                }.get(device.get('type', 'unknown').lower(), QColor(255, 255, 255))
                
                # Set text color to black for better contrast
                text_color = QColor(0, 0, 0)  # Black text
                
                # Apply colors to each cell
                for col, item in enumerate(items):
                    item.setBackground(bg_color)
                    item.setForeground(text_color)
                    self.device_table.setItem(row, col, item)
            
            # Resize columns to fit content
            self.device_table.resizeColumnsToContents()
            
            # Enable sorting
            self.device_table.setSortingEnabled(True)
            
        except Exception as e:
            self.device_info.append(f"<span style='color: red;'>Error updating device list: {str(e)}</span>")
            import traceback
            self.device_info.append(f"<pre>{traceback.format_exc()}</pre>")
            
    def update_status(self, data):
        """Update status from USB analyzer callbacks."""
        if data.get('type') == 'progress':
            # Update progress if needed
            pass
        elif data.get('type') == 'log':
            level = data.get('level', 'info').upper()
            message = data.get('message', '')
            self.device_info.append(f"[{level}] {message}")
        elif data.get('type') == 'devices':
            # Update device list in the UI thread using the signal
            if GUI_AVAILABLE:
                devices = list(data.get('devices', []))
                error = data.get('error', '')
                self.devices_updated.emit(devices, error)
    
    def scan_finished(self):
        """Handle scan completion."""
        try:
            # Ensure we're in the main thread for UI updates
            if not hasattr(self, 'scan_button') or not hasattr(self, 'refresh_button'):
                return
                
            # Re-enable buttons
            self.scan_button.setEnabled(True)
            self.refresh_button.setEnabled(True)
            
            # Clean up the analyzer
            if hasattr(self, 'usb_analyzer'):
                try:
                    self.usb_analyzer.stop_scan()
                except:
                    pass
                self.usb_analyzer = None
                
        except Exception as e:
            if hasattr(self, 'device_info'):
                self.device_info.append(f"<span style='color: red;'>Error in scan_finished: {str(e)}</span>")
        
        if hasattr(self, 'device_info'):
            self.device_info.append("Scan completed.")
    
    # Old update_device_list method removed - replaced with _update_device_list
    
    def show_device_details(self):
        """Show detailed information for the selected USB device."""
        selected_items = self.device_table.selectedItems()
        if not selected_items:
            return
            
        # Get the selected row
        row = selected_items[0].row()
        
        # Get device details
        device_type = self.device_table.item(row, 0).text()
        category = self.device_table.item(row, 1).text()
        vendor_id = self.device_table.item(row, 2).text()
        product_id = self.device_table.item(row, 3).text()
        manufacturer = self.device_table.item(row, 4).text()
        description = self.device_table.item(row, 5).text()
        serial = self.device_table.item(row, 6).text()
        
        # Get the full device data from the USBAnalyzer
        if hasattr(self, 'usb_analyzer') and self.usb_analyzer:
            try:
                devices = self.usb_analyzer.get_usb_devices()
                device = next((d for d in devices if 
                             d.get('vendor_id') == vendor_id and 
                             d.get('product_id') == product_id and
                             d.get('serial_number') == serial), None)
            except:
                device = None
        else:
            device = None
        
        # Prepare HTML content
        details = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 10px; }}
                h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                .section {{ margin-bottom: 15px; }}
                .section-title {{ 
                    font-weight: bold; 
                    color: #3498db; 
                    margin: 10px 0 5px 0;
                    font-size: 1.1em;
                }}
                .property {{ margin: 5px 0; }}
                .property-name {{ 
                    display: inline-block; 
                    width: 160px; 
                    font-weight: bold; 
                    color: #7f8c8d;
                }}
                .device-header {{
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    border-left: 4px solid #3498db;
                }}
                .device-icon {{
                    font-size: 1.5em;
                    margin-right: 10px;
                    vertical-align: middle;
                }}
                .device-title {{
                    font-size: 1.5em;
                    font-weight: bold;
                    vertical-align: middle;
                }}
                .device-subtitle {{
                    color: #7f8c8d;
                    margin-left: 34px;
                    margin-top: -5px;
                }}
            </style>
        </head>
        <body>
            <div class="device-header">
                <span class="device-icon">
                    {'📱' if device_type.lower() in ['android', 'ios'] else '🔌'}
                </span>
                <span class="device-title">{description}</span>
                <div class="device-subtitle">
                    {manufacturer}
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Device Information</div>
                <div class="property">
                    <span class="property-name">Type:</span>
                    <span>{device_type}</span>
                </div>
                <div class="property">
                    <span class="property-name">Category:</span>
                    <span>{category}</span>
                </div>
                <div class="property">
                    <span class="property-name">Manufacturer:</span>
                    <span>{manufacturer}</span>
                </div>

                <div class="property">
                    <span class="property-name">Description:</span>
                    <span>{description}</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Hardware IDs</div>
                <div class="property">
                    <span class="property-name">Vendor ID:</span>
                    <span>{vendor_id}</span>
                </div>
                <div class="property">
                    <span class="property-name">Product ID:</span>
                    <span>{product_id}</span>
                </div>
                <div class="property">
                    <span class="property-name">Serial Number:</span>
                    <span>{serial or 'N/A'}</span>
                </div>
        """
        
        # Add additional details if available
        if device:
            details += "<div class=\"section\">"
            details += "<div class=\"section-title\">Connection Information</div>"
            
            if 'bus' in device:
                details += f"""
                <div class="property">
                    <span class="property-name">Bus:</span>
                    <span>{device['bus']}</span>
                </div>
                """
                
            if 'address' in device:
                details += f"""
                <div class="property">
                    <span class="property-name">Address:</span>
                    <span>{device['address']}</span>
                </div>
                """
                
            if 'port_numbers' in device and device['port_numbers']:
                details += f"""
                <div class="property">
                    <span class="property-name">Port Numbers:</span>
                    <span>{device['port_numbers']}</span>
                </div>
                """
                
            # Add device class information
            if 'device_class' in device:
                details += f"""
                <div class="property">
                    <span class="property-name">Device Class:</span>
                    <span>{device['device_class']}</span>
                </div>
                """
                
                # Add common device class descriptions
                class_info = {
                    '0x00': 'Use class information in the Interface Descriptors',
                    '0x01': 'Audio',
                    '0x02': 'Communications and CDC Control',
                    '0x03': 'HID (Human Interface Device)',
                    '0x05': 'Physical',
                    '0x06': 'Image',
                    '0x07': 'Printer',
                    '0x08': 'Mass Storage',
                    '0x09': 'Hub',
                    '0x0a': 'CDC-Data',
                    '0x0b': 'Smart Card',
                    '0x0d': 'Content Security',
                    '0x0e': 'Video',
                    '0x0f': 'Personal Healthcare',
                    '0x10': 'Audio/Video Devices',
                    '0xdc': 'Diagnostic Device',
                    '0xe0': 'Wireless Controller',
                    '0xef': 'Miscellaneous',
                    '0xfe': 'Application Specific',
                    '0xff': 'Vendor Specific'
                }
                
                if device['device_class'] in class_info:
                    details += f"""
                    <div class="property" style="margin-left: 20px; color: #7f8c8d;">
                        {class_info[device['device_class']]}
                    </div>
                    """
            
            details += "</div>"  # Close section
        
        # Close HTML
        details += """
            </body>
        </html>
        """
        
        self.device_info.setHtml(details)


class MobileEmbeddedToolsGUI(QMainWindow):
    """Main GUI window for the Mobile & Embedded Tools module."""
    
    def __init__(self, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        
        # Initialize variables
        self.scan_thread = None
        self.current_scan_type = None
        self.mobile_analyzer = None
        self.embedded_tester = None
        self.usb_analyzer = None
        self.results = {}
        
        # Setup the UI
        self.setup_ui()
        
        # Set window properties
        self.setWindowTitle("Hack Attack - Mobile & Embedded Tools")
        self.setMinimumSize(1200, 800)
        
        # Apply Hack Attack theme
        self.apply_styles()
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                background: #1e1e2e;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 5px;
                border-radius: 4px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTableWidget {
                background-color: #181825;
                border: none;
                font-size: 13px;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                background: #1e1e2e;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                width: 10px;
                margin: 0.5px;
            }
            QStatusBar {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border-top: 1px solid #45475a;
            }
            QSplitter::handle {
                background-color: #45475a;
                height: 4px;
            }
        """)
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget and main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create USB Devices tab
        self.setup_usb_tab()
        
        # Create main scanning tab with controls, results, and logs
        self.setup_scan_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Idle")
        self.status_bar.addPermanentWidget(self.progress_bar, 1)
    
    def setup_usb_tab(self):
        """Set up the USB devices tab."""
        self.usb_tab = USBTab()
        self.tabs.addTab(self.usb_tab, "USB Devices")
    
    def setup_scan_tab(self):
        """Set up the main scanning tab with controls, results, and logs."""
        scan_tab = QWidget()
        main_layout = QVBoxLayout(scan_tab)
        
        # Create a splitter to separate controls from results/logs
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Top part: Scan controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # Target input
        self.target_group = QGroupBox("Target Configuration")
        target_layout = QHBoxLayout()
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter target IP address or hostname")
        self.target_input.setMinimumWidth(300)
        
        target_layout.addWidget(QLabel("Target:"))
        target_layout.addWidget(self.target_input)
        target_layout.addStretch()
        self.target_group.setLayout(target_layout)
        
        # Scan type selection
        scan_type_group = QGroupBox("Scan Type")
        scan_type_layout = QHBoxLayout()
        
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItem("Mobile Device Analysis", "mobile")
        self.scan_type_combo.addItem("Embedded Device Testing", "embedded")
        
        scan_type_layout.addWidget(QLabel("Scan Type:"))
        scan_type_layout.addWidget(self.scan_type_combo)
        scan_type_layout.addStretch()
        
        # Buttons
        self.start_button = QPushButton("Start Scan")
        self.start_button.clicked.connect(self.start_scan)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        
        scan_type_layout.addWidget(self.start_button)
        scan_type_layout.addWidget(self.stop_button)
        scan_type_group.setLayout(scan_type_layout)
        
        # Add control widgets
        controls_layout.addWidget(self.target_group)
        controls_layout.addWidget(scan_type_group)
        controls_layout.addStretch()
        
        # Bottom part: Results and logs in a tab widget
        results_widget = QTabWidget()
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Monospace"))
        
        # Export button
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        
        results_layout.addWidget(QLabel("Scan Results:"))
        results_layout.addWidget(self.results_text)
        results_layout.addWidget(export_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        # Logs tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        
        # Logs text area
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Monospace"))
        
        # Clear logs button
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        logs_layout.addWidget(QLabel("Logs:"))
        logs_layout.addWidget(self.logs_text)
        logs_layout.addWidget(clear_logs_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        # Add tabs to results widget
        results_widget.addTab(results_tab, "Results")
        results_widget.addTab(logs_tab, "Logs")
        
        # Add widgets to splitter
        splitter.addWidget(controls_widget)
        splitter.addWidget(results_widget)
        
        # Set initial sizes (controls take 1/3, results/logs take 2/3)
        splitter.setSizes([int(self.height() / 3), int(self.height() * 2 / 3)])
        
        # Add tab
        self.tabs.addTab(scan_tab, "Network Devices")
        
        # Set minimum size for the results widget
        results_widget.setMinimumHeight(300)
    
    def log_message(self, message: str, level: str = 'info'):
        """Add a message to the log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Set color based on log level
        if level.lower() == 'error':
            color = 'red'
            prefix = '[ERROR]'
        elif level.lower() == 'warning':
            color = 'orange'
            prefix = '[WARN] '
        elif level.lower() == 'success':
            color = 'green'
            prefix = '[OK]   '
        elif level.lower() == 'high':
            color = 'darkred'
            prefix = '[HIGH] '
        elif level.lower() == 'debug':
            color = 'gray'
            prefix = '[DEBUG]'
        else:  # info
            color = 'black'
            prefix = '[INFO] '
        
        # Add message to log
        self.logs_text.append(f"<span style='color:{color}'><b>{timestamp} {prefix}</b> {message}</span>")
        
        # Auto-scroll to bottom
        self.logs_text.verticalScrollBar().setValue(self.logs_text.verticalScrollBar().maximum())
        
        # Also update status bar for important messages
        if level in ['error', 'warning', 'high']:
            self.status_bar.showMessage(f"{prefix} {message}", 5000)
    
    def clear_logs(self):
        """Clear the log window."""
        self.log_text.clear()
    
    def update_progress(self, message: str, value: int):
        """Update the progress bar and status."""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} - {value}%")
        QApplication.processEvents()
    
    def update_connection_ui(self):
        """Update the UI based on the selected connection type."""
        # Only network connection is available in this tab
        self.target_group.setVisible(True)
    
    def refresh_usb_devices(self):
        """Refresh the list of available USB devices."""
        if not USB_AVAILABLE:
            QMessageBox.warning(self, "USB Not Available", 
                              "pyusb is not installed. Install with: pip install pyusb")
            return
            
        self.usb_device_combo.clear()
        self.usb_analyzer = USBAnalyzer()
        devices = self.usb_analyzer.get_usb_devices()
        
        if not devices:
            self.usb_device_combo.addItem("No USB devices found", None)
            return
            
        for device in devices:
            name = f"{device.get('manufacturer', 'Unknown')} {device.get('product', 'Device')} ({device.get('vendor_id')}:{device.get('product_id')})"
            self.usb_device_combo.addItem(name, device)
    
    def get_selected_usb_device(self):
        """Get the currently selected USB device."""
        if self.usb_device_combo.currentData() is None:
            return None
        return self.usb_device_combo.currentData()
    
    def start_scan(self):
        """Start the selected scan."""
        scan_type = self.scan_type_combo.currentData()
        self.current_scan_type = f"network_{scan_type}"
        
        # Validate input
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", "Please enter a target IP address or hostname")
            return
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.results = {}
        self.results_text.clear()
        
        # Create and start scan thread
        self.scan_thread = ScanThread(target, scan_type, self.update_scan_status, conn_type)
        self.scan_thread.finished_signal.connect(self.scan_finished)
        self.scan_thread.start()
        
        self.log_message(f"Started {scan_type} scan on {target} ({conn_type})", "info")
    
    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.log_message("Stopping scan...", 'warning')
            self.stop_button.setEnabled(False)
    
    def update_scan_status(self, data):
        """Update the UI based on scan status updates.
        
        Args:
            data: Dictionary containing status information with keys:
                - type: Type of update ('progress', 'log', 'result')
                - message: Status message
                - level: Log level ('info', 'warning', 'error')
                - progress: Progress percentage (0-100)
                - result: Scan result data
        """
        if data.get('type') == 'progress':
            self.update_progress(data.get('message', ''), data.get('progress', 0))
        elif data.get('type') == 'log':
            self.log_message(data.get('message', ''), data.get('level', 'info'))
        elif data.get('type') == 'result':
            result = data.get('result', {})
            self.results.update(result)
            # Update results display
            self.results_text.append(f"\n=== Scan Results ===")
            for key, value in result.items():
                self.results_text.append(f"{key}: {value}")
    
    def scan_finished(self, success: bool):
        """Handle scan thread finishing.
        
        Args:
            success: Whether the scan completed successfully
        """
        # Re-enable UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Idle")
        
        if success:
            self.log_message(f"{self.current_scan_type.capitalize()} scan completed", 'success')
            self.status_bar.showMessage("Scan completed", 5000)
            
            # Switch to results tab
            self.tabs.setCurrentIndex(1)
        else:
            self.log_message("Scan failed or was stopped", 'error')
    
    def export_results(self):
        """Export scan results to a file."""
        if not self.results or ('mobile_analysis' not in self.results and 'embedded_testing' not in self.results):
            QMessageBox.warning(self, "No Results", "No scan results to export")
            return
        
        # Get save file name
        default_name = f"hack_attack_scan_{time.strftime('%Y%m%d_%H%M%S')}.json"
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Scan Results",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_name:
            return  # User cancelled
        
        # Add .json extension if not present
        if not file_name.lower().endswith('.json'):
            file_name += '.json'
        
        try:
            with open(file_name, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            self.log_message(f"Results exported to {file_name}", 'success')
            QMessageBox.information(self, "Export Successful", f"Scan results exported to:\n{file_name}")
            
        except Exception as e:
            error_msg = f"Failed to export results: {str(e)}"
            self.log_message(error_msg, 'error')
            QMessageBox.critical(self, "Export Failed", error_msg)


class ScanThread(QThread):
    """Thread for running scans in the background."""
    
    # Define signals
    progress_signal = pyqtSignal(str, int)  # message, progress
    log_signal = pyqtSignal(str, str)  # message, level
    result_signal = pyqtSignal(dict)  # partial results
    finished_signal = pyqtSignal(bool)  # success
    
    def __init__(self, target: str, scan_type: str, callback: Callable, conn_type: str = 'network'):
        """Initialize the scan thread.
        
        Args:
            target: Target IP address, hostname, or USB device ID
            scan_type: Type of scan ('mobile' or 'embedded')
            callback: Callback function for status updates
            conn_type: Type of connection ('network' or 'usb')
        """
        super().__init__()
        self.target = target
        self.scan_type = scan_type
        self.conn_type = conn_type
        self.callback = callback
        self._stop = False
        self.mobile_analyzer = None
        self.embedded_tester = None
    
    def run(self):
        """Run the scan."""
        try:
            results = {}
            
            # Setup callback
            def callback(data):
                if data.get('type') == 'progress':
                    self.progress_signal.emit(data.get('message', ''), data.get('progress', 0))
                elif data.get('type') == 'log':
                    self.log_signal.emit(data.get('message', ''), data.get('level', 'info'))
            
            # Run mobile scan if requested
            if self.scan_type in ['mobile', 'full']:
                self.log_signal.emit(f"Starting mobile device analysis on {self.target}", 'info')
                self.mobile_analyzer = MobileDeviceAnalyzer(self.target, callback=callback)
                
                # Check common ports
                self.progress_signal.emit("Scanning common ports...", 10)
                open_ports = self.mobile_analyzer.check_common_ports()
                results['mobile_analysis'] = {'open_ports': open_ports}
                self.result_signal.emit({'mobile_analysis': {'open_ports': open_ports}})
                
                if self._stop:
                    self.log_signal.emit("Mobile device analysis stopped by user", 'warning')
                    return
                
                # Scan device info
                self.progress_signal.emit("Gathering device information...", 50)
                device_info = self.mobile_analyzer.scan_device_info()
                results['mobile_analysis']['device_info'] = device_info
                self.result_signal.emit({'mobile_analysis': {'device_info': device_info}})
                
                if self._stop:
                    self.log_signal.emit("Mobile device analysis stopped by user", 'warning')
                    return
            
            # Run embedded scan if requested
            if self.scan_type in ['embedded', 'full']:
                self.log_signal.emit(f"Starting embedded device testing on {self.target}", 'info')
                self.embedded_tester = EmbeddedDeviceTester(self.target, callback=callback)
                
                # Test HTTP endpoints
                self.progress_signal.emit("Testing HTTP endpoints...", 60)
                http_endpoints = self.embedded_tester.test_http_endpoints()
                results['embedded_testing'] = {'http_endpoints': http_endpoints}
                self.result_signal.emit({'embedded_testing': {'http_endpoints': http_endpoints}})
                
                if self._stop:
                    self.log_signal.emit("Embedded device testing stopped by user", 'warning')
                    return
                
                # Check for vulnerabilities
                self.progress_signal.emit("Checking for common vulnerabilities...", 80)
                vulns = self.embedded_tester.check_common_vulnerabilities()
                results['embedded_testing']['vulnerability_checks'] = vulns
                self.result_signal.emit({'embedded_testing': {'vulnerability_checks': vulns}})
            
            # Emit final results
            self.progress_signal.emit("Scan completed", 100)
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.log_signal.emit(f"An error occurred: {str(e)}", 'error')
            self.finished_signal.emit(False)
    
    def stop(self):
        """Stop the scan."""
        self._stop = True
        if self.mobile_analyzer:
            self.mobile_analyzer.stop()
        if self.embedded_tester:
            self.embedded_tester.stop()


def main_gui():
    """Launch the GUI application."""
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for a consistent look
        
        # Set application info
        app.setApplicationName("Hack Attack - Mobile & Embedded Tools")
        app.setOrganizationName("Hack Attack")
        
        # Create and show the main window
        window = MobileEmbeddedToolsGUI()
        window.show()
        
        # Start the event loop
        return app.exec()
    except Exception as e:
        print(f"Error launching GUI: {str(e)}", file=sys.stderr)
        return 1


def main():
    """Launch the application."""
    if not GUI_AVAILABLE:
        print("Error: PyQt6 is required. Please install it with: pip install PyQt6")
        return 1
    
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for a consistent look
        
        # Set application info
        app.setApplicationName("Hack Attack - Mobile & Embedded Tools")
        app.setOrganizationName("Hack Attack")
        
        # Create and show the main window
        window = MobileEmbeddedToolsGUI()
        window.show()
        
        # Start the event loop
        return app.exec()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
