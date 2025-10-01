import importlib.util
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import tkinter as tk


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"
HEADLESS_DISPLAY = os.name != "nt" and "DISPLAY" not in os.environ


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t4", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
AxiomDriverSession = BIRHA.AxiomDriverSession
AxiomDriverWindow = BIRHA.AxiomDriverWindow
start_axiom_driver_for = BIRHA.start_axiom_driver_for
AxiomWorkqueueStore = BIRHA.AxiomWorkqueueStore


class AxiomDriverSessionTest(unittest.TestCase):
    def test_queue_created_and_resumed_correctly(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["verse-001", "verse-002"], store_path=store_path)
            self.assertFalse(session.is_empty)
            self.assertIsNotNone(session.current_item)
            self.assertEqual(session.current_item.verse_key, "verse-001")
            session.pause()

            resumed = AxiomDriverSession(["verse-001", "verse-002"], store_path=store_path)
            self.assertIsNotNone(resumed.current_item)
            self.assertEqual(resumed.current_item.verse_key, "verse-001")
            self.assertEqual(resumed.current_item.status, "in_progress")
            self.assertIsNotNone(resumed.current_item.analysis_started_at)

    def test_pause_and_resume_updates_status(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["verse-010"], store_path=store_path)
            session.pause()
            store = AxiomWorkqueueStore(store_path=store_path)
            records = store.list_queue()
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["status"], "in_progress")
            self.assertIsNotNone(record["analysis_started_at"])

    def test_next_and_prev_navigation(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["v-1", "v-2", "v-3"], store_path=store_path)
            session.advance()
            first = session.store.list_queue()[0]
            self.assertEqual(first["status"], "done")
            current = session.current_item
            self.assertIsNotNone(current)
            self.assertEqual(current.verse_key, "v-2")

            session.go_back()
            back = session.current_item
            self.assertIsNotNone(back)
            self.assertEqual(back.verse_key, "v-1")
            queue_data = session.store.list_queue()
            self.assertEqual(queue_data[1]["status"], "pending")

            session.advance()
            replay = session.store.list_queue()[0]
            self.assertEqual(replay["status"], "done")
            self.assertIsNotNone(replay.get("reanalysis_started_at"))

    def test_resume_after_restart(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["verse-a", "verse-b", "verse-c"], store_path=store_path)
            session.advance()
            session.pause()

            resumed = AxiomDriverSession([], store_path=store_path)
            self.assertIsNotNone(resumed.current_item)
            self.assertEqual(resumed.current_item.verse_key, "verse-b")
            resumed.advance()
            next_item = resumed.current_item
            self.assertIsNotNone(next_item)
            self.assertEqual(next_item.verse_key, "verse-c")

    def test_reseeding_preserves_completed_history(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["verse-x", "verse-y"], store_path=store_path)
            while session.current_item is not None:
                session.advance()

            records_before = session.store.list_queue()
            self.assertTrue(records_before)
            self.assertTrue(all(record["status"] == "done" for record in records_before))
            snapshot = {
                record["verse_key"]: (record["status"], record.get("analysis_completed_at"))
                for record in records_before
            }

            reseeded = AxiomDriverSession(["verse-x", "verse-y"], store_path=store_path)
            self.assertTrue(reseeded.is_complete)
            self.assertIsNone(reseeded.current_item)

            records_after = reseeded.store.list_queue()
            self.assertEqual(len(records_after), len(records_before))
            for record in records_after:
                status, completed_at = snapshot[record["verse_key"]]
                self.assertEqual(record["status"], status)
                self.assertEqual(record.get("analysis_completed_at"), completed_at)


class AxiomDriverWindowTest(unittest.TestCase):
    @unittest.skipIf(HEADLESS_DISPLAY, "no display available")
    def test_window_smoke(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            session = AxiomDriverSession(["verse-window"], store_path=store_path)
            root = tk.Tk()
            root.withdraw()
            try:
                window = AxiomDriverWindow(root, session)
                root.update_idletasks()
                window.destroy()
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
