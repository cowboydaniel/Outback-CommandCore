"""Application entrypoints and configuration for DROIDCOM."""

from .config import APP_VERSION, IS_WINDOWS
from .module import AndroidToolsModule

__all__ = ["AndroidToolsModule", "APP_VERSION", "IS_WINDOWS"]
