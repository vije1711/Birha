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


class TestWordIndexCompatOverwrite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_birha()
        cls.inst = object.__new__(cls.mod.GrammarApp)

    def test_overwrite_legacy_no_word_index_column(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "legacy_no_widx.csv")
            # Write a legacy CSV without 'Word Index' column
            headers = [
                "Vowel Ending", "Number / ???", "Grammar / ??????", "Gender / ????",
                "Word Root", "Type", "Evaluation", "Reference Verse",
                "Darpan Translation", "Darpan Meaning", "ChatGPT Commentry"
            ]
            base = {
                "Vowel Ending": "abc",
                "Number / ???": "Singular",
                "Grammar / ??????": "Nominative",
                "Gender / ????": "Masculine",
                "Word Root": "root1",
                "Type": "Noun",
                "Evaluation": "Derived",
                "Reference Verse": "verse x",
                "Darpan Translation": "t1",
                "Darpan Meaning": "m1",
                "ChatGPT Commentry": "c1",
            }
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerow(base)

            # Overwrite with Word Index present in entry
            upd = dict(base)
            upd.update({
                "Darpan Meaning": "m2",
                "ChatGPT Commentary": "c2",
                "Word Index": 5,
            })
            saved, row_no, mode = self.inst._append_birha_csv_row(upd, path)
            self.assertTrue(saved)
            self.assertEqual(mode, 'overwrite')
            self.assertEqual(row_no, 1)

            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r.get("Darpan Meaning"), "m2")
            self.assertEqual(r.get("ChatGPT Commentry"), "c2")
            # Header should now include Word Index (blank is acceptable, but we prefer populated)
            self.assertIn("Word Index", rows[0].keys())
            self.assertEqual(str(r.get("Word Index", "")).strip(), "5")

    def test_overwrite_when_existing_word_index_blank(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "blank_widx.csv")
            headers = [
                "Vowel Ending", "Reference Verse", "Word Index", "Darpan Meaning", "ChatGPT Commentry"
            ]
            base = {
                "Vowel Ending": "abc",
                "Reference Verse": "verse x",
                "Word Index": "",
                "Darpan Meaning": "m1",
                "ChatGPT Commentry": "c1",
            }
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader(); w.writerow(base)

            upd = dict(base)
            upd.update({"Darpan Meaning": "m2", "ChatGPT Commentary": "c2", "Word Index": 7})
            saved, row_no, mode = self.inst._append_birha_csv_row(upd, path)
            self.assertTrue(saved)
            self.assertEqual(mode, 'overwrite')
            self.assertEqual(row_no, 1)

            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("Darpan Meaning"), "m2")
            self.assertEqual(rows[0].get("ChatGPT Commentry"), "c2")
            self.assertEqual(str(rows[0].get("Word Index") or "").strip(), "7")

    def test_overwrite_and_append_with_populated_word_index(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "populated_widx.csv")
            headers = [
                "Vowel Ending", "Reference Verse", "Word Index", "Darpan Meaning", "ChatGPT Commentry"
            ]
            base = {
                "Vowel Ending": "abc",
                "Reference Verse": "verse x",
                "Word Index": 0,
                "Darpan Meaning": "m1",
                "ChatGPT Commentry": "c1",
            }
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader(); w.writerow(base)

            # Overwrite same index
            upd_same = dict(base)
            upd_same.update({"Darpan Meaning": "m2", "ChatGPT Commentary": "c2"})
            saved, row_no, mode = self.inst._append_birha_csv_row(upd_same, path)
            self.assertTrue(saved); self.assertEqual(mode, 'overwrite'); self.assertEqual(row_no, 1)

            # Append with a new index
            upd_new = dict(base)
            upd_new.update({"Word Index": 1, "Darpan Meaning": "m3", "ChatGPT Commentary": "c3"})
            saved, row_no, mode = self.inst._append_birha_csv_row(upd_new, path)
            self.assertTrue(saved); self.assertEqual(mode, 'append'); self.assertEqual(row_no, 2)

            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            vals = sorted((r.get("Word Index"), r.get("Darpan Meaning")) for r in rows)
            self.assertEqual(vals, [("0", "m2"), ("1", "m3")])


if __name__ == "__main__":
    unittest.main()

