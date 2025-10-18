▌ Study @0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx
   and implement **Task T0 — Axioms Entry Point (Button Injection)** in 1.1.0_birha.py.

▌ Objective:
   Introduce a new button labeled **“Axioms (beta)”** on the *Welcome to Gurbani Software Dashboard*.
   When clicked, it should open a new `AxiomsDashboard` window (to be implemented in Task T1).
   The goal is only to integrate this entry point — no backend or logic wiring yet.

▌ Implementation details:
   • Reuse the same Tkinter/ttk style and layout conventions as other dashboard buttons.  
   • Position the button logically with other feature buttons (e.g., below “Literal Analysis” or similar group).  
   • On click, create a new instance of `AxiomsDashboard(master=self)` and bring it to the foreground.  
   • Ensure the button integrates seamlessly into existing layout containers (e.g., within the main Frame or Grid).  
   • Do **not** block or replace any existing event loops; the window must open non-modally.  
   • Graceful handling: if the class `AxiomsDashboard` is not found, show a simple info popup stating  
     “Axioms module will be available in the next build.”

▌ Mandates:
   • Do **not** alter existing functions, constants, or strings outside the additive block.  
   • No renames, refactors, or deletions.  
   • Add new code only under the header:
        # === Axioms T0: Axioms Entry Point (additive only) ===
   • Treat 1.1.0_birha_pre_Axiom.py as reference-only (read-only).  
   • Work on a new branch dedicated to Task T0.

▌ Acceptance criteria:
   • “Axioms (beta)” button is visible on the Welcome Dashboard.  
   • Clicking it opens a placeholder window (or message) without errors.  
   • No layout shifts or regressions occur in other dashboard components.  
   • Application compiles successfully via `python -m py_compile 1.1.0_birha.py`.
