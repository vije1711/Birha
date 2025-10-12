# Repository Guidelines

## Project Structure & Module Organization
The Tkinter dashboard lives in `1.1.0_birha.py`; grammar datasets such as `1.1.1_birha.csv` and `1.1.4 Verse_Padarth_Arth_with_pages.json` stay in the repository root so the app can read/write them directly. Reference notes reside in `docs/`, while utilities like `scripts/patch_abw_labels.py` and `scripts/tracker_quick_check.py` belong in `scripts/`. Use `tests/` for automation that mirrors the runtime layout, and treat `.venv/` as disposable—rebuild it instead of editing tracked files inside.

## Build, Test, and Development Commands
- `python -m venv .venv` then `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Unix) to prepare the environment.
- `pip install -r requirements.txt` installs the pinned GUI and data processing stack.
- `python 1.1.0_birha.py` launches the desktop app; run it from the repo root.
- `python -m py_compile 1.1.0_birha.py` gives a fast syntax check before committing.
- `python scripts/tracker_quick_check.py` validates tracker exports after CSV changes.

## Coding Style & Naming Conventions
Follow PEP 8 defaults: four-space indentation, snake_case functions, PascalCase classes (see `WindowManager`). Keep helpers single-purpose, add brief docstrings when behavior is subtle, and centralize UI strings for future localization. Document any new dataset columns inside the scripts that generate or mutate them.

## Testing Guidelines
Add regression modules as `tests/test_<feature>.py` using Python's built-in `unittest`. Place lightweight fixtures in `tests/fixtures/` so full CSVs stay untouched. Run `python -m unittest discover tests` before opening a pull request, and pair data-sensitive code with the relevant `scripts/` check for quick verification.

## Commit & Pull Request Guidelines
Write imperative commit subjects (e.g., `Preserve session entries when save fails`) and group related data exports together. Reference issues or Trello IDs in commit bodies, noting any manual migrations. Pull requests should outline behavior changes, list the commands/tests run, include screenshots for UI work, and call out dataset risks so reviewers can schedule backups.

## Data Safety & Configuration Tips
Treat the bundled datasets as the canonical SGGS grammar source; keep backups and avoid partial saves. Remove `1.1.3_lexicon_index.json` to rebuild the lexicon cache after updating the Excel input. Use `chcp 65001` or another Unicode-capable terminal on Windows to prevent corrupting Gurmukhi text.
