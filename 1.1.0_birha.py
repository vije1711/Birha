import csv
import os
from tkinter import messagebox, scrolledtext
import pandas as pd
import ast
import re
import math
import unicodedata
import pyperclip
import tkinter as tk
from tkinter import ttk
import threading
from rapidfuzz import fuzz
import numpy as np
import textwrap
import webbrowser
import subprocess
import json
import webbrowser


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# GLOBAL HELPER  â€“  build live noun-morphology lookup
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from functools import lru_cache

# ID used to gate the one-time "What's New" prompt.
# Prefer the latest UI tag from Git if available; otherwise, fall back.
def _compute_whats_new_id():
    try:
        # Get UI tags sorted by create date (newest first)
        result = subprocess.run(
            ["git", "tag", "--list", "ui-*", "--sort=-creatordate"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                tag = line.strip()
                if tag:
                    return tag
    except Exception:
        pass
    return "ui-2025-09-07-cards-layout"

WHATS_NEW_ID = _compute_whats_new_id()

# Structured Darpan sources: JSON/CSV loader helpers
def _normalize_simple(text: str) -> str:
    try:
        s = str(text)
    except Exception:
        return ""
    try:
        s = unicodedata.normalize('NFC', s)
    except Exception:
        pass
    s = s.strip().lower()
    return " ".join(s.split())

def _normalize_verse_key(text: str) -> str:
    """Robust comparable key for verse text.
    - Unicode normalize, lowercase
    - Remove danda marks (à¥¤, à¥¥) and digits (ASCII + Gurmukhi)
    - Collapse whitespace
    """
    try:
        s = str(text)
    except Exception:
        return ""
    try:
        s = unicodedata.normalize('NFC', s)
    except Exception:
        pass
    s = s.lower()
    s = s.replace('à¥¥', ' ').replace('à¥¤', ' ')
    s = re.sub(r"[\u0A66-\u0A6F0-9]+", " ", s)
    s = " ".join(s.split())
    return s

def _parse_page_value(val):
    try:
        if val is None:
            return None
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            if math.isnan(val):
                return None
            return str(int(val))
        s = str(val).strip()
        # Find first ASCII digit group anywhere, e.g., "171-172", "[171]"
        m = re.search(r"(\d+)", s)
        if m:
            return m.group(1)
        return s or None
    except Exception:
        return None

def _normalize_record(rec: dict) -> dict:
    try:
        items = rec.items()
    except Exception:
        try:
            items = dict(rec).items()
        except Exception:
            items = []
    keys = {str(k).lower(): v for k, v in items}
    out = {
        'verse': keys.get('verse', ''),
        'padarth': keys.get('padarth', ''),
        'arth': keys.get('arth', ''),
        'chhand': keys.get('chhand', ''),
        'bhav': keys.get('bhav', ''),
        'excel_verses': keys.get('excel_verses') if 'excel_verses' in keys else keys.get('excel_verse'),
        'pages': keys.get('pages') if 'pages' in keys else keys.get('page'),
    }
    ex = out.get('excel_verses') or out.get('verse') or ''
    if isinstance(ex, (list, tuple)):
        try:
            ex = " ".join(map(str, ex))
        except Exception:
            ex = str(ex)
    out['norm_excel'] = _normalize_simple(ex)
    out['norm_excel_key'] = _normalize_verse_key(ex)
    out['norm_page'] = _parse_page_value(out.get('pages'))
    return out

def _load_arth_sources_once(self):
    if getattr(self, '_arth_loaded', False):
        return
    self._arth_loaded = True
    records = []
    # JSON sources (try multiple known filenames)
    for json_path in [
        '1.1.3 sggs_extracted_with_page_numbers.json',
        '1.1.4 Verse_Padarth_Arth_with_pages.json',
    ]:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = list(data.values())[0] if isinstance(data, dict) else data
                if isinstance(items, list):
                    for rec in items:
                        if isinstance(rec, dict):
                            r = _normalize_record(rec); r['source'] = json_path; records.append(r)
        except Exception:
            continue
    # CSV sources (try multiple known filenames)
    for csv_path in [
        '1.1.4 Verse_Padarth_Arth_with_pages.csv',
        '1.1.5 Verse_Padarth_Arth_with_pages.csv',
    ]:
        try:
            df = pd.read_csv(csv_path)
            for idx, row in df.iterrows():
                r = _normalize_record(row.to_dict()); r['source'] = csv_path; r['row'] = int(idx); records.append(r)
        except Exception:
            continue
    # Deduplicate by (norm_excel, norm_page)
    seen = {}
    for rec in records:
        key = (rec.get('norm_excel') or '', rec.get('norm_page') or '')
        if key not in seen:
            seen[key] = rec
    self._arth_records = list(seen.values())

def _find_arth_for(self, verse_text: str, page_num, strict=False):
    try:
        _load_arth_sources_once(self)
    except Exception:
        return None
    if not getattr(self, '_arth_records', None):
        return None
    target_norm_verse = _normalize_simple(verse_text)
    target_norm_key = _normalize_verse_key(verse_text)
    target_page = _parse_page_value(page_num)
    # Pass 1: exact verse match; optionally require page match if strict is True
    for rec in self._arth_records:
        verse_ok = (rec.get('norm_excel') == target_norm_verse or rec.get('norm_excel_key') == target_norm_key)
        if not verse_ok:
            continue
        page_ok = (target_page is None or rec.get('norm_page') == target_page)
        if strict and target_page is not None and not page_ok:
            continue
        if verse_ok and page_ok:
            info = {'match': 'exact+page' if (target_page is not None and page_ok) else 'exact', 'source': rec.get('source')}
            return rec, info
    # Pass 2: verse-only strict match
    for rec in self._arth_records:
        if rec.get('norm_excel') == target_norm_verse or rec.get('norm_excel_key') == target_norm_key:
            info = {'match': 'exact', 'source': rec.get('source')}
            return rec, info
    # Pass 3: fuzzy match on verse key (prefer page matches)
    try:
        best = None
        best_info = None
        best_score = 0
        for rec in self._arth_records:
            key = rec.get('norm_excel_key') or ''
            score = fuzz.token_sort_ratio(target_norm_key, key)
            if target_page is not None and rec.get('norm_page') == target_page:
                score += 5
            if score > best_score:
                best_score = score
                best = rec
                best_info = {'match': 'fuzzy', 'score': best_score, 'source': rec.get('source')}
        if best and best_score >= 75 and not strict:
            return best, best_info
    except Exception:
        pass
    return None

# Helper to determine whether a given string is a full Punjabi word
def is_full_word(s: str) -> bool:
    """Return ``True`` if *s* looks like a complete Punjabi word."""
    s = str(s).strip()
    # Words starting with a vowel matra are generally suffixes
    return len(s) > 1 and not ("\u0A3E" <= s[0] <= "\u0A4C")

# â”€â”€ Canonical ending-class labels for the dropdown â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CANONICAL_ENDINGS = [
    "NA",
    "à¨®à©à¨•à¨¤à¨¾ Ending",      # bare consonant
    "à¨•à©°à¨¨à¨¾ Ending",       # â€“à¨¾
    "à¨¸à¨¿à¨¹à¨¾à¨°à©€ Ending",     # â€“à¨¿
    "à¨¬à¨¿à¨¹à¨¾à¨°à©€ Ending",     # â€“à©€
    "à¨¹à©‹à¨°à¨¾ Ending",       # â€“à©‹ / â€“à¨“ poetic
    "à¨‰ Ending",          # â€“à©
    "à©‚ Ending",          # â€“à©‚
]

# ------------------------------------------------------------------
#  FULL-WORD EXEMPLARS FOR EACH ENDING-CLASS
#  (trim / extend these lists whenever you like)
# ------------------------------------------------------------------

# â”€â”€â”€ Canonical â€œkeepâ€ vowel for each ending-class â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
KEEP_CHAR = {
    "à¨®à©à¨•à¨¤à¨¾ Ending": "",
    "à¨•à©°à¨¨à¨¾ Ending": ("à¨¾", "à¨†", "à¨¿à¨†"),
    "à¨¸à¨¿à¨¹à¨¾à¨°à©€ Ending": "à¨¿",
    "à¨¬à¨¿à¨¹à¨¾à¨°à©€ Ending": "à©€",
    "à¨¹à©‹à¨°à¨¾ Ending": "à©‹",
    "à¨‰ Ending": "à©",
    "à©‚ Ending": "à©‚",
}

ENDING_EXAMPLES = {
    "à¨®à©à¨•à¨¤à¨¾ Ending": [
        "à¨‰à¨¦à¨¿à¨†à¨¨à©ˆ","à¨‰à¨ªà¨¾à¨µà©€","à¨“à¨…à©°à¨•à¨¾à¨°à¨¿","à¨…à¨–à©€","à¨…à¨–à¨°à¨¾","à¨†à¨¹à¨°",
        "à¨…à¨®à©à¨²","à¨…à¨®à©à¨²à©","à¨…à¨µà¨¿à¨—à¨¤à©‹","à¨…à©°à¨§à©‡","à¨…à¨¹à©°à¨•à¨¾à¨°à©€","à¨†à¨¸","à¨†à¨¸à©ˆ",
        "à¨‰à¨¤à¨®","à¨‰à¨ªà¨¾à¨‡","à¨‰à¨¦à¨®","à¨•à¨¦à¨°","à¨œà¨¹à¨¾à¨œ", "à¨¦à¨°à¨¦","à¨…à¨¨à¨¾à¨¥à¨¹",
        "à¨•à¨°à¨®","à¨•à¨‰à¨¤à¨•","à¨šà¨°à¨£","à¨šà¨¿à¨¤","à¨§à¨°à¨®","à¨¨à¨¦à¨°","à¨¨à¨¿à¨¸à¨¼à¨¾à¨¨","à¨ªà¨¦à¨®"
    ],

    "à¨•à©°à¨¨à¨¾ Ending": [
        "à¨†à¨—à¨¿à¨†","à¨¤à©à¨°à¨¿à¨¸à¨¨à¨¾","à¨¦à©à¨¬à¨¿à¨§à¨¾","à¨¨à¨¿à©°à¨¦à¨¾","à¨°à¨¸à¨¨à¨¾","à¨¸à¨–à©€à¨†","à¨¸à¨¿à¨°à©€à¨†","à¨œà¨¿à¨¹à¨¬à¨¾",
        "à¨œà¨¿à¨¹à¨µà©‡","à¨®à¨¾à¨‡à¨†","à¨­à¨¾à¨ˆà¨†","à¨¬à¨¹à©à¨°à©€à¨†","à¨®à¨¨à©‚à¨†","à¨¨à¨¿à¨®à¨¾à¨£à¨¿à¨†","à¨¨à¨¿à¨—à©à¨°à¨¿à¨†",
        "à¨µà¨¡à¨­à¨¾à¨—à©€à¨†","à¨µà¨¡à¨¿à¨†à¨ˆà¨†","à¨šà©°à¨—à¨¿à¨†à¨ˆà¨†","à¨—à©‹à¨ªà©€à¨†","à¨•à¨¹à¨¾à¨£à©€à¨†","à¨•à©œà¨›à©€à¨†","à¨šà¨¾à¨Ÿà©œà¨¿à¨†",
        "à¨–à¨Ÿà©€à¨†","à¨—à©à¨ªà¨¤à¨§à¨¾","à¨¦à©à¨¹à¨¾à¨ˆà¨†","à¨šà©œà©à¨¹à¨¾à¨ˆà¨†","à¨˜à©œà©€à¨†","à¨¸à¨¥à¨¾à¨¸à©€à¨†","à¨•à¨¹à¨¾à¨£à©€à¨†"
    ],

    "à¨¸à¨¿à¨¹à¨¾à¨°à©€ Ending": [
        "à¨•à¨¿à¨°à¨¤à¨¿","à¨šà¨¿à¨¤à¨¿","à¨­à¨—à¨¤à¨¿","à¨—à©à¨°à¨¹à¨¿","à¨ªà¨°à¨®à¨¾à¨¤à¨®à¨¿","à¨•à¨²à¨ªà¨¿","à¨°à¨¿à¨¦à¨¿",
        "à¨–à¨°à¨šà¨¿","à¨¨à¨°à¨¸à¨¿","à¨šà¨¾à¨°à¨¿à¨¤à©à¨°à¨¿","à¨…à¨šà¨°à¨œà¨¿","à¨²à¨¹à¨¿à¨°à¨¿","à¨¦à©à¨°à¨¿à¨¸à¨Ÿà¨¿","à¨¸à©°à¨œà©€à¨µà¨¨à¨¿",
        "à¨¨à¨µà¨œà¨¾à¨¤à¨¿","à¨…à¨•à¨¸à¨¼à¨¿","à¨…à¨°à¨¸à¨¿à¨…","à¨¸à¨¿à¨–à¨¿","à¨¸à¨¿à¨–à¨¿à¨†","à¨œà¨ªà¨¤à¨¿","à¨¸à©à¨°à¨¿à¨¸à¨Ÿà¨¿","à¨¨à¨¿à¨°à¨®à¨¤à¨¿",
        "à¨¦à©‡à¨µà¨¤à¨¿","à¨†à¨¦à¨¿à¨¸à¨Ÿà¨¿","à¨†à¨¸à¨•à¨¤à¨¿","à¨‰à¨°à¨§à¨¿à¨•à¨¿","à¨•à¨²à¨®à¨¿","à¨¨à¨¿à¨œà¨®à¨¿","à¨¸à©°à¨—à¨¤à¨¿"
    ],

    "à¨¬à¨¿à¨¹à¨¾à¨°à©€ Ending": [
        "à¨¨à¨¿à¨°à¨—à©à¨£à©€","à¨¸à©à¨œà¨¾à¨£à©€","à¨­à¨—à¨¤à©€","à¨¦à¨¿à¨²à¨—à©€","à¨¬à©€à¨¬à©€","à¨¸à¨¾à¨•à©€","à¨•à¨¹à¨¾à¨£à©€",
        "à¨•à¨¬à©€à¨°à©€","à¨¸à¨¦à©€à¨•à©€","à¨ªà©à¨°à©€à¨¤à©€","à¨®à¨¹à¨¿à¨²à©€","à¨®à¨¾à¨¤à©€","à¨¬à¨²à¨µà©€","à¨¡à©°à¨¡à©€","à¨®à¨¿à¨²à¨¨à©€",
        "à¨¸à¨šà¨¾à¨ˆ","à¨°à©à¨¸à¨¼à¨¤à©€","à¨…à¨²à¨¸à©€","à¨¦à¨¿à©°à¨¦à©€","à¨²à¨¿à¨–à¨¤à©€à¨‚","à¨§à©€à¨°à¨œà©€","à¨•à©à¨°à¨¿à¨ªà¨¾à¨²à©€",
        "à¨•à¨¿à¨°à¨ªà¨¾à¨ˆ","à¨—à©à¨°à¨¹à¨£à©€","à¨¨à¨¿à¨®à¨¾à¨£à©€"
    ],

    "à¨¹à©‹à¨°à¨¾ Ending": [
        "à¨“à¨¹à©","à¨“à¨¹","à¨“à¨¹à©€","à¨“à¨¹à©‹","à¨“à¨†","à¨“à¨†à¨¹","à¨“à¨ˆà¨","à¨“à¨‡","à¨“à¨ˆ","à¨“à¨"
    ],

    "à¨‰ Ending": [
        "à¨²à¨–à©","à¨²à¨›à©","à¨²à¨¾à¨–à©","à¨…à©°à¨¸à©","à¨•à¨²à¨¤à©","à¨–à¨¾à¨•à©","à¨…à¨•à¨¤à©","à¨…à¨®à¨¤à©","à¨¤à¨ªà©",
        "à¨°à¨•à¨¤à©","à¨­à¨µà¨¨à©","à¨•à©°à¨¤à©","à¨¸à¨¤à©","à¨¸à¨¤à©","à¨¨à¨¿à¨¸à©","à¨•à¨‰à¨¨à©","à¨®à¨¨à©","à¨¸à¨¨à©",
        "à¨‰à¨¤à¨ªà¨¤à©","à¨†à¨¦à¨¤à©","à¨¦à¨¯à©","à¨¦à¨¨à©","à¨•à¨°à¨®à©","à¨•à¨°à¨¤à©","à¨°à¨‰","à¨—à¨‰","à¨˜à¨‰","à¨šà¨¹à©"
    ],

    "à©‚ Ending": [
        "à¨®à©‚à¨²à©‚","à¨¸à©‚à¨²à©‚","à¨­à©‚à¨²à©‚","à¨¶à©‚à¨²à©‚","à¨°à©‚à¨ªà©‚","à¨¹à¨¿à¨°à¨¦à©‚","à¨¦à¨¿à¨²à©‚","à¨®à¨¿à¨¤à©à¨°à©‚","à¨§à¨°à¨¤à©‚",
        "à¨¸à¨µà¨¾à¨°à©‚"
    ],
}

# â”€â”€â”€ Function that turns ENDING_EXAMPLES into (Full, Base, Suffix) tuples â”€â”€

def build_example_bases(
    csv_path: str = "1.1.1_birha.csv",
    ending_examples: dict[str, list[str]] = None,
    keep_char: dict[str, str] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    if ending_examples is None or keep_char is None:
        raise ValueError("Pass ENDING_EXAMPLES and KEEP_CHAR")


    df = (pd.read_csv(csv_path).rename(columns={"Vowel Ending": "\ufeffVowel Ending", "Word Type": "Type"}).fillna("")
            .assign(**{
                "Word Root": lambda d: (
                    d["Word Root"]
                      .str.replace("à¨•à¨¨à¨¾à©± Ending","à¨•à©°à¨¨à¨¾ Ending", regex=False)
                      .str.replace("à¨•à¨¨à¨¾ Ending","à¨•à©°à¨¨à¨¾ Ending", regex=False)
                )
            }))

    # map: same 5-feature key â†’ list of 1-glyph endings
    suffix_lookup = {}
    small = df[~df["\ufeffVowel Ending"].apply(is_full_word)]
    for _, r in small.iterrows():
        k = (r["Word Root"], r["Type"], r["Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"],
             r["Gender / à¨²à¨¿à©°à¨—"], r["Number / à¨µà¨šà¨¨"])
        suffix_lookup.setdefault(k, []).append(r["\ufeffVowel Ending"].strip())

    result = {}
    for label, wordlist in ending_examples.items():
        canon = keep_char.get(label, "")
        canon_set = set(canon) if isinstance(canon, (list, tuple, set)) else {canon}
        triples = []
        for full in wordlist:
            row = df[(df["\ufeffVowel Ending"].str.strip() == full) &
                     (df["Word Root"] == label)]
            if row.empty:
                triples.append((full, full, ""))
                continue
            r = row.iloc[0]
            k = (r["Word Root"], r["Type"], r["Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"],
                 r["Gender / à¨²à¨¿à©°à¨—"], r["Number / à¨µà¨šà¨¨"])
            base, suf = full, ""
            for cand in suffix_lookup.get(k, []):
                cand = cand.strip()
                if cand in canon_set or cand == "":
                    continue
                if full.endswith(cand):
                    base = full[:-len(cand)]
                    suf = cand
                    break
               
            if label == "à¨®à©à¨•à¨¤à¨¾ Ending" and base == full and len(full) > 1:
                last = full[-1]
                # Unicode range for Gurmukhi matras (U+0A3Eâ€“U+0A4C)
                if "\u0A3E" <= last <= "\u0A4C":
                    # strip that final matra as a true detachment
                    base, suf = full[:-1], last
            
            triples.append((full, base, suf))
        result[label] = triples
    return result

EXAMPLE_BASES = build_example_bases(
    csv_path="1.1.1_birha.csv",
    ending_examples=ENDING_EXAMPLES,
    keep_char=KEEP_CHAR,
)


@lru_cache(maxsize=1)
def build_noun_map(csv_path="1.1.1_birha.csv"):
    """
    Returns a nested dict:
        noun_map[ending][gender][number][case] -> [list of attested forms]
    The loader also normalises stray spaces & typo-variants so look-ups never fail
    due to invisible characters.
    """
    df = (
        pd.read_csv(csv_path)
          .query("Type.str.startswith('Noun')", engine="python")
          .fillna("NA")
          .rename(columns={
              "Vowel Ending"        : "ending",
              "Number / à¨µà¨šà¨¨"         : "num",
              "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"     : "case",
              "Gender / à¨²à¨¿à©°à¨—"         : "gender",
              "Word Root"           : "root",
          })
    )

    # --- normalise whitespace & common misspellings -----------------
    for c in ("ending", "gender", "num", "case", "root"):
        df[c] = (
            df[c].astype(str)
                 .str.replace(r"\s+", " ", regex=True)   # collapse weird spaces
                 .str.strip()                            # trim front/back
        )

    # unify the Kanna spelling
    df["root"] = df["root"].str.replace("à¨•à¨¨à¨¾à©± Ending", "à¨•à©°à¨¨à¨¾ Ending")

    # --- build nested dictionary ------------------------------------
    by_end = {}
    for ending, g1 in df.groupby("ending"):
        g_dict = {}
        for gender, g2 in g1.groupby("gender"):
            n_dict = {}
            for num, g3 in g2.groupby("num"):
                case_dict = (
                    g3.groupby("case")["ending"]     # store the surface form
                      .apply(list)                   # list of forms
                      .to_dict()
                )
                n_dict[num] = case_dict
            g_dict[gender] = n_dict
        by_end[ending] = g_dict
    return by_end


class GrammarApp:
    def __init__(self, root):
        """
        Initialize the application and display the dashboard as the main window.
        """
        # ------------------------------------------------------------------
        # â”€â”€â”€ 1.  BASIC ROOTâ€‘WINDOW SETUP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # ------------------------------------------------------------------
        self.root = root
        self.root.title("Dashboard")
        self.root.configure(bg="light gray")
        self.root.state("zoomed")        # maximise on Windows
      
        # ------------------------------------------------------------------
        # â”€â”€â”€ 2.  APPâ€‘WIDE STATE VARIABLES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # ------------------------------------------------------------------
        self.number_var  = tk.StringVar(value="NA")
        self.gender_var  = tk.StringVar(value="NA")
        self.pos_var     = tk.StringVar(value="NA")

        self.new_entries                   = []
        self.accumulated_pankti            = ""
        self.accumulated_meanings          = []
        self.accumulated_grammar_matches   = []
        self.accumulated_finalized_matches = []
        self.current_pankti                = ""
        self.match_vars                    = []
        self.all_matches                   = []
        self.all_new_entries               = []   # global accumulator

        # wordâ€‘byâ€‘word navigation
        self.current_word_index = 0
        self.pankti_words       = []

        # per-verse repeat-word note tracking
        self._repeat_note_shown = set()
        self._suppress_repeat_notes_for_verse = False
        self._use_inline_literal_banner = True
        self._always_show_literal_banner_frame = False
        self._last_literal_verse_key = None
        self._first_repeat_token = None
        self._last_dropdown_verse_key = None

        self._LITERAL_NOTE_TEXT = (
            "In literal analysis: This word appears multiple times in this verse. "
            "The highlighted grammar options reflect your past selections for this word "
            "(or close matches) to encourage consistency. Theyâ€™re suggestions, not mandatesâ€”"
            "adjust if the current context differs."
        )

        # ------------------------------------------------------------------
        # â”€â”€â”€ 3.  DATA LOAD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # ------------------------------------------------------------------
        self.grammar_data   = self.load_grammar_data("1.1.1_birha.csv")
        self.dictionary_data = pd.read_csv(
            "1.1.2 Grammatical Meanings Dictionary.csv",
            encoding="utf-8"
        )

        # ------------------------------------------------------------------
        # â”€â”€â”€ 4.  LAUNCH DASHBOARD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # ------------------------------------------------------------------
        self.show_dashboard()
    def _norm_get(self, d, key):
        """Unified getter that tolerates legacy field names."""
        if key == "\ufeffVowel Ending" or key == "Vowel Ending":
            return d.get("\ufeffVowel Ending") or d.get("Vowel Ending")
        if key == "Type" or key == "Word Type":
            return d.get("Type") or d.get("Word Type")
        return d.get(key)

    # TODO: Reuse in user_input(...) and prompt_save_results(...) for consistent comparisons.
    def _norm_tok(self, t: str) -> str:
        """Normalize token via NFC; drop dandas, zero-width spaces, ZWJ/ZWNJ, trailing digits & punctuation."""
        t = unicodedata.normalize("NFC", t.strip())
        t = re.sub(r"[à¥¤à¥¥]", "", t)  # danda/double-danda
        # remove ZERO WIDTH SPACE, ZWNJ, ZWJ
        t = t.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
        t = re.sub(r"[\d\u0A66-\u0A6F.,;:!?\"'â€”â€“-]+$", "", t)  # trailing digits (Latin+Gurmukhi) & punct
        return t

    def _verse_key(self, verse_text: str) -> str:
        """NFC + collapse spaces + remove danda variations; used for verse-scoped de-dupe keys."""
        cleaned = re.sub(r"[à¥¤à¥¥]", "", verse_text).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return unicodedata.normalize("NFC", cleaned)

    def _banner_wraplength(self, win=None) -> int:
        """Return a wraplength tuned to the window width (clamped 600â€“900)."""
        try:
            target = win or (self.match_window if hasattr(self, "match_window") else None)
            if target and target.winfo_exists():
                target.update_idletasks()
                w = target.winfo_width()
                return max(600, min(900, w - 120))
        except Exception:
            pass
        return 900

    def _modal_wraplength(self, win=None) -> int:
        """Return a wraplength tuned for the small modal (clamped 360â€“520)."""
        try:
            target = win or (self.root if hasattr(self, "root") else getattr(self, "match_window", None))
            if target and target.winfo_exists():
                target.update_idletasks()
                w = target.winfo_width()
                return max(360, min(520, w - 200))
        except Exception:
            pass
        return 400

    def _on_match_window_resize(self, event=None):
        """Resize handler to reflow the inline banner text, if present."""
        try:
            if hasattr(self, "literal_note_body") and self.literal_note_body and self.literal_note_body.winfo_exists():
                self.literal_note_body.config(wraplength=self._banner_wraplength(self.match_window))
        except Exception:
            pass

    def _ensure_literal_banner(self, text: str):
        """Create/reuse and render the inline literal-analysis banner."""
        reuse_ok = (
            hasattr(self, "literal_note_frame")
            and self.literal_note_frame
            and self.literal_note_frame.winfo_exists()
            and self.literal_note_frame.master is self.match_window
        )
        if not reuse_ok:
            if hasattr(self, "literal_note_frame") and getattr(self, "literal_note_frame", None):
                try:
                    if self.literal_note_frame.winfo_exists():
                        self.literal_note_frame.destroy()
                except Exception:
                    pass
            self.literal_note_frame = tk.Frame(
                self.match_window, bg="AntiqueWhite", relief="groove", bd=2
            )
            self.literal_note_title = tk.Label(
                self.literal_note_frame,
                text="Important Note â€” Literal Analysis",
                bg="AntiqueWhite",
                font=("Arial", 14, "bold"),
            )
            self.literal_note_title.pack(anchor="w", padx=10, pady=(5, 0))
            self.literal_note_body = tk.Label(
                self.literal_note_frame,
                bg="AntiqueWhite",
                wraplength=self._banner_wraplength(self.match_window),
                justify=tk.LEFT,
                font=("Arial", 12),
            )
        if not self.literal_note_frame.winfo_ismapped():
            self.literal_note_frame.pack(fill=tk.X, padx=20, pady=(5, 10))
        if not self.literal_note_body.winfo_ismapped():
            self.literal_note_body.pack(anchor="w", padx=10, pady=(0, 5))
        self.literal_note_body.config(
            text=text, wraplength=self._banner_wraplength(self.match_window)
        )
        try:
            if not getattr(self, "_inline_resize_bound", False):
                self.match_window.bind("<Configure>", self._on_match_window_resize, add="+")
                self._inline_resize_bound = True
        except Exception:
            pass

    def _has_repeat(self, norm_words, norm_target: str) -> bool:
        """Return True iff *norm_target* appears at least twice in ``norm_words``.

        ``norm_words`` is expected to be a list of pre-normalized tokens so this
        helper can operate without re-normalizing each time it is called.
        """
        if not norm_target:
            return False
        return norm_words.count(norm_target) >= 2

    def _maybe_show_repeat_important_note(self, word, occurrence_idx, verse_norm):
        """Show an explanatory note for repeated words within a verse."""
        if occurrence_idx < 1 or self._suppress_repeat_notes_for_verse:
            return
        norm_word = self._norm_tok(word)
        if not norm_word:
            return
        norm_verse = self._verse_key(verse_norm)
        key = (norm_verse, norm_word, "second")
        if key in self._repeat_note_shown:
            return
        self._repeat_note_shown.add(key)

        top = tk.Toplevel(self.root)
        top.title("Important Note â€” Literal Analysis")
        top.configure(bg='AntiqueWhite')
        top.transient(self.root)
        top.grab_set()

        body_lbl = tk.Label(
            top,
            text=self._LITERAL_NOTE_TEXT,
            bg='AntiqueWhite',
            wraplength=self._modal_wraplength(top),
            justify=tk.LEFT,
            font=('Arial', 12)
        )
        body_lbl.pack(padx=20, pady=(15,5))
        # Reflow text on modal resize
        try:
            top.bind("<Configure>", lambda e: body_lbl.config(wraplength=self._modal_wraplength(top)))
        except Exception:
            pass

        dont_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            top,
            text="Don't show again for this verse",
            variable=dont_var,
            bg='AntiqueWhite',
            font=('Arial', 11)
        ).pack(pady=(0,10))

        def _commit_and_close():
            try:
                if dont_var.get():
                    self._suppress_repeat_notes_for_verse = True
            except Exception:
                pass
            top.destroy()

        ok_btn = tk.Button(
            top,
            text="OK",
            command=_commit_and_close,
            font=('Arial', 12, 'bold'),
            bg='navy',
            fg='white',
            padx=10,
            pady=5
        )
        ok_btn.pack(pady=(0,15))
        try:
            ok_btn.focus_set()
            top.bind("<Return>", lambda e: _commit_and_close(), add="+")
            top.bind("<Escape>", lambda e: _commit_and_close(), add="+")
        except Exception:
            pass

        def _on_close():
            _commit_and_close()
        top.protocol("WM_DELETE_WINDOW", _on_close)

        top.update_idletasks()
        w, h = top.winfo_width(), top.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() - w)//2
        y = self.root.winfo_y() + (self.root.winfo_height() - h)//2
        top.geometry(f"{w}x{h}+{x}+{y}")
        top.wait_window()

    def show_dashboard(self):
        """Creates the dashboard interface directly in the main root window."""
        # Clear any existing widgets from the root
        for widget in self.root.winfo_children():
            widget.destroy()

        # Set up the dashboard appearance in the root window
        self.root.title("Dashboard")
        self.root.configure(bg='light gray')
        self.root.state("zoomed")  # Maximize the window

        # Dashboard header label
        header = tk.Label(
            self.root,
            text="Welcome to Gurbani Software Dashboard",
            font=('Arial', 18, 'bold'),
            bg='dark slate gray',
            fg='white'
        )
        header.pack(fill=tk.X, pady=20)

        # Create a frame to hold dashboard buttons
        button_frame = tk.Frame(self.root, bg='light gray')
        button_frame.pack(expand=True)

        # New Button to open the Verse Analysis Dashboard
        verse_analysis_btn = tk.Button(
            button_frame,
            text="Verse Analysis Dashboard",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_verse_analysis_dashboard
        )
        verse_analysis_btn.pack(pady=10)

        # Button to open the Grammarâ€‘DB Update window
        grammar_update_btn = tk.Button(
            button_frame,
            text="Grammar DB Update",
            font=('Arial', 14, 'bold'),
            bg='teal',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_grammar_update_dashboard
        )
        grammar_update_btn.pack(pady=10)

        # Placeholder for future features (e.g., Grammar Correction)
        future_btn = tk.Button(
            button_frame,
            text="Upcoming Feature: Grammar Correction",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        future_btn.pack(pady=10)

        # What's New / Releases button
        whats_new_btn = tk.Button(
            button_frame,
            text="What's New",
            font=('Arial', 12, 'bold'),
            bg='#2f4f4f',
            fg='white',
            padx=16,
            pady=8,
            command=self.show_whats_new
        )
        whats_new_btn.pack(pady=(20, 10))

        # One-time prompt to announce recent UI changes
        try:
            self.root.after(800, self.maybe_prompt_whats_new)
        except Exception:
            pass

    def show_whats_new(self):
        """Display a small dialog with links to the latest UI updates and releases."""
        win = tk.Toplevel(self.root)
        win.title("What's New")
        win.configure(bg='light gray')
        win.transient(self.root)
        try:
            win.grab_set()
        except Exception:
            pass

        header = tk.Label(
            win,
            text="What's New",
            font=('Arial', 16, 'bold'),
            bg='dark slate gray',
            fg='white',
            pady=8
        )
        header.pack(fill=tk.X)

        body = tk.Frame(win, bg='light gray')
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(
            body,
            text=(
                "Recent UI improvements: two-column card parity in matches view, "
                "centered layout, equal column widths, radios never overlap text, and a centered final "
                "card without stretching when there's an odd number of results."
            ),
            font=('Arial', 12),
            bg='light gray',
            wraplength=800,
            justify='left'
        ).pack(anchor='w', pady=(0, 10))

        links = tk.Frame(body, bg='light gray')
        links.pack(anchor='w', pady=(0, 8))

        def link(label_parent, text, url):
            lbl = tk.Label(
                label_parent,
                text=text,
                font=('Arial', 12, 'underline'),
                fg='blue',
                bg='light gray',
                cursor='hand2'
            )
            lbl.pack(anchor='w', pady=2)
            lbl.bind('<Button-1>', lambda e: webbrowser.open(url))

        link(links, f"View UI tag: {WHATS_NEW_ID}",
             f"https://github.com/vije1711/Birha/tree/{WHATS_NEW_ID}")
        link(links, 'All Releases', 'https://github.com/vije1711/Birha/releases')

        btns = tk.Frame(win, bg='light gray')
        btns.pack(fill=tk.X, padx=20, pady=(0, 16))
        tk.Button(
            btns,
            text='Close',
            font=('Arial', 12, 'bold'),
            bg='gray', fg='white',
            padx=16, pady=6,
            command=win.destroy
        ).pack(side=tk.RIGHT)

        # Center over root
        win.update_idletasks()
        try:
            w, h = win.winfo_width(), win.winfo_height()
            x = self.root.winfo_x() + (self.root.winfo_width() - w)//2
            y = self.root.winfo_y() + (self.root.winfo_height() - h)//2
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    # ---------------------------
    # One-time "What's New" helpers
    # ---------------------------
    def _state_file_path(self):
        try:
            base = os.path.join(os.path.expanduser("~"), ".birha")
            os.makedirs(base, exist_ok=True)
            return os.path.join(base, "state.json")
        except Exception:
            # Fallback to current working directory if home is not accessible
            return os.path.join(os.getcwd(), ".birha_state.json")

    def _load_state(self):
        path = self._state_file_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self, state: dict):
        path = self._state_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except Exception:
            pass

    def maybe_prompt_whats_new(self):
        # Avoid multiple prompts per session
        if getattr(self, "_whats_new_checked", False):
            return
        self._whats_new_checked = True

        state = self._load_state()
        if state.get("last_whats_new") != WHATS_NEW_ID:
            # Ask the user if they'd like to view details, then record as shown
            self.root.after(100, lambda: self._do_prompt_whats_new_fixed(state))

    def _do_prompt_whats_new(self, state: dict):
        try:
            if messagebox.askyesno(
                "Whatâ€™s New",
                (
                    "Weâ€™ve improved verse selection cards: centered layout, equal column widths, "
                    "and radios no longer overlap text. View details now?"
                ),
            ):
                self.show_whats_new()
        finally:
            try:
                state["last_whats_new"] = WHATS_NEW_ID
                self._save_state(state)
            except Exception:
                pass
        return

        header = tk.Label(
            win,
            text="What's New",
            font=('Arial', 16, 'bold'),
            bg='dark slate gray',
            fg='white',
            pady=8
        )
        header.pack(fill=tk.X)

        body = tk.Frame(win, bg='light gray')
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(
            body,
            text=(
                "Recent UI improvements: two-column card parity in matches view, "
                "centered layout, equal column widths, radios never overlap text, and a centered final "
                "card without stretching when thereâ€™s an odd number of results."
            ),
            font=('Arial', 12),
            bg='light gray',
            wraplength=800,
            justify='left'
        ).pack(anchor='w', pady=(0, 10))

        links = tk.Frame(body, bg='light gray')
        links.pack(anchor='w', pady=(0, 8))

        def link(label_parent, text, url):
            lbl = tk.Label(
                label_parent,
                text=text,
                font=('Arial', 12, 'underline'),
                fg='blue',
                bg='light gray',
                cursor='hand2'
            )
            lbl.pack(anchor='w', pady=2)
            lbl.bind('<Button-1>', lambda e: webbrowser.open(url))

        link(links, f"View UI tag: {WHATS_NEW_ID}",
             f"https://github.com/vije1711/Birha/tree/{WHATS_NEW_ID}")
        link(links, 'All Releases', 'https://github.com/vije1711/Birha/releases')

        btns = tk.Frame(win, bg='light gray')
        btns.pack(fill=tk.X, padx=20, pady=(0, 16))
        tk.Button(
            btns,
            text='Close',
            font=('Arial', 12, 'bold'),
            bg='gray', fg='white',
            padx=16, pady=6,
            command=win.destroy
        ).pack(side=tk.RIGHT)

        # Center over root
        win.update_idletasks()
        try:
            w, h = win.winfo_width(), win.winfo_height()
            x = self.root.winfo_x() + (self.root.winfo_width() - w)//2
            y = self.root.winfo_y() + (self.root.winfo_height() - h)//2
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def launch_grammar_update_dashboard(self):
        win = tk.Toplevel(self.root)
        win.title("Grammar Database Update")
        win.configure(bg='#e0e0e0')  # light neutral background
        win.state("zoomed")

        # â€” Header Bar â€”
        header = tk.Frame(win, bg='#2f4f4f', height=60)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Grammar Database Update",
            font=('Arial', 20, 'bold'),
            bg='#2f4f4f',
            fg='white'
        ).place(relx=0.5, rely=0.5, anchor='center')

        # â€” Separator â€”
        sep = tk.Frame(win, bg='#cccccc', height=2)
        sep.pack(fill=tk.X)

        # â€” Navigation Buttons â€”
        nav = tk.Frame(win, bg='#e0e0e0')
        nav.pack(pady=30)
        btn_kwargs = dict(
            font=('Arial', 14, 'bold'),
            width=20,
            padx=10, pady=10,
            relief='flat',
            activebackground='#007d7d',
            bg='#008c8c', fg='white'
        )

        btn_verse = tk.Button(
            nav, text="Assess by Verse", **btn_kwargs,
            command=self.launch_verse_assessment
        )
        btn_verse.grid(row=0, column=0, padx=20)

        btn_word = tk.Button(
            nav, text="Assess by Word (coming soon)", **btn_kwargs,
            state=tk.DISABLED, disabledforeground='#666666'
        )
        btn_word.grid(row=0, column=1, padx=20)

        # â€” Instruction / Description â€”
        instr = (
            "Choose â€œAssess by Verseâ€ to look up verses and refine grammar entries.\n"
            "The â€œAssess by Wordâ€ workflow is coming in the next release."
        )
        tk.Label(
            win, text=instr,
            font=('Arial', 16),
            bg='#e0e0e0', fg='#333333',
            justify='center', wraplength=800
        ).pack(pady=20)

        # â€” Bottom Back Button â€”
        bottom = tk.Frame(win, bg='#e0e0e0')
        bottom.pack(side=tk.BOTTOM, pady=30)
        back_btn = tk.Button(
            bottom,
            text="â† Back to Dashboard",
            font=('Arial', 14),
            bg='#2f4f4f', fg='white',
            activebackground='#3f6f6f',
            padx=20, pady=10,
            command=self.show_dashboard
        )
        back_btn.pack()

        # Optional: make ESC key close this window
        win.bind("<Escape>", lambda e: win.destroy())

    def launch_verse_assessment(self):
        """Window for searching & selecting verses to assess grammar using a 2â€‘column card layout."""
        win = tk.Toplevel(self.root)
        win.title("Assess by Verse")
        win.configure(bg='light gray')
        win.state("zoomed")
        
        # â€” Optional pageâ€wide heading â€”
        tk.Label(
            win,
            text="Select a Verse to Refine Grammar Entries",
            font=("Arial", 20, "bold"),
            bg="dark slate gray",
            fg="white",
            pady=10
        ).pack(fill=tk.X)

        # keep track of which card is selected
        self._selected_verse_idx = tk.IntVar(value=-1)

        # â€” Top frame: entry + Search button â€”
        top = tk.Frame(win, bg='light gray')
        top.pack(fill=tk.X, padx=20, pady=15)
        tk.Label(top, text="Enter Verse:", font=("Arial", 16), bg='light gray').pack(side=tk.LEFT)
        self._verse_var = tk.StringVar()
        tk.Entry(top, textvariable=self._verse_var, font=("Arial", 16))\
        .pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,10))
        tk.Button(
            top, text="Search", font=("Arial", 16, "bold"),
            bg='dark cyan', fg='white',
            command=self._populate_cards
        ).pack(side=tk.LEFT)

        # â€” Middle frame: scrollable canvas + 2â€‘column grid of â€œcardsâ€ â€”
        middle = tk.Frame(win, bg='light gray')
        middle.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(middle, bg='light gray', highlightthickness=0)
        vsb    = tk.Scrollbar(middle, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # This frame goes inside the canvas and will hold our cards
        self._cards_frame = tk.Frame(canvas, bg='light gray')

        # create_window with anchor="n" so its x coordinate is the top-center of cards_frame
        cards_window = canvas.create_window((0, 0), window=self._cards_frame, anchor="n")

        # configure two equalâ€‘weight columns for 2â€‘column layout
        self._cards_frame.grid_columnconfigure(0, weight=1, minsize=450)
        self._cards_frame.grid_columnconfigure(1, weight=1, minsize=450)

        # keep scrollregion up to date
        def _on_cards_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._cards_frame.bind("<Configure>", _on_cards_configure)

        # **New:** whenever the canvas resizes, recenter cards_frame horizontally
        def _on_canvas_resize(event):
            canvas.coords(cards_window, event.width // 2, 0)
        canvas.bind("<Configure>", _on_canvas_resize)

        # â€” Bottom frame: navigation buttons â€”
        bottom = tk.Frame(win, bg='light gray')
        bottom.pack(fill=tk.X, padx=20, pady=15)
        tk.Button(
            bottom, text="â€¹ Back", font=("Arial", 14),
            bg='gray', fg='white', command=win.destroy
        ).pack(side=tk.LEFT)
        tk.Button(
            bottom, text="Back to Dashboard", font=("Arial", 14),
            bg='gray', fg='white', command=self.show_dashboard
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            bottom, text="Next â†’", font=("Arial", 14, "bold"),
            bg='dark cyan', fg='white',
            command=lambda: self.proceed_to_word_assessment(self._selected_verse_idx.get())
        ).pack(side=tk.RIGHT)

    def _populate_cards(self):
        """Perform the verse search, filter & then render up to 10 cards in two columns."""
        # first, clear any existing cards
        for w in self._cards_frame.winfo_children():
            w.destroy()

        # Ensure equal column widths using a uniform group to avoid asymmetry
        try:
            self._cards_frame.grid_columnconfigure(0, weight=1, minsize=450, uniform='cards')
            self._cards_frame.grid_columnconfigure(1, weight=1, minsize=450, uniform='cards')
        except Exception:
            # Fallback in case uniform isn't supported, keep prior settings
            self._cards_frame.grid_columnconfigure(0, weight=1, minsize=450)
            self._cards_frame.grid_columnconfigure(1, weight=1, minsize=450)

        # 1) run search & filter
        query = self._verse_var.get().strip()
        headers, all_matches = self.match_sggs_verse(query)
        filtered = [m for m in all_matches if m.get("Score",0) >= 25.0][:10]
        # remember these for the â€œNext â†’â€ step
        self._last_filtered = filtered

        # reset selection
        self._selected_verse_idx.set(-1)

        # 2) render each card
        total_cards = len(filtered)
        for idx, m in enumerate(filtered):
            row, col = divmod(idx, 2)
            card = tk.Frame(
                self._cards_frame,
                bd=1,
                relief="solid",
                bg="white",
                padx=8,
                pady=8
            )
            # If odd number of cards and this is the last one, span both columns for visual centering
            if (total_cards % 2 == 1) and (idx == total_cards - 1):
                # Do not stretch the final full-width card; keep it centered with natural width
                card.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="n")
            else:
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # the verse itself, wrapped
            tk.Label(
                card,
                text=m.get("Verse","").strip(),
                font=("Arial", 14, "bold"),
                wraplength=500,
                justify="center",
                bg="white"
            ).pack(pady=(14,4), padx=(28,8))

            # a little radiobutton at top-left for selection (created after the label and raised)
            rb = tk.Radiobutton(
                card,
                variable=self._selected_verse_idx,
                value=idx,
                bg="white",
                activebackground="white"
            )
            rb.place(x=6, y=6)
            try:
                rb.lift()
            except Exception:
                pass

            # metadata line
            # build a list of (label, key) pairs
            fields = [
                ("Raag",   "Raag (Fixed)"),
                ("Writer", "Writer (Fixed)"),
                ("Bani",   "Bani Name"),
                ("Page",   "Page Number"),
            ]

            meta_parts = []
            for label, key in fields:
                v = m.get(key)
                # skip if missing or NaN
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    continue
                meta_parts.append(f"{label}: {v}")

            # always include the match%
            meta_parts.append(f"Match: {m.get('Score',0):.1f}%")

            # join with separators
            meta = "   |   ".join(meta_parts)

            tk.Label(
                card,
                text=meta,
                font=("Arial", 12),
                bg="white"
            ).pack()

        # 3) force a canvas update of its scroll region
        self._cards_frame.update_idletasks()
        self._cards_frame.master.configure(
            scrollregion=self._cards_frame.master.bbox("all")
        )

    def show_translation_input(self):
        win = tk.Toplevel(self.root)
        win.title("Paste Darpan Translation")
        win.configure(bg='light gray')
        # bump default size up so buttons are always visible
        win.state("zoomed")
        win.transient(self.root)
        win.grab_set()

        # â€” Heading â€”
        tk.Label(
            win,
            text=self.selected_verse_text,
            font=("Arial", 20, "bold"),
            bg="light gray",
            wraplength=900,
            justify="center",
            pady=10
        ).pack(fill=tk.X, padx=20, pady=(15,10))

        # â€” Translation area â€”
        tf = tk.LabelFrame(
            win,
            text="Established Darpan Translation",
            font=("Arial", 14, "bold"),
            bg='light gray',
            fg='black',
            padx=10, pady=10
        )
        tf.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0,15))

        self._translation_text = tk.Text(
            tf, wrap=tk.WORD, font=("Arial", 13),
            height=8, padx=5, pady=5
        )
        self._translation_text.pack(fill=tk.BOTH, expand=False)

        # Status + Refresh row under the translation box
        status_row = tk.Frame(tf, bg='light gray')
        status_row.pack(fill=tk.X, pady=(6, 0))
        self._translation_status_var = tk.StringVar(value="")
        tk.Label(
            status_row,
            textvariable=self._translation_status_var,
            font=("Arial", 10, "italic"),
            bg='light gray', fg='#333333'
        ).pack(side=tk.LEFT)
        # Strictness toggle
        self._translation_strict_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            status_row,
            text="Strict (verse + page only)",
            variable=self._translation_strict_var,
            bg='light gray',
            font=("Arial", 10),
            command=self._on_strict_toggle
        ).pack(side=tk.LEFT, padx=(10, 0))
        # Why didn't this match? diagnostics
        tk.Button(
            status_row,
            text="Why?",
            font=("Arial", 10),
            bg='#666666', fg='white',
            command=self._show_translation_match_diagnostics
        ).pack(side=tk.LEFT, padx=(6, 0))
        tk.Button(
            status_row,
            text="Refresh from data files",
            font=("Arial", 10),
            bg='gray', fg='white',
            command=self._refresh_translation_from_data
        ).pack(side=tk.RIGHT)

        # Try to auto-populate translation from structured sources
        filled, status = self._populate_translation_from_structured()
        self._translation_status_var.set(status)

        # â€” Wordâ€selection area â€”
        wf = tk.LabelFrame(
            win,
            text="Select Words to Assess Grammar",
            font=("Arial", 14, "bold"),
            bg='light gray',
            fg='black',
            padx=10, pady=10
        )
        wf.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0,15))

        # select/deselect all
        self._select_all_words_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            wf,
            text="Select/Deselect All Words",
            variable=self._select_all_words_var,
            bg="light gray",
            font=("Arial", 12, "italic"),
            command=self._toggle_all_word_selection
        ).pack(anchor="w", pady=(0,10))

        # scrollable word grid
        canvas = tk.Canvas(wf, bg='light gray', highlightthickness=0)
        scrollbar = tk.Scrollbar(wf, orient="vertical", command=canvas.yview)
        word_frame = tk.Frame(canvas, bg='light gray')
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=False)
        canvas.create_window((0,0), window=word_frame, anchor="nw")

        def _on_wf_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        word_frame.bind("<Configure>", _on_wf_resize)

        # lay out each word
        self._word_selection_vars = []

        # 1) grab the verse text, remove any trailing danda symbols:
        verse_text = self.selected_verse_text.strip().rstrip('à¥¥ ').strip()

        # 2) split into words (now â€œà¥¥â€ wonâ€™t appear as its own token)
        words = verse_text.split()

        # 3) build your checkboxes off `words` instead of the raw text:
        for i, w in enumerate(words):
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(
                word_frame,
                text=w,
                variable=var,
                bg='light gray',
                font=('Arial', 12),
                wraplength=120,
                anchor='w',
                justify='left'
            )
            chk.grid(row=i//4, column=i%4, sticky='w', padx=5, pady=3)
            self._word_selection_vars.append((var, w))

        # â€” Bottom buttons â€”
        btn_frame = tk.Frame(win, bg="light gray")
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(
            btn_frame,
            text="â† Back to Verse Search",
            font=("Arial", 12),
            bg="gray",
            fg="white",
            command=win.destroy,
            padx=15, pady=8
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame,
            text="Submit Translation â†’",
            font=("Arial", 12, "bold"),
            bg="dark cyan",
            fg="white",
            command=lambda: self._on_translation_submitted(win),
            padx=15, pady=8
        ).pack(side=tk.RIGHT)

    def _populate_translation_from_structured(self):
        """Attempt to fill the translation Text from structured JSON/CSV.
        Returns (filled: bool, status: str)."""
        try:
            meta = getattr(self, 'selected_verse_meta', {}) or {}
            verse_text = self.selected_verse_text if hasattr(self, 'selected_verse_text') else ''
            page_num = meta.get('Page Number')
            strict = bool(getattr(self, '_translation_strict_var', tk.BooleanVar(value=False)).get())
            found = _find_arth_for(self, verse_text, page_num, strict=strict)
            if not found:
                return False, ("No structured data match found (strict)" if strict else "Manual input")
            record, info = found
            parts = []
            v = record.get('verse') or record.get('Verse') or ''
            if v:
                parts.append("Verse:\n" + str(v).strip())
            p = record.get('padarth') or record.get('Padarth') or ''
            if p:
                parts.append("Padarth:\n" + str(p).strip())
            a = record.get('arth') or record.get('Arth') or ''
            if a:
                parts.append("Arth:\n" + str(a).strip())
            ch = record.get('chhand') or record.get('Chhand') or ''
            if ch:
                parts.append("Chhand:\n" + str(ch).strip())
            bh = record.get('bhav') or record.get('Bhav') or ''
            if bh:
                parts.append("Bhav:\n" + str(bh).strip())
            if not parts:
                return False, ("No structured data content available" if strict else "Manual input")
            self._translation_text.delete('1.0', tk.END)
            self._translation_text.insert('1.0', "\n\n".join(parts) + "\n")
            # Build status
            src = info.get('source') if isinstance(info, dict) else None
            match = info.get('match') if isinstance(info, dict) else None
            score = info.get('score') if isinstance(info, dict) else None
            if match == 'fuzzy' and score is not None:
                status = f"Auto-filled (fuzzy {int(score)}) from {src}" if src else f"Auto-filled (fuzzy {int(score)})"
            elif match in ('exact', 'exact+page'):
                label = 'exact + page' if match == 'exact+page' else 'exact'
                status = f"Auto-filled ({label}) from {src}" if src else f"Auto-filled ({label})"
            else:
                status = "Auto-filled from structured data"
            return True, status
        except Exception:
            return False, "Manual input"

    def _refresh_translation_from_data(self):
        """Handler for the Refresh button to try loading from data files again."""
        filled, status = self._populate_translation_from_structured()
        if hasattr(self, '_translation_status_var'):
            self._translation_status_var.set(status)

    def _on_strict_toggle(self):
        # Re-attempt population whenever strictness is toggled
        self._refresh_translation_from_data()

    def _gather_translation_diagnostics(self, top_n=10):
        try:
            _load_arth_sources_once(self)
            if not getattr(self, '_arth_records', None):
                return False, "No structured data loaded.", []
            verse_text = getattr(self, 'selected_verse_text', '') or ''
            meta = getattr(self, 'selected_verse_meta', {}) or {}
            target_page = _parse_page_value(meta.get('Page Number'))
            key = _normalize_verse_key(verse_text)
            rows = []
            for rec in self._arth_records:
                rec_key = rec.get('norm_excel_key') or ''
                score = fuzz.token_sort_ratio(key, rec_key)
                page_ok = (target_page is not None and rec.get('norm_page') == target_page)
                # small preference boost for page match
                disp_score = score + (5 if page_ok else 0)
                preview = str(rec.get('verse') or rec.get('excel_verses') or '')
                preview = preview.replace('\n', ' ').strip()
                if len(preview) > 140:
                    preview = preview[:137] + '...'
                rows.append({
                    'score': disp_score,
                    'raw_score': score,
                    'page': rec.get('norm_page'),
                    'page_match': bool(page_ok),
                    'source': rec.get('source'),
                    'preview': preview,
                })
            rows.sort(key=lambda r: r['score'], reverse=True)
            return True, f"Target page={target_page or 'NA'}", rows[:top_n]
        except Exception as e:
            return False, f"Error: {e}", []

    def _show_translation_match_diagnostics(self):
        ok, info, rows = self._gather_translation_diagnostics(top_n=12)
        win = tk.Toplevel(self.root)
        win.title("Translation Match Diagnostics")
        win.configure(bg='light gray')
        tk.Label(
            win,
            text=f"Diagnostics — {info}",
            font=("Arial", 12, "bold"),
            bg='dark slate gray', fg='white', pady=6
        ).pack(fill=tk.X)

        body = tk.Frame(win, bg='light gray')
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        txt = scrolledtext.ScrolledText(body, wrap=tk.WORD, font=("Consolas", 11), height=12)
        txt.pack(fill=tk.BOTH, expand=True)

        lines = []
        if not ok:
            lines.append(info)
        else:
            # Target info
            verse_text = getattr(self, 'selected_verse_text', '') or ''
            meta = getattr(self, 'selected_verse_meta', {}) or {}
            target_page = _parse_page_value(meta.get('Page Number'))
            lines.append(f"Target verse: {verse_text}")
            lines.append(f"Target page: {target_page or 'NA'}")
            lines.append("")
            lines.append("Top candidates:")
            for i, r in enumerate(rows, 1):
                pm = '✓' if r['page_match'] else ' '
                src = r.get('source') or 'unknown'
                lines.append(f"{i:2}. score={int(r['score'])} (raw={int(r['raw_score'])}) page={r['page'] or 'NA'}{('*' if r['page_match'] else '')} src={src}")
                lines.append(f"    {r['preview']}")
        txt.insert('1.0', "\n".join(lines))
        txt.config(state=tk.DISABLED)

        btns = tk.Frame(win, bg='light gray')
        btns.pack(fill=tk.X, padx=12, pady=(6, 10))
        def copy_diag():
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(lines))
            messagebox.showinfo("Copied", "Diagnostics copied to clipboard.")
        tk.Button(btns, text="Copy", command=copy_diag, bg="#007acc", fg="white", font=("Arial", 10, "bold"), padx=10, pady=4).pack(side=tk.LEFT)
        tk.Button(btns, text="Close", command=win.destroy, bg="gray", fg="white", font=("Arial", 10, "bold"), padx=10, pady=4).pack(side=tk.RIGHT)

    def proceed_to_word_assessment(self, idx):
        # grab the metadata dict from the last search
        self.selected_verse_meta = self._last_filtered[idx]
        self.selected_verse_text = self.selected_verse_meta["Verse"]
        # now pop up the translationâ€paste window
        self.show_translation_input()

    def process_next_word_assessment(self):
        if self.current_queue_pos >= len(self.grammar_queue):
            return self.finish_and_prompt_save()

        idx, word = self.grammar_queue[self.current_queue_pos]
        self.current_word_index = idx
        self.user_input_grammar(word, self.current_translation, idx)

    def _on_translation_submitted(self, win):
        # 1) grab and validate the translation itself
        text = self._translation_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Translation", "Please paste a translation before submitting.")
            return
        self.current_translation = text

        # 2) capture exactly which indices the user checked
        #    (you built self._word_selection_vars = [(var, word), ...] in show_translation_input)
        selected_idxs = [
            idx for idx, (var, _) in enumerate(self._word_selection_vars)
            if var.get()
        ]
        if not selected_idxs:
            messagebox.showwarning("Nothing Selected", "Please select at least one word to assess.")
            return
        self._selected_word_indices = selected_idxs

        # 3) tear down and hand off to your queue initializer
        win.destroy()
        self.initialize_grammar_queue()
        # â† NO MORE direct call to process_next_word_assessment() here,
        #     initialize_grammar_queue() will immediately invoke it.

    def initialize_grammar_queue(self):
        """
        After the user has pasted their translation, split the verse
        into words and build the queue of those words the user selected
        for grammar assessment. Then immediately start the first word.
        """
        # split the verse text
        words = self.selected_verse_text.strip().split()

        # collect exactly those indices the user checked in show_translation_input()
        # (you should have created a tk.BooleanVar list self._word_vars there)
        selected_indices = self._selected_word_indices

        # build the queue
        self.grammar_queue = [
            (i, words[i]) for i in selected_indices
        ]
        self.grammar_meanings = []        # â† NEW: clear out any old entries
        self.current_queue_pos = 0

        if not self.grammar_queue:
            messagebox.showinfo("Nothing Selected",
                "You didnâ€™t select any words for grammar assessment.")
            return

        # **IMMEDIATELY** start your per-word flow
        self.process_next_word_assessment()

    def _toggle_all_word_selection(self):
        """Called by the top â€˜Select/Deselect All Wordsâ€™ checkbox."""
        val = self._select_all_words_var.get()
        for var, _ in getattr(self, "_word_selection_vars", []):
            var.set(val)

    def user_input_grammar(self, word, translation, index):
        """
        Pop up a window to collect grammar info for one word:
        - shows full verse with the `index`th word highlighted
        - shows the Darpan translation
        - left pane: dictionary meanings
        - right pane: Number/Gender/POS radio buttons + Expert-Prompt button
        - bottom row: Back / Skip / Submit
        """
        win = tk.Toplevel(self.root)
        win.title(f"Assess Grammar: {word}")
        win.configure(bg='light gray')
        # give a reasonable size so buttons show up
        win.state("zoomed")
        win.resizable(True, True)

        # 1) Verse display + highlight
        vf = tk.Frame(win, bg='light gray')
        vf.pack(fill=tk.X, padx=20, pady=(20,10))
        td = tk.Text(vf, wrap=tk.WORD, bg='light gray',
                     font=('Arial', 24), height=1, bd=0)
        td.pack(fill=tk.X)
        td.insert('1.0', self.selected_verse_text)
        td.tag_add('center', '1.0', 'end')
        td.tag_configure('center', justify='center')
        # highlight the word
        words = self.selected_verse_text.split()
        start = sum(len(w)+1 for w in words[:index])
        end   = start + len(words[index])
        td.tag_add('highlight', f'1.{start}', f'1.{end}')
        td.tag_configure('highlight',
                         font=('Arial',24,'bold'),
                         foreground='blue')
        td.config(state=tk.DISABLED)

        # 2) Translation LabelFrame
        tf = tk.LabelFrame(win, text="Darpan Translation",
                           font=('Arial',16,'bold'),
                           bg='light gray', fg='black',
                           padx=10, pady=10)
        tf.pack(fill=tk.BOTH, padx=20, pady=(0,15))
        trans = tk.Text(tf, wrap=tk.WORD, font=('Arial',14),
                        height=2, bd=0)
        trans.insert('1.0', translation)
        trans.config(state=tk.DISABLED)
        trans.pack(fill=tk.BOTH, expand=False)

        # Prepare vars for grammar options
        # Default to â€œUnknownâ€ (NA)
        self.number_var = tk.StringVar(value="NA")
        self.gender_var = tk.StringVar(value="NA")
        self.pos_var    = tk.StringVar(value="NA")

        # 3+4) Split pane: left=meanings, right=options
        split = tk.PanedWindow(win, orient=tk.HORIZONTAL, bg='light gray')
        split.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0,15))

        # â€” Left: Dictionary Meanings in 5 columns with scrollbar â€”
        left = tk.LabelFrame(split,
                            text=f"Meanings for â€œ{word}â€",
                            font=('Arial',16,'bold'),
                            bg='light gray', fg='black',
                            padx=10, pady=10)

        self.meanings_canvas = tk.Canvas(left, bg='light gray', borderwidth=0)
        scrollbar = tk.Scrollbar(left, orient=tk.VERTICAL, command=self.meanings_canvas.yview)
        self.meanings_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.meanings_canvas.pack(side='left', fill='both', expand=True)
        self.meanings_inner_frame = tk.Frame(self.meanings_canvas, bg='light gray')
        self.meanings_canvas.create_window((0,0), window=self.meanings_inner_frame, anchor='nw')

        def _on_meanings_configure(evt):
            self.meanings_canvas.configure(scrollregion=self.meanings_canvas.bbox("all"))
        self.meanings_inner_frame.bind("<Configure>", _on_meanings_configure)

        split.add(left, stretch="always")

        self.current_word = word   # â† NEW: remember which word weâ€™re looking up
        threading.Thread(
            target=lambda: self.lookup_grammar_meanings_thread(word),
            daemon=True
        ).start()


        # â€” Right: Grammar Options + Expert Prompt â€”
        right = tk.LabelFrame(split,
                            text="Select Grammar Options",
                            font=("Arial", 16, "bold"),
                            bg="light gray", fg="black",
                            padx=10, pady=10)
        split.add(right, stretch="never")

        # prepare your choices
        nums = [
            ("Singular", "Singular / à¨‡à¨•"),
            ("Plural",   "Plural / à¨¬à¨¹à©"),
            ("Unknown",  "NA")
        ]
        gends = [
            ("Masculine", "Masculine / à¨ªà©à¨²à¨¿à©°à¨—"),
            ("Feminine",  "Feminine / à¨‡à¨¸à¨¤à¨°à©€"),
            ("Neuter",    "Trans / à¨¨à¨ªà©à©°à¨¸à¨•"),
            ("Unknown",   "NA")
        ]
        pos_choices = [
            ("Noun",        "Noun / à¨¨à¨¾à¨‚à¨µ"),
            ("Adjective",   "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£"),
            ("Adverb",      "Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£"),
            ("Verb",        "Verb / à¨•à¨¿à¨°à¨¿à¨†"),
            ("Pronoun",     "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ"),
            ("Postposition","Postposition / à¨¸à©°à¨¬à©°à¨§à¨•"),
            ("Conjunction", "Conjunction / à¨¯à©‹à¨œà¨•"),
            ("Interjection", "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•"),
            ("Unknown",     "NA")
        ]

        # Number & Gender side-by-side
        frame_ng = tk.Frame(right, bg="light gray")
        frame_ng.pack(fill=tk.X)

        # Number frame in col0
        num_frame = tk.LabelFrame(frame_ng, text="Number",
                                font=("Arial", 14, "bold"),
                                bg="light gray", padx=8, pady=8)
        num_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        for txt, val in nums:
            tk.Radiobutton(
                num_frame, text=txt, variable=self.number_var, value=val,
                bg="light gray", font=("Arial", 12),
                anchor="w", justify="left"
            ).pack(anchor="w", pady=2)

        # Gender frame in col1, split into two columns
        gend_frame = tk.LabelFrame(frame_ng, text="Gender",
                                font=("Arial", 14, "bold"),
                                bg="light gray", padx=8, pady=8)
        gend_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # two sub-frames for the two columns
        gf_col1 = tk.Frame(gend_frame, bg="light gray")
        gf_col2 = tk.Frame(gend_frame, bg="light gray")
        gf_col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        gf_col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))

        # split the list in half
        half = (len(gends)+1)//2
        for i, (txt, val) in enumerate(gends):
            parent = gf_col1 if i < half else gf_col2
            tk.Radiobutton(
                parent, text=txt, variable=self.gender_var, value=val,
                bg="light gray", font=("Arial", 12),
                anchor="w", justify="left"
            ).pack(anchor="w", pady=2)

        # Part-of-Speech in two columns
        pos_frame = tk.LabelFrame(right, text="Part of Speech",
                                font=("Arial", 14, "bold"),
                                bg="light gray", padx=8, pady=8)
        pos_frame.pack(fill=tk.X, pady=5)

        # sub-frames for POS
        p1 = tk.Frame(pos_frame, bg="light gray")
        p2 = tk.Frame(pos_frame, bg="light gray")
        p1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        p2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))

        half_pos = (len(pos_choices)+1)//2
        for i, (txt, val) in enumerate(pos_choices):
            parent = p1 if i < half_pos else p2
            tk.Radiobutton(
                parent, text=txt, variable=self.pos_var, value=val,
                bg="light gray", font=("Arial", 12),
                anchor="w", justify="left"
            ).pack(anchor="w", pady=2)

        # Expert-prompt builder
        def ask_suggestion():
            verse = self.selected_verse_text
            trans = self.current_translation
            word  = self.current_word
            num   = self.number_var.get() or "â€“"
            gen   = self.gender_var.get() or "â€“"
            pos   = self.pos_var.get()    or "â€“"

            # --------------------------------------------------------------
            # Surface existing matches from the grammar database.  We mimic
            # perform_search_and_finish_reanalysis() to determine whether to
            # call search_by_criteria() or search_by_inflections().
            # --------------------------------------------------------------
            try:
                search_num = self.number_var.get()
                search_gen = self.gender_var.get()
                search_pos = self.pos_var.get()

                if (
                    search_num == "NA" and
                    search_gen == "NA" and
                    search_pos == "NA"
                ):
                    matches = self.search_by_inflections(word)
                else:
                    matches = self.search_by_criteria(
                        word, search_num, search_gen, search_pos
                    )
                    if not matches:
                        matches = self.search_by_inflections(word)

                rows = []
                for result, _count, _perc in matches[:5]:
                    parts = [p.strip() for p in result.split("|")]
                    if len(parts) < 7:
                        parts += [""] * (7 - len(parts))

                    highlight = parts[0] == parts[1] and is_full_word(parts[0])
                    if highlight:
                        parts = [f"**{p}**" for p in parts]
                        parts[0] = "âœ… " + parts[0]

                    rows.append(
                        "| "
                        + " | ".join(parts + [str(_count), f"{_perc:.1f}%"])
                        + " |"
                    )

                if rows:
                    headers = [
                        "Word under Analysis",
                        "Vowel Ending / Word Matches",
                        "Number / à¨µà¨šà¨¨",
                        "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
                        "Gender / à¨²à¨¿à©°à¨—",
                        "Word Root",
                        "Type",
                        "Match Count",
                        "Match %",
                    ]
                    table_lines = [
                        "**Top Grammar Matches**",
                        "| " + " | ".join(headers) + " |",
                        "| " + " | ".join(["---"] * len(headers)) + " |",
                        *rows,
                    ]
                    matches_block = "\n".join(table_lines)
                else:
                    matches_block = ""
            except Exception as exc:
                print(f"search for matches failed: {exc}")
                matches_block = ""

            # pull the meanings we stored for this word
            meanings = next(
                (e["meanings"] for e in self.grammar_meanings if e["word"] == word),
                []
            )
            meanings_block = "\n".join(f"- {m}" for m in meanings) or "- (no dictionary meanings found)"

            prompt = textwrap.dedent(f"""
            You are a Punjabi grammar expert trained in the grammatical framework of Sri Guru Granth Sahib (SGGS). I will provide:

            1. **Verse** (in Gurmukhi)  
            2. **Established Darpan Translation** (by Prof. Sahib Singh)  
            3. **Word under scrutiny**, along with my selected values for Number, Gender, and Part of Speech  
            4. **Dictionary Meanings** of that word (as a secondary reference)

            Your job is to confirm or correct my selections based on the **Darpan Translation and its contextual meaning**, which is the **primary reference**. Override my input only if the Darpan explanation makes it grammatically, semantically, or functionally incorrect within the SGGS grammatical framework.

           ---

            ## ðŸ”„ Two-Pass Analysis Workflow
            **Phase 1 â€“ Functional Tagging**  
            1 a. Locate every occurrence of the stem in the verse.  
            1 b. Assign provisional POS to each occurrence from context.  

            **Phase 2 â€“ Morphological Reconciliation**  
            2 a. Compare endings of all identical stems found in 1 a.  
            2 b. If endings differ â†’ mark the stem **declinable** and align each form with its noun/pronoun.  
            2 c. If endings never differ â†’ note â€œNo declension detected.â€  

            If Phase 2 detects a declinable pattern but any token fails to agree with its noun/pronoun, **STOP** and return â€œAgreement Error â€“ Review Needed.â€

            ---

            ## ðŸ“˜ Reference Framework â€“ SGGS Grammar Definitions

            ### ðŸ§© Implicit Case Logic in Gurbani Grammar
            Many case roles in SGGS are conveyed through **inflection or contextual meaning**, not modern postpositions. Refer to the gloss clues (â€œofâ€, â€œbyâ€, â€œwithâ€, etc.) to infer case correctly.

            ### 1. **Noun (à¨¨à¨¾à¨‚à¨µ)**  
            A noun is a word that names a person, place, thing, quality, or idea.

            #### ðŸ”¹ Types:
            - **Proper Noun (à¨µà¨¿à¨¸à¨¼à©‡à¨¸à¨¼ à¨¨à¨¾à¨‚à¨µ)** â€“ e.g., à¨—à©à¨°à©‚ à¨¨à¨¾à¨¨à¨•
            - **Common Noun (à¨¸à¨§à¨¾à¨°à¨¨ à¨¨à¨¾à¨‚à¨µ)** â€“ e.g., à¨ªà¨¾à¨£à©€, à¨°à©‹à¨Ÿà©€
            - **Abstract Noun (à¨­à¨¾à¨µ à¨¨à¨¾à¨‚à¨µ)** â€“ e.g., à¨ªà¨¿à¨†à¨°, à¨—à¨¿à¨†à¨¨
            - **Material Noun (à¨¦à©à¨°à¨µ à¨¨à¨¾à¨‚à¨µ)** â€“ e.g., à¨¸à©‹à¨¨à¨¾, à¨œà¨²
            - **Collective Noun (à¨¸à¨®à©‚à¨¹à¨• à¨¨à¨¾à¨‚à¨µ)** â€“ e.g., à¨¸à©°à¨—à¨¤, à¨«à©Œà¨œ

            #### ðŸ”¹ Cases in Gurbani Grammar:
            Nouns in Gurbani may appear in the following **grammatical cases** (*vibhakti*), sometimes **without explicit post-positions**:

            | Case         | Helper (Gloss Clue)             | Modern Marker    | When to Use                                                       |
            |--------------|----------------------------------|------------------|-------------------------------------------------------------------|
            | **Nominative**     | No helper, subject role         | None             | Default when noun is subject of verb                              |
            | **Accusative**     | No helper, object role          | None             | Default when noun is object of verb                               |
            | **Genitive**       | â€œofâ€, â€œà¨¦à©‡/à¨¦à©€/à¨¦à¨¾â€                | `à¨¦à©‡`, `à¨¦à©€`, `à¨¦à¨¾` | Use when gloss adds ownership/association                         |
            | **Instrumental**   | â€œbyâ€, â€œwithâ€, â€œunderâ€           | `à¨¨à¨¾à¨²`, `à¨…à¨§à©€à¨¨`     | Use when gloss suggests means/manner (even if unstated in verse)  |
            | **Dative**         | â€œtoâ€, â€œforâ€                     | `à¨¨à©‚à©°`, `à¨²à¨ˆ`       | When gloss implies recipient/beneficiary                          |
            | **Locative**       | â€œinâ€, â€œonâ€, â€œatâ€                | `à¨µà¨¿à©±à¨š`, `à¨¤à©‡`      | When gloss places noun in space/context                           |
            | **Ablative**       | â€œfromâ€, â€œout ofâ€                | `à¨¤à©‹à¨‚`, `à¨‰à¨¤à©‹à¨‚`      | When gloss implies source                                         |
            | **Vocative**       | â€œOâ€, â€œHeyâ€                      | *(address)*       | Used for direct address (e.g., *à¨¹à©‡ à¨­à¨¾à¨ˆ!*)                          |

            > ðŸ”¸ **Implicit Post-Positions:** If Darpan adds â€œà¨¨à¨¾à¨², à¨¦à©‡, à¨µà¨¿à©±à¨š, à¨¤à©‹à¨‚â€ etc., treat it as a **helper** for inferring the nounâ€™s **grammatical case**, even if the verse lacks a marker.
            >
            > ðŸ”¸ **Indeclinable Loan Nouns:** Sanskrit-based nouns (like *à¨¬à¨¿à¨§à¨¿*, *à¨®à¨¤à©€*) may not show visible inflection. Their case must be inferred from semantic role and Darpan gloss, not suffix alone.

            > ðŸ”¹ **Fallback Rule:**  
            > When the gloss offers no helper and the noun does not visibly decline, default to **Nominative or Accusative**, then refine based on sentence structure and implied role in the Darpan explanation.

            ### 2. **Pronoun (à¨ªà©œà¨¨à¨¾à¨‚à¨µ)**  
            Used in place of nouns. Types include:  
            - **Personal**, **Demonstrative**, **Reflexive**, **Possessive**, **Relative**, **Indefinite**, **Interrogative**

            ### 3. **Adjective (à¨µà¨¿à¨¸à¨¼à©‡à¨¸à¨¼à¨£) â€“ Agreement Framework**
            Describes or qualifies a noun or pronoun only. Must be directly linked to one.  
            Adjectives include: **Qualitative**, **Demonstrative**, **Indefinite**, **Pronominal**, **Numeral**, and **Interrogative**.
            Examples include: à¨šà©°à¨—à¨¾ à¨®à¨¨à©, à¨šà©°à¨—à©€ à¨¬à¨¾à¨£à©€, à¨šà©°à¨—à©‡ à¨¬à¨šà¨¨, à¨¸à¨¾à¨°à¨¾ à¨¦à©à¨–, à¨‰à¨¹ à¨®à¨¾à¨‡à¨†, à¨•à©‹à¨ˆ à¨®à¨¨à©à©±à¨–

            ðŸ”´ **GURBANI RULE (STRICT)**  
            â–¶ï¸ **All adjectives in Gurbani MUST agree in Number and Gender with the noun or pronoun they qualify.**  
            This is a **non-negotiable rule** confirmed by both **Sikh Research Institute (SikhRi)** and **Prof. Sahib Singhâ€™s Gurbani Vyakaran**.  
            The agreement must be:
            - **Semantic** (referring to the correct noun/pronoun)
            - **Morphological** (adjective form visibly matches Number & Gender)

            ðŸ‘‰ *In Gurbani, adjectives are always **declined** to match the Number and Gender of the noun or pronoun they describe. This means adjectives **change form** based on their grammatical role. They are not fixed or invariable by default.*

            If the adjectiveâ€™s form appears fixed (e.g., ending in â€˜Åâ€™ or â€˜auâ€™), consult its grammatical root ending (MuktÄ, KannÄ, AunkÄr, HorÄ, BihÄrÄ«) to verify its role and alignment.

            ðŸ” *Do not assume that any adjective is morphologically invariable unless **Gurbani Vyakaran** explicitly identifies it as a poetic variant that still maintains grammatical agreement.* **Do not conclude invariance merely because the same form appears with multiple nouns.**
            **Many adjectives follow internal paradigms that are consistent across different contexts, even if they *look* fixed.**

            ðŸ§  *If the adjectiveâ€™s ending appears unchanged, it must still be evaluated against known adjective paradigms (e.g., hÅrÄ-ending, kannÄ-ending). Only when those forms confirm invariance through grammatical structureâ€”not intuitionâ€”should it be marked as â€˜invariableâ€™ in the agreement table.*

            > **Cross-token check ** â€“ If the same stem re-appears with a different ending in the *line*, treat that as conclusive evidence it is **declinable**; do not invoke â€œindeclinableâ€ unless all tokens are identical in form *and* no paradigm lists inflected endings.

            ---

            **ðŸ›‘ Mandatory Adjective Agreement Table**
            âš ï¸ **Caution:**  
            Do **not** classify a word as an Adjective merely because it appears near a noun.  
            Carefully check whether the word is:
            - Acting as the **object of a postposition** (e.g., "à¨¦à©‡ à¨…à¨§à©€à¨¨", "à¨µà¨¿à©±à¨š", "à¨¤à©‹à¨‚", "à¨‰à©±à¨¤à©‡"), in which case it is a **noun**, not an adjective.
            - Part of an **oblique noun phrase** and not qualifying the noun directly.
            - Functioning as a **noun in instrumental case** (e.g., à¨¤à©à¨°à¨¿à¨¬à¨¿à¨§à¨¿ â€“ by/with threefold means); these may **appear** descriptive but are **semantically instrumental nouns**, not adjectives.
            
            These constructions often create **false links**. Always confirm grammatical agreement and functional relationship before assigning Adjective.

            If a word is confirmed as an adjective, this table is required:

            | Step | Requirement | Observation | Result |
            |------|-------------|-------------|--------|
            | 1 | Identify the qualified noun/pronoun | (e.g., à¨¸à©à¨–à© â€“ masculine singular) | ... |
            | 2 | Show matching Number & Gender in adjective form | (e.g., à¨…à¨—à¨²à©‹ = masculine singular form of à¨¹à©Œà¨°à¨¾-ending adjective) | âœ… / âŒ |
            | 3 | Stem-variation observed? | e.g. à¨«à¨•à©œ / à¨«à¨•à©œà© | âœ… / âŒ |

            âŒ *Responses that skip this table or assume invariable adjectives will be treated as incomplete.*
            *(skip the table entirely if final POS â‰  Adjective)*

            ### 4. **Verb (à¨•à¨¿à¨°à¨¿à¨†)**  
            Expresses an action, state, or condition. Includes forms like transitive/intransitive, passive, causative, auxiliary, etc.

            ### 5. **Adverb (à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à¨¼à©‡à¨¸à¨¼à¨£)**  
            Modifies verbs only. Never nouns. Categories include Time, Place, Manner, Degree, Frequency, etc.

            ### 6. **Postposition (à¨¸à¨¿à©°à¨¬à©°à¨§à¨•)** â€“ e.g., à¨¨à¨¾à¨², à¨µà¨¿à©±à¨š, à¨‰à©±à¨¤à©‡  
            ### 7. **Conjunction (à¨¯à©‹à¨—à¨•)** â€“ e.g., à¨…à¨¤à©‡, à¨œà©‡à¨•à¨°, à¨ªà¨°  
            ### 8. **Interjection (à¨µà¨¿à¨¸à¨®à©€à¨•)** â€“ e.g., à¨µà¨¾à¨¹ à¨µà¨¾à¨¹!, à¨¹à¨¾à¨!

            ---

            ## ðŸŽ¯ Evaluation Guidelines

            1. Use **Darpan Translation** to determine the wordâ€™s semantic role.  
            2. Confirm **Part of Speech**:  
            - Modifies noun/pronoun â†’ Adjective (**triggers the agreement check**)  
            - Modifies verb/adjective/adverb â†’ Adverb  
            - If noun/pronoun â†’ classify accordingly  
            3. For Adjectives:
            - Confirm Number & Gender based on the noun/pronoun the adjective qualifies. If the adjective form appears fixed, verify its grammatical alignment using its root ending.
            - If adjective doesnâ€™t change form (invariable), still list target noun and declare this explicitly 
            - âš ï¸ The **nounâ€™s gender and number** must be derived from **Gurbani Grammar definitions** (as per Darpan and Vyakaran), not from modern Punjabi intuition or pronunciation. For example, abstract nouns like **à¨¸à©‡à¨µà¨¾** are feminine singular by SGGS convention.
            âœ… *Trigger Adjective Agreement Table only if:*  
            - Word semantically modifies a noun/pronoun (confirmed in Darpan gloss)  
            - Is not the subject/object of a helper-preposition  
            - Does not serve as the head of a noun phrase or abstract concept (e.g., à¨¤à©à¨°à¨¿à¨¬à¨¿à¨§à¨¿ = by/through threefold mode)  
            4. Do not guess based on spelling or intuitionâ€”**rely on function and context from translation**  
            5. Output is **incomplete** if POS = Adjective and Adjective Agreement Table is missing

            ---

            ## ðŸ“¥ Inputs

            **Verse (Gurmukhi):**  
            {verse}

            **Darpan Translation:**  
            {trans}

            **Word under scrutiny:**  
            {word}

            **My Selections:**  
            - Number: {num}  
            - Gender: {gen}  
            - Part of Speech: {pos}

            **Dictionary Meanings (Secondary Aid):**
            {meanings_block}

            {matches_block}

            ---

            ## ðŸ“‹ Response Format (Follow exactly)

            1. **Feature Confirmation**  
            - Number: (Correct / Incorrect) â€“ based on Darpan gloss and noun agreement  
            - Gender: (Correct / Incorrect) â€“ based on noun gender  
            - Part of Speech: (Correct / Incorrect) â€“ based on function and Darpan context  

            2. **Corrections (if needed)**  
            - Number: <correct value> â€“ with rationale  
            - Gender: <correct value> â€“ with rationale  
            - Part of Speech: <correct value> â€“ with rationale  

            3. **Commentary**  
            - Explain briefly how the Darpan translation and noun/pronoun connection led to your decision  
            - If adjective form is invariable, name the adjective group (e.g., **Horaa** ending or **Poetic variation**)

            4. **Adjective-Agreement Table (REQUIRED if POS = Adjective)**  
            | Step | Requirement              | Observation                    | Result        |
            |------|--------------------------|--------------------------------|---------------|
            | 1    | Qualified noun/pronoun   | (e.g., à¨¸à©à¨–à© â€“ masculine-singular) | (Identified) |
            | 2    | Number & Gender match    | (e.g., adjective ends with -Å, matches masculine singular noun; or declare as invariable) | âœ…/âŒ |
            
            ---

            ðŸ“˜ **Quick Reference: Common Adjective Endings in Gurbani**

            | Ending      | Number & Gender         | Example           |
            |-------------|--------------------------|-------------------|
            | **-Å**      | Masculine singular        | à¨…à¨—à¨²à©‹, à¨¨à¨¿à¨µà©à¨°à¨¤à©‹       |
            | **-Ä“ / à¨**  | Masculine plural          | à¨…à¨—à¨²à©‡, à¨šà©°à¨—à©‡         |
            | **-Ä«**      | Feminine singular         | à¨šà©°à¨—à©€, à¨…à¨—à¨²à©€         |
            | **-Ä«Äá¹ / à¨¿à¨†à¨‚** | Feminine plural         | à¨šà©°à¨—à©€à¨†à¨‚, à¨…à¨—à¨²à©€à¨†à¨‚      |

            These endings are drawn from adjective groups described in Prof. Sahib Singhâ€™s *Gurbani Vyakaran*, e.g., hÅrÄ-samÄpt adjectives. Always match these with the gender and number of the qualified noun.
            ðŸ”¹ *Tatsam Words (Sanskrit-Derived)*:  
            Many Sanskrit-origin words in Gurbaniâ€”such as **à¨¤à©à¨°à¨¿à¨¬à¨¿à¨§à¨¿**, **à¨—à©à¨¹à¨œ**, **à¨¤à¨¤**â€”often appear morphologically fixed and may superficially resemble adjectives. However, they frequently function as **abstract nouns** or appear in **instrumental** or other oblique grammatical cases.

            > ðŸ”¸ **Tatsam Adjectives vs Indeclinable Nouns:**  
            > Do **not** classify such words as adjectives unless the **Darpan gloss clearly shows them qualifying a noun**, with **visible agreement in Number and Gender**.  
            > â–¶ï¸ If the gloss inserts a helper like *â€œby,â€ â€œwith,â€ â€œin,â€ or â€œofâ€*, this usually signals a **noun in an oblique case**â€”not an adjective.  
            > âž• For example, **à¨¤à©à¨°à¨¿à¨¬à¨¿à¨§à¨¿** may mean *â€œby threefold meansâ€* or *â€œthrough the three qualitiesâ€*, serving a **functional role** rather than describing a noun.

            ðŸ” *Key Insight:*  
            Words like **à¨¤à©à¨°à¨¿à¨¬à¨¿à¨§à¨¿**, despite their descriptive appearance, often act as **instrumental-case nouns** or form part of a **compound abstract expression** (e.g., *à¨¤à©à¨°à¨¿à¨—à©à¨£à©€ à¨®à¨¾à¨‡à¨†*). Always validate their role against the **Darpan translation** and **Gurbani grammar definitions**, not surface resemblance.

            ---

            ### ðŸ“‘ Stem-Variation Check ðŸ†•
            *(Fill this mini-grid during Phase 2 if you detected more than one token of the same stem)*  
            | Token | Ending | Nearby noun/pronoun | Expected agreement | Matches? |
            |-------|--------|---------------------|--------------------|----------|

            ---

            ðŸ›  **Debug Trace** ðŸ†• (single line at the very end):  
            `[TokensChecked:X | Declined:Yes/No | FinalPOS:___ | AgreementOK:Yes/No]`

            """).strip()

            # copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            messagebox.showinfo(
                "Prompt Ready",
                "Expert-level prompt (with secondary dictionary meanings) has been copied to your clipboard.\n"
                "Paste it into ChatGPT for its recommendation."
            )

        tk.Button(
            right,
            text="ðŸ“‹ Build Expert Prompt",
            font=("Arial", 14, "italic"),
            bg="white",
            fg="dark cyan",
            padx=6, pady=4,
            command=ask_suggestion
        ).pack(pady=(10,0))

        # 5) Bottom separator + buttons
        sep = tk.Frame(win, bg='#cccccc', height=2)
        sep.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0,5))

        btns = tk.Frame(win, bg='light gray')
        btns.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0,46))
        tk.Button(btns, text="â€¹ Back to Translation",
                  font=('Arial',12), bg='gray', fg='white',
                  padx=20, pady=8,
                  command=lambda: [win.destroy(), self.show_translation_input()]
        ).pack(side=tk.LEFT)
        tk.Button(btns, text="Skip Word",
                  font=('Arial',12), bg='orange', fg='white',
                  padx=20, pady=8,
                  command=lambda: [win.destroy(), self.skip_word_grammar()]
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(btns, text="Submit",
                  font=('Arial',12,'bold'),
                  bg='dark cyan', fg='white',
                  padx=20, pady=8,
                  command=lambda: self.submit_input_grammar(word, index)
        ).pack(side=tk.RIGHT)

        # Modal
        win.transient(self.root)
        win.grab_set()
        self.root.wait_window(win)

    def lookup_grammar_meanings_thread(self, word):
        """
        Look up dictionary meanings for â€˜wordâ€™ on a background thread,
        then schedule update into the grammar UI.
        """
        meanings = self.lookup_word_in_dictionary(word)
        # schedule into mainloop
        self.root.after(0, lambda: self.update_grammar_meanings_ui(meanings))

    def update_grammar_meanings_ui(self, meanings):
        """
        Populate the meanings_inner_frame into N columns (now 7).
        """
        # 1) Clear any old widgets
        for w in self.meanings_inner_frame.winfo_children():
            w.destroy()

        # 2) Decide on how many columns
        num_cols = 5
        total   = len(meanings)
        # Ceil division so each column has at most ceil(total/num_cols) entries
        per_col = -(-total // num_cols)

        # 3) Grid each meaning into (row, column)
        for idx, m in enumerate(meanings):
            col = idx // per_col
            row = idx % per_col
            tk.Label(
                self.meanings_inner_frame,
                text=f"â€¢ {m}",
                bg='light gray',
                font=('Arial', 12),
                wraplength=350,   # adjust if you need narrower columns
                justify='left'
            ).grid(
                row=row,
                column=col,
                sticky='nw',
                padx=8, pady=2
            )
        
        # 4) NEW: stash into a growing list of dicts:
        entry = {
            "word": getattr(self, "current_word", None),
            "meanings": meanings
        }
        self.grammar_meanings.append(entry)

    def submit_input_grammar(self, word, index):
        """
        Collects grammar input and transitions to the dropdown step.
        """
        # 1) Extract the basic Number/Gender/POS the user just picked:
        number = self.number_var.get()
        gender = self.gender_var.get()
        pos    = self.pos_var.get()

        # 2) Gather verse + translation context:
        verse       = self.selected_verse_text
        translation = self.current_translation

        # 3) Pull the previously lookedâ€up meanings out of self.grammar_meanings:
        meanings = next(
            (e["meanings"] for e in self.grammar_meanings if e["word"] == word),
            []
        )

        # 4) Build the initial "detailed" entry dict:
        entry = {
            "\ufeffVowel Ending":       word,
            "Number / à¨µà¨šà¨¨":       number,
            "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£":    "",   # to be filled in dropdown step
            "Gender / à¨²à¨¿à©°à¨—":       gender,
            "Word Root":           "",   # to be filled next
            "Type":                pos,
            "Evaluation":          "Derived",
            "Reference Verse":     verse,
            "Darpan Translation":  translation,
            "Darpan Meaning":      "| ".join(m.strip() for m in meanings),
            "ChatGPT Commentary":  ""    # to be pasted later
        }

        # 5) Store it so the next window can read & update it:
        self.current_detailed_entry = entry

        # 6) Hand off to your dropdownâ€UI:
        self.open_final_grammar_dropdown(word, entry["Type"], index)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # MAIN METHOD  â€“  drop-in replacement
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def open_final_grammar_dropdown(self, word, pos, index):
        """
        After the user has chosen a Part-of-Speech, pop up a Toplevel
        with dropdowns for the detailed grammar fields _and_ a place
        to paste ChatGPTâ€™s commentary.
        """

        # 1) --------------  Load & filter your CSV  -----------------
        self.grammar_db = pd.read_csv("1.1.1_birha.csv")
        df = self.grammar_db[self.grammar_db["Type"] == pos]

        # option lists
        num_opts  = sorted(df["Number / à¨µà¨šà¨¨"].dropna().unique().tolist())
        gram_opts = sorted(df["Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"].dropna().unique().tolist())
        gen_opts  = sorted(df["Gender / à¨²à¨¿à©°à¨—"].dropna().unique().tolist())
        
        # pull the saved entry first
        entry = self.current_detailed_entry
        # Extract the POS type
        pos_type = entry["Type"]

        # Choose how to build root_opts based on whether it's a Noun
        if pos_type == "Noun / à¨¨à¨¾à¨‚à¨µ":
            # Option-1: For Nouns, use hard-wired canonical endings
            root_opts = CANONICAL_ENDINGS.copy()
            for lst in (num_opts, gram_opts, gen_opts):
                if "NA" not in lst:
                    lst.insert(0, "NA")
        else:
            # Option-2: For all other types (e.g., Pronoun), use actual values from database
            root_opts = sorted(df["Word Root"].dropna().unique().tolist())
            for lst in (num_opts, gram_opts, gen_opts, root_opts):
                if "NA" not in lst:
                    lst.insert(0, "NA")

        # ---- Repeat-word banner bookkeeping ----
        verse_text = getattr(self, "current_pankti", "")
        verse_key = self._verse_key(verse_text)
        if getattr(self, "_last_dropdown_verse_key", None) != verse_key:
            self._repeat_note_shown = set()
            self._first_repeat_token = None
            self._last_dropdown_verse_key = verse_key
            self._suppress_repeat_notes_for_verse = False
            # kill any stale frame
            if hasattr(self, "literal_note_frame") and self.literal_note_frame:
                try:
                    if self.literal_note_frame.winfo_exists():
                        self.literal_note_frame.destroy()
                except Exception:
                    pass
                self.literal_note_frame = None
                self.literal_note_title = None
                self.literal_note_body = None

        words = list(getattr(self, "pankti_words", []))
        if not words and verse_text:
            words = verse_text.split()
        cached_words = getattr(self, "_raw_words_cache", None)
        if cached_words != words:
            norm_words = [self._norm_tok(w) for w in words]
            self._norm_words_cache = norm_words
            self._raw_words_cache = words
        else:
            norm_words = getattr(self, "_norm_words_cache", []) or [self._norm_tok(w) for w in words]

        idx = index
        display_word = words[idx] if idx < len(words) else word
        word_norm = norm_words[idx] if idx < len(norm_words) else self._norm_tok(display_word)
        # guard empty tokens; ignore vanished punctuation/ZW chars
        has_repeat = bool(word_norm) and norm_words.count(word_norm) >= 2
        if has_repeat and self._first_repeat_token is None and word_norm:
            self._first_repeat_token = word_norm
        seen_before = norm_words[:idx].count(word_norm) if word_norm else 0
        key = (verse_key, word_norm, "second")
        is_special_hit = (
            has_repeat
            and word_norm == self._first_repeat_token
            and seen_before == 1
            and key not in self._repeat_note_shown
        )

        inline_allowed = (
            getattr(self, "_use_inline_literal_banner", True)
            and not getattr(self, "_suppress_repeat_notes_for_verse", False)
        )

        suppress_first_occurrence_of_first_token = (
            has_repeat
            and self._first_repeat_token is not None
            and word_norm == self._first_repeat_token
            and seen_before == 0
        )

        if inline_allowed and is_special_hit:
            self._repeat_note_shown.add(key)
            special_text = (
                f"In literal analysis: The word â€œ{display_word}â€ appears multiple times in this verse. "
                "The highlighted grammar options reflect your past selections for this word (or close matches) "
                "to encourage consistency. Theyâ€™re suggestions, not mandatesâ€”adjust if the current context differs."
            )
            self._ensure_literal_banner(special_text)
        elif inline_allowed and has_repeat and not suppress_first_occurrence_of_first_token:
            self._ensure_literal_banner(self._LITERAL_NOTE_TEXT)
        else:
            if not inline_allowed or not has_repeat:
                if hasattr(self, "literal_note_frame") and self.literal_note_frame:
                    try:
                        if self.literal_note_frame.winfo_exists():
                            self.literal_note_frame.destroy()
                    except Exception:
                        pass
                    self.literal_note_frame = None
                    self.literal_note_title = None
                    self.literal_note_body = None

        # 2) --------------  Build the window  -----------------------
        win = tk.Toplevel(self.root)
        win.title(f"Detail Grammar for â€˜{word}â€™")
        win.configure(bg="light gray")
        win.state("zoomed")

        frm = tk.LabelFrame(
            win, text="Finalize Detailed Grammar",
            font=("Arial", 16, "bold"), bg="light gray",
            padx=10, pady=10
        )
        frm.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        frm.grid_columnconfigure(1, weight=1)

        def _add_dropdown(row, label, var, options, colspan=1):
            ttk.Label(frm, text=label, font=("Arial", 12),
                    background="light gray").grid(
                row=row, column=0, sticky="w", padx=5, pady=8)
            cb = ttk.Combobox(
                frm, textvariable=var, values=options,
                state="readonly", font=("Arial", 12))
            cb.grid(row=row, column=1, columnspan=colspan,
                    sticky="ew", padx=5, pady=8)
            return cb

        # 3) --------------  Five dropdowns  -------------------------
        self.detailed_ve_var      = tk.StringVar(value=self._norm_get(entry, "\ufeffVowel Ending"))
        self.detailed_number_var  = tk.StringVar(value=entry["Number / à¨µà¨šà¨¨"])
        self.detailed_grammar_var = tk.StringVar(value=entry["Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"])
        self.detailed_gender_var  = tk.StringVar(value=entry["Gender / à¨²à¨¿à©°à¨—"])
        self.detailed_root_var    = tk.StringVar(value=entry["Word Root"])

        _add_dropdown(0, "Word Under Analysis:", self.detailed_ve_var, [word], colspan=2)
        _add_dropdown(1, "Number / à¨µà¨šà¨¨:",        self.detailed_number_var,  num_opts)
        _add_dropdown(2, "Grammar Case / à¨µà¨¯à¨¾à¨•à¨°à¨£:", self.detailed_grammar_var, gram_opts)
        _add_dropdown(3, "Gender / à¨²à¨¿à©°à¨—:",        self.detailed_gender_var,   gen_opts)
        _add_dropdown(4, "Word Root:",            self.detailed_root_var,     root_opts)

        # 4) --------------  Commentary box  -------------------------
        cm_frame = tk.LabelFrame(
            frm, text="ChatGPT Commentary", font=("Arial", 14, "bold"),
            bg="light gray", padx=8, pady=8
        )
        cm_frame.grid(row=5, column=0, columnspan=2,
                    sticky="nsew", padx=5, pady=(10, 0))
        self.detailed_commentary = tk.Text(
            cm_frame, wrap=tk.WORD, font=("Arial", 12),
            height=6, bd=1, relief="sunken", padx=5, pady=5
        )
        self.detailed_commentary.pack(fill=tk.BOTH, expand=True)

        # ---------- dynamic noun-map in self ----------
        if not hasattr(self, "noun_map"):
            self.noun_map = build_noun_map()

        def build_examples_footer():
            """
            Return a Markdown block that lists every ending-class with its full word,
            base form, and detachable suffix, taken from EXAMPLE_BASES.
            """
            lines = ["*Ending-class examples*"]
            for label in CANONICAL_ENDINGS:
                if label == "NA":
                    continue

                triples = EXAMPLE_BASES.get(label, [])
                if not triples:
                    continue

                # Build â€œà¨‰à¨¦à¨¿à¨†à¨¨à©ˆ â†’ à¨‰à¨¦à¨¿à¨†à¨¨ + à©ˆâ€ style strings
                rendered = [
                    f"{full} â†’ {base}{' + ' + suf if suf else ''}"
                    for full, base, suf in triples
                ]
                lines.append(f"- **{label}** â†’ " + ", ".join(rendered))

            return "\n".join(lines)

        # helper â€“ build cheat-sheet table from noun_map
        def make_cheat_sheet(word: str, gender: str, number: str) -> str:
            """
            Progressive right-edge matcher, now bounded by len(word):
            â€¢ For L = 1 â€¦ len(word):
                    slice_w = word[-L:]
                    for every ending key E in noun_map:
                        if E[-L:] == slice_w  â†’ collect E
            â€¢ Merge all collected endingsâ€™ case tables (deduped), build Markdown.
            """

            word_len = len(word)                              # new upper bound
            matched: list[str] = []

            # 1) -------- gather every ending with the same right-edge ------------
            for L in range(1, word_len + 1):                  # 1 â€¦ len(word)
                slice_w = word[-L:]
                for ending in self.noun_map:
                    if ending[-L:] == slice_w and ending not in matched:
                        matched.append(ending)

            if not matched:
                return ""                                     # nothing found

            # 2) -------- merge case â†’ suffix lists for gender & number ----------
            merged: dict[str, list[str]] = {}
            for end in matched:
                cases = (
                    self.noun_map[end]
                        .get(gender or "NA", {})
                        .get(number or "NA", {})
                )
                for case, forms in cases.items():
                    merged.setdefault(case, []).extend(forms)

            if not merged:
                return ""                                     # no data for this combo

            # Deduplicate each list while preserving order
            for case, forms in merged.items():
                seen = set()
                merged[case] = [f for f in forms if not (f in seen or seen.add(f))]

            # 3) -------- build the mini-table -----------------------------------
            rows = [
                f"| {case:11} | {', '.join(forms)} |"
                for case, forms in merged.items()
            ]
            ending_list = ", ".join(matched)

            # build the core table but DONâ€™T return yet
            table_rows = "\n".join(rows)
            table_markdown = textwrap.dedent(f"""
                **Morphology map â€“ endings matched: {ending_list}
                ({gender.split()[0]}/{number.split()[0]})**
                | Case         | Attested suffix(es) |
                |--------------|----------------------|
                {table_rows}
                _Table shows **attested** suffixes.
                If you need an unlisted case, propose a plausible form and justify._
            """).strip()

            # --- build a footer that shows EVERY ending-class with examples -------------
            footer = "\n" + build_examples_footer()
            return table_markdown + footer + "\n\n"

        # 5) --------------  Prompt-builder button  ------------------
        def build_detailed_prompt(num_opts=num_opts,
                                gram_opts=gram_opts,
                                gen_opts=gen_opts,
                                root_opts=root_opts):

            ve    = self.detailed_ve_var.get()      or "(please choose)"
            num   = self.detailed_number_var.get()  or "(please choose)"
            gram  = self.detailed_grammar_var.get() or "(please choose)"
            gen   = self.detailed_gender_var.get()  or "(please choose)"
            root  = self.detailed_root_var.get()    or "(please choose)"
            verse = entry["Reference Verse"]
            trans = entry["Darpan Translation"]
            dm    = entry["Darpan Meaning"]

            def make_block(title, items):
                lines = [f"- **{title}**"]
                for it in items:
                    lines.append(f"  â€“ {it}")
                return "\n".join(lines)

            # ------------------------------------------------------------------
            # Use the existing search_by_criteria helper to surface any grammar
            # matches that align with the current selections.  This gives the
            # language model extra context about how the form appears in the
            # database.  If no match is found or the search fails, we simply
            # omit the block from the prompt.
            # ------------------------------------------------------------------
            try:
                crit_num = num if num != "(please choose)" else "NA"
                crit_gen = gen if gen != "(please choose)" else "NA"
                crit_matches = self.search_by_criteria(word, crit_num, crit_gen, pos)

                rows = []
                for result, _count, _perc in crit_matches[:5]:
                    parts = [p.strip() for p in result.split("|")]
                    if len(parts) < 7:
                        parts += [""] * (7 - len(parts))

                    highlight = parts[0] == parts[1] and is_full_word(parts[0])
                    if highlight:
                        parts = [f"**{p}**" for p in parts]
                        parts[0] = "âœ… " + parts[0]

                    rows.append("| " + " | ".join(
                        parts + [str(_count), f"{_perc:.1f}%"]
                    ) + " |")

                if rows:
                    headers = [
                        "Word under Analysis",
                        "Vowel Ending / Word Matches",
                        "Number / à¨µà¨šà¨¨",
                        "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
                        "Gender / à¨²à¨¿à©°à¨—",
                        "Word Root",
                        "Type",
                        "Match Count",
                        "Match %",
                    ]
                    table_lines = [
                        "**Top Grammar Matches**",
                        "| " + " | ".join(headers) + " |",
                        "| " + " | ".join(["---"] * len(headers)) + " |",
                        *rows,
                    ]
                    matches_block = "\n".join(table_lines)
                else:
                    matches_block = ""
            except Exception as exc:
                print(f"search_by_criteria failed: {exc}")
                matches_block = ""

            opts_block = "\n\n".join([
                make_block("Word Under Analysis", [ve]),
                make_block("Number / à¨µà¨šà¨¨ options",   num_opts),
                make_block("Grammar Case / à¨µà¨¯à¨¾à¨•à¨°à¨£ options", gram_opts),
                make_block("Gender / à¨²à¨¿à©°à¨— options",  gen_opts),
                make_block("Word-Root options",      root_opts),
            ])

            # noun-specific notes
            ending_cheat_sheet = ""
            implicit_note      = ""
            common_sense_note  = ""

            if entry["Type"] == "Noun / à¨¨à¨¾à¨‚à¨µ":
                ending_cheat_sheet = make_cheat_sheet(ve, gen, num)

                implicit_note = textwrap.dedent("""\
                    **IMPLICIT POST-POSITIONS & CASE DECLENSIONS**  
                    In GurbÄá¹‡Ä«, relationships such as *to, from, with, of, in* are conveyed
                    by **inflected endings** rather than modern post-positions (`à¨¨à©‚à©°`, `à¨¨à¨¾à¨²`
                    â€¦). A noun may appear unmarked while the Darpan gloss supplies a helper.

                    **How to read the gloss**  
                    â€¢ If the gloss inserts **to / for / of / by / with / from / in / on / at / O / Hey**
                    that is absent in the verse, treat it as an **implicit post-position**
                    and pick the matching **case**.  
                    â€¢ If the gloss repeats the word without a helper, default to
                    **Nominative / Accusative** and let context refine the choice.

                    | Helper | Punjabi marker | Case |
                    |--------|----------------|------|
                    | to / for   | `à¨¨à©‚à©°`, `à¨²à¨ˆ`     | **Dative** |
                    | of         | `à¨¦à¨¾/à¨¦à©‡/à¨¦à©€`      | **Genitive** |
                    | by / with  | `à¨¨à¨¾à¨²`, `à¨¨à¨¾à¨²à©‹à¨‚`  | **Instrumental** |
                    | from / out of | `à¨¤à©‹à¨‚`, `à¨‰à¨¤à©‹à¨‚` | **Ablative** |
                    | in / on / at | `à¨µà¨¿à©±à¨š`, `à¨‰à©±à¨¤à©‡`, `à¨¤à©‡` | **Locative** |
                    | O / Hey    | *(address)*     | **Vocative** |

                    _Endings overlap: Nomâ‰ˆAcc, Genâ‰ˆDat, Instâ‰ˆLoc â€“ use semantics to decide._
                """).strip() + "\n\n"

                common_sense_note = textwrap.dedent("""\
                    **SEMANTIC SANITY CHECK â€“ DOES THE LABEL REALLY FIT?**  
                    Match the case to the *role* the noun plays.

                    **Quick Meanings**  Nom=subject | Acc=object | Inst=by/with | Dat=to/for |
                    Gen=of | Abl=from | Loc=in/on | Voc=address

                    â€¢ Instrumental â€“ means, agency, tool  
                    â€¢ Locative     â€“ spatial/temporal setting  
                    â€¢ Dative       â€“ recipient, purpose  
                    â€¢ Genitive     â€“ ownership, relation  
                    â€¢ Ablative     â€“ source, cause  
                    â€¢ Nom / Acc    â€“ subject vs. direct object (no helper)  
                    â€¢ Vocative     â€“ direct address

                    **Ambiguity reminder** â€“ If **one suffix stands for two cases**
                    (e.g., â€“à¨ˆ = Nom *and* Acc), *explain your semantic reason* for choosing.

                    **Oblique + Post-position lines** â€“ GurbÄá¹‡Ä« occasionally stacks a
                    post-position **after** an oblique form **and** after a direct form
                    (see examples with *à¨¨à¨‡à¨†à¨‚*, *à¨¸à¨¬à¨¦à©ˆ*).  Either is validâ€”choose the case
                    that best reflects the combined meaning.
                """).strip() + "\n\n"
                
            elif entry["Type"] == "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ":
                # â”€â”€â”€ Pronoun block with enriched cross-category logic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                implicit_note = textwrap.dedent("""\
                    **PRONOUNS â€“ INFLECTIONS, IDENTITY & IMPLIED MEANINGS**  
                    In GurbÄá¹‡Ä«, pronouns diverge from noun patterns and inflect by **person, number, and gender**.  
                    Their meaning is sometimes explicit (like à¨®à©ˆà¨‚ = I), but often **derived from Darpan's gloss**.

                    **Core Steps to Identify the Case**  
                    1. **Read the gloss literally.**  
                    If it adds a helper like *to, from, with, in*, this signals an **implicit post-position**.  
                    Match it with:  
                    â€¢ `à¨¨à©‚à©°`, `à¨²à¨ˆ` â†’ Dative  
                    â€¢ `à¨¦à¨¾/à¨¦à©€/à¨¦à©‡`, `à¨•à¨¾/à¨•à©€/à¨•à©‡` â†’ Genitive  
                    â€¢ `à¨¤à©‹à¨‚`, `à¨‰à¨¤à©‹à¨‚`, `à¨¸à©‡`, `à¨…à¨¤à©‡` â†’ Ablative  
                    â€¢ `à¨¨à¨¾à¨²`, `à¨µà¨¿à©±à¨š`, `à¨‰à©±à¨¤à©‡`, `à¨•à©‹à¨²`, `à¨…à©°à¨¦à¨°`, etc. â†’ Instrumental / Locative  
                    â€¢ `O`, `Hey` â†’ Vocative

                    2. **Check form compatibility.**  
                    Every person/gender/number has a finite set of endings (see below).  
                    Match the surface form to a standard **canonical pronoun**.

                    3. **For Relative / Interrogative / Reflexive / Indefinite types**,  
                    blend case logic with **semantic roles**: e.g.,  
                    â€¢ à¨•à¨¿à¨¸ à¨¨à©‚à©° â†’ â€œto whomâ€ â†’ Dative  
                    â€¢ à¨œà¨¿à¨¸ à¨¤à©‡ â†’ â€œon whomâ€ â†’ Locative  
                    â€¢ à¨†à¨ªà¨£à©‡ à¨¹à©€ à¨†à¨ª â†’ Reflexive emphatic  
                    â€¢ à¨œà¨¿à¨¸ à¨¦à©€, à¨œà¨¿à¨¸ à¨¦à¨¾ â†’ Genitive relative

                    _Postpositions are often absent but impliedâ€”your judgment is key._  
                    Also note: **GurbÄá¹‡Ä« often uses plural pronouns to show respect.**
                """).strip() + "\n\n"

                common_sense_note = textwrap.dedent("""\
                    **PRONOUN SEMANTIC CHECK â€“ ROLE IN MEANINGFUL CONTEXT**  
                    Pronouns are **not just replacements for nouns**â€”they carry personhood, humility, or divinity.

                    âœ… Use this test logic:  
                    - **Is the pronoun the subject?** â†’ Nom  
                    - **Receiving the action?** â†’ Acc  
                    - **Belonging to someone?** â†’ Gen  
                    - **Given to someone?** â†’ Dat  
                    - **Means or tool or â€œwithâ€ sense?** â†’ Inst  
                    - **Place or inner state?** â†’ Loc  
                    - **Directly addressed?** â†’ Voc  

                    âš ï¸ For overlapping forms:  
                    - Use the Darpan helper (e.g., "to me", "from them", "by whom")  
                    - Ask what semantic role the pronoun plays **in that line**  
                    - e.g., â€œà¨®à©ˆâ€ may be Nom or Acc depending on meaning

                    **Special Guidance per Category**  
                    - **Reflexive** (à¨†à¨ª, à¨†à¨ªà¨£à©‡): Self-reference or emphasis  
                    - **Relative/Correlative** (à¨œà©‹...à¨¸à©‹): Link two ideas (doer/result, condition/result)  
                    - **Interrogative** (à¨•à©Œà¨£, à¨•à¨¿à¨¸): Structure question  
                    - **Indefinite** (à¨•à©‹à¨ˆ, à¨¸à¨­): Ambiguous subject  
                    - **Honorific 2nd Person** (à¨¤à©à¨¸à©€à¨‚, à¨¤à©à¨®): May appear plural but refer to one Divine

                    **Final Tip**: Plural/oblique/abstract usage may reflect poetic or spiritual nuance more than grammar. Follow meaning.
                """).strip() + "\n\n"

                ending_cheat_sheet = textwrap.dedent("""\
                    **PRONOUN CASE ENDINGS â€“ EXAMPLES ACROSS CATEGORIES**

                    ðŸ”¹ **Valid Number / Gender Combinations per Category**  
                    *(Use this to cross-check if your feature choices are logically possible)*

                    - **1st Person / à¨‰à©±à¨¤à¨® à¨ªà©à¨°à¨–**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **2nd Person / à¨®à¨§à¨® à¨ªà©à¨°à¨–**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **3rd Person / à¨…à¨¨à¨¯ à¨ªà©à¨°à¨–**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **CoRelative / à¨…à¨¨à©à¨¸à©°à¨¬à©°à¨§**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **Relative / à¨¸à©°à¨¬à©°à¨§**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **Interrogative / à¨ªà©à¨°à¨¶à¨¨ à¨µà¨¾à¨šà¨•**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **Reflexive / à¨¨à¨¿à¨œ à¨µà¨¾à¨šà¨•**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    - **Indefinite / à¨…à¨¨à¨¿à¨¸à¨šà©‡ à¨µà¨¾à¨šà¨•**  
                    â€“ Number: Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©  
                    â€“ Gender: Masculine / à¨ªà©à¨²à¨¿à©°à¨—, Feminine / à¨‡à¨¸à¨¤à¨°à©€, Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•

                    _âœ³ Note: â€œTransâ€ (à¨¨à¨ªà©à¨‚à¨¸à¨•) appears for most categories due to universal/neutral references or poetic plurality._

                    **1st Person / à¨‰à©±à¨¤à¨® à¨ªà©à¨°à¨– Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨®à©ˆ / à¨®à©°à¨à¨¹à© / à¨¹à¨® à¨¤à©‡
                    - Accusative à¨•à¨°à¨®: à¨®à©ˆ / à¨®à©ˆà¨¨à©‹ / à¨®à©‹ à¨•à¨‰ / à¨®à©‹à¨•à¨‰ / à¨®à©‹à¨¹à¨¿ / à¨®à©°à¨žà© / à¨¹à¨® / à¨¹à¨®à¨¹à¨¿
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨®à¨¾à¨à©ˆ / à¨®à©à¨à¨¹à¨¿ / à¨®à©à¨à©ˆ / à¨®à©à¨¹à¨¿ / à¨®à©‚ / à¨®à©ˆ / à¨®à©ˆà¨¨à©‹ / à¨®à©‹ à¨•à¨‰ / à¨®à©‹à¨¹à¨¿ / à¨¹à¨® (à¨•à¨‰) / à¨¹à¨®à¨¹à© / à¨¹à¨®à¨¾à¨°à©ˆ
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨…à¨¸à¨¾ / à¨…à¨¸à¨¾à¨¡à©œà¨¾ / à¨…à¨¸à¨¾à¨¹ / à¨…à¨¸à¨¾à©œà¨¾ / à¨®à¨¹à¨¿à©°à¨œà¨¾ / à¨®à¨¹à¨¿à©°à¨¡à¨¾ / à¨®à¨¾ / à¨®à©‚ / à¨®à©‡à¨°à¨‰ / à¨®à©‡à¨°à¨¾ / à¨®à©‡à¨°à©€ / à¨®à©ˆ / à¨®à©ˆà¨¡à¨¾ / à¨®à©‹à¨° / à¨®à©‹à¨°à¨²à¨¾ / à¨®à©‹à¨°à¨²à©‹ / à¨®à©‹à¨°à¨¾ / à¨®à©‹à¨°à©€ / à¨®à©‹à¨°à©‡ / à¨®à©‹à¨¹à¨¿ / à¨®à©°à¨žà© / à¨¹à¨®à¨°à¨¾ / à¨¹à¨®à¨°à©ˆ / à¨¹à¨®à¨°à©‹ / à¨¹à¨®à¨¾à¨°à¨¾
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨®à©à¨ à¨®à¨¹à¨¿ / à¨®à©à¨à¨¹à¨¿ à¨ªà¨¹à¨¿ / à¨®à©à¨à© / à¨®à©à¨à©ˆ / à¨®à©‡à¨°à©ˆ / à¨®à©ˆ à¨…à©°à¨¤à¨°à¨¿ / à¨®à©ˆ à¨µà¨¿à¨šà¨¿ / à¨®à©‹ à¨®à¨¹à¨¿ / à¨®à©°à¨à© / à¨¹à¨® / à¨¹à¨®à¨°à©ˆ / à¨¹à¨®à¨¾à¨°à©ˆ
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨…à¨¸à¨¾ / à¨…à¨¸à©€ / à¨®à©‚ / à¨®à©‚à¨‚ / à¨®à©ˆ / à¨®à©‹à¨¹à¨¿ / à¨¹à¨‰ / à¨¹à¨® / à¨¹à¨®à¨¹à©

                    **2nd Person / à¨®à¨§à¨® à¨ªà©à¨°à¨– Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨¤à©à¨ à¨¤à©‡ / à¨¤à©à¨à©ˆ / à¨¤à©à¨à©ˆ à¨¤à©‡ / à¨¤à©à¨à©ˆ à¨ªà¨¹à¨¿ / à¨¤à©à¨§à¨¹à© / à¨¤à©à¨§à©ˆ à¨¤à©‡ / à¨¤à©à¨® à¨¤à©‡
                    - Accusative à¨•à¨°à¨®: à¨¤à¨‰ / à¨¤à©à¨ / à¨¤à©à¨à¨¹à¨¿ / à¨¤à©à¨à© / à¨¤à©à¨à©ˆ / à¨¤à©à¨§ / à¨¤à©à¨§ à¨¨à©‹ / à¨¤à©à¨§à© / à¨¤à©à¨§à©à¨¨à©‹ / à¨¤à©à¨§à©ˆ / à¨¤à©à¨® / à¨¤à©à¨®à¨¹à¨¿ / à¨¤à©à¨¹à¨¨à©‹ / à¨¤à©à¨¹à¨¿ / à¨¤à©‚ / à¨¤à©‚à©° / à¨¤à©‹à¨¹à¨¿ / à¨¤à©‹à¨¹à©€
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨¤à¨‰ / à¨¤à©à¨à¨¹à¨¿ / à¨¤à©à¨à© / à¨¤à©à¨à©ˆ / à¨¤à©à¨§ / à¨¤à©à¨§à© / à¨¤à©à¨® / à¨¤à©à¨® à¨•à¨‰ / à¨¤à©à¨¸à¨¾ / à¨¤à©à¨¹à¨¿ / à¨¤à©ˆ / à¨¤à©ˆ à¨•à©‚à©° / à¨¤à©‹à¨¹à¨¿ / à¨¥à©‡ / à¨¥à©ˆà¨‚
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨¤à¨‰ / à¨¤à¨µ / à¨¤à¨¹à¨¿à©°à¨œà©€ / à¨¤à¨¿à¨¹à¨¾à¨°à©ˆ / à¨¤à© / à¨¤à©à¨… / à¨¤à©à¨à¨¹à¨¿ / à¨¤à©à¨®à¨°à¨¾ / à¨¤à©à¨®à¨°à©€ / à¨¤à©à¨®à¨°à©‡ / à¨¤à©à¨®à¨¾à¨°à©€ / à¨¤à©à¨¹à¨¾à¨°à©‡ / à¨¤à©‚ / à¨¤à©‡à¨°à¨‰ / à¨¤à©‡à¨°à¨¾ / à¨¤à©‡à¨°à¨¿à¨† / à¨¤à©‡à¨°à©€ / à¨¤à©‡à¨°à©‡ / à¨¤à©‡à¨°à©‹ / à¨¤à©ˆà¨¡à¨¾ / à¨¤à©‹à¨° / à¨¤à©‹à¨¹à¨¿ / à¨¥à¨¾à¨°à©€ / à¨¥à¨¾à¨°à©‡
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨¤à©à¨ / à¨¤à©à¨ à¨¹à©€ / à¨¤à©à¨à¨¹à¨¿ / à¨¤à©à¨à©ˆ / à¨¤à©à¨à©ˆ à¨¸à¨¾à¨à¨°à¨¿ / à¨¤à©à¨§à© / à¨¤à©à¨§à©ˆ / à¨¤à©à¨® / à¨¤à©à¨®à¨¹à¨¿ / à¨¤à©‹à¨¹à¨¿
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨¤à¨‰ / à¨¤à© à¨¹à©€ / à¨¤à©à¨ / à¨¤à©à¨à¨¹à¨¿ / à¨¤à©à¨à©ˆ / à¨¤à©à¨§à© / à¨¤à©à¨§à©ˆ / à¨¤à©à¨® / à¨¤à©à¨® à¨¹à©€ / à¨¤à©à¨®à¨¹à¨¿ / à¨¤à©à¨®à©ˆ / à¨¤à©à¨¸à©€ / à¨¤à©à¨¹à©€ / à¨¤à©‚ / à¨¤à©‚ à¨¹à©ˆ / à¨¤à©‚à¨‚ / à¨¤à©‚à¨¹à©ˆ / à¨¤à©ˆ / à¨¤à©ˆà¨‚ / à¨¤à©‹à¨¹à¨¿

                    **3rd Person / à¨…à¨¨à¨¯ à¨ªà©à¨°à¨– Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨‡à¨¨ / à¨‡à¨¸ (à¨¤à©‡) / à¨‰à¨† / à¨‰à¨¨ (à¨¤à©‡) / à¨‰à¨¨à¨¾ / à¨‰à¨¸ / à¨“à¨¨à¨¾à©
                    - Accusative à¨•à¨°à¨®: à¨‡à¨¸à¨¹à¨¿ / à¨‡à¨¸à© / à¨‡à¨¹ / à¨‡à¨¹à© / à¨‰à¨†à¨¹à¨¿ / à¨‰à¨‡ / à¨‰à¨¨ / à¨‰à¨¸ / à¨‰à¨¸à© / à¨‰à¨¹ / à¨à¨¸ / à¨à¨¹à¨¾ / à¨à¨¹à¨¿ / à¨“à¨‡ / à¨“à¨ˆ / à¨“à¨¨à¨¾ / à¨“à¨¸ / à¨“à¨¸à© / à¨“à¨¹à© / à¨¤à¨¿à¨¨ / à¨¤à©‡ / à¨µà¨¾ / à¨µà¨¾à¨¹à©€ / à¨¸à©‡ / à¨¸à©‹à¨Š
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨‡à¨¸ / à¨‡à¨¸à© / à¨‰à¨† / à¨‰à¨¨ (à¨•â€Œà¨‰) / à¨‰à¨¨à¨¾ / à¨‰à¨¸ / à¨‰à¨¸à© / à¨à¨¸ / à¨“à¨¨à¨¾à© / à¨“à¨¸ / à¨“à¨¸à©
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨…à¨¸à¨—à¨¾ / à¨‡à¨¨ / à¨‡à¨¸ / à¨‰à¨† / à¨‰à¨† (à¨•à¨¾) / à¨‰à¨¨ (à¨•à©€) / à¨‰à¨¨à¨¾ / à¨‰à¨¸ (à¨•à¨¾) / à¨‰à¨¸à¨—à¨¾ / à¨‰à¨¸à© / à¨“à¨¨à¨¾ / à¨“à¨¸à© / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨à¨¾ / à¨¤à¨¿à¨¸à© / à¨µà¨¾ (à¨•à¨¾) (à¨•à©ˆ) (à¨•à©‡)
                    - Instrumental à¨•à¨°à¨£: à¨‡à¨¤à© (à¨•à¨°à¨¿)
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨‡à¨¸ / à¨‡à¨¸à© (à¨†à¨—à©ˆ) / à¨‰à¨¸à© / à¨“à¨¨à¨¾ (à¨ªà¨¿à¨›à©ˆ) / à¨“à¨¸à© / à¨µà¨¾à¨¹à©‚
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨‡à¨¨ / à¨‡à¨¨à¨¿ / à¨‡à¨¹ / à¨‡à¨¹à© / à¨‰à¨¨ / à¨‰à¨¨à¨¿ / à¨‰à¨¹ / à¨‰à¨¹à© / à¨à¨¹ / à¨à¨¹à¨¿ / à¨à¨¹à© / à¨“à¨‡ / à¨“à¨¨à¨¿ / à¨“à¨¨à©€ / à¨“à¨¹ / à¨“à¨¹à¨¾ / à¨“à¨¹à¨¿ / à¨“à¨¹à©€ / à¨“à¨¹à© / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨à¨¹à¨¿ / à¨¤à©‡ / à¨¤à©‡à¨Š / à¨¸à¨¾ / à¨¸à©‡ / à¨¸à©‹ / à¨¸à©‹à¨‡ / à¨¸à©‹à¨ˆ

                    **CoRelative / à¨…à¨¨à©à¨¸à©°à¨¬à©°à¨§ Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨¤à¨¿à¨¸ (à¨¤à©‡)
                    - Accusative à¨•à¨°à¨®: à¨¤à¨¾à¨¸à© / à¨¤à¨¾à¨¸à© (à¨•à¨‰) / à¨¤à¨¾à¨¹à¨¿ / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨à© / à¨¤à¨¿à¨¸à¨¹à¨¿ / à¨¤à¨¿à¨¸à© / à¨¤à¨¿à¨¸à©ˆ / à¨¤à¨¿à¨¹ / à¨¤à©‡ / à¨¤à©ˆ
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨¤à¨¾à¨¸à© / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨ (à¨•à¨‰) / à¨¤à¨¿à¨¨à¨¹à© / à¨¤à¨¿à¨¨à¨¹à©‚ (à¨•à¨‰) / à¨¤à¨¿à¨¨à¨¾ / à¨¤à¨¿à¨¨à¨¾à© / à¨¤à¨¿à¨¸ (à¨•à¨‰) / à¨¤à¨¿à¨¸ (à¨¨à©‹) / à¨¤à¨¿à¨¸ à¨¹à©€ / à¨¤à¨¿à¨¸à¨¹à¨¿ / à¨¤à¨¿à¨¸à© / à¨¤à¨¿à¨¸à©ˆ / à¨¤à¨¿à¨¹ / à¨¤à¨¿à©°à¨¨à¨¾ / à¨¤à©ˆ
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨¤à¨¾ / à¨¤à¨¾à¨¸à© / à¨¤à¨¾à¨¹à©‚ (à¨•à©‹) / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨ (à¨•à©€) / à¨¤à¨¿à¨¨à¨¾ / à¨¤à¨¿à¨¨à¨¾à© / à¨¤à¨¿à¨¨à¨¾à©œà¨¾ / à¨¤à¨¿à¨¨à© / à¨¤à¨¿à¨¸ (à¨•à¨¾) / à¨¤à¨¿à¨¸ (à¨•à©€) / à¨¤à¨¿à¨¸ (à¨•à©‡) / à¨¤à¨¿à¨¸ (à¨¹à¨¿) / à¨¤à¨¿à¨¸ (à¨¹à©€) / à¨¤à¨¿à¨¸à¨¹à¨¿ / à¨¤à¨¿à¨¸à© / à¨¤à¨¿à¨¸à©ˆ / à¨¤à¨¿à¨¹ / à¨¤à©°à¨¨à¨¿ (à¨–à©‡)
                    - Instrumental à¨•à¨°à¨£: à¨¤à¨¿à¨¤à©
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨¤à¨¾à¨¸ / à¨¤à¨¾à¨¸à© / à¨¤à¨¾à¨¹à¨¿ (à¨®à©ˆ) / à¨¤à¨¿à¨¤ (à¨¹à©€) / à¨¤à¨¿à¨¤à© / à¨¤à¨¿à¨¨à¨¿ / à¨¤à¨¿à¨¸à© (à¨®à¨¾à¨¹à¨¿) / à¨¤à¨¿à¨¹à¨¿
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨“à¨‡ / à¨¤à¨¿à¨¨ / à¨¤à¨¿à¨¨ à¨¹à©€ / à¨¤à¨¿à¨¨à¨¹à¨¿ / à¨¤à¨¿à¨¨à¨¹à©€ / à¨¤à¨¿à¨¨à¨¹à©‚ / à¨¤à¨¿à¨¨à¨¿ / à¨¤à¨¿à¨¨à©€ / à¨¤à¨¿à¨¨à© / à¨¤à¨¿à¨¹ / à¨¤à©‡ / à¨¸à¨¾ / à¨¸à¨¾à¨ˆ / à¨¸à¨¿ / à¨¸à© / à¨¸à©‡ / à¨¸à©‡à¨‡ / à¨¸à©‡à¨ˆ / à¨¸à©‹ / à¨¸à©‹à¨ˆ / à¨¸à©‹à¨Š

                    **Indefinite / à¨…à¨¨à¨¿à¨¸à¨šà©‡ à¨µà¨¾à¨šà¨• Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨¸à¨­ (à¨¦à©‚) / à¨¹à¨­à¨¾à¨¹à©‚à©° / à¨¹à©‹à¨°à¨¨à¨¿ / à¨¹à©‹à¨°à¨¿à¨‚à¨“
                    - Accusative à¨•à¨°à¨®: à¨…à¨‰à¨°à¨¨ / à¨…à¨—à¨²à¨¾ / à¨…à¨µà¨° / à¨…à¨µà¨°à¨¹à¨¿ / à¨…à¨µà¨°à¨¾ / à¨…à¨µà¨°à©€ (à¨¨à©‹) / à¨…à¨µà¨°à© / à¨‡à¨•à¨¨à¨¾ / à¨‡à¨•à¨¨à¨¾à© / à¨‡à¨•à¨¿ / à¨‡à¨•à© / à¨‡à¨¤à¨¨à¨¾ (à¨•à©) / à¨‡à¨¤à¨¨à©€ / à¨à¨•à¨¸à©ˆ / à¨à¨•à©€ / à¨à¨¤à¨¾ / à¨à¨¤à©‡ / à¨•à¨›à©à¨† / à¨•à¨¹à¨¾ / à¨•à¨¿ / à¨•à¨¿à¨† (à¨•à¨¿à¨›à©) / à¨•à¨¿à¨›à© / à¨•à¨¿à¨à© / à¨•à¨¿à¨¤à©€ / à¨•à¨¿à¨¸ (à¨¨à©‹) / à¨•à¨¿à¨¸à¨¹à¨¿ / à¨•à¨¿à¨¸à© / à¨•à¨¿à¨¸à©ˆ / à¨•à¨¿à¨¹à© / à¨•à©‹à¨ˆ / à¨˜à¨£à©‡à¨°à©€ / à¨œà©‡à¨¤à¨¾ / à¨œà©‡à¨¤à©€à¨† / à¨¤à©‡à¨¤à¨¾ / à¨¥à©‹à©œà¨¾ / à¨¥à©‹à©œà©€ / à¨¬à¨¹à©à¨¤à¨¾ / à¨¬à¨¹à©à¨¤à© / à¨¬à¨¹à©à¨¤à©‹ / à¨¬à¨¾à¨¹à¨°à¨¾ / à¨¸à¨—à¨² / à¨¸à¨­ / à¨¸à¨­à¨¨à¨¾ / à¨¸à¨­à¨¸à© / à¨¸à¨­à¨¸à©ˆ (à¨¨à©‹) / à¨¸à¨­à¨¿ / à¨¸à¨­à© (à¨•à¨¿à¨›à©) / à¨¸à¨­à© (à¨•à¨¿à¨¹à©) / à¨¸à¨­à©ˆ / à¨¹à¨­ / à¨¹à¨­ (à¨•à¨¿à¨›à©) / à¨¹à¨¿à¨•à© / à¨¹à¨¿à¨•à©‹ / à¨¹à©‹à¨°à¨¨à¨¾ (à¨¨à©‹) / à¨¹à©‹à¨°à¨¸à© / à¨¹à©‹à¨°à©
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨‡à¨•à¨¨à¨¾ / à¨•à¨¹à©€ / à¨•à¨¾à¨¹à©‚ / à¨•à¨¿à¨¨à©ˆ / à¨•à¨¿à¨¸ (à¨¹à©€) / à¨•à¨¿à¨¸à©ˆ / à¨¸à¨­à¨¸à© / à¨¸à¨­à¨¸à©ˆ
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨…à¨µà¨° / à¨‡à¨•à¨¨à¨¾ / à¨‡à¨•à¨¨à¨¾à© / à¨•à¨¾à¨¹à©‚ / à¨•à¨¿à¨¸à©ˆ / à¨•à©ˆà¨¹à©€ / à¨¸à¨­à¨¨à¨¾ / à¨¸à¨­à¨¸à©ˆ
                    - Instrumental à¨•à¨°à¨£: à¨•à¨¾à¨¹à©‚ / à¨•à¨¿à¨¨à©ˆ / à¨¹à©‹à¨°à¨¤à©
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨‡à¨•à¨¨à©€ / à¨•à¨¿à¨¸à© (à¨¨à¨¾à¨²à¨¿)
                    - Nominative à¨•à¨°à¨¤à¨¾: (à¨¹à©‹à¨°) à¨•à©‡à¨¤à©€ / à¨…à¨‰à¨° / à¨…à¨‰à¨°à© (à¨•à©‹) / à¨…à¨¨à©‡à¨• / à¨…à¨µà¨°à¨¿ (à¨¸à¨­à¨¿) / à¨…à¨µà¨°à© (à¨•à¨›à©) / à¨…à¨µà¨°à©‡ / à¨‡à¨•à¨¨à¨¾ / à¨‡à¨•à¨¨à©€ / à¨‡à¨•à¨¨à©ˆ / à¨‡à¨•à¨¿ / à¨‡à¨•à© / à¨à¨• / à¨à¨•à¨¹à¨¿ / à¨à¨•à© / à¨à¨•à©ˆ / à¨•à¨‰à¨£à© / à¨•à¨‰à¨¨à© / à¨•à¨›à© / à¨•à¨¹ / à¨•à¨¹à¨¾ / à¨•à¨¾ / à¨•à¨¾à¨ˆ / à¨•à¨¾à¨¹à©‚ / à¨•à¨¿à¨† / à¨•à¨¿à¨›à© / à¨•à¨¿à¨¤à©€ / à¨•à¨¿à¨¨ (à¨¹à©€) / à¨•à¨¿à¨¨à¨¹à¨¿ / à¨•à¨¿à¨¨à¨¹à©€ / à¨•à¨¿à¨¨à¨¹à©‚ / à¨•à¨¿à¨¨à¨¿ / à¨•à¨¿à¨¨à©ˆ / à¨•à¨¿à¨¸ à¨¹à©€ / à¨•à¨¿à¨¹à© / à¨•à©‡ / à¨•à©‡à¨‡ / à¨•à©‡à¨ˆ / à¨•à©‡à¨¤à¨• / à¨•à©‡à¨¤à¨¾ / à¨•à©‡à¨¤à©‡ / à¨•à©‹ / à¨•à©‹à¨‡ / à¨•à©‹à¨ˆ / à¨•à©‹à¨Š / à¨˜à¨£à©€ / à¨˜à¨£à©‡ / à¨œà©‡à¨¤à©€ / à¨¤à©‡à¨¤à©€ / à¨¬à¨¹à© / à¨¬à¨¹à©à¨¤à¨¾ / à¨¬à¨¹à©à¨¤à©‡à¨°à©€ / à¨µà¨¿à¨°à¨²à©‡ / à¨¸à¨—à¨² / à¨¸à¨—à¨²à©€ / à¨¸à¨—à¨²à©€à¨† / à¨¸à¨—à¨²à©‡ à¨•à©‡ / à¨¸à¨­ / à¨¸à¨­à¨¨à¨¾ / à¨¸à¨­à¨¨à©€ / à¨¸à¨­à¨¹à¨¿ / à¨¸à¨­à¨¾ / à¨¸à¨­à¨¿ / à¨¸à¨­à© (à¨•à¨¿à¨›à©) / à¨¸à¨­à© (à¨•à©‹) / à¨¸à¨­à© (à¨•à©‹à¨‡) / à¨¸à¨­à© (à¨•à©‹à¨ˆ) / à¨¸à¨­à©‡ / à¨¸à¨¾à¨°à©€ / à¨¹à¨­à¨¿ / à¨¹à¨­à©‡ / à¨¹à¨¿à¨•à¨¨à©€ / à¨¹à¨¿à¨•à¨¿ / à¨¹à¨¿à¨•à© / à¨¹à©‹à¨°à¨¿ / à¨¹à©‹à¨°à©

                    **Interrogative / à¨ªà©à¨°à¨¶à¨¨ à¨µà¨¾à¨šà¨• Pronouns â€“ Case Examples**
                    - Accusative à¨•à¨°à¨®: à¨•à¨¹à¨¾ / à¨•à¨¾à¨¹à¨¿ / à¨•à¨¿à¨† / à¨•à¨¿à¨¸à©
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨•à¨¾ (à¨•à¨‰) / à¨•à¨¿à¨¨à¨¾à¨¹ / à¨•à¨¿à¨¸ (à¨•à¨‰) / à¨•à¨¿à¨¸à© / à¨•à©ˆ
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨•à¨¿à¨¸à©
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨•à¨¾ (à¨ªà¨¹à¨¿) / à¨•à¨¾ (à¨¸à¨¿à¨‰) / à¨•à¨¿à¨¸à© (à¨ªà¨¹à¨¿) / à¨•à©ˆ (à¨ªà¨¹à¨¿)
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨•à¨‰à¨£à© / à¨•à¨‰à¨¨ / à¨•à¨µà¨£ / à¨•à¨µà¨¨ / à¨•à¨µà¨¨à© / à¨•à¨µà¨¨à©ˆ / à¨•à¨¿à¨¨à¨¿ / à¨•à©à¨¨à© / à¨•à©‹

                    **Reflexive / à¨¨à¨¿à¨œ à¨µà¨¾à¨šà¨• Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨†à¨ªà¨¸ (à¨¤à©‡) / à¨†à¨ªà¨¹à© / à¨†à¨ªà©Œ
                    - Accusative à¨•à¨°à¨®: à¨…à¨ªà¨¤à© / à¨†à¨ªà¨¤à© / à¨†à¨ªà¨¾ / à¨†à¨ªà©
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨†à¨ªà¨¸ (à¨•à¨‰) / à¨†à¨ªà©ˆ (à¨¨à©‹)
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨…à¨ª / à¨…à¨ªà¨£à¨¾ / à¨…à¨ªà¨¨à¨¾ / à¨…à¨ªà¨¨à©€ / à¨…à¨ªà¨¨à©ˆ / à¨…à¨ªà©à¨¨à¨¾ / à¨…à¨ªà©à¨¨à©€ / à¨†à¨ª / à¨†à¨ªà¨£ / à¨†à¨ªà¨£à¨¾ / à¨†à¨ªà¨£à©ˆ / à¨†à¨ªà¨¨ / à¨†à¨ªà¨¨à¨¾ / à¨†à¨ªà¨¾
                    - Instrumental à¨•à¨°à¨£: à¨†à¨ªà©ˆ (à¨¨à¨¾à¨²à¨¿)
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨†à¨ªà¨¹à¨¿ / à¨†à¨ªà¨¿ / à¨†à¨ªà©ˆ
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨†à¨ª (à¨¹à©€) / à¨†à¨ªà¨¹à¨¿ / à¨†à¨ªà¨¿ / à¨†à¨ªà©€à¨¨à©ˆà© / à¨†à¨ªà©‡ (à¨¹à©€) / à¨†à¨ªà©ˆ

                    **Relative / à¨¸à©°à¨¬à©°à¨§ Pronouns â€“ Case Examples**
                    - Ablative à¨…à¨ªà¨¾à¨¦à¨¾à¨¨: à¨œà¨¿à¨¦à©‚ / à¨œà¨¿à¨¸ (à¨¤à©‡) / à¨œà¨¿à¨¹ (à¨¤à©‡)
                    - Accusative à¨•à¨°à¨®: à¨œà¨¾ (à¨•à¨‰) / à¨œà¨¾à¨¸à© / à¨œà¨¾à¨¹à¨¿ / à¨œà¨¿ / à¨œà¨¿à¨¨ / à¨œà¨¿à¨¨ (à¨•à¨‰) / à¨œà¨¿à¨¨à¨¾ / à¨œà¨¿à¨¨à© / à¨œà¨¿à¨¸à¨¹à¨¿ / à¨œà¨¿à¨¸à© / à¨œà¨¿à¨¹ / à¨œà©‡à¨¹à©œà¨¾ / à¨œà©‹ / à¨œà©‹à¨ˆ à¨œà©‹à¨ˆ / à¨¯à¨¾à¨¸à©
                    - Dative à¨¸à©°à¨ªà©à¨¦à¨¾à¨¨: à¨œà¨¿à¨¨ / à¨œà¨¿à¨¨à¨¾ / à¨œà¨¿à¨¸à¨¹à¨¿ / à¨œà¨¿à¨¸à© / à¨œà¨¿à¨¹ / à¨œà©ˆ
                    - Genitive à¨¸à©°à¨¬à©°à¨§: à¨œà¨¾ / à¨œà¨¾ (à¨•à©ˆ) / à¨œà¨¾ (à¨®à¨¹à¨¿) / à¨œà¨¾à¨¸à© / à¨œà¨¿à¨¨ / à¨œà¨¿à¨¨ (à¨•à©‡) / à¨œà¨¿à¨¨à¨¾ / à¨œà¨¿à¨¨à¨¾ (à¨•à©€) / à¨œà¨¿à¨¨à© / à¨œà¨¿à¨¸ (à¨•à¨¾) / à¨œà¨¿à¨¸ (à¨•à©€) / à¨œà¨¿à¨¸ (à¨•à©‡) / à¨œà¨¿à¨¸à© / à¨œà¨¿à¨¹
                    - Instrumental à¨•à¨°à¨£: à¨œà¨¿à¨¤à© / à¨œà¨¿à¨¹
                    - Locative à¨…à¨§à¨¿à¨•à¨°à¨£: à¨œà¨¿à¨¤à© / à¨œà¨¿à¨¹
                    - Nominative à¨•à¨°à¨¤à¨¾: à¨œà¨¿ / à¨œà¨¿à¨¨ / à¨œà¨¿à¨¨à¨¹à¨¿ / à¨œà¨¿à¨¨à¨¹à© / à¨œà¨¿à¨¨à¨¾ / à¨œà¨¿à¨¨à¨¾à© / à¨œà¨¿à¨¨à¨¿ / à¨œà¨¿à¨¨à©€ / à¨œà¨¿à¨¨à©€à© / à¨œà¨¿à¨¨à© / à¨œà¨¿à¨¹ / à¨œà© / à¨œà©‹ / à¨œà©‹à¨ˆ

                    _Ending note: **â€“à¨‰** is often **omitted** before postpositions like à¨¤à©‹à¨‚, à¨¨à©‚à©°, à¨µà¨¿à¨š, à¨¤à©‡.  
                    e.g., **à¨¤à¨¿à¨¸ à¨¹à¨¥à¨¿** instead of **à¨¤à¨¿à¨¸à© à¨¹à¨¥à¨¿**_
                """).strip() + "\n\n"

            elif entry["Type"] == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£":
                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                # 3-B  IMPLICIT-NOTE  â€“ how to â€œreadâ€ the gloss
                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                implicit_note = textwrap.dedent("""
                    **ADJECTIVES IN GURBÄ€á¹†Äª â€“ AGREEMENT & HINTS FROM THE DARPAN GLOSS**

                    â€¢ An adjective always **agrees in gender & number** with the noun /
                    pronoun it qualifies.  Case is *not* tagged independently for adjectives;
                    if a noun shifts to an oblique form (due to post-positions like
                    `à¨¨à©‚à©°, à¨¤à©‡, à¨¤à©‹à¨‚â€¦`) the adjective may simply copy that *ending*.

                    â€¢ **Look at the helper words the Darpan adds**:
                    - If the gloss inserts a post-position after the noun
                        (*e.g.* â€œto the **good** oneâ€, â€œin the **other** realmâ€), the adjective
                        will mirror whatever oblique ending the noun shows â€“ **but you still
                        classify the adjective only by Gender / Number / Class**.
                    - If the gloss repeats the adjective without a helper,
                        treat the form you see in the verse as the **direct** (base) form.

                    _Quick reminder â€“ common agreement endings_  
                    | Ending-class | Masc.Sg | Fem.Sg | Plural | Notes |
                    |--------------|---------|--------|--------|-------|
                    | **Mukta**    | â€“à¨…      | â€“à¨®à©à¨•à¨¤à¨¾×€ **à¨…** dropped for fem./pl. |
                    | **KannÄ**    | â€“à¨†      | â€“à¨ˆ     | â€“à¨     | |
                    | **SihÄrÄ«**   | â€“à¨¿      | â€“à¨¿      | â€“à©‡      | |
                    | **BihÄrÄ«**   | â€“à©€      | â€“à¨ˆ     | â€“à¨/â€“à¨ˆà¨†à¨‚| |

                    _When in doubt: match what the noun is doing rather than forcing
                    a new inflection on the adjective._
                """).strip() + "\n\n"

                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                # 3-C  COMMON-SENSE-NOTE  â€“ semantic & class sanity
                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                common_sense_note = textwrap.dedent("""
                    **SEMANTIC CHECK â€“ DOES THE LABEL FIT THIS ADJECTIVE?**

                    â‘  **Identify the class** (use the column â€œAdjective Class / à¨µà¨¿à¨¶à©‡à¨¶à¨£ à¨•à¨¿à¨¸à¨®â€):  
                    â€¢ **Qualitative / Descriptive (à¨—à©à¨£ à¨µà¨¾à¨šà¨•)** â€“ *à¨šà©°à¨—à¨¾, à¨¸à©‹à¨¹à¨£à¨¾, à¨•à¨¾à¨²à¨¾*  
                    â€¢ **Demonstrative (à¨¨à¨¿à¨¸à¨¼à¨šà©‡ à¨µà¨¾à¨šà¨•)** â€“ *à¨‡à¨¹, à¨‰à¨¹, à¨‰à¨¹à©€, à¨¦à©‡à¨‰, à¨¦à¨¿à¨¨à©*  
                    â€¢ **Indefinite (à¨…à¨¨à°¿à°¶à¨šà©‡ à¨µà¨¾à¨šà¨•)** â€“ *à¨•à©‹à¨ˆ, à¨•à©ˆ, à¨•à¨‰à¨¨, à¨¸à¨­*  
                    â€¢ **Pronominal**  
                        â€“ *à¨®à©‡à¨°à¨¾, à¨¤à©‡à¨°à¨¾ (possessive) / à¨œà©ˆ, à¨œà¨¿à¨‰ (relative)*  
                    â€¢ **Interrogative (à¨ªà©à¨°à¨¸à¨¼à¨¨ à¨µà¨¾à¨šà¨•)** â€“ *à¨•à¨‰à¨£, à¨•à¨¿à¨¹, à¨•à¨¿à¨‰à©³, à¨•à¨¿à¨µà©‡à¨‚*  
                    â€¢ **Numeral (à¨¸à©°à¨–à¨¿à¨† à¨µà¨¾à¨šà¨•)**  
                        â€“ **Cardinal** *à¨‡à¨•, à¨¦à©‹, à¨¬à©€à¨¹* | **Ordinal** *à¨ªà¨¹à¨¿à¨²à¨¾, à¨¦à©‚à¨œà¨¾, à¨¤à©€à¨œà¨¾â€¦*

                    â‘¡ **Verify agreement** â€“ does the ending you see match the gender &
                    number of the noun in the gloss?  Typical pitfalls:  
                    â€¢ plural nouns paired with singular adjective forms,  
                    â€¢ masculine endings left on a feminine noun after emendation.

                    â‘¢ **Ambiguity guardrails**  
                    â€¢ Many demonstratives (*à¨‡à¨¹, à¨‰à¨¹, à¨¸à©‹â€¦*) double as pronouns â€“ keep them
                        in **Adjective** only when they *modify* a following noun.  
                    â€¢ Some numerals can work adverbially (*à¨¬à¨¹à©à¨¤ à¨­à¨œà©‡*, â€œran a lotâ€) â€“ do not
                        tag those as adjectives.

                    _If two classes seem possible, pick the one that best serves the
                    **function in that specific gloss line** and give one-line reasoning._
                """).strip() + "\n\n"

                ending_cheat_sheet = textwrap.dedent("""\
                **ADJECTIVE ENDINGS â€“ QUICK REFERENCE (GurbÄá¹‡Ä« corpus)**

                ðŸ”¹ **Agreement grid (what can legally combine)**  
                â€¢ **Number / à¨µà¨šà¨¨** â†’ Singular / à¨‡à¨•, Plural / à¨¬à¨¹à©, NA  
                â€¢ **Gender / à¨²à¨¿à©°à¨—** â†’ Masc / à¨ªà©à¨²à¨¿à©°à¨—, Fem / à¨‡à¨¸à¨¤à¨°à©€, Neut / à¨¨à¨ªà©à¨‚à¨¸à¨•, NA  
                â€¢ **Surface ending-classes** â†’ à¨®à©à¨•à¨¤à¨¾, à¨•à©°à¨¨à¨¾, à¨¸à¨¿à¨¹à¨¾à¨°à©€, à¨¬à¨¿à¨¹à¨¾à¨°à©€, à¨¹à©‹à¨°à¨¾, à©, à©‹, à©Œ, NA  
                â€¢ **Sub-classes** â†’ Qualitative, Demonstrative, Indefinite, Possessive-pronom., Pronominal, Interrogative, Numeral (Card & Ord), Diminutive, Negation, Tat-sam, Compound, NA  

                <sub>Adjectives never carry an independent â€œcaseâ€; if the noun is oblique, the adjective just copies that ending.</sub>

                ---

                ### A Â· Canonical ending patterns  

                | Ending-class | Masc Sg | Fem Sg | Plural | Tiny sample from text |
                |--------------|---------|--------|--------|-----------------------|
                | **à¨®à©à¨•à¨¤à¨¾**    | à¨¸à¨¾à¨š**à¨¾** | â€” | à¨¸à¨¾à¨š**à©‡** | **à¨¥à¨¿à¨°à©**, à¨ªà¨µà¨¿à¨¤à©, à¨¬à©‡à¨…à©°à¨¤ |
                | **à¨•à©°à¨¨à¨¾**     | à¨šà©°à¨—**à¨¾** | à¨šà©°à¨—**à©€** | à¨šà©°à¨—**à©‡** | à¨•à¨¾à¨²à¨¾, à¨¨à¨¾à¨®à¨¾, à¨¸à¨¾à¨šà¨¾ |
                | **à¨¸à¨¿à¨¹à¨¾à¨°à©€**   | â€” | â€” | à¨¨à¨¿à¨°à¨®à¨²**à©‡** | à¨¨à¨¿à¨¸à¨¼à¨šà¨¿, à¨…à¨¸à¨²à¨¿ |
                | **à¨¬à¨¿à¨¹à¨¾à¨°à©€**   | à¨¬à¨¾à¨µà¨°**à©€** | à¨¬à¨¾à¨µà¨°**à©€** | à¨¬à¨¾à¨µà¨°**à©€à¨†à¨‚** | à¨²à©‹à¨­à©€, à¨¨à¨¿à¨—à©à¨£à©€ |
                | **à¨¹à©‹à¨°à¨¾**     | à¨¸à©à¨­**à¨‰** | â€” | â€” | à¨‰à¨¤à© (rare) |
                | **à© / à©‹ / à©Œ** | à¨…à¨®à©à¨²**à©** | â€” | â€” | à¨•à¨¾à¨²à©‹, à¨®à¨¿à©±à¨ à©Œ |

                ---

                ### B Â· Sub-class snapshots  

                | Class / à¨•à¨¿à¨¸à¨® | 2-4 high-frequency examples (agreement marked) |
                |--------------|-----------------------------------------------|
                | **Qualitative (à¨—à©à¨£)** | à¨šà©°à¨—à¨¾ (M), à¨šà©°à¨—à©€ (F), à¨šà©°à¨—à©‡ (Pl) â€¢ à¨¥à¨¿à¨°à© (M) â€¢ à¨…à¨®à©à¨²à© (M) |
                | **Demonstrative (à¨¨à¨¿à¨¸à¨¼à¨šà©‡)** | à¨‡à¨¹à© (M Sg), à¨‡à¨¹ (F Sg), à¨‰à¨¹, à¨à¨¹, à¨“à¨¹à© |
                | **Indefinite (à¨…à¨¨à¨¿à¨¸à¨¼à¨šà©‡)** | à¨•à©‹à¨ˆ, à¨•à¨ˆ, à¨¸à¨­, à¨¹à©‹à¨°, à¨˜à¨£à©€ |
                | **Possessive-pronominal** | à¨®à©‡à¨°à¨¾ (M), à¨®à©‡à¨°à©€ (F), à¨®à©‡à¨°à©‡ (Pl) â€¢ à¨…à¨ªà¨£à¨¾ |
                | **Pronominal (relative etc.)** | à¨œà©‹ (F/M), à¨œà¨¿à¨¸à©, à¨œà¨¿à¨¨, à¨¤à¨¿à¨¸à© |
                | **Interrogative (à¨ªà©à¨°à¨¶à¨¨)** | à¨•à¨‰à¨£à© (M Sg), à¨•à¨µà¨£, à¨•à¨¿à¨†, à¨•à¨¿à¨¤à© |
                | **Numeral â€“ Cardinal** | à¨‡à¨•, à¨¦à©à¨‡, à¨ªà©°à¨œ, à¨¦à¨¸, à¨¸à¨‰ |
                | **Numeral â€“ Ordinal** | à¨ªà¨¹à¨¿à¨²à¨¾, à¨¦à©‚à¨œà¨¾, à¨¤à©€à¨œà©€, à¨šà¨‰à¨¥à©ˆ |
                | **Negation** | à¨¨, à¨¨à¨¾à¨¹à©€ |
                | **Tat-sam (à¨¸à©°à¨¸à¨•à©à¨°à¨¿à¨¤ loan)** | à¨…à¨¸à¨²à¨¿, à¨¬à¨°à¨¾à¨¬à¨°à¨¿, à¨¸à¨¤à¨°à¨¿ |
                | **Diminutive** | à¨¬à©°à¨•à©à©œà¨¾, à¨®à©‹à¨¹à¨¿à¨…à©œà©€, à¨¨à¨µà©‡à¨²à©œà©€à¨ |
                | **Compound** | à¨…à¨¨à¨¹à¨¦ à¨§à©à¨¨à¨¿, à¨œà©€à¨µà¨¨ à¨®à©à¨•à¨¤à¨¿, à¨¬à¨¹à© à¨—à©à¨£à¨¿ |

                """).strip() + "\n\n"

            elif entry["Type"] == "Verb / à¨•à¨¿à¨°à¨¿à¨†":
                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                # 4-B  IMPLICIT-NOTE  â€“ how to â€œreadâ€ the gloss
                # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                implicit_note = textwrap.dedent("""\
                **VERBS IN GURBÄ€á¹†Äª â€“ IMPLIED CLUES FROM THE GLOSS**

                Verbs in GurbÄá¹‡Ä« span a wide linguistic spectrumâ€”LahindÄ«, Braj, HindustÄnÄ«, and archaic PanjÄbÄ«. The verse alone often omits explicit markers for **tense, voice, mood, or even subject**. Prof. SÄhib Siá¹…ghâ€™s **Darpan gloss** therefore becomes our decoder ring: it regularly inserts the **hidden agent, auxiliary, or intent** that lets us recover the full verbal meaning.

                ---

                ### âœ” Step 1 Â· Read the gloss literally
                Ask yourself:
                * Is the action **ongoing**, **completed**, or **yet to come**?
                * Is the subject **doing** the action or **receiving** it?
                * Is the clause a **command**, a **wish**, or a **hypothetical**?
                * Do helper words appearâ€”*has, was, should, may, being, let*â€”that hint at aspect or mood?

                ---

                ### âœ” Step 2 Â· Map the gloss cue to a grammatical category

                | Category            | Common cues in the gloss (Eng. gloss)            |
                |---------------------|--------------------------------------------------|
                | **Present**         | do, does, is, are, becomes, gives                |
                | **Past**            | did, was, were, had, gave, came                  |
                | **Future**          | will, shall, would                               |
                | **Imperative**      | (you) give, fall, listen â€” direct command forms  |
                | **Subjunctive**     | if â€¦ may / might / should / let us               |
                | **Passive**         | is called, was given â€” object promoted to subject |
                | **Participles**     | having done, while doing, upon going, imbued     |
                | **Compound/Aux**    | do come, has gone, may go â€” multi-verb chains    |

                ---

                ### ðŸ§  Key heuristics from the Darpan gloss
                * **â€œwas made / is givenâ€** â†’ strong passive signal.  
                * **â€œhas shown / had comeâ€** â†’ perfect aspect; expect past-participle + auxiliary.  
                * If the gloss shows the subject **causing** another to act (*was made to go*) â†’ tag the verb **causative**.

                ---

                ### ðŸ“Œ Postposition surrogates
                Gloss words like *to, by, with, for, from* often reveal an implied **shift in voice** or a **participial/causative chain** hidden in the surface form.

                ---

                ### ðŸ”„ When in doubt
                * Subject absent, object prominent â†’ suspect **passive**.  
                * Two verbs side-by-side (*will come go*, *has been given*) â†’ parse for **compound** or **auxiliary** roles.  
                * Conditional tone (*if â€¦ may â€¦*, *let it be â€¦*) â†’ test for **subjunctive**.

                ---

                ### ðŸ§© Suffix hints  
                Endings like **â€“à¨¹à¨‰, â€“à¨¹à©€, â€“à¨®, â€“à¨¸à©€à¨…** (and LahindÄ« â€“à¨‰, â€“à¨¹à©) can encode person or emphasis. Cross-check with the glossâ€™s subject reference.

                ---

                > **Rule of thumb**  
                > *If the gloss shows something **happening to** someone and the agent is missing â†’ think passive.*  
                > *If multiple verbs are chained, the **right-most** verb usually carries tense/voice; earlier ones express the semantic action.*

                _Use the glossâ€”its hidden auxiliaries, agents, and helpersâ€”to uncover the verbâ€™s true grammatical load._\
                """).strip() + "\n\n"


                common_sense_note = textwrap.dedent("""\
                ### ðŸ”¹ `common_sense_note` â€“ VERBS / à¨•à¨¿à¨°à¨¿à¨† (semantic sanity layer)

                **Essence**â€ƒA sieve that questions every verb label: *Does this person Ã— number Ã— tense truly fit what the verb is doing in the paá¹…ktÄ«?*

                **Vision**â€ƒFuse surface-form clues with syntactic/semantic roles so edge-cases (poetic plurals, ergative flips, auxiliary drop, LahindÄ« quirks) are flagged, not rubber-stamped.

                ---

                ## 1 Â· Finite vs Non-finite: cheat grid  

                | Tag you plan | Sanity checks (abort / relabel if violated) |
                |--------------|---------------------------------------------|
                | **Present / Future** | Ending shows **person+number; no gender**. If ending = â€“à¨¦à¨¾/à¨¦à©€/à¨¦à©‡ **without** auxiliary **à¨¹à©ˆ/à¨¹à¨¨**, treat as participle (habitual/progressive) not finite. |
                | **Imperative** | Only 2nd-person. Command/request mood. If clause is conditional (*à¨œà©‡ à¨¸à©à¨£à¨¹à©â€¦*) â†’ **Subjunctive** not Imperative. |
                | **Subjunctive** | Expresses wish/suggestion; often with *à¨œà©‡, à¨œà©‡à¨•à¨°, à¨¤à¨¾à¨‚*. Never shows gender agreement. |
                | **Past / Perfective** | Built on past-participle endings **â€“à¨† / â€“à¨ˆ / â€“à¨**. Transitive verbs agree with **object** (ergative); intransitives with **subject**. |
                | **Passive finite** | Look for **à¨•à¨°à©€à¨, à¨•à©€à¨† à¨œà¨¾à¨, à¨•à¨¹à©€à¨** etc. Object promoted to subject; auxiliary **à¨•à¨°à©€à¨¨à¨¿, à¨•à¨°à©€à¨** etc. present/past table (Â§ passive pages). |
                | **Causative** | Endings â€“à¨†à¨µà¨¾, â€“à¨¨à¨¾à©³, â€“à¨µà¨‰, â€“à¨à¨‡, â€“à¨µà¨¹à¨¿â€¦; semantics must show *caused* action. |
                | **Auxiliary-only token** | If root **à¨¹à©‹** form (à¨¹à¨¾, à¨¹à©ˆ, à¨¹à¨¾à¨‚, à¨¹à©à©°, à¨¸à©€, à¨¸à©‡, à¨¸à©€à¨, à¨¸à¨¾â€¦) appears **alone**, tag = **Auxiliary Verb** not main finite. |
                *If the Canonical row label is â€œPronominal Suffixes â€¦â€ you **must tag Grammar Case = â€œPronominal Suffixes â€¦â€**, not plain Past/Present.*
                *For finite verbs, **Word-Root must record the person (1st / 2nd / 3rd)**; tense or aspect belongs in â€œGrammar Case / à¨µà¨¯à¨¾à¨•à¨°à¨£,â€ not in Word-Root.*

                ---

                ## 2 Â· Past-participle agreement sanity  

                1. **Intransitive:** participle â†” subject.  
                2. **Transitive (ergative):** participle â†” object; subject in instrumental/obl.  
                3. **Pron.-suffix â€“à¨‰/-à¨¹à©:** when object = **à¨¤à©ˆ/à¨¤à©‚à©°**, endings like **à¨•à©€à¨‰, à¨•à¨¿à¨‰à¨¹à©** act as clitics â†’ tag â€œPronominal-suffixâ€ sub-type.  
                4. Gender/number mismatch with controller â†’ flag for review.

                ---

                ## 2A Â· When gender actually matters  

                * **Finite verbs** (Present, Future, Imperative, Subjunctive, Causative, Auxiliary)  
                  â†’ **never carry masc/fem marks** in SGGS.  *Finite verbs must therefore be tagged **Gender = Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•** (not NA).*

                * **Participles** â€“ the only verb forms that **do** mark gender:  
                  â€¢ Perfect / perfective: **Masc SG -à¨† / Fem SG -à¨ˆ / Masc PL -à¨ / Fem PL -à¨ˆà¨†à¨‚**  
                  â€¢ Habitual / imperfective: **Masc SG -à¨¦à¨¾ / Fem SG -à¨¦à©€ / Masc PL -à¨¦à©‡ / Fem PL -à¨¦à©€à¨†à¨‚**  
                  â€¢ Dialectal allomorphs (à¨²à¨¹à¨¿à©°à¨¦à©€ **-à¨‡à¨“**, à¨¬à©à¨°à¨œ **-à¨¯à©‹**, etc.) are **still Masc SG**.

                * **Controller rule**  
                  â€“ **Intransitive** â†’ participle agrees with **subject**.  
                  â€“ **Transitive perfective** (ergative) â†’ participle agrees with **object**.

                * **Auxiliaries stay neuter.**  `à¨¹à©ˆ/à¨¹à¨¨/à¨¸à©€â€¦` never add gender; only the participle does.

                ---

                ## 3 Â· Auxiliary verbs & silent dropping  

                * Present auxiliaries: **à¨¹à¨¾ (1 sg), à¨¹à©ˆ (2 sg), à¨¹à©ˆ (3 sg), à¨¹à¨¾à¨‚ (1 pl), à¨¹à¨‰/à¨¹à© (2 pl respect), à¨¹à¨¨/hin (3 pl)**.  
                * Past auxiliaries (rare): **à¨¸à¨¾/à¨¸à©‡/à¨¸à©€/à¨¸à¨¿à¨¤, à¨¸à¨¿à¨†, à¨¸à¨¾; 3 pl = à¨¸à©‡, à¨¸à©ˆà¨¨, à¨¸à©€à¨®à¨¾**.  
                * In GurbÄá¹‡Ä« the auxiliary is **often absorbed** into a longer verb with pronominal suffix: *à¨šà¨²à¨¦à¨¿à¨µà©ˆ, à¨­à¨°à¨µà¨¾à¨ˆà¨*. If you canâ€™t locate a free auxiliary, confirm tense via surface ending first.

                ---

                ## 4 Â· Imperative & Subjunctive overlap  

                | Ending cluster | True Imperative ifâ€¦ | Else â†’ likely Subjunctive |
                |----------------|---------------------|---------------------------|
                | **â€“à¨¹à© / â€“à¨¹à©à¨—à©‡ / â€“à¨¹à©‹** | Stand-alone command/request | Used inside conditional/wish |
                | **â€“à¨¹à©‡ / â€“à¨¹à©€ / â€“à¨¹à©‡à¨‡** | Vocative context | Hypothetical clause |

                ---

                ## 5 Â· Passive voice heuristics  

                * **Surface template:** participle (à¨˜à¨²à¨¿à¨†) + auxiliary **à¨•à¨°à©€à¨ / à¨•à¨¹à©€à¨ / à¨•à¨µà¨¾à¨‡à¨“** etc.  
                * Only 3rd-person shows full paradigm in tables; 1st/2nd are scarce â†’ flag if you tag 1st-person finite passive without strong textual evidence.  
                * Present passive often masquerades as adjective; ensure a *patient-as-subject* reading is plausible.

                ---

                ## 6 Â· Causative sanity  

                * First-person causatives: **â€“à¨†à¨µà¨¾ / â€“à¨†à¨µà¨¾, â€“à¨•à¨°à¨¾à¨µà¨¾**. No object â†’ verb likely **inchoative**, not causative.  
                * 3rd-person causatives: **â€“à¨µà¨¾à¨‡à¨†, â€“à¨µà¨§à¨¾à¨‡à¨†, â€“à¨¤à¨¿à¨µà¨¾à¨‡à¨†, â€“à¨ˆà¨¯à©ˆ**: must show agent-causes-other scenario.  
                * If semantic agent = performer, drop â€œcausativeâ€ tag.

                ---

                ## 7 Â· Compound verbs  

                * Earlier element -> conjunct ending **-à¨•à©‡ / -à¨‡ / -à¨† / -à¨•à©‡à¨‚**.  
                * Last element holds tense/person.  
                * Tag first as â€œConjunct Verb / Gerundâ€, second as finite.

                ---

                ## 8 Â· Auto-highlight (red flags)  

                | Pattern | Likely mis-label |
                |---------|------------------|
                | Ending **-à¨—à¨¾/à¨—à©€/à¨—à©‡** but tag â‰  Future | Wrong tense |
                | Ending **-à¨¹à©/-à¨¹à©à¨—à©‡** tagged 1st/3rd person | Imperative bleed |
                | Ending **-à¨¦à¨¾/à¨¦à©€/à¨¦à©‡** with no **à¨¹à©ˆ/à¨¹à¨¨** & tag = Present/Future | Participle, not finite |
                | Two consecutive finite-verb tags inside one clause | Probably compound verb â€“ split roles |
                | Passive participle **à¨•à¨°à©€à¨/à¨•à¨°à¨¾à¨¤à©** but subjectâ€agent reading given | Reverse voice |
                | Finite verb tagged Masc/Fem | Finite forms should be Trans â€“ likely mis-tag |
                | Participial ending gender â‰  controller noun/pronoun | Agreement error (ergative or intransitive mix-up) |
                | Ending-tense combo not found in Canonical table | Illegal combination â€“ override gloss |
                | Finite verb with Gender = NA | Should be Trans â€“ fix label |

                ---

                <sub>Heuristics sourced from pages 5.1 â€“ 5.12: Present, Past, Future, Imperative, Subjunctive, Participles, Compound, Passive, Causative, Auxiliary, Pron-suffix sections.</sub>\
                """).strip() + "\n\n"

                ending_cheat_sheet = textwrap.dedent("""\
                ðŸ”” **Authoritative workflow**

                1ï¸âƒ£ **Check legality** â€“ If a surface ending Ã— person/number Ã— tense combo is **absent** from the
                Canonical table below, reject or relabel.

                2ï¸âƒ£ **Decide meaning** â€“ Among the *legal* options, pick the tag that is **best supported by
                the Darpan Translation and Darpan Meanings** (Prof. SÄhib Siá¹…gh).  
                *Those glosses remain the primary key to tense, mood, voice, and agent/object choice.*

                3ï¸âƒ£ Apply common-sense sanity rules (Â§ 1â€“8) for edge-case flags.

                ---

                **VERB / à¨•à¨¿à¨°à¨¿à¨† ENDINGS â€“ QUICK REFERENCE (GurbÄá¹‡Ä« corpus, Sheet 1)**  

                ðŸ”¹ **Agreement grid (what can legally combine)**  
                â€¢ **Person / à¨ªà©à¨°à¨–** â†’ 1st (à¨‰à©±à¨¤à¨®) | 2nd (à¨®à¨§à¨®) | 3rd (à¨…à¨¨à¨¯)  
                â€¢ **Number / à¨µà¨šà¨¨** â†’ Singular / à¨‡à¨• | Plural / à¨¬à¨¹à©  
                â€¢ **Tense / Mood** â†’ Present / à¨µà¨°à¨¤à¨®à¨¾à¨¨ | Past / à¨­à©à¨¤ | Future / à¨­à¨µà¨¿à©±à¨–à¨¤ | Causative / à¨ªà©‡à©à¨°à¨£à¨¾à¨°à¨¥à¨• | Pronominal suffix  
                <sub>*Finite verbs ignore noun-gender; â€“à¨¦à¨¾/â€“à¨¦à©€/â€“à¨¦à©‡ are participial*</sub>

                ---

                ### A Â· Canonical ending patterns (+ three toy forms on **à¨—à¨¾à¨µ-**)

                | Person Â· Number | Tense / Mood | Surface endings | Micro-examples |
                |-----------------|--------------|-----------------|---------------|
                | **1st Sg** | Present | à¨ˆ/à¨‰/à¨Š/à¨¾/à©€/à¨¤/à¨£à¨¾/à¨¤à¨¾/à¨¦à¨¾/à¨¨à¨¾/à©‡à¨‰/à©°à¨¦à¨¾/à©‡à¨‚à¨¦à©€ | à¨—à¨¾à¨µà¨ˆ, à¨—à¨¾à¨µà¨‰, à¨—à¨¾à¨µà©‡à¨‰ |
                |  | Past | à¨¾/à©€ | à¨—à¨¾à¨µà¨¾, à¨—à¨¾à¨µà©€ |
                |  | Future | à¨‰/à¨Š/à¨¾/à¨¸à¨¾/à¨‰à¨—à¨¾/à¨‰à¨—à©€/à¨‰à¨—à©‹/à©ˆ à¨¹à¨‰ | à¨—à¨¾à¨µà¨‰, à¨—à¨¾à¨µà¨Š, à¨—à¨¾à¨µà¨‰à¨—à¨¾ |
                |  | Causative | à¨µà¨‰/à¨¾à¨ˆ/à¨¾à¨µà¨¾/à¨¾à¨¹à¨¾ | à¨—à¨¾à¨µà¨µà¨‰, à¨—à¨¾à¨µà¨¾à¨ˆ, à¨—à¨¾à¨µà¨¾à¨µà¨¾ |
                |  | Pronominal | à¨®/à¨®à© | à¨—à¨¾à¨µà¨®, à¨—à¨¾à¨µà¨®à© |
                | **1st Pl** | Present | à¨¹/à¨¹à¨¾/à¨¤/à¨¤à©‡/à¨¦à©‡ | à¨—à¨¾à¨µà¨¹, à¨—à¨¾à¨µà¨¤, à¨—à¨¾à¨µà¨¤à©‡ |
                |  | Past | à©‡ | à¨—à¨¾à¨µà©‡ |
                |  | Future | à¨¸à¨¹/à¨¹à¨—à©‡/à¨¹à¨¿à¨—à©‡ | à¨—à¨¾à¨µà¨¸à¨¹, à¨—à¨¾à¨µà¨¹à¨—à©‡ |

                | Person Â· Number | Tense / Mood | Surface endings | Micro-examples |
                |-----------------|--------------|-----------------|---------------|
                | **2nd Sg** | Present | à¨¤/à©ˆ/à¨¸à¨¿/à¨¹à¨¿/à¨¹à©€/à¨¹à©‡/à©‡à¨¹à©€/à¨¦à¨¾ | à¨—à¨¾à¨µà¨¤, à¨—à¨¾à¨µà©ˆ, à¨—à¨¾à¨µà¨¹à¨¿ |
                |  | Past | à¨¾/à©€/à¨¹à© | à¨—à¨¾à¨µà¨¾, à¨—à¨¾à¨µà©€, à¨—à¨¾à¨µà¨¹à© |
                |  | Future | à¨¸à¨¿/à¨¸à©€/à¨¹à¨¿/à¨¹à©€/à¨¹à©‹/à¨¸à¨¹à¨¿/à¨¹à¨¿à¨—à¨¾ | à¨—à¨¾à¨µà¨¸à¨¿, à¨—à¨¾à¨µà¨¸à©€ |
                |  | Causative | à¨¹à¨¿/à¨‡à¨¦à¨¾/à¨‡à¨¹à¨¿ | à¨—à¨¾à¨µà¨¹à¨¿, à¨—à¨¾à¨µà¨‡à¨¦à¨¾ |
                |  | Pronominal | à¨‡/à¨ˆ/à¨¹à¨¿/à¨¹à© | à¨—à¨¾à¨µà¨‡, à¨—à¨¾à¨µà¨ˆ |
                | **2nd Pl** | Present | à¨¹à©/à¨¤ à¨¹à¨‰/à¨¤ à¨¹à©Œ/à¨¤ à¨¹à¨¹à©/à¨ˆà¨…à¨¤ à¨¹à©Œ | à¨—à¨¾à¨µà¨¹à©, à¨—à¨¾à¨µà¨¤ à¨¹à¨‰ |
                |  | Past | à©‡/à¨¹à©‹ | à¨—à¨¾à¨µà©‡, à¨—à¨¾à¨µà¨¹à©‹ |
                |  | Future | à¨¹à©/à©‡à¨¹à©/à¨¹à©à¨—à©‡ | à¨—à¨¾à¨µà¨¹à©, à¨—à¨¾à¨µà©‡à¨¹à© |

                | Person Â· Number | Tense / Mood | Surface endings | Micro-examples |
                |-----------------|--------------|-----------------|---------------|
                | **3rd Sg** | Present | à¨‡/à¨ˆ/à¨/à©ˆ/à¨¤/à¨¤à¨¾/à¨¤à©€/à¨¤à¨¿/à©‡/à¨‚à¨¤/à¨¦à¨¾/à¨¦à©€/à©°à¨¤à¨¾/à¨¸à¨¿/à¨¹à©ˆ | à¨—à¨¾à¨µà¨‡, à¨—à¨¾à¨µà¨ˆ, à¨—à¨¾à¨µà¨¤à©€ |
                |  | Past | à¨¾/à©€ | à¨—à¨¾à¨µà¨¾, à¨—à¨¾à¨µà©€ |
                |  | Future | à¨ˆ/à©ˆ/à¨—à¨¾/à¨—à©€/à¨—à©‹/à¨¸à¨¿/à¨¸à©€ | à¨—à¨¾à¨µà¨—à¨¾, à¨—à¨¾à¨µà¨—à©€ |
                |  | Causative | à¨/à¨ˆà¨/à¨¿à¨µà©ˆ/à¨¿à¨¦à¨¾/à¨¾à¨µà©ˆ | à¨—à¨¾à¨µà¨, à¨—à¨¾à¨µà¨‡à¨¦à¨¾ |
                |  | Pronominal | à¨¨à©/à¨¸à© | à¨—à¨¾à¨µà¨¨à©, à¨—à¨¾à¨µà¨¸à© |
                | **3rd Pl** | Present | à¨¤/à¨¤à©‡/à©°à¨¤à©‡/à¨¦à©‡/à©°à¨¦à©‡/à¨¨à¨¿/à¨¨à©€/à¨¸à¨¿/à¨¹à¨¿/à¨¹à©€/à¨‡à¨¨à¨¿/à¨‡à©°à¨¨à¨¿/à¨¦à©€à¨†/à¨¦à©€à¨†à¨‚ | à¨—à¨¾à¨µà¨¤à©‡, à¨—à¨¾à¨µà¨¦à©‡ |
                |  | Past | à©‡ | à¨—à¨¾à¨µà©‡ |
                |  | Future | à¨¹à¨¿/à¨¹à©€/à¨¸à¨¨à¨¿/à¨¹à¨¿à¨—à©‡ | à¨—à¨¾à¨µà¨¹à¨¿, à¨—à¨¾à¨µà¨¹à¨¿à¨—à©‡ |
                |  | Causative | à¨‡à¨¦à©‡/à¨‡à¨¨à¨¿/à¨µà¨¹à¨¿ | à¨—à¨¾à¨µà¨‡à¨¦à©‡, à¨—à¨¾à¨µà¨µà¨¹à¨¿ |

                ---

                ### B Â· How to use the dashboard  

                1. **Validate annotations** â€“ If you tag a form â€œ2nd Pl Futureâ€ but it ends in **â€“à¨¦à¨¾**, the table shows that combo never occurs â†’ revisit the tag.  
                2. **Debug machine predictions** â€“ Surface ending not found under predicted role â†’ flag for review.  
                3. **Handle sandhi** â€“ Remember silent â€“à¨‰ can drop before postpositions (e.g. **à¨¤à©‹à¨‚, à¨¨à©‚à©°**).  

                _Export or further slicing on request._\
                """).strip() + "\n\n"

            elif entry["Type"] == "Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£":
                implicit_note = textwrap.dedent("""\
                ### ðŸ”¹ `implicit_note` â€“ ADVERB / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à¨¼à©‡à¨¸à¨¼à¨£  
                *(SGGS-centric discovery guide)*  

                **Essence**â€‚Teach the evaluator to recognise words that **modify the *action itself***â€”never the doer (noun) nor the qualityâ€word (adjective).  

                **Vision**â€‚Lean on *Prof. SÄhib Siá¹…ghâ€™s* Darpan gloss to infer *how, when, where* the verb happensâ€”even when SGGS omits explicit post-positions or auxiliaries.  

                ---

                ## 1 Â· Adverb â‰  Adjective â‰  Noun â€” the litmus test ðŸ©º  

                | Ask this first | Pass âœ”ï¸ â†’ Adverb | Fail âœ–ï¸ â†’ something else |
                |----------------|------------------|--------------------------|
                | **Does the word alter the meaning of the verb?** <br>(time, place, manner, measureâ€¦) | âœ”ï¸ modifies *action* â†’ keep testing | âœ–ï¸ modifies noun â†’ likely *Adjective* or *Noun* |
                | **Will the clause stay grammatical if the word is removed?** | âœ”ï¸ sentence remains; nuance lost | âœ–ï¸ structure breaks â†’ maybe pronoun/helper |
                | **Can the word move freely in the clause?** | âœ”ï¸ adverbs float (à©´ à¨¦à¨‡à¨†à¨²à© **à¨¹à©à¨£à¨¿** à¨®à¨¿à¨²à¨¿à¨†) | âœ–ï¸ fixed next to noun â†’ adjective/compound |
                | **Any number/gender inflection visible?** | âœ”ï¸ none (adverbs are **indeclinable**) | âœ–ï¸ â€“ à¨†/â€“à¨ˆ/â€“à¨ etc. â†’ participle/adjective |
                | **Darpan gloss clue** says: â€œnow, then, quickly, here, twiceâ€¦â€ | âœ”ï¸ adopt adverb label | âœ–ï¸ gloss uses â€œof, to, withâ€ â†’ case marker |

                > **Rule:** In this framework an adverb may *expand* a phrase (à¨œà¨—à¨¿ **à¨¸à¨­à¨¤à©ˆ**), but it still targets the action, **not** the noun.  

                ---

                ## 2 Â· Functional buckets ðŸ—‚ï¸  

                | Category (Punjabi) | Core semantic cue | Minimal examples* |
                |--------------------|-------------------|-------------------|
                | **à¨¸à¨®à¨¾ / Time**        | â€˜à¨•à¨¦à©‹à¨‚? à¨•à¨¿à©°à¨¨à¨¾ à¨¸à¨®à¨¾à¨‚?â€™ | à¨¹à©à¨£à¨¿, à¨•à¨¦à©‡, à¨…à¨œà©, à¨¨à¨¿à¨¤, à¨…à¨¹à¨¿à¨¨à¨¿à¨¸à¨¿ |
                | **à¨¥à¨¾à¨‚ / Place**       | â€˜à¨•à¨¿à©±à¨¥à©‡?â€™            | à¨…à¨—à©ˆ, à¨…à©°à¨¦à¨°à¨¿, à¨¦à©‚à¨°à¨¿, à¨¨à©‡à¨°à©ˆ, à¨Šà¨ªà¨°à¨¿ |
                | **à¨µà¨¿à¨§à©€ / Manner**     | â€˜à¨•à¨¿à¨µà©‡à¨‚? à¨•à¨¿à¨¸ à¨¢à©°à¨— à¨¨à¨¾à¨²?â€™ | à¨œà¨¿à¨‰, à¨‡à¨‰, à¨¨à¨¿à¨¸à©°à¨—à©, à¨°à¨¸à¨•à¨¿ à¨°à¨¸à¨•à¨¿ |
                | **à¨ªà¨°à¨®à¨¾à¨£ / Measure**   | â€˜à¨•à¨¿à©°à¨¨à¨¾?â€™            | à¨…à¨¤à¨¿, à¨¬à¨¹à©à¨¤à©, à¨˜à¨£à¨¾, à¨­à¨°à¨ªà©‚à¨°à¨¿ |
                | **à¨¸à©°à¨–à¨¿à¨† / Number**    | â€˜à¨•à¨¿à©°à¨¨à©€ à¨µà¨¾à¨°?â€™        | à¨¬à¨¾à¨°à©° à¨¬à¨¾à¨°, à¨«à¨¿à¨°à¨¿ à¨«à¨¿à¨°à¨¿ |
                | **à¨¨à¨¿à¨¨à©ˆ / Decision**   | certainty / denial  | à¨¨à¨¾à¨¹à¨¿, à¨¨à¨¿à¨¹à¨šà¨‰ |
                | **à¨•à¨¾à¨°à¨£ / Reason**     | causation           | à¨¯à¨¾à¨¤à©‡, à¨•à¨¿à¨¤à© à¨…à¨°à¨¥à¨¿ |
                | **à¨¤à¨¾à¨•à©€à¨¦ / Stress**    | emphasis            | à¨¹à©€, à¨­à©€, à¨®à©‚à¨²à©‡ |

                * A full â€œhigh-freqâ€ tableâ€”including **phrase, compound & iterative** idiomsâ€”follows in *common_sense_note*.

                ---

                ## 3 Â· Zero-inflection principle ðŸš«ðŸ§¬  

                * Adverbs **never** show number (-à¨/-à¨‰), gender, person or case.  
                * If a token **does** decline, re-classify: participial verb (*-à¨¦à¨¾/-à¨¦à©€/-à¨¦à©‡*), adjective, or oblique noun.  

                ---

                ## 4 Â· Typical gloss helpers ðŸ”  

                | Gloss clue | Likely adverb class | Illustration |
                |------------|--------------------|--------------|
                | â€œ**now / today / always**â€ | Time | â€œà¨¹à©à¨£à¨¿ à¨®à¨¿à¨²à¨¿à¨†â€ |
                | â€œ**here / everywhere / within**â€ | Place | â€œà¨…à©°à¨¦à¨°à¨¿ à¨°à¨¹à©ˆâ€ |
                | â€œ**thus / quickly / secretly**â€ | Manner | â€œà¨œà¨¿à¨‰ à¨•à¨°à©‡â€ |
                | â€œ**fully / a little**â€ | Measure | â€œà¨­à¨°à¨ªà©‚à¨°à¨¿ à¨°à©°à¨—à¨¿ à¨°à¨¤à¨¾â€ |
                | â€œ**again / twice**â€ | Number | â€œà¨«à¨¿à¨°à¨¿ à¨«à¨¿à¨°à¨¿ à¨†à¨‡à¨†â€ |

                ---

                ## 5 Â· Quick detection workflow âš¡  

                1. **Mark all gloss adverbials** â€“ scan Darpan for English adverbs.  
                2. **Map to Punjabi surface form** â€“ locate the SGGS token(s) that carry that nuance.  
                3. **Apply indeclinability test** â€“ no visible suffix change? keep as adverb.  
                4. **Check floating mobility** â€“ move token; if syntax survives, adverb confirmed.  
                5. **Edge alert** â€“ if token sits after a post-position (à¨¦à©‡, à¨¨à¨¾à¨²â€¦), probably **oblique noun** not adverb.

                ---

                ## 6 Â· Red-flag heuristics ðŸš©  

                * Word tagged *Adverb* but ends in **-à¨¦à¨¾/-à¨¦à©€/-à¨¦à©‡** â†’ likely participial.  
                * Tagged *Adverb* but gloss shows possession (*of*) â†’ test for Genitive noun.  
                * Compound form **à¨¸à¨¾à¨¸à¨¿ à¨—à¨¿à¨°à¨¾à¨¸à¨¿** mis-tagged as Time/Manner interchangeably â†’ ensure Darpan intent.  
                * Form appears **twice with different endings** in same á¹­uk â†’ must be *declinable* â†’ not adverb.  

                ---

                ### ðŸ“ Footnote on spreadsheet codes  
                The Excel â€œAdverbsâ€ sheet groups every token into **eight functional sets** above, plus **Compound / Phrase** and **Iterative** markers. These codes are referenced only for *high-freq tables* and require **no inflection logic**.

                _Use this guide, then apply the sanity layer in `common_sense_note` for mis-tag traps._
                """).strip() + "\n\n"
            
                common_sense_note = textwrap.dedent("""\
                ### ðŸ”¹ `common_sense_note` â€“ ADVERBS / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à¨¼à©‡à¨¸à¨¼à¨£ (semantic sanity layer)

                **Essence**â€ƒA quick triage: *Does this token truly act as an **adverb**â€”i.e., modifies a verb (or a whole clause) and NEVER a noun/pronoun?*

                **Vision**â€ƒPrevent false-positives caused by:
                * Post-positions or emphatic particles masquerading as adverbs  
                * Adjectival or nominal words that look â€œadverb-ishâ€ but show agreement or case

                ---

                ## 1 Â· Three-step sanity check ðŸ§ª  

                | Step | Ask yourself | Abort / Relabel ifâ€¦ |
                |------|--------------|--------------------|
                | â‘  | **Function** â€“ Does the word modify a **verb or clause** (manner, time, place, degree)? | It directly qualifies a noun/pronoun â†’ likely Adjective or Noun |
                | â‘¡ | **Morphology** â€“ No number / gender / person agreement & no case endings | You see â€“à¨/â€“à¨‰ etc. agreeing with noun â†’ itâ€™s NOT an adverb |
                | â‘¢ | **Position / Helpers** â€“ Is it followed by a postposition (*à¨¦à©‡, à¨¨à©‚à©°, à¨¨à¨¾à¨²*)? | Token + post-position â‡’ treat token as **Noun in oblique**, PP = post-position |

                ---

                ## 2 Â· Category reference with high-frequency SGGS tokens ðŸ”  

                | Category | Typical surface cues | SGGS high-freq examples |
                |----------|----------------------|-------------------------|
                | **Time / à¨¸à¨®à¨¾à¨‚** | â€œwhen?â€, duration, sequence | à¨¹à©à¨£à¨¿, à¨¸à¨¦à¨¾, à¨•à¨¦à©‡, à¨¤à¨¦à¨¿, à¨¸à¨µà©‡à¨°à©ˆ |
                | **Place / à¨¥à¨¾à¨‚** | â€œwhere?â€, location, direction | à¨…à¨—à©ˆ, à¨…à©°à¨¦à¨°à¨¿, à¨¦à©‚à¨°à¨¿, à¨¨à©‡à¨°à©ˆ, à¨Šà¨ªà¨°à¨¿ |
                | **Manner / à¨µà¨¿à¨§à©€** | â€œhow?â€, style, attitude | à¨œà¨¿à¨‰, à¨¸à¨¹à¨œà¨¿, à¨‡à¨‰, à¨•à¨¿à¨µ, à¨¨à¨¿à¨¸à©°à¨—à© |
                | **Measurement / à¨ªà¨°à¨®à¨¾à¨£** | quantity / degree | à¨…à¨¤à¨¿, à¨¬à¨¹à©à¨¤à¨¾, à¨˜à¨£à¨¾, à¨­à¨°à¨ªà©‚à¨°à¨¿, à¨¤à¨¿à¨²à© |
                | **Number / à¨¸à©°à¨–à¨¿à¨†** | frequency / repetition | à¨«à¨¿à¨°à¨¿ à¨«à¨¿à¨°à¨¿, à¨¬à¨¾à¨°à©° à¨¬à¨¾à¨°, à¨µà¨¤à¨¿, à¨²à¨– à¨²à¨–, à¨…à¨¨à¨¿à¨• à¨¬à¨¾à¨° |
                | **Decision / à¨¨à¨¿à¨¨à©ˆ** | negation / affirmation | à¨¨à¨¾, à¨¨à¨¹, à¨¨à¨¾à¨¹à©€, à¨¨à¨¿à¨¹à¨šà¨‰, à¨®à¨¤ |
                | **Reason / à¨•à¨¾à¨°à¨£** | cause / purpose | à¨¯à¨¾à¨¤à©‡ |
                | **Stress / à¨¤à¨¾à¨•à©€à¨¦** | emphasis / focus | à¨¹à©€, à¨­à©€, à¨¹à©ˆ, à¨¸à¨°à¨ªà¨°, à¨®à©‚à¨²à©‡ |
                
                ---

                ### â–¸ Phrase / Compound & Iterative idioms (extended reference)

                | Sub-group | Token set â†’ **all indeclinable adverbs** | Main category |
                |-----------|------------------------------------------|---------------|
                | **Time â€” Phrase** | à¨…à¨¹à¨¿à¨¨à¨¿à¨¸à¨¿, à¨¨à¨¿à¨¸à¨¿ à¨¬à¨¾à¨¸à©à¨°, à¨ªà¨¹à¨¿à¨²à©‹ à¨¦à©‡, à¨ªà¨¿à¨›à©‹ à¨¦à©‡, à¨°à¨¾à¨¤à¨¿ à¨¦à¨¿à¨¨à©°à¨¤à¨¿, à¨…à©°à¨¤ à¨•à©€ à¨¬à©‡à¨²à¨¾, à¨…à¨¬ à¨•à©ˆ à¨•à¨¹à¨¿à¨, à¨†à¨  à¨ªà¨¹à¨°, à¨†à¨¦à¨¿ à¨œà©à¨—à¨¾à¨¦à¨¿, à¨‡à¨¬ à¨•à©‡ à¨°à¨¾à¨¹à©‡, à¨¨à¨¿à¨¤ à¨ªà©à¨°à¨¤à¨¿ | Time / à¨¸à¨®à¨¾ |
                | **Place â€” Phrase** | à¨…à©°à¨¤à¨°à¨¿ à¨¬à¨¾à¨¹à¨°à¨¿, à¨ªà¨¾à¨¸à¨¿ à¨¦à©à¨†à¨¸à¨¿, à¨µà¨¿à¨šà©à¨¦à©‡, à¨†à¨¸ à¨ªà¨¾à¨¸, à¨Šà¨ªà¨°à¨¿ à¨­à©à¨œà¨¾ à¨•à¨°à¨¿, à¨…à¨—à¨¹à© à¨ªà¨¿à¨›à¨¹à©, à¨ˆà¨¹à¨¾ à¨Šà¨¹à¨¾, à¨•à¨¿à¨¤à© à¨ à¨¾à¨‡, à¨¤à¨¿à¨¹à¨¾ à¨§à¨¿à¨°à¨¿, à¨¤à¨¿à©°à¨¹à© à¨²à©‹à¨‡, à¨¦à©‡à¨¸ à¨¦à¨¿à¨¸à©°à¨¤à¨° | Place / à¨¥à¨¾à¨‚ |
                | **Manner â€” Phrase** | à¨¤à¨¾ à¨­à©€, à¨¤à¨¿à¨²à© à¨¸à¨¾à¨°, à¨‡à¨• à¨®à¨¨à¨¿, à¨à¨µà©ˆ, à¨¸à¨¹à¨œ à¨­à¨¾à¨‡, à¨•à¨µà¨¨ à¨®à©à¨–à¨¿, à¨•à¨¾à¨¹à©‡ à¨•à¨‰, à¨•à¨¿à¨‰ à¨¨, à¨•à¨¿à¨¤à© à¨…à¨°à¨¥à¨¿, à¨¨à¨¾à¨¨à¨¾ à¨¬à¨¿à¨§à¨¿, à¨•à¨¿à¨µà©ˆ à¨¨, à¨°à¨¸à¨•à¨¿ à¨°à¨¸à¨•à¨¿ | Manner / à¨µà¨¿à¨§à©€ |
                | **Iterative (Time)** | à¨«à¨¿à¨°à¨¿ à¨«à¨¿à¨°à¨¿, à¨¦à¨¿à¨¨à© à¨¦à¨¿à¨¨à©, à¨¸à¨¦à¨¾ à¨¸à¨¦à¨¾, à¨¸à¨¾à¨¸à¨¿ à¨¸à¨¾à¨¸à¨¿, à¨¨à¨¿à¨¤ à¨¨à¨¿à¨¤, à¨¨à¨¿à¨®à¨– à¨¨à¨¿à¨®à¨–, à¨ªà¨²à© à¨ªà¨²à©, à¨¬à¨¾à¨°à©° à¨¬à¨¾à¨°, à¨ªà©à¨¨à¨¹ à¨ªà©à¨¨à¨¹ | Time / à¨¸à¨®à¨¾ |
                | **Iterative (Place)** | à¨œà¨¤ à¨•à¨¤, à¨˜à¨°à¨¿ à¨˜à¨°à¨¿, à¨œà¨¹ à¨œà¨¹, à¨œà¨¿à¨¤à© à¨œà¨¿à¨¤à©, à¨¦à©‡à¨¸ à¨¦à¨¿à¨¸à©°à¨¤à¨°à¨¿ | Place / à¨¥à¨¾à¨‚ |
                | **Iterative (Manner)** | à¨à¨¿à¨®à¨¿ à¨à¨¿à¨®à¨¿, à¨¤à¨¿à¨² à¨¤à¨¿à¨², à¨–à¨¿à¨° à¨–à¨¿à¨°, à¨°à¨¸à¨¿à¨• à¨°à¨¸à¨¿à¨•, à¨²à©à¨¡à¨¿ à¨²à©à¨¡à¨¿ | Manner / à¨µà¨¿à¨§à©€ |

                *(Duplicates collapsed; diacritics kept as in SGGS.)*

                ---

                ## 3 Â· Red-flag heuristics ðŸš¨  

                | Pattern | Likely mis-tag |
                |---------|---------------|
                | Token shows **plural/oblique â€“à¨†à¨‚ / â€“à¨ / â€“à¨‰** agreement | Probably a noun or adjective |
                | Token immediately followed by post-position (**à¨¨à¨¾à¨², à¨¤à©‡, à¨µà¨¿à¨š**) | Treat as noun + PP |
                | Token doubles as **auxiliary verb** (*à¨¹à©€, à¨¹à©ˆ*) in context | Re-evaluate as Stress adverb OR auxiliary |
                | Same stem appears with changing endings inside verse | Likely **declinable adjective**, not adverb |
                | Gloss marks token as **object / subject** | Not an adverb |

                ---

                ## 4 Â· Usage tips ðŸ’¡  

                1. **No gender/number tags** â€“ Always set **Gender = NA** & **Number = NA** for adverbs.  
                2. **POS override wins** â€“ If sanity check fails, switch POS before finishing the task.  
                3. Quote at least one verb the adverb is modifying when you justify your choice.

                ---

                <sub>Source pages: Grammar book ch. 6 (pp. 6.1â€“6.2.6) & â€œAdverbsâ€ sheet from 0.2 For Data to GPT.xlsx.</sub>\
                """).strip() + "\n\n"

                ending_cheat_sheet = (
                    "**ADVERBS:** Indeclinable in SGGS â†’ no ending table required."
                )

            elif entry["Type"] == "Postposition / à¨¸à©°à¨¬à©°à¨§à¨•":
                implicit_note = textwrap.dedent("""\
                    **POSTPOSITIONS IN GURBÄ€á¹†Äª â€“ SEEING THE HIDDEN LINKS**  

                    A postposition (_à¨¸à©°à¨¬à©°à¨§à¨•_) expresses the *relationship* of a noun or pronoun to the
                    rest of the clause.  Think of it as a Punjabi sibling of the English preposition,
                    except it normally **follows** the word it governs.

                    ### 1 Â· Why they matter in annotation  
                    â€¢ **Old case-endings â†’ new helpers** â€“ Classical Punjabi often fused case endings
                    straight onto the noun (e.g. à¨•à©ˆ, à¨•à¨‰).  Over centuries these endings began to act
                    like separate postpositionsâ€”and GurbÄá¹‡Ä« preserves *both* layers.  
                    â€¢ **One helper â‰  one case** â€“ Donâ€™t map â€œeach postposition to one caseâ€ by reflex.
                    Many helpers (esp. â€˜ofâ€™, â€˜fromâ€™, â€˜withâ€™) sit across **multiple traditional cases**.  
                    â€¢ **Pre-noun surprise** â€“ Forms such as **à¨•à©ˆ** can surface *before* the noun when
                    they co-occur with another postposition; still tag them as postpositions.

                    ### 2 Â· How to read the Darpan gloss  
                    1. **Scan the English helper** inserted by Prof. SÄhib Siá¹…gh â€“ _to, of, from,
                    with, without, in, on, before, after, near, farâ€¦_  
                    2. **Locate the Punjabi token(s)** that deliver that meaning in the pÄá¹…ktÄ«.
                    They may be:  
                    â€¢ an **attached ending** (*â€¦à¨•à©ˆ à¨¸à©°à¨¤*),  
                    â€¢ a **stand-alone word** (*à¨¨à¨¾à¨², à¨µà¨¿à¨š, à¨‰à¨ªà¨°à¨¿*), or  
                    â€¢ an **archaic variant** (e.g. _à¨•à¨¹, à¨µà¨¸à©‡, à¨¬à¨¾à¨¸à©‡_).  
                    3. **Check the noun form** â€“ the governed noun should be in the **oblique** (à¨¸à©°à¨¬à©°à¨§à¨•)
                    if the language still marks one; otherwise, rely on meaning.

                    > **Rule of thumb** â€“ If the gloss supplies a relational word the verse omits,
                    > treat that English word as a flag that â€œa postposition is hiding here.â€\
                    """).strip() + "\\n\\n"

                common_sense_note = textwrap.dedent("""\
                    **SEMANTIC SANITY CHECK â€“ IS THIS *REALLY* A POSTPOSITION?**  

                    ### â‘   Function test  
                    â€¢ Does the candidate **link** its noun/pronoun to the verb or another noun?  
                    _Yes_ â†’ proceed.  _No_ â†’ it may be an **adverb**, **case-suffix**, or even
                    part of a **compound noun**.

                    ### â‘¡  Morphology test  
                    â€¢ Postpositions are **indeclinable** â€“ no gender/number/person endings of their
                    own.  If the token shows â€“à¨†/à¨ˆ/à¨ etc., suspect an *oblique noun* instead.  
                    â€¢ Possessive markers **à¨¦à¨¾, à¨¦à©‡, à¨¦à©€** *look* like adjectives but behave as
                    postpositions.  Tag them here only when they attach to another noun
                    (â€œà¨°à¨¾à¨® **à¨¦à¨¾** à¨¦à¨¾à¨¸â€).  

                    ### â‘¢  Dependency test  
                    â€¢ A true postposition normally keeps a **dependent noun** close by.  If none
                    appears, ask whether the word is actually an **adverbial particle** (â€œà¨¤à¨¦à¨¿,
                    à¨…à¨—à©ˆâ€) or part of a **verb phrase**.

                    ### â‘£  Red-flag heuristics ðŸš©  
                    | Pattern | Likely mis-tag | Example cue |
                    |---------|---------------|-------------|
                    | Token plus **another postposition** with no noun in between | Missing oblique noun | â€œà¨•à©ˆ **à¨¨à¨¾à¨²**â€ |
                    | Token followed by *à¨¹à©ˆ/à¨¹à¨¨* | Probably predicate adjective | â€œà¨¨à¨¾à¨¨à¨•à© à¨¦à©‹à¨–à©€ **à¨¨à¨¾à¨¹à¨¿**â€ |
                    | Token appears twice with changing endings | Declining noun, not postposition | â€œà¨˜à¨°à¨¿ à¨˜à¨°à¨¿â€ |

                    ### â‘¤  Quick role alignment  
                    | Semantic role | Common helpers (non-exhaustive) |
                    |---------------|----------------------------------|
                    | **Genitive / OF** | à¨•à¨¾, à¨•à©‡, à¨•à©€, à¨¦à¨¾, à¨¦à©‡, à¨¦à©€, à¨•à©‹à¨°à¨¾ |
                    | **Dative / TO, FOR** | à¨•à¨‰, à¨•à©‹, à¨•à©ˆ, à¨¨à©‚, à¨²à¨ˆ |
                    | **Ablative / FROM** | à¨¤à©‹à¨‚, à¨¤à©‡, à¨µà©ˆà¨¹à©, à¨¬à¨¿à¨¨, à¨¬à¨¾à¨¹à¨° |
                    | **Instrumental / WITH** | à¨¨à¨¾à¨², à¨¸à©°à¨—, à¨¸à¨¾à¨¥, à¨¸à¨¿à¨‰, à¨¸à©‡à¨¤à©€ |
                    | **Locative / IN, ON, AT** | à¨µà¨¿à¨š, à¨…à©°à¨¦à¨°à¨¿, à¨®à¨¾à¨¹à¨¿, à¨‰à¨ªà¨°à¨¿, à¨Šà¨¤à©‡ |
                    | **Orientational / BEFORE, AFTER, NEAR, FAR** | à¨…à¨—à©ˆ, à¨ªà¨¿à¨›à©ˆ, à¨•à©‹à¨², à¨¨à¨¿à¨•à¨Ÿ, à¨¦à©‚à¨°à¨¿ |

                    _If a helper can sit in more than one row, choose the case that best matches the
                    **meaning of the clause**, and note the alternative in comments._\
                    """).strip() + "\\n\\n"
                
                ending_cheat_sheet = textwrap.dedent("""\
                    **POSTPOSITION QUICK-REFERENCE â€“ SURFACE FORMS BY SEMANTIC GROUP**  

                    | Role (Eng.) | Core Punjabi forms* | Notes |
                    |-------------|---------------------|-------|
                    | **OF / Possessive** | à¨¦à¨¾, à¨¦à©‡, à¨¦à©€ Â· à¨•à¨¾, à¨•à©‡, à¨•à©€ Â· à¨•à¨¾, à¨•à©ˆ, à¨•à©ˆà¨¹à¨¿à¨‰ Â· à¨•à©‹à¨°à¨¾ / à¨•à©‹à¨°à©ˆ | Masculine/Feminine variants; decline with possessed noun, not with owner |
                    | **TO / FOR** | à¨•à¨‰, à¨•à©‚, à¨•à©ˆ, à¨•à©‹ Â· à¨¨à©‚, à¨¨à©‚à©° Â· à¨²à¨ˆ | Older endings (à¨•à¨‰â€¦) often fuse; **à¨¨à©‚à©°** modern |
                    | **FROM / OUT OF** | à¨¤à©‹à¨‚, à¨¤à©‡, à¨‰à¨¤à©‹à¨‚, à¨µà©ˆà¨¹à©, à¨¬à¨¾à¨¹à¨°, à¨¬à¨¿à¨¨à¨¾ | Ablative / separative sense; *à¨¬à¨¿à¨¨à¨¾* also â€œwithoutâ€ |
                    | **WITH / BY / ALONG** | à¨¨à¨¾à¨², à¨¨à¨¾à¨²à©‡, à¨¸à©°à¨—, à¨¸à¨¾à¨¥, à¨¸à¨¿à¨‰, à¨¸à©‡à¨¤à©€ | Instrumental & associative; choice shaped by metre |
                    | **WITHOUT / THAN** | à¨¬à¨¾à¨œà¨¹à©, à¨¬à¨¾à¨—à©ˆ, à¨¬à¨¿à¨¨, à¨¬à¨¿à¨¨à©, à¨µà¨¿à¨£, à¨µà¨¿à¨£à¨¹à©, à¨¥à©‹à©œà¨¾ | Negative / comparative nuance |
                    | **IN / INSIDE / WITHIN** | à¨µà¨¿à¨š, à¨µà¨¿â¸±à¨š, à¨…à©°à¨¦à¨°à¨¿, à¨®à¨¾à¨¹à¨¿, à¨®à¨¹à¨¿, à¨®à¨¾à¨¹à¨°à©ˆ | Locative & internal |
                    | **ON / OVER / ABOVE** | à¨‰à¨ªà¨°à¨¿, à¨‰à¨ªà¨°, à¨‰à¨¤à©‡, à¨Šà¨¤à©‡, à¨Šà¨ªà¨°à¨¿ | Spatial elevation; *à¨¤à©‡* doubles as generic PP |
                    | **UNDER / BELOW** | à¨¤à¨²à¨¿, à¨¥à¨²à©ˆ, à¨¹à©‡à¨ , à¨¹à©‡à¨ à¨¾à¨‚ | Lower level |
                    | **BEFORE / FRONT** | à¨…à¨—à©ˆ, à¨…à¨—à©‡ | Temporal or spatial precedence |
                    | **AFTER / BEHIND** | à¨ªà¨¿à¨›à©ˆ, à¨ªà¨¾à¨›à©ˆ, à¨ªà¨¿à¨›à©‹ | Temporal or spatial following |
                    | **TOWARDS / NEAR / FAR** | à¨µà¨², à¨•à¨¨, à¨•à©‹à¨², à¨•à©‹à¨²à©€, à¨¨à¨¿à¨•à¨Ÿ, à¨ªà¨¾à¨¸à¨¿, à¨ªà¨¾à¨¸à©‡, à¨¦à©‚à¨°à¨¿ | Directional & proximity |

                    <sub>*Forms collated from pp. 1-7 of your textbook; diacritics left as printed.
                    The list is not exhaustiveâ€”add dialectal or Braj variants as you meet them.</sub>

                    **Oblique rule** â€“ The governed noun normally appears in the **oblique**; the
                    postposition itself **never inflects**.

                    **Pre-noun exception** â€“ When **à¨•à©ˆ** precedes another PP, it may surface *before*
                    its noun (e.g. â€œà¨®à©°à¨¨à©‡ à¨œà¨® **à¨•à©ˆ** à¨¸à¨¾à¨¥ à¨¨ à¨œà¨¾à¨‡â€) â€“ still tag as postposition.

                    **Cross-case cautions**  
                    â€¢ Some helpers (esp. â€œwithâ€, â€œinâ€, â€œfromâ€) can realise **Instrumental, Locative,
                    or Ablative** â€“ decide by semantics.  
                    â€¢ Genitive set **à¨¦à¨¾/à¨¦à©‡/à¨¦à©€** functions like an adjective in modern speech but
                    grammatically remains a postposition in SGGS.

                    _Use this sheet to *reject impossible guesses* and to **confirm legal surface
                    forms** before finalising your annotation._\
                    """).strip() + "\\n\\n"

            elif entry["Type"] == "Conjunction / à¨¯à©‹à¨œà¨•":
                implicit_note = textwrap.dedent("""\
                    **CONJUNCTIONS IN GURBÄ€á¹†Äª â€“ HOW TO HEAR THE HINGES**

                    A conjunction (_à¨¯à©‹à¨œà¨•_) links words, phrases, or entire clausesâ€”*and, but, or,
                    if â€¦ then, even thoughâ€¦. *  GurbÄá¹‡Ä« uses a small core set, but the
                    multilingual texture of the text supplies many **variants** (à©²à©ˆ, à¨…à¨¤à©‡, à¨…à¨‰,
                    à¨«à©à¨¨à¨¿; à¨œà©‡, à¨œà©‡à¨•à¨°; à¨¤à¨¾, à¨¤à¨¾à¨‚, à¨¤à¨­).

                    #### 1 Â· Spotting them in the verse
                    1. **Look for clause boundaries** â€“ commas or the metrical â€œ||â€ often signal the
                    join.  
                    2. **Map the gloss cue** â€“ Prof. SÄhib Siá¹…gh frequently inserts
                    *and / but / or / if / then / even*, etc.  Trace that helper back to a Punjabi
                    token (sometimes a tiny vowel like **à¨¤, à¨œà©‡, à¨¤à©‡**).  
                    3. **Check the flow** â€“ removing a true conjunction should split the sentence
                    into two meaningful parts; if the sense collapses, the token may be an
                    **adverb** (*à¨¤à©Œà¨‚ = then* vs. *à¨¤à©‹à¨‚ = from*), **post-position**, or **particle**.

                    > **Rule of thumb** â€“ If the gloss supplies an English linker and the Punjabi
                    > token neither declines nor carries case, youâ€™ve found a conjunction.
                    """).strip() + "\\n\\n"
                
                common_sense_note = textwrap.dedent("""\
                    **SEMANTIC SANITY CHECK â€“ DOES THIS REALLY JOIN THINGS?**

                    | Quick test | Keep as conjunction âœ”ï¸Ž | Rethink âœ˜ |
                    |------------|------------------------|-----------|
                    | **Function** | Links two clauses / words of equal status | Adds a helper to a noun (*post-position*) |
                    | **Morphology** | Indeclinable; no gender/number | Ends -à¨†/-à¨ˆ/-à¨ â†’ likely adjective/noun |
                    | **Mobility** | Can often move to clause edge without breaking grammar | Locked to noun it follows â†’ PP/adjective |
                    | **Gloss cue** | gloss shows *and, but, or, if â€¦ then* | gloss shows *to, of, from* â†’ case helper |

                    #### Red-flag patterns ðŸš©
                    * Token plus **post-position** (e.g. *à¨œà©‡ à¨•à©‹*): maybe *à¨œà©‡* = â€œifâ€ (OK) but *à¨•à©‹* =
                    Dative â†’ label both separately.  
                    * **à¨¨à©€â€¦à¨¨à¨¾** or **à¨¨à©‹â€¦à¨¨à©‹** â€“ might be emphatic repetition, not conjunction.  
                    * **à¨¤à¨¾/à¨¤à©‡/à¨¤à©‹à¨‚**: confirm rÃ´leâ€”*à¨¤à¨¾* = â€œthenâ€, *à¨¤à©‡* often Locative PP, *à¨¤à©‹à¨‚* Ablative.
                    """).strip() + "\\n\\n"
                
                ending_cheat_sheet = textwrap.dedent("""\
                    **CONJUNCTION QUICK-REFERENCE â€“ HIGH-FREQ FORMS IN SGGS**

                    | Logical role | Punjabi forms* | Example gloss cue |
                    |--------------|---------------|-------------------|
                    | **AND / THEN** | à¨¤à©‡, à¨…à¨¤à©‡, à¨…à¨¤à¨¿, à¨…à¨‰, à¨…à¨µà¨°, à¨…à¨‰à¨°à©, à¨«à©à¨¨à¨¿ | â€œandâ€, â€œthenâ€, â€œalsoâ€ |
                    | **OR** | à¨•à©ˆ, à¨•à¨¿, à¨…à¨•à©‡ | â€œor / whetherâ€ |
                    | **BUT / HOWEVER** | à¨˜à¨Ÿ, à¨ªà¨°, à¨ªà¨°à©°à¨¤à©‚, à¨«à©à¨¨à¨¿ | â€œbutâ€, â€œyetâ€ |
                    | **IF** | à¨œà©‡, à¨œà©‡à¨•à¨°, à¨œà©‡à¨µà©€ | â€œif / provided thatâ€ |
                    | **IF â€¦ THEN** | à¨œà©‡ â€¦ à¨¤à¨¾/à¨¤à¨¾à¨‚/à¨¤à©‹à¨‚ | paired correlative |
                    | **EVEN IF / EVEN THEN** | à¨¤, à¨œà©‡, à¨­à¨¾à¨µà©‡, à¨¤à¨‰ à¨­à©€, à¨¤à¨‰, à¨¤à¨‰à¨‚ | concessive |
                    | **NEITHER â€¦ NOR** | à¨¨ â€¦ à¨¨à¨¾ | correlative negative |
                    | **OTHERWISE** | à¨¨à¨¤ à¨°à¨¿, à¨¨à¨¤à©‚, à¨¨à¨¹à©€à¨‚, à¨¨à¨¹à©€à¨‚ à¨¤à¨¾à¨‚ | â€œotherwiseâ€ |
                    | **THEREFORE / HENCE** | à¨¤à¨¾, à¨¤à¨¾ à¨¤à©‡, à¨¤à¨¸à©‚, à¨•à¨¾ à¨¤à©‡ | result / inference |
                    | **AS / LIKE** | à¨œà¨¿à¨‰, à¨œà¨¿à¨µà©‡à¨‚ | comparative |
                    | **LEST** | à¨®à¨¤à© | preventative |

                    <sub>*Forms taken from textbook pp. 8.1 â€“ 8.4; diacritics preserved.</sub>

                    **Key reminders**

                    * **Indeclinable** â€“ conjunctions never carry case or agreement.
                    * **Dual tokens** â€“ Some forms (*à¨¤à¨¾, à¨¤à©‡, à¨¤à©‹à¨‚*) double as post-positions.
                    Decide by context: if it *links* clauses â†’ conjunction; if it *marks* a noun
                    â†’ post-position.
                    * **Correlative pairs** â€“ Tag both halves (e.g. **à¨œà©‡** â€¦ **à¨¤à¨¾à¨‚**) as one
                    logical conjunction with a note â€œcorrelativeâ€.
                    """).strip() + "\\n\\n"
                
            elif entry["Type"] == "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•":
                implicit_note = textwrap.dedent("""\
                    **INTERJECTIONS IN GURBÄ€á¹†Äª â€“ PURE, UNINFLECTED EMOTION**

                    An interjection (_à¨µà¨¿à¨¸à¨®à¨¿à¨•_) erupts outside normal grammar to voice **feeling**:
                    surprise, pain, devotion, blessing, aweâ€¦  Because they sit *outside* the clause
                    structure, they **never govern case, never inflect, never agree**.

                    #### 1 Â· What to notice in a verse
                    1. **Standalone or comma-bound** tokens â€“ often at the start, end, or mid-clause,
                    separated by a breve pause.  E.g. **à¨µà¨¾à¨¹à© à¨µà¨¾à¨¹à©**, **à¨¹à©ˆ à¨¹à©ˆ**, **à¨¹à¨°à¨¿ à¨¹à¨°à¨¿**.
                    2. **Gloss cue** â€“ Prof. SÄhib Siá¹…gh usually inserts an English exclamation
                    (*O!, Alas!, Wow!, Blessed!*) or italicises the Punjabi for emphasis.
                    3. **No syntactic load** â€“ if you remove the interjection, the grammar of the
                    sentence remains intact (though colour is lost).

                    #### 2 Â· Ten broad emotional classes in SGGS
                    1. **Vocative** â€“ calling or invoking (*à¨, à¨, à¨“, à¨¹à©ˆ, à¨¹à¨‰, à¨¹à©‡ à¨œà©€â€¦*).  
                    2. **Repulsive** â€“ aversion or disgust (*à¨µà¨¿à¨šà©, à¨«à¨¿à¨Ÿà©*).  
                    3. **Painful** â€“ sorrow, lament (*à¨¹à¨¾ à¨¹à¨¾, à¨¹à¨¾à¨ à¨¹à¨¾à¨, à¨¹à©ˆ à¨¹à©ˆ*).  
                    4. **Submission** â€“ â€˜Divine willingâ€™ (*à¨…à¨²à¨¹*).  
                    5. **Wondrous** â€“ ecstatic awe (*à¨µà¨¾à¨¹à© à¨µà¨¾à¨¹à©, à¨µà¨¾à¨¹ à¨­à©ˆà¨°à©€*).  
                    6. **Caution / Warning** â€“ prudent cry (*à¨¹à¨°à¨¿ à¨¹à¨°à¨¿ à¨¹à¨°à©‡* used admonishingly).  
                    7. **Blessing** â€“ goodwill (*à¨œà©à¨—à© à¨œà©à¨—à© à¨œà©€à¨µà¨¹à©*).  
                    8. **Curse** â€“ condemnation (*à¨œà¨²à¨‰, à¨œà¨²à¨¿ à¨œà¨¾à¨‰*).  
                    9. **Sacrificial** â€“ self-offering (*à¨¬à¨²à¨¿à¨¹à¨¾à¨°à©‡, à¨¬à¨²à¨¿ à¨¬à¨²à¨¿*).  
                    10. **Reverence** â€“ respectful welcome (*à¨†à¨‡ à¨œà©€, à¨ªà¨¿à¨›à©‹ à¨œà©€*).

                    > **Rule of thumb** â€“ if the word communicates *only* emotion and detaches
                    > cleanly from clause syntax, tag it as Interjection; otherwise test Adverb,
                    > Vocative Noun, or Particle.
                    """).strip() + "\\n\\n"

                common_sense_note = textwrap.dedent("""\
                    **SEMANTIC SANITY CHECK â€“ IS THIS TOKEN *JUST* AN EMOTION?**

                    | Quick probe | Keep as Interjection âœ” | Rethink âœ– |
                    |-------------|-----------------------|-----------|
                    | **Function** | Adds emotional colour, no syntactic role | Performs grammatical work (case, link, inflection) |
                    | **Inflection** | Completely indeclinable | Shows â€“à¨† / â€“à¨ˆ / â€“à¨ endings â†’ maybe adjective/noun |
                    | **Dependence** | Can float; removal leaves clause intact | Sentence breaks â†’ probably verb/particle |
                    | **Gloss cue** | Gloss marks â€œO!â€, â€œAlas!â€, â€œBlessed!â€ etc. | Gloss gives â€œto, from, withâ€ â†’ post-position |

                    #### Red-flag patterns ðŸš©
                    * **à¨µà¨¾à¨¹à© à¨µà¨¾à¨¹à©** appears as noun/adjective elsewhere â€“ decide per context.  
                    * **à¨¹à©ˆ à¨®à©ˆ, à¨¹à©‡ à¨­à¨¾à¨ˆ** â€“ first token vocative interjection, second token noun;
                    split tags, donâ€™t bundle.  
                    * Repeated **à¨¹à¨°à¨¿ à¨¹à¨°à¨¿** could be mantra (noun) *or* caution interjection â€“
                    weigh meaning.

                    _For every interjection, fill **Number = NA** and **Gender = NA**; they never
                    agree with anything._
                    """).strip() + "\\n\\n"
                
                ending_cheat_sheet = textwrap.dedent("""\
                    **INTERJECTION QUICK-REFERENCE â€“ FREQUENT FORMS BY EMOTIONAL CLASS**

                    | Class               | High-frequency tokens* (SGGS spelling)        |
                    |---------------------|----------------------------------------------|
                    | **Vocative**        | à¨, à¨, à¨“, à¨“à¨¹, à¨¹à©‡, à¨¹à©ˆ, à¨¹à¨‰, à¨¹à¨²à©ˆ, à¨®à©à¨¸à©ˆ, à¨œà©€, à¨°à©‡, à¨¬à©‡ |
                    | **Repulsive**       | à¨µà¨¿à¨šà©, à¨«à¨¿à¨Ÿà©                                   |
                    | **Painful**         | à¨¹à¨¾ à¨¹à¨¾, à¨¹à¨¾à¨ à¨¹à¨¾à¨, à¨¹à©ˆ à¨¹à©ˆ, à¨à©‚à¨…à¨¹ à¨¬à©‚à¨¢à¨¹           |
                    | **Submission**      | à¨…à¨²à¨¹                                          |
                    | **Wondrous**        | à¨µà¨¾à¨¹à© à¨µà¨¾à¨¹à©, à¨µà¨¾à¨¹ à¨µà¨¾à¨¹, à¨µà¨¾à¨… à¨µà¨¾à¨…, à¨µà¨¹à© à¨µà¨¹à©, à¨µà¨¾à¨¹ à¨­à©ˆ, à¨µà¨¹à© à¨µà¨¹à© |
                    | **Caution / Warning** | à¨¹à¨°à¨¿ à¨¹à¨°à¨¿ à¨¹à¨°à©‡, à¨¹à¨°à©‡ à¨¹à¨°à©‡                       |
                    | **Blessing**        | à¨œà©à¨—à© à¨œà©à¨—à© à¨œà©€à¨µà¨¹à©, à¨œà©à¨—à© à¨œà©à¨—à© à¨œà©€à¨µà©ˆ              |
                    | **Curse**           | à¨œà¨²à¨‰, à¨œà¨²à¨¿ à¨œà¨¾à¨‰, à¨œà¨²à¨¿ à¨œà¨²à¨¿ à¨œà¨°à¨¹à©                  |
                    | **Sacrificial**     | à¨¬à¨²à¨¿à¨¹à¨¾à¨°à©‡, à¨¬à¨²à¨¿ à¨¬à¨²à¨¿, à¨µà¨¾à¨°à©€ à¨µà©°à¨žà¨¾, à¨•à¨£à©€à¨ à¨µà©°à¨žà¨¾    |
                    | **Reverence**       | à¨†à¨‰ à¨œà©€, à¨†à¨‡ à¨œà©€, à¨ªà¨¿à¨›à©‹ à¨œà©€                       |

                    <sub>*Tokens taken from textbook pp. 9.1â€“9.4; diacritics preserved.  
                    Feel free to trim or expand as corpus stats evolve.</sub>

                    **Remember** â€“ Interjections are **indeclinable** and **carry no grammatical
                    features**.  Therefore the spreadsheet needs **no ending table** beyond this
                    categorical list.
                    """).strip() + "\\n\\n"
                
            notes_block = ending_cheat_sheet + implicit_note + common_sense_note

            prompt = textwrap.dedent(f"""
                **You are a Punjabi grammar expert.**

                Below are the *allowed choices* for each feature of the highlighted word:

                {opts_block}
                {matches_block}

                {notes_block}

                **IMPORTANT:**  
                Base **all** confirmations or corrections **solely on the Darpan translation** below.  
                Do **not** consult any other translation or external context.

                **My Current Selections:**  
                - Word Under Analysis: **{ve}**  
                - Number / à¨µà¨šà¨¨: **{num}**  
                - Grammar Case / à¨µà¨¯à¨¾à¨•à¨°à¨£: **{gram}**  
                - Gender / à¨²à¨¿à©°à¨—: **{gen}**  
                - Word Root: **{root}**

                **Context (use *only* the Darpan gloss):**  
                â€¢ **Verse:** {verse}  
                â€¢ **Darpan Translation:** {trans}  
                â€¢ **Darpan-Meanings:** {dm}

                **Task:**  
                1. **Confirm or correct** each featureâ€”if blank, **choose** the best option  
                (one-sentence rationale citing the inflection or usage).
                â€¢ For finite forms, choose **1st / 2nd / 3rd Person** in Word-Root (do not use Past/Perfect there). 
                2. **Corrections**, if any:  
                - Number â†’ â€¦  
                - Grammar Case â†’ â€¦  
                - Word Root â†’ â€¦  
                3. **Example Usage:**  
                Provide **one** new GurbÄá¹‡Ä«-style sentence using **â€œ{ve}â€** with the
                confirmed ending, number, case, gender, and root.
                4. **Table citation:**  
                Quote the person Ã— number Ã— tense row header you matched in the Canonical table  
                (e.g., â€œ1 Sg | Pastâ€). **Use that rowâ€™s category name for â€œGrammar Case / à¨µà¨¯à¨¾à¨•à¨°à¨£,â€ unless a sanity rule forbids it.**
                5. **Ending â‡„ Case cross-check:**
                â€¢ If the cheat-sheet already lists a suffix for your chosen case, use it.  
                â€¢ If the case is **missing**, you may propose a likely form
                    (or say â€œuninflectedâ€) **but give one-line reasoning**.
                6. **Commentary:**  
                Please write 2â€“3 sentences as â€œChatGPT Commentary:â€ explaining how you arrived at each feature choice.
            """).strip()

            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            messagebox.showinfo(
                "Prompt Ready",
                "The detailed-grammar prompt has been copied to your clipboard.\n"
                "Paste it into ChatGPT, then paste its response back into the text box."
            )

        tk.Button(
            frm, text="ðŸ“‹ Build Detailed Grammar Prompt",
            font=("Arial", 12, "italic"),
            bg="white", fg="dark cyan",
            command=build_detailed_prompt
        ).grid(row=6, column=0, columnspan=2, pady=(10, 0))

        # 6) --------------  Bottom buttons (unchanged)  --------------
        sep = tk.Frame(win, bg="#cccccc", height=2)
        sep.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(5, 0))

        btns = tk.Frame(win, bg="light gray")
        btns.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        tk.Button(
            btns, text="â€¹ Back",
            font=("Arial", 12), bg="gray", fg="white",
            command=lambda: [win.destroy(),
                            self.show_matches_grammar(self._last_matches, word, index)]
        ).pack(side=tk.LEFT)

        tk.Button(
            btns, text="Save & Finish â†’",
            font=("Arial", 12, "bold"), bg="dark cyan", fg="white",
            command=lambda: self.on_accept_detailed_grammar(win)
        ).pack(side=tk.RIGHT)

        win.transient(self.root)
        win.grab_set()
        self.root.wait_window(win)








































    def launch_verse_analysis_dashboard(self):
        """Clears the main dashboard and launches the Verse Analysis Dashboard."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.title("Verse Analysis Dashboard")
        self.setup_verse_analysis_dashboard()

    def setup_verse_analysis_dashboard(self):
        """Builds the Verse Analysis Dashboard interface."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.main_frame = tk.Frame(self.root, bg='light gray', padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header_label = tk.Label(
            self.main_frame,
            text="Verse Analysis Dashboard",
            font=('Arial', 18, 'bold'),
            bg='dark slate gray',
            fg='white',
            pady=10
        )
        header_label.pack(fill=tk.X, pady=10)

        # Create a frame for the option buttons
        button_frame = tk.Frame(self.main_frame, bg='light gray')
        button_frame.pack(expand=True)

        # Literal Translation Button
        literal_btn = tk.Button(
            button_frame,
            text="Literal Translation",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_literal_analysis
        )
        literal_btn.pack(pady=10)

        # New button for editing saved literal translation
        edit_saved_btn = tk.Button(
            button_frame,
            text="Edit Saved Literal Translation",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_select_verse  # Updated command
        )
        edit_saved_btn.pack(pady=10)

        # Placeholder for Spiritual Translation (future implementation)
        spiritual_btn = tk.Button(
            button_frame,
            text="Spiritual Translation (Coming Soon)",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        spiritual_btn.pack(pady=10)

        # Placeholder for Translation Management (future implementation)
        management_btn = tk.Button(
            button_frame,
            text="Translation Management (Coming Soon)",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        management_btn.pack(pady=10)

        # Back button to return to the main dashboard
        back_btn = tk.Button(
            self.main_frame,
            text="Back to Main Dashboard",
            font=('Arial', 14, 'bold'),
            bg='red',
            fg='white',
            padx=20,
            pady=10,
            command=self.show_dashboard
        )
        back_btn.pack(pady=10)

    def launch_select_verse(self):
        """
        Creates a centered modal window to let the user select a verse by:
        1. Searching by verse content
        2. Filtering by metadata (Raag, Writer, Bani, Page)
        Displays only those verses that already exist in the assessment Excel.
        """

        # === Setup modal ===
        select_win = tk.Toplevel(self.root)
        select_win.title("Select Verse")
        select_win.geometry("800x600")
        select_win.state("zoomed")
        select_win.configure(bg="light gray")

        # === Load Excel data ===
        file_path = "1.2.1 assessment_data.xlsx"
        df_existing = self.load_existing_assessment_data(file_path)

        # === Center content ===
        center_frame = tk.Frame(select_win, bg="light gray")
        center_frame.pack(expand=True)

        content_frame = tk.Frame(center_frame, bg="light gray", width=960)
        content_frame.pack()

        # === Header ===
        header_label = tk.Label(
            content_frame,
            text="Select Verse",
            bg="dark slate gray",
            fg="white",
            font=("Helvetica", 18, "bold"),
            padx=20, pady=10
        )
        header_label.pack(fill=tk.X, pady=(0, 10))

        # === Mode selection (Search or Filter) ===
        mode_var = tk.StringVar(value="search")
        mode_frame = tk.Frame(content_frame, bg="light gray")
        mode_frame.pack(pady=10)

        tk.Radiobutton(mode_frame, text="Search by Verse", variable=mode_var, value="search",
                    bg="light gray", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Filter by Metadata", variable=mode_var, value="filter",
                    bg="light gray", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        # === Create container for dynamic frames ===
        main_content_area = tk.Frame(content_frame, bg="light gray")
        main_content_area.pack(fill=tk.BOTH, expand=True)

        # === Search Frame ===
        search_frame = tk.Frame(main_content_area, bg="light gray")
        tk.Label(search_frame, text="Enter or paste a verse to search:", bg="light gray",
                font=("Arial", 12, "bold")).pack(pady=5)

        search_entry = tk.Entry(search_frame, font=("Arial", 12), width=80)
        search_entry.pack(pady=5)

        search_button = tk.Button(
            search_frame, text="Search", font=("Arial", 12, "bold"),
            bg="navy", fg="white", width=12,
            command=lambda: perform_search(search_entry.get())
        )
        search_button.pack(pady=5)

        search_results_list = tk.Listbox(search_frame, font=("Arial", 12), width=80, height=10)
        search_results_list.pack(pady=10)

        # === Filter Frame ===
        filter_frame = tk.Frame(main_content_area, bg="light gray")
        tk.Label(filter_frame, text="Filter verses by metadata:", bg="light gray",
                font=("Arial", 12, "bold")).pack(pady=5)

        filter_controls = tk.Frame(filter_frame, bg="light gray")
        filter_controls.pack(pady=5)

        # === Dropdowns for filter ===
        df = df_existing.copy()
        raag_var, writer_var, bani_var, page_var = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        # Sort Raag, Writer, Bani based on first page appearance
        initial_raag = df.dropna(subset=["Raag (Fixed)"]).drop_duplicates("Raag (Fixed)", keep="first").sort_values("Page Number")["Raag (Fixed)"].tolist()
        initial_writer = df.dropna(subset=["Writer (Fixed)"]).drop_duplicates("Writer (Fixed)", keep="first").sort_values("Page Number")["Writer (Fixed)"].tolist()
        initial_bani = df.dropna(subset=["Bani Name"]).drop_duplicates("Bani Name", keep="first").sort_values("Page Number")["Bani Name"].tolist()
        # Sort Page Numbers numerically
        initial_page = sorted(df["Page Number"].dropna().unique())
        initial_page = [str(p) for p in initial_page]  # Convert back to string for dropdown


        tk.Label(filter_controls, text="Raag:", bg="light gray", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        raag_dropdown = ttk.Combobox(filter_controls, textvariable=raag_var, values=initial_raag, width=15)
        raag_dropdown.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_controls, text="Writer:", bg="light gray", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5)
        writer_dropdown = ttk.Combobox(filter_controls, textvariable=writer_var, values=initial_writer, width=15)
        writer_dropdown.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(filter_controls, text="Bani:", bg="light gray", font=("Arial", 12)).grid(row=0, column=4, padx=5, pady=5)
        bani_dropdown = ttk.Combobox(filter_controls, textvariable=bani_var, values=initial_bani, width=15)
        bani_dropdown.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(filter_controls, text="Page:", bg="light gray", font=("Arial", 12)).grid(row=0, column=6, padx=5, pady=5)
        page_dropdown = ttk.Combobox(filter_controls, textvariable=page_var, values=initial_page, width=10)
        page_dropdown.grid(row=0, column=7, padx=5, pady=5)

        # === Update filter dropdowns dynamically ===
        def update_dropdowns(*args):
            filtered_df = df.copy()
            if raag_var.get():
                filtered_df = filtered_df[filtered_df["Raag (Fixed)"] == raag_var.get()]
            if writer_var.get():
                filtered_df = filtered_df[filtered_df["Writer (Fixed)"] == writer_var.get()]
            if bani_var.get():
                filtered_df = filtered_df[filtered_df["Bani Name"] == bani_var.get()]
            if page_var.get():
                filtered_df = filtered_df[filtered_df["Page Number"].astype(str) == page_var.get()]
            raag_dropdown['values'] = (
                filtered_df.dropna(subset=["Raag (Fixed)"])
                .drop_duplicates("Raag (Fixed)", keep="first")
                .sort_values("Page Number")["Raag (Fixed)"].tolist()
            )

            writer_dropdown['values'] = (
                filtered_df.dropna(subset=["Writer (Fixed)"])
                .drop_duplicates("Writer (Fixed)", keep="first")
                .sort_values("Page Number")["Writer (Fixed)"].tolist()
            )

            bani_dropdown['values'] = (
                filtered_df.dropna(subset=["Bani Name"])
                .drop_duplicates("Bani Name", keep="first")
                .sort_values("Page Number")["Bani Name"].tolist()
            )

            sorted_pages = sorted(filtered_df["Page Number"].dropna().unique())
            page_dropdown['values'] = [str(p) for p in sorted_pages]

        for var in (raag_var, writer_var, bani_var, page_var):
            var.trace_add("write", update_dropdowns)

        # === Filter Button & Listbox ===
        filter_button = tk.Button(filter_frame, text="Apply Filter", font=("Arial", 12, "bold"),
                                bg="navy", fg="white", command=lambda: update_verse_list())
        filter_button.pack(pady=5)

        filter_results_list = tk.Listbox(filter_frame, font=("Arial", 12), width=80, height=10)
        filter_results_list.pack(pady=10)

        # === Toggle mode display ===
        def update_mode():
            filter_frame.pack_forget()
            search_frame.pack_forget()
            if mode_var.get() == "search":
                search_frame.pack(pady=10)
            else:
                filter_frame.pack(pady=10)

        mode_var.trace_add("write", lambda *args: update_mode())
        update_mode()

        # === Search Logic ===
        def perform_search(query):
            search_results_list.delete(0, tk.END)
            if not query:
                search_results_list.insert(tk.END, "No query entered.")
                return
            headers, candidate_matches = self.match_sggs_verse(query)
            candidate_verses = list(dict.fromkeys(candidate["Verse"] for candidate in candidate_matches))
            excel_verses = set(df_existing["Verse"].unique())
            unique_verses = [v for v in candidate_verses if v in excel_verses]
            if unique_verses:
                for verse in unique_verses:
                    search_results_list.insert(tk.END, verse)
            else:
                search_results_list.insert(tk.END, "No analyzed verse matches found.")

        # === Filter Logic ===
        def update_verse_list():
            filter_results_list.delete(0, tk.END)
            filtered_df = df_existing.copy()
            if raag_var.get():
                filtered_df = filtered_df[filtered_df["Raag (Fixed)"].str.contains(raag_var.get(), case=False, na=False)]
            if writer_var.get():
                filtered_df = filtered_df[filtered_df["Writer (Fixed)"].str.contains(writer_var.get(), case=False, na=False)]
            if bani_var.get():
                filtered_df = filtered_df[filtered_df["Bani Name"].str.contains(bani_var.get(), case=False, na=False)]
            if page_var.get():
                filtered_df = filtered_df[filtered_df["Page Number"].astype(str).str.contains(page_var.get(), case=False, na=False)]
            for verse in filtered_df["Verse"].unique():
                filter_results_list.insert(tk.END, verse)

        # === Finalize & Back buttons ===
        def finalize_selection():
            if mode_var.get() == "search":
                sel = search_results_list.curselection()
                final_verse = search_results_list.get(sel[0]) if sel else ""
            else:
                sel = filter_results_list.curselection()
                final_verse = filter_results_list.get(sel[0]) if sel else ""
            if final_verse:
                self.finalized_verse = final_verse
                select_win.destroy()
                self.launch_edit_saved_literal_translation()
            else:
                tk.messagebox.showerror("Error", "Please select a verse before proceeding.")

        bottom_frame = tk.Frame(main_content_area, bg="light gray")
        bottom_frame.pack(side=tk.BOTTOM, pady=10)

        tk.Button(bottom_frame, text="Finalize Selection", font=("Arial", 12, "bold"),
                bg="green", fg="white", padx=15, pady=5,
                command=finalize_selection).pack(side=tk.LEFT, padx=(10, 5))

        tk.Button(bottom_frame, text="Back to Dashboard", font=("Arial", 12, "bold"),
                bg="gray", fg="white", padx=15, pady=5,
                command=lambda: (select_win.destroy(), self.setup_verse_analysis_dashboard())).pack(side=tk.LEFT, padx=(5, 10))

        # === Modal behavior ===
        select_win.transient(self.root)
        select_win.grab_set()
        self.root.wait_window(select_win)

    def launch_edit_saved_literal_translation(self):
        """Launch a window to review and select words for re-analysis from a saved verse."""

        verse = self.finalized_verse
        df = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")

        # === Clear root ===
        for widget in self.root.winfo_children():
            widget.destroy()

        # === Setup main frame ===
        main_frame = tk.Frame(self.root, bg="light gray", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === Header ===
        header = tk.Label(
            main_frame,
            text="Edit Saved Literal Translation",
            font=("Helvetica", 18, "bold"),
            bg="dark slate gray",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X, pady=(0, 20))

        # === Display Verse ===
        verse_label = tk.Label(
            main_frame,
            text=f"Verse:\n  {verse}",
            font=("Arial", 14),
            bg="light gray",
            anchor="w",
            justify="left"
        )
        verse_label.pack(fill=tk.X, padx=10)

        # === Display Translation ===
        row_data = df[df['Verse'] == verse].iloc[0]
        translation = row_data.get('Translation', '')
        translation_label = tk.Label(
            main_frame,
            text=f"Translation:\n  {translation}",
            font=("Arial", 13, "italic"),
            bg="light gray",
            anchor="w",
            justify="left"
        )
        translation_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Returns the real value if it isnâ€™t NaN; otherwise it returns a â€œâ€”â€ placeholder
        def safe(val):
            return val if pd.notna(val) else "â€”"

        # === Metadata (Raag, Writer, Bani, Page) ===
        metadata_frame = tk.Frame(main_frame, bg="light gray")
        metadata_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        for label, col in [
            ("Raag:", "Raag (Fixed)"),
            ("Writer:", "Writer (Fixed)"),
            ("Bani:", "Bani Name"),
            ("Page:", "Page Number"),
        ]:
            val = row_data.get(col)
            # only show non-missing values
            if val is None or pd.isna(val):
                continue

            meta = tk.Label(
                metadata_frame,
                text=f"{label} {val}",
                font=("Arial", 11, "bold"),
                bg="light gray",
                anchor="w",
                justify="left"
            )
            meta.pack(anchor="w")

        # === Editable Metadata for Entire Verse ===
        # Create a frame for editing verse-wide settings like "Framework?" and "Explicit?"
        edit_metadata_frame = tk.Frame(main_frame, bg="light gray")
        edit_metadata_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        # Helper: safely extract a boolean value (assuming Excel stores these as numbers 0/1 or booleans)
        def safe_bool(val):
            try:
                # If the value is a numpy integer, convert it to a normal int first
                if isinstance(val, np.integer):
                    val = int(val)
                # Now, if it's numeric, nonzero means True; otherwise, use its boolean conversion
                return bool(val) if isinstance(val, (int, float)) else val
            except Exception:
                return False

        # Get initial values from the Excel row data
        initial_framework = safe_bool(row_data.get("Framework?"))
        initial_explicit = safe_bool(row_data.get("Explicit?"))

        # Create checkboxes for Framework and Explicit metadata
        framework_var_edit = tk.BooleanVar(value=initial_framework)
        explicit_var_edit = tk.BooleanVar(value=initial_explicit)

        framework_cb_edit = tk.Checkbutton(
            edit_metadata_frame,
            text="Framework?",
            variable=framework_var_edit,
            font=("Arial", 11, "bold"),
            bg="light gray"
        )
        framework_cb_edit.pack(side=tk.LEFT, padx=10)

        explicit_cb_edit = tk.Checkbutton(
            edit_metadata_frame,
            text="Explicit?",
            variable=explicit_var_edit,
            font=("Arial", 11, "bold"),
            bg="light gray"
        )
        explicit_cb_edit.pack(side=tk.LEFT, padx=10)

        def update_verse_metadata(new_framework, new_explicit):
            file_path = "1.2.1 assessment_data.xlsx"
            try:
                # Load existing data
                df_existing = self.load_existing_assessment_data(file_path)
                # Create a mask for rows corresponding to the current verse
                verse_mask = df_existing["Verse"] == verse
                # Update the columns for the entire verse with the new values
                df_existing.loc[verse_mask, "Framework?"] = int(new_framework)
                df_existing.loc[verse_mask, "Explicit?"] = int(new_explicit)
                df_existing.to_excel(file_path, index=False)
                messagebox.showinfo("Updated", "Verse metadata updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update verse metadata: {e}")

        update_btn = tk.Button(
            edit_metadata_frame,
            text="Update Verse Metadata",
            font=("Arial", 11, "bold"),
            bg="dark cyan", fg="white",
            padx=10, pady=5,
            command=lambda: update_verse_metadata(framework_var_edit.get(), explicit_var_edit.get())
        )
        update_btn.pack(side=tk.LEFT, padx=10)

        # === Word Table Frame ===
        word_frame = tk.LabelFrame(
            main_frame,
            text="Select words to re-analyze:",
            bg="light gray",
            font=("Arial", 12, "bold")
        )
        word_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === Checkbox Simulation ===
        selected_items = set()

        columns = [
            'Select', 'Word', 'Vowel Ending', 'Number / à¨µà¨šà¨¨',
            'Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'Gender / à¨²à¨¿à©°à¨—', 'Word Type',
            'Word Root', 'Word Index'
        ]

        tree = ttk.Treeview(word_frame, columns=columns, show='headings', selectmode='none')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=110 if col != 'Select' else 60)

        # Add scrollbar
        vsb = ttk.Scrollbar(word_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Insert rows
        # 1) Configure tag styles for odd/even rows
        tree.tag_configure('oddrow', background='white')
        tree.tag_configure('evenrow', background='#E8E8E8')  # light gray

        # 2) Insert rows with alternating row tags
        rows = df[df['Verse'] == verse]
        for i, (_, row) in enumerate(rows.iterrows()):
            row_id = f"row{i}"
            # Your existing 'values' building
            values = [
                "",  # checkbox
                safe(self._norm_get(row, "Word")),
                safe(self._norm_get(row, "\ufeffVowel Ending")),
                safe(self._norm_get(row, "Number / à¨µà¨šà¨¨")),
                safe(self._norm_get(row, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£")),
                safe(self._norm_get(row, "Gender / à¨²à¨¿à©°à¨—")),
                safe(self._norm_get(row, "Word Root")),
                safe(self._norm_get(row, "Type")),
                int(self._norm_get(row, "Word Index") or -1)
            ]

            # Determine odd/even row coloring
            if i % 2 == 0:
                tree.insert('', tk.END, iid=row_id, values=values, tags=('evenrow',))
            else:
                tree.insert('', tk.END, iid=row_id, values=values, tags=('oddrow',))

        # === Toggle âœ“ in first column ===
        def on_tree_click(event):
            region = tree.identify_region(event.x, event.y)
            if region == 'cell':
                row_id = tree.identify_row(event.y)
                col = tree.identify_column(event.x)
                if row_id and col == '#1':
                    if row_id in selected_items:
                        selected_items.remove(row_id)
                        tree.set(row_id, 'Select', "")
                    else:
                        selected_items.add(row_id)
                        tree.set(row_id, 'Select', "âœ“")

        tree.bind('<Button-1>', on_tree_click)

        # === Action Buttons ===
        btn_frame = tk.Frame(main_frame, bg="light gray")
        btn_frame.pack(pady=20)

        def analyze_selected_words():
            if not hasattr(self, "results_text"):
                self.results_text = scrolledtext.ScrolledText(
                    self.root,
                    width=90,
                    height=20,
                    font=("Consolas", 11),
                    bd=3,
                    relief=tk.SUNKEN,
                    wrap=tk.WORD
                )
                self.results_text.pack_forget()  # Donâ€™t show it to the user during re-analysis

            # Get column names to dynamically determine index of "Word" and "Word Index"
            column_names = tree["columns"]
            word_col_index = column_names.index("Word")
            index_col_index = column_names.index("Word Index")

            # Build the list of selected words with indices
            selected_words_with_indices = [
                (
                    tree.item(rid)['values'][word_col_index],
                    int(tree.item(rid)['values'][index_col_index])
                )
                for rid in selected_items
            ]

            all_words_in_verse = [tree.item(rid)['values'][1] for rid in tree.get_children()]

            if not selected_words_with_indices:
                messagebox.showwarning(
                    "No Words Selected",
                    "You havenâ€™t selected any words for re-analysis.\n\n"
                    "Click the âœ“ box beside the word(s) you wish to re-analyze, then press the button again."
                )
                return

            # Step 1: Set context before any processing
            self.current_pankti = verse
            self.accumulated_pankti = verse
            self.pankti_words = all_words_in_verse  # Keep 'à¥¥' if part of original flow
            self.selected_verses = [verse]
            self.accumulated_meanings = [{} for _ in self.pankti_words]
            self.accumulated_finalized_matches = [[] for _ in self.pankti_words]
            self.all_new_entries = []
            self.current_reanalysis_index = []

            # Step 2: Load Excel and pre-fill all words from verse
            df = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")
            verse_rows = df[df["Verse"] == verse]

            for i, word in enumerate(self.pankti_words):
                word_rows = verse_rows[
                    (verse_rows["Word"] == word) &
                    (verse_rows["Verse"] == verse) &
                    (verse_rows["Word Index"] == i)
                ]
                if not word_rows.empty:
                    # Meanings
                    meanings = [
                        row.get("Selected Darpan Meaning", "")
                        for _, row in word_rows.iterrows()
                        if pd.notna(row.get("Selected Darpan Meaning"))
                    ]
                    self.accumulated_meanings[i] = {"word": word, "meanings": meanings}

                    # Grammar matches
                    finalized = word_rows.to_dict("records")
                    self.accumulated_finalized_matches[i] = finalized
                    self.all_new_entries.extend(finalized)

            # Step 3: Determine which indices to re-analyze
            selected_words_with_indices.sort(key=lambda x: x[1])  # Sort by Word Index (ascending)
            word_indices = [idx for (_, idx) in selected_words_with_indices]
            if not word_indices:
                messagebox.showinfo("Not Found", "Selected words not found in verse structure.")
                return

            # Populate past details (grammar and selected meanings) for each word in the verse.
            self.past_word_details = {}

            # Iterate over each tuple (word, idx) in selected_words_with_indices.
            for word, idx in selected_words_with_indices:
                # Filter the DataFrame for rows matching the word, verse, and unique word index.
                word_rows = verse_rows[
                    (verse_rows["Word"] == word) &
                    (verse_rows["Verse"] == verse) &
                    (verse_rows["Word Index"] == idx)
                ]
                
                if not word_rows.empty:
                    # Choose the representative row that has the highest Grammar Revision.
                    latest_idx = word_rows["Grammar Revision"].idxmax()
                    latest_row = word_rows.loc[latest_idx]
                    
                    # Gather all available past Darpan meanings from the filtered rows.
                    darpan_meanings = []
                    for _, row in word_rows.iterrows():
                        val = row.get("Selected Darpan Meaning")
                        if pd.notna(val):
                            # Split on comma and strip whitespace
                            split_meanings = [m.strip() for m in val.split("| ")]
                            darpan_meanings.extend(split_meanings)

                    # Store the past details in the dictionary using the word index as the key.
                    self.past_word_details[idx] = {
                        "Word": word,
                        "\ufeffVowel Ending": self._norm_get(latest_row, "\ufeffVowel Ending") or "",
                        "Number / à¨µà¨šà¨¨": self._norm_get(latest_row, "Number / à¨µà¨šà¨¨") or "",
                        "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£": self._norm_get(latest_row, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£") or "",
                        "Gender / à¨²à¨¿à©°à¨—": self._norm_get(latest_row, "Gender / à¨²à¨¿à©°à¨—") or "",
                        "Type": self._norm_get(latest_row, "Type") or "",
                        "Word Root": self._norm_get(latest_row, "Word Root") or "",
                        "Word Index": idx,
                        "darpan_meanings": darpan_meanings
                    }

            # Step 4: Store queue and start
            self.reanalysis_queue = word_indices
            self.process_next_selected_word()

        def back_to_search():
            self.launch_select_verse()

        def back_to_dashboard():
            self.setup_verse_analysis_dashboard()

        tk.Button(
            btn_frame,
            text="Analyze Selected Words",
            bg="navy", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=analyze_selected_words
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Search",
            bg="gray", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=back_to_search
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Dashboard",
            bg="red", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=back_to_dashboard
        ).pack(side=tk.LEFT, padx=10)

        # === Optional: Customize style ===
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 11, 'bold'))
        style.configure("Treeview", rowheight=28, font=('Arial', 11))

    def process_next_selected_word(self):
        """Process the next word from re-analysis queue, or prompt to save if finished."""
        if not hasattr(self, 'reanalysis_queue') or not self.reanalysis_queue:
            messagebox.showinfo("Done", "Re-analysis completed for all selected words.")
            
            # Proceed to save reanalyzed results
            if hasattr(self, 'save_results_btn') and self.save_results_btn.winfo_exists():
                self.save_results_btn.config(state=tk.NORMAL)
            
            self.prompt_save_results_reanalysis(self.all_new_entries, skip_copy=False)  # Skip clipboard step for reanalysis
            return

        # Process the next word from queue
        idx = self.reanalysis_queue.pop(0)
        self.current_word_index = idx
        word = self.pankti_words[idx]
        self.ensure_meanings_slot_initialized(idx, word)

        self.fetch_data_for_reanalysis(word, self.accumulated_pankti, idx)

    def fetch_data_for_reanalysis(self, word, pankti, index):
        self.reset_input_variables()
        self.current_word_index = index
        self.user_input_reanalysis(word, pankti, index)

        if hasattr(self, 'input_window') and self.input_window.winfo_exists():
            self.root.wait_window(self.input_window)
        else:
            return

        if self.input_submitted:
            self.handle_submitted_input(word)
        else:
            print(f"Skipped: {word}")

        # Now move to next in reanalysis queue
        self.process_next_selected_word()

    def user_input_reanalysis(self, word, pankti, index):
        print(f"[Reanalysis] Opening input window for {word} (index {index})")
        self.input_submitted = False
        self.current_word_index = index  # Ensure correct word gets highlighted

        self.input_window = tk.Toplevel(self.root)
        self.input_window.title(f"[Edit Mode] Input for {word}")
        self.input_window.configure(bg='light gray')
        self.input_window.state('zoomed')
        self.input_window.resizable(True, True)

        # Display the Pankti with word highlight
        pankti_frame = tk.Frame(self.input_window, bg='light gray')
        pankti_frame.pack(fill=tk.X, padx=20, pady=10)

        pankti_display = tk.Text(
            pankti_frame, wrap=tk.WORD, bg='light gray', font=('Arial', 32),
            height=2, padx=5, pady=5
        )
        pankti_display.pack(fill=tk.X, expand=False)
        pankti_display.insert(tk.END, pankti)
        pankti_display.tag_add("center", "1.0", "end")
        pankti_display.tag_configure("center", justify='center')

        # Highlight the word at the re-analysis index
        words = pankti.split()
        start_idx = 0
        for i, w in enumerate(words):
            if i == index:
                end_idx = start_idx + len(w)
                pankti_display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
                pankti_display.tag_config("highlight", foreground="blue", font=('Arial', 32, 'bold'))
                break
            start_idx += len(w) + 1
        pankti_display.config(state=tk.DISABLED)

        # Create layout pane
        split_pane = tk.PanedWindow(self.input_window, orient=tk.HORIZONTAL, bg='light gray')
        split_pane.pack(fill=tk.BOTH, expand=True)

        # Left: Meanings
        self.left_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(self.left_pane, stretch="always")
        tk.Label(self.left_pane, text=f"Re-analyze Meanings for {word}:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(anchor='center', pady=(0, 10))
        self.meanings_scrollbar = tk.Scrollbar(self.left_pane, orient=tk.VERTICAL)
        self.meanings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.meanings_canvas = tk.Canvas(self.left_pane, bg='light gray', borderwidth=0,
                                        yscrollcommand=self.meanings_scrollbar.set)
        self.meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.meanings_scrollbar.config(command=self.meanings_canvas.yview)
        self.meanings_inner_frame = tk.Frame(self.meanings_canvas, bg='light gray')
        self.meanings_canvas.create_window((0, 0), window=self.meanings_inner_frame, anchor='nw')

        # Right: Grammar Options
        right_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(right_pane, stretch="always")
        tk.Label(right_pane, text="Adjust Grammar Options:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(pady=10)
        self.setup_options(
            right_pane,
            "Do you know the Number of the word?",
            [("Singular", "Singular / à¨‡à¨•"), ("Plural", "Plural / à¨¬à¨¹à©"), ("Not Applicable", "NA")],
            self.number_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Gender of the word?",
            [("Masculine", "Masculine / à¨ªà©à¨²à¨¿à©°à¨—"), ("Feminine", "Feminine / à¨‡à¨¸à¨¤à¨°à©€"), ("Neutral", "Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•")],
            self.gender_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Part of Speech for the word?",
            [("Noun", "Noun / à¨¨à¨¾à¨‚à¨µ"), ("Adjective", "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£"),
            ("Adverb", "Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£"), ("Verb", "Verb / à¨•à¨¿à¨°à¨¿à¨†"),
            ("Pronoun", "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ"), ("Postposition", "Postposition / à¨¸à©°à¨¬à©°à¨§à¨•"),
            ("Conjunction", "Conjunction / à¨¯à©‹à¨œà¨•"), ("Interjection", "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•")],
            self.pos_var
        )

        # Submit / Skip
        button_frame = tk.Frame(self.input_window, bg='light gray')
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Submit", command=self.submit_input_reanalysis,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)
        tk.Button(button_frame, text="Skip", command=self.skip_input,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)

        # Progress + Dictionary Lookup
        self.start_progress()
        threading.Thread(target=self.lookup_meanings_thread, args=(word,), daemon=True).start()

        self.input_window.transient(self.root)
        self.input_window.grab_set()
        self.root.wait_window(self.input_window)
        print(f"[Reanalysis] Closed input window for {word}")

    def submit_input_reanalysis(self):
        self.input_submitted = True
        if hasattr(self, 'input_window') and self.input_window.winfo_exists():
            self.input_window.destroy()

        # Start the progress bar
        self.start_progress()

        # Run the reanalysis search in a separate thread
        search_thread = threading.Thread(target=self.perform_search_and_finish_reanalysis)
        search_thread.start()

    def perform_search_and_finish_reanalysis(self):
        current_word = self.pankti_words[self.current_word_index]
        number = self.number_var.get()
        gender = self.gender_var.get()
        pos = self.pos_var.get()

        print(f"[Reanalysis] Processing word: {current_word}, Number: {number}, Gender: {gender}, POS: {pos}")
        
        if number == "NA" and gender == "NA" and pos == "NA":
            matches = self.search_by_inflections(current_word)
        else:
            matches = self.search_by_criteria(current_word, number, gender, pos)
            if not matches:
                messagebox.showinfo(
                    "No Matches Found",
                    "No matches were found as per the criteria. Now conducting a general search."
                )
                matches = self.search_by_inflections(current_word)

        # Meanings are guaranteed to be preloaded from the Excel into self.accumulated_meanings
        entry = self.accumulated_meanings[self.current_word_index]
        meanings = entry.get("meanings", []) if isinstance(entry, dict) else entry

        # Stop progress bar first
        self.root.after(0, self.stop_progress)

        if matches:
            print(f"[Reanalysis] Found matches for {current_word}: {matches}")
            self.root.after(0, lambda: self.show_matches_reanalysis(matches, self.current_pankti, meanings, self.current_word_index))
        else:
            self.root.after(0, lambda: messagebox.showinfo("No Matches", f"No matches found for the word: {current_word}"))
            self.current_word_index += 1
            self.root.after(0, self.process_next_selected_word)

    def show_matches_reanalysis(self, matches, pankti, meanings, index, max_display=30):
        # Destroy any existing match window
        if hasattr(self, 'match_window') and self.match_window.winfo_exists():
            self.match_window.destroy()

        self.match_window = tk.Toplevel(self.root)
        self.match_window.title("Re-analysis: Select Matches and Meanings")
        self.match_window.configure(bg='light gray')
        self.match_window.state('zoomed')

        self.match_vars = []
        self.meaning_vars = []
        unique_matches = self.filter_unique_matches(matches)
        self.all_matches.append(unique_matches)

        self.current_reanalysis_index.append(index)
        
        # Display Pankti
        self.display_pankti_with_highlight(self.match_window, pankti, index)

        # --- Explanation Section ---
        explanation_frame = tk.Frame(self.match_window, bg='AntiqueWhite', 
                                    relief='groove', bd=2)  # A tinted frame with a grooved border
        explanation_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        heading_label = tk.Label(
            explanation_frame, 
            text="Important Note", 
            font=("Arial", 14, 'bold'),
            bg='AntiqueWhite'
        )
        heading_label.pack(pady=(5, 0))

        explanation_text = (
            "â€¢ Highlighted selections (displayed in MistyRose) indicate the meanings or grammar rules that "
            "were previously confirmed in your assessment.\n"
            "â€¢ This helps you quickly recognize which items reflect your earlier choices."
        )

        body_label = tk.Label(
            explanation_frame, 
            text=explanation_text,
            bg='AntiqueWhite', 
            fg='black', 
            font=('Arial', 12),
            wraplength=900,    # Adjust wrap length to your windowâ€™s width
            justify=tk.LEFT
        )
        body_label.pack(pady=(0, 10), padx=10)

        # Main layout
        main_frame = tk.Frame(self.match_window, bg='light gray')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # --- Left Pane: Meanings ---
        word = self.pankti_words[index]
        self.display_meanings_section_reanalysis(main_frame, word, index, meanings)

        # --- Right Pane: Matches ---
        self.display_matches_section_reanalysis(main_frame, unique_matches, index, max_display)

        # --- Bottom Buttons ---
        button_frame = tk.Frame(self.match_window, bg='light gray')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Submit",
            command=self.submit_matches_reanalysis,
            font=('Arial', 12, 'bold'), bg='navy', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Back",
            command=lambda: self.back_to_user_input_reanalysis(pankti, index),
            font=('Arial', 12, 'bold'), bg='navy', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=5)

    def display_pankti_with_highlight(self, parent, pankti, index):
        """
        Displays the full pankti and highlights the word at the given index in a Text widget.
        """
        pankti_frame = tk.Frame(parent, bg='light gray')
        pankti_frame.pack(fill=tk.BOTH, padx=30, pady=20)

        display = tk.Text(
            pankti_frame,
            wrap=tk.WORD,
            bg='light gray',
            font=('Arial', 32),
            height=1,
            padx=5,
            pady=5
        )
        display.pack(fill=tk.BOTH, expand=False)
        display.insert(tk.END, pankti)
        display.tag_add("center", "1.0", "end")
        display.tag_configure("center", justify='center')

        words = pankti.split()
        start_idx = 0
        for i, w in enumerate(words):
            if i == index:
                break
            start_idx += len(w) + 1
        end_idx = start_idx + len(words[index])

        display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
        display.tag_config("highlight", foreground="blue", font=('Arial', 32, 'bold'))
        display.config(state=tk.DISABLED)

    def display_meanings_section_reanalysis(self, parent_frame, word, index, meanings):
        """Display meanings as checkboxes for reanalysis with prior selection support."""
        meanings_frame = tk.Frame(parent_frame, bg='light gray')
        meanings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(meanings_frame, text=f"Select Meanings for {word}:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(pady=10)

        self.select_all_meanings_var = tk.BooleanVar(value=True)
        tk.Checkbutton(meanings_frame, text="Select/Deselect All Meanings",
                    variable=self.select_all_meanings_var, bg='light gray',
                    font=('Arial', 12), command=self.toggle_all_meanings).pack(pady=5)

        meanings_canvas = tk.Canvas(meanings_frame, bg='light gray', borderwidth=0)
        meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(meanings_frame, orient=tk.VERTICAL, command=meanings_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        meanings_canvas.config(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(meanings_canvas, bg='light gray')
        meanings_canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        # Merge past meanings
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == word), index)
        merged_meanings = []
        for idx in range(first_index, index):
            if idx < len(self.accumulated_meanings):
                entry = self.accumulated_meanings[idx]
                if isinstance(entry, dict):
                    merged_meanings.extend(entry.get("meanings", []))
        prior_meanings = list(dict.fromkeys(merged_meanings))

        # Extract assessment-specific selected meanings from past_word_details.
        # These are the meanings the user had previously selected (from assessment).
        assessment_meanings = self.past_word_details.get(index, {}).get("darpan_meanings", [])

        # Reorder current meanings
        if isinstance(meanings, dict):
            current_meanings = meanings.get("meanings", [])
        else:
            current_meanings = meanings
            
        # Tier 1: assessment_meanings at very top
        reordered_assessment = [m for m in current_meanings if m in assessment_meanings]

        # Tier 2: prior_meanings next
        reordered_prior = [m for m in current_meanings 
                        if (m in prior_meanings and m not in assessment_meanings)]

        # Tier 3: everything else
        reordered_others = [m for m in current_meanings
                            if m not in prior_meanings and m not in assessment_meanings]

        reordered = reordered_assessment + reordered_prior + reordered_others

        split = self.split_meanings_for_display(reordered)
        self.meaning_vars = []

        for i, column in enumerate(split.values()):
            col_frame = tk.Frame(inner_frame, bg='light gray')
            col_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nw')
            for meaning in column:
                # Determine whether this meaning was previously chosen during
                # the earlier assessment.  Those meanings should stand out in
                # MistyRose so that the user can easily recognise them when
                # reâ€‘analysing a word (mirroring the behaviour of grammar
                # rule highlighting).
                highlight = (meaning in assessment_meanings)

                # Default selection â€“ for reâ€‘analysis we only preâ€‘select a
                # meaning if it was explicitly chosen earlier.  Previously the
                # first occurrence of a word had every meaning preâ€‘selected
                # which made it difficult to spot the assessed choice.  By
                # limiting the preâ€‘selection to the highlighted meanings we
                # keep the focus on what was actually picked before.
                if index != first_index:
                    preselect = (meaning in prior_meanings) or highlight
                else:
                    preselect = highlight

                # Apply the MistyRose background when the meaning was part of
                # the previous assessment; otherwise fall back to light gray.
                bg_color = "MistyRose" if highlight else "light gray"

                var = tk.BooleanVar(value=preselect)
                chk = tk.Checkbutton(
                    col_frame,
                    text=f"- {meaning}",
                    variable=var,
                    bg=bg_color,
                    font=('Arial', 12),
                    wraplength=325,
                    anchor='w',
                    justify=tk.LEFT,
                    selectcolor='light blue',
                )
                chk.pack(anchor='w', padx=15, pady=5)
                self.meaning_vars.append((var, meaning))

        inner_frame.update_idletasks()
        meanings_canvas.config(scrollregion=meanings_canvas.bbox("all"))

    def display_matches_section_reanalysis(self, parent_frame, unique_matches, index, max_display=30):
        """Display matching rule checkboxes in the reanalysis pane."""
        matches_frame = tk.Frame(parent_frame, bg='light gray')
        matches_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(matches_frame, text="Select the matching rules:",
                bg='light gray', font=('Arial', 14, 'bold')).pack(pady=10)

        canvas = tk.Canvas(matches_frame, bg='light gray', borderwidth=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas, bg='light gray')
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        self.match_vars = []  # Reset match_vars in reanalysis flow

        # Retrieve the prior assessment grammar details for this word occurrence.
        grammar_assessment = self.past_word_details.get(index, {})
        assessment_fields = self.extract_grammar_fields(grammar_assessment)
        
        # For each match, we assume a tuple (label, value). In some cases,
        # label might be a composite string (e.g. with fields joined by " | ").
        # We reorder or highlight based on whether the extracted values match.
        reordered_matches = unique_matches[:max_display]  # (Assume prior reordering if needed)

        for match in reordered_matches:
            field_label, match_value = match[0], match[1]

            # If the field label is composite, parse it.
            if " | " in field_label:
                parsed = self.parse_composite(field_label)
                # Check for each target field whether the parsed value matches the assessment.
                highlight = True
                for key, expected in assessment_fields.items():
                    if key in parsed:
                        if not self.safe_equal_matches_reanalysis(parsed[key], expected):
                            highlight = False
                            break
                bg_color = "MistyRose" if highlight else "light gray"
            else:
                # Otherwise, if the label is a single field name, use a simple check.
                if field_label in assessment_fields and assessment_fields[field_label] == match_value:
                    bg_color = "MistyRose"
                else:
                    bg_color = "light gray"

            var = tk.BooleanVar()
            chk = tk.Checkbutton(inner_frame,
                                text=f"{field_label}: {match_value}",
                                variable=var,
                                bg=bg_color,
                                font=('Arial', 12),
                                selectcolor='light blue',
                                anchor='w')
            chk.pack(fill=tk.X, padx=10, pady=5)
            self.match_vars.append((var, match))

        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def safe_equal_matches_reanalysis(self, val1, val2):
        def normalize(v):
            # Convert real NaN to empty
            if pd.isna(v):
                return ""
            # Turn into string, strip whitespace, and treat "NA" (any case) as empty
            s = str(v).strip()
            return "" if s.upper() == "NA" else s
        return normalize(val1) == normalize(val2)

    def extract_grammar_fields(self, grammar_assessment):
        """
        Extract only the fields we wish to highlight from grammar_assessment.
        Returns a dict with keys:
        - "Vowel Ending"
        - "Number / à¨µà¨šà¨¨"
        - "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£"
        - "Gender / à¨²à¨¿à©°à¨—"
        - "Word Root"
        - "Word Type"
        """
        target_keys = ["\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
                    "Gender / à¨²à¨¿à©°à¨—", "Word Root", "Type"]
        return {key: grammar_assessment.get(key) for key in target_keys}

    def parse_composite(self, label):
        """
        Assume a composite label is built by joining fields with " | ".
        This function splits the composite string into its individual parts
        and returns a dictionary mapping (in order) the following keys:
        "Word", "Vowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
        "Gender / à¨²à¨¿à©°à¨—", "Word Root", "Type"
        """
        parts = label.split(" | ")
        keys = ["Word", "\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
                "Gender / à¨²à¨¿à©°à¨—", "Word Root", "Type"]
        return dict(zip(keys, parts))

    def back_to_user_input_reanalysis(self, pankti, index):
        """
        Returns to the grammar input screen for the current word during re-analysis.
        """
        try:
            if hasattr(self, 'match_window') and self.match_window:
                self.match_window.destroy()

            if 0 <= index < len(self.pankti_words):
                word = self.pankti_words[index]
                self.current_word_index = index
                self.reset_input_variables()
                self.user_input_reanalysis(word, pankti, index)
            else:
                messagebox.showerror("Invalid Index", "Cannot return to word â€” index out of range.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while going back: {e}")

    def submit_matches_reanalysis(self):
        any_selection = False
        current_entries = []

        for var, match in self.match_vars:
            if var.get():
                match_string = match[0]
                data = match_string.split(" | ")
                new_entry = {
                    "Word": data[0],
                    "\ufeffVowel Ending": data[1],
                    "Number / à¨µà¨šà¨¨": data[2],
                    "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£": data[3],
                    "Gender / à¨²à¨¿à©°à¨—": data[4],
                    "Word Root": data[5],
                    "Type": data[6]
                }
                current_entries.append(new_entry)
                any_selection = True

        selected_meanings = [meaning for var, meaning in self.meaning_vars if var.get()]
        self.accumulate_meanings_data(selected_meanings)

        current_word = self.pankti_words[self.current_word_index]
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == current_word), self.current_word_index)

        current_selected = selected_meanings
        if self.current_word_index != first_index:
            merged_meanings = []
            for idx in range(first_index, self.current_word_index):
                if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                    entry = self.accumulated_meanings[idx]
                    if isinstance(entry, dict):
                        merged_meanings.extend(entry.get("meanings", []))
                    else:
                        merged_meanings.extend(entry)
            prior_meanings = list(dict.fromkeys(merged_meanings))

            if set(current_selected) != set(prior_meanings):
                update_prev = messagebox.askyesno(
                    "Update Previous Meanings",
                    f"You have selected different meanings for the word '{current_word}'.\n"
                    "Do you want to update the meanings for all previous occurrences of this word?"
                )
                if update_prev:
                    for idx in range(first_index, self.current_word_index):
                        if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                            self.accumulated_meanings[idx] = {"word": current_word, "meanings": current_selected}

        if self.current_word_index < len(self.accumulated_meanings):
            self.accumulated_meanings[self.current_word_index] = {"word": current_word, "meanings": current_selected}
        else:
            self.accumulated_meanings.append({"word": current_word, "meanings": current_selected})

        # Assign the current verse using index-to-verse mapping
        verse_boundaries = []
        pointer = 0
        for verse in self.selected_verses:
            verse_words = verse.split()
            start = pointer
            end = pointer + len(verse_words)
            verse_boundaries.append((start, end))
            pointer = end

        current_verse = None
        for i, (start, end) in enumerate(verse_boundaries):
            if start <= self.current_word_index < end:
                current_verse = self.selected_verses[i]
                break

        for entry in current_entries:
            entry["Verse"] = current_verse
            entry["Word Index"] = self.current_word_index

        finalized_matches = []
        for var, match in self.match_vars:
            if var.get():
                match_word = match[0].split(" | ")[0]
                for entry in current_entries:
                    if entry["Word"] == match_word and entry not in finalized_matches:
                        finalized_matches.append(entry)
        self.accumulate_finalized_matches(finalized_matches)

        if not any_selection:
            messagebox.showwarning("No Selection", "No matches were selected. Please select at least one match.")
        else:
            self.match_window.destroy()
            self.all_new_entries.extend(current_entries)
            self.process_next_selected_word()

    def prompt_save_results_reanalysis(self, new_entries, skip_copy=False):
        file_path = "1.2.1 assessment_data.xlsx"
        existing_data = self.load_existing_assessment_data(file_path)
        original_accumulated_pankti = self.accumulated_pankti

        for verse in self.selected_verses:
            self.accumulated_pankti = verse
            current_verse_words = verse.replace('à¥¥', '').split()
            selected_words = set(current_verse_words)

            # Filter grammar entries specific to this verse
            # now you can pick only the entries for that exact wordâ€index
            filtered_new_entries = [
                entry for entry in new_entries
                if entry.get("Verse", "").strip() == verse.strip()
                and entry.get("Word Index") in self.current_reanalysis_index
            ]

            # Silently remove exact duplicates based on your key fields
            seen = set()
            unique_entries = []

            keys = [
                "Word", "\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
                "Gender / à¨²à¨¿à©°à¨—", "Word Root", "Type", "Verse", 'Word Index'
            ]

            for entry in filtered_new_entries:
                # build a normalized tuple of comparison values
                key = tuple(self.normalize_save_results_reanalysis(entry.get(k)) for k in keys)
                if key not in seen:
                    seen.add(key)
                    unique_entries.append(entry)

            if not skip_copy:
                self.prompt_copy_to_clipboard_reanalysis()

            if unique_entries:
                save = messagebox.askyesno("Save Results", f"Would you like to save the new entries for the following verse?\n\n{verse}")
                if save:
                    assessment_data = self.prompt_for_assessment_once_reanalysis()

                    # Extract verse metadata from chosen_match if available
                    verse_to_match = self.accumulated_pankti.strip()
                    candidate = None
                    if hasattr(self, 'candidate_matches') and self.chosen_match:
                        for cand in self.chosen_match:
                            if cand.get("Verse", "").strip() == verse_to_match:
                                candidate = cand
                                break
                        if candidate is None:
                            candidate = self.chosen_match[0]

                        verse_metadata = {
                            "Verse": verse_to_match,
                            "S. No.": candidate.get("S. No.", ""),
                            "Verse No.": candidate.get("Verse No.", ""),
                            "Stanza No.": candidate.get("Stanza No.", ""),
                            "Text Set No.": candidate.get("Text Set No.", ""),
                            "Raag (Fixed)": candidate.get("Raag (Fixed)", ""),
                            "Sub-Raag": candidate.get("Sub-Raag", ""),
                            "Writer (Fixed)": candidate.get("Writer (Fixed)", ""),
                            "Verse Configuration (Optional)": candidate.get("Verse Configuration (Optional)", ""),
                            "Stanza Configuration (Optional)": candidate.get("Stanza Configuration (Optional)", ""),
                            "Bani Name": candidate.get("Bani Name", ""),
                            "Musical Note Configuration": candidate.get("Musical Note Configuration", ""),
                            "Special Type Demonstrator": candidate.get("Special Type Demonstrator", ""),
                            "Verse Type": candidate.get("Verse Type", ""),
                            "Page Number": candidate.get("Page Number", "")
                        }
                    else:
                        verse_metadata = {}

                    # Group grammar entries by word and partition by occurrence index
                    word_groups = {}
                    for entry in unique_entries:
                        word = entry["Word"]
                        word_groups.setdefault(word, []).append(entry)

                    final_entries = []
                    occurrence_mapping = {}
                    for word in set(current_verse_words):
                        count = current_verse_words.count(word)
                        if word not in word_groups:
                            continue
                        entries_list = word_groups[word]
                        n = len(entries_list)
                        k = count
                        group_size = n // k
                        remainder = n % k
                        start = 0
                        groups = []
                        for i in range(k):
                            size = group_size + (1 if i < remainder else 0)
                            group = entries_list[start:start+size]
                            groups.append(group)
                            start += size

                        occurrence_positions = [i for i, w in enumerate(current_verse_words) if w == word]
                        for occ, pos in zip(range(k), occurrence_positions):
                            occurrence_mapping[(word, pos)] = groups[occ]

                    for idx, word in enumerate(current_verse_words):
                        key = (word, idx)
                        entries = occurrence_mapping.get(key, [])
                        if not entries:
                            continue

                        seen = set()
                        dedup_entries = []
                        for entry in entries:
                            entry_tuple = tuple(sorted(entry.items()))
                            if entry_tuple not in seen:
                                seen.add(entry_tuple)
                                dedup_entries.append(entry)
                        entries = dedup_entries

                        if len(entries) > 1:
                            chosen_entry = self.prompt_for_final_grammar_reanalysis(entries)
                        else:
                            chosen_entry = entries[0]

                        chosen_entry['Word Index'] = idx

                        if len(self.accumulated_finalized_matches) <= idx:
                            self.accumulated_finalized_matches.extend([[]] * (idx - len(self.accumulated_finalized_matches) + 1))
                        self.accumulated_finalized_matches[idx] = [chosen_entry]
                        final_entries.append(chosen_entry)

                    for entry in final_entries:
                        entry.update(assessment_data)
                        entry.update(verse_metadata)
                        self.save_assessment_data_reanalysis(entry)

                    messagebox.showinfo("Saved", "Assessment data saved successfully for verse:\n" + verse)

        self.accumulated_pankti = original_accumulated_pankti

        if hasattr(self, 'copy_button') and self.copy_button.winfo_exists():
            self.copy_button.config(state=tk.NORMAL)

    def normalize_save_results_reanalysis(self, v):
        # Convert real NaN â†’ ""
        if pd.isna(v):
            return ""
        # Convert None â†’ ""
        if v is None:
            return ""
        # Convert the literal string "NA" (any case, with whitespace) â†’ ""
        s = str(v).strip()
        return "" if s.upper() == "NA" else s

    def safe_equal_save_results_reanalysis(self, val1, val2):
        return self.normalize_save_results_reanalysis(val1) == self.normalize_save_results_reanalysis(val2)

    def prompt_copy_to_clipboard_reanalysis(self):
        print("Prompting to copy re-analysis to clipboard...")

        copy_prompt = messagebox.askyesno(
            "Copy to Clipboard",
            f"Would you like to copy the re-analysis for the verse '{self.accumulated_pankti}' to your clipboard?"
        )

        if not copy_prompt:
            return

        # Validation checks
        if not self.accumulated_pankti:
            messagebox.showerror("Error", "No verse (pankti) available to copy.")
            return

        if not self.accumulated_meanings or not self.accumulated_finalized_matches or not self.all_new_entries:
            messagebox.showerror("Error", "Missing re-analysis data to copy.")
            print("Error: Data is incomplete for clipboard copy.")
            return

        try:
            # Use the existing composing utility
            clipboard_text = self.compose_clipboard_text_for_chatgpt_reanalysis()
            pyperclip.copy(clipboard_text)
            messagebox.showinfo("Copied", "The re-analysis has been copied to the clipboard!")
            print("Clipboard content copied successfully.")

        except Exception as e:
            print(f"Unexpected error while copying reanalysis: {e}")
            messagebox.showerror("Error", f"Unexpected error occurred: {e}")

    def compose_clipboard_text_for_chatgpt_reanalysis(self):
        clipboard_text = "### Detailed Reanalysis & Literal Translation\n\n"
        clipboard_text += (
            f"The verse **'{self.accumulated_pankti}'** has undergone re-analysis. "
            "Below is a breakdown of each word with revised user-selected meanings and grammar details.\n\n"
        )

        # --- Preceding Verses & Translations ---
        existing_data = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")
        selected_columns = [
            'S. No.', 'Verse', 'Verse No.', 'Stanza No.', 'Text Set No.',
            'Raag (Fixed)', 'Sub-Raag', 'Writer (Fixed)', 'Verse Configuration (Optional)',
            'Stanza Configuration (Optional)', 'Bani Name', 'Musical Note Configuration',
            'Special Type Demonstrator', 'Verse Type', 'Page Number'
        ]
        df_filtered = existing_data[selected_columns]
        chosen_list = df_filtered[
            df_filtered["Verse"].str.strip() == self.accumulated_pankti.strip()
        ].drop_duplicates().to_dict(orient="records")
        current_candidate = chosen_list[0] if chosen_list else None

        preceding_verses_text = ""
        if current_candidate:
            text_set_no = current_candidate.get("Text Set No.")
            try:
                current_verse_no = int(current_candidate.get("Verse No."))
            except (ValueError, TypeError):
                current_verse_no = None

            if current_verse_no is not None:
                filtered_data = existing_data[existing_data["Text Set No."] == text_set_no]
                consecutive_verses = []
                target_verse_no = current_verse_no - 1
                while True:
                    row = filtered_data[filtered_data["Verse No."] == target_verse_no]
                    if row.empty:
                        break
                    row_data = row.iloc[0]
                    consecutive_verses.insert(0, row_data)
                    target_verse_no -= 1

                if consecutive_verses:
                    preceding_verses_text += "\n### Preceding Verses & Translations\n\n"
                    for row_data in consecutive_verses:
                        verse_no = row_data.get("Verse No.", "")
                        verse_text = row_data.get("Verse", "")
                        translation = row_data.get("Translation", "")
                        preceding_verses_text += f"**Verse {verse_no}:** {verse_text}\n"
                        preceding_verses_text += f"**Translation:** {translation}\n\n"

        clipboard_text += preceding_verses_text

        # --- Past Translation of the Current Verse ---
        past_translation_text = ""
        if current_candidate:
            text_set_no = current_candidate.get("Text Set No.")
            try:
                current_verse_no = int(current_candidate.get("Verse No."))
            except (ValueError, TypeError):
                current_verse_no = None

            if current_verse_no is not None:
                filtered_data = existing_data[existing_data["Text Set No."] == text_set_no]
                # Instead of iterating for preceding verses, we directly extract the row for the current verse.
                row = filtered_data[filtered_data["Verse No."] == current_verse_no]
                if not row.empty:
                    row_data = row.iloc[0]
                    verse_text = row_data.get("Verse", "")
                    translation = row_data.get("Translation", "")
                    past_translation_text += "\n### Past Translation of the Current Verse\n\n"
                    past_translation_text += f"**Verse {current_verse_no}:** {verse_text}\n"
                    past_translation_text += f"**Translation:** {translation}\n\n"

        clipboard_text += past_translation_text

        current_verse_words = self.accumulated_pankti.split()

        def find_sublist_index(haystack, needle):
            for i in range(len(haystack) - len(needle) + 1):
                if haystack[i:i + len(needle)] == needle:
                    return i
            return -1

        start_index = find_sublist_index(self.pankti_words, current_verse_words)
        if start_index == -1:
            start_index = 0

        for i, word in enumerate(current_verse_words):
            actual_index = start_index + i
            clipboard_text += f"**Word {i + 1}: {word}**\n"

            acc_entry = self.accumulated_meanings[actual_index] if actual_index < len(self.accumulated_meanings) else {}
            meanings_list = acc_entry.get("meanings", []) if isinstance(acc_entry, dict) else acc_entry
            meanings_str = ", ".join(meanings_list) if meanings_list else "No user-selected meanings available"
            clipboard_text += f"- **User-Selected Meanings:** {meanings_str}\n"

            # --- Past Assessment Details ---
            assessment_details = self.past_word_details.get(actual_index, {})
            if assessment_details:
                clipboard_text += "- **Past Assessment Details:**\n"
                # Display past meanings if available
                past_meanings = assessment_details.get("darpan_meanings", [])
                if past_meanings:
                    clipboard_text += f"   - **Past Meanings:** {', '.join(past_meanings)}\n"
                # Display grammar fields
                clipboard_text += f"   - **Vowel Ending:** {self._norm_get(assessment_details, '\\ufeffVowel Ending') or 'N/A'}\n"
                clipboard_text += f"   - **Number / à¨µà¨šà¨¨:** {assessment_details.get('Number / à¨µà¨šà¨¨', 'N/A')}\n"
                clipboard_text += f"   - **Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£:** {assessment_details.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'N/A')}\n"
                clipboard_text += f"   - **Gender / à¨²à¨¿à©°à¨—:** {assessment_details.get('Gender / à¨²à¨¿à©°à¨—', 'N/A')}\n"
                clipboard_text += f"   - **Word Root:** {assessment_details.get('Word Root', 'N/A')}\n"
                clipboard_text += f"   - **Word Type:** {self._norm_get(assessment_details, 'Type') or 'N/A'}\n"

            # --- Grammar Options ---
            clipboard_text += "- **Grammar Options:**\n"
            finalized_matches_list = self.accumulated_finalized_matches[actual_index] if actual_index < len(self.accumulated_finalized_matches) else []

            if finalized_matches_list:
                for option_idx, match in enumerate(finalized_matches_list, start=1):
                    clipboard_text += (
                        f"  - **Option {option_idx}:**\n"
                        f"      - **Word:** {self._norm_get(match, 'Word') or 'N/A'}\n"
                        f"      - **Vowel Ending:** {self._norm_get(match, '\\ufeffVowel Ending') or 'N/A'}\n"
                        f"      - **Number / à¨µà¨šà¨¨:** {match.get('Number / à¨µà¨šà¨¨', 'N/A')}\n"
                        f"      - **Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£:** {match.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'N/A')}\n"
                        f"      - **Gender / à¨²à¨¿à©°à¨—:** {match.get('Gender / à¨²à¨¿à©°à¨—', 'N/A')}\n"
                        f"      - **Word Root:** {match.get('Word Root', 'N/A')}\n"
                        f"      - **Type:** {self._norm_get(match, 'Type') or 'N/A'}\n"
                        f"      - **Literal Translation (Option {option_idx}):** The word '{word}' functions as a "
                        f"'{self._norm_get(match, 'Type') or 'N/A'}' with '{match.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'N/A')}' usage, "
                        f"in the '{match.get('Number / à¨µà¨šà¨¨', 'N/A')}' form and '{match.get('Gender / à¨²à¨¿à©°à¨—', 'N/A')}' gender. Translation: â€¦\n"
                    )
            else:
                clipboard_text += "  - No finalized grammar options available\n"

            clipboard_text += "\n"

        if 'à¥¥' in current_verse_words:
            clipboard_text += (
                "**Symbol:** à¥¥\n"
                "- **Meaning:** End of verse or sentence\n"
                "- **Context:** Denotes the conclusion of the verse.\n\n"
            )

        clipboard_text += "\n### Literal Translation Prompt\n"
        clipboard_text += (
            f"Using the above user-selected meanings and grammar details for the verse '{self.accumulated_pankti}', "
            "please generate a literal translation that adheres strictly to the grammatical structure, "
            "capturing the tense, number, gender, and function accurately."
        )

        return clipboard_text

    def prompt_for_assessment_once_reanalysis(self):
        """Opens a modal prompt for re-analysis of the entire verse and returns the collected assessment data."""
        assessment_win = tk.Toplevel(self.root)
        assessment_win.title(f"Re-Assessment: '{self.accumulated_pankti}'")
        assessment_win.configure(bg='light gray')

        instruction_label = tk.Label(
            assessment_win,
            text="Paste the updated translation or assessment for this verse:",
            font=("Helvetica", 14), bg="light gray"
        )
        instruction_label.pack(pady=10)

        analysis_text = scrolledtext.ScrolledText(
            assessment_win, width=80, height=10,
            font=("Helvetica", 12), wrap=tk.WORD
        )
        analysis_text.pack(padx=20, pady=10)

        cb_frame = tk.Frame(assessment_win, bg="light gray")
        cb_frame.pack(pady=10)

        framework_var = tk.BooleanVar()
        explicit_var = tk.BooleanVar()

        framework_cb = tk.Checkbutton(cb_frame, text="Framework?", variable=framework_var,
                                    font=("Helvetica", 12), bg="light gray")
        framework_cb.pack(side=tk.LEFT, padx=10)

        explicit_cb = tk.Checkbutton(cb_frame, text="Explicit?", variable=explicit_var,
                                    font=("Helvetica", 12), bg="light gray")
        explicit_cb.pack(side=tk.LEFT, padx=10)

        assessment_data = {}

        def on_save():
            translation = analysis_text.get("1.0", tk.END).strip()
            if not translation:
                messagebox.showerror("Error", "Please provide the revised assessment or translation.")
                return
            assessment_data["Translation"] = translation
            assessment_data["Framework?"] = framework_var.get()
            assessment_data["Explicit?"] = explicit_var.get()
            assessment_win.destroy()

        save_btn = tk.Button(
            assessment_win, text="Save Re-Assessment",
            command=on_save, font=("Helvetica", 14, "bold"),
            bg="#2a7b39", fg="white", padx=20, pady=10
        )
        save_btn.pack(pady=20)

        assessment_win.transient(self.root)
        assessment_win.grab_set()
        self.root.wait_window(assessment_win)

        return assessment_data

    def prompt_for_final_grammar_reanalysis(self, word_entries):
        """
        Opens a modal window to finalize grammar during reanalysis.
        Displays a structured prompt for ChatGPT and allows selection from available grammar options.
        """
        final_choice = {}

        final_win = tk.Toplevel(self.root)
        final_win.title(f"Reanalysis: Finalize Grammar for '{word_entries[0]['Word']}'")
        final_win.configure(bg='light gray')

        # --- Build prompt for clipboard ---
        prompt_lines = [
            f"Finalize the applicable grammar for the word: {word_entries[0]['Word']}"
        ]
        prompt_lines.append("The following grammar options are available:")

        fields = [
            "\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
            "Gender / à¨²à¨¿à©°à¨—",   "Word Root", "Type"
        ]

        for idx, entry in enumerate(word_entries, start=1):
            # coerce each field to str, converting NaN â†’ ""
            parts = []
            for f in fields:
                val = self._norm_get(entry, f) or ""
                if pd.isna(val):
                    val = ""
                parts.append(str(val))
            summary = " | ".join(parts)

            prompt_lines.append(f"Option {idx}: {summary}")

        prompt_text = "\n".join(prompt_lines)

        # --- Prompt display with copy ---
        prompt_frame = tk.Frame(final_win, bg="light gray")
        prompt_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        tk.Label(prompt_frame,
                text="ChatGPT Prompt for Grammar Reassessment:",
                font=("Helvetica", 14, "bold"),
                bg="light gray").pack(anchor="w", pady=(0, 5))

        prompt_text_widget = scrolledtext.ScrolledText(prompt_frame, width=80, height=6,
                                                    font=("Helvetica", 12), wrap=tk.WORD)
        prompt_text_widget.pack(fill=tk.BOTH, expand=True)
        prompt_text_widget.insert(tk.END, prompt_text)
        prompt_text_widget.config(state=tk.DISABLED)

        def copy_prompt():
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt_text)
            messagebox.showinfo("Copied", "Prompt text copied to clipboard!")

        tk.Button(prompt_frame, text="Copy Prompt", command=copy_prompt,
                font=("Helvetica", 12, "bold"), bg="#007acc", fg="white", padx=10, pady=5
                ).pack(anchor="e", pady=5)

        # --- Instruction and option selection ---
        tk.Label(final_win,
                text="Please select the correct grammar from the following options:",
                font=("Helvetica", 14), bg="light gray").pack(pady=10)

        choice_var = tk.IntVar(value=0)
        options_container = tk.Frame(final_win, bg="light gray")
        options_container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(options_container, bg="light gray", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = tk.Scrollbar(options_container, orient="vertical", command=canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=vsb.set)

        options_frame = tk.Frame(canvas, bg="light gray")
        canvas.create_window((0, 0), window=options_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        options_frame.bind("<Configure>", on_frame_configure)

        def as_str(val):
            # turn real NaN â†’ "" and everything else â†’ string
            return "" if pd.isna(val) else str(val)

        fields = [
            "\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",
            "Gender / à¨²à¨¿à©°à¨—",   "Word Root", "Type"
        ]

        for idx, entry in enumerate(word_entries):
            summary = " | ".join(
                as_str(self._norm_get(entry, f) or "") for f in fields
            )

            tk.Radiobutton(options_frame,
                        text=f"Option {idx+1}: {summary}",
                        variable=choice_var,
                        value=idx,
                        bg="light gray",
                        font=("Helvetica", 12),
                        anchor='w',
                        justify=tk.LEFT,
                        selectcolor='light blue'
                        ).pack(anchor="w", padx=10, pady=5)

        def on_save():
            selected_index = choice_var.get()
            nonlocal final_choice
            final_choice = word_entries[selected_index]
            final_win.destroy()

        tk.Button(final_win, text="Save Choice",
                command=on_save,
                font=("Helvetica", 14, "bold"),
                bg="#2a7b39", fg="white", padx=20, pady=10).pack(pady=20)

        final_win.transient(self.root)
        final_win.grab_set()
        self.root.wait_window(final_win)
        return final_choice

    def save_assessment_data_reanalysis(self, new_entry):
        """
        Saves a new re-analysis entry to the Excel file.
        Handles grammar and translation revision tracking for specific word occurrences.
        """
        file_path = "1.2.1 assessment_data.xlsx"
        df_existing = self.load_existing_assessment_data(file_path)

        grammar_keys = [
            '\ufeffVowel Ending', 'Number / à¨µà¨šà¨¨', 'Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£',
            'Gender / à¨²à¨¿à©°à¨—', 'Word Root', 'Type'
        ]

        # Update translation for all entries of the same verse
        df_existing.loc[df_existing["Verse"] == new_entry["Verse"], "Translation"] = new_entry["Translation"]

        # Locate matching entries
        matching_rows = df_existing[
            (df_existing["Word"] == new_entry["Word"]) &
            (df_existing["Verse"] == new_entry["Verse"]) &
            (df_existing["Word Index"] == new_entry["Word Index"])
        ]

        if not matching_rows.empty:
            latest_idx = matching_rows["Grammar Revision"].idxmax()
            latest_row = df_existing.loc[latest_idx]
            differences = any(new_entry.get(key) != self._norm_get(latest_row, key) for key in grammar_keys)

            if differences:
                new_revision = matching_rows["Grammar Revision"].max() + 1
                new_entry["Grammar Revision"] = new_revision

                for idx in matching_rows.index:
                    for key in grammar_keys:
                        df_existing.at[idx, key] = new_entry.get(key)
                    df_existing.at[idx, "Grammar Revision"] = new_revision

                    for key, value in new_entry.items():
                        if key not in grammar_keys and key != "Translation":
                            if key in ("Framework?", "Explicit?"):
                                df_existing.at[idx, key] = int(value)
                            else:
                                df_existing.at[idx, key] = value

                # Update Selected Darpan Meaning
                global_index = new_entry.get("Word Index", 0)
                if len(self.accumulated_meanings) > global_index:
                    acc_entry = self.accumulated_meanings[global_index]
                    selected_meaning = "| ".join(acc_entry.get("meanings", [])) if isinstance(acc_entry, dict) else ", ".join(acc_entry)
                    for idx in matching_rows.index:
                        df_existing.at[idx, "Selected Darpan Meaning"] = selected_meaning

                # Update Translation Revision
                verse_mask = df_existing["Verse"] == new_entry["Verse"]
                latest_revision = df_existing.loc[verse_mask, "Grammar Revision"].max()
                df_existing.loc[verse_mask, "Translation Revision"] = latest_revision
            else:
                return  # No changes, skip saving
        else:
            new_entry["Grammar Revision"] = 1
            current_revision = df_existing[df_existing["Verse"] == new_entry["Verse"]]["Translation Revision"].max()
            new_entry["Translation Revision"] = (current_revision + 1) if not pd.isna(current_revision) else 1

            # Set Selected Darpan Meaning
            global_index = new_entry.get("Word Index", 0)
            if len(self.accumulated_meanings) > global_index:
                acc_entry = self.accumulated_meanings[global_index]
                selected_meaning = "| ".join(acc_entry.get("meanings", [])) if isinstance(acc_entry, dict) else ", ".join(acc_entry)
                new_entry["Selected Darpan Meaning"] = selected_meaning

            df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)

        try:
            df_existing.to_excel(file_path, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save reanalysis data: {e}")

    def ensure_meanings_slot_initialized(self, index, word):
        """Ensure self.accumulated_meanings[index] is initialized with a valid structure."""
        while len(self.accumulated_meanings) <= index:
            self.accumulated_meanings.append({"word": None, "meanings": []})

        if not isinstance(self.accumulated_meanings[index], dict) or "word" not in self.accumulated_meanings[index]:
            self.accumulated_meanings[index] = {"word": word, "meanings": []}

    def setup_main_analysis_interface(self):
        """Builds the main analysis interface for Literal Meaning Analysis."""
        # Define a consistent color scheme
        BG_COLOR = "#f0f0f0"        # Light gray background for main area
        HEADER_COLOR = "#2c3e50"    # Dark slate-like header
        HEADER_TEXT_COLOR = "white"
        BUTTON_COLOR = "#007acc"    # A pleasant blue for action buttons
        BUTTON_TEXT_COLOR = "white"
        NAV_BUTTON_COLOR = "#5f9ea0" # CadetBlue for navigation
        LABEL_TEXT_COLOR = "#333333"
        
        # Define fonts
        TITLE_FONT = ("Helvetica", 20, "bold")
        LABEL_FONT = ("Helvetica", 14, "bold")
        ENTRY_FONT = ("Helvetica", 14)
        BUTTON_FONT = ("Helvetica", 14, "bold")
        RESULT_FONT = ("Helvetica", 12)

        # Clear existing widgets in case we re-enter
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=BG_COLOR)

        # Main frame (entire interface)
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Label
        header_label = tk.Label(
            self.main_frame,
            text="Grammar Analyzer",
            bg=HEADER_COLOR,
            fg=HEADER_TEXT_COLOR,
            font=TITLE_FONT,
            pady=10
        )
        header_label.pack(fill=tk.X, pady=(0, 20))

        # Label and Entry for Pankti
        self.pankti_label = tk.Label(
            self.main_frame,
            text="Please share the Pankti:",
            bg=BG_COLOR,
            fg=LABEL_TEXT_COLOR,
            font=LABEL_FONT
        )
        self.pankti_label.pack(anchor="w", pady=(0, 5))

        self.pankti_entry = tk.Entry(
            self.main_frame,
            width=70,
            font=ENTRY_FONT,
            bd=3,
            relief=tk.GROOVE
        )
        self.pankti_entry.pack(pady=(0, 15))

        # Analyze Button
        self.analyze_button = tk.Button(
            self.main_frame,
            text="Analyze",
            command=self.analyze_pankti,
            font=BUTTON_FONT,
            bg=BUTTON_COLOR,
            fg=BUTTON_TEXT_COLOR,
            relief=tk.RAISED,
            padx=30,
            pady=10
        )
        self.analyze_button.pack(pady=(0, 20))

        # Results Text Area
        self.results_text = scrolledtext.ScrolledText(
            self.main_frame,
            width=90,
            height=20,
            font=RESULT_FONT,
            bd=3,
            relief=tk.SUNKEN,
            wrap=tk.WORD
        )
        self.results_text.pack(pady=(0, 20))

        # Navigation Frame
        nav_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        nav_frame.pack(fill=tk.X, pady=10)

        # --- New Word Navigation Panel ---
        # A label to display the current word
        self.word_label = tk.Label(nav_frame, text="", font=("Helvetica", 16, "bold"),
                                bg="white", fg="black", width=20, relief=tk.SUNKEN)
        self.word_label.pack(side=tk.LEFT, padx=10)
        self.update_current_word_label()  # Update this label based on self.current_word_index

        # Previous button for word navigation
        self.prev_button = tk.Button(
            nav_frame,
            text="Previous",
            command=self.prev_word,
            state=tk.DISABLED,
            font=BUTTON_FONT,
            bg=NAV_BUTTON_COLOR,
            fg="white",
            padx=20,
            pady=5
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))

        # Next button for word navigation
        self.next_button = tk.Button(
            nav_frame,
            text="Next",
            command=self.next_word,
            state=tk.DISABLED,
            font=BUTTON_FONT,
            bg=NAV_BUTTON_COLOR,
            fg="white",
            padx=20,
            pady=5
        )
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))

        # Select Word button to analyze the currently displayed word
        select_word_btn = tk.Button(
            nav_frame,
            text="Select Word",
            command=self.select_current_word,
            font=BUTTON_FONT,
            bg=BUTTON_COLOR,
            fg=BUTTON_TEXT_COLOR,
            padx=20,
            pady=5
        )
        select_word_btn.pack(side=tk.LEFT, padx=(0, 10))
        # --- End Word Navigation Panel ---

        # Copy Analysis Button (initially disabled)
        self.copy_button = tk.Button(
            nav_frame,
            text="Copy Analysis",
            command=self.prompt_copy_to_clipboard,
            font=BUTTON_FONT,
            bg="#1b95e0",   # A slightly different blue for variety
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED
        )
        self.copy_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Back to Dashboard Button
        back_dashboard_btn = tk.Button(
            nav_frame,
            text="Back to Dashboard",
            command=self.back_to_dashboard,
            font=BUTTON_FONT,
            bg="red",
            fg="white",
            padx=20,
            pady=5
        )
        back_dashboard_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Create a new "Save Results" button:
        self.save_results_btn = tk.Button(
            nav_frame,
            text="Save Results",
            command=lambda: self.prompt_save_results(self.all_new_entries, skip_copy=True),
            font=BUTTON_FONT,
            bg="#1b95e0",   # Choose a color you like
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED  # Initially disabled
        )
        self.save_results_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def back_to_dashboard(self):
        """Destroy the current main interface and return to the dashboard."""
        # Destroy the main analysis interface
        self.main_frame.destroy()
        # Optionally, reset any state if needed here.
        # Then, show the dashboard again:
        self.show_dashboard()

    def launch_literal_analysis(self):
        """Clears the dashboard and builds the literal meaning analysis interface."""
        # Clear the root window (removes the dashboard)
        for widget in self.root.winfo_children():
            widget.destroy()

        # Optionally update the window title
        self.root.title("Literal Meaning Analysis")

        # Build the main analysis interface
        self.setup_main_analysis_interface()

    def user_input(self, word, pankti):
        print(f"Opening input window for {word}")
        self.input_submitted = False
        # normalize for repeat-note consistency
        verse_key = unicodedata.normalize(
            "NFC", re.sub(r"\s+", " ", pankti.replace('à¥¥', '').strip())
        )
        raw_tokens = pankti.split()
        word_norm = unicodedata.normalize("NFC", word.strip())
        safe_idx = max(0, min(self.current_word_index, len(raw_tokens)))
        occurrence_idx = sum(
            1
            for tok in raw_tokens[:safe_idx]
            if unicodedata.normalize("NFC", tok.strip().replace('à¥¥', '')) == word_norm
        )
        if occurrence_idx > 0 and not getattr(self, "_use_inline_literal_banner", True):
            self._maybe_show_repeat_important_note(word_norm, occurrence_idx, verse_key)

        self.input_window = tk.Toplevel(self.root)
        self.input_window.title(f"Input for {word}")
        self.input_window.configure(bg='light gray')
        self.input_window.state('zoomed')
        self.input_window.resizable(True, True)

        # ---------------------------
        # Display the Pankti on top
        # ---------------------------
        pankti_frame = tk.Frame(self.input_window, bg='light gray')
        pankti_frame.pack(fill=tk.X, padx=20, pady=10)

        pankti_display = tk.Text(
            pankti_frame, wrap=tk.WORD, bg='light gray', font=('Arial', 32),
            height=2, padx=5, pady=5
        )
        pankti_display.pack(fill=tk.X, expand=False)
        pankti_display.insert(tk.END, pankti)
        pankti_display.tag_add("center", "1.0", "end")
        pankti_display.tag_configure("center", justify='center')

        # Highlight the word at self.current_word_index
        words = pankti.split()
        start_idx = 0
        for i, w in enumerate(words):
            # When we reach the word at current_word_index, calculate its start/end
            if i == self.current_word_index:
                end_idx = start_idx + len(w)
                pankti_display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
                pankti_display.tag_config("highlight", foreground="red", font=('Arial', 32, 'bold'))
                break
            # Move the start index past this word plus one space
            start_idx += len(w) + 1

        pankti_display.config(state=tk.DISABLED)

        # ---------------------------
        # Create a horizontal PanedWindow for split layout
        # ---------------------------
        split_pane = tk.PanedWindow(self.input_window, orient=tk.HORIZONTAL, bg='light gray')
        split_pane.pack(fill=tk.BOTH, expand=True)

        # Left pane: Meanings
        self.left_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(self.left_pane, stretch="always")
        tk.Label(self.left_pane, text=f"Meanings for {word}:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(anchor='center', pady=(0, 10))
        self.meanings_scrollbar = tk.Scrollbar(self.left_pane, orient=tk.VERTICAL)
        self.meanings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.meanings_canvas = tk.Canvas(self.left_pane, bg='light gray', borderwidth=0,
                                        yscrollcommand=self.meanings_scrollbar.set)
        self.meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.meanings_scrollbar.config(command=self.meanings_canvas.yview)
        self.meanings_inner_frame = tk.Frame(self.meanings_canvas, bg='light gray')
        self.meanings_canvas.create_window((0, 0), window=self.meanings_inner_frame, anchor='nw')

        # Right pane: Grammar Options
        right_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(right_pane, stretch="always")
        tk.Label(right_pane, text="Select Grammar Options:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(pady=10)
        self.setup_options(
            right_pane,
            "Do you know the Number of the word?",
            [("Singular", "Singular / à¨‡à¨•"), ("Plural", "Plural / à¨¬à¨¹à©"), ("Not Applicable", "NA")],
            self.number_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Gender of the word?",
            [("Masculine", "Masculine / à¨ªà©à¨²à¨¿à©°à¨—"), ("Feminine", "Feminine / à¨‡à¨¸à¨¤à¨°à©€"), ("Neutral", "Trans / à¨¨à¨ªà©à¨‚à¨¸à¨•")],
            self.gender_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Part of Speech for the word?",
            [("Noun", "Noun / à¨¨à¨¾à¨‚à¨µ"), ("Adjective", "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£"),
            ("Adverb", "Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£"), ("Verb", "Verb / à¨•à¨¿à¨°à¨¿à¨†"),
            ("Pronoun", "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ"), ("Postposition", "Postposition / à¨¸à©°à¨¬à©°à¨§à¨•"),
            ("Conjunction", "Conjunction / à¨¯à©‹à¨œà¨•"), ("Interjection", "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•")],
            self.pos_var
        )

        # ---------------------------
        # Bottom Button Frame
        # ---------------------------
        button_frame = tk.Frame(self.input_window, bg='light gray')
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Submit", command=self.submit_input,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)
        tk.Button(button_frame, text="Skip", command=self.skip_input,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)

        # ---------------------------
        # Launch the dictionary lookup in a separate thread
        # ---------------------------
        self.start_progress()
        threading.Thread(target=self.lookup_meanings_thread, args=(word,), daemon=True).start()

        self.input_window.transient(self.root)
        self.input_window.grab_set()
        self.root.wait_window(self.input_window)
        print(f"Input window for {word} closed")

    def lookup_meanings_thread(self, word):
        """
        Performs the dictionary lookup in a separate thread and then
        schedules the update of the meanings UI on the main thread.
        """
        meanings = self.lookup_word_in_dictionary(word)
        # Schedule the UI update on the main thread
        self.root.after(0, lambda: self.update_meanings_ui(meanings))

    def update_meanings_ui(self, meanings):
        """
        Updates the meanings UI with the lookup results.
        Stops the progress bar and populates the meanings section.
        """
        self.stop_progress()  # Stop the progress window now that lookup is complete
        self.accumulate_meanings_data(meanings)
        split_meanings = self.split_meanings_for_display(meanings)
        # Clear any existing widgets in the meanings inner frame
        for widget in self.meanings_inner_frame.winfo_children():
            widget.destroy()
        # Repopulate the meanings UI
        for i, column in enumerate(split_meanings.values()):
            column_frame = tk.Frame(self.meanings_inner_frame, bg='light gray')
            column_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nw')
            for meaning in column:
                tk.Label(column_frame, text=f"- {meaning}", bg='light gray',
                        font=('Arial', 12), wraplength=400, justify=tk.LEFT).pack(anchor='w', padx=15, pady=5)
        self.meanings_inner_frame.update_idletasks()
        self.meanings_canvas.config(scrollregion=self.meanings_inner_frame.bbox("all"))

    def split_meanings_for_display(self, meanings): # Helper function to split meanings into two columns
        # Determine if 'meanings' is a dict or list.
        if isinstance(meanings, dict):
            mlist = meanings.get("meanings", [])
        else:
            mlist = meanings  # Assume it's already a list.
            
        # Now split the list into two halves.
        mid = len(mlist) // 2
        left = mlist[:mid]
        right = mlist[mid:]
        return {"left": left, "right": right}

    def _rule_key_from_entry(self, d):
        return " | ".join([
            d.get("Word",""),
            d.get("\ufeffVowel Ending",""),
            d.get("Number / à¨µà¨šà¨¨",""),
            d.get("Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£",""),
            d.get("Gender / à¨²à¨¿à©°à¨—",""),
            d.get("Word Root",""),
            d.get("Type",""),
        ]).strip()

    def submit_matches(self):
        any_selection = False
        current_entries = []  # Local list for entries of the current word

        # Process matching rule checkboxes as before
        for var, match in self.match_vars:
            if var.get():
                match_string = match[0]
                self.results_text.insert(tk.END, f"{match_string}\n")
                self.results_text.insert(tk.END, "-" * 50 + "\n")
                data = match_string.split(" | ")
                new_entry = {
                    "Word": data[0],
                    "\ufeffVowel Ending": data[1],
                    "Number / à¨µà¨šà¨¨": data[2],
                    "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£": data[3],
                    "Gender / à¨²à¨¿à©°à¨—": data[4],
                    "Word Root": data[5],
                    "Type": data[6],
                }
                current_entries.append(new_entry)
                any_selection = True

        # Also update the accumulated meanings for the current word
        selected_meanings = [meaning for var, meaning in self.meaning_vars if var.get()]
        self.accumulate_meanings_data(selected_meanings)

        # --- NEW BLOCK: Check for repeated word and prompt update for previous occurrences ---
        current_word = self.pankti_words[self.current_word_index]
        # Find the first occurrence index for the current word
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == current_word), self.current_word_index)

        # Get the current selection from the UI for this occurrence.
        current_selected = selected_meanings  # already computed

        # If this is a repeated occurrence, merge prior selections for this word only.
        if self.current_word_index != first_index:
            merged_meanings = []
            for idx in range(first_index, self.current_word_index):
                # Only merge if the word at that index matches the current word.
                if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                    entry = self.accumulated_meanings[idx]
                    if isinstance(entry, dict):
                        merged_meanings.extend(entry.get("meanings", []))
                    else:
                        merged_meanings.extend(entry)
            # Remove duplicates while preserving order.
            prior_meanings = list(dict.fromkeys(merged_meanings))
            
            # Compare the current selection to prior selections.
            if set(current_selected) != set(prior_meanings):
                update_prev = messagebox.askyesno(
                    "Update Previous Meanings",
                    f"You have selected different meanings for the word '{current_word}'.\n"
                    "Do you want to update the meanings for all previous occurrences of this word?"
                )
                if update_prev:
                    for idx in range(first_index, self.current_word_index):
                        if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                            self.accumulated_meanings[idx] = {"word": current_word, "meanings": current_selected}

        # Finally, update (or add) the current occurrence's accumulated meanings with only the current selection.
        if self.current_word_index < len(self.accumulated_meanings):
            self.accumulated_meanings[self.current_word_index] = {"word": current_word, "meanings": current_selected}
        else:
            self.accumulated_meanings.append({"word": current_word, "meanings": current_selected})

        # --- End NEW BLOCK ---

        # --- Assign verse using word index and verse boundaries ---
        verse_boundaries = []
        pointer = 0
        for verse in self.selected_verses:
            verse_words = verse.split()
            start = pointer
            end = pointer + len(verse_words)
            verse_boundaries.append((start, end))
            pointer = end

        current_verse = None
        for i, (start, end) in enumerate(verse_boundaries):
            if start <= self.current_word_index < end:
                current_verse = self.selected_verses[i]
                break

        # Attach current verse to each grammar entry
        for entry in current_entries:
            entry["Verse"] = current_verse

        # Process finalized matches (avoiding duplicates)
        finalized_matches = []
        for var, match in self.match_vars:
            if var.get():
                match_word = match[0].split(" | ")[0]
                for entry in current_entries:
                    if entry["Word"] == match_word and entry not in finalized_matches:
                        finalized_matches.append(entry)
        self.accumulate_finalized_matches(finalized_matches)
            
        if not any_selection:
            messagebox.showwarning("No Selection", "No matches were selected. Please select at least one match.")
        else:
            self.match_window.destroy()
            # Add the current word's entries to the global accumulator
            self.all_new_entries.extend(current_entries)
            self.current_word_index += 1
            self.process_next_word()

    def show_matches(self, matches, pankti, meanings, max_display=30):
        # Destroy any existing match window
        if hasattr(self, 'match_window') and self.match_window.winfo_exists():
            self.match_window.destroy()

        # Create the match window
        self.match_window = tk.Toplevel(self.root)
        self.match_window.title("Select Matches and Meanings")
        self.match_window.configure(bg='light gray')
        self.match_window.state('zoomed')
        # New window â‡’ allow a fresh one-time resize binding
        self._inline_resize_bound = False
        try:
            # If the window is destroyed via an atypical path, ensure the next window can rebind
            # and clear any lingering inline banner references.
            def _on_destroy(_e=None):
                try:
                    self._inline_resize_bound = False
                    self.literal_note_frame = None
                    self.literal_note_title = None
                    self.literal_note_body  = None
                except Exception:
                    pass
            self.match_window.bind("<Destroy>", _on_destroy, add="+")
        except Exception:
            pass

        # Reset check-variable lists for matches and meanings
        self.match_vars = []      # For matching rule checkboxes
        self.meaning_vars = []    # For meaning checkboxes
        unique_matches = self.filter_unique_matches(matches)
        self.all_matches.append(unique_matches)

        # ---------------------------
        # Display the complete Pankti at the top
        # ---------------------------
        pankti_frame = tk.Frame(self.match_window, bg='light gray')
        pankti_frame.pack(fill=tk.BOTH, padx=30, pady=20)

        pankti_display = tk.Text(pankti_frame, wrap=tk.WORD, bg='light gray',
                                font=('Arial', 32), height=2, padx=5, pady=5)
        pankti_display.pack(fill=tk.BOTH, expand=False)
        pankti_display.insert(tk.END, f"{pankti}")
        pankti_display.tag_add("center", "1.0", "end")
        pankti_display.tag_configure("center", justify='center')
        pankti_display.config(state=tk.DISABLED)

        # Compute the character offset for the word at self.current_word_index
        words = pankti.split()
        # Align the navigation token stream with the displayed verse tokens so
        # highlighting, indexing, and repeat detection use the same sequence.
        if getattr(self, "pankti_words", None) != words:
            self._norm_words_cache = [self._norm_tok(w) for w in words]
        self.pankti_words = words
        max_idx = len(words) - 1
        self.current_word_index = max(0, min(self.current_word_index, max_idx))
        idx = self.current_word_index
        start_idx = 0
        for i, w in enumerate(words):
            if i == idx:
                break
            # +1 accounts for the space between words
            start_idx += len(w) + 1
        end_idx = start_idx + len(words[idx])

        pankti_display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
        pankti_display.tag_config("highlight", foreground="red", font=('Arial', 32, 'bold'))
        pankti_display.config(state=tk.DISABLED)

        # ----- Inline Important Note â€” Literal Analysis (conditional replica of reanalysis) -----
        # Anchor just under the Pankti for deterministic placement (mirrors reanalysis)
        banner_anchor = tk.Frame(self.match_window, bg='light gray')
        banner_anchor.pack(fill=tk.X, padx=20, pady=(0, 0))

        # Compute repeat condition for the selected token
        display_word = self.pankti_words[idx] if idx < len(self.pankti_words) else words[idx]
        word_norm    = self._norm_tok(display_word)
        seen_before  = sum(self._norm_tok(w) == word_norm for w in words[:idx]) if word_norm else 0
        total_hits   = sum(self._norm_tok(w) == word_norm for w in words)        if word_norm else 0
        trigger_now  = bool(word_norm) and total_hits >= 2 and seen_before >= 1
        inline_allowed = bool(getattr(self, "_use_inline_literal_banner", True)) \
                         and not bool(getattr(self, "_suppress_repeat_notes_for_verse", False))

        if inline_allowed and trigger_now:
            # Create/reuse the same framed banner style used by reanalysis
            if not (getattr(self, "literal_note_frame", None)
                    and self.literal_note_frame.winfo_exists()
                    and self.literal_note_frame.master is banner_anchor):
                try:
                    if getattr(self, "literal_note_frame", None) and self.literal_note_frame.winfo_exists():
                        self.literal_note_frame.destroy()
                except Exception:
                    pass
                self.literal_note_frame = tk.Frame(banner_anchor, bg='AntiqueWhite', relief='groove', bd=2)
                self.literal_note_title = tk.Label(self.literal_note_frame,
                                                   text="Important Note â€” Literal Analysis",
                                                   font=("Arial", 14, 'bold'),
                                                   bg='AntiqueWhite')
                self.literal_note_title.pack(pady=(5, 0))
                self.literal_note_body  = tk.Label(self.literal_note_frame,
                                                   bg='AntiqueWhite', fg='black',
                                                   font=('Arial', 12), justify=tk.LEFT)
                self.literal_note_body.pack(pady=(0, 10), padx=10)

            explanation_text = (
                "â€¢ Highlighted selections (displayed in Yellow) indicate the meanings or grammar rules that "
                "were previously confirmed in your assessment.\n"
                "â€¢ This helps you quickly recognize which items reflect your earlier choices."
            )
            self.literal_note_body.config(
                text=explanation_text,
                wraplength=self._banner_wraplength(self.match_window)
            )
            if not self.literal_note_frame.winfo_ismapped():
                self.literal_note_frame.pack(fill=tk.X, padx=20, pady=(5, 10))
            try:
                if not getattr(self, "_inline_resize_bound", False):
                    self.match_window.bind("<Configure>", self._on_match_window_resize, add="+")
                    self._inline_resize_bound = True
            except Exception:
                pass
        else:
            # Clean up any stale banner if not needed
            if getattr(self, "literal_note_frame", None):
                try:
                    if self.literal_note_frame.winfo_exists():
                        self.literal_note_frame.destroy()
                except Exception:
                    pass
                self.literal_note_frame = None
                self.literal_note_title = None
                self.literal_note_body  = None
        # ----- end inline note -----

        # ---------------------------
        # Create a main frame to hold both the Meanings and the Matching Rules sections
        # ---------------------------
        main_frame = tk.Frame(self.match_window, bg='light gray')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # ---------------------------
        # Left Pane: Display Meanings as Checkboxes
        # ---------------------------
        meanings_frame = tk.Frame(main_frame, bg='light gray')
        meanings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(meanings_frame, text=f"Select Meanings for {self.pankti_words[self.current_word_index]}:",
                bg='light gray', font=('Arial', 14, 'bold')).pack(pady=10)
        # NEW: Add a toggle checkbutton to select/deselect all meanings
        self.select_all_meanings_var = tk.BooleanVar(value=True)
        tk.Checkbutton(meanings_frame, text="Select/Deselect All Meanings",
                    variable=self.select_all_meanings_var, bg='light gray',
                    font=('Arial', 12), command=self.toggle_all_meanings).pack(pady=5)

        meanings_canvas = tk.Canvas(meanings_frame, bg='light gray', borderwidth=0)
        meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meanings_scrollbar = tk.Scrollbar(meanings_frame, orient=tk.VERTICAL, command=meanings_canvas.yview)
        meanings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        meanings_canvas.config(yscrollcommand=meanings_scrollbar.set)

        meanings_content = tk.Frame(meanings_canvas, bg='light gray')
        meanings_canvas.create_window((0, 0), window=meanings_content, anchor='nw')

        # Split the meanings into two columns and create a checkbox for each meaning
        split_meanings = self.split_meanings_for_display(meanings)
        # --- Determine if the current word is repeated and merge prior selections ---
        current_word = self.pankti_words[self.current_word_index]
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == current_word), self.current_word_index)

        # Merge meanings from all occurrences from the first occurrence up to (but not including) the current occurrence.
        merged_meanings = []
        for idx in range(first_index, self.current_word_index):
            if idx < len(self.accumulated_meanings):
                entry = self.accumulated_meanings[idx]
                if isinstance(entry, dict):
                    merged_meanings.extend(entry.get("meanings", []))
                else:
                    merged_meanings.extend(entry)
        # Remove duplicates while preserving order
        prior_meanings = list(dict.fromkeys(merged_meanings))

        # If this is a repeated occurrence (current index is not the first occurrence), reorder the meanings.
        if self.current_word_index != first_index:
            # Obtain the current meanings list
            if isinstance(meanings, dict):
                current_meanings = meanings.get("meanings", [])
            else:
                current_meanings = meanings
            # Reorder: meanings from the first occurrence first, then the rest.
            reordered = [m for m in current_meanings if m in prior_meanings]
            reordered += [m for m in current_meanings if m not in prior_meanings]
            if isinstance(meanings, dict):
                meanings["meanings"] = reordered
            else:
                meanings = reordered

        # Now split the meanings for display using the (possibly) reordered meanings.
        split_meanings = self.split_meanings_for_display(meanings)

        # --- Create the checkboxes as before ---
        for i, column in enumerate(split_meanings.values()):
            column_frame = tk.Frame(meanings_content, bg='light gray')
            column_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nw')
            for meaning in column:
                # For repeated occurrences, preselect if the meaning was chosen in the first occurrence,
                # and highlight those checkbuttons with yellow.
                if self.current_word_index != first_index:
                    preselect = meaning in prior_meanings
                    bg_color = "yellow" if preselect else "light gray"
                else:
                    preselect = True
                    bg_color = "light gray"
                var = tk.BooleanVar(value=preselect)
                chk = tk.Checkbutton(
                    column_frame,
                    text=f"- {meaning}",
                    variable=var,
                    bg=bg_color,
                    font=('Arial', 12),
                    wraplength=325,
                    anchor='w',
                    justify=tk.LEFT,
                    selectcolor='light blue'
                )
                chk.pack(anchor='w', padx=15, pady=5)
                self.meaning_vars.append((var, meaning))

        meanings_content.update_idletasks()
        meanings_canvas.config(scrollregion=meanings_canvas.bbox("all"))

        # ---------------------------
        # Right Pane: Display Matching Rules as Checkboxes
        # ---------------------------
        matches_frame = tk.Frame(main_frame, bg='light gray')
        matches_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(matches_frame, text="Select the matching rules:",
                bg='light gray', font=('Arial', 14, 'bold')).pack(pady=10)

        matches_canvas = tk.Canvas(matches_frame, bg='light gray', borderwidth=0)
        matches_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        matches_scrollbar = tk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=matches_canvas.yview)
        matches_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        matches_canvas.config(yscrollcommand=matches_scrollbar.set)

        matches_content = tk.Frame(matches_canvas, bg='light gray')
        matches_canvas.create_window((0, 0), window=matches_content, anchor='nw')

        # Determine if the current word is repeated and gather prior grammar rules
        prior_rules = set()
        if self.current_word_index != first_index:
            for idx in range(first_index, self.current_word_index):
                if idx < len(self.accumulated_finalized_matches):
                    prior_rules.update({
                        self._rule_key_from_entry(entry)
                        for entry in self.accumulated_finalized_matches[idx]
                    })

        # Display each match with a checkbox
        for match in unique_matches[:max_display]:
            display_str = match[0]
            core = re.sub(r'\s*\(Matching Characters:\s*\d+\)\s*$', '', display_str).strip()
            if self.current_word_index != first_index:
                preselect = core in prior_rules
                bg_color = "yellow" if preselect else "light gray"
            else:
                preselect = False
                bg_color = "light gray"
            var = tk.BooleanVar(value=preselect)
            text_str = display_str if " (Matching Characters:" in display_str else f"{display_str} (Matching Characters: {match[1]})"
            tk.Checkbutton(
                matches_content,
                text=text_str,
                variable=var,
                bg=bg_color,
                selectcolor='light blue',
                anchor='w'
            ).pack(fill=tk.X, padx=10, pady=5)
            self.match_vars.append((var, match))

        matches_content.update_idletasks()
        matches_canvas.config(scrollregion=matches_canvas.bbox("all"))

        # ---------------------------
        # Bottom Button Frame: Submit and Back
        # ---------------------------
        button_frame = tk.Frame(self.match_window, bg='light gray')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Submit", command=self.submit_matches,
                font=('Arial', 12, 'bold'), bg='navy', fg='white', padx=20, pady=10
                ).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: self.back_to_user_input_with_pankti(pankti),
                font=('Arial', 12, 'bold'), bg='navy', fg='white', padx=20, pady=10
                ).pack(side=tk.LEFT, padx=5)

        print("Match window created and populated.")

    def toggle_all_meanings(self):
        """Toggle all meaning checkboxes based on the select-all checkbutton."""
        new_value = self.select_all_meanings_var.get()
        for var, meaning in self.meaning_vars:
            var.set(new_value)

    def load_grammar_data(self, file_path):
        """
        Loads grammar data from a CSV file.

        Args:
        file_path (str): The path to the CSV file containing grammar data.

        Returns:
        list: A list of dictionaries containing the grammar data.

        Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If an error occurs while reading the file.
        """
        try:
            with open(file_path, "r", encoding='utf-8') as data_base:
                return list(csv.DictReader(data_base))
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' does not exist.")
            return []
        except IOError as e:
            print(f"Error reading file '{file_path}': {e}")
            return []

    def break_into_characters(self, word):
        """Breaks a word into individual characters."""
        return [char for char in unicodedata.normalize('NFC', word)]

    def match_inflections(self, word, inflection, pos):
        """
        Determines the number of Matching Characters between the word and the inflection pattern,
        considering the part of speech. Matches are weighted by position and continuity.

        Args:
        word (str): The word to check.
        inflection (str): The inflection pattern to match against.
        pos (str): The part of speech to consider.

        Returns:
        int: The number of Matching Characters, weighted by position and continuity.
        """
        # Break the word and inflection into individual characters
        word_chars = self.break_into_characters(word)
        inflection_chars = self.break_into_characters(inflection)

        # Only consider specified endings for nouns
        if (pos == "Noun / à¨¨à¨¾à¨‚à¨µ" or pos == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£") and inflection == 'à¨®à©à¨•à¨¤à¨¾':
            return 0  # No suffix match needed for this case

        # Initialize the match count
        match_count = 0

        # Determine the minimum length between word and inflection for suffix comparison
        min_length = min(len(word_chars), len(inflection_chars))

        # Iterate through the characters in reverse order (from the end of the word and inflection)
        for i in range(1, min_length + 1):
            if word_chars[-i] == inflection_chars[-i]:
                # Increment the match count with a weight factor based on position
                match_count += i  # Giving more weight to matches that occur further back in the word
            else:
                break  # Stop the loop if a mismatch is found (ensuring continuity)

        return match_count  # Return the weighted match count

    def lookup_word_in_dictionary(self, word):
        """
        Looks up the meanings of a word in the dictionary data.

        Args:
        word (str): The word to look up in the dictionary.

        Returns:
        list: A list of meanings for the word.
        """
        meanings = []
        exact_meanings = []

        # Attempt to find the word directly in the dictionary
        result = self.dictionary_data[self.dictionary_data['Word'] == word]
        if not result.empty:
            exact_meanings = ast.literal_eval(result.iloc[0]['Meanings'])
            print(f"Found exact match for: {word}")

        # Search for the word within combined entries regardless of exact match
        combined_entries = []
        for _, row in self.dictionary_data.iterrows():
            combined_word = row['Word']
            combined_word_list = re.split(r'\s+', combined_word)  # Split by whitespace to handle combined words

            if word in combined_word_list:  # Check if the exact word is in the list of combined words
                print(f"Found exact match in combined entry: {row['Word']}")
                combined_entries.append(row)

        # If combined entries are found, proceed with adjacent word search
        adjacent_word_matches = []
        if combined_entries:
            words_in_pankti = self.accumulated_pankti.split()  # Split pankti into words
            word_index = words_in_pankti.index(word) if word in words_in_pankti else -1

            # Identify adjacent words in the pankti
            adjacent_combinations = []
            if word_index != -1:
                # Two-word combinations (main word + adjacent)
                if word_index > 0:  # Previous word
                    adjacent_combinations.append([words_in_pankti[word_index - 1], word])
                if word_index < len(words_in_pankti) - 1:  # Next word
                    adjacent_combinations.append([word, words_in_pankti[word_index + 1]])

                # Three-word combinations (main word + two adjacents)
                if word_index < len(words_in_pankti) - 2:
                    adjacent_combinations.append([words_in_pankti[word_index], words_in_pankti[word_index + 1], words_in_pankti[word_index + 2]])
                if word_index > 0 and word_index < len(words_in_pankti) - 1:
                    adjacent_combinations.append([words_in_pankti[word_index - 1], words_in_pankti[word_index], words_in_pankti[word_index + 1]])
                if word_index >= 2:
                    adjacent_combinations.append([words_in_pankti[word_index - 2], words_in_pankti[word_index - 1], words_in_pankti[word_index]])

            # Now search within combined entries using adjacent word combinations
            for entry in combined_entries:
                combined_word_list = re.split(r'\s+', entry['Word'])  # Split by whitespace to handle combined words

                for combination in adjacent_combinations:
                    # Convert the combination to possible strings to match
                    combination_strings = [' '.join(combination), ' '.join(combination[::-1])]
                    
                    if any(comb_str in entry['Word'] for comb_str in combination_strings):
                        print(f"Found adjacent match in combined entry: {entry['Word']}")
                        combined_meanings = ast.literal_eval(entry['Meanings'])
                        combined_entry = f"{entry['Word']}: {', '.join(combined_meanings)}"
                        adjacent_word_matches.append(combined_entry)

            # Sort the adjacent matches to prioritize three-word matches
            adjacent_word_matches = sorted(adjacent_word_matches, key=lambda x: len(x.split(' ')), reverse=True)

        # If both exact match and adjacent word matches are found, return adjacent first
        if adjacent_word_matches and exact_meanings:
            return adjacent_word_matches + exact_meanings

        # If only exact match is found, return exact match
        if exact_meanings:
            return exact_meanings

        # If only adjacent word matches are found, return them
        if adjacent_word_matches:
            return adjacent_word_matches

        # If no adjacent word matches are found, return original combined entries meanings
        for entry in combined_entries:
            combined_meanings = ast.literal_eval(entry['Meanings'])
            combined_entry = f"{entry['Word']}: {', '.join(combined_meanings)}"
            meanings.append(combined_entry)

        # If meanings are found, return them
        if meanings:
            return meanings

        # If no meaning is found, return a list with a single string message
        return [f"No meanings found for {word}"]

    def back_to_user_input_with_pankti(self, pankti):
        """
        Allows the user to return to the input stage for the current word, with pankti passed as an argument.
        """
        try:
            if hasattr(self, 'match_window') and self.match_window:
                self.match_window.destroy()  # Close the match window if it exists

            # Ensure the current_word_index is within valid range
            if 0 <= self.current_word_index < len(self.pankti_words):
                word = self.pankti_words[self.current_word_index]  # Get the current word
                self.reset_input_variables()  # Reset selections for the new word
                self.user_input(word, pankti)  # Reopen the input window for the current word and pass pankti
            else:
                messagebox.showerror("Error", "No valid word to return to.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def fetch_data(self, word, pankti):
        try:
            self.reset_input_variables()  # Reset selections for the new word
            print(f"Opening input window for {word}")

            self.user_input(word, pankti)  # Opens the input window with the Pankti

            # Check if input_window exists before waiting
            if hasattr(self, 'input_window') and self.input_window.winfo_exists():
                self.root.wait_window(self.input_window)  # Wait for the input window to close
            else:
                print(f"Input window for {word} did not open properly.")
                return  # Exit if the input window was not opened

            print(f"Input window for {word} closed")

            if not self.input_submitted:
                print(f"No input submitted for {word}. Skipping to next word.")
                self.current_word_index += 1
                self.process_next_word()
            else:
                # Process the submitted input
                self.handle_submitted_input(word)

        except Exception as e:
            print(f"An error occurred while fetching data for {word}: {str(e)}")
            # Ensure the input window is closed in case of an error
            if hasattr(self, 'input_window') and self.input_window.winfo_exists():
                try:
                    self.input_window.destroy()
                except Exception as close_error:
                    print(f"Failed to close input window: {str(close_error)}")
            # Optionally, log the error to a file for future debugging
            with open("error_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"Error with word '{word}': {str(e)}\n")

    def process_next_word(self):
        """Process the next valid word or prompt for saving if finished."""
        pankti = " ".join(self.pankti_words)
        self.current_pankti = pankti

        if self.current_word_index < len(self.pankti_words):
            word = self.pankti_words[self.current_word_index]
            if self.is_non_word_character(word):
                self.current_word_index += 1  # Skip non-word characters
                self.process_next_word()
            else:
                self.fetch_data(word, pankti)  # Process current word
        else:
            # All words processedâ€”prompt to save using the global accumulator
            self.save_results_btn.config(state=tk.NORMAL)
            self.prompt_save_results(self.all_new_entries)

    def skip_input(self):
        """
        Handles the action when the user decides to skip the current word.
        """
        try:
            # Ask for user confirmation before skipping
            confirm_skip = messagebox.askyesno("Confirm Skip", "Are you sure you want to skip this word?")
            if not confirm_skip:
                return  # Do nothing if the user cancels the skip

            # Mark input as not submitted and close the input window
            self.input_submitted = False
            self.input_window.destroy()

            # Update the index to move to the next word and process it
            self.current_word_index += 1
            self.process_next_word()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while skipping: {e}")

    def submit_input(self):
        self.input_submitted = True
        if hasattr(self, 'input_window') and self.input_window.winfo_exists():
            self.input_window.destroy()

        # Start the progress bar
        self.start_progress()

        # Run the search in a separate thread
        search_thread = threading.Thread(target=self.perform_search_and_finish)
        search_thread.start()

    def perform_search_and_finish(self):
        current_word = self.pankti_words[self.current_word_index]
        number = self.number_var.get()
        gender = self.gender_var.get()
        pos = self.pos_var.get()

        print(f"Processing word: {current_word}, Number: {number}, Gender: {gender}, POS: {pos}")
        
        matches = []
        
        if number == "NA" and gender == "NA" and pos == "NA":
            matches = self.search_by_inflections(current_word)
        else:
            matches = self.search_by_criteria(current_word, number, gender, pos)
            if not matches:
                messagebox.showinfo("No Matches Found", "No matches were found as per the criteria given by you. Now conducting a general search.")
                matches = self.search_by_inflections(current_word)

        # Check if meanings are already accumulated for the current word index
        if len(self.accumulated_meanings) > self.current_word_index:
            entry = self.accumulated_meanings[self.current_word_index]
            # If the entry is a dictionary, extract the meanings list; otherwise assume it's already a list.
            if isinstance(entry, dict):
                meanings = entry.get("meanings", [])
            else:
                meanings = entry
            self.handle_lookup_results(matches, meanings)
        else:
            # Launch the dictionary lookup in a separate thread if no meanings are accumulated.
            self.perform_dictionary_lookup(current_word, lambda meanings: self.handle_lookup_results(matches, meanings))

        # Stop the progress bar once done (use Tkinter's `after` to ensure it runs in the main thread)
        self.root.after(0, self.stop_progress)

        if matches:
            print(f"Found matches for {current_word}: {matches}")
            # Ensure current_pankti and meanings are passed to show_matches
            self.root.after(0, lambda: self.show_matches(matches, self.current_pankti, meanings))
        else:
            self.root.after(0, lambda: messagebox.showinfo("No Matches", f"No matches found for the word: {current_word}"))
            self.current_word_index += 1
            self.root.after(0, self.process_next_word)

    def is_non_word_character(self, word):
        """
        Determines if the given word consists solely of non-word characters.

        Args:
        word (str): The word to be checked.

        Returns:
        bool: True if the word consists only of non-word characters; False otherwise.
        """
        # Regular expression pattern to match non-word characters and digits
        pattern = r"^[^\w\s]*[\dà¥¥]+[^\w\s]*$"

        # Check if the word matches the pattern
        return re.match(pattern, word) is not None

    def search_by_criteria(self, word, number, gender, pos):
        matches = []
        seen = set()  # To store unique combinations

        # Part of Speech: Noun, Verb
        if pos in ["Noun / à¨¨à¨¾à¨‚à¨µ", "Verb / à¨•à¨¿à¨°à¨¿à¨†"]:
            specified_endings = [
                "à©Œ", "à©‹", "à©ˆ", "à©‡", "à©‚", "à©", "à©€à¨¹à©‹", "à©€à¨¹à©‚", "à©€à¨", "à©€à¨ˆà¨‚", "à©€à¨ˆ",
                "à©€à¨†", "à©€à¨…à©ˆ", "à©€à¨…à¨¹à©", "à©€à¨“", "à©€à¨‚", "à©€", "à¨¿à¨¨", "à¨¿à¨¹à©‹", "à¨¿à¨ˆà¨‚", "à¨¿à¨†à¨‚",
                "à¨¿à¨†", "à¨¿à¨…à¨¨", "à¨¿à¨…à¨¹à©", "à¨¿", "à¨¾à¨°à©‚", "à¨¾à¨¹à©", "à¨¾à¨¹à¨¿", "à¨¾à¨‚", "à¨¾", "à¨¹à¨¿",
                "à¨¸à©ˆ", "à¨¸", "à¨ˆà¨¦à¨¿", "à¨ˆ", "à¨‰", "à¨¹à¨¿à¨‰", "à¨—à¨¾", "à¨†", "à¨‡"
            ]

            # Determine if the word is truly inflectionless
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)

            # Iterate through each rule in the grammar data
            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / à¨µà¨šà¨¨']
                current_gender = gender if gender != "NA" else rule['Gender / à¨²à¨¿à©°à¨—']
                current_pos = pos if pos != "NA" else rule['Type']

                # Handle the 'à¨®à©à¨•à¨¤à¨¾' case
                include_mukta = is_inflectionless and current_pos == "Noun / à¨¨à¨¾à¨‚à¨µ"

                if include_mukta and rule['\ufeffVowel Ending'] == "à¨®à©à¨•à¨¤à¨¾" and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                elif not include_mukta and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == current_pos:
                    # Regular inflection matching
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / à¨µà¨šà¨¨', ""),
                                rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                                rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))

        # Part of Speech: Adjective (Always perform both searches)
        elif pos == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£":
            specified_endings = [
                "à©Œ", "à©‹", "à©ˆ", "à©‡", "à©‚", "à©", "à©€à¨¹à©‹", "à©€à¨¹à©‚", "à©€à¨", "à©€à¨ˆà¨‚", "à©€à¨ˆ",
                "à©€à¨†", "à©€à¨…à©ˆ", "à©€à¨…à¨¹à©", "à©€à¨“", "à©€à¨‚", "à©€", "à¨¿à¨¨", "à¨¿à¨¹à©‹", "à¨¿à¨ˆà¨‚", "à¨¿à¨†à¨‚",
                "à¨¿à¨†", "à¨¿à¨…à¨¨", "à¨¿à¨…à¨¹à©", "à¨¿", "à¨¾à¨°à©‚", "à¨¾à¨¹à©", "à¨¾à¨¹à¨¿", "à¨¾à¨‚", "à¨¾", "à¨¹à¨¿",
                "à¨¸à©ˆ", "à¨¸", "à¨ˆà¨¦à¨¿", "à¨ˆ", "à¨‰", "à¨¹à¨¿à¨‰", "à¨—à¨¾", "à¨†", "à¨‡"
            ]

            # Determine if the word is truly inflectionless
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)

            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / à¨µà¨šà¨¨']
                current_gender = gender if gender != "NA" else rule['Gender / à¨²à¨¿à©°à¨—']
                current_pos = pos if pos != "NA" else rule['Type']

                # Handle the 'à¨®à©à¨•à¨¤à¨¾' case
                include_mukta = is_inflectionless and current_pos == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£"

                # Handle inflections (like Nouns)
                if include_mukta and rule['\ufeffVowel Ending'] == "à¨®à©à¨•à¨¤à¨¾" and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                elif not include_mukta and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == current_pos:
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / à¨µà¨šà¨¨', ""),
                                rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                                rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))

                # Also check for exact matches (like Pronouns)
                if word in rule['\ufeffVowel Ending'] and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Part of Speech: Pronoun
        elif pos == "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ":
            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / à¨µà¨šà¨¨']
                current_gender = gender if gender != "NA" else rule['Gender / à¨²à¨¿à©°à¨—']

                if word in rule['\ufeffVowel Ending'] and rule['Number / à¨µà¨šà¨¨'] == current_number and rule['Gender / à¨²à¨¿à©°à¨—'] == current_gender and rule['Type'] == pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Part of Speech: Adverb, Postposition, Conjunction
        elif pos in ["Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£", "Postposition / à¨¸à©°à¨¬à©°à¨§à¨•", "Conjunction / à¨¯à©‹à¨œà¨•", "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•"]:
            for rule in self.grammar_data:
                if word in rule['\ufeffVowel Ending'] and rule['Type'] == pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Use filter_unique_matches to remove duplicates and sort the results
        unique_sorted_matches = self.filter_unique_matches(matches)

        return unique_sorted_matches

    def search_by_inflections(self, word):
        """
        Searches for inflection matches for the given word within the grammar data.

        Args:
        word (str): The word to search for inflections.

        Returns:
        list: A list of tuples representing matched grammatical rules for the word,
            along with match count and match percentage.
        """
        matches = []
        seen = set()  # To store unique combinations

        # Define the specified endings for inflectionless check
        specified_endings = [
            "à©Œ", "à©‹", "à©ˆ", "à©‡", "à©‚", "à©", "à©€à¨¹à©‹", "à©€à¨¹à©‚", "à©€à¨", "à©€à¨ˆà¨‚", "à©€à¨ˆ",
            "à©€à¨†", "à©€à¨…à©ˆ", "à©€à¨…à¨¹à©", "à©€à¨“", "à©€à¨‚", "à©€", "à¨¿à¨¨", "à¨¿à¨¹à©‹", "à¨¿à¨ˆà¨‚", "à¨¿à¨†à¨‚",
            "à¨¿à¨†", "à¨¿à¨…à¨¨", "à¨¿à¨…à¨¹à©", "à¨¿", "à¨¾à¨°à©‚", "à¨¾à¨¹à©", "à¨¾à¨¹à¨¿", "à¨¾à¨‚", "à¨¾", "à¨¹à¨¿",
            "à¨¸à©ˆ", "à¨¸", "à¨ˆà¨¦à¨¿", "à¨ˆ", "à¨‰", "à¨“", "à¨¹à¨¿à¨‰", "à¨—à¨¾", "à¨†", "à¨‡"
        ]

        # Determine if the word is truly inflectionless
        try:
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)
        except Exception as e:
            print(f"Error determining if the word '{word}' is inflectionless: {str(e)}")
            is_inflectionless = False  # Default to False if there's an error

        for rule in self.grammar_data:
            rule_pos = rule['Type']

            # Noun, Adjective, and Verb processing
            if rule_pos in ["Noun / à¨¨à¨¾à¨‚à¨µ", "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£", "Verb / à¨•à¨¿à¨°à¨¿à¨†"]:
                include_mukta = is_inflectionless and (rule_pos == "Noun / à¨¨à¨¾à¨‚à¨µ" or rule_pos == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£")

                if include_mukta and rule['\ufeffVowel Ending'] == "à¨®à©à¨•à¨¤à¨¾":
                    # Handle the 'à¨®à©à¨•à¨¤à¨¾' case
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                else:
                    # Regular inflection matching
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / à¨µà¨šà¨¨', ""),
                                rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                                rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))
                    # Hybrid handling for Adjectives
                    if rule_pos == "Adjectives / à¨µà¨¿à¨¶à©‡à¨¶à¨£" and word in rule['\ufeffVowel Ending']:
                        result = " | ".join([
                            word,
                            rule.get('\ufeffVowel Ending', ""),
                            rule.get('Number / à¨µà¨šà¨¨', ""),
                            rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                            rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                            rule.get('Word Root', ""),
                            rule.get('Type', "")
                        ])
                        match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                        matches.append((result, match_count, match_percentage))

            # Pronoun processing
            elif rule_pos == "Pronoun / à¨ªà©œà¨¨à¨¾à¨‚à¨µ":
                if word in rule['\ufeffVowel Ending']:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

            # Adverb, Postposition, and Conjunction processing
            elif rule_pos in ["Adverb / à¨•à¨¿à¨°à¨¿à¨† à¨µà¨¿à¨¸à©‡à¨¶à¨£", "Postposition / à¨¸à©°à¨¬à©°à¨§à¨•", "Conjunction / à¨¯à©‹à¨œà¨•", "Interjection / à¨µà¨¿à¨¸à¨®à¨¿à¨•"]:
                if word in rule['\ufeffVowel Ending']:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / à¨µà¨šà¨¨', ""),
                        rule.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', ""),
                        rule.get('Gender / à¨²à¨¿à©°à¨—', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Use filter_unique_matches to remove duplicates and sort the results
        unique_sorted_matches = self.filter_unique_matches(matches)

        return unique_sorted_matches

    def analyze_pankti(self):
        """
        1) Get userâ€™s typed verse/pankti.
        2) Fuzzy-match it against SGGS data.
        3) Show radio buttons for each match so user can select exactly one.
        """
        user_input = self.pankti_entry.get().strip()
        if not user_input:
            messagebox.showerror("Error", "Please enter some text to analyze.")
            return

        # 1) Fuzzy-match the verse in SGGS data (example function)
        candidate_matches = self.match_sggs_verse(user_input)
        if not candidate_matches:
            messagebox.showinfo("No SGGS Match", "No matching verses found in SGGS. Continuing with grammar analysis.")
            # If you still want to do grammar analysis with the typed input:
            self.finish_grammar_analysis(user_input)
            return
        else:
            # Show a new window with radio buttons
            self.show_sggs_matches_option(candidate_matches, user_input)

    def load_sggs_data(self):
        """
        Loads the SGGS data from an Excel file while displaying a modal progress bar.
        The main window is disabled (to prevent user interaction) while the heavy work runs in a background thread.
        The main thread enters a loop to update the UI (so the progress bar animates) until the data is loaded.
        """
        # Disable the main window to prevent interaction
        self.root.attributes("-disabled", True)

        # Show the progress bar modally on the main thread
        self.start_progress()
        self.root.update()  # Ensure the progress window appears immediately

        # This flag will be set when loading is complete.
        self.loading_done = False

        import threading

        def heavy_work():
            # Perform the heavy work (reading and processing the Excel file)
            data = pd.read_excel("1.1.3 sggs_extracted_with_page_numbers.xlsx")
            headers = list(data.columns)
            data['NormalizedVerse'] = (
                data['Verse']
                .astype(str)
                .str.lower()
                .str.strip()
            )
            # Schedule the finalization on the main thread.
            def finish():
                self.sggs_data = data
                self.sggs_headers = headers
                self.loading_done = True
            self.root.after(0, finish)

        # Run the heavy work in a background thread
        threading.Thread(target=heavy_work, daemon=True).start()

        # Process the event loop until loading is done (this allows the progress bar to animate)
        while not self.loading_done:
            self.root.update_idletasks()
            self.root.update()

        # Re-enable the main window now that the heavy work is complete
        self.root.attributes("-disabled", False)
        self.stop_progress()

    def match_sggs_verse(self, user_input, max_results=10, min_score=25):
        """
        Fuzzy-match the user's input (pankti) against the SGGS 'Verse' column.
        Return a tuple (headers, candidate_matches) where headers is the list
        of all column names from the Excel file, and candidate_matches is a list
        (up to max_results) of best matches above the min_score similarity.
        """
        # Ensure we have loaded the data and headers
        if not hasattr(self, 'sggs_data'):
            self.load_sggs_data()
        
        headers = self.sggs_headers
        normalized_input = user_input.lower().strip()
        candidate_matches = []

        # Disable the main window to block user interaction during matching
        self.root.attributes("-disabled", True)
        # Start the modal progress bar
        self.start_progress()
        self.root.update()  # Ensure progress window appears

        total_rows = len(self.sggs_data)
        # Iterate over the rows in SGGS data
        for i, (_, row) in enumerate(self.sggs_data.iterrows()):
            verse_text = row['NormalizedVerse']
            # Remove extra spaces around numbers within "à¥¥" markers
            verse_text = re.sub(r'à¥¥\s*(\d+)\s*à¥¥', r'à¥¥\1à¥¥', verse_text)
            score = fuzz.token_sort_ratio(normalized_input, verse_text)
            if score >= min_score:
                candidate_matches.append({
                    'S. No.': row['S. No.'],
                    'Verse': row['Verse'],
                    'Verse No.': row.get('Verse No.'),
                    'Stanza No.': row['Stanza No.'],
                    'Text Set No.': row.get('Text Set No.'),
                    'Raag (Fixed)': row['Raag (Fixed)'],
                    'Sub-Raag': row.get('Sub-Raag'),
                    'Writer (Fixed)': row['Writer (Fixed)'],
                    'Verse Configuration (Optional)': row.get('Verse Configuration (Optional)'),
                    'Stanza Configuration (Optional)': row.get('Stanza Configuration (Optional)'),
                    'Bani Name': row['Bani Name'],
                    'Musical Note Configuration': row.get('Musical Note Configuration'),
                    'Special Type Demonstrator': row.get('Special Type Demonstrator'),
                    'Type': row.get('Type'),
                    'Page Number': row['Page Number'],
                    'Score': score
                })
            if i % 50 == 0:
                self.root.update_idletasks()
                self.root.update()

        # Sort the candidate matches by descending score and select the top results.
        candidate_matches.sort(key=lambda x: x['Score'], reverse=True)

        # Stop the progress bar and re-enable the main window.
        self.stop_progress()
        self.root.attributes("-disabled", False)

        return headers, candidate_matches[:max_results]

    def show_sggs_matches_option(self, candidate_matches, user_input):
        """
        Display fuzzy SGGS matches as radio buttons so the user can choose one.
        The header will also include the user input verse.
        """

        # 1) If the first item is a header list, strip it off:
        if candidate_matches and isinstance(candidate_matches[0], list):
            # This is presumably the header row
            self.header_row = candidate_matches[0]
            # If there's a second element and it's a list of dicts, use that
            if len(candidate_matches) > 1 and isinstance(candidate_matches[1], list):
                candidate_matches = candidate_matches[1]
            else:
                # No real data after the header
                candidate_matches = []

        # 2) Store matches for later reference
        self.candidate_matches = candidate_matches

        # 3) Destroy if there's an existing option window
        if hasattr(self, 'sggs_option_window') and self.sggs_option_window.winfo_exists():
            self.sggs_option_window.destroy()

        # 4) Create a new Toplevel window
        self.sggs_option_window = tk.Toplevel(self.root)
        self.sggs_option_window.title("Select One Matching Verse")
        self.sggs_option_window.configure(bg='light gray')
        self.sggs_option_window.state("zoomed")

        # 5) A Tk variable that holds the index of the selected match
        self.sggs_option_var = tk.IntVar(value=-1)  # -1 = nothing selected

        # 6) Header label
        header_label = tk.Label(
            self.sggs_option_window,
            text=f"Fuzzy Matches Found for '{user_input}'. Please select one:",
            bg='dark slate gray',
            fg='white',
            font=('Arial', 16, 'bold'),
            pady=10
        )
        header_label.pack(fill=tk.X)

        # 7) Scrollable 2-column cards layout (visual parity with _populate_cards)
        middle = tk.Frame(self.sggs_option_window, bg='light gray')
        middle.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(middle, bg='light gray', highlightthickness=0)
        vsb    = tk.Scrollbar(middle, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        cards_frame = tk.Frame(canvas, bg='light gray')
        cards_window = canvas.create_window((0, 0), window=cards_frame, anchor="n")

        # two equal-width columns
        # Enforce equal column widths using a uniform group
        try:
            cards_frame.grid_columnconfigure(0, weight=1, minsize=450, uniform='cards')
            cards_frame.grid_columnconfigure(1, weight=1, minsize=450, uniform='cards')
        except Exception:
            cards_frame.grid_columnconfigure(0, weight=1, minsize=450)
            cards_frame.grid_columnconfigure(1, weight=1, minsize=450)

        def _on_cards_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        cards_frame.bind("<Configure>", _on_cards_configure)

        def _on_canvas_resize(event):
            # Keep the cards frame horizontally centered within the visible canvas
            canvas.coords(cards_window, event.width // 2, 0)
            # Optionally make the window at least as wide as the canvas to avoid left-hugging
            try:
                canvas.itemconfigure(cards_window, width=event.width)
            except Exception:
                pass
        canvas.bind("<Configure>", _on_canvas_resize)

        # Ensure initial centering after first layout
        canvas.update_idletasks()
        try:
            canvas.coords(cards_window, canvas.winfo_width() // 2, 0)
            canvas.itemconfigure(cards_window, width=canvas.winfo_width())
        except Exception:
            pass

        # 8) Populate cards mirroring _populate_cards, but keep selection via radio buttons
        total_cards = len(candidate_matches)
        for idx, match in enumerate(candidate_matches):
            # Normalize match into a dict-like mapping
            if isinstance(match, dict):
                m = match
            else:
                # Fallback mapping for list/tuple structures (preserve prior behavior)
                score_val = match[7] if len(match) > 7 else '?'
                verse_val = match[1] if len(match) > 1 else ''
                raag_val  = match[2] if len(match) > 2 else ''
                writer_val= match[3] if len(match) > 3 else ''
                bani_val  = match[4] if len(match) > 4 else ''
                page_val  = match[5] if len(match) > 5 else ''
                m = {
                    'Score': score_val,
                    'Verse': verse_val,
                    'Raag (Fixed)': raag_val,
                    'Writer (Fixed)': writer_val,
                    'Bani Name': bani_val,
                    'Page Number': page_val,
                }

            # Build each card
            row, col = divmod(idx, 2)
            card = tk.Frame(
                cards_frame,
                bd=1,
                relief="solid",
                bg="white",
                padx=8,
                pady=8
            )
            # If odd number of cards and this is the last one, span both columns for visual centering
            if (total_cards % 2 == 1) and (idx == total_cards - 1):
                card.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
            else:
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Verse label
            tk.Label(
                card,
                text=str(m.get("Verse", "")).strip(),
                font=("Arial", 14, "bold"),
                wraplength=500,
                justify="center",
                bg="white"
            ).pack(pady=(14,4), padx=(28,8))

            # Radio button at top-left for selection (placed after verse to ensure on top)
            rb = tk.Radiobutton(
                card,
                variable=self.sggs_option_var,
                value=idx,
                bg="white",
                activebackground="white",
                selectcolor='light blue'
            )
            rb.place(x=6, y=6)
            try:
                rb.lift()
            except Exception:
                pass

            # Metadata line (Raag, Writer, Bani, Page) + Match%
            fields = [
                ("Raag",   "Raag (Fixed)"),
                ("Writer", "Writer (Fixed)"),
                ("Bani",   "Bani Name"),
                ("Page",   "Page Number"),
            ]
            meta_parts = []
            for label, key in fields:
                v = m.get(key)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    continue
                if str(v).lower() == 'nan':
                    continue
                meta_parts.append(f"{label}: {v}")

            # score formatting
            try:
                score_val = float(m.get('Score', 0))
            except Exception:
                score_val = 0.0
            meta_parts.append(f"Match: {score_val:.1f}%")

            tk.Label(
                card,
                text="   |   ".join(meta_parts),
                font=("Arial", 12),
                bg="white"
            ).pack()

        # Ensure scrollregion correct
        cards_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # 9) Buttons
        btn_frame = tk.Frame(self.sggs_option_window, bg='light gray')
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Submit",
            command=self.handle_sggs_option_submit,
            font=('Arial', 12, 'bold'), bg='navy', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="Cancel",
            command=self.sggs_option_window.destroy,
            font=('Arial', 12, 'bold'), bg='red', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)

        print("Match window created and populated.")

    def handle_sggs_option_submit(self):
        idx = self.sggs_option_var.get()
        if idx < 0:
            messagebox.showwarning("No Selection", "Please select one verse match.")
            return

        chosen_match = self.candidate_matches[idx]
        final_input = chosen_match.get('Verse', '')

        if not final_input.strip():
            messagebox.showerror("Error", "The selected verse text is empty. Cannot proceed.")
            return

        # Optionally close the first match window
        self.sggs_option_window.destroy()

        # Now, show the consecutive lines selection
        self.show_consecutive_verses_option(chosen_match, final_input)

    def show_consecutive_verses_option(self, chosen_match, main_verse_text):
        """
        After the user picks the main verse from fuzzy matches,
        let them select additional consecutive lines from the same stanza or text set.
        Ensure the main verse is highlighted and only consecutive verses can be selected.
        """
        # 1) Query your data to find consecutive lines
        stanza_lines = self.fetch_stanza_lines(chosen_match)
        self.chosen_match = stanza_lines
        if not stanza_lines:
            messagebox.showinfo("No Consecutive Lines", "No additional consecutive verses found. Proceeding.")
            self.finish_grammar_analysis(main_verse_text)
            return

        # 2) Store the main user input so that we can return to SGGS matches later.
        self.last_user_input = main_verse_text

        # 3) Create a window to show these lines as checkboxes
        self.consecutive_window = tk.Toplevel(self.root)
        self.consecutive_window.title("Select Consecutive Verses")
        self.consecutive_window.configure(bg='light gray')
        self.consecutive_window.state('zoomed')

        # Adjust header text based on the stored user's choice.
        if hasattr(self, 'verses_choice') and self.verses_choice:
            header_text = f"Select Additional Lines from the '{chosen_match['Special Type Demonstrator']}'"
        else:
            header_text = "Select Additional Lines from the Stanza"

        header_label = tk.Label(
            self.consecutive_window,
            text=header_text,
            bg='dark slate gray',
            fg='white',
            font=('Arial', 16, 'bold'),
            pady=10
        )
        header_label.pack(fill=tk.X)

        frame = tk.Frame(self.consecutive_window, bg='light gray')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(frame, bg='light gray', borderwidth=0)
        vsb = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='light gray')

        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # Populate with checkboxes for each consecutive line.
        # Highlight the main verse (pre-selected and disabled) and add normal checkboxes for others.
        self.stanza_checkvars = []
        for idx, line_info in enumerate(stanza_lines):
            line_text = line_info.get('Verse', '')
            if line_text.strip() == main_verse_text.strip():
                # Highlight the main verse
                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(
                    scroll_frame,
                    text=line_text,
                    variable=var,
                    bg='yellow',           # highlight color
                    font=('Arial', 12, 'bold'),
                    anchor='w',
                    justify=tk.LEFT,
                    wraplength=800,
                    state='disabled',      # force it to remain selected
                    selectcolor='light blue'
                )
            else:
                var = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    scroll_frame,
                    text=line_text,
                    variable=var,
                    bg='light gray',
                    font=('Arial', 12),
                    anchor='w',
                    justify=tk.LEFT,
                    wraplength=800,
                    selectcolor='light blue'
                )
            chk.pack(fill=tk.X, padx=10, pady=5)
            self.stanza_checkvars.append((var, line_text))

        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # ---------------------------
        # Button Frame: Submit, Cancel, and Back
        # ---------------------------
        btn_frame = tk.Frame(self.consecutive_window, bg='light gray')
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Submit",
            command=lambda: self.validate_and_submit_consecutive(main_verse_text),
            font=('Arial', 12, 'bold'),
            bg='navy',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.consecutive_window.destroy,
            font=('Arial', 12, 'bold'),
            bg='red',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back",
            command=self.back_to_sggs_matches_option,
            font=('Arial', 12, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        print("Consecutive verses window created and populated.")

    def validate_and_submit_consecutive(self, main_verse_text):
        """
        Validate that the selected verses form a consecutive block that includes the main verse.
        If valid, proceed with handling the submission.
        """
        # Get indices of all selected verses
        selected_indices = [i for i, (var, _) in enumerate(self.stanza_checkvars) if var.get()]
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please ensure at least the main verse is selected.")
            return

        # Find the index of the main verse (which should be pre-selected)
        main_indices = [i for i, (_, line_text) in enumerate(self.stanza_checkvars)
                        if line_text.strip() == main_verse_text.strip()]
        if not main_indices:
            messagebox.showerror("Error", "Main verse not found in the list.")
            return
        main_index = main_indices[0]

        # Check if the selected indices form a consecutive block.
        if max(selected_indices) - min(selected_indices) != len(selected_indices) - 1:
            messagebox.showerror("Non-Consecutive Selection", "Please select only consecutive verses.")
            return

        # Ensure the consecutive block includes the main verse.
        if main_index < min(selected_indices) or main_index > max(selected_indices):
            messagebox.showerror("Selection Error", "The selected consecutive block must include the main verse.")
            return

        # If validation passes, proceed with the submission.
        self.handle_consecutive_submit(main_verse_text)

    def back_to_sggs_matches_option(self):
        """
        Close the consecutive verses window and re-display the SGGS matches option window.
        """
        self.consecutive_window.destroy()
        # Re-open the SGGS matches option window using the stored candidate matches and user input.
        self.show_sggs_matches_option(self.candidate_matches, self.last_user_input)

    def handle_consecutive_submit(self, main_verse_text):
        """
        Combine the main verse text with the lines selected by the user,
        then proceed with grammar analysis. Ensures that the main verse is
        not duplicated if it was also selected by the user.
        Also, store the individual selected verses in self.selected_verses 
        (as a list of tuples: (start_index, end_index, verse_text)) for later use.
        """
        # Strip the main verse text
        main_line = main_verse_text.strip()

        # Gather the lines that were checked; strip extra whitespace
        selected_lines = [line.strip() for var, line in self.stanza_checkvars if var.get()]

        # Store each selected line as an individual verse in self.selected_verses.
        self.selected_verses = list(selected_lines)

        # Keep only matches where the verse is in self.selected_verses.
        self.chosen_match = [match for match in self.chosen_match if match['Verse'] in self.selected_verses]

        # Filter out any line that is exactly the same as the main verse
        extra_lines = [line for line in selected_lines if line != main_line]

        # Combine all selected lines (including the main verse, already in correct order) into a single string,
        # ensuring the original sequence of the verse is maintained.
        if extra_lines:
            combined_text = " ".join(selected_lines)
        else:
            combined_text = main_line
        
        # Close the consecutive window
        self.consecutive_window.destroy()

        # Proceed with grammar analysis using the combined text
        self.finish_grammar_analysis(combined_text)

    def fetch_stanza_lines(self, chosen_match):
        """
        Return a list of dictionaries representing consecutive lines from either the current stanza or the entire text set,
        based on the user's choice.
        This function uses the SGGS data loaded by load_sggs_data() (stored in self.sggs_data).
        """
        # Ensure the SGGS data is loaded
        if not hasattr(self, 'sggs_data'):
            self.load_sggs_data()

        # Retrieve the Stanza No. and Text Set No. from the chosen match.
        stanza_no = chosen_match.get('Stanza No.')
        text_set_no = chosen_match.get('Text Set No.')

        if stanza_no is None or text_set_no is None:
            print("Chosen match does not contain required 'Stanza No.' or 'Text Set No.' information.")
            return []

        # Get the Special Type Demonstrator value.
        special_type = chosen_match.get('Special Type Demonstrator', '')

        # If it's 'à¨¶à¨²à©‹à¨•', then we don't ask the user because a à¨¶à¨²à©‹à¨• is always a stanza.
        if special_type == 'à¨¶à¨²à©‹à¨•':
            choice = False
        else:
            choice = messagebox.askyesno(
                "Select Verses",
                f"Do you want to fetch verses from the entire '{special_type}'?\n\n"
                f"(Yes = Entire '{special_type}', No = Only the current Stanza)"
            )
        # Store the user's choice for later use
        self.verses_choice = choice

        if choice:
            # User selected the entire text set.
            subset = self.sggs_data[self.sggs_data['Text Set No.'] == text_set_no]
        else:
            # User selected only the current stanza.
            subset = self.sggs_data[
                (self.sggs_data['Stanza No.'] == stanza_no) &
                (self.sggs_data['Text Set No.'] == text_set_no)
            ]

        # Optionally sort by 'Verse No.' if available
        if 'Verse No.' in subset.columns:
            subset = subset.sort_values(by='Verse No.')

        lines = subset.to_dict(orient='records')

        return lines

    def finish_grammar_analysis(self, user_input):
        """
        Runs grammar analysis after the user has selected or typed a final verse.
        """
        self._repeat_note_shown = set()
        self._suppress_repeat_notes_for_verse = False
        self.pankti_words = user_input.split()
        self.accumulate_pankti_data(user_input)
        self.current_word_index = 0
        self.all_new_entries = []  # Reset global accumulator

        self.update_navigation_buttons()
        self.process_next_word()

    def prompt_for_assessment(self, metadata_entry):
        """
        Opens a modal window that lets the user paste the analysis result (translation)
        and choose options for 'Framework?' and 'Explicit?'.
        The metadata_entry is a dictionary containing the existing metadata (e.g., Word, Vowel Ending, etc.).
        """
        assessment_win = tk.Toplevel(self.root)
        assessment_win.title("Enter Translation Assessment")
        assessment_win.configure(bg='light gray')

        instruction_label = tk.Label(assessment_win, 
                                    text="Paste the analysis result below:",
                                    font=("Helvetica", 14), bg="light gray")
        instruction_label.pack(pady=10)

        analysis_text = scrolledtext.ScrolledText(assessment_win, width=80, height=10,
                                                font=("Helvetica", 12), wrap=tk.WORD)
        analysis_text.pack(padx=20, pady=10)

        cb_frame = tk.Frame(assessment_win, bg="light gray")
        cb_frame.pack(pady=10)

        framework_var = tk.BooleanVar()
        explicit_var = tk.BooleanVar()

        framework_cb = tk.Checkbutton(cb_frame, text="Framework?", variable=framework_var,
                                    font=("Helvetica", 12), bg="light gray")
        framework_cb.pack(side=tk.LEFT, padx=10)

        explicit_cb = tk.Checkbutton(cb_frame, text="Explicit?", variable=explicit_var,
                                    font=("Helvetica", 12), bg="light gray")
        explicit_cb.pack(side=tk.LEFT, padx=10)

        def on_save():
            translation = analysis_text.get("1.0", tk.END).strip()
            if not translation:
                messagebox.showerror("Error", "Please paste the analysis result.")
                return
            # Merge the metadata with the new assessment data
            new_entry = metadata_entry.copy()
            new_entry["\ufeffVowel Ending"] = self._norm_get(new_entry, "\ufeffVowel Ending")
            new_entry.pop("Vowel Ending", None)
            new_entry["Type"] = self._norm_get(new_entry, "Type")
            new_entry.pop("Word Type", None)
            new_entry["Translation"] = translation
            new_entry["Framework?"] = framework_var.get()
            new_entry["Explicit?"] = explicit_var.get()
            # Revision is computed in save_assessment_data
            self.save_assessment_data(new_entry)
            assessment_win.destroy()

        save_btn = tk.Button(assessment_win, text="Save Assessment",
                            command=on_save, font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        assessment_win.transient(self.root)
        assessment_win.grab_set()
        self.root.wait_window(assessment_win)

    def load_existing_assessment_data(self, file_path):
        expected_columns = [
            "Verse", "Translation", "Translation Revision",
            "Word", "Selected Darpan Meaning", "\ufeffVowel Ending", "Number / à¨µà¨šà¨¨", "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£", "Gender / à¨²à¨¿à©°à¨—", "Word Root", "Type", "Grammar Revision", "Word Index",
            "S. No.", "Verse No.", "Stanza No.", "Text Set No.", "Raag (Fixed)", "Sub-Raag", "Writer (Fixed)",
            "Verse Configuration (Optional)", "Stanza Configuration (Optional)", "Bani Name", "Musical Note Configuration",
            "Special Type Demonstrator", "Verse Type", "Page Number",
            "Framework?", "Explicit?"
        ]
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                df.rename(columns={"Vowel Ending": "\ufeffVowel Ending", "Word Type": "Type"}, inplace=True)
                if df.empty or len(df.columns) == 0:
                    df = pd.DataFrame(columns=expected_columns)
                else:
                    # Ensure the DataFrame has exactly the expected columns.
                    df = df.reindex(columns=expected_columns)
                return df
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return pd.DataFrame(columns=expected_columns)

    def save_assessment_data(self, new_entry):
        """
        Saves a new assessment entry to an Excel file with the following behavior:
        - For a given verse, update the "Translation" field for all entries.
        - For the specific word being assessed in that verse, group all matching rows.
        - If any grammar field differs from the new entry, increment the Grammar Revision once for the group
            and update all matching rows with the new grammar details.
        - Update "Selected Darpan Meaning" for the specific word occurrence.
        - If any word's grammar is revised in the verse, increment the "Translation Revision" for all words of that verse.
        - If no matching entry exists for the word in that verse, append the new entry with a Grammar Revision of 1,
            and initialize the Translation Revision.
        """
        file_path = "1.2.1 assessment_data.xlsx"
        df_existing = self.load_existing_assessment_data(file_path)
        
        # Define the grammar keys to compare (excluding Translation, which is updated separately).
        grammar_keys = [
            '\ufeffVowel Ending', 'Number / à¨µà¨šà¨¨', 'Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£',
            'Gender / à¨²à¨¿à©°à¨—', 'Word Root', 'Type'
        ]
        
        # Update the Translation for all rows in the same verse.
        df_existing.loc[df_existing["Verse"] == new_entry["Verse"], "Translation"] = new_entry["Translation"]
        
        # Filter for rows with the same word, same verse, and same word index.
        matching_rows = df_existing[
            (df_existing["Word"] == new_entry["Word"]) &
            (df_existing["Verse"] == new_entry["Verse"]) &
            (df_existing["Word Index"] == new_entry["Word Index"])
        ]
        
        if not matching_rows.empty:
            # For repeated occurrences, pick the highest Grammar Revision as a representative.
            latest_idx = matching_rows["Grammar Revision"].idxmax()
            latest_row = df_existing.loc[latest_idx]
            
            # Check if any grammar field is different.
            differences = any(new_entry.get(key) != self._norm_get(latest_row, key) for key in grammar_keys)
            
            if differences:
                # Compute new Grammar Revision number for the group.
                new_grammar_revision = matching_rows["Grammar Revision"].max() + 1
                new_entry["Grammar Revision"] = new_grammar_revision
                
                # Update all matching rows with new grammar values and new Grammar Revision.
                for idx in matching_rows.index:
                    for key in grammar_keys:
                        df_existing.at[idx, key] = new_entry.get(key)
                    df_existing.at[idx, "Grammar Revision"] = new_grammar_revision
                    # Update additional fields from new_entry if needed.
                    for key, value in new_entry.items():
                        if key not in grammar_keys and key not in ["Translation"]:
                            if key in ("Framework?", "Explicit?"):
                                df_existing.at[idx, key] = int(value)  # Cast Boolean to int (False->0, True->1)
                            else:
                                df_existing.at[idx, key] = value
                # Update Selected Darpan Meaning for these rows.
                for idx in matching_rows.index:
                    # --- Compute correct global index for the current word using the current verse ---
                    current_verse_words = self.accumulated_pankti.split()

                    def find_sublist_index(haystack, needle):
                        for i in range(len(haystack) - len(needle) + 1):
                            if haystack[i:i+len(needle)] == needle:
                                return i
                        return -1

                    start_index = find_sublist_index(self.pankti_words, current_verse_words)
                    if start_index == -1:
                        start_index = 0

                    # Assume new_entry["Word Index"] is the local index within the verse.
                    global_index = start_index + new_entry.get("Word Index", 0)

                    # Retrieve the selected Darpan meaning using the global index.
                    if len(self.accumulated_meanings) > global_index:
                        acc_entry = self.accumulated_meanings[global_index]
                        if isinstance(acc_entry, dict):
                            selected_meaning = "| ".join(acc_entry.get("meanings", []))
                        else:
                            selected_meaning = "| ".join(acc_entry)
                    else:
                        selected_meaning = ""

                    df_existing.at[idx, "Selected Darpan Meaning"] = selected_meaning

                # Now update the Translation Revision for all rows in the verse 
                # to reflect the latest Grammar Revision (without extra +1).
                verse_mask = df_existing["Verse"] == new_entry["Verse"]
                latest_grammar_revision = df_existing.loc[verse_mask, "Grammar Revision"].max()
                df_existing.loc[verse_mask, "Translation Revision"] = latest_grammar_revision
            else:
                # No differences detected; no update necessary.
                return
        else:
            # No existing entry for this word in the verse; add it with Grammar Revision 1 as well as Translation Revision 1.
            new_entry["Grammar Revision"] = 1
            new_entry["Translation Revision"] = 1

            # --- Compute correct global index for the current word using the current verse ---
            current_verse_words = self.accumulated_pankti.split()
            
            def find_sublist_index(haystack, needle):
                for i in range(len(haystack) - len(needle) + 1):
                    if haystack[i:i+len(needle)] == needle:
                        return i
                return -1

            start_index = find_sublist_index(self.pankti_words, current_verse_words)
            if start_index == -1:
                start_index = 0

            # Assume new_entry["Word Index"] holds the local index within the current verse.
            global_index = start_index + new_entry.get("Word Index", 0)

            # Retrieve the selected Darpan meaning using the global index.
            if len(self.accumulated_meanings) > global_index:
                acc_entry = self.accumulated_meanings[global_index]
                if isinstance(acc_entry, dict):
                    selected_meaning = "| ".join(acc_entry.get("meanings", []))
                else:
                    selected_meaning = "| ".join(acc_entry)
            else:
                selected_meaning = ""

            new_entry["Selected Darpan Meaning"] = selected_meaning

            # Determine Translation Revision for the verse.
            current_translation_revision = df_existing[df_existing["Verse"] == new_entry["Verse"]]["Translation Revision"].max()
            new_entry["Translation Revision"] = (current_translation_revision + 1) if current_translation_revision is not None else 1

            # Append new_entry to the DataFrame.
            df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)


        try:
            df_existing.to_excel(file_path, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save assessment data: {e}")

    def setup_options(self, parent_frame, label_text, options, variable):
        """
        Sets up radio button options in the specified parent frame.

        Args:
        parent_frame (tk.Frame): The frame in which to pack the radio buttons.
        label_text (str): The label text to display above the radio buttons.
        options (list of tuple): A list of tuples where each tuple contains the option text and the value to set in the variable.
        variable (tk.StringVar): The control variable for the group of radio buttons.
        """
        # Create a label for the option group with styling
        tk.Label(parent_frame, text=label_text, bg='light gray', font=('Arial', 12)).pack(pady=(10, 5))

        # Create radio buttons for each option
        for opt_text, opt_value in options:
            tk.Radiobutton(
                parent_frame,
                text=opt_text,
                variable=variable,
                value=opt_value,
                bg='light gray',
                selectcolor='light blue',
                anchor='w',
                font=('Arial', 11)
            ).pack(anchor='w', padx=20, pady=2)

    def navigation_controls(self, parent_frame):
        """
        Add navigation controls to the parent frame to navigate through words.
        """
        nav_frame = tk.Frame(parent_frame, bg='light gray')
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="Previous", command=self.previous_word, bg='dark gray', fg='white').pack(side='left', padx=5)
        tk.Button(nav_frame, text="Next", command=self.next_word, bg='dark gray', fg='white').pack(side='left', padx=5)

    def update_navigation_buttons(self):
        """Enable or disable navigation buttons based on the current word index."""
        print(f"Updating buttons, current index: {self.current_word_index}, total words: {len(self.pankti_words)}")
        
        # Disable 'Previous' button if at the start
        if self.current_word_index <= 0:
            self.prev_button.config(state=tk.DISABLED)
        else:
            self.prev_button.config(state=tk.NORMAL)
        
        # Disable 'Next' button if at the end
        if self.current_word_index >= len(self.pankti_words) - 1:
            self.next_button.config(state=tk.DISABLED)
        else:
            self.next_button.config(state=tk.NORMAL)

    def update_current_word_label(self):
        """Update the word label to display the current word."""
        if hasattr(self, 'pankti_words') and self.pankti_words:
            # Clamp the index to valid range:
            if self.current_word_index < 0:
                self.current_word_index = 0
            if self.current_word_index >= len(self.pankti_words):
                self.current_word_index = len(self.pankti_words) - 1
            current_word = self.pankti_words[self.current_word_index]
            self.word_label.config(text=current_word)
        else:
            self.word_label.config(text="No Word Available")

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.update_current_word_label()
        self.update_navigation_buttons()

    def next_word(self):
        if self.current_word_index < len(self.pankti_words) - 1:
            self.current_word_index += 1
            self.update_current_word_label()
        self.update_navigation_buttons()

    def select_current_word(self):
        """Trigger analysis for the currently displayed word."""
        if hasattr(self, 'pankti_words') and self.pankti_words:
            # Ensure current_word_index is within range:
            if self.current_word_index >= len(self.pankti_words):
                self.current_word_index = len(self.pankti_words) - 1
            word = self.pankti_words[self.current_word_index]
            self.fetch_data(word, " ".join(self.pankti_words))
        else:
            print("No word available for selection.")

    def close_window(self, window):
        """Closes the given Tkinter window."""
        if window and window.winfo_exists():
            window.destroy()

    def reset_input_variables(self):
        """Reset input variables for number, gender, and part of speech."""
        self.number_var.set("NA")
        self.gender_var.set("NA")
        self.pos_var.set("NA")

    def compose_clipboard_text_for_chatgpt(self):
        clipboard_text = "### Detailed Analysis & Literal Translation\n\n"
        clipboard_text += (
            f"The verse **'{self.accumulated_pankti}'** holds deep meaning. Below is a breakdown of each word with "
            "user-selected meanings and grammar details, which together form the basis for a literal translation prompt.\n\n"
        )
        
        # --- Preceding Verses & Translations ---
        # Load existing assessment data.
        existing_data = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")
        
        # Identify the candidate matching the current verse.
        current_candidate = next((cand for cand in self.chosen_match 
                                if cand.get("Verse", "").strip() == self.accumulated_pankti.strip()), None)
        
        preceding_verses_text = ""
        if current_candidate:
            text_set_no = current_candidate.get("Text Set No.")
            try:
                current_verse_no = int(current_candidate.get("Verse No."))
            except (ValueError, TypeError):
                current_verse_no = None
            
            if current_verse_no is not None:
                # Filter for the same Text Set No.
                filtered_data = existing_data[existing_data["Text Set No."] == text_set_no]
                consecutive_verses = []
                target_verse_no = current_verse_no - 1
                # Collect consecutive preceding verses.
                while True:
                    row = filtered_data[filtered_data["Verse No."] == target_verse_no]
                    if row.empty:
                        break
                    row_data = row.iloc[0]
                    consecutive_verses.insert(0, row_data)  # earlier verses first
                    target_verse_no -= 1
                
                if consecutive_verses:
                    preceding_verses_text += "\n### Preceding Verses & Translations\n\n"
                    for row_data in consecutive_verses:
                        verse_no = row_data.get("Verse No.", "")
                        verse_text = row_data.get("Verse", "")
                        translation = row_data.get("Translation", "")
                        preceding_verses_text += f"**Verse {verse_no}:** {verse_text}\n"
                        preceding_verses_text += f"**Translation:** {translation}\n\n"
        
        clipboard_text += preceding_verses_text
        
        # --- Current Verse Analysis ---
        current_verse_words = self.accumulated_pankti.split()
        
        def find_sublist_index(haystack, needle):
            # Find a consecutive occurrence of 'needle' in 'haystack'
            for i in range(len(haystack) - len(needle) + 1):
                if haystack[i:i+len(needle)] == needle:
                    return i
            return -1

        start_index = find_sublist_index(self.pankti_words, current_verse_words)
        if start_index == -1:
            start_index = 0  # Fallback if no match is found

        for i, word in enumerate(current_verse_words):
            actual_index = start_index + i
            clipboard_text += f"**Word {i+1}: {word}**\n"
            
            # Retrieve the entry for the current word (if available)
            acc_entry = self.accumulated_meanings[actual_index] if actual_index < len(self.accumulated_meanings) else {}
            # If the entry is a dictionary, extract the 'meanings' list; otherwise, assume it's already a list
            if isinstance(acc_entry, dict):
                meanings_list = acc_entry.get("meanings", [])
            else:
                meanings_list = acc_entry
            # Create a string of meanings, or a default message if none are available
            meanings_str = ", ".join(meanings_list) if meanings_list else "No user-selected meanings available"
            clipboard_text += f"- **User-Selected Meanings:** {meanings_str}\n"
            
            clipboard_text += "- **Grammar Options:**\n"
            finalized_matches_list = self.accumulated_finalized_matches[actual_index] if actual_index < len(self.accumulated_finalized_matches) else []
            
            if finalized_matches_list:
                for option_idx, match in enumerate(finalized_matches_list, start=1):
                    clipboard_text += (
                        f"  - **Option {option_idx}:**\n"
                        f"      - **Word:** {self._norm_get(match, 'Word') or 'N/A'}\n"
                        f"      - **Vowel Ending:** {self._norm_get(match, '\\ufeffVowel Ending') or 'N/A'}\n"
                        f"      - **Number / à¨µà¨šà¨¨:** {match.get('Number / à¨µà¨šà¨¨', 'N/A')}\n"
                        f"      - **Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£:** {match.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'N/A')}\n"
                        f"      - **Gender / à¨²à¨¿à©°à¨—:** {match.get('Gender / à¨²à¨¿à©°à¨—', 'N/A')}\n"
                        f"      - **Word Root:** {match.get('Word Root', 'N/A')}\n"
                        f"      - **Type:** {self._norm_get(match, 'Type') or 'N/A'}\n"
                    )
                    clipboard_text += (
                        f"      - **Literal Translation (Option {option_idx}):** The word '{word}' functions as a "
                        f"'{self._norm_get(match, 'Type') or 'N/A'}' with '{match.get('Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£', 'N/A')}' usage, in the "
                        f"'{match.get('Number / à¨µà¨šà¨¨', 'N/A')}' form and '{match.get('Gender / à¨²à¨¿à©°à¨—', 'N/A')}' gender. Translation: â€¦\n"
                    )
            else:
                clipboard_text += "  - No finalized grammar options available\n"
            
            clipboard_text += "\n"
        
        if 'à¥¥' in current_verse_words:
            clipboard_text += (
                "**Symbol:** à¥¥\n"
                "- **Meaning:** End of verse or sentence\n"
                "- **Context:** Denotes the conclusion of the verse.\n\n"
            )
        
        clipboard_text += "\n### Literal Translation Prompt\n"
        clipboard_text += (
            f"Using the above user-selected meanings and grammar details for the verse '{self.accumulated_pankti}', "
            "please generate a literal translation that adheres strictly to the grammatical structure, "
            "capturing the tense, number, gender, and function accurately."
        )
        
        return clipboard_text

    def prompt_copy_to_clipboard(self):
        print("Prompting to copy text to clipboard...")
        copy_prompt = messagebox.askyesno(
            "Copy to Clipboard", 
            f"Would you like to copy the detailed analysis for the verse '{self.accumulated_pankti}' to your clipboard?"
        )
        if copy_prompt:
            if not self.accumulated_pankti or not self.accumulated_meanings or not self.accumulated_grammar_matches or not self.accumulated_finalized_matches:
                print("Error: Accumulated data is not populated.")
                messagebox.showerror("Error", "Failed to copy data to clipboard: Data not populated.")
            else:
                clipboard_text = self.compose_clipboard_text_for_chatgpt()
                pyperclip.copy(clipboard_text)
                messagebox.showinfo("Copied", "The analysis has been copied to the clipboard!")
                print("Clipboard text copied successfully!")

    def prompt_for_final_grammar(self, word_entries):
        """
        Opens a modal window showing all grammar options for a given word.
        Generates a prompt text for ChatGPT to help finalize the grammar choice,
        copies it to the clipboard (with a button to re-copy if needed), and then
        allows the user to select the final applicable grammar.
        
        word_entries: a list of dictionaries (each corresponding to one grammar option for the word)
        """
        final_choice = {}

        final_win = tk.Toplevel(self.root)
        final_win.title(f"Finalize Grammar for '{word_entries[0]['Word']}'")
        final_win.configure(bg='light gray')

        # --- Build the ChatGPT prompt text ---
        prompt_lines = []
        prompt_lines.append(f"Finalise the applicable grammar for the word: {word_entries[0]['Word']}")
        prompt_lines.append("The following grammar options are available:")
        for idx, entry in enumerate(word_entries, start=1):
            summary = " | ".join([
                self._norm_get(entry, "\ufeffVowel Ending") or "",
                self._norm_get(entry, "Number / à¨µà¨šà¨¨") or "",
                self._norm_get(entry, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£") or "",
                self._norm_get(entry, "Gender / à¨²à¨¿à©°à¨—") or "",
                self._norm_get(entry, "Word Root") or "",
                self._norm_get(entry, "Type") or ""
            ])
            prompt_lines.append(f"Option {idx}: {summary}")
        prompt_text = "\n".join(prompt_lines)
        # --- End building prompt text ---

        # --- Display the prompt text and add a copy button ---
        prompt_frame = tk.Frame(final_win, bg="light gray")
        prompt_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        prompt_label = tk.Label(prompt_frame, 
                                text="ChatGPT Prompt for Grammar Finalisation:",
                                font=("Helvetica", 14, "bold"),
                                bg="light gray")
        prompt_label.pack(anchor="w", pady=(0,5))

        prompt_text_widget = scrolledtext.ScrolledText(prompt_frame, width=80, height=6,
                                                        font=("Helvetica", 12), wrap=tk.WORD)
        prompt_text_widget.pack(fill=tk.BOTH, expand=True)
        prompt_text_widget.insert(tk.END, prompt_text)
        prompt_text_widget.config(state=tk.DISABLED)

        def copy_prompt():
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt_text)
            messagebox.showinfo("Copied", "Prompt text copied to clipboard!")

        copy_btn = tk.Button(prompt_frame, text="Copy Prompt", command=copy_prompt,
                            font=("Helvetica", 12, "bold"),
                            bg="#007acc", fg="white", padx=10, pady=5)
        copy_btn.pack(anchor="e", pady=5)
        # --- End prompt display ---

        # Instruction for selecting final grammar
        instruction = tk.Label(final_win,
                            text="Multiple grammar options found for this word.\nPlease select the final applicable grammar:",
                            font=("Helvetica", 14),
                            bg="light gray")
        instruction.pack(pady=10)

        # Tk variable to hold the selected option index
        choice_var = tk.IntVar(value=0)

        # --- Create a scrollable area for the radio buttons ---
        options_container = tk.Frame(final_win, bg="light gray")
        options_container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Create a canvas in the container
        canvas = tk.Canvas(options_container, bg="light gray", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar to the container
        vsb = tk.Scrollbar(options_container, orient="vertical", command=canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame inside the canvas to hold the radio buttons
        options_frame = tk.Frame(canvas, bg="light gray")
        canvas.create_window((0,0), window=options_frame, anchor="nw")

        # Update the scroll region when the frame's size changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        options_frame.bind("<Configure>", on_frame_configure)
        # --- End scrollable area creation ---

        # Create radio buttons with option text as "Option {number}: {summary}"
        for idx, entry in enumerate(word_entries):
            summary = " | ".join([
                self._norm_get(entry, "\ufeffVowel Ending") or "",
                self._norm_get(entry, "Number / à¨µà¨šà¨¨") or "",
                self._norm_get(entry, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£") or "",
                self._norm_get(entry, "Gender / à¨²à¨¿à©°à¨—") or "",
                self._norm_get(entry, "Word Root") or "",
                self._norm_get(entry, "Type") or ""
            ])
            rb_text = f"Option {idx+1}: {summary}"
            rb = tk.Radiobutton(options_frame,
                                text=rb_text,
                                variable=choice_var,
                                value=idx,
                                bg="light gray",
                                font=("Helvetica", 12),
                                anchor='w',
                                justify=tk.LEFT,
                                selectcolor='light blue')
            rb.pack(anchor="w", padx=10, pady=5)

        def on_save():
            selected_index = choice_var.get()
            nonlocal final_choice
            final_choice = word_entries[selected_index]
            final_win.destroy()

        save_btn = tk.Button(final_win, text="Save Choice",
                            command=on_save,
                            font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        final_win.transient(self.root)
        final_win.grab_set()
        self.root.wait_window(final_win)
        return final_choice

    def prompt_save_results(self, new_entries, skip_copy=False):
        """
        For each verse in self.selected_verses, prompts the user to save new entries (accumulated from all words),
        checking for duplicates first. Then opens a modal prompt for assessment and saves the finalized data
        (including verse-level metadata) to an Excel file.
        """
        def _s(val):
            if val is None:
                return ""
            return unicodedata.normalize("NFC", str(val).strip())

        file_path = "1.2.1 assessment_data.xlsx"
        existing_data = self.load_existing_assessment_data(file_path)
        
        # Save the original accumulated_pankti so it can be restored later.
        original_accumulated_pankti = self.accumulated_pankti

        # Process each verse in the selected verses
        for verse in self.selected_verses:
            # Update the current verse for processing.
            self.accumulated_pankti = verse
            verse_norm = _s(verse)

            # reset repeat-note tracking for this verse
            self._repeat_note_shown = set()
            self._suppress_repeat_notes_for_verse = False

            # normalize for repeat-note consistency
            verse_key = unicodedata.normalize(
                "NFC", re.sub(r"\s+", " ", verse_norm.replace('à¥¥', '').strip())
            )
            current_verse_words = verse_key.split()

            # Normalize tokens once and use everywhere to avoid Unicode/spacing mismatches
            normalized_tokens = [_s(w) for w in current_verse_words]
            normalized_words = set(normalized_tokens)

            from collections import Counter
            word_counts = Counter(normalized_tokens)

            # Filter new_entries to only those whose "Word" is present in the current verse.
            filtered_new_entries = [
                entry for entry in new_entries
                if _s(entry.get("Word")) in normalized_words and _s(entry.get("Verse")) == verse_norm
            ]

            duplicate_entries = []
            unique_entries = []

            # Duplicate check: for each filtered entry, compare against existing data.
            for new_entry in filtered_new_entries:
                new_word = self._norm_get(new_entry, "Word")
                new_ve = self._norm_get(new_entry, "\ufeffVowel Ending")
                new_num = self._norm_get(new_entry, "Number / à¨µà¨šà¨¨")
                new_grammar = self._norm_get(new_entry, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£")
                new_gender = self._norm_get(new_entry, "Gender / à¨²à¨¿à©°à¨—")
                new_root = self._norm_get(new_entry, "Word Root")
                new_type = self._norm_get(new_entry, "Type")
                new_verse = self._norm_get(new_entry, "Verse")

                if any(
                    new_word == self._norm_get(existing_entry, "Word") and
                    new_ve == self._norm_get(existing_entry, "\ufeffVowel Ending") and
                    new_num == self._norm_get(existing_entry, "Number / à¨µà¨šà¨¨") and
                    new_grammar == self._norm_get(existing_entry, "Grammar / à¨µà¨¯à¨¾à¨•à¨°à¨£") and
                    new_gender == self._norm_get(existing_entry, "Gender / à¨²à¨¿à©°à¨—") and
                    new_root == self._norm_get(existing_entry, "Word Root") and
                    new_type == self._norm_get(existing_entry, "Type") and
                    new_verse == self._norm_get(existing_entry, "Verse")
                    for existing_entry in existing_data.to_dict('records')
                ):
                    duplicate_entries.append(new_entry)
                else:
                    unique_entries.append(new_entry)

            if duplicate_entries:
                duplicate_message = "Some entries are already present:\n" + "\n".join(map(str, duplicate_entries))
                messagebox.showinfo("Duplicates Found", duplicate_message)

            if not skip_copy:
                self.prompt_copy_to_clipboard()

            if unique_entries:
                save = messagebox.askyesno(
                    "Save Results",
                    f"Would you like to save the new entries for the following verse?\n\n{verse_norm}"
                )
                if save:
                    # Open one assessment prompt for the current verse.
                    assessment_data = self.prompt_for_assessment_once()

                    # --- Extract verse metadata from candidate matches ---
                    verse_to_match = _s(self.accumulated_pankti)
                    candidate = None
                    if hasattr(self, 'candidate_matches') and hasattr(self, 'chosen_match') and self.chosen_match:
                        for cand in self.chosen_match:
                            if _s(cand.get("Verse")) == verse_to_match:
                                candidate = cand
                                break
                        if candidate is None:
                            candidate = self.chosen_match[0]
                        verse_metadata = {
                            "Verse": verse_to_match,
                            "S. No.": candidate.get("S. No.", ""),
                            "Verse No.": candidate.get("Verse No.", ""),
                            "Stanza No.": candidate.get("Stanza No.", ""),
                            "Text Set No.": candidate.get("Text Set No.", ""),
                            "Raag (Fixed)": candidate.get("Raag (Fixed)", ""),
                            "Sub-Raag": candidate.get("Sub-Raag", ""),
                            "Writer (Fixed)": candidate.get("Writer (Fixed)", ""),
                            "Verse Configuration (Optional)": candidate.get("Verse Configuration (Optional)", ""),
                            "Stanza Configuration (Optional)": candidate.get("Stanza Configuration (Optional)", ""),
                            "Bani Name": candidate.get("Bani Name", ""),
                            "Musical Note Configuration": candidate.get("Musical Note Configuration", ""),
                            "Special Type Demonstrator": candidate.get("Special Type Demonstrator", ""),
                            "Verse Type": candidate.get("Type", ""),
                            "Page Number": candidate.get("Page Number", "")
                        }
                    else:
                        verse_metadata = {}
                    # -------------------------------------------------------

                    # --- Finalize grammar options per word (handling repeated words by occurrence order via clustering) ---
                    # --- Group unique_entries by word ---
                    word_groups = {}
                    for entry in unique_entries:
                        word = _s(entry["Word"])
                        word_groups.setdefault(word, []).append(entry)
                        
                    final_entries = []
                    occurrence_mapping = {}  # Mapping from (word, occurrence_position) to list of entries (options)

                    # For each unique word in the current verse, partition its entries into clusters based on occurrence count.
                    for word in set(normalized_tokens):
                        count = word_counts[word]
                        if word not in word_groups:
                            continue
                        entries_list = word_groups[word]  # all unique entries for that word (in sequence)
                        n = len(entries_list)
                        k = count  # expected number of clusters
                        groups = []
                        start = 0
                        # Partition entries_list into k groups using a chunking method.
                        # If n isn't exactly divisible by k, distribute the remainder to the first few groups.
                        group_size = n // k
                        remainder = n % k
                        for i in range(k):
                            size = group_size + (1 if i < remainder else 0)
                            group = entries_list[start:start+size]
                            groups.append(group)
                            start += size
                        # Find the indices (positions) in normalized_tokens where this word occurs, in order.
                        occurrence_positions = [i for i, w in enumerate(normalized_tokens) if w == word]
                        for occ, pos in zip(range(k), occurrence_positions):
                            occurrence_mapping[(word, pos)] = groups[occ]

                    occurrence_counters = {}
                    # Now, iterate over normalized_tokens (which are in order) and process each occurrence.
                    for idx, word in enumerate(normalized_tokens):
                        occ_idx = occurrence_counters.get(word, 0)
                        occurrence_counters[word] = occ_idx + 1
                        key = (word, idx)  # Unique key for the occurrence at position idx.
                        entries = occurrence_mapping.get(key, [])
                        if not entries:
                            continue  # No entries for this occurrence.

                        if word_counts.get(word, 0) > 1 and occ_idx > 0:
                            if not getattr(self, "_use_inline_literal_banner", True):
                                self._maybe_show_repeat_important_note(word, occ_idx, verse_key)
                            else:
                                self._repeat_note_shown.add((verse_key, word, "second"))

                        # Remove duplicate entries within this occurrence group (local deduplication).
                        dedup_entries = []
                        seen = set()
                        for entry in entries:
                            entry_tuple = tuple(sorted(entry.items()))
                            if entry_tuple not in seen:
                                seen.add(entry_tuple)
                                dedup_entries.append(entry)
                        entries = dedup_entries

                        # If more than one unique option exists for this occurrence, prompt the user to choose.
                        if len(entries) > 1:
                            chosen_entry = self.prompt_for_final_grammar(entries)
                        else:
                            chosen_entry = entries[0]

                        # Capture the occurrence index.
                        chosen_entry['Word Index'] = idx

                        # Ensure self.accumulated_finalized_matches is long enough.
                        if len(self.accumulated_finalized_matches) <= idx:
                            self.accumulated_finalized_matches.extend([[]] * (idx - len(self.accumulated_finalized_matches) + 1))
                        self.accumulated_finalized_matches[idx] = [chosen_entry]
                        final_entries.append(chosen_entry)
                    # -------------------------------------------------------

                    # Now update each finalized entry with the assessment and verse metadata, then save.
                    for entry in final_entries:
                        entry.update(assessment_data)
                        entry.update(verse_metadata)
                        self.save_assessment_data(entry)
                    messagebox.showinfo("Saved", "Assessment data saved successfully for verse:\n" + verse_norm)

        # Restore the original accumulated_pankti after processing all verses.
        self.accumulated_pankti = original_accumulated_pankti

        if hasattr(self, 'copy_button') and self.copy_button.winfo_exists():
            self.copy_button.config(state=tk.NORMAL)

    def prompt_for_assessment_once(self):
        """Opens a modal prompt for the entire verse assessment and returns the collected data."""
        assessment_win = tk.Toplevel(self.root)
        assessment_win.title(f"Enter Translation Assessment for: '{self.accumulated_pankti}'")
        assessment_win.configure(bg='light gray')

        instruction_label = tk.Label(
            assessment_win, 
            text="Paste the analysis result for the entire verse below:",
            font=("Helvetica", 14), bg="light gray"
        )
        instruction_label.pack(pady=10)

        analysis_text = scrolledtext.ScrolledText(assessment_win, width=80, height=10,
                                                font=("Helvetica", 12), wrap=tk.WORD)
        analysis_text.pack(padx=20, pady=10)

        cb_frame = tk.Frame(assessment_win, bg="light gray")
        cb_frame.pack(pady=10)

        framework_var = tk.BooleanVar()
        explicit_var = tk.BooleanVar()

        framework_cb = tk.Checkbutton(cb_frame, text="Framework?", variable=framework_var,
                                    font=("Helvetica", 12), bg="light gray")
        framework_cb.pack(side=tk.LEFT, padx=10)

        explicit_cb = tk.Checkbutton(cb_frame, text="Explicit?", variable=explicit_var,
                                    font=("Helvetica", 12), bg="light gray")
        explicit_cb.pack(side=tk.LEFT, padx=10)

        assessment_data = {}

        def on_save():
            translation = analysis_text.get("1.0", tk.END).strip()
            if not translation:
                messagebox.showerror("Error", "Please paste the analysis result.")
                return
            assessment_data["Translation"] = translation
            assessment_data["Framework?"] = framework_var.get()
            assessment_data["Explicit?"] = explicit_var.get()
            assessment_win.destroy()

        save_btn = tk.Button(assessment_win, text="Save Assessment",
                            command=on_save, font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        assessment_win.transient(self.root)
        assessment_win.grab_set()
        self.root.wait_window(assessment_win)

        return assessment_data

    def accumulate_pankti_data(self, pankti):
        self.accumulated_pankti = pankti

    def accumulate_meanings_data(self, meanings):
        """
        Accumulate the meanings for the current word, along with the word itself and its index.
        This creates a mapping for each word occurrence.
        """
        # Ensure the list is long enough for the current word index.
        while len(self.accumulated_meanings) <= self.current_word_index:
            self.accumulated_meanings.append({"word": None, "meanings": []})
        
        # Store the word if it hasn't been stored yet.
        if self.accumulated_meanings[self.current_word_index]["word"] is None:
            # Assuming self.pankti_words is defined and holds the current verse's words.
            self.accumulated_meanings[self.current_word_index]["word"] = self.pankti_words[self.current_word_index]
        
        # Update the meanings for the current word occurrence.
        self.accumulated_meanings[self.current_word_index]["meanings"] = meanings

    def accumulate_grammar_matches(self, matches):
        self.accumulated_grammar_matches.append(matches)

    def accumulate_finalized_matches(self, finalized_matches):
        # Ensure the list is long enough to hold the current index
        if len(self.accumulated_finalized_matches) <= self.current_word_index:
            # Expand the list to the required length with empty lists
            self.accumulated_finalized_matches.extend([[]] * (self.current_word_index - len(self.accumulated_finalized_matches) + 1))
        
        # Store the finalized matches at the correct index
        self.accumulated_finalized_matches[self.current_word_index] = finalized_matches

    def start_progress(self):
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Please Wait...")
        self.progress_window.geometry("350x120")
        self.progress_window.resizable(False, False)
        self.progress_window.attributes("-topmost", True)
        self.progress_window.configure(bg="#f0f0f0")
        self.progress_window.attributes('-alpha', 0.0)  # Start fully transparent

        # Center the progress window
        self.progress_window.update_idletasks()
        x = (self.progress_window.winfo_screenwidth() - self.progress_window.winfo_width()) // 2
        y = (self.progress_window.winfo_screenheight() - self.progress_window.winfo_height()) // 3
        self.progress_window.geometry(f"+{x}+{y}")

        # Fade-in effect
        def fade_in(window, alpha=0.0):
            alpha = round(alpha + 0.05, 2)
            if alpha <= 1.0:
                window.attributes('-alpha', alpha)
                window.after(30, lambda: fade_in(window, alpha))

        fade_in(self.progress_window)

        # Custom style
        style = ttk.Style(self.progress_window)
        style.theme_use('default')

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#e0e0e0",
                        bordercolor="#e0e0e0",
                        background="#4a90e2",
                        lightcolor="#4a90e2",
                        darkcolor="#4a90e2",
                        thickness=20)

        label = ttk.Label(self.progress_window, text="Processing, please wait...", background="#f0f0f0", font=("Segoe UI", 10))
        label.pack(pady=(20, 5))

        self.progress_bar = ttk.Progressbar(self.progress_window,
                                            mode='indeterminate',
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(padx=30, fill=tk.X)
        self.progress_bar.start(7)

        self.root.update_idletasks()

    def stop_progress(self):
        self.progress_bar.stop()
        self.progress_window.destroy()

    def handle_submitted_input(self, word):
        # Implement your logic for handling the submitted input here
        print(f"Handling submitted input for: {word}")
        # You can add your logic here, such as saving or processing the input further

    def filter_unique_matches(self, matches):
        """
        Eliminate duplicates based on the grammatical parts and return unique matches.

        Args:
        matches (list): The list of matches to filter.

        Returns:
        list: The list of unique matches.
        """
        # Sort matches by match_count first and then by match_percentage, both in descending order
        matches_sorted = sorted(matches, key=lambda x: (x[1], x[2]), reverse=True)

        unique_matches = []
        seen_grammar = set()
        for match in matches_sorted:
            grammar_info = match[0].split(" | ")[2:]  # Extract grammar info (e.g., Number, Gender, POS, etc.)
            grammar_tuple = tuple(grammar_info)
            if grammar_tuple not in seen_grammar:
                unique_matches.append(match)
                seen_grammar.add(grammar_tuple)

        # Accumulate Grammar Matches data
        self.accumulate_grammar_matches(unique_matches)
        return unique_matches

    def perform_dictionary_lookup(self, word, callback):
        """
        Runs the dictionary lookup (with its progress bar) in a separate thread.
        Once the lookup completes, the callback is called on the main thread with the lookup result.
        """
        def lookup_worker():
            # Call your lookup function (which already shows the progress bar)
            meanings = self.lookup_word_in_dictionary(word)
            # Schedule the callback on the main thread with the obtained meanings
            self.root.after(0, lambda: callback(meanings))
        threading.Thread(target=lookup_worker, daemon=True).start()

    def handle_lookup_results(self, matches, meanings):
        """
        Called when the dictionary lookup is finished.
        'matches' are those computed earlier and 'meanings' is the result from the lookup.
        This method updates the UI by calling show_matches.
        """
        print(f"Lookup completed for {self.pankti_words[self.current_word_index]}. Meanings: {meanings}")
        self.show_matches(matches, self.current_pankti, meanings)

    def calculate_match_metrics(self, word, vowel_ending):
        """
        Calculates the number of matching characters from the end of vowel_ending and word, 
        and the percentage of matching characters with respect to the matched part of vowel_ending.
        
        Parameters:
        word (str): The word to be compared.
        vowel_ending (str): The vowel ending to be compared, possibly containing multiple parts.
        
        Returns:
        tuple: A tuple containing:
            - match_count (int): Number of matching characters from the end.
            - match_percentage (float): Percentage of matching characters based on the matched part of vowel_ending.
        """
        word_chars = list(word)  # Convert word to a list of characters
        vowel_parts = vowel_ending.split()  # Split vowel ending into parts

        total_match_count = 0
        max_match_percentage = 0.0

        # Iterate through each part of the vowel ending
        for part in vowel_parts:
            part_chars = list(part)  # Convert each part to a list of characters

            match_count = 0

            # Reverse iterate through both word and part to compare characters from the end
            for i in range(1, min(len(word_chars), len(part_chars)) + 1):
                if word_chars[-i] == part_chars[-i]:
                    match_count += 1
                else:
                    break  # Stop when characters no longer match

            if match_count > 0:
                # Calculate match percentage based on the length of the matched part
                match_percentage = (match_count / len(part_chars)) * 100
                total_match_count += match_count
                
                # Track the highest match percentage found
                if match_percentage > max_match_percentage:
                    max_match_percentage = match_percentage

            # Stop if there was any match in the current part
            if match_count > 0:
                break

        return total_match_count, max_match_percentage


if __name__ == "__main__":
    root = tk.Tk()
    app = GrammarApp(root)
    root.mainloop()
    def _do_prompt_whats_new_fixed(self, state: dict):
        """Prompt the user about recent UI changes with ASCII-safe quotes."""
        try:
            if messagebox.askyesno(
                "What's New",
                (
                    "We've improved verse selection cards: centered layout, equal column widths, ",
                    "and radios no longer overlap text. View details now?"
                ),
            ):
                self.show_whats_new()
        finally:
            try:
                state["last_whats_new"] = WHATS_NEW_ID
                self._save_state(state)
            except Exception:
                pass
        return
