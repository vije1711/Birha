
---

## Task T10 — Reanalysis & Revision Sync (additive only)

**Goal:** Detect verses whose translation/assessment revision has changed since last seen and queue them for reanalysis. Parent verses must always trigger reanalysis when any supporting verse updates.

**Read these files explicitly (no `@` shorthand inside this .md):**

* `./0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx`
  (See Phase II Task **T10 — Reanalysis & Revision Sync**: compare stored revision numbers against `1.2.1 assessment_data.xlsx`; queue outdated verses; parent verses trigger reanalysis.)
* `./1.1.0_birha.py` (current source to extend additively)

**Create a new branch (do not work on `main`):**
`task/t10-reanalysis-revision-sync`

**Additive-only code block header to use:**

```python
# === Axioms T10: Reanalysis & Revision Sync (additive only) ===
```

### Requirements

1. **Revision snapshot loader**

   * Add a small, pure helper that reads `./1.2.1 assessment_data.xlsx` (assume sheet and columns named in a defensive way; normalize headers).
   * Extract a mapping: `{ verse_key_norm -> translation_revision }`.
   * Keep it resilient (missing file → empty mapping; tolerate tz/NaN/whitespace).

2. **Axioms store sync points**

   * If not present already, ensure the Axioms store file exists: `./1.3.0_axioms.xlsx` with sheets:

     * `Axioms`, `AxiomDescriptions`, `AxiomContributions`, `AxiomKeywords`, `AxiomWorkqueue`, and `Metadata` as per contract (add sheets if missing; never drop non-spec sheets).
   * For verse-bearing sheets (e.g., `AxiomContributions` or wherever verse text lives), ensure these columns (add if missing):

     * `verse`, `verse_key_norm`, `translation_revision_seen`, `last_checked_at`.

3. **Diff & queue logic**

   * Compare `translation_revision_seen` vs the latest revision from `assessment_data.xlsx`.
   * For any mismatch (or if `translation_revision_seen` is empty), add/refresh an item in `AxiomWorkqueue`:

     * Columns: `verse`, `verse_key_norm`, `reason="revision_mismatch"`, `queued_at`, `status="pending"`.
   * **Parent rule:** If a verse is marked as a parent (or appears as a parent in any association you maintain), queue it when any of its child/support verses update. If explicit parent/child columns don’t exist yet, infer conservatively from your current Axioms linkages; if none found, skip parent propagation with a TODO note.

4. **UI surface (dashboard)**

   * Add a lightweight status chip/button to the Axioms Dashboard that:

     * Shows a count of “Reanalysis Required” items (pending in `AxiomWorkqueue`).
     * Provides a “Refresh Revisions” action to rerun the sync.
     * Provides a “View Queue” action that lists pending items (verse snippet + reason) and allows no-op close for now (processing lands in later tasks).

5. **Persistence & safety**

   * Reuse your existing Excel helpers (atomic temp write, preserve non-spec sheets, keep_vba where applicable).
   * Never modify `1.1.0_birha_pre_Axiom.py`. All work is additive to `1.1.0_birha.py`.

6. **Acceptance criteria**

   * Running “Refresh Revisions” updates `AxiomWorkqueue` based on `1.2.1 assessment_data.xlsx`.
   * Dashboard visibly flags when any verse needs reanalysis (non-zero pending count).
   * Parent verses are queued when any linked child/support verse changes (where linkage is available).
   * `python -m py_compile 1.1.0_birha.py` passes.

### Deliverables

* New additive block under the specified header.
* Updated Excel helpers (if needed) to safely read/write `1.3.0_axioms.xlsx`.
* Minimal UI hooks (badge/count + two buttons) wired into the Axioms Dashboard.

### Git & PR

* Branch: `task/t10-reanalysis-revision-sync`
* Commit message prefix: `[Axioms T10] Reanalysis & Revision Sync — additive only`
* After push, open a PR into `main`.

---
