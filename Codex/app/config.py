"""Configuration for CommandCoreCodex."""

from dataclasses import dataclass

from Codex.core.base import BaseConfig


@dataclass(frozen=True)
class AppConfig(BaseConfig):
    """Configuration values for the GUI application."""

    window_title: str = "CommandCoreCodex AI Pipeline Control Center"
    min_width: int = 1000
    min_height: int = 700


DEFAULT_CONFIG = AppConfig(name="CommandCoreCodex", version="1.0.0")
