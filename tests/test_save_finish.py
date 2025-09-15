import importlib.util
import pathlib
from unittest.mock import patch

# Dynamically import the main module with a valid name
SPEC = importlib.util.spec_from_file_location(
    "birha", pathlib.Path(__file__).resolve().parents[1] / "1.1.0_birha.py"
)
birha = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(birha)
GrammarApp = birha.GrammarApp

class DummyVar:
    def __init__(self, value=""):
        self.value = value
    def get(self):
        return self.value


def create_app():
    app = GrammarApp.__new__(GrammarApp)
    app.all_new_entries = []
    return app


def test_save_finish_abv(tmp_path):
    app = create_app()
    app.selected_verses = ["dummy verse"]
    app.current_detailed_entry = {
        "Word": "foo",
        "Vowel Ending": "foo",
        "Number / ਵਚਨ": "Singular",
        "Grammar / ਵਯਾਕਰਣ": "Noun",
        "Gender / ਲਿੰਗ": "Masc",
        "Word Root": "root",
        "Type": "Noun / ਨਾਂਵ",
        "Evaluation": "Derived",
        "Reference Verse": "dummy verse",
        "Darpan Translation": "",
        "Darpan Meaning": "",
        "ChatGPT Commentary": "",
        "Word Index": 0,
    }
    app.detailed_ve_var = DummyVar("foo")
    app.detailed_number_var = DummyVar("Singular")
    app.detailed_grammar_var = DummyVar("Noun")
    app.detailed_gender_var = DummyVar("Masc")
    app.detailed_root_var = DummyVar("root")

    with patch.object(app, '_append_birha_csv_row', return_value=(True, 1, 'append')), \
         patch.object(app, 'prompt_save_results', return_value=None), \
         patch('tkinter.messagebox.showinfo') as mock_info:
        app.on_accept_detailed_grammar(None)
        app.finish_and_prompt_save()
        titles = [call.args[0] for call in mock_info.call_args_list]
        messages = [call.args[1] for call in mock_info.call_args_list]
        assert "No Entries" not in titles
        assert any("Session Summary" == t for t in titles)
        assert any("1 grammar assessments" in m for m in messages)
        assert app.all_new_entries == []


def test_save_finish_abw(tmp_path):
    app = create_app()
    app._current_detailed_mode = 'word'
    app.selected_verses = []
    app.current_detailed_entry = {
        "Word": "bar",
        "Vowel Ending": "bar",
        "Number / ਵਚਨ": "Singular",
        "Grammar / ਵਯਾਕਰਣ": "Noun",
        "Gender / ਲਿੰਗ": "Masc",
        "Word Root": "root",
        "Type": "Noun / ਨਾਂਵ",
        "Evaluation": "Derived",
        "Reference Verse": "verse2",
        "Darpan Translation": "",
        "Darpan Meaning": "",
        "ChatGPT Commentary": "",
        "Word Index": 1,
    }

    with patch.object(app, '_append_birha_csv_row', return_value=(True, 1, 'append')), \
         patch.object(app, 'prompt_save_results', return_value=None), \
         patch('tkinter.messagebox.showinfo') as mock_info:
        app.on_accept_detailed_grammar(None)
        app.finish_and_prompt_save()
        titles = [call.args[0] for call in mock_info.call_args_list]
        messages = [call.args[1] for call in mock_info.call_args_list]
        assert "No Entries" not in titles
        assert any("Session Summary" == t for t in titles)
        assert any("1 grammar assessments" in m for m in messages)
        assert app.all_new_entries == []
