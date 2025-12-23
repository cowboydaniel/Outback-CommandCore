#!/usr/bin/env python3
"""
OMNISCRIBE - Automation and Scripting Control Suite
"""
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTextEdit, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QStatusBar, QMessageBox, QComboBox,
                             QSplitter, QFileDialog, QInputDialog, QLineEdit, QFormLayout)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QFont, QTextCursor, QColor, QIcon, QAction

class SignalEmitter(QObject):
    script_executed = Signal(dict)  # script execution result
    log_message = Signal(str, str)   # level, message

class OmniscribeUI(QMainWindow):
    def __init__(self, omniscribe):
        super().__init__()
        self.omniscribe = omniscribe
        self.signal_emitter = SignalEmitter()
        self.current_script = None
        self.setup_ui()
        self.setup_connections()
        self.setWindowTitle("OMNISCRIBE - Scripting Control Suite")
        self.setMinimumSize(1000, 700)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons', 'omniscribe.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        """Set up the main UI components."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Script list
        self.script_list = QTableWidget()
        self.script_list.setColumnCount(2)
        self.script_list.setHorizontalHeaderLabels(["Name", "Language"])
        self.script_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.script_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.script_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.script_list.setMinimumWidth(300)
        
        # Right panel - Script editor and output
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Script info
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Script name")
        
        self.script_language = QComboBox()
        for lang in ScriptLanguage:
            self.script_language.addItem(lang.value.upper(), lang)
        
        self.script_description = QTextEdit()
        self.script_description.setPlaceholderText("Description")
        self.script_description.setMaximumHeight(80)
        
        # Script editor
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Monospace", 10))
        
        # Output panel
        self.output_panel = QTextEdit()
        self.output_panel.setReadOnly(True)
        self.output_panel.setFont(QFont("Monospace", 9))
        
        # Add widgets to right layout
        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.script_name)
        form_layout.addRow("Language:", self.script_language)
        form_layout.addRow("Description:", self.script_description)
        
        right_layout.addLayout(form_layout)
        right_layout.addWidget(QLabel("Script:"))
        right_layout.addWidget(self.script_editor)
        right_layout.addWidget(QLabel("Output:"))
        right_layout.addWidget(self.output_panel)
        
        # Add widgets to splitter
        splitter.addWidget(self.script_list)
        splitter.addWidget(right_panel)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")
    
    def setup_toolbar(self):
        """Set up the toolbar with actions."""
        toolbar = self.addToolBar("Tools")
        
        # New script action
        new_action = QAction("New Script", self)
        new_action.triggered.connect(self.new_script)
        toolbar.addAction(new_action)
        
        # Save script action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_script)
        toolbar.addAction(save_action)
        
        # Run script action
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.run_current_script)
        toolbar.addAction(run_action)
        
        toolbar.addSeparator()
        
        # Import/Export actions
        import_action = QAction("Import Script", self)
        import_action.triggered.connect(self.import_script)
        toolbar.addAction(import_action)
        
        export_action = QAction("Export Script", self)
        export_action.triggered.connect(self.export_script)
        toolbar.addAction(export_action)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.script_list.itemSelectionChanged.connect(self.on_script_selected)
        self.signal_emitter.script_executed.connect(self.on_script_executed)
        self.signal_emitter.log_message.connect(self.log_message)
    
    def update_script_list(self):
        """Update the list of scripts."""
        self.script_list.setRowCount(0)
        for script in self.omniscribe.scripts.values():
            row = self.script_list.rowCount()
            self.script_list.insertRow(row)
            self.script_list.setItem(row, 0, QTableWidgetItem(script.name))
            self.script_list.setItem(row, 1, QTableWidgetItem(script.language.value))
    
    def on_script_selected(self):
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
    
    def new_script(self):
        """Create a new script."""
        name, ok = QInputDialog.getText(self, "New Script", "Script name:")
        if not ok or not name:
            return
            
        try:
            script = self.omniscribe.create_script(
                name=name,
                language=ScriptLanguage.PYTHON,  # Default to Python
                code="# Write your script here\nprint('Hello, OMNISCRIBE!')",
                description=""
            )
            self.update_script_list()
            self.log_message("INFO", f"Created new script: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create script: {e}")
    
    def save_script(self):
        """Save the current script."""
        if not self.current_script:
            return
            
        try:
            # Update script data from UI
            self.current_script.name = self.script_name.text()
            self.current_script.language = ScriptLanguage(self.script_language.currentText().lower())
            self.current_script.description = self.script_description.toPlainText()
            self.current_script.code = self.script_editor.toPlainText()
            
            self.update_script_list()
            self.log_message("INFO", f"Saved script: {self.current_script.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save script: {e}")
    
    def run_current_script(self):
        """Run the currently selected script."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script selected")
            return
            
        try:
            # Save before running
            self.save_script()
            
            # Clear output
            self.output_panel.clear()
            self.log_message("INFO", f"Running script: {self.current_script.name}")
            
            # Run the script
            result = self.omniscribe.run_script(self.current_script.name, {"timestamp": datetime.now().isoformat()})
            self.signal_emitter.script_executed.emit(result)
            
        except Exception as e:
            self.log_message("ERROR", f"Failed to run script: {e}")
    
    def on_script_executed(self, result):
        """Handle script execution result."""
        self.output_panel.append("=== Script Execution Result ===")
        self.output_panel.append(f"Status: {'Success' if result.get('success') else 'Failed'}")
        self.output_panel.append(f"Output: {result.get('output', 'No output')}")
        self.output_panel.append(f"Execution Time: {result.get('execution_time', 'N/A')}")
        self.output_panel.append("=" * 30)
        
        # Auto-scroll to bottom
        self.output_panel.moveCursor(QTextCursor.End)
    
    def import_script(self):
        """Import a script from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Script",
            "",
            "Script Files (*.py *.sh *.js);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Guess language from file extension
            if file_path.endswith('.sh'):
                lang = ScriptLanguage.SHELL
            elif file_path.endswith('.js'):
                lang = ScriptLanguage.JAVASCRIPT
            else:  # Default to Python
                lang = ScriptLanguage.PYTHON
                
            # Get script name from filename
            import os
            name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Create new script
            script = self.omniscribe.create_script(
                name=name,
                language=lang,
                code=content,
                description=f"Imported from {os.path.basename(file_path)}"
            )
            
            self.update_script_list()
            self.log_message("INFO", f"Imported script: {name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import script: {e}")
    
    def export_script(self):
        """Export the current script to a file."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script selected")
            return
            
        # Determine default extension based on language
        ext = {
            ScriptLanguage.PYTHON: '.py',
            ScriptLanguage.SHELL: '.sh',
            ScriptLanguage.JAVASCRIPT: '.js'
        }.get(self.current_script.language, '.txt')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Script",
            f"{self.current_script.name}{ext}",
            f"Script Files (*{ext});;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                f.write(self.current_script.code)
                
            self.log_message("INFO", f"Exported script to: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export script: {e}")
    
    def log_message(self, level, message):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        
        # Color code log levels
        if level.upper() == "ERROR":
            color = QColor("red")
        elif level.upper() == "WARNING":
            color = QColor("orange")
        else:
            color = QColor("black")
        
        # Append to output panel
        self.output_panel.setTextColor(color)
        self.output_panel.append(log_entry)
        
        # Update status bar for errors/warnings
        if level.upper() in ("ERROR", "WARNING"):
            self.status_bar.showMessage(message, 5000)  # Show for 5 seconds
    
    def update_status(self, message):
        """Update the status bar message."""
        self.status_bar.showMessage(message)


