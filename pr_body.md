## Summary
Implements **Task T10 — Reanalysis & Revision Sync**, enabling detection and queuing of Axioms whose verse translations have been revised since last analyzed.  
This feature ensures that any verse, and its parent where applicable, is automatically flagged for reanalysis whenever its translation version changes in the master dataset (`1.2.1 assessment_data.xlsx`).

## Scope & Behavior
- Introduces a new additive module under  
  `# === Axioms T10: Reanalysis & Revision Sync (additive only) ===`
- Adds helpers to:
  - Read verse translation revisions from `1.2.1 assessment_data.xlsx`
  - Compare with stored revision metadata (`translation_revision_seen`) in `1.3.0_axioms.xlsx`
  - Identify mismatches and queue affected verses in the `AxiomWorkqueue` sheet.
- Parent verses are also queued whenever linked child/support verses are updated.
- Enhances the **Axioms Dashboard** with:
  - A badge displaying the current count of “Reanalysis Required” verses.
  - A **Refresh Revisions** action to rerun sync logic.
  - A **View Queue** dialog listing all pending verses for reanalysis (read-only preview).

## Implementation Notes
- Data structure follows contract fields:
  `verse`, `verse_key_norm`, `translation_revision_seen`, `last_checked_at`, `reason`, `queued_at`, `status`.
- Workbook I/O uses atomic save (temp write → rename), preserving all non-spec sheets.
- Handles missing or corrupted `assessment_data.xlsx` gracefully with an empty diff set.
- All additions are **additive-only**, maintaining full compatibility with pre-Axiom code.

## How to Verify
1. Launch the **Axioms Dashboard** and open the Reanalysis section.  
2. Run **Refresh Revisions** — the pending count should reflect any verses whose revision differs from stored values.  
3. Open **View Queue** to confirm pending entries are correctly populated with verse keys and reasons.  
4. Inspect `1.3.0_axioms.xlsx → AxiomWorkqueue` to ensure queued rows have valid timestamps and statuses.  
5. Re-run sync to confirm already-updated verses are no longer requeued.

## Risks & Mitigations
- **File access issues:** mitigated by atomic writes and try–except guards.  
- **Parent–child propagation gaps:** handled conservatively, only when linkage metadata exists.  
- **GUI freeze risk:** sync runs with UI-safe update calls (lightweight scan, no blocking).

## Compliance
- Fully aligned with **“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx”** (Phase II, Task T10).  
- Additive-only; no modification to pre-Axiom constants, strings, or UI components.  
- Verified compilation with:  
  ```bash
  python -m py_compile 1.1.0_birha.py

