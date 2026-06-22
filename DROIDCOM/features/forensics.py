"""
DROIDCOM - Forensics Feature Module
Launchers and pipelines for third-party mobile forensics tooling
(Andriller, ALEAPP, MVT, Autopsy) used against the connected Android
device or a prior extraction/backup.
"""

from PySide6 import QtWidgets
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from ..utils.qt_dispatcher import emit_ui

ALEAPP_REPO_URL = "https://github.com/abrignoni/ALEAPP.git"
ALEAPP_DIR = Path.home() / ".local" / "share" / "outback-commandcore" / "ALEAPP"


class ForensicsMixin:
    """Mixin providing launchers for external mobile-forensics tools."""

    def run_andriller(self):
        """Launch Andriller, which auto-detects ADB devices on its own.

        Andriller's pip package has no `andriller` console script (it only
        ships a legacy `andriller-gui.py`), so it must be run as a module.
        """
        if importlib.util.find_spec("andriller") is None:
            self._offer_pip_install("andriller", "Andriller")
            return

        self.log_message("Launching Andriller...")
        try:
            subprocess.Popen([sys.executable, "-m", "andriller"])
            self.update_status("Andriller launched")
        except Exception as e:
            self.log_message(f"Failed to launch Andriller: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "Andriller Error", f"Failed to launch Andriller: {str(e)}"
            )

    def run_aleapp(self):
        """Run the ALEAPP artifact parser against an extraction/backup folder.

        ALEAPP has no PyPI package or console-script entry point, so it is
        obtained by cloning its GitHub repo on demand and run as a script.
        """
        aleapp_script = ALEAPP_DIR / "aleapp.py"
        if not aleapp_script.exists():
            self._offer_git_clone_install(ALEAPP_REPO_URL, ALEAPP_DIR, "ALEAPP")
            return

        input_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Android Extraction / Backup Folder"
        )
        if not input_dir:
            return

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select ALEAPP Report Output Folder"
        )
        if not output_dir:
            return

        self._run_in_thread(lambda: self._run_forensic_tool_task(
            sys.executable, [str(aleapp_script), "-t", "fs", "-i", input_dir, "-o", output_dir], "ALEAPP"
        ))

    def run_mvt_check(self):
        """Run MVT (Mobile Verification Toolkit) against the device or a backup."""
        if not shutil.which("mvt-android"):
            self._offer_pip_install("mvt", "MVT (Mobile Verification Toolkit)")
            return

        choice = QtWidgets.QMessageBox.question(
            self,
            "MVT Android Check",
            "Run a live indicator-of-compromise check over ADB on the connected "
            "device?\n\nChoose 'No' to check a previously captured ADB backup instead.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
        )
        if choice == QtWidgets.QMessageBox.Cancel:
            return

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select MVT Report Output Folder"
        )
        if not output_dir:
            return

        if choice == QtWidgets.QMessageBox.Yes:
            if not self.device_connected or not self.device_info.get('serial'):
                QtWidgets.QMessageBox.information(
                    self, "Not Connected", "Please connect to a device first."
                )
                return
            args = ["check-adb", "--output", output_dir, "--serial", self.device_info['serial']]
        else:
            backup_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select ADB Backup File", filter="Android Backup (*.ab)"
            )
            if not backup_file:
                return
            args = ["check-backup", "--output", output_dir, backup_file]

        self._run_in_thread(lambda: self._run_forensic_tool_task("mvt-android", args, "MVT"))

    def launch_autopsy(self):
        """Launch the Autopsy forensic suite for case-based analysis of extracted data."""
        self._launch_or_offer_install(
            binary="autopsy",
            pip_package=None,
            tool_name="Autopsy",
            install_hint=(
                "Autopsy is a standalone Java application and is not distributed via pip.\n\n"
                "Install the modern Autopsy 4.x via Snap (do NOT use 'apt-get install autopsy' -- "
                "that package is the abandoned, non-functional Autopsy 2.24):\n"
                "  sudo snap install autopsy\n\n"
                "Or download it directly from https://www.autopsy.com/download/"
            ),
        )

    # -- shared helpers -----------------------------------------------------

    def _launch_or_offer_install(self, binary, pip_package, tool_name, install_hint=None):
        path = shutil.which(binary)
        if not path:
            if pip_package:
                self._offer_pip_install(pip_package, tool_name)
            else:
                QtWidgets.QMessageBox.information(
                    self, f"{tool_name} Not Found",
                    install_hint or f"{tool_name} ({binary}) was not found on PATH."
                )
            return

        self.log_message(f"Launching {tool_name}...")
        try:
            subprocess.Popen([path])
            self.update_status(f"{tool_name} launched")
        except Exception as e:
            self.log_message(f"Failed to launch {tool_name}: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, f"{tool_name} Error", f"Failed to launch {tool_name}: {str(e)}"
            )

    def _offer_pip_install(self, pip_package, tool_name):
        choice = QtWidgets.QMessageBox.question(
            self, f"{tool_name} Not Found",
            f"{tool_name} was not found on PATH.\n\n"
            f"Install it now with 'pip install --user {pip_package}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if choice == QtWidgets.QMessageBox.Yes:
            self._run_in_thread(lambda: self._pip_install_forensic_tool_task(pip_package, tool_name))

    def _offer_git_clone_install(self, repo_url, dest, tool_name):
        choice = QtWidgets.QMessageBox.question(
            self, f"{tool_name} Not Found",
            f"{tool_name} was not found.\n\n"
            f"Clone it now from {repo_url} and install its dependencies?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if choice == QtWidgets.QMessageBox.Yes:
            self._run_in_thread(lambda: self._git_clone_install_task(repo_url, dest, tool_name))

    def _git_clone_install_task(self, repo_url, dest, tool_name):
        self.update_status(f"Installing {tool_name}...")
        self.log_message(f"Cloning {tool_name} from {repo_url}...")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(dest)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300,
            )
            if result.returncode != 0:
                self.log_message(f"{tool_name} clone failed: {result.stderr.strip()}")
                self.update_status(f"{tool_name} install failed")
                emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                    self, "Install Error", f"Failed to clone {tool_name}: {result.stderr.strip()}"
                ))
                return

            req_file = dest / "requirements.txt"
            if req_file.exists():
                self.log_message(f"Installing {tool_name} dependencies...")
                pip_result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--user", "-r", str(req_file)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300,
                )
                if pip_result.returncode != 0:
                    self.log_message(f"{tool_name} dependency install failed: {pip_result.stderr.strip()}")
                    self.update_status(f"{tool_name} install failed")
                    emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                        self, "Install Error",
                        f"Failed to install {tool_name} dependencies: {pip_result.stderr.strip()}"
                    ))
                    return

            self.log_message(f"{tool_name} installed successfully")
            self.update_status(f"{tool_name} installed")
            emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                self, "Install Complete",
                f"{tool_name} installed successfully. You may need to re-run the action."
            ))
        except Exception as e:
            self.log_message(f"Error installing {tool_name}: {str(e)}")
            self.update_status(f"{tool_name} install failed")
            emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                self, "Install Error", f"Failed to install {tool_name}: {str(e)}"
            ))

    def _pip_install_forensic_tool_task(self, pip_package, tool_name):
        self.update_status(f"Installing {tool_name}...")
        self.log_message(f"Installing {tool_name} via pip...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", pip_package],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300,
            )
            if result.returncode == 0:
                self.log_message(f"{tool_name} installed successfully")
                self.update_status(f"{tool_name} installed")
                emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                    self, "Install Complete",
                    f"{tool_name} installed successfully. You may need to re-run the action."
                ))
            else:
                self.log_message(f"{tool_name} install failed: {result.stderr.strip()}")
                self.update_status(f"{tool_name} install failed")
                emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                    self, "Install Error", f"Failed to install {tool_name}: {result.stderr.strip()}"
                ))
        except Exception as e:
            self.log_message(f"Error installing {tool_name}: {str(e)}")
            emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                self, "Install Error", f"Failed to install {tool_name}: {str(e)}"
            ))

    def _run_forensic_tool_task(self, binary, args, tool_name):
        self.update_status(f"Running {tool_name}...")
        self.log_message(f"Running: {binary} {' '.join(args)}")
        try:
            result = subprocess.run(
                [binary] + args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1800,
            )
            if result.stdout:
                for line in result.stdout.strip().splitlines()[-50:]:
                    self.log_message(line)

            if result.returncode == 0:
                self.update_status(f"{tool_name} completed")
                self.log_message(f"{tool_name} completed successfully")
                emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                    self, f"{tool_name} Complete", f"{tool_name} finished successfully."
                ))
            else:
                self.update_status(f"{tool_name} failed")
                error_tail = result.stderr.strip()[-500:]
                self.log_message(f"{tool_name} failed: {error_tail}")
                emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                    self, f"{tool_name} Error", f"{tool_name} failed: {error_tail}"
                ))
        except subprocess.TimeoutExpired:
            self.update_status(f"{tool_name} timed out")
            self.log_message(f"{tool_name} timed out")
        except Exception as e:
            self.update_status(f"{tool_name} failed")
            self.log_message(f"Error running {tool_name}: {str(e)}")
            emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                self, f"{tool_name} Error", f"Failed to run {tool_name}: {str(e)}"
            ))
