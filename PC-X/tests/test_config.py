import sys
import unittest
from pathlib import Path

PCX_DIR = Path(__file__).resolve().parents[1]
if str(PCX_DIR) not in sys.path:
    sys.path.insert(0, str(PCX_DIR))

from app import config
from core import base


class TestConfig(unittest.TestCase):
    def test_color_palette_has_core_keys(self):
        for key in ["primary", "secondary", "background", "border"]:
            self.assertIn(key, config.COLOR_PALETTE)

    def test_cache_config_defaults(self):
        self.assertTrue(config.CACHE_CONFIG["enabled"])
        self.assertIn("ttl", config.CACHE_CONFIG)

    def test_required_tools_defined(self):
        self.assertIn("debian", config.REQUIRED_TOOLS)
        self.assertIn("redhat", config.REQUIRED_TOOLS)

    def test_paths_resolve(self):
        root_dir, pcx_dir = base.get_paths()
        self.assertTrue(root_dir.exists())
        self.assertTrue((pcx_dir / "app").exists())


if __name__ == "__main__":
    unittest.main()
