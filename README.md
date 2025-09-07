# Birha Toolkit

Birha is a desktop toolkit for studying the grammar of Gurbani (the Sikh scripture). It ships as a Tkinter app (`1.1.0_birha.py`) with a dashboard for:

- Verse analysis from the Sri Guru Granth Sahib (SGGS)
- Updating noun/verb morphology in the grammar database
- Working through literal-meaning translations and reâ€‘analysis

The app reads/writes the bundled CSV/XLSX data files in place. Make a backup before large editing sessions.

## Features

- Dashboard workflow: quick access to verse analysis, grammar updates, and literal meanings.
- Search and filter: find verses by text or metadata, then select one for analysis.
- Grammar editing: review/update entries (ending class, gender, number, case) with live lookups.
- Literal meanings: paste translations (e.g., Darpan), pick matches/meanings, and finalize results.
- Reâ€‘analysis tools: revisit prior entries to correct or refine decisions.
- Clipboard support: copy/paste helpers for faster data entry.

- 1.1.4 Verse_Padarth_Arth_with_pages.json: Verse + padarth + arth with SGGS page numbers (JSON).\r\n- 1.1.5 Verse_Padarth_Arth_with_pages.csv: CSV counterpart of 1.1.4 for spreadsheet workflows.\r\nRequirements

- Python 3.10 or newer (Windows, macOS, or Linux)
- Tkinter (included with most Python installers)
- Packages pinned in `requirements.txt`

Install dependencies into a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

This installs `pandas`, `numpy`, `RapidFuzz`, `pyperclip`, `openpyxl`, and related runtime dependencies.

## Run

From the repository root:

```bash
python 1.1.0_birha.py
```

The dashboard opens with buttons to start verse analysis, update the grammar database, or work through literal meanings.

## Usage Tips

- Fonts: ensure a Gurmukhi/Punjabi font is installed so text renders correctly (e.g., Raavi, Saab, AnmolLipi, GurbaniAkhar).
- Backups: the app updates the CSV/XLSX files; keep backups if you are making lots of edits.
- Excel locks files: close spreadsheets in Excel/LibreOffice while running the app to avoid fileâ€‘inâ€‘use errors.

## Troubleshooting

- Garbled characters (ï¿½): open files as UTFâ€‘8. On Windows terminals, run `chcp 65001` before launching Python or enable â€œUse Unicode UTFâ€‘8 (Beta)â€ in Region settings.
- Tkinter not found: install a standard Python from python.org (includes Tk) or your OS package that bundles Tk support.
- Missing fonts: install a Gurmukhi font and restart the app.

## Development

- Quick compile check: `python -m py_compile 1.1.0_birha.py`
- Optional QA script (if Bash is available): `bash scripts/qa.sh`

## Status

Active work in progress. Names/formats of datasets and UI flows may change as the grammar resources evolve.

