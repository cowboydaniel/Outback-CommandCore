"""Utility helpers for PC-X."""

from __future__ import annotations

import getpass
import importlib
import importlib.util
import logging
import os
import platform
import subprocess
import tempfile
from typing import Optional, Tuple

from PySide6.QtWidgets import QMessageBox

from app import config
from core.base import get_paths


_LOGGER_CONFIGURED = False


def configure_logging() -> None:
    """Configure module logging once."""
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    _LOGGER_CONFIGURED = True


def check_and_setup_sudoers(parent: Optional[object] = None) -> Tuple[bool, str]:
    """Check if sudoers setup is needed and run it with a GUI prompt if required."""
    try:
        test_cmd = ["sudo", "-n", "smartctl", "--version"]
        result = subprocess.run(test_cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True, "Already configured with passwordless sudo access"

        if parent:
            reply = QMessageBox.question(
                parent,
                "Elevated Permissions Required",
                "PC Tools requires elevated permissions to access hardware information.\n\n"
                "Would you like to set up passwordless sudo access now?\n\n"
                "You will be prompted for your password once.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return False, "User declined to set up passwordless sudo"

        _, pcx_dir = get_paths()
        script_path = os.path.join(pcx_dir, "setup_sudoers.sh")

        if not os.path.exists(script_path):
            return False, f"Setup script not found at {script_path}"

        os.chmod(script_path, 0o755)

        username = getpass.getuser()

        cmd = ["pkexec", "--user", "root", "bash", script_path]

        if parent:
            QMessageBox.information(
                parent,
                "Authentication Required",
                f"You will now be prompted for your password to set up passwordless sudo access for user '{username}'.",
            )

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True, "Successfully set up passwordless sudo access"
        error_msg = f"Failed to set up passwordless sudo: {result.stderr or 'Unknown error'}"
        if parent:
            QMessageBox.critical(parent, "Setup Failed", error_msg)
        return False, error_msg

    except Exception as exc:
        error_msg = f"Error setting up passwordless sudo: {str(exc)}"
        if parent:
            QMessageBox.critical(parent, "Error", error_msg)
        return False, error_msg


def check_and_install_dependencies() -> None:
    """Check for required system packages and install them if missing."""
    logging.info("Checking for required system packages...")

    distro_family = None
    try:
        if os.path.exists("/etc/debian_version"):
            distro_family = "debian"
        elif os.path.exists("/etc/redhat-release") or os.path.exists("/etc/fedora-release"):
            distro_family = "redhat"
        else:
            if importlib.util.find_spec("distro") is not None:
                distro = importlib.import_module("distro")
                dist_id = distro.id()
                if dist_id in ["ubuntu", "debian", "linuxmint", "pop"]:
                    distro_family = "debian"
                elif dist_id in ["fedora", "rhel", "centos", "rocky", "almalinux"]:
                    distro_family = "redhat"
    except Exception as exc:
        logging.error("Error detecting Linux distribution: %s", exc)

    if not distro_family or platform.system() != "Linux":
        logging.info("Auto-installation only supported on Linux. Skipping dependency check.")
        return

    install_cmd = "apt-get -y install" if distro_family == "debian" else "dnf -y install"

    missing_tools = []
    for package, binary in config.REQUIRED_TOOLS[distro_family].items():
        if binary:
            which_cmd = f"which {binary} 2>/dev/null"
            if subprocess.run(which_cmd, shell=True, check=False).returncode != 0:
                missing_tools.append(package)

    if missing_tools:
        cmd = f"sudo {install_cmd} {' '.join(missing_tools)}"
        print(f"Installing missing tools with: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"Failed to install packages: {exc}")
            print("Please make sure you have sudo permissions or install the following packages manually:")
            print(" ".join(missing_tools))
            return
        except Exception as exc:
            logging.error("Error installing system packages: %s", exc)
    else:
        logging.info("All required system packages are already installed")


def setup_passwordless_sudo() -> bool:
    """Set up passwordless sudo for required commands."""
    if os.geteuid() == 0:
        return True

    script_content = """#!/bin/bash
set -e

CURRENT_USER=$(who am i | awk '{print $1}')
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(whoami)
fi

echo "Setting up passwordless sudo for user: $CURRENT_USER"

SUDOERS_FILE="/etc/sudoers.d/99-nest-pc-tools"

if [ -f "$SUDOERS_FILE" ]; then
    echo "Backing up existing sudoers file to ${SUDOERS_FILE}.bak"
    cp "$SUDOERS_FILE" "${SUDOERS_FILE}.bak"
fi

echo "# Allow $CURRENT_USER to run required commands without a password" > "$SUDOERS_FILE"
echo "# This file was automatically generated by Nest PC Tools" >> "$SUDOERS_FILE"
echo "" >> "$SUDOERS_FILE"

cat << 'EOT' >> "$SUDOERS_FILE"
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/smartctl *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/hdparm *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/fdisk *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/parted *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/lsblk *
CURRENT_USER ALL=(root) NOPASSWD: /bin/mount *
CURRENT_USER ALL=(root) NOPASSWD: /bin/umount *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/wipefs *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/sfdisk *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lshw *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/dmidecode *
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/hddtemp *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lspci *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lsusb *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/killall *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/pkexec *
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/setcap *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/journalctl *
CURRENT_USER ALL=(root) NOPASSWD: /bin/cat /var/log/*
EOT

sed -i "s/CURRENT_USER/$CURRENT_USER/g" "$SUDOERS_FILE"
chmod 0440 "$SUDOERS_FILE"

if [ -x "/usr/sbin/smartctl" ]; then
    setcap cap_sys_rawio,cap_dac_override,cap_sys_admin,cap_sys_nice+ep /usr/sbin/smartctl 2>/dev/null || true
    echo "Set capabilities on smartctl for non-root access"
fi

echo ""
echo "Passwordless sudo setup complete!"
"""

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as temp_script:
            script_path = temp_script.name
            temp_script.write(script_content)

        os.chmod(script_path, 0o755)

        print("Setting up passwordless sudo. You may be prompted for your password...")
        result = subprocess.run(["sudo", "bash", script_path],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                text=True,
                                check=False)

        try:
            os.unlink(script_path)
        except OSError:
            pass

        if result.returncode == 0:
            print("Successfully set up passwordless sudo!")
            return True
        print("Failed to set up passwordless sudo:")
        print(result.stderr)
        return False

    except Exception as exc:
        print(f"Error setting up passwordless sudo: {exc}")
        return False
