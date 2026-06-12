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

    main_windows = []

    def finish_startup() -> None:
        # Close splash screen first
        if splash:
            splash.close()

        # Create main window
        window = QtWidgets.QWidget()
        window.setWindowTitle("DROIDCOM - Android Device Management")
        window.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowMinimizeButtonHint |
            QtCore.Qt.WindowMaximizeButtonHint |
            QtCore.Qt.WindowCloseButtonHint
        )
        
        # Set window size to screen size
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window.resize(screen_geometry.width(), screen_geometry.height())
        window.setMinimumSize(screen_geometry.width() // 2, screen_geometry.height() // 2)

        # Set window icon
        icon_path = Path(__file__).resolve().parents[2] / 'icons' / 'droidcom.png'
        if icon_path.exists():
            window.setWindowIcon(QIcon(str(icon_path)))

        layout = QtWidgets.QVBoxLayout(window)
        app = AndroidToolsModule(window)
        layout.addWidget(app)
        main_windows.append(window)
        window.show()

    # Show main window after splash animation completes (5.9 seconds)
    QTimer.singleShot(5900, finish_startup)

    qt_app.exec()


if __name__ == "__main__":
    main()
