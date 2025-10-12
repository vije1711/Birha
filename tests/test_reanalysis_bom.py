import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "1.1.0_birha.py"


def _load():
    spec = importlib.util.spec_from_file_location("birha_module_reanalysis", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load()
GrammarApp = BIRHA.GrammarApp


class ReanalysisBomTest(unittest.TestCase):
    def test_normalize_field_strips_bom(self):
        app = GrammarApp.__new__(GrammarApp)
        result = app._normalize_reanalysis_field_key("\ufeffWord")
        self.assertEqual(result, "Word")

    def test_normalize_field_handles_non_string(self):
        app = GrammarApp.__new__(GrammarApp)
        self.assertIsNone(app._normalize_reanalysis_field_key(None))


if __name__ == "__main__":
    unittest.main()
    def test_safe_equal_strips_bom(self):
        app = GrammarApp.__new__(GrammarApp)
        self.assertTrue(app.safe_equal_matches_reanalysis("\ufeffਕਾ", "ਕਾ"))
