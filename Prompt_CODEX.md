
---

### **Prompt for Codex CLI – Task 6**

**Prompt Title:**
Implement Axioms T6 – Finalize Axiom (Mock) Flow

**Prompt Text:**
Study `@Prompt_CODEX.md` and its reference `@0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`, then implement **Task 6 (Finalize Axiom (Mock) Flow)** in `1.1.0_birha.py`.
Work on a new branch and strictly follow these mandates:

* Do **not** alter any existing functions, constants, or strings.
* No renames, refactors, in-place edits, or deletions.
* Add all new code only under the header:
  `# === Axioms T6: Finalize Axiom (Mock) Flow (additive only) ===`

**Implementation Scope:**

* Introduce a new `AxiomsFinalizeAxiomView` class as the final stage after the Prompt Builder (T4).
* Display the generated Axiom prompt with editable fields for:

  * **AXIOM (text entry)** and
  * **RATIONALE (multi-line input)**.
* Add buttons for **Back**, **Cancel**, and **Save Axiom** (placeholder).
* The **Back** button returns to the Prompt Builder, **Cancel** closes the Axioms Dashboard, and **Save Axiom** should show a mock confirmation message (e.g., “Draft axiom recorded — persistence arrives in T7”).
* Integrate a wrapped call from T4’s **Save Draft** or **Proceed** actions so this view appears as the next step in the flow.
* Maintain visual consistency with prior T2–T5 screens (light-gray background, dark-cyan buttons, bold labels).

**Testing Note:**
Confirm smooth navigation between Prompt Builder → Finalize Axiom (Mock) → Back → Prompt Builder without state loss.
Run `python -m py_compile 1.1.0_birha.py` to validate syntax and imports.

---
