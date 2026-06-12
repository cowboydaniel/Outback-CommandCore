"""Utility helpers for PC-X."""

from __future__ import annotations

import getpass
import importlib
import importlib.util
import logging
import os
import platform
import shutil
import subprocess
import tempfile
from typing import Optional, Sequence, Tuple

from PySide6.QtWidgets import QMessageBox

from app import config

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


def run_privileged_command(
    command: Sequence[str],
    *,
    timeout: Optional[float] = None,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Run a privileged command from a GUI session.

    PC-X is commonly launched from a desktop shortcut, so commands must not rely
    on an interactive terminal for password entry.  Prefer already-configured
    passwordless sudo, then fall back to PolicyKit so the desktop authentication
    agent can display a GUI password prompt.
    """
    command_list = list(command)
    if command_list and os.sep not in command_list[0]:
        resolved_binary = shutil.which(command_list[0])
        if resolved_binary:
            command_list[0] = resolved_binary

    run_kwargs = {
        "timeout": timeout,
        "capture_output": capture_output,
        "text": text,
        "check": False,
    }

    if os.geteuid() == 0:
        return subprocess.run(command_list, **run_kwargs)

    if shutil.which("sudo"):
        sudo_result = subprocess.run(["sudo", "-n", *command_list], **run_kwargs)
        if sudo_result.returncode == 0:
            return sudo_result

    if shutil.which("pkexec"):
        return subprocess.run(["pkexec", *command_list], **run_kwargs)

    raise RuntimeError(
        "Elevated privileges are required, but neither passwordless sudo nor "
        "PolicyKit pkexec is available. Install polkit/pkexec or configure "
        "passwordless sudo for PC-X hardware tools."
    )


def check_and_setup_sudoers(parent: Optional[object] = None) -> Tuple[bool, str]:
    """Offer GUI-driven setup for passwordless sudo if it is not configured."""
    try:
        if os.geteuid() == 0:
            return True, "Already running with root privileges"

        if shutil.which("sudo"):
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
                "A desktop authentication prompt will ask for your password.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return False, "User declined to set up passwordless sudo"

            QMessageBox.information(
                parent,
                "Authentication Required",
                "Approve the upcoming desktop authentication prompt to configure PC-X hardware access.",
            )

        if setup_passwordless_sudo():
            return True, "Successfully set up passwordless sudo access"

        error_msg = (
            "Failed to set up passwordless sudo. Check that PolicyKit pkexec is installed "
            "and a desktop authentication agent is running."
        )
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
        install_args = install_cmd.split() + missing_tools
        logging.info("Installing missing tools with elevated privileges: %s", " ".join(install_args))
        try:
            result = run_privileged_command(install_args, capture_output=False, text=True)
            if result.returncode != 0:
                print("Failed to install packages.")
                print("Please make sure you have administrator permissions or install the following packages manually:")
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

CURRENT_USER="$1"
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(logname 2>/dev/null || true)
fi
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(who am i | awk '{print $1}')
fi
if [ -z "$CURRENT_USER" ]; then
    echo "Unable to determine the desktop user for sudoers setup" >&2
    exit 1
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

        print("Setting up passwordless sudo. A desktop authentication prompt may appear...")
        result = run_privileged_command(["bash", script_path, getpass.getuser()])

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
