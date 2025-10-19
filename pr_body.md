## Summary
Implements **Task T4 — Prompt Builder Preview** (UI-first). After Translation Choice (T3), a new view composes a structured, copyable prompt based on the selected verse(s) and the user’s translation mode (Darpan vs Own). Drafts can be saved in memory for the session.

## Scope & Behavior
- Adds `AxiomsPromptBuilderView` with sections: primary verse, related verses, consecutive setting, translation mode, and read-only prompt preview.
- Actions: **Regenerate**, **Copy Prompt** (pyperclip with fallback), **Save Draft** (in-memory), **Back**, **Cancel**.
- Wires T3’s Proceed to open Prompt Builder, carrying verse summaries and translation content.
- No persistence or store writes (T5 will handle persistence).

## How to Verify
1. Follow the Verse Analysis flow through Review → Translation Choice.
2. Choose Darpan or Own; Proceed to Prompt Builder.
3. Confirm prompt content matches choices; Copy Prompt & Save Draft work.
4. Back returns to T3; Cancel exits dashboard.

## Implementation Notes
- All code under `# === Axioms T4: Prompt Builder Preview (additive only) ===`.
- Additive wrapper replaces T3 `_proceed_choice` safely.
- Session drafts stored at `dashboard._axioms_drafts`.
- `python -m py_compile 1.1.0_birha.py` passes.

## Risks & Mitigations
- `pyperclip` may be absent → guarded import with highlight fallback.
- GUI needs DISPLAY in CI → headless-safe tests land in T12.

## Compliance
- Additive-only; no changes to pre-Axiom code/strings.
- `1.1.0_birha_pre_Axiom.py` remains read-only reference.

