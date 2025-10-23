## Summary
Implements **Task T8 — Axioms Store Adapter Integration**, enabling persistence of Axioms data to a new Excel-based store (`1.3.0_axioms.xlsx`).  
This milestone transitions the project from UI-only (T0–T7) to logic integration, ensuring the system can now create, update, and track Axiom records without affecting existing modules.

## Scope & Behavior
- Adds a new adapter layer under header  
  `# === Axioms T8: Store Adapter Integration (additive only) ===`.
- Creates and manages `1.3.0_axioms.xlsx` with five structured sheets:  
  `Axioms`, `AxiomDescriptions`, `AxiomContributions`, `AxiomKeywords`, `AxiomWorkqueue`.
- Provides atomic helpers:
  - `ensure_axioms_store(path)` → safely create workbook if missing.  
  - `load_axioms_store(path)` / `_save_axioms_store(path, dfs_dict, others)` → atomic read/write preserving non-spec sheets.
- Exposes public API:
  - `create_axiom`, `upsert_axiom_description`, `link_contribution`, `upsert_keywords`, `enqueue_work`.
- Wires into T6’s **“Create Axiom”** and **“Link to Existing Axiom”** buttons so the UI now saves real records while maintaining all existing dialogs.

## Implementation Notes
- Additive-only: pre-Axiom functions remain read-only reference.  
- Workbook creation uses `pandas + openpyxl`; all writes are atomic (temp → replace).  
- In-process lock prevents concurrent save conflicts.  
- File operations run headless-safe (no GUI dependency).  
- `python -m py_compile 1.1.0_birha.py` passes.

## How to Verify
1. Delete/rename any existing `1.3.0_axioms.xlsx`.  
2. Launch the application and run the **Create Axiom** or **Link to Existing Axiom** actions.  
3. Confirm the workbook is created with five sheets and headers.  
4. Check rows appended to `Axioms` and `AxiomContributions`.  
5. Re-run to confirm idempotent updates (no duplicates, consistent timestamps).

## Risks & Mitigations
- **File-system permission failure:** handled by guarded `try/except` and info message.  
- **Concurrent access:** protected with a thread lock for in-process safety.  
- **Data corruption risk:** mitigated by atomic write (temp → rename pattern).  

## Compliance
- Fully conforms to **“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx”** (Phase II → Task T8).  
- All work is strictly additive; `1.1.0_birha_pre_Axiom.py` remains read-only reference.

