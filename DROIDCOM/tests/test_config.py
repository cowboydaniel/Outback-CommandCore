"""Basic tests for DROIDCOM configuration."""

import unittest

from DROIDCOM.app import config


class TestConfig(unittest.TestCase):
    def test_platform_flag_is_boolean(self):
        self.assertIsInstance(config.IS_WINDOWS, bool)

    def test_default_ports_and_timeouts(self):
        self.assertGreater(config.DEFAULT_ADB_PORT, 0)
        self.assertGreater(config.DEFAULT_ADB_TIMEOUT, 0)

    def test_version_is_non_empty(self):
        self.assertTrue(config.APP_VERSION)


if __name__ == "__main__":
    unittest.main()
