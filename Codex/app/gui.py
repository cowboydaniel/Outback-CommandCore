#!/usr/bin/env python3
"""
CommandCoreCodex AI Pipeline Control Center

A PySide6-based GUI for managing the AI training and code generation pipeline.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
    QLabel, QProgressBar, QLineEdit, QMessageBox, QDialog,
    QFormLayout, QGroupBox, QStatusBar, QCheckBox
)
from PySide6.QtCore import Qt, QThread, QObject, Slot, QTimer, Signal
from PySide6.QtGui import QAction, QTextCursor, QPalette, QColor, QIcon

# Import the orchestrator
from Codex.ai.orchestrator import Orchestrator
from Codex.app.config import AppConfig, DEFAULT_CONFIG
from Codex.tabs import (
    setup_data_prep_tab,
    setup_generation_tab,
    setup_logs_tab,
    setup_training_tab,
    setup_validation_tab,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    progress = Signal(int)
    status = Signal(str)
    error = Signal(str)
    finished = Signal()
    data_ready = Signal(dict)


class TrainingWorker(QObject):
    """Worker thread for running training in the background."""
    def __init__(self, orchestrator, params):
        super().__init__()
        self.orchestrator = orchestrator
        self.params = params
        self.is_running = True
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.status.emit("Starting training...")
            # Replace with actual training call
            # self.orchestrator.train_model(**self.params)
            for i in range(101):
                if not self.is_running:
                    break
                # Simulate training progress
                QThread.msleep(50)
                self.signals.progress.emit(i)
                self.signals.status.emit(f"Epoch {i}/100")
            
            if self.is_running:
                self.signals.status.emit("Training completed successfully")
                self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(f"Training error: {str(e)}")
        finally:
            self.signals.finished.emit()

    def stop(self):
        self.is_running = False


class AboutDialog(QDialog):
    """About dialog showing application information."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About CommandCoreCodex")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        title = QLabel("CommandCoreCodex AI Pipeline")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        version = QLabel("Version 1.0.0")
        description = QLabel(
            "A control center for managing AI training and code generation pipeline.\n\n"
            "© 2025 CommandCore. All rights reserved."
        )
        description.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(description)
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        self.setLayout(layout)


