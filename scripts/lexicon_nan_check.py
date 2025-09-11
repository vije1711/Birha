import os
from pathlib import Path
import importlib.util
import tkinter as tk
import numpy as np
import pandas as pd


def _load_birha_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "1.1.0_birha.py"
    spec = importlib.util.spec_from_file_location("birha_mod", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main():
    root = tk.Tk()
    root.withdraw()
    mod = _load_birha_module()
    app = mod.GrammarApp(root)

    # 1) NaN verse should yield no tokens and never 'nan'
    toks_nan = app._tokenize_and_normalize(np.nan)
    print("nan_input_tokens=", toks_nan)
    print("contains_literal_nan_token=", any((t or '').lower() == 'nan' for t in toks_nan))

    # 2) Empty string also yields no tokens
    toks_empty = app._tokenize_and_normalize("")
    print("empty_input_tokens=", toks_empty)

    # 3) Valid strings tokenize and normalize: danda, digits stripped
    toks_valid = app._tokenize_and_normalize("foo ॥ 123 bar")
    print("valid_input_tokens=", toks_valid)

    # 4) DataFrame-like iteration: includes NaN row
    df = pd.DataFrame({"Verse": [np.nan, "baz ॥ 77", "qux"]})
    all_tokens = []
    for v in df["Verse"]:
        all_tokens.extend(app._tokenize_and_normalize(v))
    print("df_all_tokens=", all_tokens)
    print("df_contains_literal_nan_token=", any((t or '').lower() == 'nan' for t in all_tokens))

    root.destroy()


if __name__ == "__main__":
    main()

