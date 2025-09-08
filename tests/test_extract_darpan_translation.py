import unittest
import importlib.util
from pathlib import Path


def _load_birha():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("birha_mod", str(root / "1.1.0_birha.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestExtractDarpanTranslation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_birha()

    def test_only_arth_present(self):
        text = (
            "Arth:\n"
            "This   is\tArth text.\n\n"
            "More  lines here.\n"
        )
        out = self.mod.extract_darpan_translation(text)
        # Excessive spaces/tabs collapsed, line breaks preserved
        self.assertEqual(out, "This is Arth text.\n\nMore lines here.")

    def test_arth_and_chhand_present(self):
        text = (
            "Arth:\nArth first.\n\n"
            "Chhand:\nChhand content.\n"
        )
        out = self.mod.extract_darpan_translation(text)
        self.assertEqual(out, "Arth first.\n\nChhand content.")

    def test_arth_and_bhav_present(self):
        text = (
            "Arth:\nArth text\n"
            "Bhav:\nBhav text\n"
        )
        out = self.mod.extract_darpan_translation(text)
        self.assertEqual(out, "Arth text\n\nBhav text")

    def test_all_three_reordered_output(self):
        text = (
            "Verse:\nSome verse\n"
            "Padarth:\nSome padarth\n"
            "Bhav:\nB1 line\n"
            "Arth:\nA1 line\n"
            "Chhand:\nC1 line\n"
        )
        out = self.mod.extract_darpan_translation(text)
        # Output must be Arth + Chhand + Bhav order
        self.assertEqual(out, "A1 line\n\nC1 line\n\nB1 line")

    def test_missing_all_three_fallback(self):
        original = "Manual translation without labels.\nLine two."
        out = self.mod.extract_darpan_translation(original)
        # Should return original unchanged to avoid data loss
        self.assertEqual(out, original)


if __name__ == "__main__":
    unittest.main()

