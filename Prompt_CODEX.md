---

### **Prompt Title**

Implement Axioms T5 — Local Draft Save/Load (JSON Mock)

### **Prompt Text (for Prompt_Codex.md)**

Implement **Task T5** of the Axioms Framework inside `1.1.0_birha.py` under a new header:
`# === Axioms T5: Local Draft Save/Load (JSON Mock) ===`

#### **Objective**

Enhance the `AxiomsPromptBuilderView` introduced in T4 so that saved drafts now persist between application sessions using a lightweight JSON file (`axioms_drafts.json`) placed in the project root directory.

#### **Implementation Scope**

1. **Draft Persistence Adapter**

   * Add helper functions:

     * `_axioms_t5_get_draft_path()` → returns local JSON path (same folder as 1.1.0_birha.py).
     * `_axioms_t5_load_drafts()` → reads file; returns list of drafts (or empty list if missing/corrupt).
     * `_axioms_t5_save_drafts(drafts)` → safely writes JSON (UTF-8, indent 2).
   * All file I/O must be exception-guarded (use try/except) and never crash UI.

2. **Integration with Dashboard**

   * Extend `AxiomsDashboard` or attach lightweight mixin logic:

     * On startup, call `_axioms_t5_load_drafts()` and attach results as `self._axioms_drafts`.
     * Provide method `save_all_axiom_drafts()` that calls `_axioms_t5_save_drafts(self._axioms_drafts)` on exit.
     * Hook `WM_DELETE_WINDOW` to save drafts before closing.

3. **Enhance Prompt Builder View**

   * When `_save_draft()` is triggered, persist draft both in-memory and to disk immediately via `_axioms_t5_save_drafts()`.
   * On open/re-launch, previously saved drafts must appear automatically (no UI listing yet — just load to memory).

4. **Data Format**
   Each stored draft is a dict like:

   ```json
   {
     "created_at": "2025-10-19T07:45:00",
     "verse": "text…",
     "related_summ": "text…",
     "consecutive_summ": "2",
     "translation_mode": "own|darpan",
     "own_text": "string",
     "prompt_text": "string"
   }
   ```

   Time format: ISO 8601 (`datetime.now().isoformat(timespec="seconds")`).

5. **Acceptance Criteria**

   * Drafts saved via “Save Draft” remain after closing and reopening the app.
   * No crashes if file is missing or corrupt (auto-reset to empty list).
   * File created at first save; readable with standard JSON viewers.
   * `python -m py_compile 1.1.0_birha.py` passes.

#### **Additive Requirements**

* Do not modify or rename any pre-Axiom functions, constants, or strings.
* Place all new code under its own T5 header.
* Preserve T4 UI behavior; this task adds persistence only.

#### **Testing**

1. Run app → open Prompt Builder (T4).
2. Click **Save Draft**, then close the Axioms Dashboard or restart the program.
3. Reopen Dashboard → `_axioms_drafts` list should contain previous entries.

---