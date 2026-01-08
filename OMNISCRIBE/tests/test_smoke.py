"""Stub tests for OMNISCRIBE."""
import unittest

from OMNISCRIBE.core.base import Omniscribe, ScriptLanguage


class OmniscribeSmokeTests(unittest.TestCase):
    def test_create_and_run_script(self) -> None:
        omni = Omniscribe()
        omni.create_script(
            name="hello",
            language=ScriptLanguage.PYTHON,
            code="print('hi')",
            description="sample",
        )
        result = omni.run_script("hello", {})
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
