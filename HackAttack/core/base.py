"""Base types shared across HackAttack modules."""

from dataclasses import dataclass
from typing import Callable

try:
    from PySide6.QtWidgets import QWidget
except Exception:  # pragma: no cover - optional GUI dependency
    QWidget = object


@dataclass(frozen=True)
class TabDefinition:
    """Definition for a GUI tab."""

    title: str
    description: str
    icon: str
    builder: Callable[[str, str, str], "QWidget"]
