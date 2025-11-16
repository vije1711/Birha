
---

## Task prompt for Prompt_CODEX.md (plain text)

Task – Axioms “Perform own literal translation” workflow (auto-prefill + dedicated workbench)

Context:
We are working on the Axioms/Framework feature inside 1.1.0_birha.py. The Axioms module must remain self-contained and must not reuse or call pre-Axioms GUI helpers or flows from other modules. It may read/write shared data files (for example, assessment_data.xlsx) but all UI and control logic for Axioms must be implemented locally within the Axioms section.

Before making any change:

1. Carefully read the latest “0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx” that is present in the workspace.
2. Carefully read this Prompt_CODEX.md file itself to respect all meta-rules (additive safety, no cross-module UI reuse, etc.).
3. Inspect the current Axioms Translation Choice flow inside 1.1.0_birha.py: the “Perform own literal translation” option, any existing Axioms literal helpers, and the prompt-builder path.

Goal for this task:
Implement a robust, Axioms-specific “Perform own literal translation” workflow that:

A) Auto-prefills literal translation text when prior work exists (from assessment_data.xlsx), especially for consecutive verses;
B) Provides a dedicated Axioms Literal Translation Workbench when no prior translation exists;
C) Handles mixed cases where some selected verses already have translations and others do not;
D) Keeps all behavior inside the Axioms module and does not call UI functions from the legacy “Literal Translation” or “Edit Saved Literal Translation → Analyze Selected Words” flows.

Detailed requirements:

1. Auto-prefill from assessment_data.xlsx

* Use the existing data file (for example, 1.2.1 assessment_data.xlsx, or whatever file is already being used for literal translation history) as the single source of truth for prior literal translations.
* When the user reaches the Axioms Translation Choice screen and selects “Perform own literal translation”, look at the currently selected verse block (including any consecutive verses) and check which of those verses already have a stored literal translation in the assessment data.
* If all selected verses in the block have complete literal translations, automatically construct a combined literal translation string and prefill the “own literal translation” option in the Axioms UI.
* Show a clear status in the Translation Choice view indicating that the text was loaded from saved assessment data. The user should still be able to open the Axioms workbench to refine or override the auto-filled text.

2. Dedicated Axioms Literal Translation Workbench (no verse re-entry, no legacy UI reuse)

* When there is no prior translation for the selected verse(s), or when the user wants to refine them, open a dedicated Axioms Literal Translation Workbench.
* This workbench must NOT ask the user to paste the verse again or click an “Analyze” button like the legacy Grammar Analyzer. The verse(s) are already known from the Axioms flow (Verse Analysis + consecutive selection or SGGS Reading Mode), so the workbench should receive the verse block directly as input.
* Do NOT reuse the legacy UI flow that shows “Select one matching verse” or the step that re-selects additional lines; that verse selection work has already been done earlier in the Axioms path.
* Instead, design the workbench by taking conceptual inspiration from the “Literal Translation” step of the Verse Analysis Dashboard:

  * Break the verse(s) into words/tokens.
  * Show grammar options and any existing word-level meanings where available.
  * Allow the user to enter per-word literal meanings and build up a full, verse-level literal translation.
  * Provide controls to copy the assembled translation and to apply it back into the Translation Choice view.
* The workbench must live entirely inside the Axioms section of 1.1.0_birha.py (for example, as an Axioms-specific dialog or embedded frame) and must not call the pre-Axioms literal-translation or grammar-analysis UI functions.

3. Mixed cases – some verses already translated, some not

* When the user has selected multiple consecutive verses, there may be a mix of verses with and without pre-existing literal translations.
* In such cases, the Translation Choice screen should clearly indicate how many verses already have literal translations and how many still need to be completed.
* When the user opens the Axioms Literal Translation Workbench:

  * Prefill any verses that already have stored literal translations (read-only or editable as appropriate).
  * Guide the user to complete literal translations for the remaining verses, using the same per-word grammar/meaning workflow.
  * After the user finishes, the combined literal translation for all selected verses should be available and applied back to the “own literal translation” option in Translation Choice.
* Optionally, and only if consistent with the Engineering Contract, you may write newly created literal translations back into assessment_data.xlsx so other modules can benefit later. If this is done, it must be done carefully and consistently (no partial or corrupted writes).

4. Separation from legacy modules and safety

* Do not call or reuse GUI helpers, windows, or flows from:

  * The old “Literal Meaning Analysis” feature of the Verse Analysis Dashboard, or
  * “Edit Saved Literal Translation → Analyze Selected Words”.
* You may reuse the idea of per-word grammar and meaning, but the actual code must be implemented as Axioms-owned helpers and classes.
* Maintain all existing Axioms entry, verse selection, translation choice, and prompt builder behavior. New work should extend or wrap these flows rather than breaking them.
* Be defensive: if loading from assessment_data.xlsx fails or returns no matches, fall back to the Axioms workbench path instead of crashing.

5. Tests and sanity checks

* Run at least:
  python -m py_compile 1.1.0_birha.py
* Manually verify these scenarios at minimum (describe in your remarks):

  * Single verse with existing translation → Axioms auto-prefills correctly and Proceed works.
  * Multiple consecutive verses with all translations present → combined literal translation is auto-filled.
  * Block with partial coverage (some verses translated, some not) → status shows correctly, workbench opens, missing verses can be completed, and final translation is applied.
  * Block with no prior translations → workbench starts from scratch and the resulting translation flows back into Translation Choice and then the prompt builder.

In your final remarks, briefly summarize:

* How you used “0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx” and this Prompt_CODEX.md to guide decisions,
* How you ensured no legacy UI flows are reused inside Axioms, and
* How the new Axioms Literal Translation Workbench and auto-prefill behavior work together for single and consecutive verse selections.

---
