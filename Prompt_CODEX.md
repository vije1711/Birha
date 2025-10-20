
---

### Prompt for Codex CLI — **Task 7**

**Title:** Implement Axioms T7 — SGGS Reading Mode (Stub)

**Prompt text (paste as-is below your Task sections):**

Study `@Prompt_CODEX.md` and `@0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`, then implement **Task 7 (SGGS Reading Mode — Stub)** in `1.1.0_birha.py`.

**Non-negotiable mandates**

* Do **not** alter any existing functions, constants, or strings.
* No renames, refactors, in-place edits, or deletions.
* Add new code **only** under the header:
  `# === Axioms T7: SGGS Reading Mode (stub, additive only) ===`

**Scope**

* Add a lightweight **SGGS Reading Mode** view (e.g., `AxiomsSGGSReaderView`) that:

  * Displays **mock SGGS content** in a scrollable list/text area (enough entries to scroll).
  * Lets the user **select a verse** (single click or button) to start the Axiom flow.
  * On selection, routes back into the existing **Verse Input Flow (T2)**, pre-filling the verse field with the chosen verse string.
* **Wire the existing Axioms Dashboard button** “Axiom via SGGS Reading Mode” to open this view (do not change the button text created in T1).
* Preserve navigation:

  * **Back** returns to the Axioms Dashboard home (the two-button landing).
  * **Cancel** closes the Axioms Dashboard window.
* Keep visuals consistent with T2–T4 (light-gray background, bold labels, dark-cyan primary buttons).

**Acceptance**

* Clicking “Axiom via SGGS Reading Mode” opens the new reader view with mock data.
* Selecting a verse returns the user to Verse Input Flow (T2) with the verse input **pre-filled**.
* Back/Cancel behave as described. No regressions to T0–T4.
* `python -m py_compile 1.1.0_birha.py` succeeds.

**Notes**

* This is a **stub only** (no real SGGS file I/O). Use a small, hard-coded set of verse lines for now.
* All integration must be additive (e.g., wrap or attach handlers; do not edit existing functions).

---

