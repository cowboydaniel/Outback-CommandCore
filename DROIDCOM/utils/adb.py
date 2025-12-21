"""
DROIDCOM - ADB Utility Functions
Functions for finding and interacting with ADB (Android Debug Bridge).
"""

import os
import shutil
import subprocess
import platform
import logging

from ..constants import IS_WINDOWS, DEFAULT_ADB_TIMEOUT


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

        # Skip the first line (header)
        for line in lines[1:]:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]
                    details = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    devices.append((serial, status, details))

        return devices

    except Exception as e:
        logging.error(f"Error getting connected devices: {e}")
        return []


def get_device_property(serial, prop_name, adb_path=None, timeout=5):
    """
    Get a device property using getprop.

    Args:
        serial: Device serial number
        prop_name: Property name (e.g., 'ro.product.model')
        adb_path: Path to ADB executable
        timeout: Command timeout

    Returns:
        str: Property value or empty string if not found
    """
    if adb_path is None:
        adb_path = 'adb'

    try:
        result = subprocess.run(
            [adb_path, '-s', serial, 'shell', 'getprop', prop_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return ''
    except Exception:
        return ''
