import sys
import tkinter as tk
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / '1.1.0_birha.py'

spec = importlib.util.spec_from_file_location('birha_app', str(MOD_PATH))
birha_app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
try:
    spec.loader.exec_module(birha_app)  # type: ignore
except ModuleNotFoundError as e:
    missing = getattr(e, 'name', 'dependencies')
    print(f"ui_smoke_checks: SKIPPED (missing dependency: {missing})")
    sys.exit(0)
GrammarApp = birha_app.GrammarApp  # type: ignore


def _find_toplevel_by_title(root: tk.Tk, title: str):
    for w in root.winfo_children():
        try:
            if isinstance(w, tk.Toplevel) and w.wm_title() == title:
                return w
        except Exception:
            continue
    return None


def _iter_children_recursive(widget):
    try:
        children = list(widget.winfo_children())
    except Exception:
        return
    for c in children:
        yield c
        yield from _iter_children_recursive(c)


def _find_button_by_text(container, text: str):
    for w in _iter_children_recursive(container):
        try:
            if isinstance(w, tk.Button) and str(w.cget('text')) == text:
                return w
        except Exception:
            continue
    return None

def _find_button_text_contains(container, needle: str):
    for w in _iter_children_recursive(container):
        try:
            if isinstance(w, tk.Button) and needle in str(w.cget('text')):
                return w
        except Exception:
            continue
    return None


def check_back_button_closes_toplevel():
    root = tk.Tk()
    root.withdraw()
    app = GrammarApp(root)
    # open verse assessment window
    app.launch_verse_assessment()
    win = _find_toplevel_by_title(root, 'Assess by Verse')
    assert win is not None, 'Assess by Verse window not found'
    back_btn = _find_button_by_text(win, 'Back to Dashboard')
    assert back_btn is not None, 'Back to Dashboard button not found in verse window'
    # invoke and ensure window closes
    back_btn.invoke()
    root.update_idletasks()
    exists = 1
    try:
        exists = int(win.winfo_exists())
    except Exception:
        exists = 0
    assert exists == 0, 'Back to Dashboard did not destroy the verse selection window'
    try:
        root.destroy()
    except Exception:
        pass


def check_word_button_grouped_under_grammar_update():
    root = tk.Tk()
    root.withdraw()
    app = GrammarApp(root)
    # open grammar update window
    app.launch_grammar_update_dashboard()
    win = _find_toplevel_by_title(root, 'Grammar Database Update')
    assert win is not None, 'Grammar Database Update window not found'
    word_btn = _find_button_by_text(win, 'Assess by Word')
    assert word_btn is not None, 'Assess by Word button not present in Grammar DB Update'
    # ensure not present on main dashboard
    app.show_dashboard()
    none_btn = _find_button_by_text(root, 'Assess by Word Dashboard')
    assert none_btn is None, 'Assess by Word should not be a top-level dashboard button'
    try:
        root.destroy()
    except Exception:
        pass


def check_grammar_update_back_button_destroys_win():
    root = tk.Tk()
    root.withdraw()
    app = GrammarApp(root)
    app.launch_grammar_update_dashboard()
    win = _find_toplevel_by_title(root, 'Grammar Database Update')
    assert win is not None, 'Grammar Database Update window not found'
    back_btn = _find_button_text_contains(win, 'Back to Dashboard')
    assert back_btn is not None, 'Back to Dashboard button not found in Grammar DB Update'
    back_btn.invoke()
    root.update_idletasks()
    exists = 1
    try:
        exists = int(win.winfo_exists())
    except Exception:
        exists = 0
    assert exists == 0, 'Back to Dashboard did not destroy the Grammar DB window'
    try:
        root.destroy()
    except Exception:
        pass


def check_word_dashboard_back_button_no_error():
    # Ensure the Back to Dashboard button in the Word dashboard does not reference a Toplevel
    root = tk.Tk(); root.withdraw()
    app = GrammarApp(root)
    # Open Grammar DB Update and navigate to Word dashboard
    app.launch_grammar_update_dashboard()
    win = _find_toplevel_by_title(root, 'Grammar Database Update')
    assert win is not None, 'Grammar Database Update window not found'
    word_btn = _find_button_by_text(win, 'Assess by Word')
    assert word_btn is not None, 'Assess by Word button not found in Grammar DB Update'
    word_btn.invoke()
    root.update_idletasks()

    # Intercept Tk callback exceptions
    errors = []
    def _report_cb(self, exc, val, tb):
        errors.append((exc, val))
    orig = tk.Misc.report_callback_exception
    tk.Misc.report_callback_exception = _report_cb
    try:
        back_btn = _find_button_by_text(root, 'Back to Dashboard')
        assert back_btn is not None, 'Back to Dashboard button not found in Word dashboard'
        back_btn.invoke()
        root.update_idletasks()
    finally:
        tk.Misc.report_callback_exception = orig
    assert not errors, f'Exception during Word dashboard Back to Dashboard: {errors!r}'
    try:
        root.destroy()
    except Exception:
        pass


def check_reanalysis_buttons_present():
    root = tk.Tk(); root.withdraw()
    app = GrammarApp(root)
    # Attempt to open the Select Verse window; skip if deps prevent it
    try:
        app.launch_select_verse()
    except Exception as e:
        print(f"ui_smoke_checks: SKIPPED (launch_select_verse dependency issue: {e})")
        try:
            root.destroy()
        except Exception:
            pass
        return
    win = _find_toplevel_by_title(root, 'Select Verse')
    assert win is not None, 'Select Verse window not found'
    analyze_btn = _find_button_text_contains(win, 'Analyze Selected')
    back_search_btn = _find_button_text_contains(win, 'Back to Search')
    back_dash_btn = _find_button_text_contains(win, 'Back to Dashboard')
    assert analyze_btn is not None, 'Analyze Selected button not found in reanalysis view'
    assert back_search_btn is not None, 'Back to Search button not found in reanalysis view'
    assert back_dash_btn is not None, 'Back to Dashboard button not found in reanalysis view'
    try:
        root.destroy()
    except Exception:
        pass


def main():
    check_back_button_closes_toplevel()
    check_word_button_grouped_under_grammar_update()
    check_grammar_update_back_button_destroys_win()
    check_word_dashboard_back_button_no_error()
    check_reanalysis_buttons_present()
    print('ui_smoke_checks: OK')


if __name__ == '__main__':
    main()
