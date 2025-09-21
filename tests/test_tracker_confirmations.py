import importlib.util
import os
import unittest
from datetime import datetime
from unittest import mock

import pandas as pd


class TrackerConfirmationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        module_path = os.path.join(repo_root, "1.1.0_birha.py")
        spec = importlib.util.spec_from_file_location("birha_app", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.mod = module

    def setUp(self):
        self.mod = self.__class__.mod
        self.words_df = pd.DataFrame(columns=self.mod._WORDS_COLUMNS)
        self.others = []

    def _mock_tracker(self, progress_df):
        return mock.patch.object(
            self.mod,
            "load_word_tracker",
            return_value=(self.words_df.copy(), progress_df.copy(), list(self.others)),
        )

    def test_remove_pending_cancel_does_not_save(self):
        mod = self.mod
        records = [
            {"row_index": 10, "verse_snippet": "Verse A", "page": "1", "status": "pending"},
            {"row_index": 20, "verse_snippet": "Verse B", "page": "2", "status": "pending"},
        ]
        progress_df = pd.DataFrame(
            [
                {
                    "word": "Test",
                    "status": "pending",
                    "selected_for_analysis": True,
                    "removed_at": None,
                },
                {
                    "word": "Test",
                    "status": "pending",
                    "selected_for_analysis": True,
                    "removed_at": None,
                },
            ],
            index=[10, 20],
        )

        with self._mock_tracker(progress_df), \
            mock.patch.object(mod, "_save_tracker") as save_mock, \
            mock.patch.object(mod.messagebox, "askokcancel", return_value=False) as ask_mock, \
            mock.patch.object(mod.messagebox, "showinfo") as info_mock, \
            mock.patch.object(mod, "_TRACKER_LOGGER", mock.Mock()) as log_mock:

            updated, processed = mod._confirm_remove_pending_records("tracker.xlsx", records)

        self.assertFalse(updated)
        self.assertEqual(processed, [])
        save_mock.assert_not_called()
        info_mock.assert_not_called()
        ask_mock.assert_called_once()
        self.assertEqual(ask_mock.call_args.kwargs.get("default"), "cancel")
        log_mock.info.assert_called_once_with("%s cancelled for %d %s%s", "Remove", 2, "pending verse", "s")

    def test_remove_pending_confirm_updates_rows(self):
        mod = self.mod
        records = [
            {"row_index": 10, "verse_snippet": "Verse A", "page": "1", "status": "pending"},
            {"row_index": 20, "verse_snippet": "Verse B", "page": "2", "status": "reanalysis_queued"},
            {"row_index": 30, "verse_snippet": "Verse C", "page": "3", "status": "pending"},
        ]
        progress_df = pd.DataFrame(
            [
                {
                    "word": "Test",
                    "status": "pending",
                    "selected_for_analysis": True,
                    "removed_at": None,
                },
                {
                    "word": "Test",
                    "status": "pending",
                    "selected_for_analysis": True,
                    "removed_at": None,
                },
                {
                    "word": "Test",
                    "status": "removed",
                    "selected_for_analysis": True,
                    "removed_at": None,
                },
            ],
            index=[10, 20, 30],
        )

        saved = {}

        def fake_save(path, words_out, progress_out, others_out, *args, **kwargs):
            saved["df"] = progress_out.copy()

        fixed_time = datetime(2024, 1, 2, 3, 4, 5)

        with self._mock_tracker(progress_df), \
            mock.patch.object(mod, "_save_tracker", side_effect=fake_save), \
            mock.patch.object(mod.messagebox, "askokcancel", return_value=True) as ask_mock, \
            mock.patch.object(mod.messagebox, "showinfo") as info_mock, \
            mock.patch.object(mod, "_TRACKER_LOGGER", mock.Mock()) as log_mock:

            updated, processed = mod._confirm_remove_pending_records(
                "tracker.xlsx", records, now_factory=lambda: fixed_time
            )

        self.assertTrue(updated)
        self.assertEqual([rec["row_index"] for rec in processed], [10, 20])
        info_mock.assert_not_called()
        ask_mock.assert_called_once()
        message = ask_mock.call_args.args[1]
        self.assertIn("Remove 2 pending verses?", message)
        self.assertIn("Verse A", message)
        self.assertIn("p. 1", message)
        log_mock.info.assert_called_once_with("%s confirmed for %d %s%s", "Remove", 2, "pending verse", "s")

        self.assertIn("df", saved)
        result_df = saved["df"]
        self.assertEqual(mod._normalize_progress_status(result_df.loc[10, "status"]), "removed")
        self.assertEqual(mod._normalize_progress_status(result_df.loc[20, "status"]), "removed")
        self.assertEqual(mod._normalize_progress_status(result_df.loc[30, "status"]), "removed")
        self.assertFalse(result_df.loc[10, "selected_for_analysis"])
        self.assertFalse(result_df.loc[20, "selected_for_analysis"])
        self.assertTrue(result_df.loc[30, "selected_for_analysis"])
        self.assertEqual(result_df.loc[10, "removed_at"], fixed_time)
        self.assertEqual(result_df.loc[20, "removed_at"], fixed_time)

    def test_archive_completed_cancel(self):
        mod = self.mod
        records = [
            {"row_index": 101, "verse_snippet": "Verse X", "page": "10", "status": "completed"},
            {"row_index": 202, "verse_snippet": "Verse Y", "page": "11", "status": "completed"},
        ]
        progress_df = pd.DataFrame(
            [
                {"word": "Test", "status": "completed", "archived_at": None},
                {"word": "Test", "status": "completed", "archived_at": None},
            ],
            index=[101, 202],
        )

        with self._mock_tracker(progress_df), \
            mock.patch.object(mod, "_save_tracker") as save_mock, \
            mock.patch.object(mod.messagebox, "askokcancel", return_value=False) as ask_mock, \
            mock.patch.object(mod.messagebox, "showinfo") as info_mock, \
            mock.patch.object(mod, "_TRACKER_LOGGER", mock.Mock()) as log_mock:

            updated, processed = mod._confirm_archive_completed_records("tracker.xlsx", records)

        self.assertFalse(updated)
        self.assertEqual(processed, [])
        save_mock.assert_not_called()
        info_mock.assert_not_called()
        ask_mock.assert_called_once()
        self.assertEqual(ask_mock.call_args.kwargs.get("default"), "cancel")
        log_mock.info.assert_called_once_with("%s cancelled for %d %s%s", "Archive", 2, "completed verse", "s")

    def test_archive_completed_confirm_updates_rows(self):
        mod = self.mod
        records = [
            {"row_index": 101, "verse_snippet": "Verse X", "page": "10", "status": "completed"},
            {"row_index": 202, "verse_snippet": "Verse Y", "page": "11", "status": "completed"},
            {"row_index": 303, "verse_snippet": "Verse Z", "page": "12", "status": "completed"},
        ]
        progress_df = pd.DataFrame(
            [
                {"word": "Test", "status": "completed", "archived_at": None},
                {"word": "Test", "status": "completed", "archived_at": None},
                {"word": "Test", "status": "archived", "archived_at": datetime(2023, 12, 31)},
            ],
            index=[101, 202, 303],
        )

        saved = {}

        def fake_save(path, words_out, progress_out, others_out, *args, **kwargs):
            saved["df"] = progress_out.copy()

        fixed_time = datetime(2024, 2, 3, 4, 5, 6)

        with self._mock_tracker(progress_df), \
            mock.patch.object(mod, "_save_tracker", side_effect=fake_save), \
            mock.patch.object(mod.messagebox, "askokcancel", return_value=True) as ask_mock, \
            mock.patch.object(mod.messagebox, "showinfo") as info_mock, \
            mock.patch.object(mod, "_TRACKER_LOGGER", mock.Mock()) as log_mock:

            updated, processed = mod._confirm_archive_completed_records(
                "tracker.xlsx", records, now_factory=lambda: fixed_time
            )

        self.assertTrue(updated)
        self.assertEqual([rec["row_index"] for rec in processed], [101, 202])
        info_mock.assert_not_called()
        ask_mock.assert_called_once()
        prompt = ask_mock.call_args.args[1]
        self.assertIn("Archive 2 completed verses?", prompt)
        self.assertIn("Verse X", prompt)
        log_mock.info.assert_called_once_with("%s confirmed for %d %s%s", "Archive", 2, "completed verse", "s")

        self.assertIn("df", saved)
        result_df = saved["df"]
        self.assertEqual(mod._normalize_progress_status(result_df.loc[101, "status"]), "archived")
        self.assertEqual(mod._normalize_progress_status(result_df.loc[202, "status"]), "archived")
        self.assertEqual(mod._normalize_progress_status(result_df.loc[303, "status"]), "archived")
        self.assertEqual(result_df.loc[101, "archived_at"], fixed_time)
        self.assertEqual(result_df.loc[202, "archived_at"], fixed_time)
        self.assertEqual(result_df.loc[303, "archived_at"], datetime(2023, 12, 31))


if __name__ == "__main__":
    unittest.main()
