"""Configuration constants for OMNISCRIBE."""
import os

APP_NAME = "OMNISCRIBE"
APP_VERSION = "1.0.0"
WINDOW_TITLE = "OMNISCRIBE - Scripting Control Suite"
MIN_WINDOW_SIZE = (1000, 700)
ICON_RELATIVE_PATH = os.path.join("icons", "omniscribe.png")

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

DEFAULT_SCRIPT_TEMPLATE = "# Write your script here\nprint('Hello, OMNISCRIBE!')"
