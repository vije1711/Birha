import os
import unittest
import importlib.util
from pathlib import Path


def _load_birha_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "1.1.0_birha.py"
    spec = importlib.util.spec_from_file_location("birha_mod", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestExtractDarpanTranslation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_birha_module()

    def test_a_only_arth_present(self):
        text = (
            "Verse:\nLine 1\n\n"
            "Padarth:\nPad line\n\n"
            "Arth:\nThis is the Arth line one.\nLine two of Arth.\n"
        )
        out = self.mod.extract_darpan_translation_from_labeled_text(text)
        self.assertEqual(out, "This is the Arth line one.\nLine two of Arth.")

    def test_b_arth_and_chhand(self):
        text = (
            "Verse:\nV1\n\n"
            "Padarth:\nP1\n\n"
            "Arth: First line in same label\nSecond Arth line\n\n"
            "Chhand:\nChhand explanation here.\n"
        )
        out = self.mod.extract_darpan_translation_from_labeled_text(text)
        self.assertEqual(out, "First line in same label\nSecond Arth line\n\nChhand explanation here.")

    def test_c_arth_and_bhav(self):
        text = (
            "Verse:\nV\n"
            "Padarth:\nP\n"
            "Arth:\nArth A\n\n"
            "Bhav:  Bhav starts same line  \t with  extra spaces\nNext bhav line\n"
        )
        out = self.mod.extract_darpan_translation_from_labeled_text(text)
        self.assertEqual(out, "Arth A\n\nBhav starts same line with extra spaces\nNext bhav line")

    def test_d_all_three(self):
        text = (
            "Verse:\nV\n"
            "Padarth:\nP\n"
            "Arth:\nA1\n\nA2\n\n\n"
            "Chhand:\nC1\n\n"
            "Bhav:\nB1\nB2\n"
        )
        out = self.mod.extract_darpan_translation_from_labeled_text(text)
        self.assertEqual(out, "A1\n\nA2\n\nC1\n\nB1\nB2")

    def test_e_missing_all_three(self):
        text = (
            "Verse:\nOnly verse\n\n"
            "Padarth:\nOnly padarth\n"
        )
        out = self.mod.extract_darpan_translation_from_labeled_text(text)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
