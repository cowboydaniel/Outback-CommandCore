"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

if __package__:
    from . import AndroidToolsModule
    from .config import APP_VERSION
    from ..ui.splash_screen import show_splash_screen
else:
    module_root = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(module_root))
    from DROIDCOM.app import AndroidToolsModule
    from DROIDCOM.app.config import APP_VERSION
    from DROIDCOM.ui.splash_screen import show_splash_screen


def main():
    """Main entry point for the application"""
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setApplicationVersion(APP_VERSION)

    # Show splash screen
    splash = show_splash_screen()
    qt_app.processEvents()

    splash.update_status("Scanning for devices...")
    qt_app.processEvents()

    window = QtWidgets.QWidget()
    window.setWindowTitle("DROIDCOM - Android Device Management")
    # Ensure window has minimize, maximize and close buttons
    window.setWindowFlags(
        QtCore.Qt.Window |
        QtCore.Qt.WindowMinimizeButtonHint |
        QtCore.Qt.WindowMaximizeButtonHint |
        QtCore.Qt.WindowCloseButtonHint
    )
    # Set a smaller default size that fits most screens
    window.resize(800, 600)  # Wider but shorter
    window.setMinimumSize(800, 400)  # Set minimum size

    # Set window icon
    icon_path = Path(__file__).resolve().parents[2] / 'icons' / 'droidcom.png'
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    layout = QtWidgets.QVBoxLayout(window)
    app = AndroidToolsModule(window)
    layout.addWidget(app)

    splash.update_status("Ready!")
    qt_app.processEvents()

    # Close splash and show main window after animation completes
    def show_main():
        splash.close()
        window.show()

    QTimer.singleShot(5900, show_main)

    qt_app.exec()


# For testing the module independently
if __name__ == "__main__":
    main()
