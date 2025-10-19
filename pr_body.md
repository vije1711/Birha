## Summary
Implements **Task T5 — Local Draft Save / Load (JSON Mock)** as per  
**“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx.”**

This enhancement extends the **Axioms Prompt Builder View** (T4) to provide real local persistence for user-saved drafts, allowing them to survive application restarts.  
Drafts are written to and reloaded from a lightweight JSON file named **`axioms_drafts.json`** located in the same directory as `1.1.0_birha.py`.

---

## Scope & Behavior
- Introduces `_axioms_t5_get_draft_path()`, `_axioms_t5_load_drafts()`, and `_axioms_t5_save_drafts(drafts)` for safe JSON persistence.
- Integrates with `AxiomsDashboard` to:
  - Load drafts on startup (`self._axioms_drafts = _load_drafts()`).
  - Auto-save on window close through `WM_DELETE_WINDOW`.
- Enhances `AxiomsPromptBuilderView._save_draft()` to immediately persist every new draft to disk.
- Drafts reload silently on next launch (no UI listing yet).

---

## How to Verify
1. Launch app → navigate to **Axioms → Verse Analysis → Prompt Builder**.  
2. Click **Save Draft**.  
   - Confirm `axioms_drafts.json` appears in the project folder.  
3. Close the Axioms Dashboard and restart the program.  
   - Verify previously saved draft entries are present in memory (`dashboard._axioms_drafts`).  
4. Repeat saves to ensure multiple drafts accumulate and JSON updates without corruption.  
5. Delete or corrupt the file intentionally → app should recreate it gracefully.

---

## Implementation Notes
- All code is placed under  
  `# === Axioms T5: Local Draft Save / Load (JSON Mock) ===`.  
- Additive-only: no edits to pre-Axiom functions or constants.  
- Data format:
  ```json
  {
    "created_at": "2025-10-19T07:45:00",
    "verse": "...",
    "related_summ": "...",
    "consecutive_summ": "2",
    "translation_mode": "own|darpan",
    "own_text": "...",
    "prompt_text": "..."
  }

