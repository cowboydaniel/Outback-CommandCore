"""
DROIDCOM - Constants and Platform Detection
Android device management and debugging toolkit.
"""

import platform
import logging

# Set up logging for Android Tools Module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Check if running on Windows or Linux/Mac
IS_WINDOWS = platform.system().lower() == 'windows'

# Application version
APP_VERSION = '1.0.0'

# Default ADB port for WiFi connections
DEFAULT_ADB_PORT = 5555

# Screenshot directory name
SCREENSHOT_DIR_NAME = "Android"

# Backup directory name
BACKUP_DIR_NAME = "AndroidBackups"

# Default timeout values (in seconds)
DEFAULT_ADB_TIMEOUT = 60
SHORT_ADB_TIMEOUT = 5
LONG_ADB_TIMEOUT = 300

# UI Constants
MIN_WINDOW_WIDTH = 1024
MIN_WINDOW_HEIGHT = 600
CATEGORY_WIDTH = 480
CATEGORY_HEIGHT = 360

# Button width
DEFAULT_BUTTON_WIDTH = 18
WIDE_BUTTON_WIDTH = 20
EXTRA_WIDE_BUTTON_WIDTH = 30

# Device list height
DEVICE_LISTBOX_HEIGHT = 3

# Log text height
LOG_TEXT_HEIGHT = 6
LOG_TEXT_WIDTH = 80

# Debug text height
DEBUG_TEXT_HEIGHT = 5
DEBUG_TEXT_WIDTH = 80
