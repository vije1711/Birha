import importlib.util
import os
import unittest
from datetime import datetime, timedelta
from unittest import mock

import pandas as pd


class ReanalysisSupersededTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        module_path = os.path.join(repo_root, "1.1.0_birha.py")
        spec = importlib.util.spec_from_file_location("birha_app", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.mod = module

    def test_reanalysis_finalization_preserves_superseded_history(self):
        mod = self.mod
        verse_text = "Sample verse text"
        word_norm = "testnorm"
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        old_created = base_time
        new_created = base_time + timedelta(days=1)
        old_superseded = base_time + timedelta(hours=1)
        queued_superseded = base_time + timedelta(days=2)

        progress_df = pd.DataFrame(
            [
                {
                    "word": "Test",
                    "word_key_norm": word_norm,
                    "word_index": 1,
                    "verse": verse_text,
                    "page_number": None,
                    "selected_for_analysis": True,
                    "selected_at": old_created,
                    "status": "completed",
                    "completed_at": old_created,
                    "reanalyzed_count": 1,
                    "last_reanalyzed_at": old_created,
                    "created_at": old_created,
                    "removed_at": None,
                    "archived_at": None,
                    "superseded_at": old_superseded,
                    "verse_key_norm": mod._normalize_verse_key(verse_text),
                },
                {
                    "word": "Test",
                    "word_key_norm": word_norm,
                    "word_index": 1,
                    "verse": verse_text,
                    "page_number": None,
                    "selected_for_analysis": True,
                    "selected_at": new_created,
                    "status": "reanalysis_queued",
                    "completed_at": None,
                    "reanalyzed_count": 1,
                    "last_reanalyzed_at": old_created,
                    "created_at": new_created,
                    "removed_at": None,
                    "archived_at": None,
                    "superseded_at": queued_superseded,
                    "verse_key_norm": mod._normalize_verse_key(verse_text),
                },
            ],
            index=[101, 202],
        )

        queue_record = progress_df.loc[202].to_dict()
        queue_record[mod._TRACKER_QUEUE_INDEX_KEY] = 202

        app = mod.GrammarApp.__new__(mod.GrammarApp)
        app._word_driver_queue = [queue_record]
        app._word_driver_index = 0
        app._word_driver_current_verse = verse_text
        app._word_driver_current_record = queue_record
        app._word_driver_norm = word_norm
        app._word_driver_paused = False
        app._word_driver_in_progress = True
        app._word_driver_update_ui = lambda: None
        app._word_driver_open_current_verse = lambda: None
        app._word_driver_complete_word_if_done = lambda: None
        app._get_word_tracker_path = lambda: "tracker.xlsx"

        words_df = pd.DataFrame(columns=mod._WORDS_COLUMNS)
        others = []

        saved_progress = {}

        def fake_save(path, words_out, progress_out, others_out, *args, **kwargs):
            saved_progress["df"] = progress_out.copy()

        with mock.patch.object(mod, "load_word_tracker", return_value=(words_df.copy(), progress_df.copy(), others)):
            with mock.patch.object(mod, "_save_tracker", side_effect=fake_save):
                app._word_driver_after_verse_finished()

        self.assertIn("df", saved_progress, "Expected progress data to be saved")
        result_df = saved_progress["df"]
        before_superseded = progress_df["superseded_at"].notna().sum()
        after_superseded = result_df["superseded_at"].notna().sum()
        self.assertEqual(result_df.loc[101, "superseded_at"], old_superseded)
        self.assertTrue(pd.isna(result_df.loc[202, "superseded_at"]))
        self.assertEqual(mod._normalize_progress_status(result_df.loc[202, "status"]), "completed")
        self.assertEqual(mod._normalize_progress_status(result_df.loc[101, "status"]), "completed")
        self.assertIsNone(getattr(app, "_word_driver_current_record", None))
        self.assertEqual(result_df.loc[202, "reanalyzed_count"], 2)
        self.assertEqual(after_superseded, before_superseded - 1)


if __name__ == "__main__":
    unittest.main()
