import pytest


pytest.importorskip("PySide6")


def test_launcher_import():
    from BLACKSTORM.app import main

    assert hasattr(main, "BlackStormLauncher")
