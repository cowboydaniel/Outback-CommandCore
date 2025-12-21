"""
DROIDCOM - Android Device Management Tool
Main application module that combines all features.
"""

from PySide6 import QtCore, QtWidgets
import subprocess
import os
import shutil
import platform
import logging
import tempfile
import zipfile
import urllib.request

from .constants import IS_WINDOWS
from .dependencies import check_and_install_android_dependencies
from .utils.qt_dispatcher import emit_ui, get_ui_dispatcher

# Import UI mixin
from .ui.widgets import WidgetsMixin

# Import feature mixins
from .features.connection import ConnectionMixin
from .features.device_info import DeviceInfoMixin
from .features.screenshot import ScreenshotMixin
from .features.backup import BackupMixin
from .features.file_manager import FileManagerMixin
from .features.app_manager import AppManagerMixin
from .features.logcat import LogcatMixin
from .features.system_tools import SystemToolsMixin
from .features.device_control import DeviceControlMixin
from .features.security import SecurityMixin
from .features.debugging import DebuggingMixin
from .features.advanced_tests import AdvancedTestsMixin
from .features.automation import AutomationMixin


class AndroidToolsModule(
    WidgetsMixin,
    ConnectionMixin,
    DeviceInfoMixin,
    ScreenshotMixin,
    BackupMixin,
    FileManagerMixin,
    AppManagerMixin,
    LogcatMixin,
    SystemToolsMixin,
    DeviceControlMixin,
    SecurityMixin,
    DebuggingMixin,
    AdvancedTestsMixin,
    AutomationMixin,
    QtWidgets.QWidget
):
    """Main Android Tools Module that combines all feature mixins."""

    def __init__(self, parent):
        # Check dependencies when module is instantiated
        if platform.system() == 'Linux':
            self.dependencies_installed = check_and_install_android_dependencies()

        super().__init__(parent)
        self.parent = parent
        self.device_connected = False
        self.device_info = {}
        self.device_serial = None  # Initialize device_serial to None
        self.threads = []  # Keep track of threads
        self.log_text = None  # Initialize to None, will be created in create_widgets

        # Initialize UiDispatcher on the UI thread to prevent threading issues
        # This must be done before any worker threads are spawned
        get_ui_dispatcher(self)

        # Set the ADB path early so it's available throughout the application
        if IS_WINDOWS:
            self.adb_path = self._find_adb_path()
        else:
            # On Linux/Mac, the command is simply 'adb' if installed
            self.adb_path = "adb"

        # Initialize platform_tools_installed to False by default
        # This needs to be set before create_widgets is called
        self.platform_tools_installed = False

        # Create UI first so logging works properly
        self.create_widgets()

        # Now check for platform-specific tools after UI is created
        if IS_WINDOWS:
            # Windows-specific initialization
            self.adb_path = self._find_adb_path()
            self.platform_tools_installed = self.adb_path is not None
        else:
            # Linux/Mac initialization
            self.platform_tools_installed = self._check_platform_tools()

        # Update UI to reflect the actual tools status
        tools_status = "✅ Installed" if self.platform_tools_installed else "❌ Not Installed"
        self.tools_label.setText(f"Android Platform Tools: {tools_status}")

        # Automatically try to connect to device when module is opened, if tools are installed
        if self.platform_tools_installed:
            # Use after() to ensure the UI is fully loaded before attempting connection
            self.log_message("Android Tools module loaded - will attempt auto-connection shortly")
            # Increase delay to 1000ms to ensure UI is fully loaded
            QtCore.QTimer.singleShot(1000, self.auto_connect_sequence)

    def _find_adb_path(self):
        """Find the ADB executable path on Windows"""
        try:
            # Check if ADB is in PATH
            adb_in_path = shutil.which('adb')
            if adb_in_path:
                self.log_message(f"Found ADB in PATH: {adb_in_path}")
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
                    self.log_message(f"Found ADB at: {location}")
                    return location

            # Check Android Studio installation
            try:
                if IS_WINDOWS:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Android Studio')
                    install_path = winreg.QueryValueEx(key, 'Path')[0]
                    sdk_path = os.path.join(install_path, 'sdk', 'platform-tools', 'adb.exe')
                    if os.path.exists(sdk_path):
                        self.log_message(f"Found ADB in Android Studio: {sdk_path}")
                        return sdk_path
            except Exception as e:
                self.log_message(f"Could not check Android Studio registry: {str(e)}")

            self.log_message("Could not find ADB executable")
            return None
        except Exception as e:
            self.log_message(f"Error finding ADB path: {str(e)}")
            return None

    def _check_platform_tools(self):
        """Check if Android platform tools are installed on Linux/Mac"""
        # If we've already run dependency installation and it succeeded, return True
        if hasattr(self, 'dependencies_installed') and self.dependencies_installed:
            self.log_message("Android dependencies already installed successfully")
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
                self.log_message(f"ADB found: {result.stdout.strip()}")
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
                    self.log_message(f"Found ADB at: {location}")
                    return True

            self.log_message("Could not find ADB executable")

            # Try auto-installing the dependencies
            if platform.system() == 'Linux':
                self.log_message("Attempting to install Android platform tools...")
                if check_and_install_android_dependencies():
                    self.log_message("Successfully installed Android platform tools")
                    return True

            return False
        except Exception as e:
            self.log_message(f"Error checking platform tools: {str(e)}")

            # Try auto-installing as a fallback
            if platform.system() == 'Linux':
                self.log_message("Attempting to install Android platform tools after error...")
                if check_and_install_android_dependencies():
                    self.log_message("Successfully installed Android platform tools")
                    return True

            return False

    def install_platform_tools(self):
        """Install Android platform tools"""
        self._run_in_thread(self._install_platform_tools_task)

    def _install_platform_tools_task(self):
        """Worker thread to download and install Android platform tools"""
        try:
            self.log_message("Installing Android platform tools...")
            self.update_status("Installing Android platform tools...")

            # Create a temp directory for downloads
            temp_dir = tempfile.mkdtemp()
            self.log_message(f"Created temporary directory: {temp_dir}")

            # Determine the correct download URL based on platform
            if IS_WINDOWS:
                platform_name = "windows"
                file_name = "platform-tools-latest-windows.zip"
            else:
                # For Linux/Mac
                if platform.system().lower() == "darwin":
                    platform_name = "mac"
                    file_name = "platform-tools-latest-darwin.zip"
                else:
                    platform_name = "linux"
                    file_name = "platform-tools-latest-linux.zip"

            download_url = f"https://dl.google.com/android/repository/{file_name}"
            zip_path = os.path.join(temp_dir, file_name)

            # Download the platform tools
            self.log_message(f"Downloading platform tools from {download_url}...")
            self.update_status("Downloading platform tools...")

            try:
                urllib.request.urlretrieve(download_url, zip_path)
                self.log_message("Download completed successfully")
            except Exception as e:
                self.log_message(f"Download failed: {str(e)}")
                self.update_status("Installation failed")
                QtWidgets.QMessageBox.critical(
                    self, "Download Error", f"Failed to download Android platform tools: {str(e)}"
                )
                return

            # Determine the installation directory
            if IS_WINDOWS:
                install_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android')
            else:
                install_dir = os.path.expanduser("~/Android")

            # Create the directory if it doesn't exist
            os.makedirs(install_dir, exist_ok=True)
            self.log_message(f"Installing to: {install_dir}")

            # Extract the ZIP file
            self.log_message("Extracting platform tools...")
            self.update_status("Extracting platform tools...")

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(install_dir)
                self.log_message("Extraction completed successfully")
            except Exception as e:
                self.log_message(f"Extraction failed: {str(e)}")
                self.update_status("Installation failed")
                QtWidgets.QMessageBox.critical(
                    self, "Extraction Error", f"Failed to extract Android platform tools: {str(e)}"
                )
                return

            # Set up PATH environment variable
            platform_tools_path = os.path.join(install_dir, "platform-tools")
            self.log_message(f"Platform tools installed at: {platform_tools_path}")

            # Add to PATH for the current session
            if platform_tools_path not in os.environ['PATH']:
                os.environ['PATH'] = platform_tools_path + os.pathsep + os.environ['PATH']
                self.log_message("Added platform-tools to PATH for current session")

            # Instruct user on permanent PATH setup
            if IS_WINDOWS:
                path_instructions = (
                    "To use ADB from any command prompt, you need to add it to your PATH:\n\n"
                    f"1. Add this to your PATH: {platform_tools_path}\n"
                    "2. Open System Properties > Advanced > Environment Variables\n"
                    "3. Edit the PATH variable and add the path above\n"
                    "4. Restart any open command prompts"
                )
            else:
                path_instructions = (
                    "To use ADB from any terminal, add this line to your .bashrc or .zshrc file:\n\n"
                    f"export PATH=\"$PATH:{platform_tools_path}\""
                )

            # Clean up temporary files
            try:
                shutil.rmtree(temp_dir)
                self.log_message("Cleaned up temporary files")
            except Exception as e:
                self.log_message(f"Failed to clean up temporary files: {str(e)}")

            # Update UI to reflect successful installation
            emit_ui(self, lambda: self.tools_label.setText("Android Platform Tools: ✅ Installed"))
            self.platform_tools_installed = True

            # Show success message with PATH instructions
            self.update_status("Installation completed")
            self.log_message("Android platform tools installed successfully")

            QtWidgets.QMessageBox.information(
                self,
                "Installation Complete",
                f"Android platform tools have been installed successfully.\n\n{path_instructions}"
            )

        except Exception as e:
            self.log_message(f"Installation error: {str(e)}")
            self.update_status("Installation failed")
            QtWidgets.QMessageBox.critical(
                self, "Installation Error", f"Failed to install Android platform tools: {str(e)}"
            )

    def run_adb_command(self, command, device_serial=None, timeout=60):
        """Run an ADB command and return the result

        Args:
            command: List of command arguments (excluding adb binary)
            device_serial: Optional device serial number
            timeout: Command timeout in seconds

        Returns:
            tuple: (success, output)
        """
        try:
            # Use stored adb path or default to 'adb' in PATH
            adb_cmd = self.adb_path if self.adb_path else 'adb'

            # Construct full command
            cmd = [adb_cmd]

            # Add device serial if specified
            if device_serial:
                cmd.extend(['-s', device_serial])

            # Add the actual command
            cmd.extend(command)

            self.log_message(f"Running: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
