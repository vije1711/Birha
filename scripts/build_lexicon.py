import json
import re
import unicodedata
from collections import Counter
from datetime import datetime

import pandas as pd


def _norm_tok(t: str) -> str:
    """Mirror app's token normalization:
    - NFC normalize and strip
    - remove danda/double-danda
    - remove ZERO WIDTH SPACE, ZWNJ, ZWJ
    - strip trailing digits (Latin+Gurmukhi) and punctuation
    """
    if t is None:
        return ""
    t = unicodedata.normalize("NFC", str(t).strip())
    # danda and double danda (characters intentionally literal to mirror app regex)
    t = re.sub(r"[॥।]", "", t)
    # remove ZERO WIDTH SPACE, ZWNJ, ZWJ
    t = t.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    # trailing digits (Latin+Gurmukhi) & common punctuation/hyphens
    t = re.sub(r"[\d\u0A66-\u0A6F.,;:!?\"'\-–—]+$", "", t)
    return t


def build_lexicon(excel_path: str = "1.1.3 sggs_extracted_with_page_numbers.xlsx",
                  out_json: str = "1.1.3_lexicon.json") -> dict:
    df = pd.read_excel(excel_path)
    if 'Verse' not in df.columns:
        raise ValueError("Expected a 'Verse' column in the SGGS Excel.")

    counter = Counter()
    total_rows = len(df)

    for _, row in df.iterrows():
        verse = row.get('Verse', '')
        if not isinstance(verse, str):
            verse = str(verse)
        # quick clean of danda inside verse text before splitting
        verse = unicodedata.normalize("NFC", verse)
        # Tokenize by whitespace, then normalize per-token
        for tok in verse.split():
            nt = _norm_tok(tok)
            if nt:
                counter[nt] += 1

    counts = dict(counter)
    payload = {
        "meta": {
            "source": excel_path,
            "built_at": datetime.utcnow().isoformat() + "Z",
            "unique_tokens": len(counts),
            "rows": int(total_rows),
        },
        "counts": counts,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


if __name__ == "__main__":
    payload = build_lexicon()
    print(f"Lexicon built with {payload['meta']['unique_tokens']} unique tokens.")

