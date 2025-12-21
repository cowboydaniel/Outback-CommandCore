"""
DROIDCOM - Helper Utility Functions
General helper functions used throughout the application.
"""

import os
import threading
import logging


def format_size(size_bytes):
    """
    Format a size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string (e.g., "1.5 GB")
    """
    try:
        size_bytes = int(size_bytes)
        if size_bytes < 0:
            return "N/A"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0

        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024.0
            unit_index += 1

        if unit_index == 0:
            return f"{size_bytes} {units[unit_index]}"
        else:
            return f"{size_bytes:.2f} {units[unit_index]}"
    except (ValueError, TypeError):
        return "N/A"


def format_bytes(bytes_val):
    """
    Format bytes to human-readable format.

    Args:
        bytes_val: Value in bytes

    Returns:
        str: Formatted string (e.g., "1.5 MB")
    """
    try:
        bytes_val = float(bytes_val)
        if bytes_val < 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                if unit == 'B':
                    return f"{int(bytes_val)} {unit}"
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0

        return f"{bytes_val:.2f} PB"
    except (ValueError, TypeError):
        return "0 B"


def run_in_thread(target_function, *args, daemon=True, **kwargs):
    """
    Run a function in a separate thread.

    Args:
        target_function: The function to run
        *args: Positional arguments to pass to the function
        daemon: Whether the thread should be a daemon thread
        **kwargs: Keyword arguments to pass to the function

    Returns:
        threading.Thread: The started thread
    """
    def thread_wrapper():
        try:
            target_function(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in thread: {e}", exc_info=True)

    thread = threading.Thread(target=thread_wrapper, daemon=daemon)
    thread.start()
    return thread


def ensure_directory(path):
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory {path}: {e}")
        return False


def get_home_directory():
    """
    Get the user's home directory.

    Returns:
        str: Path to home directory
    """
    return os.path.expanduser("~")


def get_nest_directory():
    """
    Get the Nest directory path (used for storing app data).

    Returns:
        str: Path to Nest directory
    """
    return os.path.join(get_home_directory(), "Nest")


def get_screenshots_directory():
    """
    Get the screenshots directory path.

    Returns:
        str: Path to screenshots directory
    """
    from ..constants import SCREENSHOT_DIR_NAME
    return os.path.join(get_nest_directory(), "Screenshots", SCREENSHOT_DIR_NAME)


def get_backups_directory():
    """
    Get the backups directory path.

    Returns:
        str: Path to backups directory
    """
    from ..constants import BACKUP_DIR_NAME
    return os.path.join(get_nest_directory(), BACKUP_DIR_NAME)


def parse_key_value_output(output, separator='='):
    """
    Parse output that contains key-value pairs.

    Args:
        output: String output to parse
        separator: The separator between key and value

    Returns:
        dict: Dictionary of key-value pairs
    """
    result = {}
    for line in output.strip().split('\n'):
        if separator in line:
            parts = line.split(separator, 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                result[key] = value
    return result


def truncate_string(s, max_length=50, suffix='...'):
    """
    Truncate a string to a maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        str: Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def is_valid_package_name(package_name):
    """
    Check if a string is a valid Android package name.

    Args:
        package_name: The package name to check

    Returns:
        bool: True if valid package name format
    """
    if not package_name:
        return False

    # Basic validation: must contain at least one dot and only valid characters
    parts = package_name.split('.')
    if len(parts) < 2:
        return False

    for part in parts:
        if not part:  # Empty segment
            return False
        if not part[0].isalpha() and part[0] != '_':
            return False
        for char in part:
            if not (char.isalnum() or char == '_'):
                return False

    return True
