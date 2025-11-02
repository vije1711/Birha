## Task T12 — Axioms Test Harness & Smoke Tests (additive only)

**Goal:** Provide a runnable, headless-safe test harness for Axioms UI surface and helpers so we can verify presence/wiring without touching legacy flows.

**Read these files explicitly (no @ shorthands):**

* `./Prompt_CODEX.md` (this file)
* `./0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx` (Engineering Contract V2.0)

**Scope & constraints:**

* Target file: `1.1.0_birha.py` (additive code only).
* Do **not** modify or rename any existing functions/constants/strings.
* Do **not** alter `1.1.0_birha_pre_Axiom.py`; treat as read-only reference.
* GUI tests must be **headless-safe** (no real Tk mainloop, no OS window required).

**What to implement (minimal but useful):**

1. **Harness API (additive in `1.1.0_birha.py`)**

   * `AXIOMS_T12_TEST_PATTERN = "test_axioms_*.py"` (or reuse if present).
   * `def run_axioms_tests(pattern: str = AXIOMS_T12_TEST_PATTERN, directory: Optional[Union[str, Path]] = None, *, verbosity: int = 1) -> int:`

     * Prefer **pytest** execution if available: `pytest.main([...])` against a discovered tests root (default `tests/axioms`).
     * Fallback to `unittest` discovery if `pytest` is not importable.
     * Return a **process-style** exit code (0 = success, non-zero = failures).
     * Must not crash if tests dir is missing; print a short note and return 0.
   * Keep any existing `discover_axioms_tests` helper intact; just call it only in the unittest fallback.

2. **Tests layout (create new files only):**

   * Create folder `tests/axioms/`.
   * Add `tests/axioms/_loader.py` with a safe helper to import `1.1.0_birha.py` under an alias (use `importlib.machinery.SourceFileLoader` since the filename starts with a digit). Never mutate module state.
   * Add **smoke tests** (pytest preferred) named `test_axioms_smoke.py` (pattern-compliant):

     * Assert the following **classes** exist on import:
       `AxiomsDashboard`, `AxiomsVerseInputFlow`, `AxiomsTranslationChoiceView`, `AxiomsPromptBuilderView`, `AxiomsSGGSReaderView`.
     * Assert **entry wiring** is present: `_axioms_t0_install` exists and doesn’t raise on call (idempotent).
     * Assert **T2 flow guards**: constructing `AxiomsVerseInputFlow` with a dummy master does not throw; calling its `reset()` works headless.
     * Mark GUI-dependent sections with `pytest.mark.skipif("DISPLAY" not set)` or guard in try/except; no real windows.

3. **Developer ergonomics:**

   * Add a **docstring snippet** near the new harness function showing how to run locally:

     * `python - <<'PY'\nimport importlib.machinery as M; m=M.SourceFileLoader('birha','1.1.0_birha.py').load_module(); exit(m.run_axioms_tests())\nPY`
   * Ensure the harness does **not** import `tkinter` at import time beyond what is already imported by the file; any GUI touch must be guarded.

**Acceptance criteria:**

* `python -m py_compile 1.1.0_birha.py` passes.
* Running the docstring one-liner returns **0** when tests are present and passing.
* Deleting the `tests/axioms` folder returns **0** gracefully with a short “no tests found” note.
* All changes are strictly additive; no regressions in existing UI.

**Deliverables checklist:**

* [ ] Additive harness function `run_axioms_tests(...)` (pytest-first, unittest fallback).
* [ ] `tests/axioms/_loader.py` (module loader helper).
* [ ] `tests/axioms/test_axioms_smoke.py` (presence + wiring + headless safety).
* [ ] Inline docstring with example shell invocation.

---
