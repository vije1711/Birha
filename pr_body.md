## Summary
Implements **Task T11 — Axiom Contribution & Linking**, introducing the ability to connect verses to new or existing Axioms and record both verse-specific and global Axiom-level descriptions.  
The feature builds on the persistence and UI framework from Tasks T5–T10 and fulfills the functional requirements defined in *“0.1.7.4 Axioms_Framework Engineering Contract — Birha V2.0.docx.”*

## Scope & Behavior
- Adds a new section under  
  `# === Axioms T11: Axiom Contribution & Linking (additive only) ===`
  within `1.1.0_birha.py`.
- Extends the post-translation Axioms flow to present a **Link to Axiom** dialog that supports:
  - **Create New Axiom** → prompts for *Title* and optional *Axiom-level description.*
  - **Link to Existing** → searchable type-ahead list of current Axioms.
  - **Verse-specific description** → mandatory field summarizing the verse’s contribution.
- Buttons: **Save Link**, **Back**, **Cancel** with non-blocking info dialogs.
- Fully additive integration—no edits to pre-Axiom or legacy modules.

## Data Model & Storage
Persists data safely into `1.3.0_axioms.xlsx` using atomic write-and-replace logic established in T8.  
New / extended sheets and fields:
- **Axioms:** `axiom_id (UUID)`, `title`, `created_at`, `updated_at`
- **AxiomDescriptions:** `axiom_id`, `kind (axiom|verse)`, `verse_key_norm`, `description_text`, timestamps, `author`
- **AxiomContributions:** `axiom_id`, `verse_key_norm`, `source (darpan|own)`, link timestamps
Ensures idempotent updates—relinking the same verse updates existing entries instead of duplicating them.

## How to Verify
1. Launch the Axioms flow after verse review or translation steps.  
2. Choose **Link to Axiom** → **Create New Axiom**, provide required fields, and Save.  
3. Re-open **Link to Axiom** → **Existing**, select the same axiom, and add another verse-specific description.  
4. Confirm both entries appear in `AxiomContributions` and `AxiomDescriptions` with correct timestamps.  
5. Verify that no duplicate rows are created and that Excel write operations remain atomic.  
6. Compilation:  
   ```bash
   python -m py_compile 1.1.0_birha.py

