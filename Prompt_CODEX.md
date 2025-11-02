
---

## Task T13 — Implement exactly as specified in the Engineering Contract (additive-only)

**Read these sources first (use exact quoted paths, do not rely on `@filename` shorthands inside this Markdown):**

1. `"./0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx"`
2. `"./1.1.0_birha.py"`

**What to do**

* Open the DOCX above and locate the section titled **Task 13** (a.k.a. **T13**). Treat that section as the single source of truth for scope, UI/UX, behavior, data flow, and acceptance criteria.
* Implement T13 **additively** in `1.1.0_birha.py` only.

  * **Do not modify, rename, or delete** any existing functions, constants, or strings.
  * If a helper is required, create new helpers **only** under a new header:

    ```python
    # === Axioms T13: <short, precise title from the contract> ===
    ```
  * Keep all new UI in the Axioms surfaces (Axioms Dashboard / Verse flow / SGGS mode) per the contract. Do **not** touch literal translation or other legacy features.
* If T13 depends on any earlier T0–T12 utilities, **reuse them as-is**. If an extension is required, wrap or subclass rather than editing existing code.
* Follow the contract’s **Non-Goals** and **Constraints** verbatim.

**Branching & PR hygiene**

* Create and work on a new branch named: `task/t13-<short-feature-name>`.
* Ensure `python -m py_compile 1.1.0_birha.py` passes.
* Add a short internal smoke check (if the contract asks for it) under the T13 header without altering earlier test hooks.
* Prepare a succinct `pr_body.md` summarizing: scope, how-to-verify, risks/mitigations, and a note that the change is additive-only.

**Acceptance checklist (complete per the DOCX)**

* [ ] Every requirement listed in **Task 13** is implemented.
* [ ] No edits to pre-existing symbols; new code lives under the T13 header.
* [ ] Axioms UI flows remain navigable end-to-end after the change.
* [ ] All docstrings/comments reference **T13** and the contract where helpful.
* [ ] `python -m py_compile 1.1.0_birha.py` succeeds.

**Notes**

* If the contract specifies copy or file paths, preserve exact text/labels.
* Prefer defensive try/except around Tk operations to match earlier tasks’ style.

---

