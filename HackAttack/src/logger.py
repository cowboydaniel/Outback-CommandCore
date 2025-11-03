"""
Logging configuration for Hack Attack.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from .config import config

class Logger:
    """Centralized logging configuration."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._logger = logging.getLogger('hack_attack')
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging with both file and console handlers."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Get log level from config
        log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
        self._logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler
        log_file = config.get('logging.file', 'hack_attack.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # Set log level for all handlers
        for handler in self._logger.handlers:
            handler.setLevel(log_level)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance with the given name."""
        if name:
            return self._logger.getChild(name)
        return self._logger

# Initialize logger
logger = Logger().get_logger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the given name."""
    return Logger().get_logger(name)
