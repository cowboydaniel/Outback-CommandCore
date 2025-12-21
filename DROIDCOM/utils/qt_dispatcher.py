"""
DROIDCOM - Qt UI dispatcher utilities.
Provides Qt-based scheduling and signal helpers for UI-safe updates.
"""

from PySide6 import QtCore


class UiDispatcher(QtCore.QObject):
    """Qt signal dispatcher to marshal callbacks onto the UI thread."""

    run_in_ui = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.run_in_ui.connect(self._execute)

    @QtCore.Slot(object)
    def _execute(self, callback):
        if callable(callback):
            callback()


def get_ui_dispatcher(owner):
    """Return a cached UiDispatcher for the owner."""
    dispatcher = getattr(owner, "_ui_dispatcher", None)
    if dispatcher is None:
        dispatcher = UiDispatcher()
        owner._ui_dispatcher = dispatcher
    return dispatcher


def emit_ui(owner, callback):
    """Emit a callback onto the UI thread using Qt signals."""
    get_ui_dispatcher(owner).run_in_ui.emit(callback)


def schedule_ui(callback, delay_ms=0):
    """Schedule a callback on the Qt event loop."""
    QtCore.QTimer.singleShot(delay_ms, callback)


def set_text(widget, text):
    """Set text on a QLabel/Qt widget, with a Tk fallback."""
    if hasattr(widget, "setText"):
        widget.setText(text)
    elif hasattr(widget, "config"):
        widget.config(text=text)
    elif hasattr(widget, "configure"):
        widget.configure(text=text)
    elif hasattr(widget, "set"):
        widget.set(text)


def append_text(widget, text, tag=None):
    """Append text to a QTextEdit-like widget with Tk fallback."""
    if hasattr(widget, "append"):
        widget.append(text.rstrip("\n"))
        return
    if hasattr(widget, "insert"):
        try:
            if tag is not None:
                widget.insert("end", text, tag)
            else:
                widget.insert("end", text)
        except TypeError:
            widget.insert("end", text)


def clear_text(widget):
    """Clear text from a text widget with Qt/Tk support."""
    if hasattr(widget, "clear"):
        widget.clear()
        return
    if hasattr(widget, "delete"):
        try:
            widget.delete(1.0, "end")
        except Exception:
            widget.delete(0, "end")


def set_progress(widget, value):
    """Set progress on a progress bar with Qt/Tk support."""
    if hasattr(widget, "setValue"):
        widget.setValue(int(value))
    elif hasattr(widget, "configure"):
        widget.configure(value=value)
