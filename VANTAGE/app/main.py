#!/usr/bin/env python3
"""VANTAGE - UI Framework and Style Management"""

import logging
import os
import sys
import time
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, QSize, QTimer, QCoreApplication
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
    
    # Track initialization progress and timing
    initialization_complete = False
    main_window = None
    tabs_data = {}
    splash_start_time = time.time()  # Record when splash started
    last_message_time = 0  # Track time of last message update
    MINIMUM_SPLASH_DURATION = 5.9  # Minimum splash screen time in seconds
    
    def update_splash_message(message: str, progress: int = None):
        """Update splash screen with current loading status and progress.
        
        Args:
            message: The status message to display
            progress: Optional progress percentage (0-100)
        """
        _update_message(message, progress)
        app.processEvents()  # Ensure UI updates happen
    
    def _update_message(message: str, progress: int = None):
        """Internal function to update the splash screen message and progress.
        
        Args:
            message: Status message to display
            progress: Optional progress percentage (0-100)
        """
        if splash and splash.isVisible():
            try:
                if hasattr(splash, 'update_status'):
                    splash.update_status(message)
                if progress is not None and hasattr(splash, 'set_progress'):
                    splash.set_progress(progress)
                app.processEvents()  # Force UI update
            except RuntimeError:
                # Handle case where app is shutting down
                pass
    
    def background_initialization():
        """Perform all heavy initialization tasks in background."""
        nonlocal initialization_complete, main_window, tabs_data
        
        try:
            # Step 1: Update splash and import modules
            update_splash_message("Loading modules...")
            from tabs.dashboard import DashboardTab
            from tabs.devices import DevicesTab  
            from tabs.performance_analytics import PerformanceAnalyticsTab
            
            time.sleep(0.5)  # 500ms delay
            
            # Step 2: Create main window (but don't show it yet)
            update_splash_message("Initializing interface...")
            main_window = VantageUI(show_immediately=False)  # Don't show until splash is done
            main_windows.append(main_window)  # Prevent garbage collection
            time.sleep(0.5)  # 500ms delay
            
            # Step 3: Initialize tabs and start data collection
            update_splash_message("Loading dashboard...")
            dashboard_tab = DashboardTab()
            time.sleep(0.5)  # 500ms delay
            
            # If your tabs have initialization methods that fetch data, call them here
            if hasattr(dashboard_tab, 'initialize_data'):
                dashboard_tab.initialize_data()
            
            update_splash_message("Initializing performance analytics...")
            performance_tab = PerformanceAnalyticsTab()
            time.sleep(0.5)  # 500ms delay
            
            # Start any background data collection
            if hasattr(performance_tab, 'start_data_collection'):
                performance_tab.start_data_collection()
            
            update_splash_message("Scanning devices...")
            devices_tab = DevicesTab()
            time.sleep(0.5)  # 500ms delay
            
            # Perform device discovery/scanning during splash
            if hasattr(devices_tab, 'scan_devices'):
                devices_tab.scan_devices()
            
            # Step 4: Add tabs to main window
            update_splash_message("Finalizing interface...")
            time.sleep(0.5)  # 500ms delay
            main_window.add_tab(dashboard_tab, "Dashboard")
            time.sleep(0.2)  # 200ms between tab additions
            main_window.add_tab(performance_tab, "Performance Analytics") 
            time.sleep(0.2)  # 200ms between tab additions
            main_window.add_tab(devices_tab, "Devices")
            time.sleep(0.5)  # 500ms delay
            
            # Set Dashboard as the default tab
            main_window.tab_widget.setCurrentWidget(dashboard_tab)
            
            # Store references for later use
            tabs_data = {
                'dashboard': dashboard_tab,
                'performance': performance_tab,
                'devices': devices_tab
            }
            
            update_splash_message("Ready!")
            
            # Mark initialization as complete
            initialization_complete = True
            
        except Exception as e:
            logger.error(f"Error during background initialization: {e}")
            update_splash_message(f"Error: {e}")
            # Still mark as complete to avoid hanging
            initialization_complete = True
    
    def check_initialization_and_show():
        """Check if initialization is complete AND minimum splash time has elapsed."""
        nonlocal initialization_complete, main_window, splash_start_time
        
        # Check if both conditions are met:
        # 1. Initialization is complete
        # 2. Minimum splash duration has elapsed
        elapsed_time = time.time() - splash_start_time
        minimum_time_elapsed = elapsed_time >= MINIMUM_SPLASH_DURATION
        
        if initialization_complete and minimum_time_elapsed:
            try:
                if main_window:
                    # Show the fully initialized window
                    main_window.showMaximized()
                    
                    # Close splash screen
                    if splash and splash.isVisible():
                        splash.close()
                    
                    # Optional: Trigger any post-show initialization
                    for tab_name, tab_widget in tabs_data.items():
                        if hasattr(tab_widget, 'on_show'):
                            tab_widget.on_show()
                    
                    logger.info(f"VANTAGE application fully loaded and ready (took {elapsed_time:.1f}s)")
                else:
                    logger.error("Main window not created during initialization")
                    if splash and splash.isVisible():
                        splash.close()
                    sys.exit(1)
            except Exception as e:
                logger.error(f"Error showing main window: {e}")
                if splash and splash.isVisible():
                    splash.close()
                sys.exit(1)
        else:
            # Show status of what we're waiting for
            if initialization_complete and not minimum_time_elapsed:
                remaining_time = MINIMUM_SPLASH_DURATION - elapsed_time
                update_splash_message(f"Ready! Starting in {remaining_time:.1f}s...")
            elif not initialization_complete and minimum_time_elapsed:
                update_splash_message("Finishing initialization...")
            
            # Check again in 100ms
            QTimer.singleShot(100, check_initialization_and_show)
    
    # Start background initialization immediately
    QTimer.singleShot(100, background_initialization)  # Small delay to ensure splash is shown
    
    # Start checking for completion
    QTimer.singleShot(200, check_initialization_and_show)
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()