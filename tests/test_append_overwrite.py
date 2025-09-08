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


class TestUniqueGrammarSaving(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_birha()
        # Create an instance without running __init__ (avoids Tk requirements)
        cls.inst = object.__new__(cls.mod.GrammarApp)

    def _read_rows(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def test_overwrite_shows_review_and_replaces(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "birha.csv")
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

            # First insert
            res1 = self.inst._append_birha_csv_row(base, path)
            self.assertTrue(res1.get("success"))
            self.assertEqual(res1.get("action"), "append")

            # Overwrite existing (same key); force overwrite choice to simulate modal
            upd = dict(base)
            upd.update({"Darpan Translation": "t2", "Darpan Meaning": "m2", "ChatGPT Commentary": "c2"})
            setattr(self.inst, "_test_overwrite_choice", "overwrite")
            res2 = self.inst._append_birha_csv_row(upd, path)
            self.assertTrue(res2.get("success"))
            self.assertEqual(res2.get("action"), "overwrite")

            rows = self._read_rows(path)
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r.get("Darpan Translation"), "t2")
            self.assertEqual(r.get("Darpan Meaning"), "m2")
            self.assertEqual(r.get("ChatGPT Commentry"), "c2")

    def test_insert_adds_new_row(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "birha.csv")
            base = {
                "\ufeffVowel Ending": "abc",
                "Reference Verse": "verse x",
                "Word Root": "root1",
            }
            res1 = self.inst._append_birha_csv_row(base, path)
            self.assertEqual(res1.get("action"), "append")
            # Different composite key -> new row
            new2 = dict(base)
            new2["Word Root"] = "root2"
            res2 = self.inst._append_birha_csv_row(new2, path)
            self.assertEqual(res2.get("action"), "append")
            self.assertEqual(len(self._read_rows(path)), 2)

    def test_legacy_duplicates_collapse(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "birha.csv")
            headers = [
                "\ufeffVowel Ending", "Number / ???", "Grammar / ??????", "Gender / ????", "Word Root",
                "Type", "Evaluation", "Reference Verse", "Darpan Translation", "Darpan Meaning", "ChatGPT Commentry",
            ]
            row1 = {h: "" for h in headers}
            row2 = {h: "" for h in headers}
            row1.update({"\ufeffVowel Ending": "abc", "Reference Verse": "verse x", "Word Root": "root1", "Darpan Translation": "t1"})
            row2.update({"\ufeffVowel Ending": "abc", "Reference Verse": "verse x", "Word Root": "root1", "Darpan Translation": "t1-dup"})
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write("\ufeff")
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerow(row1)
                w.writerow(row2)

            # Now overwrite with new values; expect single row remaining
            upd = {"\ufeffVowel Ending": "abc", "Reference Verse": "verse x", "Word Root": "root1", "Darpan Translation": "t-new"}
            setattr(self.inst, "_test_overwrite_choice", "overwrite")
            res = self.inst._append_birha_csv_row(upd, path)
            self.assertTrue(res.get("success"))
            rows = self._read_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("Darpan Translation"), "t-new")

    def test_fallback_key_when_root_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "birha.csv")
            base = {
                "\ufeffVowel Ending": "clicked-token",
                "Reference Verse": "verse x",
                "Word Root": "",
                "Darpan Translation": "t1",
            }
            res1 = self.inst._append_birha_csv_row(base, path)
            self.assertTrue(res1.get("success"))
            # Overwrite using fallback key (same verse + selected word)
            upd = dict(base)
            upd["Darpan Translation"] = "t2"
            setattr(self.inst, "_test_overwrite_choice", "overwrite")
            res2 = self.inst._append_birha_csv_row(upd, path)
            self.assertTrue(res2.get("success"))
            rows = self._read_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("Darpan Translation"), "t2")


if __name__ == "__main__":
    unittest.main()
