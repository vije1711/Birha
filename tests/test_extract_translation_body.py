import unittest
import importlib.util
import pathlib


# Dynamically import the main module file
ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "1.1.0_birha.py"
spec = importlib.util.spec_from_file_location("birha_mod", str(MOD_PATH))
birha_mod = importlib.util.module_from_spec(spec)  # type: ignore
assert spec and spec.loader
spec.loader.exec_module(birha_mod)  # type: ignore
extract = birha_mod.extract_translation_body


class TestExtractTranslationBody(unittest.TestCase):
    def test_only_arth(self):
        text = "Arth:\nLine A1\nLine A2\n"
        self.assertEqual(extract(text), "Line A1\nLine A2")

    def test_arth_chhand(self):
        text = (
            "Arth:\nA line\n\n"
            "Chhand:\nC line\n"
        )
        self.assertEqual(extract(text), "A line\n\nC line")

    def test_arth_bhav(self):
        text = (
            "Arth:\nA1\n\nA2\n\n\n"
            "Bhav:\nB1\n"
        )
        self.assertEqual(extract(text), "A1\n\nA2\n\nB1")

    def test_all_three(self):
        text = (
            "Verse:\nignored\n\n"
            "Padarth:\nignored too\n\n"
            "Arth:\nAA\n\n"
            "Chhand:\nCC\n\n"
            "Bhav:\nBB\n"
        )
        self.assertEqual(extract(text), "AA\n\nCC\n\nBB")

    def test_missing_all(self):
        text = "Verse:\nV\n\nPadarth:\nP\n"
        self.assertEqual(extract(text), "")


if __name__ == "__main__":
    unittest.main()

