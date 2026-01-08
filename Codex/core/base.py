"""Shared base classes for CommandCoreCodex."""

from dataclasses import dataclass


@dataclass
class BaseConfig:
    """Base configuration data for application components."""

    name: str
    version: str
