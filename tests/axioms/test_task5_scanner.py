import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t5", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
scan_for_axiom_work = BIRHA.scan_for_axiom_work
AxiomContribStore = BIRHA.AxiomContribStore
AxiomWorkqueueStore = BIRHA.AxiomWorkqueueStore
_normalize_verse_key = BIRHA._normalize_verse_key


class AxiomReanalysisScannerTest(unittest.TestCase):
    @staticmethod
    def _write_assessment_excel(path: Path, rows: List[dict]) -> None:
        df = pd.DataFrame(rows)
        df.to_excel(path, index=False)

    def test_framework_without_contribution_creates_pending_queue(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            assessment_path = tmp_path / "1.2.1 assessment_data.xlsx"
            store_path = tmp_path / "1.3.0_axioms.xlsx"

            self._write_assessment_excel(
                assessment_path,
                [
                    {
                        "Verse": "Framework Verse",
                        "Translation Revision": 1,
                        "Framework?": True,
                        "Explicit?": False,
                    },
                ],
            )

            results = scan_for_axiom_work(
                assessment_path=assessment_path,
                store_path=store_path,
            )

            self.assertEqual(len(results), 1)
            item = results[0]
            self.assertEqual(item.status, "pending")
            self.assertEqual(item.seen_translation_revision, 0)
            self.assertTrue(item.is_framework)
            self.assertFalse(item.parents)
            self.assertFalse(item.supporting)

            queue_records = AxiomWorkqueueStore(store_path=store_path).list_queue()
            self.assertEqual(len(queue_records), 1)
            self.assertEqual(queue_records[0]["status"], "pending")

    def test_translation_revision_advances_marks_reanalysis(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            assessment_path = tmp_path / "1.2.1 assessment_data.xlsx"
            store_path = tmp_path / "1.3.0_axioms.xlsx"

            verse_text = "Reanalysis Verse"
            verse_key = _normalize_verse_key(verse_text)

            self._write_assessment_excel(
                assessment_path,
                [
                    {
                        "Verse": verse_text,
                        "Translation Revision": 2,
                        "Framework?": True,
                        "Explicit?": True,
                    },
                ],
            )

            contrib_store = AxiomContribStore(store_path=store_path)
            contrib_store.link_contribution(
                axiom_id="AX-001",
                verse_key=verse_key,
                category="Primary",
                translation_revision_seen=1,
            )

            AxiomWorkqueueStore(store_path=store_path).enqueue_or_update(
                verse_key=verse_key,
                status="done",
                translation_revision_seen=1,
            )

            results = scan_for_axiom_work(
                assessment_path=assessment_path,
                store_path=store_path,
            )

            self.assertTrue(any(item.verse_key == verse_key for item in results))
            record = next(item for item in results if item.verse_key == verse_key)
            self.assertEqual(record.status, "reanalysis_required")
            self.assertEqual(record.seen_translation_revision, 1)
            self.assertEqual(record.current_translation_revision, 2)
            self.assertTrue(record.is_explicit)

            queue_records = {
                entry["verse_key"]: entry for entry in AxiomWorkqueueStore(store_path=store_path).list_queue()
            }
            self.assertEqual(queue_records[verse_key]["status"], "reanalysis_required")

    def test_supporting_revision_enqueues_parent(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            assessment_path = tmp_path / "1.2.1 assessment_data.xlsx"
            store_path = tmp_path / "1.3.0_axioms.xlsx"

            primary_text = "Primary Verse"
            supporting_text = "Supporting Verse"
            primary_key = _normalize_verse_key(primary_text)
            supporting_key = _normalize_verse_key(supporting_text)

            self._write_assessment_excel(
                assessment_path,
                [
                    {
                        "Verse": primary_text,
                        "Translation Revision": 1,
                        "Framework?": True,
                        "Explicit?": False,
                    },
                    {
                        "Verse": supporting_text,
                        "Translation Revision": 2,
                        "Framework?": True,
                        "Explicit?": False,
                    },
                ],
            )

            contrib_store = AxiomContribStore(store_path=store_path)
            contrib_store.link_contribution(
                axiom_id="AX-002",
                verse_key=primary_key,
                category="Primary",
                translation_revision_seen=1,
            )
            contrib_store.link_contribution(
                axiom_id="AX-002",
                verse_key=supporting_key,
                category="Secondary",
                translation_revision_seen=1,
            )

            results = scan_for_axiom_work(
                assessment_path=assessment_path,
                store_path=store_path,
            )

            result_map = {item.verse_key: item for item in results}
            self.assertIn(supporting_key, result_map)
            self.assertIn(primary_key, result_map)

            supporting_item = result_map[supporting_key]
            self.assertEqual(supporting_item.status, "reanalysis_required")
            self.assertIn(primary_key, supporting_item.parents)

            primary_item = result_map[primary_key]
            self.assertEqual(primary_item.status, "reanalysis_required")
            self.assertTrue(primary_item.triggered_by_supporting)
            self.assertIn(supporting_key, primary_item.supporting)

            queue_entries = {
                entry["verse_key"]: entry for entry in AxiomWorkqueueStore(store_path=store_path).list_queue()
            }
            self.assertEqual(queue_entries[supporting_key]["status"], "reanalysis_required")
            self.assertEqual(queue_entries[primary_key]["status"], "reanalysis_required")


if __name__ == "__main__":
    unittest.main()
