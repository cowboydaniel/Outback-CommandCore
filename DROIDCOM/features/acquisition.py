"""
DROIDCOM - Forensic Acquisition & Case Management
Case/exhibit organisation, write-blocker enforcement, bit-for-bit logical
imaging with hash verification, the evidence integrity log, and
chain-of-custody report generation.
"""

import os
import subprocess
import time
from pathlib import Path

from PySide6 import QtWidgets

from ..core.evidence import (
    CaseManager,
    ChainOfCustodyReport,
    WriteBlocker,
    WriteBlockedError,
    sha256_file,
)
from ..utils.qt_dispatcher import emit_ui


class AcquisitionMixin:
    """Mixin providing forensic case management and device acquisition."""

    # -- case lifecycle -------------------------------------------------

    def new_case_dialog(self):
        """Open a dialog to start a new forensic case (creates on-disk case folders)."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("New Forensic Case")
        dialog.setModal(True)
        layout = QtWidgets.QFormLayout(dialog)

        case_edit = QtWidgets.QLineEdit()
        exhibit_edit = QtWidgets.QLineEdit()
        examiner_edit = QtWidgets.QLineEdit()
        root_edit = QtWidgets.QLineEdit(str(Path.home() / "DroidcomCases"))
        browse_btn = QtWidgets.QPushButton("Browse...")

        def browse():
            chosen = QtWidgets.QFileDialog.getExistingDirectory(dialog, "Select Case Storage Root")
            if chosen:
                root_edit.setText(chosen)

        browse_btn.clicked.connect(browse)
        root_row = QtWidgets.QHBoxLayout()
        root_row.addWidget(root_edit)
        root_row.addWidget(browse_btn)

        layout.addRow("Case Number:", case_edit)
        layout.addRow("Exhibit Number:", exhibit_edit)
        layout.addRow("Examiner Name:", examiner_edit)
        layout.addRow("Case Storage Root:", root_row)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        if not case_edit.text().strip() or not exhibit_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Missing Information", "Case number and exhibit number are required.")
            return

        case = CaseManager(
            case_number=case_edit.text(),
            exhibit_number=exhibit_edit.text(),
            examiner_name=examiner_edit.text().strip() or "UNSPECIFIED",
            root=Path(root_edit.text().strip() or str(Path.home() / "DroidcomCases")),
        )
        case.open()

        self.active_case = case
        if not hasattr(self, "write_blocker") or self.write_blocker is None:
            self.write_blocker = WriteBlocker(evidence_log=case.evidence_log, enabled=True)
        else:
            self.write_blocker.set_evidence_log(case.evidence_log)
            self.write_blocker.enabled = True

        self.log_message(
            f"Case opened: {case.case_number}/{case.exhibit_number} "
            f"(examiner: {case.examiner_name}) at {case.case_dir}"
        )
        self.update_status(f"Active case: {case.case_number}/{case.exhibit_number}")
        QtWidgets.QMessageBox.information(
            self, "Case Opened",
            f"Case folder created:\n{case.case_dir}\n\n"
            "Write blocker is ENABLED. No write commands will be sent to the "
            "device while this case is active.",
        )

    def toggle_write_blocker(self):
        """Enable or disable write-blocker enforcement for the active case."""
        if not getattr(self, "write_blocker", None):
            QtWidgets.QMessageBox.information(self, "No Active Case", "Open a case first.")
            return

        if self.write_blocker.enabled:
            confirm = QtWidgets.QMessageBox.warning(
                self, "Disable Write Blocker",
                "This will allow write commands (install, push, uninstall, etc.) "
                "to reach the device. This action is permanently recorded in the "
                "evidence log.\n\nDisable write blocker?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if confirm != QtWidgets.QMessageBox.Yes:
                return
            self.write_blocker.enabled = False
            self.write_blocker.evidence_log.record("WRITE_BLOCKER_DISABLED", {"examiner": self.active_case.examiner_name})
            self.log_message("WARNING: Write blocker disabled")
        else:
            self.write_blocker.enabled = True
            self.write_blocker.evidence_log.record("WRITE_BLOCKER_ENABLED", {"examiner": self.active_case.examiner_name})
            self.log_message("Write blocker re-enabled")

        self.update_status(f"Write blocker: {'ENABLED' if self.write_blocker.enabled else 'DISABLED'}")

    def _check_write_blocker(self, adb_args, description=""):
        """Shared guard other feature mixins call before any device-mutating command.

        Returns True if the action is allowed, False if it was blocked (and
        shows the user why).
        """
        blocker = getattr(self, "write_blocker", None)
        if not blocker and getattr(self, "forensic_mode", False):
            blocker = WriteBlocker(enabled=True)
        if not blocker:
            return True
        try:
            blocker.check(adb_args, description)
            return True
        except WriteBlockedError as e:
            self.log_message(f"BLOCKED by write blocker: {description or ' '.join(map(str, adb_args))}")
            emit_ui(self, lambda: QtWidgets.QMessageBox.critical(
                self, "Write Blocked",
                f"{str(e)}\n\nDisable the write blocker first if this action is intentional."
            ))
            return False

    # -- acquisition imaging ---------------------------------------------

    def run_device_acquisition(self):
        """Acquire a bit-for-bit logical image of the device's accessible storage."""
        if not self.device_connected or not self.device_info.get("serial"):
            QtWidgets.QMessageBox.information(self, "Not Connected", "Please connect to a device first.")
            return
        if not getattr(self, "active_case", None):
            QtWidgets.QMessageBox.information(self, "No Active Case", "Open a forensic case before acquiring evidence.")
            return

        source_path, ok = QtWidgets.QInputDialog.getText(
            self, "Acquisition Source", "Device path to image (e.g. /sdcard):", text="/sdcard"
        )
        if not ok or not source_path.strip():
            return

        self._run_in_thread(lambda: self._acquisition_task(source_path.strip()))

    def _acquisition_task(self, source_path):
        case = self.active_case
        serial = self.device_info.get("serial")
        adb_cmd = self.adb_path if getattr(self, "adb_path", None) else "adb"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_name = f"{case.case_number}_{case.exhibit_number}_{timestamp}.tar"
        image_path = case.images_dir / image_name

        self.update_status("Acquiring device image...")
        self.log_message(f"Starting logical acquisition of {source_path} -> {image_path}")
        case.evidence_log.record(
            "ACQUISITION_STARTED",
            {"source_path": source_path, "image_path": str(image_path), "device_serial": serial},
        )

        tar_cmd = [adb_cmd, "-s", serial, "exec-out", "tar", "-cf", "-", source_path]
        if not self._check_write_blocker(tar_cmd, "device acquisition (read-only tar stream)"):
            return

        try:
            with open(image_path, "wb") as out_file:
                proc = subprocess.Popen(tar_cmd, stdout=out_file, stderr=subprocess.PIPE)
                _, stderr = proc.communicate(timeout=3600)

            if proc.returncode not in (0, None) and not image_path.exists():
                self.log_message(f"Acquisition failed: {stderr.decode(errors='ignore')[-500:]}")
                self.update_status("Acquisition failed")
                case.evidence_log.record("ACQUISITION_FAILED", {"error": stderr.decode(errors="ignore")[-500:]})
                return

            self.log_message("Computing image hash (sha256)...")
            image_hash = sha256_file(image_path)
            image_size = image_path.stat().st_size

            case.evidence_log.record(
                "ACQUISITION_COMPLETED",
                {
                    "source_path": source_path,
                    "image_path": str(image_path),
                    "image_sha256": image_hash,
                    "image_size_bytes": image_size,
                    "device_serial": serial,
                    "device_info": self.device_info,
                },
            )

            hash_file = image_path.with_suffix(".sha256")
            hash_file.write_text(f"{image_hash}  {image_name}\n", encoding="utf-8")

            self.log_message(f"Acquisition complete: {image_path} ({image_size} bytes)")
            self.log_message(f"SHA-256: {image_hash}")
            self.update_status("Acquisition completed")

            emit_ui(self, lambda: QtWidgets.QMessageBox.information(
                self, "Acquisition Complete",
                f"Image saved to:\n{image_path}\n\nSHA-256:\n{image_hash}\n\n"
                "This hash and every step of this acquisition has been recorded "
                "in the case evidence log.",
            ))
        except subprocess.TimeoutExpired:
            self.log_message("Acquisition timed out")
            self.update_status("Acquisition timed out")
            case.evidence_log.record("ACQUISITION_FAILED", {"error": "timeout"})
        except Exception as e:
            self.log_message(f"Acquisition error: {str(e)}")
            self.update_status("Acquisition failed")
            case.evidence_log.record("ACQUISITION_FAILED", {"error": str(e)})

    def verify_acquisition_image(self):
        """Re-hash a previously acquired image and compare it to its recorded hash."""
        if not getattr(self, "active_case", None):
            QtWidgets.QMessageBox.information(self, "No Active Case", "Open a forensic case first.")
            return

        image_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Acquisition Image", str(self.active_case.images_dir)
        )
        if not image_file:
            return

        self._run_in_thread(lambda: self._verify_image_task(Path(image_file)))

    def _verify_image_task(self, image_path):
        case = self.active_case
        self.update_status("Verifying image integrity...")
        recorded_hash = None
        for entry in case.evidence_log.entries():
            if entry["action"] == "ACQUISITION_COMPLETED" and entry["details"].get("image_path") == str(image_path):
                recorded_hash = entry["details"].get("image_sha256")

        current_hash = sha256_file(image_path)
        match = recorded_hash is not None and current_hash == recorded_hash

        case.evidence_log.record(
            "IMAGE_VERIFIED",
            {"image_path": str(image_path), "recorded_sha256": recorded_hash,
             "current_sha256": current_hash, "match": match},
        )

        self.log_message(f"Verification of {image_path.name}: current={current_hash} recorded={recorded_hash} match={match}")
        self.update_status("Image verified -- MATCH" if match else "Image verification -- MISMATCH")

        emit_ui(self, lambda: QtWidgets.QMessageBox.information(
            self, "Image Verification",
            f"Recorded hash: {recorded_hash or 'unknown'}\nCurrent hash:  {current_hash}\n\n"
            + ("Hashes MATCH -- image integrity confirmed." if match else
               "Hashes DO NOT MATCH -- image may have been altered or no recorded hash was found."),
        ))

    # -- evidence log / chain of custody ----------------------------------

    def view_evidence_log(self):
        """Display the active case's evidence log and verify its hash chain."""
        if not getattr(self, "active_case", None):
            QtWidgets.QMessageBox.information(self, "No Active Case", "Open a forensic case first.")
            return

        case = self.active_case
        intact, break_idx = case.evidence_log.verify()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Evidence Log -- {case.case_number}/{case.exhibit_number}")
        dialog.resize(800, 600)
        layout = QtWidgets.QVBoxLayout(dialog)

        status_label = QtWidgets.QLabel(
            "Hash chain: INTACT" if intact else f"Hash chain: BROKEN at entry {break_idx}"
        )
        status_label.setStyleSheet(f"color: {'green' if intact else 'red'}; font-weight: bold;")
        layout.addWidget(status_label)

        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        lines = []
        for entry in case.evidence_log.entries():
            lines.append(f"[{entry['timestamp']}] {entry['action']}  {entry['details']}")
            lines.append(f"    entry_hash={entry['entry_hash']}")
        text.setPlainText("\n".join(lines))
        layout.addWidget(text)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def generate_chain_of_custody_report(self):
        """Generate a chain-of-custody report (PDF if reportlab is installed, else text)."""
        if not getattr(self, "active_case", None):
            QtWidgets.QMessageBox.information(self, "No Active Case", "Open a forensic case first.")
            return

        case = self.active_case
        output_path = case.reports_dir / f"chain_of_custody_{int(time.time())}.pdf"

        acquisition_summary = {}
        for entry in case.evidence_log.entries():
            if entry["action"] == "ACQUISITION_COMPLETED":
                acquisition_summary = entry["details"]

        report_path = ChainOfCustodyReport.generate(
            case=case,
            device_info=self.device_info,
            acquisition_summary=acquisition_summary,
            output_path=output_path,
        )

        case.evidence_log.record("CUSTODY_REPORT_GENERATED", {"report_path": str(report_path)})
        self.log_message(f"Chain of custody report generated: {report_path}")
        self.update_status("Chain of custody report generated")

        QtWidgets.QMessageBox.information(
            self, "Report Generated", f"Chain of custody report saved to:\n{report_path}"
        )
