"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys

from PySide6 import QtCore, QtWidgets

if __package__:
    from .app import AndroidToolsModule
else:
    module_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(module_root))
    from DROIDCOM.app import AndroidToolsModule


def main():
    """Main entry point for the application"""
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setApplicationVersion("1.0.0")

    window = QtWidgets.QWidget()
    window.setWindowTitle("Android Tools Module Test")
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

    layout = QtWidgets.QVBoxLayout(window)
    app = AndroidToolsModule(window)
    layout.addWidget(app)

    window.show()
    qt_app.exec()


# For testing the module independently
if __name__ == "__main__":
    main()
