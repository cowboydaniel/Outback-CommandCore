"""Core base classes for DROIDCOM."""

import logging


class BaseModule:
    """Base class that provides a module-specific logger."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__()
