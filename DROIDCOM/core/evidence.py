"""
DROIDCOM - Forensic Evidence Handling
Case management, a hash-chained evidence integrity log, a write-blocker
guard, and chain-of-custody report generation for forensic acquisitions.

This module has no Qt/UI dependency so it can be unit tested in isolation.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


GENESIS_HASH = "0" * 64


class WriteBlockedError(Exception):
    """Raised when an action is rejected by the write blocker."""


class EvidenceLog:
    """Append-only, hash-chained audit trail.

    Each entry's hash is computed over its own content plus the previous
    entry's hash, so any edit, reorder, or deletion of a prior line breaks
    the chain. ``verify()`` walks the whole file and recomputes the chain
    to detect tampering.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def _last_hash(self) -> str:
        last = GENESIS_HASH
        if self.path.exists() and self.path.stat().st_size:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        last = json.loads(line)["entry_hash"]
        return last

    @staticmethod
    def _hash_entry(prev_hash: str, timestamp: str, action: str, details: dict) -> str:
        payload = json.dumps(
            {"prev_hash": prev_hash, "timestamp": timestamp, "action": action, "details": details},
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def record(self, action: str, details: Optional[dict] = None) -> dict:
        """Append a new immutable entry and return it."""
        details = details or {}
        prev_hash = self._last_hash()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        entry_hash = self._hash_entry(prev_hash, timestamp, action, details)
        entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def entries(self) -> list:
        out = []
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        return out

    def verify(self) -> tuple:
        """Recompute the hash chain. Returns (is_intact, first_break_index_or_None)."""
        prev_hash = GENESIS_HASH
        for idx, entry in enumerate(self.entries()):
            if entry["prev_hash"] != prev_hash:
                return False, idx
            expected = self._hash_entry(
                entry["prev_hash"], entry["timestamp"], entry["action"], entry["details"]
            )
            if expected != entry["entry_hash"]:
                return False, idx
            prev_hash = entry["entry_hash"]
        return True, None


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute the sha256 of a file on disk, streaming in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize(value: str) -> str:
    return _SAFE_ID.sub("_", value.strip()) or "UNSPECIFIED"


@dataclass
class CaseManager:
    """Organises acquisitions/reports on disk by case number and exhibit number."""

    case_number: str
    exhibit_number: str
    examiner_name: str
    root: Path
    case_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self):
        self.case_number = _sanitize(self.case_number)
        self.exhibit_number = _sanitize(self.exhibit_number)
        self.root = Path(self.root)
        self.case_dir = self.root / self.case_number / self.exhibit_number
        self.images_dir = self.case_dir / "images"
        self.reports_dir = self.case_dir / "reports"
        self.logs_dir = self.case_dir / "logs"
        for d in (self.images_dir, self.reports_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.evidence_log = EvidenceLog(self.logs_dir / "evidence_log.jsonl")

    def open(self):
        self.evidence_log.record(
            "CASE_OPENED",
            {
                "case_number": self.case_number,
                "exhibit_number": self.exhibit_number,
                "examiner": self.examiner_name,
                "case_id": self.case_id,
            },
        )


class WriteBlocker:
    """Enforces (and logs) a read-only guarantee against the connected device.

    When enabled, any action classified as a write is rejected before it
    reaches ADB. Every check -- allowed or blocked -- is appended to the
    bound evidence log, so the guarantee is independently auditable rather
    than just a docstring promise.
    """

    # adb subcommands (or shell verbs) that mutate device state.
    WRITE_ADB_SUBCOMMANDS = {"push", "install", "install-multiple", "uninstall", "sideload", "restore"}
    WRITE_SHELL_VERBS = (
        "pm install", "pm uninstall", "pm clear", "pm disable", "pm enable",
        "rm ", "rm-rf", "mkdir", "touch ", "dd of=", "echo >", "echo>>",
        "settings put", "input ", "am force-stop", "svc ", "reboot",
        "wm ", "appops set",
    )

    def __init__(self, evidence_log: Optional[EvidenceLog] = None, enabled: bool = True):
        self.evidence_log = evidence_log
        self.enabled = enabled

    def set_evidence_log(self, evidence_log: Optional[EvidenceLog]):
        self.evidence_log = evidence_log

    def classify(self, adb_args) -> bool:
        """Return True if the given adb argument list would write to the device."""
        if not adb_args:
            return False
        args = [str(a) for a in adb_args]

        # Drop the adb binary itself, then any global "-s <serial>" / "-d" / "-e"
        # options, to get to the actual subcommand (install, push, shell, ...).
        idx = 1
        while idx < len(args) and args[idx].startswith("-"):
            idx += 1 if args[idx] in ("-d", "-e") else 2
        rest = args[idx:]
        if not rest:
            return False

        if rest[0] in self.WRITE_ADB_SUBCOMMANDS:
            return True
        if rest[0] == "shell":
            joined = " ".join(rest[1:])
            return any(verb in joined for verb in self.WRITE_SHELL_VERBS)
        return False

    def check(self, adb_args, description: str = ""):
        """Raise WriteBlockedError if this command would write while enforcement is on.

        Always logs the decision (allowed or blocked) when an evidence log is bound.
        """
        is_write = self.classify(adb_args)
        if self.enabled and is_write:
            if self.evidence_log:
                self.evidence_log.record(
                    "WRITE_BLOCKED",
                    {"command": list(map(str, adb_args)), "description": description},
                )
            raise WriteBlockedError(
                f"Write blocker is enabled -- refused to execute: {' '.join(map(str, adb_args))}"
            )
        if self.evidence_log:
            self.evidence_log.record(
                "COMMAND_EXECUTED",
                {
                    "command": list(map(str, adb_args)),
                    "description": description,
                    "classified_write": is_write,
                    "write_blocker_enabled": self.enabled,
                },
            )


class ChainOfCustodyReport:
    """Generates a chain-of-custody report (PDF if reportlab is available, else text)."""

    @staticmethod
    def generate(case: CaseManager, device_info: dict, acquisition_summary: dict, output_path: Path) -> Path:
        output_path = Path(output_path)
        intact, break_idx = case.evidence_log.verify()

        try:
            return ChainOfCustodyReport._generate_pdf(
                case, device_info, acquisition_summary, output_path, intact, break_idx
            )
        except ImportError:
            text_path = output_path.with_suffix(".txt")
            ChainOfCustodyReport._generate_text(
                case, device_info, acquisition_summary, text_path, intact, break_idx
            )
            return text_path

    @staticmethod
    def _generate_text(case, device_info, acquisition_summary, output_path, intact, break_idx) -> Path:
        lines = [
            "CHAIN OF CUSTODY REPORT",
            "=" * 60,
            f"Case Number:     {case.case_number}",
            f"Exhibit Number:  {case.exhibit_number}",
            f"Examiner:        {case.examiner_name}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "",
            "DEVICE INFORMATION",
            "-" * 60,
        ]
        for key, value in (device_info or {}).items():
            lines.append(f"  {key}: {value}")

        lines += ["", "ACQUISITION SUMMARY", "-" * 60]
        for key, value in (acquisition_summary or {}).items():
            lines.append(f"  {key}: {value}")

        lines += [
            "",
            "EVIDENCE INTEGRITY LOG",
            "-" * 60,
            f"  Hash chain intact: {'YES' if intact else 'NO -- tampering detected at entry ' + str(break_idx)}",
            "",
        ]
        for entry in case.evidence_log.entries():
            lines.append(
                f"  [{entry['timestamp']}] {entry['action']} {json.dumps(entry['details'])}"
            )
            lines.append(f"      entry_hash={entry['entry_hash']}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def _generate_pdf(case, device_info, acquisition_summary, output_path, intact, break_idx) -> Path:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        output_path = output_path.with_suffix(".pdf")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
        story = [
            Paragraph("Chain of Custody Report", styles["Title"]),
            Spacer(1, 0.2 * inch),
            Paragraph(f"Case Number: {case.case_number}", styles["Normal"]),
            Paragraph(f"Exhibit Number: {case.exhibit_number}", styles["Normal"]),
            Paragraph(f"Examiner: {case.examiner_name}", styles["Normal"]),
            Paragraph(f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}", styles["Normal"]),
            Spacer(1, 0.3 * inch),
            Paragraph("Device Information", styles["Heading2"]),
        ]
        if device_info:
            rows = [[k, str(v)] for k, v in device_info.items()]
            story.append(Table(rows, colWidths=[2 * inch, 4 * inch]))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Acquisition Summary", styles["Heading2"]))
        if acquisition_summary:
            rows = [[k, str(v)] for k, v in acquisition_summary.items()]
            story.append(Table(rows, colWidths=[2 * inch, 4 * inch]))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Evidence Integrity", styles["Heading2"]))
        story.append(Paragraph(
            "Hash chain intact: YES" if intact else
            f"Hash chain intact: NO -- tampering detected at entry {break_idx}",
            styles["Normal"],
        ))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Evidence Log", styles["Heading2"]))
        log_rows = [["Timestamp", "Action", "Details", "Entry Hash"]]
        for entry in case.evidence_log.entries():
            log_rows.append([
                entry["timestamp"],
                entry["action"],
                json.dumps(entry["details"])[:80],
                entry["entry_hash"][:16] + "...",
            ])
        table = Table(log_rows, colWidths=[1.3 * inch, 1.2 * inch, 2.7 * inch, 1.3 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)

        doc.build(story)
        return output_path
