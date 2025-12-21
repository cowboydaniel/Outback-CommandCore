"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys

from PySide6 import QtWidgets

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
    window.resize(700, 800)

    layout = QtWidgets.QVBoxLayout(window)
    app = AndroidToolsModule(window)
    layout.addWidget(app)

    window.show()
    qt_app.exec()


# For testing the module independently
if __name__ == "__main__":
    main()
