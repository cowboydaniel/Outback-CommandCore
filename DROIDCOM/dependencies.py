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


def _get_scrcpy_version():
    """Return (major, minor) or (0, 0) if not installed / not parseable."""
    import re
    try:
        out = subprocess.run(
            ["scrcpy", "--version"], capture_output=True, text=True
        ).stdout
        m = re.search(r"scrcpy\s+(\d+)\.(\d+)", out)
        if m:
            return (int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    return (0, 0)


def check_and_install_scrcpy():
    """Ensure scrcpy >= 2.1 is installed.

    scrcpy 2.1 introduced --keyboard=uhid / --mouse=uhid which inject
    input via a virtual HID device, bypassing the Android InputManager
    reflection path that NPEs on some devices.  No older version is ever
    installed as a fallback — that would break uhid input.

    Strategy (mirrors the manual install procedure):
      1. Install build dependencies via pkexec apt-get
      2. Clone the scrcpy repo into a temp directory
      3. Run ./install_release.sh (builds and installs the latest release)
    """
    if platform.system() != 'Linux':
        return True

    MIN_VERSION = (2, 1)
    current = _get_scrcpy_version()
    if current >= MIN_VERSION:
        logging.info(f"scrcpy {current[0]}.{current[1]} already satisfies >= 2.1")
        return True

    ver_str = f"{current[0]}.{current[1]}" if current != (0, 0) else "(not installed)"
    logging.info(f"scrcpy {ver_str} < 2.1 — installing latest from source...")

    import tempfile

    # Step 1: install build dependencies.
    build_deps = [
        "ffmpeg", "libsdl2-2.0-0", "adb", "wget",
        "gcc", "git", "pkg-config", "meson", "ninja-build",
        "libsdl2-dev", "libavcodec-dev", "libavdevice-dev",
        "libavformat-dev", "libavutil-dev", "libswresample-dev",
        "libusb-1.0-0", "libusb-1.0-0-dev",
    ]
    logging.info(f"Installing scrcpy build dependencies: {' '.join(build_deps)}")
    result = subprocess.run(
        ["pkexec", "apt-get", "-y", "install"] + build_deps,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        logging.error(f"Failed to install build dependencies: {result.stderr.strip()}")
        return False

    # Step 2 & 3: clone repo and run install_release.sh.
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_dir = os.path.join(tmpdir, "scrcpy")
            logging.info("Cloning scrcpy repository...")
            result = subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/Genymobile/scrcpy.git", clone_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                logging.error(f"git clone failed: {result.stderr.strip()}")
                return False

            logging.info("Running install_release.sh...")
            result = subprocess.run(
                ["pkexec", "bash", "./install_release.sh"],
                cwd=clone_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                logging.error(f"install_release.sh failed: {result.stderr.strip()}")
                return False

    except Exception as e:
        logging.error(f"Error during scrcpy installation: {e}")
        return False

    new_ver = _get_scrcpy_version()
    if new_ver >= MIN_VERSION:
        logging.info(f"scrcpy successfully installed: {new_ver[0]}.{new_ver[1]}")
        return True

    logging.error(
        f"install_release.sh completed but scrcpy reports {new_ver[0]}.{new_ver[1]}"
    )
    return False


def run_dependency_check():
    """Run dependency check on Linux systems"""
    if platform.system() == 'Linux':
        adb_ok = check_and_install_android_dependencies()
        scrcpy_ok = check_and_install_scrcpy()
        return adb_ok and scrcpy_ok
    return True
