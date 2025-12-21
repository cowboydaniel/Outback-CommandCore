"""
Compatibility layer for the Tkinter-to-PySide6 migration.

Tkinter imports have been removed from DROIDCOM. This module provides
lightweight placeholders so existing modules can be imported while the
UI is refactored to PySide6.
"""

from __future__ import annotations

from types import SimpleNamespace

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError as exc:  # pragma: no cover - dependency is required at runtime
    raise ImportError(
        "PySide6 is required to use the DROIDCOM UI. Please install PySide6."
    ) from exc


class TkCompatError(RuntimeError):
    """Raised when legacy Tkinter-only widgets are requested."""


class _UnsupportedWidget:
    def __init__(self, *args, **kwargs):
        raise TkCompatError(
            "Tkinter widgets are no longer available. "
            "Use the PySide6 UI implementation instead."
        )


class _Var:
    def __init__(self, value=None):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class _CompatNamespace(SimpleNamespace):
    def __getattr__(self, name):
        return _UnsupportedWidget


class _CompatModule:
    def __getattr__(self, name):
        def _unsupported(*args, **kwargs):
            raise TkCompatError(
                "Tkinter dialog helpers are no longer available. "
                "Use the PySide6 UI implementation instead."
            )

        return _unsupported


tk = _CompatNamespace(
    END="end",
    StringVar=_Var,
    BooleanVar=_Var,
    IntVar=_Var,
    DoubleVar=_Var,
)

ttk = _CompatNamespace()
messagebox = _CompatModule()
filedialog = _CompatModule()
scrolledtext = _CompatModule()

__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "TkCompatError",
    "filedialog",
    "messagebox",
    "scrolledtext",
    "tk",
    "ttk",
]
