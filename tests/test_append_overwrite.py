import csv
import os
import unittest
import importlib.util
from pathlib import Path
import tempfile


def _load_birha():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("birha_mod", str(root / "1.1.0_birha.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAppendOrOverwrite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_birha()
        # Create an instance without running __init__ (avoids Tk requirements)
        cls.inst = object.__new__(cls.mod.GrammarApp)

    def test_overwrite_then_append(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test_birha.csv")

            base = {
                "\ufeffVowel Ending": "abc",
                "Number / ???": "Singular",
                "Grammar / ??????": "Nominative",
                "Gender / ????": "Masculine",
                "Word Root": "root1",
                "Type": "Noun",
                "Evaluation": "Derived",
                "Reference Verse": "verse x",
                "Darpan Translation": "t1",
                "Darpan Meaning": "m1",
                "ChatGPT Commentary": "c1",
            }

            # First write (creates file)
            self.inst._append_birha_csv_row(base, path)

            # Overwrite with same keys but different non-key values
            upd = dict(base)
            upd.update({
                "Darpan Translation": "t2",
                "Darpan Meaning": "m2",
                "ChatGPT Commentary": "c2",
            })
            self.inst._append_birha_csv_row(upd, path)

            # Read back and assert one data row with updated values
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r.get("Darpan Translation"), "t2")
            self.assertEqual(r.get("Darpan Meaning"), "m2")
            self.assertEqual(r.get("ChatGPT Commentry"), "c2")

            # Append with different key (change Vowel Ending)
            new2 = dict(base)
            new2["\ufeffVowel Ending"] = "abc2"
            new2["Word Root"] = "root2"
            self.inst._append_birha_csv_row(new2, path)

            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            # Ensure both roots present
            roots = sorted([row.get("Word Root") for row in rows])
            self.assertEqual(roots, ["root1", "root2"])


if __name__ == "__main__":
    unittest.main()
