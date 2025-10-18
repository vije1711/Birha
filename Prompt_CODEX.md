▌ Study @0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx
   and implement **Task T2 — Verse Input Flow** in `1.1.0_birha.py`.

▌ Objective:
   Under the Axioms Dashboard (beta), make the **“Axiom via Verse Analysis”** button
   open a new pane that lets the user:
   1) enter a single verse (phase-1 scope),
   2) fetch and display **10 related verse suggestions** (mock data),
   3) choose whether to **include consecutive verses**,
   4) proceed to a simple **Review** placeholder screen.

▌ Implementation details (UI-first, no backend wiring):
   • Add new code only under:
       # === Axioms T2: Verse Input Flow (additive only) ===
   • Create a dedicated `Frame` (or small view class) for the Verse Input Flow with:
       - A labeled Entry/Text field for “Enter verse (single verse)”.
       - A “Find Related” button → loads **10 mock suggestions** (hardcoded list or
         small local fixture in memory) into a Listbox with multi-select enabled.
       - A control for **Include consecutive verses?**
         (checkbox + disabled-by-default Spinbox for count, enabled when checked).
       - Buttons: **Next** (go to Review), **Back** (return to dashboard shell),
         **Cancel** (close the pane/window safely).
   • Review screen (placeholder):
       - Lists the chosen verse, the selected suggestions, and consecutive-verse choice.
       - Has **Back** and **Continue** (Continue does nothing yet except a messagebox).
   • Validation:
       - Disable “Next” until at least one verse (the main input) is present.
       - If “Include consecutive” is checked but count is empty/zero, show a friendly warning.
   • Navigation:
       - Wire the existing “Axiom via Verse Analysis” button to swap the AxiomsDashboard
         content to this new view (do not open a new Toplevel).
   • Styling:
       - Reuse Tk/ttk patterns consistent with the app (fonts/padding similar to T1 buttons).

▌ Mandates:
   • Do **not** alter any existing functions, constants, or strings.
   • No renames, refactors, in-place edits, or deletions.
   • Treat `1.1.0_birha_pre_Axiom.py` as read-only reference.
   • Work on a **new branch** dedicated to Task T2.

▌ Acceptance criteria:
   • Clicking **“Axiom via Verse Analysis”** shows the Verse Input pane inside the
     Axioms Dashboard (no new window).
   • “Find Related” populates a list of **10 mock** verse suggestions.
   • “Include consecutive verses?” toggle enables/disables an adjacent count control.
   • **Next** advances to a Review placeholder summarizing inputs; **Back** returns.
   • **Cancel** exits the flow cleanly without affecting other dashboards.
   • `python -m py_compile 1.1.0_birha.py` passes, and no regressions occur in existing UI.

▌ Notes:
   • Mock data is acceptable for T2 (no Excel/CSV reads yet).
   • Keep all strings additive (do not modify canonical headers/labels elsewhere).
