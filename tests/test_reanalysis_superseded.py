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

    def test_reanalyze_completed_prefers_active_grammar_row(self):
        mod = self.mod

        class FakeToplevel:
            def __init__(self, _root=None, **_kwargs):
                self._bindings = {}
                self._state = None

            def title(self, *_args, **_kwargs):
                pass

            def configure(self, *_args, **_kwargs):
                pass

            def state(self, value=None):
                if value is None:
                    return self._state
                self._state = value
                return self._state

            def resizable(self, *_args, **_kwargs):
                pass

            def bind(self, event, handler):
                self._bindings[event] = handler

            def destroy(self):
                pass

        class FakeStringVar:
            def __init__(self, *_args, **_kwargs):
                self._value = ""

            def set(self, value):
                self._value = value

            def get(self):
                return self._value

        class FakeLabel:
            def __init__(self, *_args, **_kwargs):
                pass

            def pack(self, *_args, **_kwargs):
                pass

        class FakeFrame:
            def __init__(self, *_args, **kwargs):
                self._bg = kwargs.get("bg", "")

            def pack(self, *_args, **_kwargs):
                pass

            def bind(self, *_args, **_kwargs):
                pass

            def cget(self, key):
                if key == "bg":
                    return self._bg
                return ""

            def destroy(self):
                pass

            def winfo_children(self):
                return []

        class FakeScrollbar:
            def __init__(self, *_args, **_kwargs):
                pass

            def pack(self, *_args, **_kwargs):
                pass

            def set(self, *_args, **_kwargs):
                pass

        class FakeNotebook:
            def __init__(self, *_args, **_kwargs):
                self.tabs = []
                self.tab_text = {}
                self.selected = None
                self.bindings = {}

            def pack(self, *_args, **_kwargs):
                pass

            def add(self, frame, text=""):
                self.tabs.append(frame)
                self.tab_text[frame] = text

            def select(self, frame):
                self.selected = frame

            def bind(self, event, handler):
                self.bindings[event] = handler

            def tab(self, frame, **kwargs):
                if "text" in kwargs:
                    self.tab_text[frame] = kwargs["text"]

        class FakeProgressCardList:
            instances = []

            def __init__(self, *_args, on_selection_change=None, **_kwargs):
                self.on_selection_change = on_selection_change
                self.records = []
                self._selection = []
                FakeProgressCardList.instances.append(self)

            def set_records(self, records):
                self.records = list(records)
                if callable(self.on_selection_change):
                    self.on_selection_change()

            def selection(self):
                return list(self._selection)

            def has_selection(self):
                return bool(self._selection)

            def clear_selection(self):
                self._selection = []

            def ensure_selected(self, *_args, **_kwargs):
                pass

            def destroy(self):
                pass

            def select_indices(self, indices):
                self._selection = [self.records[i] for i in indices if 0 <= i < len(self.records)]
                if callable(self.on_selection_change):
                    self.on_selection_change()

        class FakeButton:
            instances = []

            def __init__(self, *_args, **kwargs):
                self.command = kwargs.get("command")
                self.text = kwargs.get("text")
                self.state = kwargs.get("state")
                FakeButton.instances.append(self)

            def pack(self, *_args, **_kwargs):
                pass

            def config(self, **kwargs):
                if "state" in kwargs:
                    self.state = kwargs["state"]
                if "text" in kwargs:
                    self.text = kwargs["text"]

            configure = config

            def invoke(self):
                if callable(self.command):
                    self.command()

        FakeButton.instances = []
        FakeProgressCardList.instances = []

        app = mod.GrammarApp.__new__(mod.GrammarApp)
        app.root = object()
        app._get_word_tracker_path = lambda: "tracker.xlsx"
        app._wm_apply = lambda *args, **kwargs: None
        app.start_word_driver_for = lambda *args, **kwargs: None
        app.show_word_verse_hits_modal = lambda *args, **kwargs: None

        word = "TestWord"
        word_token = app._norm_tok(word)
        norm = mod._normalize_simple(word_token)
        verse_text = "Example verse for chips"
        verse_key = mod._normalize_verse_key(verse_text)
        word_index = 7
        base_time = datetime(2024, 5, 1, 8, 0, 0)

        ve_col = "\ufeffVowel Ending"
        grammar_rows = [
            {
                ve_col: word_token,
                "Word Index": str(word_index),
                "Reference Verse": verse_text,
                "Number": "SupNum",
                "Grammar": "SupGrammar",
                "Gender": "SupGender",
                "Word Root": "SupRoot",
                "Type": "SupType",
                "Row State": "Superseded",
            },
            {
                ve_col: word_token,
                "Word Index": str(word_index),
                "Reference Verse": verse_text,
                "Number": "ActiveNum",
                "Grammar": "ActiveGrammar",
                "Gender": "ActiveGender",
                "Word Root": "ActiveRoot",
                "Type": "ActiveType",
                "Row State": "Active",
            },
            {
                ve_col: word_token,
                "Word Index": str(word_index),
                "Reference Verse": verse_text,
                "Number": "LegacyNum",
                "Grammar": "LegacyGrammar",
                "Gender": "LegacyGender",
                "Word Root": "LegacyRoot",
                "Type": "LegacyType",
                "Row State": "",
            },
        ]
        grammar_df = pd.DataFrame(grammar_rows)

        progress_df = pd.DataFrame(
            [
                {
                    "word": word,
                    "word_key_norm": norm,
                    "word_index": word_index,
                    "verse": verse_text,
                    "page_number": 12,
                    "selected_for_analysis": True,
                    "selected_at": base_time,
                    "status": "completed",
                    "completed_at": base_time,
                    "reanalyzed_count": 0,
                    "last_reanalyzed_at": base_time,
                    "created_at": base_time,
                    "removed_at": None,
                    "archived_at": None,
                    "superseded_at": None,
                    "verse_key_norm": verse_key,
                }
            ]
        )

        words_df = pd.DataFrame(
            [
                {
                    "word_key_norm": norm,
                    "analysis_completed": True,
                    "analysis_completed_at": base_time,
                }
            ]
        )

        tracker_state = {
            "words": words_df.copy(),
            "progress": progress_df.copy(),
        }

        def fake_load(*_args, **_kwargs):
            return (
                tracker_state["words"].copy(),
                tracker_state["progress"].copy(),
                [],
            )

        def fake_save(_path, words_out, progress_out, _others_out, *_args, **_kwargs):
            tracker_state["words"] = words_out.copy()
            tracker_state["progress"] = progress_out.copy()

        updated_states = []

        def fake_update(word_arg, verse_arg, index_arg, state_arg):
            updated_states.append((word_arg, verse_arg, index_arg, state_arg))

        expected_chips = "ActiveNum | ActiveGrammar | ActiveGender | ActiveRoot | ActiveType"

        with mock.patch.object(mod.pd, "read_csv", return_value=grammar_df), \
            mock.patch.object(mod, "ensure_word_tracker", side_effect=lambda *args, **kwargs: None), \
            mock.patch.object(mod, "load_word_tracker", side_effect=fake_load), \
            mock.patch.object(mod, "_save_tracker", side_effect=fake_save), \
            mock.patch.object(mod, "_update_birha_row_state", side_effect=fake_update), \
            mock.patch.object(mod.tk, "Toplevel", FakeToplevel), \
            mock.patch.object(mod.tk, "StringVar", FakeStringVar), \
            mock.patch.object(mod.tk, "Label", FakeLabel), \
            mock.patch.object(mod.tk, "Frame", FakeFrame), \
            mock.patch.object(mod.tk, "Scrollbar", FakeScrollbar), \
            mock.patch.object(mod.tk, "Button", FakeButton), \
            mock.patch.object(mod.ttk, "Notebook", FakeNotebook), \
            mock.patch.object(mod, "ProgressCardList", FakeProgressCardList):
            app.show_word_progress_board(word, initial_tab="completed")

            self.assertGreaterEqual(len(FakeProgressCardList.instances), 2, "Expected pending and completed card lists")
            pending_cards, completed_cards = FakeProgressCardList.instances[:2]
            self.assertEqual(len(completed_cards.records), 1, "Should load existing completed record")
            completed_cards.select_indices([0])

            re_btn = next((btn for btn in FakeButton.instances if btn.text == "Re-analyze Selected"), None)
            self.assertIsNotNone(re_btn, "Reanalysis button should exist")
            re_btn.invoke()

        # After invoking reanalysis the tracker should contain a queued row and update chips
        progress_after = tracker_state["progress"]
        self.assertEqual(len(progress_after), 2, "Expected original completed row plus reanalysis queue")
        self.assertIn("reanalysis_queued", progress_after["status"].values)
        self.assertTrue(any(state[-1] == "Superseded" for state in updated_states))

        # The completed cards should now prefer the active grammar chips
        self.assertEqual(len(completed_cards.records), 1)
        chips_value = completed_cards.records[0]["chips"]
        self.assertEqual(chips_value, expected_chips)

        # Pending cards should show the queued row with the same chips source
        self.assertEqual(len(pending_cards.records), 1)
        pending_chips = pending_cards.records[0]["chips"]
        self.assertEqual(pending_chips, expected_chips)


if __name__ == "__main__":
    unittest.main()
