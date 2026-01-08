"""Tests for the dashboard tab module."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def _ensure_commandcore_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_dashboard_tab_module_exports_tab() -> None:
    pytest.importorskip("PySide6")
    _ensure_commandcore_on_path()

    module = importlib.import_module("tabs.dashboard_tab")

    assert hasattr(module, "DashboardTab")
    assert hasattr(module.DashboardTab, "request_tab_change")