class SettingsDialog(QDialog):
    """Settings dialog for application preferences."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Theme settings
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout()
        
        self.dark_mode = QCheckBox("Dark Mode")
        theme_layout.addWidget(self.dark_mode)
        
        theme_group.setLayout(theme_layout)
        
        # Add more settings here as needed
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)


class CommandCoreGUI(QMainWindow):
    """Main application window for the CommandCoreCodex control center."""
    
    def __init__(self, config: AppConfig = DEFAULT_CONFIG):
        super().__init__()
        self.config = config
        self.orchestrator = Orchestrator()
        self.worker_thread = None
        self.worker = None
        self.dark_mode = False

        self.setWindowTitle(self.config.window_title)
        self.setMinimumSize(self.config.min_width, self.config.min_height)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'icons', 'codex.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()
        self.setup_connections()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_ui(self):
        """Set up the main UI components."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        setup_data_prep_tab(self)
        setup_training_tab(self)
        setup_generation_tab(self)
        setup_validation_tab(self)
        setup_logs_tab(self)
        
        main_layout.addWidget(self.tab_widget)
        
        # Set up menu bar
        self.setup_menu_bar()
    
    def setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
        appearance_action = QAction("&Appearance...", self)
        appearance_action.triggered.connect(self.show_settings)
        settings_menu.addAction(appearance_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    
    def setup_connections(self):
        """Set up signal-slot connections."""
        # Connect menu actions
        self.start_training_btn.clicked.connect(self.start_training)
        self.stop_training_btn.clicked.connect(self.stop_training)
        
        # Setup logging
        self.handler = GuiLogHandler()
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.handler.log_signal.connect(self.log_message)
        
        # Remove any existing handlers
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.addHandler(self.handler)
    
    # ===== Event Handlers =====
    
    def browse_dataset_dir(self):
        """Open a directory dialog to select the dataset directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Dataset Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if dir_path:
            self.dataset_path_edit.setText(dir_path)
    
    def prepare_dataset(self):
        """Prepare the dataset for training."""
        dataset_path = self.dataset_path_edit.text()
        
        if not dataset_path:
            QMessageBox.warning(self, "Error", "Please select a dataset directory first.")
            return
        
        try:
            self.log_message("Preparing dataset...")
            # Call orchestrator to prepare dataset
            # self.orchestrator.prepare_dataset(dataset_path)
            self.log_message("Dataset prepared successfully.")
        except Exception as e:
            self.log_message(f"Error preparing dataset: {str(e)}", is_error=True)
    
    def start_training(self):
        """Start the training process in a separate thread."""
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.log_message("Training is already in progress.", is_error=True)
            return
        
        # Get training parameters
        params = {
            'batch_size': self.batch_size.value(),
            'learning_rate': self.learning_rate.value(),
            'num_epochs': self.num_epochs.value()
        }
        
        # Set up worker thread
        self.worker_thread = QThread()
        self.worker = TrainingWorker(self.orchestrator, params)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.signals.progress.connect(self.update_training_progress)
        self.worker.signals.status.connect(self.update_training_status)
        self.worker.signals.error.connect(self.training_error)
        self.worker.signals.finished.connect(self.training_finished)
        
        # Start the worker
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        
        # Update UI
        self.start_training_btn.setEnabled(False)
        self.stop_training_btn.setEnabled(True)
        self.training_status.clear()
        self.log_message("Training started...")
    
    def stop_training(self):
        """Stop the training process."""
        if self.worker is not None:
            self.worker.stop()
            self.log_message("Stopping training...")
            self.stop_training_btn.setEnabled(False)
    
    def update_training_progress(self, value):
        """Update the training progress bar."""
        self.training_progress.setValue(value)
    
    def update_training_status(self, message):
        """Update the training status text."""
        self.training_status.appendPlainText(message)
        self.status_bar.showMessage(message)
    
    def training_error(self, error_message):
        """Handle training errors."""
        self.log_message(f"Training error: {error_message}", is_error=True)
        self.training_status.appendPlainText(f"ERROR: {error_message}")
        self.stop_training_btn.setEnabled(False)
        self.start_training_btn.setEnabled(True)
    
    def training_finished(self):
        """Clean up after training is finished."""
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker_thread.deleteLater()
        self.worker_thread = None
        self.worker = None
        
        self.start_training_btn.setEnabled(True)
        self.stop_training_btn.setEnabled(False)
        self.log_message("Training finished.")
    
    def generate_code(self):
        """Generate code based on the prompt."""
        prompt = self.prompt_edit.text().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt.")
            return
        
        try:
            self.log_message("Generating code...")

            # Check if model is trained
            if self.orchestrator.model is None:
                # If no model is trained, show a message and return
                self.log_message("No trained model available. Please train a model first.", is_error=True)
                self.generated_code.setPlainText(
                    "# No trained model available\n"
                    "# Please train a model first by:\n"
                    "# 1. Loading training data\n"
                    "# 2. Starting the training process\n"
                    f"# Then you can generate code from prompt: {prompt}"
                )
                return

            # Call orchestrator to generate code
            max_tokens = self.max_length.value() if hasattr(self, 'max_length') else 100
            generated = self.orchestrator.generate_code(
                prompt=prompt,
                max_tokens=max_tokens
            )

            # Display the generated code with the prompt
            full_code = f"{prompt}\n{generated}" if not generated.startswith(prompt) else generated
            self.generated_code.setPlainText(full_code)
            self.log_message("Code generation completed.")
        except Exception as e:
            self.log_message(f"Error generating code: {str(e)}", is_error=True)
    
    def run_linter(self):
        """Run the linter on the generated code."""
        code = self.generated_code.toPlainText().strip()
        
        if not code:
            QMessageBox.warning(self, "Error", "No code to lint. Please generate some code first.")
            return
        
        try:
            self.log_message("Running linter...")

            # Call orchestrator to run linter
            lint_results = self.orchestrator.lint_code(code)

            # Format the lint results for display
            if lint_results:
                output = "Linter Results:\n" + "-" * 40 + "\n"
                for i, issue in enumerate(lint_results, 1):
                    output += f"{i}. {issue}\n"
                output += "-" * 40 + f"\nTotal issues: {len(lint_results)}"
            else:
                output = "✓ No issues found. Code passed all lint checks."

            self.linter_output.setPlainText(output)
            self.log_message(f"Linting completed. Found {len(lint_results)} issue(s).")
        except Exception as e:
            self.log_message(f"Error running linter: {str(e)}", is_error=True)
    
    def run_in_sandbox(self):
        """Run the generated code in a sandboxed environment."""
        code = self.generated_code.toPlainText().strip()
        
        if not code:
            QMessageBox.warning(self, "Error", "No code to run. Please generate some code first.")
            return
        
        try:
            self.log_message("Running code in sandbox...")

            # Call orchestrator to run in sandbox
            stdout, stderr = self.orchestrator.run_sandboxed(code)

            # Format the sandbox output
            output = "Sandbox Execution Results:\n" + "=" * 40 + "\n\n"

            if stdout:
                output += "STDOUT:\n" + "-" * 20 + "\n"
                output += stdout + "\n\n"

            if stderr:
                output += "STDERR:\n" + "-" * 20 + "\n"
                output += stderr + "\n\n"

            if not stdout and not stderr:
                output += "(No output produced)\n"

            output += "=" * 40 + "\nExecution completed."

            self.sandbox_output.setPlainText(output)
            self.log_message("Sandbox execution completed.")
        except Exception as e:
            self.log_message(f"Error running in sandbox: {str(e)}", is_error=True)
    
    def save_logs(self):
        """Save the logs to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_display.toPlainText())
                self.log_message(f"Logs saved to {file_path}")
            except Exception as e:
                self.log_message(f"Error saving logs: {str(e)}", is_error=True)
    
    def clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
    
    def log_message(self, message, is_error=False):
        """Add a message to the log display."""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        log_entry = f"[{timestamp}] {message}"
        
        # Add to log display
        self.log_display.appendPlainText(log_entry)
        
        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
        
        # Log to console as well
        if is_error:
            logger.error(message)
        else:
            logger.info(message)
    
    def show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Apply settings
            if dialog.dark_mode.isChecked() != self.dark_mode:
                self.toggle_dark_mode()
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            # Set dark palette
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            
            self.setPalette(palette)
            self.log_message("Dark mode enabled")
        else:
            # Reset to default palette
            self.setPalette(QApplication.style().standardPalette())
            self.log_message("Light mode enabled")
    
    def closeEvent(self, event):
        """Handle the window close event."""
        if self.worker_thread is not None and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                'Training in Progress',
                'Training is still in progress. Are you sure you want to quit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker_thread.quit()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class GuiLogHandler(logging.Handler, QObject):
    """Custom logging handler that emits log messages to the GUI."""
    log_signal = Signal(str, bool)  # message, is_error
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
    
    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg, record.levelno >= logging.ERROR)


def main():
    """Main function to start the application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Create and show the main window
    window = CommandCoreGUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