class ScriptLanguage(Enum):
    PYTHON = "python"
    SHELL = "shell"
    JAVASCRIPT = "javascript"

class ScriptLanguage(Enum):
    PYTHON = "python"
    SHELL = "shell"
    JAVASCRIPT = "javascript"
    
@dataclass
class Script:
    name: str
    language: ScriptLanguage
    code: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the script with the given context."""
        # In a real implementation, this would execute the script in the appropriate runtime
        print(f"Executing script: {self.name}")
        print(f"Language: {self.language.value}")
        print(f"Code:\n{self.code}")
        
        if context:
            print("Context:", json.dumps(context, indent=2))
            
        # Simulate execution result
        return {
            "success": True,
            "output": f"Script '{self.name}' executed successfully",
            "execution_time": "0.123s",
            "timestamp": datetime.now().isoformat()
        }

class Omniscribe:
    def __init__(self):
        self.scripts: Dict[str, Script] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for OMNISCRIBE."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('OMNISCRIBE')
    
    def create_script(self, name: str, language: ScriptLanguage, code: str, description: str = "") -> Script:
        """Create and store a new script."""
        if name in self.scripts:
            raise ValueError(f"Script with name '{name}' already exists")
            
        script = Script(
            name=name,
            language=language,
            code=code,
            description=description
        )
        self.scripts[name] = script
        self.logger.info(f"Created new script: {name}")
        return script
    
    def run_script(self, name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a stored script by name."""
        if name not in self.scripts:
            raise ValueError(f"No script found with name: {name}")
            
        script = self.scripts[name]
        self.logger.info(f"Executing script: {name}")
        return script.execute(context or {})

def main():
    """Main entry point for OMNISCRIBE."""
    app = QApplication(sys.argv)
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create Omniscribe instance
    omni = Omniscribe()
    
    # Create and show the main window
    ui = OmniscribeUI(omni)
    ui.show()
    
    # Add some sample scripts if none exist
    if not omni.scripts:
        try:
            # Sample Python script
            omni.create_script(
                name="hello_world",
                language=ScriptLanguage.PYTHON,
                code="""# Simple Python script\nprint('Hello from OMNISCRIBE!')\nprint('Context:', context)\n""",
                description="A simple hello world script in Python"
            )
            
            # Sample shell script
            omni.create_script(
                name="system_info",
                language=ScriptLanguage.SHELL,
                code="""#!/bin/bash\n# Simple system info script\necho "Hostname: $(hostname)"\necho "Uptime: $(uptime)"\n""",
                description="Display basic system information"
            )
            
            # Sample JavaScript script
            omni.create_script(
                name="array_ops",
                language=ScriptLanguage.JAVASCRIPT,
                code="""// Simple array operations\nconst numbers = [1, 2, 3, 4, 5];\nconst doubled = numbers.map(n => n * 2);\nconsole.log('Original:', numbers);\nconsole.log('Doubled:', doubled);\n""",
                description="JavaScript array operations example"
            )
            
            # Update the script list in the UI
            ui.update_script_list()
            
        except Exception as e:
            print(f"Error creating sample scripts: {e}", file=sys.stderr)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
