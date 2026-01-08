import importlib
import unittest


class TestAppImports(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import PySide6  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest("PySide6 is required for GUI imports") from exc

    def test_main_module_loads(self) -> None:
        module = importlib.import_module("Codex.app.main")
        self.assertTrue(callable(module.main))
        self.assertTrue(callable(module.create_app))

    def test_tab_builders_load(self) -> None:
        tabs = importlib.import_module("Codex.tabs")
        expected = [
            "setup_data_prep_tab",
            "setup_generation_tab",
            "setup_logs_tab",
            "setup_training_tab",
            "setup_validation_tab",
        ]
        for name in expected:
            self.assertTrue(callable(getattr(tabs, name)))


if __name__ == "__main__":
    unittest.main()
