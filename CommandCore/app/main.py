#!/usr/bin/env python3
"""
CommandCore Launcher Application

Main entry point for the CommandCore launcher application.
"""
import sys
import os

# Add parent directory to path to allow package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check and install dependencies before importing anything else
def ensure_dependencies():
    """Ensure all module dependencies are installed before starting."""
    try:
        from app.dependency_installer import check_and_install_dependencies
        print("\nChecking module dependencies...\n")
        success = check_and_install_dependencies(verbose=True)
        if not success:
            print("\nWarning: Some dependencies could not be installed.")
            print("The application may not function correctly.")
            response = input("\nContinue anyway? [y/N]: ").strip().lower()
            if response != 'y':
                print("Exiting.")
                sys.exit(1)
        print()  # Add blank line before Qt output
    except Exception as e:
        print(f"Warning: Dependency check failed: {e}")
        print("Continuing with application startup...")

# Run dependency check if not already done
if '--skip-deps' not in sys.argv:
    ensure_dependencies()
else:
    sys.argv.remove('--skip-deps')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QColor, QFont, QIcon

from app.config import Config
from ui.splash_screen import SplashScreen


class CommandCoreLauncher(QMainWindow):
    """Main application window for the CommandCore Launcher."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("CommandCore Launcher")
        self.setMinimumSize(1024, 768)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'CommandCore.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Center the window on screen
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry()
        frame_geometry.moveCenter(screen.center())
        self.move(frame_geometry.topLeft())
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2A2D2E;
                color: #ECF0F1;
            }
            
            QTabWidget::pane {
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                margin: 8px;
                padding: 8px;
                background: #3A3A3A;
            }
            
            QTabBar::tab {
                background: #2A2D2E;
                color: #B0B0B0;
                padding: 8px 16px;
                border: 1px solid #3E3E3E;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: #3A3A3A;
                color: #ECF0F1;
                border-bottom: 1px solid #3A3A3A;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:hover:!selected {
                background: #353839;
            }
        """)
        
        # Set application font
        font = QFont('Segoe UI', 10)
        QApplication.setFont(font)
        
        self.init_ui()
        self.show()
    
    def init_ui(self):
        """Initialize the main UI components."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        
        # Add tabs (to be implemented in tab modules)
        self.load_tabs()
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
    
    def load_tabs(self):
        """Load and initialize tab modules."""
        # Import tab modules
        from tabs.dashboard_tab import DashboardTab
        from tabs.application_manager_tab import ApplicationManagerTab
        
        # Create and add tabs
        self.dashboard_tab = DashboardTab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Store tabs in a dictionary for easy access
        self.tabs = {
            "Dashboard": 0,
            "Application Manager": 1
        }
        
        # Add Application Manager tab
        self.tab_widget.addTab(ApplicationManagerTab(), "Application Manager")
        
        # Connect signals
        self.dashboard_tab.request_tab_change.connect(self.switch_to_tab)
    
    def switch_to_tab(self, tab_name):
        """Switch to the specified tab by name."""
        if tab_name in self.tabs:
            self.tab_widget.setCurrentIndex(self.tabs[tab_name])
        else:
            print(f"Tab '{tab_name}' not found")


def show_splash_screen():
    """Show the splash screen during application startup."""
    from ui.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    return splash


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CommandCore")
    app.setApplicationDisplayName("CommandCore - Device Management")
    app.setApplicationVersion("1.0.0")
    
    # Show splash screen
    splash = show_splash_screen()
    if not splash:
        print("Warning: Failed to create splash screen. Starting without splash...")
    
    # Process events to make sure the splash screen is shown immediately
    app.processEvents()
    
    # Store the main window in a list to prevent garbage collection
    main_windows = []
    
    def initialize_and_show_main_window():
        """Initialize and show the main window, then close splash."""
        nonlocal splash
        try:
            # Create the main window
            window = CommandCoreLauncher()
            
            # Store the window to prevent garbage collection
            main_windows.append(window)
            
            # Show the main window
            window.show()
            
            # Close the splash screen if it's still open
            if splash and splash.isVisible():
                splash.finish(window)
                splash = None  # Clear the reference to splash screen
            
        except Exception as e:
            print(f"Error initializing application: {e}")
            if splash and splash.isVisible():
                splash.close()
            sys.exit(1)
    
    # Schedule the main window initialization to start after 5.9 seconds
    QTimer.singleShot(5900, initialize_and_show_main_window)
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
