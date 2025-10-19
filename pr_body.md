## Summary
This PR delivers **Task T3 — Translation Choice Screen** (UI-first) inside the Axiom via Verse Analysis flow. After the T2 Review screen, the user chooses either:
- **Use predefined Darpan translation** (read-only preview), or
- **Perform own literal translation** (editable text area).
Proceed is enabled when a valid selection/entry exists. Navigation includes **Back** (to Review) and **Cancel** (exit flow).

All work is **additive-only** in `1.1.0_birha.py`; pre-Axiom code remains read-only reference.

## Scope & Behavior
- Adds `AxiomsTranslationChoiceView` (new `tk.Frame`) to the Axioms dashboard pipeline.
- Shows a summary of: Primary verse, Selected related verses, and Consecutive verse choice.
- Two radio options:
  - **Darpan** → read-only text preview (mock content).
  - **Own translation** → editable text area; Proceed enabled only if non-empty.
- **Back** returns to the Review page; **Cancel** exits the dashboard flow.
- No backend/store writes; mock-only preview.

## How to Verify (manual)
1) Launch app → Welcome → **Axioms (beta)**.
2) Click **Axiom via Verse Analysis**.
3) Enter a verse → **Find Related** → select any → optionally enable **Include consecutive verses?** and set count.
4) Click **Next** → Review screen.
5) Click **Continue** → Translation Choice screen appears.
6) Pick **Use predefined Darpan translation** → **Proceed** becomes enabled.
7) Switch to **Perform own literal translation** → type any text → **Proceed** enables.
8) **Back** returns to Review; **Cancel** exits cleanly.
9) Confirm existing dashboards and flows are unaffected.

## Implementation Notes
- New additive section headers:
  - `# === Axioms T3: Translation Choice Screen (additive only) ===`
- View class: `AxiomsTranslationChoiceView`.
- Hook: additive wrapper patches `AxiomsVerseInputFlow._placeholder_continue` to swap in the T3 view.
- Styling matches prior screens (headers, bg, fonts).
- Syntax check: `python -m py_compile 1.1.0_birha.py` passes.

## Risks & Mitigations
- **Widget-patching fragility:** If T2 internals change, the T3 wrapper may not attach.  
  _Mitigation:_ Install guard + fallback to original handler; clear headers make future maintenance easy.
- **Headless environments:** GUI requires DISPLAY.  
  _Mitigation:_ GUI tests will be marked headless-safe in T12; manual verification for now.

## Out of Scope
- Real Darpan fetch; persistence of the user’s own translation.
- Prompt builder (T4) and downstream store integration (T8+).

## Compliance
- Additive-only; no edits/renames/deletions of existing code or strings.
- `1.1.0_birha_pre_Axiom.py` remains read-only reference.

