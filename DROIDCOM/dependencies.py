"""
DROIDCOM - Dependency Management
Functions for checking and installing required Android support packages.
"""

import os
import platform
import subprocess
import shutil
import logging

from .app.config import IS_WINDOWS


def check_and_install_android_dependencies():
    """Check for required Android support packages and install them if missing"""
    logging.info("Checking for required Android support packages...")

    # Only run on Linux
    if platform.system() != 'Linux':
        return

    # Define required tools by distro family
    required_tools = {
        'debian': {
            'android-tools-adb': 'adb',
            'android-tools-fastboot': 'fastboot',
            'android-tools-mkbootimg': None,  # No specific binary to check
            'android-sdk-platform-tools-common': None,  # No specific binary to check
            'adb': 'adb'  # Some distros have this as a separate package
        },
        'redhat': {
            'android-tools': 'adb',
            'android-tools-fastboot': 'fastboot'
        }
    }

    # Detect distro family
    distro_family = None
    try:
        if os.path.exists('/etc/debian_version'):
            distro_family = 'debian'
        elif os.path.exists('/etc/redhat-release') or os.path.exists('/etc/fedora-release'):
            distro_family = 'redhat'
        else:
            # Try to use the distro module if available
            try:
                import distro
                dist_id = distro.id()
                if dist_id in ['ubuntu', 'debian', 'linuxmint', 'pop']:
                    distro_family = 'debian'
                elif dist_id in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']:
                    distro_family = 'redhat'
            except ImportError:
                logging.warning(
                    "distro module unavailable; falling back to file checks only for distro detection."
                )
    except Exception as e:
        logging.error(f"Error detecting Linux distribution: {e}")
        return

    if not distro_family:
        logging.warning("Could not detect Linux distribution. Skipping dependency check.")
        return

    # Determine installation command
    if distro_family == 'debian':
        install_cmd = 'apt-get -y install'
    elif distro_family == 'redhat':
        install_cmd = 'dnf -y install'

    # Check for missing tools
    missing_tools = []
    for package, binary in required_tools[distro_family].items():
        if binary:
            # Check if binary exists in PATH
            which_cmd = f"which {binary} 2>/dev/null"
            if subprocess.run(which_cmd, shell=True).returncode != 0:
                missing_tools.append(package)
        else:
            # For packages without a specific binary to check, always include them
            # if we can't find adb (which depends on them)
            adb_path = shutil.which('adb')
            if adb_path is None:
                missing_tools.append(package)

    # Remove duplicates while preserving order
    missing_tools = list(dict.fromkeys(missing_tools))

    # Install missing tools if any
    if missing_tools:
        try:
            logging.info(f"Missing Android support packages: {', '.join(missing_tools)}")
            cmd = f"pkexec {install_cmd} {' '.join(missing_tools)}"
            logging.info(f"Installing missing packages with: {cmd}")

            # Run installation command
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                logging.info("Successfully installed missing Android support packages")
                return True
            else:
                logging.error(f"Failed to install packages: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error installing Android support packages: {e}")
            return False
    else:
        logging.info("All required Android support packages are already installed")
        return True


def run_dependency_check():
    """Run dependency check on Linux systems"""
    if platform.system() == 'Linux':
        return check_and_install_android_dependencies()
    return True
