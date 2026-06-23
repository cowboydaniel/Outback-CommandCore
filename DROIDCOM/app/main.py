"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtCore import QTimer


def _apply_dark_title_bar(window) -> None:
    """Force the native title bar to render dark, matching the app's dark
    theme, on platforms where Qt doesn't pick this up automatically."""
    if sys.platform == "win32":
        try:
            import ctypes

            hwnd = int(window.winId())
            value = ctypes.c_int(1)
            for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (+ pre-20H1 fallback)
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
                if result == 0:
                    break
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a1a"))
            app.setPalette(palette)

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
        _apply_dark_title_bar(window)

    # Show main window after splash animation completes (5.9 seconds)
    QTimer.singleShot(5900, finish_startup)

    qt_app.exec()


if __name__ == "__main__":
    main()
