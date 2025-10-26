# Repository Guidelines

## Project Structure & Module Organization
The toolkit revolves around `1.1.0_birha.py`, a Tkinter dashboard that reads and writes the bundled Gurbani datasets (`1.1.1_birha.csv`, `1.1.3 sggs_extracted_with_page_numbers.xlsx`, `1.1.4`/`1.1.5` verse exports, and related JSON). Keep these large files under source control and back them up before running batch edits. Testing code lives in `tests/` with domain-specific suites under `tests/axioms/`. `requirements.txt` pins runtime libraries; `Prompt_CODEX.md` and `pr_body.md` capture workflow guidance.

## Build, Test, and Development Commands
Use a virtual environment and install dependencies with:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Launch the app locally via `python 1.1.0_birha.py`. Run a fast syntax check with `python -m py_compile 1.1.0_birha.py`. Execute automated tests from the repo root:
```bash
python -m unittest discover -s tests
```
Add targeted test files to the command when iterating (`python -m unittest tests.test_reanalysis_bom`).

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and descriptive, domain-aware names (`GrammarApp`, `safe_equal_matches_reanalysis`). Prefer module-level constants for paths, and guard filesystem writes with clear context managers. Keep UI callbacks and data helpers small; break long Tk layouts into helper methods. When touching data normalization, preserve existing Unicode handling and byte-order-mark stripping idioms already present in `GrammarApp`.

## Testing Guidelines
Tests rely on the standard library `unittest`. Mirror the existing pattern of one `Test*` class per feature and name files `test_<feature>.py`. Cover BOM stripping, normalization, and data transforms with focused assertions against lightweight fixtures; avoid bundling large XLSX/CSV blobs into new tests. Run the full suite before opening a PR, and add regression tests whenever fixing parsing bugs or edge-case UI behavior.

## Commit & Pull Request Guidelines
Commit history favors short, imperative summaries (“Corrections implemented”, “Task 10 Implemented”) with optional follow-up commits for refinements. Commit after logical units, keeping data updates and code changes in separate commits when practical. For pull requests, fill out `pr_body.md`, link the relevant issue or task, note any data migrations, and include before/after screenshots for UI adjustments. Confirm test output and mention manual QA steps in the PR description.

## Data & Configuration Notes
The app mutates the CSV/XLSX assets in place; never commit temporary spreadsheets or personal exports. Use `.env`-style files only if absolutely necessary and exclude secrets from version control. When sharing builds, scrub local paths from configuration dialogs and verify that no proprietary fonts or licensed datasets slip into the repository.
