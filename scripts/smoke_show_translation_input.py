import tkinter as tk
import importlib.util
from pathlib import Path


def main():
    root = tk.Tk()
    # Dynamically load the main app module (filename is not a valid identifier)
    mod_path = (Path(__file__).resolve().parents[1] / '1.1.0_birha.py').resolve()
    spec = importlib.util.spec_from_file_location('birha_mod', str(mod_path))
    assert spec and spec.loader, f"Cannot load module from {mod_path}"
    birha_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(birha_mod)
    app = birha_mod.GrammarApp(root)

    # Provide a simple verse for tokenization
    app.selected_verse_text = "ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ ਨਿਰਭਉ ਨਿਰਵੈਰੁ"

    # Open the Assess-by-Word analyzer (uses the shared translation input UI)
    app.show_assess_by_word_analyzer()

    def fill_and_submit():
        try:
            # Enter minimal translation text
            app._translation_text.delete('1.0', tk.END)
            app._translation_text.insert('1.0', "Arth:\nSample translation for smoke test.\n\nBhav:\nSample.")
            # Select the first two words
            for i, (var, _w) in enumerate(getattr(app, '_word_selection_vars', [])):
                if i < 2:
                    var.set(True)
            # Find the top-level analyzer window and submit
            tops = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
            if tops:
                app._on_translation_submitted(tops[-1])
        except Exception as e:
            print(f"Smoke submit error: {e}")

    # Give the UI time to render before interacting
    root.after(800, fill_and_submit)
    # Close shortly after to keep it lightweight
    root.after(1600, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
