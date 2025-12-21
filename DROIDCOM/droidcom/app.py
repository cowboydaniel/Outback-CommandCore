import sys

from PySide6 import QtCore, QtWidgets

from droidcom.utils import threading as threading_utils


class AndroidToolsModule(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("DROIDCOM module wiring placeholder.")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    QtCore.QCoreApplication.setApplicationVersion("1.0.0")

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Android Tools Module Test")
    window.resize(700, 800)
    widget = AndroidToolsModule(window)
    window.setCentralWidget(widget)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
