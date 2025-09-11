import os
import shutil
import time
import tkinter as tk
from tkinter import messagebox


def main():
    # Paths used by the app
    excel_path = "1.1.3 sggs_extracted_with_page_numbers.xlsx"
    cache_path = "1.1.3_lexicon_index.json"

    # Prepare environment: hide Tk windows and silence messageboxes
    root = tk.Tk()
    root.withdraw()
    try:
        # Monkey-patch message boxes to avoid blocking UI during quick check
        messagebox.showerror = lambda *a, **k: None
        messagebox.showinfo = lambda *a, **k: None
    except Exception:
        pass

    from importlib import import_module
    mod = import_module("1.1.0_birha".replace(".py", ""))
    app = mod.GrammarApp(root)

    # Ensure clean in-memory state
    if hasattr(app, "_lexicon_index"):
        app._lexicon_index = None

    # Temporarily move Excel out of the way
    excel_backup = None
    if os.path.exists(excel_path):
        excel_backup = excel_path + ".bak-" + str(int(time.time()))
        shutil.move(excel_path, excel_backup)

    # Also move cache if present, to force missing-file scenario
    cache_backup = None
    if os.path.exists(cache_path):
        cache_backup = cache_path + ".bak-" + str(int(time.time()))
        shutil.move(cache_path, cache_backup)

    print("Step 1: Excel missing → build_lexicon_index() should return {} and not set cache")
    res1 = app.build_lexicon_index()
    print("  returned_count=", len(res1))
    print("  in_memory_cache_is_none=", getattr(app, "_lexicon_index", None) is None)

    # Restore Excel
    if excel_backup and os.path.exists(excel_backup):
        shutil.move(excel_backup, excel_path)

    print("Step 2: Excel restored → build_lexicon_index() should rebuild and cache")
    res2 = app.build_lexicon_index()
    print("  returned_count=", len(res2))
    print("  in_memory_cache_len=", len(getattr(app, "_lexicon_index", {}) or {}))
    print("  cache_file_exists=", os.path.exists(cache_path))

    # Restore cache if we moved it (overwrite new cache only if we had a prior backup)
    if cache_backup and os.path.exists(cache_backup):
        try:
            shutil.move(cache_backup, cache_path)
        except Exception:
            pass

    root.destroy()


if __name__ == "__main__":
    main()

