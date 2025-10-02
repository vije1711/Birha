import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "1.1.0_birha.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("birha_module_bom", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_module()
GrammarApp = BIRHA.GrammarApp


class VowelBomHandlingTest(unittest.TestCase):
    def test_derived_suggestions_strip_bom(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "derived.csv"

            data = pd.DataFrame(
                [
                    {
                        "\ufeffVowel Ending": "ਕਾ",
                        "Evaluation": "Derived",
                        "Number / ਵਚਨ": "Singular",
                        "Gender / ਲਿੰਗ": "Masculine",
                        "Type": "Noun",
                    }
                ]
                * 3
            )
            data.to_csv(csv_path, index=False, encoding="utf-8")

            app = GrammarApp.__new__(GrammarApp)
            app._derived_cache_path = str(csv_path)
            app._derived_cache = None
            app._derived_cache_mtime = None

            result = app.get_derived_suggestions_by_vowel_ending("ਕਾ")

            self.assertIn("Type", result)
            self.assertIsNotNone(result["Type"])
            self.assertEqual(result["Type"][0], "Noun")
            self.assertIn("Vowel Ending", app._derived_cache.columns)
            self.assertNotIn("\ufeffVowel Ending", app._derived_cache.columns)


if __name__ == "__main__":
    unittest.main()
