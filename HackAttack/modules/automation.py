"""
Automation & Scripting Module for HackAttack
Provides automation workflows and scripting capabilities.
"""

import os
import json
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QFileDialog, QMessageBox, QComboBox,
    QFormLayout, QCheckBox, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class ScriptWorker(QThread):
    """Worker thread for running scripts."""
    output = Signal(str)
    error = Signal(str)
    finished = Signal(int)

    def __init__(self, script, interpreter="python3"):
        super().__init__()
        self.script = script
        self.interpreter = interpreter
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                [self.interpreter, '-c', self.script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in self.process.stdout:
                self.output.emit(line.rstrip())

            for line in self.process.stderr:
                self.error.emit(line.rstrip())

            self.process.wait()
            self.finished.emit(self.process.returncode)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(-1)

    def stop(self):
        if self.process:
            self.process.terminate()


class AutomationGUI(QWidget):
    """Automation & Scripting GUI."""

    def __init__(self):
        super().__init__()
        self.workflows = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the automation interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # Script Editor Tab
        script_tab = self.create_script_editor_tab()
        self.tabs.addTab(script_tab, "Script Editor")

        # Workflows Tab
        workflow_tab = self.create_workflow_tab()
        self.tabs.addTab(workflow_tab, "Workflows")

        # Scheduled Tasks Tab
        schedule_tab = self.create_schedule_tab()
        self.tabs.addTab(schedule_tab, "Scheduled Tasks")

        # Templates Tab
        templates_tab = self.create_templates_tab()
        self.tabs.addTab(templates_tab, "Templates")

        layout.addWidget(self.tabs)

    def create_script_editor_tab(self):
        """Create the script editor tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Splitter for editor and output
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Editor section
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        # Toolbar
        toolbar = QHBoxLayout()
        self.interpreter = QComboBox()
        self.interpreter.addItems(["python3", "bash", "sh", "ruby", "perl"])
        toolbar.addWidget(QLabel("Interpreter:"))
        toolbar.addWidget(self.interpreter)
        toolbar.addStretch()

        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_script)
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_script)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_script)
        run_btn = QPushButton("Run")
        run_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        run_btn.clicked.connect(self.run_script)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_script)

        toolbar.addWidget(new_btn)
        toolbar.addWidget(open_btn)
        toolbar.addWidget(save_btn)
        toolbar.addWidget(run_btn)
        toolbar.addWidget(self.stop_btn)
        editor_layout.addLayout(toolbar)

        # Editor
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Monospace", 11))
        self.script_editor.setPlaceholderText("# Enter your script here...")
        editor_layout.addWidget(self.script_editor)

        splitter.addWidget(editor_widget)

        # Output section
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.addWidget(QLabel("Output:"))
        self.script_output = QTextEdit()
        self.script_output.setReadOnly(True)
        self.script_output.setFont(QFont("Monospace", 10))
        output_layout.addWidget(self.script_output)

        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self.script_output.clear)
        output_layout.addWidget(clear_btn)

        splitter.addWidget(output_widget)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)
        return tab

    def create_workflow_tab(self):
        """Create the workflows tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Workflow list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)

        list_layout.addWidget(QLabel("Workflows"))
        self.workflow_list = QListWidget()
        self.workflow_list.itemClicked.connect(self.load_workflow)
        list_layout.addWidget(self.workflow_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_workflow)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_workflow)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        list_layout.addLayout(btn_row)

        layout.addWidget(list_widget)

        # Workflow editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        self.workflow_name = QLineEdit()
        self.workflow_name.setPlaceholderText("Workflow name...")
        editor_layout.addWidget(self.workflow_name)

        editor_layout.addWidget(QLabel("Steps:"))
        self.workflow_steps = QListWidget()
        editor_layout.addWidget(self.workflow_steps)

        step_btns = QHBoxLayout()
        add_step_btn = QPushButton("Add Step")
        add_step_btn.clicked.connect(self.add_workflow_step)
        remove_step_btn = QPushButton("Remove Step")
        remove_step_btn.clicked.connect(self.remove_workflow_step)
        step_btns.addWidget(add_step_btn)
        step_btns.addWidget(remove_step_btn)
        editor_layout.addLayout(step_btns)

        save_workflow_btn = QPushButton("Save Workflow")
        save_workflow_btn.clicked.connect(self.save_workflow)
        run_workflow_btn = QPushButton("Run Workflow")
        run_workflow_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        run_workflow_btn.clicked.connect(self.run_workflow)

        editor_layout.addWidget(save_workflow_btn)
        editor_layout.addWidget(run_workflow_btn)

        layout.addWidget(editor_widget)
        return tab

    def create_schedule_tab(self):
        """Create the scheduled tasks tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scheduled tasks table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels(["Name", "Type", "Schedule", "Last Run", "Status"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.schedule_table)

        # Add sample tasks
        sample_tasks = [
            ("Network Scan", "Workflow", "Daily 02:00", "2024-01-15", "Active"),
            ("Vulnerability Check", "Script", "Weekly Mon", "2024-01-14", "Active"),
            ("Port Monitor", "Script", "Every 6 hours", "2024-01-15", "Paused"),
        ]
        for i, (name, task_type, schedule, last_run, status) in enumerate(sample_tasks):
            self.schedule_table.insertRow(i)
            self.schedule_table.setItem(i, 0, QTableWidgetItem(name))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(task_type))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(schedule))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(last_run))
            self.schedule_table.setItem(i, 4, QTableWidgetItem(status))

        # Buttons
        btn_row = QHBoxLayout()
        add_task_btn = QPushButton("Add Task")
        add_task_btn.clicked.connect(self.add_scheduled_task)
        edit_task_btn = QPushButton("Edit Task")
        remove_task_btn = QPushButton("Remove Task")
        btn_row.addWidget(add_task_btn)
        btn_row.addWidget(edit_task_btn)
        btn_row.addWidget(remove_task_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return tab

    def create_templates_tab(self):
        """Create the templates tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Script Templates"))

        templates = [
            ("Port Scanner", "# Port Scanner Template\nimport socket\n\ndef scan_port(host, port):\n    sock = socket.socket()\n    sock.settimeout(1)\n    result = sock.connect_ex((host, port))\n    sock.close()\n    return result == 0\n\n# Usage: scan_port('127.0.0.1', 80)"),
            ("Network Ping", "# Network Ping Template\nimport subprocess\n\ndef ping_host(host):\n    result = subprocess.run(['ping', '-c', '1', host], capture_output=True)\n    return result.returncode == 0\n\n# Usage: ping_host('google.com')"),
            ("HTTP Request", "# HTTP Request Template\nimport urllib.request\n\ndef check_url(url):\n    try:\n        response = urllib.request.urlopen(url, timeout=5)\n        return response.status\n    except Exception as e:\n        return str(e)\n\n# Usage: check_url('https://example.com')"),
            ("File Hash", "# File Hash Template\nimport hashlib\n\ndef file_hash(filepath, algo='sha256'):\n    h = hashlib.new(algo)\n    with open(filepath, 'rb') as f:\n        for chunk in iter(lambda: f.read(4096), b''):\n            h.update(chunk)\n    return h.hexdigest()"),
        ]

        self.templates_list = QListWidget()
        for name, _ in templates:
            self.templates_list.addItem(name)
        self.templates_list.itemDoubleClicked.connect(lambda: self.use_template(templates))
        layout.addWidget(self.templates_list)

        use_btn = QPushButton("Use Template")
        use_btn.clicked.connect(lambda: self.use_template(templates))
        layout.addWidget(use_btn)

        return tab

    def new_script(self):
        """Create a new script."""
        self.script_editor.clear()
        self.script_output.clear()

    def open_script(self):
        """Open a script file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Script", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.script_editor.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def save_script(self):
        """Save the current script."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.script_editor.toPlainText())
                QMessageBox.information(self, "Success", "Script saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def run_script(self):
        """Run the current script."""
        script = self.script_editor.toPlainText()
        if not script.strip():
            QMessageBox.warning(self, "Error", "No script to run.")
            return

        self.script_output.clear()
        self.stop_btn.setEnabled(True)

        self.worker = ScriptWorker(script, self.interpreter.currentText())
        self.worker.output.connect(lambda msg: self.script_output.append(msg))
        self.worker.error.connect(lambda msg: self.script_output.append(f"[ERROR] {msg}"))
        self.worker.finished.connect(self.script_finished)
        self.worker.start()

    def stop_script(self):
        """Stop the running script."""
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.script_output.append("[Script terminated]")

    def script_finished(self, return_code):
        """Handle script completion."""
        self.stop_btn.setEnabled(False)
        self.script_output.append(f"\n[Script finished with code: {return_code}]")

    def add_workflow(self):
        """Add a new workflow."""
        name, ok = QInputDialog.getText(self, "New Workflow", "Workflow name:")
        if ok and name:
            self.workflow_list.addItem(name)
            self.workflows.append({'name': name, 'steps': []})

    def remove_workflow(self):
        """Remove selected workflow."""
        current = self.workflow_list.currentRow()
        if current >= 0:
            self.workflow_list.takeItem(current)
            if current < len(self.workflows):
                self.workflows.pop(current)

    def load_workflow(self, item):
        """Load a workflow into the editor."""
        index = self.workflow_list.currentRow()
        if index >= 0 and index < len(self.workflows):
            workflow = self.workflows[index]
            self.workflow_name.setText(workflow['name'])
            self.workflow_steps.clear()
            for step in workflow.get('steps', []):
                self.workflow_steps.addItem(step)

    def add_workflow_step(self):
        """Add a step to the workflow."""
        step, ok = QInputDialog.getText(self, "Add Step", "Step description:")
        if ok and step:
            self.workflow_steps.addItem(step)

    def remove_workflow_step(self):
        """Remove selected step from workflow."""
        current = self.workflow_steps.currentRow()
        if current >= 0:
            self.workflow_steps.takeItem(current)

    def save_workflow(self):
        """Save the current workflow."""
        index = self.workflow_list.currentRow()
        if index >= 0:
            steps = [self.workflow_steps.item(i).text() for i in range(self.workflow_steps.count())]
            self.workflows[index] = {
                'name': self.workflow_name.text(),
                'steps': steps
            }
            self.workflow_list.item(index).setText(self.workflow_name.text())
            QMessageBox.information(self, "Success", "Workflow saved!")

    def run_workflow(self):
        """Run the selected workflow."""
        index = self.workflow_list.currentRow()
        if index >= 0 and index < len(self.workflows):
            workflow = self.workflows[index]
            QMessageBox.information(
                self, "Run Workflow",
                f"Running workflow: {workflow['name']}\n\nSteps:\n" +
                "\n".join(f"  {i+1}. {s}" for i, s in enumerate(workflow.get('steps', [])))
            )

    def add_scheduled_task(self):
        """Add a scheduled task."""
        QMessageBox.information(
            self, "Add Task",
            "Task scheduler would open here to configure a new scheduled task."
        )

    def use_template(self, templates):
        """Use the selected template."""
        current = self.templates_list.currentRow()
        if current >= 0:
            name, script = templates[current]
            self.tabs.setCurrentIndex(0)  # Switch to script editor
            self.script_editor.setText(script)
