"""Basic tests for NIGHTFIRE."""
import unittest

from NIGHTFIRE.app import config


class ConfigSmokeTests(unittest.TestCase):
    def test_alert_thresholds_are_defined(self) -> None:
        self.assertIn("network_scan", config.ALERT_THRESHOLDS)
        self.assertIn("failed_auth", config.ALERT_THRESHOLDS)

    def test_threat_types_are_defined(self) -> None:
        self.assertGreaterEqual(len(config.THREAT_TYPES), 1)
        self.assertGreaterEqual(len(config.DEMO_THREAT_TYPES), 1)
