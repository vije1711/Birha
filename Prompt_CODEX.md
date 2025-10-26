
---
## Task T9 — Keyword Manager (additive-only)

**Goal:** Implement a UI + logic layer to manage Axiom keywords in four categories:

* **Literal Synonyms**
* **Literal Antonyms**
* **Spiritual Synonyms**
* **Spiritual Antonyms**

This must follow the Axioms contract and be fully **additive-only** inside `1.1.0_birha.py` under a header exactly like:

```
# === Axioms T9: Keyword Manager (additive only) ===
```

### Read These Files Explicitly (no symbolic `@`):

* Study this spec file from disk:
  `./0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`
* Review the current codebase file:
  `./1.1.0_birha.py`
* (Optional context) The working prompt:
  `./Prompt_CODEX.md`

> Note: Codex, **do not** rely on `@filename` shorthand within this Markdown. You must open the exact paths given above from the workspace.

### Branching & PR hygiene (must do)

1. Create and switch to a new branch:
   `git switch -c task/t9-keyword-manager`
2. Only modify `1.1.0_birha.py` additively (no edits to pre-Axiom frozen areas).
3. Commit with conventional message:
   `[Axioms T9] Keyword Manager — additive only; pre-Axiom untouched.`
4. Open a PR targeting `main`.

### Scope

1. **UI Panel (Axioms Dashboard integration)**

   * Add a dedicated, navigable screen for “Keyword Manager” reachable from the Axioms dashboard/workflow after T6/T8 states.
   * Show the four keyword categories with:

     * List view (chips or rows) + add/remove/edit controls.
     * Validation feedback (inline) and a **density meter** (see rules below).
     * “Regenerate from Description” button (uses current Axiom description to seed/update keywords; non-destructive merge with review dialog).
   * Non-blocking toasts/alerts for success, warnings.

2. **Data Model & Persistence (workbook adapter)**

   * Persist to the **AxiomKeywords** sheet in `1.3.0_axioms.xlsx` per the contract. If the file/sheet doesn’t exist, create it additively.
   * Columns (minimum):
     `axiom_id, category, keyword, normalized_key, source, created_at, updated_at`
   * Categories are one of: `literal_syn`, `literal_ant`, `spiritual_syn`, `spiritual_ant`.
   * `normalized_key` must be case-insensitive, Unicode-NFC normalized, whitespace-collapsed; use it for dedupe.
   * Provide helpers: `load_axiom_keywords(axiom_id)`, `save_axiom_keywords(axiom_id, records)` that NEVER touch non-spec sheets.

3. **Validation & Normalization**

   * Trim whitespace; NFC normalize; lower/“casefold” for matches; collapse internal spaces.
   * Disallow empty or purely punctuational entries.
   * **Dedupe** within category by `normalized_key`.
   * Optional rule: max 24 items per category (configurable constant).
   * Warn if too many near-duplicates (Levenshtein or `rapidfuzz` ≥ 92 within category).

4. **Density Control**

   * Compute **density** = (#keywords in category) / (total keywords for axiom). Display per category:

     * Green (≤ 35%), Amber (35–55%), Red (> 55%).
   * Show a compact bar + percentage. If any category exceeds the red threshold, show a non-blocking warning.

5. **Auto-update on Description Change**

   * If an Axiom’s **description** (from T8/T11 flows) changes, offer:
     “Re-generate suggestions from description?”

     * If accepted: compute suggested inflow (do not overwrite). Show diff dialog with Accept/Reject per keyword.

6. **Regeneration Heuristics (simple & local)**

   * Use current Axiom description text to propose candidates by:

     * Tokenizing, removing stop-words (English + simple Punjabi list), stemming/normalize (lightweight), and collecting top-scored noun-like or salient tokens.
     * Classify into the four categories **heuristically**:

       * “Antonym” buckets seeded by simple opposite-lexeme table (tiny static list; additive).
       * “Spiritual” vs “Literal” by presence in a tiny curated list of spiritual terms; otherwise default to Literal Synonyms.
   * This remains a **local heuristic** (no network). Keep it small and transparent.

7. **Additive-only Guardrails**

   * Do not modify or rename any pre-Axiom code.
   * New classes/functions must be prefixed clearly (e.g., `AxiomsKeywordManagerView`, `AxiomKeywordStoreAdapter`, etc.).
   * UI wiring should wrap/extend, not replace, existing callbacks.

### Acceptance Criteria

* A “Keyword Manager” screen exists and is reachable from the Axioms dashboard/flows.
* Users can add/edit/delete keywords across the four categories with inline validation and dedupe.
* Data persists in `1.3.0_axioms.xlsx` → `AxiomKeywords` sheet (created if missing) without altering other sheets.
* Density meter renders per category and shows warnings on red.
* “Regenerate from Description” proposes non-destructive suggestions with a review/merge step.
* Changing an Axiom description prompts to re-suggest keywords.
* Code compiles: `python -m py_compile 1.1.0_birha.py`.

### Implementation Hints

* Follow the existing workbook helpers’ patterns (safe Excel read/write, overlay, atomic temp files).
* Reuse/extend any normalization utilities already present (NFC, whitespace collapse).
* Keep UI fonts/colors consistent with prior Axioms screens.

### Deliverables

* Code under:
  `# === Axioms T9: Keyword Manager (additive only) ===`
* Unit-lite check: a small internal test function you can call from UI to simulate suggestion/merge.
* PR body file `pr_body.md` summarizing scope, verification steps, and risks.

---
