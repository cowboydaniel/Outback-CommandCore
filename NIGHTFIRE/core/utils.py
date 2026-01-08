"""Utility helpers for NIGHTFIRE core services."""
import logging

from NIGHTFIRE.app import config


def setup_logging() -> logging.Logger:
    """Configure logging for the NIGHTFIRE system."""
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
    )
    return logging.getLogger(config.APP_NAME)
