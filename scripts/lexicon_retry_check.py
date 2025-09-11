import os
import shutil
import time
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import messagebox


def _load_birha_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "1.1.0_birha.py"
    spec = importlib.util.spec_from_file_location("birha_mod", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main():
    # Paths used by the app
    excel_path = "1.1.3 sggs_extracted_with_page_numbers.xlsx"
    cache_path = "1.1.3_lexicon_index.json"

    excel_backup = None
    cache_backup = None
    root = None
    try:
        # Prepare environment: hide Tk windows and silence messageboxes
        try:
            root = tk.Tk()
            root.withdraw()
            try:
                # Monkey-patch message boxes to avoid blocking UI during quick check
                messagebox.showerror = lambda *a, **k: None
                messagebox.showinfo = lambda *a, **k: None
            except Exception:
                pass
        except tk.TclError:
            # Headless environment (no display). Skip GUI-based quick check gracefully.
            print("Headless environment: no display available. Skipping lexicon retry quick-check.")
            return

        mod = _load_birha_module()
        app = mod.GrammarApp(root)

        # Ensure clean in-memory state
        if hasattr(app, "_lexicon_index"):
            app._lexicon_index = None

        # Temporarily move Excel out of the way
        if os.path.exists(excel_path):
            excel_backup = excel_path + ".bak-" + str(int(time.time()))
            shutil.move(excel_path, excel_backup)

        # Also move cache if present, to force missing-file scenario
        if os.path.exists(cache_path):
            cache_backup = cache_path + ".bak-" + str(int(time.time()))
            shutil.move(cache_path, cache_backup)

        print("Step 1: Excel missing -> build_lexicon_index() should return {} and not set cache")
        res1 = app.build_lexicon_index()
        print("  returned_count=", len(res1))
        print("  in_memory_cache_is_none=", getattr(app, "_lexicon_index", None) is None)

        # Restore Excel before step 2
        if excel_backup and os.path.exists(excel_backup):
            shutil.move(excel_backup, excel_path)
            excel_backup = None

        print("Step 2: Excel restored -> build_lexicon_index() should rebuild and cache")
        res2 = app.build_lexicon_index()
        print("  returned_count=", len(res2))
        print("  in_memory_cache_len=", len(getattr(app, "_lexicon_index", {}) or {}))
        print("  cache_file_exists=", os.path.exists(cache_path))
    finally:
        # Always restore backups on any error or interruption
        try:
            if excel_backup and os.path.exists(excel_backup):
                if not os.path.exists(excel_path):
                    shutil.move(excel_backup, excel_path)
                else:
                    os.remove(excel_backup)
        except Exception:
            pass
        try:
            if cache_backup and os.path.exists(cache_backup):
                if not os.path.exists(cache_path):
                    shutil.move(cache_backup, cache_path)
                else:
                    os.remove(cache_backup)
        except Exception:
            pass
        try:
            if root is not None:
                root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
