import sys
from pathlib import Path

import pytest


@pytest.mark.skip(reason="Entry point smoke test placeholder; UI dependencies not loaded in CI.")
def test_main_entry_point_exists():
    base_dir = Path(__file__).resolve().parents[1]
    main_path = base_dir / "app" / "main.py"
    assert main_path.exists()
