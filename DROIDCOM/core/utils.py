"""
DROIDCOM - Core utility helpers.
Shared helpers for file system operations, threading, and ADB access.
"""

import logging
import os
import platform
import shutil
import subprocess
import threading

from ..app.config import BACKUP_DIR_NAME, DEFAULT_ADB_TIMEOUT, IS_WINDOWS, SCREENSHOT_DIR_NAME


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
    return os.path.join(get_nest_directory(), "Screenshots", SCREENSHOT_DIR_NAME)


def get_backups_directory():
    """
    Get the backups directory path.

    Returns:
        str: Path to backups directory
    """
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


def truncate_string(value, max_length=50, suffix='...'):
    """
    Truncate a string to a maximum length.

    Args:
        value: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        str: Truncated string
    """
    if len(value) <= max_length:
        return value
    return value[:max_length - len(suffix)] + suffix


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


def find_adb_path(log_callback=None):
    """Find the ADB executable path on Windows"""
    def log_message(msg):
        if log_callback:
            log_callback(msg)
        else:
            logging.info(msg)

    try:
        # Check if ADB is in PATH
        adb_in_path = shutil.which('adb')
        if adb_in_path:
            log_message(f"Found ADB in PATH: {adb_in_path}")
            return adb_in_path

        # Check common installation locations
        common_locations = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'platform-tools', 'adb.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Android', 'platform-tools', 'adb.exe'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
        ]

        for location in common_locations:
            if os.path.exists(location):
                log_message(f"Found ADB at: {location}")
                return location

        # Check Android Studio installation
        try:
            if IS_WINDOWS:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Android Studio')
                install_path = winreg.QueryValueEx(key, 'Path')[0]
                sdk_path = os.path.join(install_path, 'sdk', 'platform-tools', 'adb.exe')
                if os.path.exists(sdk_path):
                    log_message(f"Found ADB in Android Studio: {sdk_path}")
                    return sdk_path
        except Exception as e:
            log_message(f"Could not check Android Studio registry: {str(e)}")

        log_message("Could not find ADB executable")
        return None
    except Exception as e:
        log_message(f"Error finding ADB path: {str(e)}")
        return None


def check_platform_tools(log_callback=None, dependencies_installed=False):
    """Check if Android platform tools are installed on Linux/Mac"""
    def log_message(msg):
        if log_callback:
            log_callback(msg)
        else:
            logging.info(msg)

    # If we've already run dependency installation and it succeeded, return True
    if dependencies_installed:
        log_message("Android dependencies already installed successfully")
        return True

    try:
        # Check if ADB is in PATH
        result = subprocess.run(
            ['adb', 'version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            log_message(f"ADB found: {result.stdout.strip()}")
            return True

        # Check common Linux/Mac installation locations
        common_locations = [
            '/usr/bin/adb',
            '/usr/local/bin/adb',
            '/opt/android-sdk/platform-tools/adb',
            os.path.expanduser('~/Android/Sdk/platform-tools/adb'),
            '/usr/lib/android-sdk/platform-tools/adb'
        ]

        for location in common_locations:
            if os.path.exists(location):
                log_message(f"Found ADB at: {location}")
                return True

        log_message("Could not find ADB executable")

        # Try auto-installing the dependencies
        if platform.system() == 'Linux':
            log_message("Attempting to install Android platform tools...")
            from ..dependencies import check_and_install_android_dependencies
            if check_and_install_android_dependencies():
                log_message("Successfully installed Android platform tools")
                return True

        return False
    except Exception as e:
        log_message(f"Error checking platform tools: {str(e)}")

        # Try auto-installing as a fallback
        if platform.system() == 'Linux':
            log_message("Attempting to install Android platform tools after error...")
            from ..dependencies import check_and_install_android_dependencies
            if check_and_install_android_dependencies():
                log_message("Successfully installed Android platform tools")
                return True

        return False


def run_adb_command(command, device_serial=None, timeout=DEFAULT_ADB_TIMEOUT, adb_path=None):
    """
    Run an ADB command and return the result.

    Args:
        command: The ADB command to run (without 'adb' prefix)
        device_serial: Optional device serial to target specific device
        timeout: Command timeout in seconds
        adb_path: Path to ADB executable (optional, will use 'adb' if not specified)

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    try:
        # Build the full command
        if adb_path:
            cmd = [adb_path]
        else:
            cmd = ['adb']

        # Add device serial if specified
        if device_serial:
            cmd.extend(['-s', device_serial])

        # Add the command parts
        if isinstance(command, str):
            cmd.extend(command.split())
        else:
            cmd.extend(command)

        # Run the command
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )

        return (result.returncode == 0, result.stdout, result.stderr)

    except subprocess.TimeoutExpired:
        return (False, '', f'Command timed out after {timeout} seconds')
    except Exception as e:
        return (False, '', str(e))


def get_connected_devices(adb_path=None):
    """
    Get list of connected Android devices.

    Returns:
        list: List of tuples (serial, status, details)
    """
    if adb_path is None:
        adb_path = 'adb'

    try:
        result = subprocess.run(
            [adb_path, 'devices', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        devices = []
        lines = result.stdout.strip().split('\n')

        # Skip first line (header)
        for line in lines[1:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                details = ' '.join(parts[2:]) if len(parts) > 2 else ''
                devices.append((serial, status, details))

        return devices
    except Exception:
        return []


__all__ = [
    'format_size',
    'format_bytes',
    'run_in_thread',
    'ensure_directory',
    'get_home_directory',
    'get_nest_directory',
    'get_screenshots_directory',
    'get_backups_directory',
    'parse_key_value_output',
    'truncate_string',
    'is_valid_package_name',
    'find_adb_path',
    'check_platform_tools',
    'run_adb_command',
    'get_connected_devices',
]
