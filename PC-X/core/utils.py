"""Utility helpers for PC-X."""

from __future__ import annotations

import atexit
import getpass
import importlib
import importlib.util
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
from typing import Optional, Sequence, Tuple

from app import config

_LOGGER_CONFIGURED = False
_PRIVILEGED_HELPER = None
_PRIVILEGED_HELPER_LOCK = threading.RLock()

SMARTCTL_EXIT_STATUS_MESSAGES = {
    0: "command line did not parse",
    1: "device open failed or the device did not return an identify response",
    2: "a SMART command failed or SMART data failed a checksum check",
    3: "SMART status reports the disk is failing",
    4: "a prefail SMART attribute is at or below its threshold",
    5: "a usage or age SMART attribute is at or below its threshold",
    6: "the device error log contains errors",
    7: "the device self-test log contains errors",
}


def describe_smartctl_exit_status(returncode: int) -> str:
    """Return a human-readable explanation of smartctl's bitmask exit code."""
    if returncode == 0:
        return "smartctl completed successfully"

    messages = [
        message
        for bit, message in SMARTCTL_EXIT_STATUS_MESSAGES.items()
        if returncode & (1 << bit)
    ]
    known_mask = sum(1 << bit for bit in SMARTCTL_EXIT_STATUS_MESSAGES)
    unknown_bits = returncode & ~known_mask
    if unknown_bits:
        messages.append(f"unknown status bits: {unknown_bits}")

    if not messages:
        messages.append("no detailed status bits were set")

    return f"smartctl exit status {returncode}: " + "; ".join(messages)


def format_smartctl_output(
    device: str,
    returncode: int,
    stdout: Optional[str],
    stderr: Optional[str],
) -> str:
    """Format smartctl output without hiding useful reports on non-zero statuses.

    smartctl uses a bitmask exit status, so non-zero does not necessarily mean
    there is no useful report. SMART reports are commonly written to stdout even
    when a status bit is set, so PC-X should display stdout first and add the
    decoded status as context instead of showing a blank error pane.
    """
    sections = []
    stdout = stdout or ""
    stderr = stderr or ""

    if stdout.strip():
        sections.append(stdout.rstrip())
    if stderr.strip():
        sections.append(f"smartctl messages:\n{stderr.rstrip()}")

    if returncode != 0:
        sections.append(f"PC-X note: {describe_smartctl_exit_status(returncode)}")

    if sections:
        return "\n\n".join(sections)

    return f"SMART command completed but returned no data for {device}."


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


def _privileged_helper_script() -> str:
    """Return the source for the long-lived root command helper."""
    return r'''
import json
import subprocess
import sys

print(json.dumps({"ready": True}), flush=True)

for line in sys.stdin:
    try:
        request = json.loads(line)
        command = request["command"]
        timeout = request.get("timeout")
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        response = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        response = {
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {exc.timeout} seconds",
        }
    except Exception as exc:
        response = {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Privileged helper error: {exc}",
        }
    print(json.dumps(response), flush=True)
'''


class _PrivilegedCommandHelper:
    """Keep one authenticated PolicyKit session alive for the app lifetime."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._script_path: Optional[str] = None

    def run(
        self,
        command: Sequence[str],
        *,
        timeout: Optional[float] = None,
    ) -> subprocess.CompletedProcess:
        """Run a command through the persistent root helper."""
        self._ensure_started()
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Privileged helper is not available")

        payload = json.dumps({"command": list(command), "timeout": timeout})
        try:
            self._process.stdin.write(f"{payload}\n")
            self._process.stdin.flush()
            response_line = self._process.stdout.readline()
        except BrokenPipeError:
            self.stop()
            raise RuntimeError("Privileged helper stopped unexpectedly") from None

        if not response_line:
            stderr = ""
            if self._process.stderr:
                stderr = self._process.stderr.read()
            self.stop()
            raise RuntimeError(f"Privileged helper exited without a response. {stderr}".strip())

        response = json.loads(response_line)
        return subprocess.CompletedProcess(
            list(command),
            response.get("returncode", 1),
            response.get("stdout", ""),
            response.get("stderr", ""),
        )

    def _ensure_started(self) -> None:
        if self._process and self._process.poll() is None:
            return

        self.stop()
        pkexec_path = shutil.which("pkexec")
        if not pkexec_path:
            raise RuntimeError(
                "Elevated privileges are required, but PolicyKit pkexec is not available. "
                "Install polkit/pkexec or configure passwordless sudo for PC-X hardware tools."
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as helper_file:
            helper_file.write(_privileged_helper_script())
            self._script_path = helper_file.name
        os.chmod(self._script_path, 0o700)

        self._process = subprocess.Popen(
            [pkexec_path, sys.executable, "-u", self._script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if not self._process.stdout:
            self.stop()
            raise RuntimeError("Privileged helper did not provide stdout")

        ready_line = self._process.stdout.readline()
        if not ready_line:
            stderr = ""
            if self._process.stderr:
                stderr = self._process.stderr.read()
            self.stop()
            raise RuntimeError(f"PolicyKit authentication failed. {stderr}".strip())

        ready = json.loads(ready_line)
        if not ready.get("ready"):
            self.stop()
            raise RuntimeError("Privileged helper did not start correctly")

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=1)
        self._process = None

        if self._script_path:
            try:
                os.unlink(self._script_path)
            except OSError:
                pass
            self._script_path = None


def _stop_privileged_helper() -> None:
    """Stop the authenticated helper when PC-X exits."""
    global _PRIVILEGED_HELPER
    with _PRIVILEGED_HELPER_LOCK:
        if _PRIVILEGED_HELPER:
            _PRIVILEGED_HELPER.stop()
            _PRIVILEGED_HELPER = None


def _run_with_privileged_helper(
    command: Sequence[str],
    *,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess:
    """Run a command through one cached PolicyKit authentication session."""
    global _PRIVILEGED_HELPER
    with _PRIVILEGED_HELPER_LOCK:
        if _PRIVILEGED_HELPER is None:
            _PRIVILEGED_HELPER = _PrivilegedCommandHelper()
        return _PRIVILEGED_HELPER.run(command, timeout=timeout)


atexit.register(_stop_privileged_helper)


def run_privileged_command(
    command: Sequence[str],
    *,
    timeout: Optional[float] = None,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Run a privileged command from a GUI session.

    PC-X is commonly launched from a desktop shortcut, so commands must not rely
    on an interactive terminal for password entry. Prefer already-configured
    passwordless sudo. If sudo is not ready, start one PolicyKit-authenticated
    root helper and reuse it until the application exits, so the user only has
    to approve one desktop authentication prompt per PC-X session.
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

    if not text:
        raise RuntimeError("Binary privileged command output is not supported by the desktop helper")

    return _run_with_privileged_helper(command_list, timeout=timeout)


def check_and_setup_sudoers(parent: Optional[object] = None) -> Tuple[bool, str]:
    """Offer GUI-driven setup for passwordless sudo if it is not configured."""
    if parent:
        from PySide6.QtWidgets import QMessageBox

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
