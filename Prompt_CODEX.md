
---

# Prompt for `Prompt_CODEX.md` (Task 8)

## Axioms T8 — Store Adapter Integration (additive only)

**Study these local files first (use their actual filenames/paths; do not rely on `@` shorthand inside this markdown):**

* `0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`
* `1.1.0_birha.py`

### Goal

Implement the **Axioms Store Adapter** to persist real data to a new workbook without breaking any existing stores. This is the first “logic” milestone after the UI-first phase and must be **strictly additive**.

### Hard constraints

* Follow the contract in “0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx” (Phase II → **T8**).
* Work **only** in `1.1.0_birha.py`. Keep pre-Axiom modules untouched (read-only baseline).
* Use a clear header block:
  `# === Axioms T8: Store Adapter Integration (additive only) ===`
* Headless safety: no GUI blocking calls during file I/O; catch and downgrade UI notifications if DISPLAY is absent.
* Atomic writes; never corrupt existing workbooks; preserve non-spec sheets.

### Data target

Create (if missing) and then read/write the workbook:

* **`1.3.0_axioms.xlsx`** with these sheets:

  * `Axioms` (columns: `axiom_id`, `short_axiom`, `category`, `created_at`, `updated_at`, `created_by`, `status`)
  * `AxiomDescriptions` (columns: `axiom_id`, `description_type` ["axiom","verse_specific"], `text`, `rev`, `updated_at`)
  * `AxiomContributions` (columns: `axiom_id`, `verse`, `verse_key_norm`, `page`, `translation_revision_seen`, `link_type` ["primary","supporting"], `created_at`)
  * `AxiomKeywords` (columns: `axiom_id`, `literal_synonyms`, `literal_antonyms`, `spiritual_synonyms`, `spiritual_antonyms`, `updated_at`)
  * `AxiomWorkqueue` (columns: `work_id`, `axiom_id`, `task` ["reanalysis","keywords","description"], `reason`, `created_at`, `status` ["pending","done"])

> Types: keep columns flexible (strings/datetimes); do **not** enforce strict dtypes that can fail on Excel round‐trips.

### Implementation outline

Add a small adapter layer with pandas/openpyxl, mirroring the tracker helpers already present in `1.1.0_birha.py`:

1. **Path resolver**: `_get_axioms_store_path() -> str` (default to project root `1.3.0_axioms.xlsx`).
2. **Ensure & load**:

   * `ensure_axioms_store(path)` -> create workbook with empty frames if missing (atomic temp file then replace).
   * `load_axioms_store(path)` -> return DataFrames per sheet + ordered list of “other sheets” to preserve.
3. **Save**:

   * `_save_axioms_store(path, dfs_dict, others)` -> overlay/update only spec sheets; keep non-spec sheets intact; one `ExcelWriter` per save; atomic replace.
4. **Adapter API (pure functions or a small class)**:

   * `create_axiom(short_axiom, category="Primary", created_by="ui") -> axiom_id`
   * `upsert_axiom_description(axiom_id, text, description_type="axiom")`
   * `link_contribution(axiom_id, verse, page=None, translation_revision_seen=None, link_type="primary")`
   * `upsert_keywords(axiom_id, literal_synonyms=None, literal_antonyms=None, spiritual_synonyms=None, spiritual_antonyms=None)`
   * `enqueue_work(axiom_id, task, reason)`
   * Helpers: `_normalize_verse_key(text)`, timestamp factory, simple id factory like `AX{YYYYMMDDHHMMSS}{counter}` and `WQ{...}`.
5. **Thread/file safety**:

   * In-process lock (`threading.Lock`) guarding load→mutate→save.
   * Best-effort file lock on Windows optional (guarded import); never block UI.
6. **Minimal wiring (non-disruptive)**:

   * From **T6** buttons (“Create Axiom” / “Link to Existing”), if they exist, **augment** the confirmation path to call the adapter with mock/real values gathered from T4/T5 (verse summaries, translation source, prompt text). Keep all prior messageboxes; wrap in try/except and silently no-op on failure.
   * Do **not** alter T0–T7 behavior; only add calls where the T6 button handlers already exist.

### Acceptance criteria

* First run creates `1.3.0_axioms.xlsx` with the 5 sheets and headers.
* Subsequent runs append/update without corrupting the file; non-spec sheets (if any) remain intact.
* “Create Axiom” and “Link to Existing Axiom” paths (from T6) now persist rows (at least `Axioms`, `AxiomContributions`); success still shows the same UI confirmations.
* `python -m py_compile 1.1.0_birha.py` passes.

### Test notes (manual)

* Delete/rename any existing `1.3.0_axioms.xlsx`, run the app, trigger T6 actions, confirm workbook is created and populated.
* Re-run actions to ensure idempotent upserts (descriptions/keywords) and proper append for contributions/workqueue.

### Strict do-nots

* No edits to pre-Axiom modules or baseline strings.
* No breaking changes to previously added Axioms UI tasks (T0–T7).
* No heavy dependencies; only stdlib, pandas, openpyxl already used in project.

---
