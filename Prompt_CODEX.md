▌ Study @0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx 
   and implement **Task T1 — Axioms Dashboard Shell** in `1.1.0_birha.py`.

▌  Implementation scope:
   • Create a new additive-only window class named `AxiomsDashboard`.
   • Window title: “Axioms Dashboard (beta)”.
   • Layout: two large buttons, vertically centered and spaced apart:
        1. “Axiom via Verse Analysis”
        2. “Axiom via SGGS Reading Mode”
   • Both buttons should open placeholder frames or simple dialogs confirming 
     that each path has been selected. No logic or data binding yet.
   • Window should close gracefully without affecting any existing dashboards.
   • Use the same UI style patterns as pre-Axiom dashboards (Tkinter, ttk, WindowManager, etc.).

▌  Mandates:
   • Do **not** alter any existing functions, constants, or strings.
   • No renames, refactors, in-place edits, or deletions.
   • Add all new code only under the header:
        # === Axioms T1: Axioms Dashboard Shell (additive only) ===
   • Treat `1.1.0_birha_pre_Axiom.py` as read-only reference.
   • Work on a new branch dedicated to Task T1.

▌  Acceptance criteria:
   • The Welcome Dashboard’s “Axioms (beta)” button (from Task T0) opens this new window.  
   • Both sub-buttons are visible and clickable, launching their placeholder dialogs.  
   • No errors thrown on open or close; UI remains responsive.  
   • Pre-Axiom dashboards and functions remain unaffected.
