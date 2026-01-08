"""
DROIDCOM - Android Device Management Tool
A comprehensive tool for managing Android devices via ADB.
"""

from .app import AndroidToolsModule
from .dependencies import check_and_install_android_dependencies
from .app.config import IS_WINDOWS

__all__ = [
    'AndroidToolsModule',
    'check_and_install_android_dependencies',
    'IS_WINDOWS'
]

__version__ = '1.0.0'
