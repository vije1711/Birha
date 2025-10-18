## Summary
This PR delivers **Axioms UI Phase I (partial)**:
- **T0**: Injects **Axioms (beta)** button on the Welcome dashboard (additive wrapper; no edits).
- **T1**: Adds `AxiomsDashboard` shell with two paths (Verse Analysis / SGGS Reading Mode) and placeholders.
- **T2**: Implements **Verse Input Flow** (single verse entry, 10 mock suggestions, “Include consecutive verses?” toggle, Review screen).  
All work is **additive-only** in `1.1.0_birha.py`. `1.1.0_birha_pre_Axiom.py` remains read-only reference.

## Scope & Behavior
- Clicking **Axioms (beta)** opens the Axioms Dashboard (non-modal).
- **Axiom via Verse Analysis** swaps the dashboard content to the T2 flow:
  - enter verse → “Find Related” → choose suggestions → toggle consecutive verses → Review.
- No backend/store wiring yet; mock data only. Existing Literal/Grammar flows untouched.

## Screens/How to Verify
1. Launch app → “Axioms (beta)” is visible on the Welcome dashboard.
2. Click it → Axioms Dashboard opens with two large buttons.
3. Click “Axiom via Verse Analysis” → verse input pane appears.
4. Type any verse → **Next** enables. Click “Find Related” → 10 mock suggestions appear.
5. Toggle “Include consecutive verses?” → Spinbox enables; set to 2+.
6. Click **Next** → Review shows primary verse, selected suggestions, and consecutive count.
7. **Back** returns to input; **Cancel** closes the dashboard.

## Implementation Notes
- New code lives under headers:
  - `# === Axioms T0: Axioms Entry Point (additive only) ===`
  - `# === Axioms T1: Axioms Dashboard Shell (additive only) ===`
  - `# === Axioms T2: Verse Input Flow (additive only) ===`
- Defensive Tk handling (no modal takeover, single-window instance management).
- `python -m py_compile 1.1.0_birha.py` passes.

## Risks & Mitigations
- **Widget discovery assumptions** for the Welcome dashboard: additive wrapper searches for the existing button frame; if layout changes, injection may miss.  
  _Mitigation_: logs/messagebox fallback; wrapper is idempotent.
- **Headless CI**: Tk windows require DISPLAY.  
  _Mitigation_: future tests will skip in headless (T12).
- **Styling consistency**: currently `tk.Button`; may switch to ttk later if desired.

## Out of Scope (future tasks)
- T3: Translation choice (Darpan vs Own).
- T4: Prompt builder preview and copy/export.
- T5+: Persistence, stores, linking, reanalysis, keywords.

## Compliance
- Pre-Axiom file is untouched (read-only safeguard).
- Additive-only; no renames/refactors/deletions.
- Canonical strings/headers unchanged.

