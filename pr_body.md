## Summary
Implements **Task T9 — Keyword Manager**, adding a complete UI and persistence layer for managing Axiom keywords across four categories:  
**Literal Synonyms**, **Literal Antonyms**, **Spiritual Synonyms**, and **Spiritual Antonyms**.  
The feature introduces validation, normalization, duplicate control, and a density-based visualization system while keeping all logic additive within `1.1.0_birha.py`.

## Scope & Behavior
- Adds `AxiomsKeywordManagerView` and adapter helpers under header  
  `# === Axioms T9: Keyword Manager (additive only) ===`.
- Integrates a navigable UI for managing keyword sets per Axiom, allowing users to:
  - Add, edit, delete, and regenerate keywords per category.
  - View a **density meter** that highlights category balance (Green ≤35%, Amber 35–55%, Red >55%).
  - Review duplicates and near-duplicates (Unicode/Levenshtein filtered).
  - Trigger **Regenerate from Description**, producing keyword suggestions based on current Axiom text.
- Keywords are normalized (Unicode NFC, casefold, trimmed, whitespace-collapsed) and deduped before saving.
- All data persists safely in the `AxiomKeywords` sheet of `1.3.0_axioms.xlsx`, created additively if absent.
- Dashboard wiring connects Keyword Manager entry points after the Axiom creation/update flows.

## Implementation Notes
- Purely additive; no changes to pre-Axiom logic or constants.  
- Workbook operations follow the same atomic pattern as T8 (`ensure → load → save`).  
- Each keyword record includes:
  `axiom_id, category, keyword, normalized_key, source, created_at, updated_at`.
- Regeneration heuristics extract token candidates, filter stop words, and classify them into the four buckets using a simple ruleset (no network dependency).
- The module compiles cleanly via:
  ```bash
  python -m py_compile 1.1.0_birha.py

