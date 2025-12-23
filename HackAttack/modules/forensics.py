"""
Forensics & Incident Response Module for HackAttack
Provides tools for digital forensics and incident response.
"""

import os
import hashlib
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QFileDialog, QProgressBar, QMessageBox, QComboBox,
    QFormLayout, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal


class HashWorker(QThread):
    """Worker thread for computing file hashes."""
    progress = Signal(int)
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, file_path, algorithms):
        super().__init__()
        self.file_path = file_path
        self.algorithms = algorithms

    def run(self):
        try:
            hashers = {}
            for algo in self.algorithms:
                hashers[algo] = hashlib.new(algo)

            file_size = os.path.getsize(self.file_path)
            bytes_read = 0

            with open(self.file_path, 'rb') as f:
                while chunk := f.read(8192):
                    for hasher in hashers.values():
                        hasher.update(chunk)
                    bytes_read += len(chunk)
                    self.progress.emit(int((bytes_read / file_size) * 100))

            results = {algo: hasher.hexdigest() for algo, hasher in hashers.items()}
            self.result.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ForensicsGUI(QWidget):
    """Forensics & Incident Response GUI."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up the forensics interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # File Analysis Tab
        file_tab = self.create_file_analysis_tab()
        self.tabs.addTab(file_tab, "File Analysis")

        # Memory Analysis Tab
        memory_tab = self.create_memory_analysis_tab()
        self.tabs.addTab(memory_tab, "Memory Analysis")

        # Timeline Tab
        timeline_tab = self.create_timeline_tab()
        self.tabs.addTab(timeline_tab, "Timeline")

        # Evidence Collection Tab
        evidence_tab = self.create_evidence_tab()
        self.tabs.addTab(evidence_tab, "Evidence Collection")

        layout.addWidget(self.tabs)

    def create_file_analysis_tab(self):
        """Create the file analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # File Hash Calculator
        hash_group = QGroupBox("File Hash Calculator")
        hash_layout = QVBoxLayout()

        # File selection
        file_row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select a file to analyze...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_row.addWidget(self.file_path)
        file_row.addWidget(browse_btn)
        hash_layout.addLayout(file_row)

        # Hash algorithm selection
        algo_layout = QHBoxLayout()
        self.md5_check = QCheckBox("MD5")
        self.md5_check.setChecked(True)
        self.sha1_check = QCheckBox("SHA-1")
        self.sha1_check.setChecked(True)
        self.sha256_check = QCheckBox("SHA-256")
        self.sha256_check.setChecked(True)
        self.sha512_check = QCheckBox("SHA-512")
        algo_layout.addWidget(self.md5_check)
        algo_layout.addWidget(self.sha1_check)
        algo_layout.addWidget(self.sha256_check)
        algo_layout.addWidget(self.sha512_check)
        algo_layout.addStretch()
        hash_layout.addLayout(algo_layout)

        # Calculate button and progress
        calc_row = QHBoxLayout()
        self.calc_btn = QPushButton("Calculate Hashes")
        self.calc_btn.clicked.connect(self.calculate_hashes)
        self.hash_progress = QProgressBar()
        self.hash_progress.setVisible(False)
        calc_row.addWidget(self.calc_btn)
        calc_row.addWidget(self.hash_progress)
        hash_layout.addLayout(calc_row)

        # Results
        self.hash_results = QTextEdit()
        self.hash_results.setReadOnly(True)
        self.hash_results.setMaximumHeight(150)
        hash_layout.addWidget(self.hash_results)

        hash_group.setLayout(hash_layout)
        layout.addWidget(hash_group)

        # File Metadata
        meta_group = QGroupBox("File Metadata")
        meta_layout = QVBoxLayout()
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        meta_layout.addWidget(self.metadata_table)

        refresh_meta_btn = QPushButton("Refresh Metadata")
        refresh_meta_btn.clicked.connect(self.refresh_metadata)
        meta_layout.addWidget(refresh_meta_btn)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        return tab

    def create_memory_analysis_tab(self):
        """Create the memory analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Process List
        proc_group = QGroupBox("Running Processes")
        proc_layout = QVBoxLayout()

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Memory", "Status"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        proc_layout.addWidget(self.process_table)

        refresh_proc_btn = QPushButton("Refresh Process List")
        refresh_proc_btn.clicked.connect(self.refresh_processes)
        proc_layout.addWidget(refresh_proc_btn)

        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)

        # Memory Dump
        dump_group = QGroupBox("Memory Dump")
        dump_layout = QFormLayout()

        self.dump_pid = QLineEdit()
        self.dump_pid.setPlaceholderText("Enter PID")
        dump_layout.addRow("Process ID:", self.dump_pid)

        dump_btn = QPushButton("Create Memory Dump")
        dump_btn.clicked.connect(self.create_memory_dump)
        dump_layout.addRow(dump_btn)

        dump_group.setLayout(dump_layout)
        layout.addWidget(dump_group)

        layout.addStretch()
        return tab

    def create_timeline_tab(self):
        """Create the timeline analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Timeline viewer
        timeline_group = QGroupBox("Event Timeline")
        timeline_layout = QVBoxLayout()

        # Filter controls
        filter_row = QHBoxLayout()
        self.timeline_filter = QComboBox()
        self.timeline_filter.addItems(["All Events", "File Access", "Process Events", "Network Events"])
        filter_row.addWidget(QLabel("Filter:"))
        filter_row.addWidget(self.timeline_filter)
        filter_row.addStretch()

        refresh_timeline_btn = QPushButton("Refresh")
        refresh_timeline_btn.clicked.connect(self.refresh_timeline)
        filter_row.addWidget(refresh_timeline_btn)
        timeline_layout.addLayout(filter_row)

        # Timeline table
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(4)
        self.timeline_table.setHorizontalHeaderLabels(["Timestamp", "Type", "Source", "Description"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        timeline_layout.addWidget(self.timeline_table)

        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)

        return tab

    def create_evidence_tab(self):
        """Create the evidence collection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Evidence list
        evidence_group = QGroupBox("Collected Evidence")
        evidence_layout = QVBoxLayout()

        self.evidence_list = QListWidget()
        evidence_layout.addWidget(self.evidence_list)

        # Evidence actions
        btn_row = QHBoxLayout()
        add_evidence_btn = QPushButton("Add Evidence")
        add_evidence_btn.clicked.connect(self.add_evidence)
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_evidence_report)
        btn_row.addWidget(add_evidence_btn)
        btn_row.addWidget(export_btn)
        evidence_layout.addLayout(btn_row)

        evidence_group.setLayout(evidence_layout)
        layout.addWidget(evidence_group)

        # Notes
        notes_group = QGroupBox("Investigation Notes")
        notes_layout = QVBoxLayout()
        self.investigation_notes = QTextEdit()
        self.investigation_notes.setPlaceholderText("Enter investigation notes here...")
        notes_layout.addWidget(self.investigation_notes)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        return tab

    def browse_file(self):
        """Browse for a file to analyze."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if file_path:
            self.file_path.setText(file_path)
            self.refresh_metadata()

    def calculate_hashes(self):
        """Calculate file hashes."""
        file_path = self.file_path.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Please select a valid file.")
            return

        algorithms = []
        if self.md5_check.isChecked():
            algorithms.append('md5')
        if self.sha1_check.isChecked():
            algorithms.append('sha1')
        if self.sha256_check.isChecked():
            algorithms.append('sha256')
        if self.sha512_check.isChecked():
            algorithms.append('sha512')

        if not algorithms:
            QMessageBox.warning(self, "Error", "Please select at least one hash algorithm.")
            return

        self.hash_progress.setVisible(True)
        self.calc_btn.setEnabled(False)

        self.hash_worker = HashWorker(file_path, algorithms)
        self.hash_worker.progress.connect(self.hash_progress.setValue)
        self.hash_worker.result.connect(self.display_hash_results)
        self.hash_worker.error.connect(self.hash_error)
        self.hash_worker.finished.connect(self.hash_finished)
        self.hash_worker.start()

    def display_hash_results(self, results):
        """Display hash calculation results."""
        output = f"File: {self.file_path.text()}\n"
        output += f"Calculated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += "-" * 50 + "\n"
        for algo, hash_value in results.items():
            output += f"{algo.upper()}: {hash_value}\n"
        self.hash_results.setText(output)

    def hash_error(self, error):
        """Handle hash calculation error."""
        QMessageBox.critical(self, "Error", f"Hash calculation failed: {error}")

    def hash_finished(self):
        """Clean up after hash calculation."""
        self.hash_progress.setVisible(False)
        self.calc_btn.setEnabled(True)

    def refresh_metadata(self):
        """Refresh file metadata display."""
        file_path = self.file_path.text()
        if not file_path or not os.path.exists(file_path):
            return

        try:
            stat = os.stat(file_path)
            self.metadata_table.setRowCount(0)

            metadata = [
                ("File Name", os.path.basename(file_path)),
                ("File Size", f"{stat.st_size:,} bytes"),
                ("Created", datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')),
                ("Modified", datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')),
                ("Accessed", datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')),
                ("Permissions", oct(stat.st_mode)[-3:]),
            ]

            for i, (prop, value) in enumerate(metadata):
                self.metadata_table.insertRow(i)
                self.metadata_table.setItem(i, 0, QTableWidgetItem(prop))
                self.metadata_table.setItem(i, 1, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read metadata: {e}")

    def refresh_processes(self):
        """Refresh the process list."""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            self.process_table.setRowCount(0)
            for i, line in enumerate(lines[:100]):  # Limit to 100 processes
                parts = line.split()
                if len(parts) >= 11:
                    self.process_table.insertRow(i)
                    self.process_table.setItem(i, 0, QTableWidgetItem(parts[1]))  # PID
                    self.process_table.setItem(i, 1, QTableWidgetItem(parts[10]))  # Name
                    self.process_table.setItem(i, 2, QTableWidgetItem(f"{parts[3]}%"))  # Memory
                    self.process_table.setItem(i, 3, QTableWidgetItem(parts[7]))  # Status
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get process list: {e}")

    def create_memory_dump(self):
        """Create a memory dump of a process."""
        pid = self.dump_pid.text()
        if not pid:
            QMessageBox.warning(self, "Error", "Please enter a PID.")
            return

        QMessageBox.information(
            self, "Memory Dump",
            f"Memory dump for PID {pid} would be created.\n\n"
            "Note: This requires elevated privileges and appropriate tools like gcore."
        )

    def refresh_timeline(self):
        """Refresh the timeline view."""
        # Add sample timeline entries
        self.timeline_table.setRowCount(0)
        sample_events = [
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "File Access", "System", "Config file accessed"),
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Process", "System", "New process started"),
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Network", "eth0", "Connection established"),
        ]
        for i, (ts, etype, source, desc) in enumerate(sample_events):
            self.timeline_table.insertRow(i)
            self.timeline_table.setItem(i, 0, QTableWidgetItem(ts))
            self.timeline_table.setItem(i, 1, QTableWidgetItem(etype))
            self.timeline_table.setItem(i, 2, QTableWidgetItem(source))
            self.timeline_table.setItem(i, 3, QTableWidgetItem(desc))

    def add_evidence(self):
        """Add evidence to the collection."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Add Evidence", "", "All Files (*)")
        if file_path:
            item = QListWidgetItem(f"[{datetime.now().strftime('%H:%M:%S')}] {os.path.basename(file_path)}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.evidence_list.addItem(item)

    def export_evidence_report(self):
        """Export the evidence report."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("FORENSICS INVESTIGATION REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Generated: {datetime.now()}\n\n")
                    f.write("Evidence Items:\n")
                    for i in range(self.evidence_list.count()):
                        f.write(f"  - {self.evidence_list.item(i).text()}\n")
                    f.write("\nNotes:\n")
                    f.write(self.investigation_notes.toPlainText())
                QMessageBox.information(self, "Success", f"Report exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export report: {e}")
