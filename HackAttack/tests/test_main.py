"""Stub tests for the GUI entry point."""

import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "PySide6 not installed")
class TestMain(unittest.TestCase):
    def test_entrypoint_exists(self):
        from HackAttack.app import main as app_main

        self.assertTrue(callable(app_main.main))
