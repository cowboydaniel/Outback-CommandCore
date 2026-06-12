"""
DROIDCOM - Icon utilities for SVG loading
"""

from PySide6 import QtCore, QtGui, QtWidgets, QtSvg
import os


def get_icon_path(icon_name):
    """Get the path to an SVG icon"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'icons', f'{icon_name}.svg')


def load_svg_icon(icon_name, size=16):
    """Load an SVG icon as QIcon"""
    icon_path = get_icon_path(icon_name)
    if os.path.exists(icon_path):
        # Create a pixmap from the SVG
        renderer = QtSvg.QSvgRenderer(icon_path)
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QtGui.QIcon(pixmap)
    return QtGui.QIcon()


def load_svg_pixmap(icon_name, size=16):
    """Load an SVG icon as QPixmap"""
    icon_path = get_icon_path(icon_name)
    if os.path.exists(icon_path):
        renderer = QtSvg.QSvgRenderer(icon_path)
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    return QtGui.QPixmap()


def create_icon_label(icon_name, size=16, tooltip=None):
    """Create a QLabel with an SVG icon"""
    label = QtWidgets.QLabel()
    pixmap = load_svg_pixmap(icon_name, size)
    label.setPixmap(pixmap)
    if tooltip:
        label.setToolTip(tooltip)
    return label


def get_status_icon(installed, size=16):
    """Get success or error icon based on installation status"""
    icon_name = 'success' if installed else 'error'
    return load_svg_pixmap(icon_name, size)
