#!/usr/bin/env python3
"""
BLACKSTORM - Secure Data Erasure & Forensic Suite
Main application launcher.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
    QPushButton, QMessageBox, QStatusBar, QFileDialog, QMenu, QDialog, 
    QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QProgressBar, QListWidget, QListWidgetItem, QHBoxLayout, QGroupBox, 
    QScrollArea, QFrame, QToolBar, QTextEdit, QProgressDialog,
    QDoubleSpinBox, QGridLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsProxyWidget, QGraphicsWidget,
    QInputDialog, QMenuBar, QFontComboBox
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QSize, QTimer, QProcess, QPointF, QRectF, QObject,
    QSettings, QByteArray, QFile, QTextStream, QIODevice
)
from PySide6.QtGui import (
    QIcon, QFont, QColor, QPalette, QTextCursor, QPainter, QPen, QBrush, QCursor,
    QLinearGradient, QGradient, QPainterPath, QPolygonF, QPixmap, QAction,
    QFontDatabase, QGuiApplication
)

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from BLACKSTORM.app.config import (
    APP_TITLE,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_SETTINGS,
    ICON_PATH,
    SETTINGS_FILE,
    WINDOW_MIN_SIZE,
)
from BLACKSTORM.core.utils import deep_merge
from BLACKSTORM.tabs.advanced_tab import AdvancedTab
from BLACKSTORM.tabs.bulk_operations_tab import BulkOperationsTab
from BLACKSTORM.tabs.dashboard_tab import DashboardTab
from BLACKSTORM.tabs.device_management_tab import DeviceManagementTab
from BLACKSTORM.tabs.forensic_tools_tab import ForensicToolsTab
from BLACKSTORM.tabs.security_compliance_tab import SecurityComplianceTab
from BLACKSTORM.tabs.settings_tab import SettingsTab
from BLACKSTORM.tabs.wipe_operations_tab import WipeOperationsTab
from BLACKSTORM.ui.splash_screen import show_splash_screen

class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading forensic modules...")
            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            logging.exception("BLACKSTORM startup failed")
            self.failed.emit(str(exc))


class BlackStormLauncher(QMainWindow):
    """
    Main application window for BLACKSTORM - Secure Data Erasure & Forensic Suite.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        # Set window icon
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        # Initialize logging
        self._setup_logging()
        self.logger = logging.getLogger('BlackStormLauncher')
        
        # Initialize application state
        self.settings_file = SETTINGS_FILE
        
        # Load default settings first
        self.settings = self._load_settings()
        
        # Log application start
        self.logger.info("BLACKSTORM Application Started")
        
        # Setup UI first
        self.setup_ui()
        
        # Then apply settings to initialize everything
        self.reload_settings()
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2A2D2E;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E3E;
                background: #2A2D2E;
                padding: 5px;
                border-top: none;
            }
            QTabBar::tab {
                background: #252729;
                color: #E0E0E0;
                padding: 8px 20px;
                border: 1px solid #3E3E3E;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 120px;
                font-weight: 500;
                text-align: center;
            }
            QTabBar::tab:selected {
                background: #1E88E5;
                color: white;
                border-color: #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #3E3E3E;
            }
            QPushButton {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #34495E;
            }
            QPushButton:pressed {
                background-color: #2C3E50;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3A3A3A;
                color: #ECF0F1;
                border: 1px solid #4A4A4A;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
                background-color: #2A2A2A;
                color: #7F8C8D;
            }
            QLabel {
                color: #ECF0F1;
            }
            QProgressBar {
                border: 1px solid #4A4A4A;
                border-radius: 3px;
                text-align: center;
                background-color: #2A2D2E;
            }
            QProgressBar::chunk {
                background-color: #1E88E5;
                width: 10px;
            }
            QStatusBar {
                background-color: #2A2D2E;
                color: #ECF0F1;
                border-top: 1px solid #3E3E3E;
            }
            QStatusBar QLabel {
                padding: 0 5px;
                border-left: 1px solid #3E3E3E;
            }
            QStatusBar QLabel:first-child {
                border-left: none;
            }
            QGroupBox {
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget, QTreeView, QTableView {
                background-color: #2A2D2E;
                color: #ECF0F1;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item:selected, QTreeView::item:selected, QTableView::item:selected {
                background-color: #1E88E5;
                color: white;
            }
            QListWidget::item:hover, QTreeView::item:hover, QTableView::item:hover {
                background-color: #3A3A3A;
            }
            QHeaderView::section {
                background-color: #2A2D2E;
                color: #ECF0F1;
                padding: 5px;
                border: 1px solid #3E3E3E;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #2A2D2E;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #4A4A4A;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #5A5A5A;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Initialize UI components
        self.setup_ui()
        
        # Set up signal connections
        self.setup_connections()
        
    def setup_ui(self):
        """Set up the main UI components."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.setup_tabs()
        
    def setup_tabs(self):
        """Set up the application tabs."""
        # Create and add dashboard tab
        self.dashboard_tab = DashboardTab(parent=self, tab_widget=self.tab_widget)
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
    
        # Create other tab instances
        self.wipe_operations_tab = WipeOperationsTab()
        
        # Create and add forensic tools tab
        self.forensic_tools_tab = ForensicToolsTab()
        forensic_tools_widget = self.forensic_tools_tab.create_forensic_tools_tab()
        
        self.device_management_tab = DeviceManagementTab()
        self.bulk_operations_tab = BulkOperationsTab()
        self.security_compliance_tab = SecurityComplianceTab()
        self.settings_tab = SettingsTab()
        self.advanced_tab = AdvancedTab()
    
        # Add other tabs to tab widget
        self.tab_widget.addTab(self.wipe_operations_tab, "Wipe Operations")
        self.tab_widget.addTab(forensic_tools_widget, "Forensic Tools")
        self.tab_widget.addTab(self.device_management_tab, "Device Management")
        self.tab_widget.addTab(self.bulk_operations_tab, "Bulk Operations")
        self.tab_widget.addTab(self.security_compliance_tab, "Security && Compliance")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.advanced_tab, "Advanced")
        
        # Apply settings to all tabs after they're created
        self._apply_settings_to_tabs()
        
    def _load_settings(self):
        """Load application settings from file."""
        if not os.path.exists(self.settings_file):
            return DEFAULT_SETTINGS.copy()
            
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                return deep_merge(DEFAULT_SETTINGS, settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()
            
    def _save_settings(self):
        """Save current settings to file."""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def reload_settings(self):
        """Reload settings from file and apply them.
        
        Returns:
            bool: True if settings were reloaded successfully, False otherwise
        """
        try:
            # Reload settings from file
            new_settings = self._load_settings()
            if not new_settings:
                print("No settings found or error loading settings")
                return False
                
            self.settings = new_settings
            
            # Apply settings to the entire application
            # This will also update all tabs including settings_tab
            self._apply_settings()
                
            return True
            
        except Exception as e:
            import traceback
            print(f"Error reloading settings: {e}\n{traceback.format_exc()}")
            return False
    
    def _apply_settings(self):
        """Apply loaded settings to the UI and all tabs."""
        try:
            # Apply window geometry if saved
            if 'window_geometry' in self.settings and self.settings['window_geometry']:
                self.restoreGeometry(self.settings['window_geometry'])
                
            # Apply window state if saved
            if 'window_state' in self.settings and self.settings['window_state']:
                self.restoreState(self.settings['window_state'])
                
            # Get font settings with defaults
            font_family = self.settings.get('font', {}).get('family', DEFAULT_FONT_FAMILY)
            font_size = self.settings.get('font', {}).get('size', DEFAULT_FONT_SIZE)
            
            # Apply font settings to the application
            app = QApplication.instance()
            if app:
                font = QFont(font_family)
                font.setPointSize(font_size)
                app.setFont(font)
                
                # Apply font to all existing widgets
                for widget in app.allWidgets():
                    try:
                        widget.setFont(font)
                    except:
                        continue
            
            # Apply theme
            theme = self.settings.get('ui_theme', 'dark').lower()
            if theme == 'dark':
                self.setStyleSheet("""
                    QMainWindow, QDialog, QWidget {
                        background-color: #2A2D2E;
                        color: #E0E0E0;
                    }
                    /* Rest of the dark theme styles */
                """)
            elif theme == 'light':
                self.setStyleSheet("""
                    QMainWindow, QDialog, QWidget {
                        background-color: #F5F5F5;
                        color: #333333;
                    }
                    /* Rest of the light theme styles */
                """)
                
            # Apply settings to all tabs
            self._apply_settings_to_tabs()
            
        except Exception as e:
            print(f"Error applying settings: {e}")
            
    def _apply_settings_to_tabs(self):
        """Apply current settings to all tabs."""
        try:
            # Make sure we have tabs to work with
            if not hasattr(self, 'tab_widget') or not self.tab_widget:
                return
                
            # Get all tab widgets
            tabs = []
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    tabs.append(widget)
            
            # Also include direct tab references if they exist
            tab_references = [
                getattr(self, attr) for attr in dir(self) 
                if attr.endswith('_tab') and hasattr(getattr(self, attr), 'set_settings')
            ]
            
            # Combine and deduplicate
            all_tabs = list({id(tab): tab for tab in tabs + tab_references}.values())
            
            # Apply settings to each tab
            for tab in all_tabs:
                try:
                    if hasattr(tab, 'set_settings') and callable(tab.set_settings):
                        tab.set_settings(self.settings)
                except Exception as tab_error:
                    print(f"Error applying settings to tab {tab}: {tab_error}")
                    
        except Exception as e:
            print(f"Error in _apply_settings_to_tabs: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_connections(self):
        """Set up signal-slot connections."""
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
    def _setup_logging(self):
        """Set up logging configuration and clear existing logs on startup."""
        log_dir = os.path.expanduser('~/.config/blackstorm/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'blackstorm.log')
        
        # Clear existing log file if it exists
        try:
            if os.path.exists(log_file):
                with open(log_file, 'w'):
                    pass  # This clears the file
                os.chmod(log_file, 0o644)  # Ensure proper permissions
                print(f"Cleared existing log file: {log_file}")
        except Exception as e:
            print(f"Warning: Could not clear log file {log_file}: {e}")
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers to avoid duplicate logs
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            if hasattr(handler, 'close'):
                handler.close()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add file handler with rotation (10MB per file, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also log to console in debug mode
        if os.getenv('BLACKSTORM_DEBUG'):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
        # Log that logging has been initialized
        logger.info("Logging initialized")
    
    def log_event(self, event_type, details=None):
        """Log an application event with timestamp and details."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'details': details or {}
        }
        self.logger.info("Application Event: %s", json.dumps(log_entry, default=str))
        
    def on_tab_changed(self, index):
        """Handle tab change events.
        
        Args:
            index (int): Index of the newly selected tab
        """
        tab_name = self.tab_widget.tabText(index)
        self.statusBar().showMessage(f"Switched to {tab_name} tab")
        self.log_event('tab_changed', {'tab_name': tab_name, 'tab_index': index})
        
        # Call the tab's refresh method if it exists
        current_widget = self.tab_widget.widget(index)
        if hasattr(current_widget, 'refresh') and callable(getattr(current_widget, 'refresh')):
            try:
                current_widget.refresh()
                self.logger.debug(f"Refreshed tab: {tab_name}")
            except Exception as e:
                self.logger.error(f"Error refreshing tab {tab_name}: {str(e)}", exc_info=True)
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Log application closing
        self.log_event('application_closing')
        
        # Stop any running operations
        if hasattr(self, 'wipe_worker') and self.wipe_worker:
            self.wipe_worker.stop()
            self.log_event('worker_stopped', {'worker_type': 'wipe_worker'})
            
        if hasattr(self, 'imaging_worker') and self.imaging_worker:
            self.imaging_worker.stop()
            self.log_event('worker_stopped', {'worker_type': 'imaging_worker'})
            
        # Save settings before closing
        self._save_settings()
        self.log_event('settings_saved')
        
        # Log final message before closing
        self.logger.info("BLACKSTORM Application Shutting Down")
        
        # Clean up logging handlers
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        
        # Accept the close event
        event.accept()

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setApplicationVersion("1.0.0")

    # Set application style
    app.setStyle('Fusion')

    # Show splash screen
    splash = show_splash_screen()
    app.processEvents()

    splash_start_time = time.time()
    minimum_splash_duration = 5.9

    thread = QThread()
    worker = StartupWorker()
    worker.moveToThread(thread)

    worker.status.connect(splash.update_status)
    if hasattr(splash, "set_progress"):
        worker.progress.connect(splash.set_progress)

    main_windows = []

    def show_main() -> None:
        elapsed = time.time() - splash_start_time
        remaining = max(0, minimum_splash_duration - elapsed)

        def finish_startup() -> None:
            nonlocal main_window
            if splash and splash.isVisible():
                splash.close()
            window = BlackStormLauncher()
            main_windows.append(window)
            window.show()
            window.showMaximized()

        QTimer.singleShot(int(remaining * 1000), finish_startup)

    def handle_error(message: str) -> None:
        if splash and splash.isVisible():
            splash.update_status(f"Error: {message}")
        QTimer.singleShot(2000, app.quit)

    worker.finished.connect(show_main)
    worker.failed.connect(handle_error)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.started.connect(worker.run)
    thread.start()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
