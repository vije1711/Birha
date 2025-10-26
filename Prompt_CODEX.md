
---

## Axioms — Task T11: Axiom Contribution & Linking (additive only)

**Goal**
Implement UI + data wiring so a user can link selected verse(s) to **new** or **existing** Axioms, with two description layers:

1. **Verse-specific description** (what this verse contributes)
2. **Axiom-level description** (global description for the axiom)

**Important sources to read first (explicit file paths, no `@` shorthand in this file):**

* `./0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`
  Focus Section “Phase II — Backend Integration & Logic (T8–T13)”, Task **T11 — Axiom Contribution & Linking** (scope & acceptance).
* `./1.1.0_birha.py`
  Only **additive** edits. Keep pre-Axiom code frozen per Contract. Reuse the patterns from T5–T10 (store adapters, safe UI patches, headers).

**Branch & headers**

* Create branch: `task/t11-axiom-linking`
* All new code inside `1.1.0_birha.py` under a single header block:

```
# === Axioms T11: Axiom Contribution & Linking (additive only) ===
```

**UI requirements (additive, no removals):**

* In the Axioms flow (post T6/T8/T10 screens), add a **“Link to Axiom”** path that:

  * Lets user choose: **Create New Axiom** or **Link to Existing**.
  * If **Create New**: prompt for `Axiom Title` (one-line) and optional `Axiom-level description`.
  * If **Existing**: searchable dropdown/list (type-ahead) of Axioms from the store.
  * Always show an **inline editor** for the **Verse-specific description** (short paragraph).
  * Buttons: **Save Link**, **Cancel**, **Back**.
  * Non-blocking toasts/messageboxes on success/failure; no destructive actions.

**Data model & sheets (use the adapter patterns from T8):**

* Persist to `1.3.0_axioms.xlsx` with at least these sheets/columns (create if missing; additive w/ atomic write):

  * **Axioms**: `axiom_id` (stable UUID), `title`, `created_at`, `updated_at`, optional `status`.
  * **AxiomDescriptions**:

    * `axiom_id`, `kind` in {`axiom`, `verse`}
    * `verse_key_norm` (for `kind=verse`), `description_text`, `created_at`, `updated_at`, `author`
  * **AxiomContributions**:

    * `axiom_id`, `verse_key_norm`, `source` (e.g., `darpan`|`own`), `link_created_at`, `link_updated_at`
* Keep all writes **atomic** (temp file + replace) and **non-destructive** for non-spec sheets (match T8 writer).
* **Normalization**: reuse existing helpers (e.g., `_normalize_verse_key`) for `verse_key_norm`.

**Behaviors & validation:**

* **Existing Axiom selection**: fuzzy search by title (case-insensitive); show top matches with recency.
* **Create-new**: de-dupe by normalized title; if a nearby match exists, prompt “Use Existing or Create New”.
* **Verse-specific description** is required on Save Link; Axiom-level description optional when linking to existing.
* On Save:

  * Ensure Axiom exists (create if needed).
  * Upsert **AxiomContributions** (one row per `(axiom_id, verse_key_norm)`).
  * Upsert **AxiomDescriptions** rows:

    * `kind=verse` → attach to `(axiom_id, verse_key_norm)`.
    * If provided `axiom` description for new axiom (or explicit user choice), add/append `kind=axiom`.
* **Idempotency**: re-linking the same verse to the same axiom updates timestamps/text, not duplicates.
* **Back/Cancel** returns to previous view without writing.

**Cross-feature hooks (read contract doc while implementing):**

* If T9 (Keyword Manager) exists: after a successful link, trigger a **non-blocking** “Consider refreshing keywords” notice for that axiom (no auto-writes).
* If T10 (Reanalysis & Revision Sync) exists: linking does **not** queue reanalysis, but if verse has outdated revision, show a small inline warning (read-only).

**Testing & acceptance:**

* Run: `python -m py_compile 1.1.0_birha.py`
* Manual path:

  1. Open Axioms flow → pick a verse → **Link to Axiom**
  2. Create New Axiom with verse-specific description → save
  3. Link another verse to the same axiom via **Existing** picker → save
  4. Reopen the view; verify both links and descriptions are persisted in `1.3.0_axioms.xlsx`.
* Acceptance Criteria (per Contract T11):

  * Multiple verses can link to one axiom.
  * Verse-specific and Axiom-level descriptions are stored distinctly and load correctly.
  * No edits to pre-Axiom modules; all code is additive.

**Deliverables:**

* New T11 block (UI + adapters) in `1.1.0_birha.py`.
* Schema-safe updates to `1.3.0_axioms.xlsx` via the existing T8 writer pattern.
* Minimal PR body summarizing scope, testing steps, and risks.

---
