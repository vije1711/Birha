## Summary
Implements **Task T7 — SGGS Reading Mode (Stub)** per “0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx”. This introduces a lightweight reading experience inside the Axioms Dashboard that shows mock SGGS lines in a scrollable view. The user can pick a verse on the fly; the selection routes back into the existing **Verse Input Flow (T2)** with the verse field pre-filled, keeping the UI-first, additive approach.

## Scope & Behavior
- Adds `AxiomsSGGSReaderView` (stub) with:
  - Scrollable mock SGGS content (enough to scroll).
  - Single-verse selection → returns to Axiom via Verse Analysis (T2) with pre-filled verse text.
- Wires the **“Axiom via SGGS Reading Mode”** dashboard button (from T1) to open the new reader view.
- Navigation:
  - **Back** → returns to Axioms Dashboard landing (two-button home).
  - **Cancel** → closes the Axioms Dashboard.
- No real SGGS file I/O; mock content only.

## How to Verify
1. Launch app → **Axioms (beta)** → click **Axiom via SGGS Reading Mode**.
2. Confirm a scrollable list/text of mock lines is shown.
3. Select a verse (via click or “Select Verse” button).
4. Verify the app returns to **Verse Input (T2)** with the verse entry **pre-filled**.
5. Use **Back** to return to dashboard home; **Cancel** should close the Axioms window.
6. Run `python -m py_compile 1.1.0_birha.py` to confirm syntax integrity.

## Implementation Notes
- All new code placed under:
  `# === Axioms T7: SGGS Reading Mode (stub, additive only) ===`
- Additive wiring only (attach handlers; do not edit existing functions).
- Visuals match T2–T4: light-gray background, bold labels, dark-cyan primary buttons.
- Reuses T2 container/display helpers to swap views without losing state.

## Risks & Mitigations
- **Risk:** Navigation regressions between T7 ↔ T2.  
  **Mitigation:** Use the same `_display()`-style swap pattern as prior tasks; no window re-creation.
- **Risk:** Unexpected edits to pre-Axiom code.  
  **Mitigation:** Additive-only header and wrapper hooks; no in-place modifications.

## Compliance
- Follows **“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx.”**
- Additive-only; `1.1.0_birha_pre_Axiom.py` remains read-only reference.
- Existing Literal/Grammar flows untouched.
