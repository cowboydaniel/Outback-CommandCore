"""Base classes for VANTAGE core modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class HealthCheck(Protocol):
    """Protocol for health check providers."""

    def health_status(self) -> str:
        """Return a short health status string."""


@dataclass(frozen=True)
class ServiceMetadata:
    """Shared metadata for core services."""

    name: str
    version: str = "0.1.0"
