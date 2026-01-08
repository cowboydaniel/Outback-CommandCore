"""Core functionality for VANTAGE."""

from .base import HealthCheck, ServiceMetadata
from .utils import utc_now

__all__ = [
    "HealthCheck",
    "ServiceMetadata",
    "utc_now",
]
