"""Script management tab for OMNISCRIBE."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from OMNISCRIBE.app.config import DEFAULT_SCRIPT_TEMPLATE
from OMNISCRIBE.core.base import ScriptLanguage


class ScriptTab(QWidget):
    def __init__(self, omniscribe, status_bar: Optional[QStatusBar] = None) -> None:
        super().__init__()
        self.omniscribe = omniscribe
        self.status_bar = status_bar
        self.current_script = None
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        self.script_list = QTableWidget()
        self.script_list.setColumnCount(2)
        self.script_list.setHorizontalHeaderLabels(["Name", "Language"])
        self.script_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.script_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.script_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.script_list.setMinimumWidth(300)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Script name")

        self.script_language = QComboBox()
        for lang in ScriptLanguage:
            self.script_language.addItem(lang.value.upper(), lang)

        self.script_description = QTextEdit()
        self.script_description.setPlaceholderText("Description")
        self.script_description.setMaximumHeight(80)

        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Monospace", 10))

        self.output_panel = QTextEdit()
        self.output_panel.setReadOnly(True)
        self.output_panel.setFont(QFont("Monospace", 9))

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.script_name)
        form_layout.addRow("Language:", self.script_language)
        form_layout.addRow("Description:", self.script_description)

        right_layout.addLayout(form_layout)
        right_layout.addWidget(QLabel("Script:"))
        right_layout.addWidget(self.script_editor)
        right_layout.addWidget(QLabel("Output:"))
        right_layout.addWidget(self.output_panel)

        splitter.addWidget(self.script_list)
        splitter.addWidget(right_panel)

        main_layout.addWidget(splitter)

        self.script_list.itemSelectionChanged.connect(self.on_script_selected)

    def update_script_list(self) -> None:
        """Update the list of scripts."""
        self.script_list.setRowCount(0)
        for script in self.omniscribe.scripts.values():
            row = self.script_list.rowCount()
            self.script_list.insertRow(row)
            self.script_list.setItem(row, 0, QTableWidgetItem(script.name))
            self.script_list.setItem(row, 1, QTableWidgetItem(script.language.value))

    def on_script_selected(self) -> None:
        """Handle script selection from the list."""
        selected = self.script_list.selectedItems()
        if not selected:
            return

        script_name = selected[0].text()
        script = self.omniscribe.scripts.get(script_name)
        if script:
            self.current_script = script
            self.script_name.setText(script.name)
            self.script_language.setCurrentText(script.language.value.upper())
            self.script_description.setPlainText(script.description)
            self.script_editor.setPlainText(script.code)

    def new_script(self) -> None:
        """Create a new script."""
        name, ok = QInputDialog.getText(self, "New Script", "Script name:")
        if not ok or not name:
            return

        try:
            self.omniscribe.create_script(
                name=name,
                language=ScriptLanguage.PYTHON,
                code=DEFAULT_SCRIPT_TEMPLATE,
                description="",
            )
            self.update_script_list()
            self.log_message("INFO", f"Created new script: {name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to create script: {exc}")

    def save_script(self) -> None:
        """Save the current script."""
        if not self.current_script:
            return

        try:
            self.current_script.name = self.script_name.text()
            self.current_script.language = ScriptLanguage(self.script_language.currentText().lower())
            self.current_script.description = self.script_description.toPlainText()
            self.current_script.code = self.script_editor.toPlainText()

            self.update_script_list()
            self.log_message("INFO", f"Saved script: {self.current_script.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save script: {exc}")

    def run_current_script(self) -> None:
        """Run the currently selected script."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script selected")
            return

        try:
            self.save_script()
            self.output_panel.clear()
            self.log_message("INFO", f"Running script: {self.current_script.name}")

            result = self.omniscribe.run_script(
                self.current_script.name,
                {"timestamp": datetime.now().isoformat()},
            )
            self.on_script_executed(result)
        except Exception as exc:
            self.log_message("ERROR", f"Failed to run script: {exc}")

    def on_script_executed(self, result) -> None:
        """Handle script execution result."""
        self.output_panel.append("=== Script Execution Result ===")
        self.output_panel.append(f"Status: {'Success' if result.get('success') else 'Failed'}")
        self.output_panel.append(f"Output: {result.get('output', 'No output')}")
        self.output_panel.append(f"Execution Time: {result.get('execution_time', 'N/A')}")
        self.output_panel.append("=" * 30)

        self.output_panel.moveCursor(QTextCursor.End)

    def import_script(self) -> None:
        """Import a script from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Script",
            "",
            "Script Files (*.py *.sh *.js);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()

            if file_path.endswith(".sh"):
                lang = ScriptLanguage.SHELL
            elif file_path.endswith(".js"):
                lang = ScriptLanguage.JAVASCRIPT
            else:
                lang = ScriptLanguage.PYTHON

            name = os.path.splitext(os.path.basename(file_path))[0]

            self.omniscribe.create_script(
                name=name,
                language=lang,
                code=content,
                description=f"Imported from {os.path.basename(file_path)}",
            )

            self.update_script_list()
            self.log_message("INFO", f"Imported script: {name}")
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", f"Failed to import script: {exc}")

    def export_script(self) -> None:
        """Export the current script to a file."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script selected")
            return

        ext = {
            ScriptLanguage.PYTHON: ".py",
            ScriptLanguage.SHELL: ".sh",
            ScriptLanguage.JAVASCRIPT: ".js",
        }.get(self.current_script.language, ".txt")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Script",
            f"{self.current_script.name}{ext}",
            f"Script Files (*{ext});;All Files (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(self.current_script.code)

            self.log_message("INFO", f"Exported script to: {file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to export script: {exc}")

    def log_message(self, level: str, message: str) -> None:
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"

        if level.upper() == "ERROR":
            color = QColor("red")
        elif level.upper() == "WARNING":
            color = QColor("orange")
        else:
            color = QColor("black")

        self.output_panel.setTextColor(color)
        self.output_panel.append(log_entry)

        if level.upper() in ("ERROR", "WARNING"):
            self.update_status(message)

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        if self.status_bar is not None:
            self.status_bar.showMessage(message, 5000)
