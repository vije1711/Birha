▌ Study the engineering contract document titled 
   “0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx”
   available in the project root, and implement **Task T3 — Translation Choice Screen** in 1.1.0_birha.py.

▌ Objective:
   Extend the Axiom-via-Verse-Analysis flow so that after the Review screen (T2),
   the user chooses how the translation for the selected verse(s) will be obtained.

▌ UI scope (UI-first, no backend logic yet):
   • Add all new code only under the header:
       # === Axioms T3: Translation Choice Screen (additive only) ===
   • When the user clicks **Continue** on the T2 Review screen,
     swap to a new frame/pane that presents two radio-button options:
       1. **Use predefined Darpan translation**  
          – shows a read-only textbox area with mock “Darpan translation” text.  
          – enable a **Proceed** button.
       2. **Perform own literal translation**  
          – shows an editable Text widget where the user can type or paste their own translation.  
          – enable the same **Proceed** button once non-empty.
   • Include a **Back** button to return to Review and a **Cancel** to exit the flow.
   • Use consistent fonts/colors with prior screens (e.g., light-gray bg, dark-slate header).
   • No file I/O or data persistence yet; mock text only.

▌ Navigation rules:
   • Hook the T2 Review’s “Continue” button so it launches this new Translation Choice pane.
   • “Back” returns to the Review view; “Proceed” advances to a simple placeholder
     message (“Translation choice recorded — next step coming soon.”).

▌ Mandates:
   • Do not alter any existing functions, constants, or strings.
   • No renames, refactors, in-place edits, or deletions.
   • Treat `1.1.0_birha_pre_Axiom.py` as read-only reference.
   • Work on a **new branch** dedicated to Task T3.

▌ Acceptance criteria:
   • Clicking **Continue** on the Review screen opens the Translation Choice Screen.  
   • Two exclusive radio options appear: “Use Darpan translation” / “Perform own translation.”  
   • Switching options updates which text area is active (editable vs readonly).  
   • **Proceed** enabled only when a valid selection/entry exists.  
   • **Back** returns to Review, **Cancel** exits gracefully.  
   • `python -m py_compile 1.1.0_birha.py` passes and existing dashboards remain unaffected.
