#!/usr/bin/env python3
"""VANTAGE - UI Framework and Style Management"""

import logging
import os
import sys
import time
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, QSize, QTimer, QCoreApplication, QObject, QThread
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QStatusBar
)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.splash_screen import show_splash_screen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/vantage_ui.log')),
    ]
)
logger = logging.getLogger('VANTAGE_UI')


    
class VantageUI(QMainWindow):
    """Main VANTAGE application window handling UI initialization and tab management."""

    # Signal emitted when the active tab changes
    tab_changed = Signal(int)
    
    def __init__(self, parent: Optional[QWidget] = None, show_immediately: bool = True):
        """Initialize the main UI window.

        Args:
            parent: Parent widget
            show_immediately: If True, shows the window maximized immediately.
                            If False, window is created but not shown (for splash screen scenarios)
        """
        super().__init__(parent)
        self.setWindowTitle("VANTAGE")
        self.setMinimumSize(1024, 768)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'icons', 'vantage.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize tabs
        self.tabs: Dict[str, QWidget] = {}
        self.tab_widget: Optional[QTabWidget] = None
        
        # Setup the UI
        self.init_ui()
        self.apply_styles()
        
        # Only show immediately if requested (default behavior for backwards compatibility)
        if show_immediately:
            self.showMaximized()
    
    # ... rest of the VantageUI class methods remain the same ...
    
    def init_ui(self) -> None:
        """Initialize the main UI components."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(False)  # Disable tab movement
        self.tab_widget.setTabsClosable(False)  # Remove close buttons
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def apply_styles(self) -> None:
        """Apply the application-wide styles and palette."""
        # Set dark theme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
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
        
        # Apply the palette
        QApplication.setPalette(palette)
        
        # Set application-wide stylesheet
        style_sheet = """
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
        """
        self.setStyleSheet(style_sheet)
    
    def add_tab(self, widget: QWidget, title: str, icon=None) -> int:
        """Add a new tab to the main window.
        
        Args:
            widget: The widget to add as a tab
            title: The title of the tab
            icon: Optional icon for the tab
            
        Returns:
            int: The index of the new tab
        """
        if not self.tab_widget:
            logger.error("Tab widget not initialized")
            return -1
            
        # Add tab to the tab widget
        index = self.tab_widget.addTab(widget, title)
        
        # Store reference to the tab widget
        self.tabs[title] = widget
        
        # Set tab tooltip
        self.tab_widget.setTabToolTip(index, f"Switch to {title}")
        if icon:
            self.tab_widget.setTabIcon(index, icon)
            
        self.tabs[title] = widget
        self.tab_widget.setCurrentIndex(index)
        return index
    
    def close_tab(self, index: int) -> None:
        """Close a tab at the specified index.
        
        Args:
            index: The index of the tab to close
        """
        if not self.tab_widget:
            return
            
        widget = self.tab_widget.widget(index)
        if widget:
            widget.deleteLater()
            self.tab_widget.removeTab(index)
            
            # Remove from tabs dictionary
            for title, w in list(self.tabs.items()):
                if w == widget:
                    del self.tabs[title]
                    break
    
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change events.
        
        Args:
            index: The index of the newly selected tab
        """
        self.tab_changed.emit(index)
        
        # Update window title with current tab
        if self.tab_widget:
            tab_text = self.tab_widget.tabText(index)
            self.setWindowTitle(f"VANTAGE - {tab_text}")


class StartupWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.status.emit("Loading modules...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Initializing interface...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Loading dashboard...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Initializing performance analytics...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Scanning devices...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Finalizing interface...")
            time.sleep(0.5)  # 500ms delay

            self.status.emit("Ready!")
            self.finished.emit()
        except Exception as exc:
            logger.error("Error during background initialization: %s", exc, exc_info=True)
            self.failed.emit(str(exc))

def main():
    """Main entry point for the VANTAGE UI application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("VANTAGE")
    app.setApplicationDisplayName("VANTAGE - Device Intelligence Platform")
    app.setApplicationVersion("1.0.0")
    
    # Show splash screen
    splash = show_splash_screen()
    if not splash:
        print("Warning: Failed to create splash screen. Starting without splash...")
    
    # Process events to make sure the splash screen is shown immediately
    app.processEvents()
    
    # Store the main window in a list to prevent garbage collection
    main_windows = []

    splash_start_time = time.time()  # Record when splash started
    minimum_splash_duration = 5.9  # Minimum splash screen time in seconds

    def update_splash_message(message: str) -> None:
        """Update splash screen with current loading status."""
        if splash and splash.isVisible():
            try:
                if hasattr(splash, 'update_status'):
                    splash.update_status(message)
            except RuntimeError:
                # Handle case where app is shutting down
                pass

    thread = QThread()
    worker = StartupWorker()
    worker.moveToThread(thread)

    worker.status.connect(update_splash_message)
    if splash and hasattr(splash, 'set_progress'):
        worker.progress.connect(splash.set_progress)

    def show_main() -> None:
        elapsed_time = time.time() - splash_start_time
        remaining = max(0, minimum_splash_duration - elapsed_time)

        def finish_startup() -> None:
            if splash and splash.isVisible():
                splash.close()

            from tabs.dashboard import DashboardTab
            from tabs.devices import DevicesTab
            from tabs.performance_analytics import PerformanceAnalyticsTab

            main_window = VantageUI(show_immediately=False)
            dashboard_tab = DashboardTab(main_window=main_window)
            performance_tab = PerformanceAnalyticsTab()
            devices_tab = DevicesTab()

            if hasattr(dashboard_tab, 'initialize_data'):
                dashboard_tab.initialize_data()
            if hasattr(performance_tab, 'start_data_collection'):
                performance_tab.start_data_collection()
            if hasattr(devices_tab, 'scan_devices'):
                devices_tab.scan_devices()

            main_window.add_tab(dashboard_tab, "Dashboard")
            main_window.add_tab(performance_tab, "Performance Analytics")
            main_window.add_tab(devices_tab, "Devices")
            main_window.tab_widget.setCurrentWidget(dashboard_tab)

            tabs_data = {
                'dashboard': dashboard_tab,
                'performance': performance_tab,
                'devices': devices_tab
            }

            main_windows.append(main_window)
            main_window.showMaximized()

            # Optional: Trigger any post-show initialization
            for tab_widget in tabs_data.values():
                if hasattr(tab_widget, 'on_show'):
                    tab_widget.on_show()

            logger.info("VANTAGE application fully loaded and ready (took %.1fs)", elapsed_time)

        QTimer.singleShot(int(remaining * 1000), finish_startup)

    def handle_error(message: str) -> None:
        update_splash_message(f"Error: {message}")
        QTimer.singleShot(2000, QCoreApplication.quit)

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
